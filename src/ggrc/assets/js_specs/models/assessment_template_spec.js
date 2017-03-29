/*!
  Copyright (C) 2017 Google Inc.
  Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

describe('can.Model.AssessmentTemplate', function () {
  'use strict';

  var AssessmentTemplate;
  var instance;  // an AssessmentTemplate instance

  beforeAll(function () {
    AssessmentTemplate = CMS.Models.AssessmentTemplate;
  });

  beforeEach(function () {
    instance = new AssessmentTemplate();
  });

  describe('_choosableObjectTypes() method', function () {
    var fakeMapper;  // an instance of the fake MapperModel
    var origMapperModel;

    beforeEach(function () {
      var FakeMapperModel;

      origMapperModel = GGRC.Models.MapperModel;

      // mock the MapperModel used by the method under test
      fakeMapper = {
        initTypes: jasmine.createSpy()
      };
      FakeMapperModel = jasmine.createSpy().and.callFake(function (config) {
        return fakeMapper;
      });

      GGRC.Models.MapperModel = FakeMapperModel;
    });

    afterEach(function () {
      // restore the mocked MapperModel
      GGRC.Models.MapperModel = origMapperModel;
    });

    it('returns the types obtained from the mapper model', function () {
      var result;

      var objectTypes = {
        groupFoo: {
          name: 'Foo Objects',
          items: [{name: 'Foo1'}, {value: 'Foo2'}]
        },
        groupBar: {
          name: 'Bar Objects',
          items: [{value: 'Bar1'}, {value: 'Bar2'}]
        }
      };

      fakeMapper.initTypes.and.returnValue(objectTypes);
      result = instance._choosableObjectTypes();
      expect(result).toEqual(objectTypes);
    });

    it('sorts types within a group by name', function () {
      var result;

      var objectTypes = {
        groupFoo: {
          name: 'Bar-ish Objects',
          items: [
            {name: 'Car'}, {name: 'Bar'}, {name: 'Zar'}, {name: 'Dar'}
          ]
        }
      };

      var expected = [
        {name: 'Bar'}, {name: 'Car'}, {name: 'Dar'}, {name: 'Zar'}
      ];

      fakeMapper.initTypes.and.returnValue(objectTypes);
      result = instance._choosableObjectTypes();
      expect(result.groupFoo.items).toEqual(expected);
    });

    it('omits the all_objects group from result', function () {
      var result;

      var objectTypes = {
        all_objects: {
          models: ['Foo', 'Bar', 'Baz'],
          name: 'FooBarBaz-type Objects'
        }
      };

      fakeMapper.initTypes.and.returnValue(objectTypes);
      result = instance._choosableObjectTypes();
      expect(result.all_objects).toBeUndefined();
    });

    it('omits the types not relevant to the AssessmentTemplate from result',
      function () {
        var result;

        var objectTypes = {
          groupFoo: {
            name: 'Foo Objects',
            items: [
              {value: 'Contract'},  // this object type is relevant
              {value: 'Assessment'},
              {value: 'Audit'},
              {value: 'CycleTaskGroupObjectTask'}
            ]
          },
          groupBar: {
            name: 'Bar Objects',
            items: [
              {value: 'Policy'},  // this object type is relevant
              {value: 'TaskGroup'},
              {value: 'TaskGroupTask'}
            ]
          },
          groupBaz: {
            name: 'Baz Objects',
            items: [
              {value: 'Workflow'}
            ]
          }
        };

        var expected = {
          groupFoo: {
            name: 'Foo Objects',
            items: [{value: 'Contract'}]
          },
          groupBar: {
            name: 'Bar Objects',
            items: [{value: 'Policy'}]
          }
          // the groupBaz group, being empty, is expected to have been removed
        };

        fakeMapper.initTypes.and.returnValue(objectTypes);
        result = instance._choosableObjectTypes();
        expect(result).toEqual(expected);
      }
    );
  });

  describe('_packPeopleData() method', function () {
    it('packs default people data into a JSON string', function () {
      var result;

      instance.attr('default_people', {
        assessors: 'Rabbits',
        verifiers: 'Turtles'
      });

      result = instance._packPeopleData();

      expect(result).toEqual({
        assessors: 'Rabbits',
        verifiers: 'Turtles'
      });
    });

    it('uses the list of chosen assessor IDs if default assessors are set ' +
      'to "other"',
      function () {
        var assessorIds;
        var result;

        instance.attr('default_people', {
          assessors: 'other',
          verifiers: 'Whatever'
        });

        assessorIds = new can.Map({'17': true, '2': true, '9': true});
        instance.attr('assessorsList', assessorIds);

        result = instance._packPeopleData();

        expect(result).toEqual({
          assessors: [2, 9, 17],
          verifiers: 'Whatever'
        });
      }
    );

    it('uses the list of chosen verifier IDs if default verifiers are set ' +
      'to "other"',
      function () {
        var verifierIds;
        var result;

        instance.attr('default_people', {
          assessors: 'Whatever',
          verifiers: 'other'
        });

        verifierIds = new can.Map({'12': true, '6': true, '11': true});
        instance.attr('verifiersList', verifierIds);

        result = instance._packPeopleData();

        expect(result).toEqual({
          assessors: 'Whatever',
          verifiers: [6, 11, 12]
        });
      }
    );
  });

  describe('_unpackPeopleData() method', function () {
    it('builds an IDs dict from the default assessors list', function () {
      instance.attr('default_people', {
        assessors: new can.List([5, 7, 12])
      });
      instance.attr('assessorsList', {});

      instance._unpackPeopleData();

      expect(
        instance.assessorsList.attr()
      ).toEqual({'5': true, '7': true, '12': true});
    });

    it('sets the default assessors option to "other" if needed', function () {
      // this is needed when the default assessors setting is actually
      // a list of User IDs...
      instance.attr('default_people', {
        assessors: new can.List([5, 7, 12])
      });

      instance._unpackPeopleData();

      expect(instance.default_people.assessors).toEqual('other');
    });

    it('clears the assessors IDs dict if needed', function () {
      instance.attr('assessorsList', {'42': true});
      instance.attr('default_people', {
        assessors: 'Some User Group'  // not a list of IDs
      });

      instance._unpackPeopleData();

      expect(instance.assessorsList.attr()).toEqual({});
    });

    it('builds an IDs dict from the default verifiers list', function () {
      instance.attr('default_people', {
        verifiers: new can.List([5, 7, 12])
      });
      instance.attr('verifiersList', {});

      instance._unpackPeopleData();

      expect(
        instance.verifiersList.attr()
      ).toEqual({'5': true, '7': true, '12': true});
    });

    it('sets the default verifiers option to "other" if needed', function () {
      // this is needed when the default verifiers setting is actually
      // a list of User IDs...
      instance.attr('default_people', {
        verifiers: new can.List([5, 7, 12])
      });

      instance._unpackPeopleData();

      expect(instance.default_people.verifiers).toEqual('other');
    });

    it('clears the verifiers IDs dict if needed', function () {
      instance.attr('verifiersList', {'42': true});
      instance.attr('default_people', {
        verifiers: 'Some User Group'  // not a list of IDs
      });

      instance._unpackPeopleData();

      expect(instance.verifiersList.attr()).toEqual({});
    });
  });

  describe('assessorAdded() method', function () {
    var context;
    var $element;
    var eventObj;

    beforeEach(function () {
      context = {};
      $element = $('<div></div>');
      eventObj = $.Event();
    });

    it('adds the new assessor\'s ID to the assessors list', function () {
      instance.attr('assessorsList', {'7': true});
      eventObj.selectedItem = {id: 42};

      instance.assessorAdded(context, $element, eventObj);

      expect(
        instance.attr('assessorsList').attr()
      ).toEqual({'7': true, '42': true});
    });

    it('silently ignores duplicate entries', function () {
      instance.attr('assessorsList', {'7': true});
      eventObj.selectedItem = {id: 7};

      instance.assessorAdded(context, $element, eventObj);
      // there should have been no error

      expect(instance.attr('assessorsList').attr()).toEqual({'7': true});
    });
  });

  describe('assessorRemoved() method', function () {
    var context;
    var $element;
    var eventObj;

    beforeEach(function () {
      context = {};
      $element = $('<div></div>');
      eventObj = $.Event();
    });

    it('removes the new assessor\'s ID from the assessors list', function () {
      instance.attr('assessorsList', {'7': true, '42': true, '3': true});
      eventObj.person = {id: 42};

      instance.assessorRemoved(context, $element, eventObj);

      expect(
        instance.attr('assessorsList').attr()
      ).toEqual({'7': true, '3': true});
    });

    it('silently ignores removing non-existing entries', function () {
      instance.attr('assessorsList', {'7': true});
      eventObj.person = {id: 50};

      instance.assessorRemoved(context, $element, eventObj);
      // there should have been no error

      expect(instance.attr('assessorsList').attr()).toEqual({'7': true});
    });
  });

  describe('verifierAdded() method', function () {
    var context;
    var $element;
    var eventObj;

    beforeEach(function () {
      context = {};
      $element = $('<div></div>');
      eventObj = $.Event();
    });

    it('adds the new verifier\'s ID to the assessors list', function () {
      instance.attr('verifiersList', {'7': true});
      eventObj.selectedItem = {id: 42};

      instance.verifierAdded(context, $element, eventObj);

      expect(
        instance.attr('verifiersList').attr()
      ).toEqual({'7': true, '42': true});
    });

    it('silently ignores duplicate entries', function () {
      instance.attr('verifiersList', {'7': true});
      eventObj.selectedItem = {id: 7};

      instance.verifierAdded(context, $element, eventObj);
      // there should have been no error

      expect(instance.attr('verifiersList').attr()).toEqual({'7': true});
    });
  });

  describe('verifierRemoved() method', function () {
    var context;
    var $element;
    var eventObj;

    beforeEach(function () {
      context = {};
      $element = $('<div></div>');
      eventObj = $.Event();
    });

    it('removes the new verifier\'s ID from the verifiers list', function () {
      instance.attr('verifiersList', {'7': true, '42': true, '3': true});
      eventObj.person = {id: 42};

      instance.verifierRemoved(context, $element, eventObj);

      expect(
        instance.attr('verifiersList').attr()
      ).toEqual({'7': true, '3': true});
    });

    it('silently ignores removing non-existing entries', function () {
      instance.attr('verifiersList', {'7': true});
      eventObj.person = {id: 50};

      instance.verifierRemoved(context, $element, eventObj);
      // there should have been no error

      expect(instance.attr('verifiersList').attr()).toEqual({'7': true});
    });
  });

  describe('defaultAssesorsChanged() method', function () {
    var context;
    var $element;
    var eventObj;

    beforeEach(function () {
      context = {};
      $element = $('<div></div>');
      eventObj = $.Event();
    });

    it('sets the assessorsListDisable flag if the corresponding ' +
      'selected option is different from "other"',
      function () {
        instance.attr('assessorsListDisable', false);
        instance.attr('default_people.assessors', 'Object Admins');

        instance.defaultAssesorsChanged(context, $element, eventObj);

        expect(instance.attr('assessorsListDisable')).toBe(true);
      }
    );

    it('clears the assessorsListDisable flag if the corresponding ' +
      'selected option is "other"',
      function () {
        instance.attr('assessorsListDisable', true);
        instance.attr('default_people.assessors', 'other');

        instance.defaultAssesorsChanged(context, $element, eventObj);

        expect(instance.attr('assessorsListDisable')).toBe(false);
      }
    );
  });

  describe('defaultVerifiersChanged() method', function () {
    var context;
    var $element;
    var eventObj;

    beforeEach(function () {
      context = {};
      $element = $('<div></div>');
      eventObj = $.Event();
    });

    it('sets the verifiersListDisable flag if the corresponding ' +
      'selected option is different from "other"',
      function () {
        instance.attr('verifiersListDisable', false);
        instance.attr('default_people.verifiers', 'Object Admins');

        instance.defaultVerifiersChanged(context, $element, eventObj);

        expect(instance.attr('verifiersListDisable')).toBe(true);
      }
    );

    it('clears the verifiersListDisable flag if the corresponding ' +
      'selected option is "other"',
      function () {
        instance.attr('verifiersListDisable', true);
        instance.attr('default_people.verifiers', 'other');

        instance.defaultVerifiersChanged(context, $element, eventObj);

        expect(instance.attr('verifiersListDisable')).toBe(false);
      }
    );
  });
});
