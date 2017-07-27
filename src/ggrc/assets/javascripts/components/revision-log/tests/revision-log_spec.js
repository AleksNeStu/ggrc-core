/*!
  Copyright (C) 2017 Google Inc.
  Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

describe('GGRC.Components.revisionLog', function () {
  'use strict';

  var viewModel;

  beforeAll(function () {
    viewModel = GGRC.Components.getViewModel('revisionLog');
  });

  afterAll(function () {
    viewModel = GGRC.Components.getViewModel('revisionLog');
  });

  describe('defining default scope values', function () {
    it('sets the instance to null', function () {
      expect(JSON.stringify(viewModel.attr('instance').attr()))
        .toBe(JSON.stringify({}));
    });

    it('sets the change history to an empty array', function () {
      expect(viewModel.attr('changeHistory').length).toEqual(0);
    });
  });

  describe('fetchItems() method', function () {
    var dfdFetchData;

    beforeEach(function () {
      dfdFetchData = can.Deferred();
      spyOn(viewModel, '_fetchRevisionsData').and.returnValue(dfdFetchData);
    });

    afterEach(function () {
      viewModel._fetchRevisionsData.calls.reset();
    });

    afterAll(function () {
      viewModel = GGRC.Components.getViewModel('revisionLog');
    });

    it('displays a toaster error if fetching the data fails', function () {
      var $fakeElement = {
        trigger: jasmine.createSpy()
      };

      spyOn(window, '$').and.returnValue($fakeElement);

      viewModel.fetchItems();
      dfdFetchData.reject('Server error');

      expect(window.$).toHaveBeenCalled();
      expect($fakeElement.trigger).toHaveBeenCalledWith(
        'ajax:flash',
        {error: 'Failed to fetch revision history data.'}
      );
    });

    it('on successfully fetching the data it sets the correctly sorted ' +
      'change history in the scope',
      function () {
        var actual;
        var expected;

        var fetchedRevisions = new can.Map({
          object: new can.List([
            {id: 10}
          ]),
          mappings: new can.List([
            {id: 20}
          ])
        });

        var mapChange = {updatedAt: new Date('2015-12-21')};
        var mapChange2 = {updatedAt: new Date('2016-03-17')};

        var objChange = {updatedAt: new Date('2016-04-14')};
        var objChange2 = {updatedAt: new Date('2014-11-18')};
        var objChange3 = {updatedAt: new Date('2016-01-09')};

        viewModel.attr('changeHistory', []);

        spyOn(viewModel, '_computeMappingChanges').and.returnValue(
          new can.List([mapChange, mapChange2])
        );
        spyOn(viewModel, '_computeRoleChanges');
        spyOn(viewModel, '_computeObjectChanges').and.returnValue(
          new can.List([objChange, objChange2, objChange3])
        );
        // end fixture

        viewModel.fetchItems();
        dfdFetchData.resolve(fetchedRevisions);

        // check that correct data has been used to calculate the history
        expect(viewModel._computeObjectChanges)
          .toHaveBeenCalledWith(fetchedRevisions.object);
        expect(viewModel._computeMappingChanges)
          .toHaveBeenCalledWith(fetchedRevisions.mappings);

        // check the actual outcome
        actual = can.makeArray(viewModel.attr('changeHistory'));
        actual = _.map(actual, function (item) {
          return item.attr();
        });
        // sorted by newest to oldest
        expected = [objChange, mapChange2, objChange3, mapChange, objChange2];

        expect(actual).toEqual(expected);
      }
    );
  });

  describe('_computeObjectChanges() method', function () {
    afterEach(function () {
      viewModel._objectChangeDiff.calls.reset();
    });

    afterAll(function () {
      viewModel = GGRC.Components.getViewModel('revisionLog');
    });

    it('computes an empty list on empty Revision history', function () {
      var result;
      var revisions = new can.List();

      spyOn(viewModel, '_objectChangeDiff');
      result = viewModel._computeObjectChanges(revisions);

      expect(result.length).toEqual(0);
    });

    it('computes diff objects for all successive Revision pairs', function () {
      var result;

      var revisions = [
        {id: 10}, {id: 20}, {id: 30}
      ];

      var diff = {
        madeBy: 'John',
        changes: [
          {fieldName: 'foo'}
        ]
      };
      var diff2 = {
        madeBy: 'Doe',
        changes: [
          {fieldName: 'bar'}
        ]
      };

      spyOn(viewModel, '_objectChangeDiff').and.returnValues(diff, diff2);

      result = viewModel._computeObjectChanges(revisions);

      expect(viewModel._objectChangeDiff.calls.count()).toEqual(3);

      expect(result.length).toEqual(2);
      expect(result[0]).toEqual(diff);
      expect(result[1]).toEqual(diff2);
    });

    it('omits the diff objects with an empty changes list from the result',
      function () {
        var result;

        var revisions = [
          {id: 10}, {id: 20}
        ];

        var diff = {
          changes: []
        };
        spyOn(viewModel, '_objectChangeDiff').and.returnValue(diff);

        result = viewModel._computeObjectChanges(revisions);

        expect(result.length).toEqual(0);
      }
    );
  });

  describe('_objectChangeDiff() method', function () {
    var origModelAttrDefs = GGRC.model_attr_defs;  // original user-friendly attribute name settings

    beforeAll(function () {
      spyOn(viewModel, '_objectCADiff').and.returnValue({});
      spyOn(viewModel, '_computeRoleChanges').and.returnValue([]);
      spyOn(viewModel, '_getRoleAtTime').and.returnValue('none');
      viewModel.attr('_LIST_FIELDS', {fake_list: 1});
    });
    beforeEach(function () {
      GGRC.model_attr_defs = {};
    });

    afterAll(function () {
      GGRC.model_attr_defs = origModelAttrDefs;
      viewModel = GGRC.Components.getViewModel('revisionLog');
    });

    it('includes the modification time in the result', function () {
      var rev1 = {
        updated_at: '2016-01-24T10:05:42',
        modified_by: 'User 1',
        content: {}
      };
      var rev2 = {
        updated_at: '2016-01-30T08:15:11',
        modified_by: 'User 1',
        content: {}
      };

      var result = viewModel._objectChangeDiff(rev1, rev2);

      expect(result.updatedAt).toEqual('2016-01-30T08:15:11');
    });

    it('includes the author of the change(s) in the result', function () {
      var rev1 = {
        updated_at: '2016-01-24T10:05:42',
        modified_by: 'User 7',
        content: {}
      };
      var rev2 = {
        updated_at: '2016-01-30T08:15:11',
        modified_by: 'User 7',
        content: {}
      };

      var result = viewModel._objectChangeDiff(rev1, rev2);

      expect(result.madeBy).toEqual('User 7');
    });

    describe('with model attributes definitions defined', function () {
      it('uses the fields\' display names in the result', function () {
        var expectedChange = {
          fieldName: 'Object Name',
          origVal: 'Audit 1.0',
          newVal: 'My Audit 1.0'
        };

        var rev1 = {
          updated_at: '2016-01-25T16:36:29',
          modified_by: {
            reify: function () {
              return 'User 5';
            }
          },
          resource_type: 'Audit',
          content: {
            title: 'Audit 1.0'
          }
        };
        var rev2 = {
          updated_at: '2016-01-30T13:22:59',
          modified_by: {
            reify: function () {
              return 'User 5';
            }
          },
          resource_type: 'Audit',
          content: {
            title: 'My Audit 1.0'
          }
        };
        var result;

        GGRC.model_attr_defs = {
          Audit: [
            {attr_name: 'title', display_name: 'Object Name'},
            {attr_name: 'fake_list', display_name: 'Fake List'}
          ]
        };
        result = viewModel._objectChangeDiff(rev1, rev2);

        expect(result.changes[0]).toEqual(expectedChange);
      });

      it('compacts the list fields in the diff',
        function () {
          var rev1 = {
            updated_at: '2016-01-25T16:36:29',
            modified_by: {
              reify: function () {
                return 'User 5';
              }
            },
            resource_type: 'Audit',
            content: {
              fake_list: 'foo,,bar,'
            }
          };
          var rev2 = {
            updated_at: '2016-01-30T13:22:59',
            modified_by: {
              reify: function () {
                return 'User 5';
              }
            },
            resource_type: 'Audit',
            content: {
              fake_list: ',,bar,baz'
            }
          };
          var result;
          GGRC.model_attr_defs = {
            Audit: [
              {attr_name: 'title', display_name: 'Object Name'},
              {attr_name: 'fake_list', display_name: 'Fake List'}
            ]
          };
          result = viewModel._objectChangeDiff(rev1, rev2);

          expect(result.changes[0]).toEqual({
            fieldName: 'Fake List',
            origVal: 'foo, bar',
            newVal: 'bar, baz'
          });
        }
      );
    });
  });

  describe('_objectCADiff() method', function () {
    it('detects set attributes', function () {
      var oldAttrs = [];
      var newValues = [{
        id: 1,
        value: 'custom value'
      }];
      var newAttrs = [{
        id: 1,
        title: 'CA',
        attribute_type: 'Text',
        values: newValues
      }];
      var result = viewModel
        ._objectCADiff(oldAttrs, newAttrs);
      expect(result).toEqual([{
        fieldName: 'CA',
        origVal: '—',
        newVal: 'custom value'
      }]);
    });

    it('detects unset attributes', function () {
      var oldValues = [{
        id: 1,
        value: 'custom value'
      }];
      var oldAttrs = [{
        id: 1,
        title: 'CA',
        attribute_type: 'Text',
        values: oldValues
      }];
      var newAttrs = [];
      var result = viewModel
        ._objectCADiff(oldAttrs, newAttrs);
      expect(result).toEqual([{
        fieldName: 'CA',
        origVal: 'custom value',
        newVal: '—'
      }]);
    });

    it('detects multiple changed attributes', function () {
      var oldValues = [{
        id: 1,
        value: 'v1'
      }, {
        id: 2,
        value: 'v2'
      }, {
        id: 3,
        value: 'v3'
      }];

      var oldAttrs = [{
        id: 1,
        title: 'CA1',
        attribute_type: 'text',
        values: [oldValues[0]]
      }, {
        id: 2,
        title: 'CA2',
        attribute_type: 'text',
        values: [oldValues[1]]
      }, {
        id: 3,
        title: 'CA3',
        attribute_type: 'text',
        values: [oldValues[2]]
      }];

      var newValues = [{
        id: 1,
        value: 'v3'
      }, {
        id: 2,
        value: 'v4'
      }, {
        id: 3,
        value: 'v3'
      }];
      var newAttrs = [{
        id: 1,
        title: 'CA1',
        attribute_type: 'text',
        values: [newValues[0]]
      }, {
        id: 2,
        title: 'CA2',
        attribute_type: 'text',
        values: [newValues[1]]
      }, {
        id: 3,
        title: 'CA3',
        attribute_type: 'text',
        values: [newValues[2]]
      }];

      var result = viewModel
        ._objectCADiff(oldAttrs, newAttrs);
      expect(result).toEqual([{
        fieldName: 'CA1',
        origVal: 'v1',
        newVal: 'v3'
      }, {
        fieldName: 'CA2',
        origVal: 'v2',
        newVal: 'v4'
      }]);
    });
  });

  describe('_fetchRevisionsData() method', function () {
    var Revision;  // the Revision object constructor

    // fake Deferred objects to return from the mocked Revision.findAll()
    var dfdResource;
    var dfdSource;
    var dfdDestination;

    beforeEach(function () {
      // obtain a reference to the method under test, and bind it to a fake
      // instance context
      viewModel.attr('instance', {
        id: 123,
        type: 'ObjectFoo'
      });
      viewModel._fetchEmbeddedRevisionData = function () {
        return can.Deferred().resolve([]);
      };
    });

    afterAll(function () {
      viewModel = GGRC.Components.getViewModel('revisionLog');
    });

    beforeEach(function () {
      // mock the Revision model's findAll() method
      Revision = CMS.Models.Revision;

      dfdResource = new can.Deferred();
      dfdSource = new can.Deferred();
      dfdDestination = new can.Deferred();

      spyOn(Revision, 'findAll').and.callFake(function (options) {
        if (options.resource_type) {
          return dfdResource;
        } else if (options.source_type) {
          return dfdSource;
        } else if (options.destination_type) {
          return dfdDestination;
        }
        throw new Error('Revision.findAll() invoked with unexpected options.');
      });
    });

    it('fetches the Revision history of the correct object', function () {
      viewModel._fetchRevisionsData();

      expect(Revision.findAll).toHaveBeenCalledWith({
        resource_type: 'ObjectFoo',
        resource_id: 123,
        __sort: 'updated_at'
      });
    });

    it('fetches the Revision history of the correct object ' +
      'as a mapping source',
      function () {
        viewModel._fetchRevisionsData();

        expect(Revision.findAll).toHaveBeenCalledWith({
          source_type: 'ObjectFoo',
          source_id: 123,
          __sort: 'updated_at'
        });
      }
    );

    it('fetches the Revision history of the correct object ' +
      'as a mapping destination',
      function () {
        viewModel._fetchRevisionsData();

        expect(Revision.findAll).toHaveBeenCalledWith({
          destination_type: 'ObjectFoo',
          destination_id: 123,
          __sort: 'updated_at'
        });
      }
    );

    it('resolves the returned Deferred with the fetched data', function () {
      var result;
      var successHandler;

      var objRevisions = new can.List([
        {revision: 'objFoo'}, {revision: 'objBar'}
      ]);
      var mappingSrcRevisions = new can.List([
        {revision: 'mappingSrcFoo'}
      ]);
      var mappingDestRevisions = new can.List([
        {revision: 'mappingDestFoo'}
      ]);

      successHandler = jasmine.createSpy().and.callFake(function (revisions) {
        var objRevisions = can.makeArray(revisions.object);
        var mappingsRevisions = can.makeArray(revisions.mappings);

        function canMapToObject(item) {
          return item.attr();
        }
        objRevisions = _.map(objRevisions, canMapToObject);
        mappingsRevisions = _.map(mappingsRevisions, canMapToObject);

        expect(objRevisions).toEqual([
          {revision: 'objFoo'}, {revision: 'objBar'}
        ]);
        expect(mappingsRevisions).toEqual([
          {revision: 'mappingSrcFoo'}, {revision: 'mappingDestFoo'}
        ]);
      });

      result = viewModel._fetchRevisionsData();
      result.then(successHandler);

      dfdResource.resolve(objRevisions);
      dfdSource.resolve(mappingSrcRevisions);
      dfdDestination.resolve(mappingDestRevisions);

      // check that the returned Deferred has indeed been resolved
      expect(successHandler).toHaveBeenCalled();
    });
  });

  describe('_computeMappingChanges() method', function () {
    beforeAll(function () {
      spyOn(viewModel, '_mappingChange');
    });

    afterEach(function () {
      viewModel._mappingChange.calls.reset();
    });

    afterAll(function () {
      viewModel = GGRC.Components.getViewModel('revisionLog');
    });

    it('creates a list of mapping changes from a Revision list', function () {
      var result;
      var revisions = new can.List([
        {id: 10, madeBy: 'John'},
        {id: 20, madeBy: 'Doe'}
      ]);

      viewModel._mappingChange.and.callFake(function (revision) {
        return new can.Map({madeBy: revision.madeBy});
      });

      result = viewModel._computeMappingChanges(revisions);

      // we call attr() to get a plain object needed for the comparison
      expect(result[0].attr()).toEqual({madeBy: 'John'});
      expect(result[1].attr()).toEqual({madeBy: 'Doe'});
      expect(viewModel._mappingChange.calls.count()).toEqual(2);
    });
  });

  describe('_mappingChange() method', function () {
    beforeAll(function () {
      viewModel.attr('instance', {
        id: 123,
        type: 'ObjectFoo'
      });
      viewModel._getRoleAtTime = function () {
        return 'none';
      };
    });

    afterAll(function () {
      viewModel = GGRC.Components.getViewModel('revisionLog');
    });

    it('returns correct change information when the instance is at the ' +
      '"source" end of the mapping',
      function () {
        var revision = {
          modified_by: 'User 17',
          updated_at: new Date('2015-05-17T17:24:01'),
          action: 'created',
          destination: {
            display_type: function () {
              return 'Other';
            },
            display_name: function () {
              return 'OtherObject';
            }
          },
          source_id: 99,
          source_type: 'OtherObject'
        };

        var result = viewModel._mappingChange(revision, [revision]);

        expect(result).toEqual({
          madeBy: 'User 17',
          role: 'none',
          updatedAt: new Date('2015-05-17T17:24:01'),
          changes: {
            origVal: '—',
            newVal: 'Created',
            fieldName: 'Mapping to Other: OtherObject'
          }
        });
      }
    );

    it('returns correct change information when the instance is at the ' +
      '"destination" end of the mapping',
      function () {
        var revision = {
          modified_by: 'User 17',
          updated_at: new Date('2015-05-17T17:24:01'),
          action: 'deleted',
          source: {
            display_type: function () {
              return 'Other';
            },
            display_name: function () {
              return 'OtherObject';
            }
          },
          destination_id: 123,
          destination_type: 'ObjectFoo'
        };

        var result = viewModel._mappingChange(revision, [revision]);

        expect(result).toEqual({
          madeBy: 'User 17',
          role: 'none',
          updatedAt: new Date('2015-05-17T17:24:01'),
          changes: {
            origVal: 'Created',
            newVal: 'Deleted',
            fieldName: 'Mapping to Other: OtherObject'
          }
        });
      }
    );
  });

  describe('_computeRoleChanges method', function () {
    var corruptedRevision = new can.Map({
      object: new can.List([
        {
          id: 10,
          modified_by: {
            id: 166
          }
        }
      ]),
      mappings: new can.List([
        {
          id: 1,
          modified_by: {
            id: 166
          },
          action: 'created',
          source_type: 'Person',
          source_id: 166,
          destination_type: 'ObjectFoo',
          destination_id: 123,
          updated_at: new Date(2016, 0, 1),
          type: 'Revision',
          content: {
            attrs: {}
          }
        }
      ])
    });
    var revisions = new can.Map({
      object: new can.List([
        {
          id: 10,
          modified_by: {
            id: 166
          }
        }
      ]),
      mappings: new can.List([
        {
          id: 1,
          modified_by: {
            id: 166
          },
          action: 'created',
          source_type: 'Person',
          source_id: 166,
          destination_type: 'ObjectFoo',
          destination_id: 123,
          updated_at: new Date(2016, 0, 1),
          type: 'Revision',
          content: {
            attrs: {
              AssigneeType: 'Requester,Assignee'
            }
          }
        },
        {
          id: 2,
          modified_by: {
            id: 166
          },
          action: 'modified',
          source_type: 'Person',
          source_id: 166,
          destination_type: 'ObjectFoo',
          destination_id: 123,
          updated_at: new Date(2016, 0, 2),
          type: 'Revision',
          content: {
            attrs: {
              AssigneeType: 'Requester,Assignee,Verifier'
            }
          }
        },
        {
          id: 3,
          modified_by: {
            id: 166
          },
          action: 'modified',
          source_type: 'Person',
          source_id: 166,
          destination_type: 'ObjectFoo',
          destination_id: 123,
          updated_at: new Date(2016, 0, 4),
          type: 'Revision',
          content: {
            attrs: {
              AssigneeType: 'Requester'
            }
          }
        },
        {
          id: 4,
          modified_by: {
            id: 166
          },
          action: 'deleted',
          source_type: 'Person',
          source_id: 166,
          destination_type: 'ObjectFoo',
          destination_id: 123,
          updated_at: new Date(2016, 0, 5),
          type: 'Revision',
          content: {
            attrs: {
              AssigneeType: 'Requester'
            }
          }
        }
      ])
    });

    beforeAll(function () {
      viewModel.attr('instance', {
        id: 123,
        type: 'ObjectFoo',
        created_at: new Date(2016, 0, 1),
        'class': {
          assignable_list: [{
            type: 'requester',
            mapping: 'related_requesters'
          }, {
            type: 'assignee',
            mapping: 'related_assignees'
          }, {
            type: 'verifier',
            mapping: 'related_verifiers'
          }]
        },
        get_binding: function (mappingName) {
          var bindingData = {
            related_requesters: {
              list: [
                {
                  instance: {id: 166}
                }
              ]
            },
            related_assignees: {
              list: [
                {
                  instance: {id: 166}
                }
              ]
            },
            related_verifiers: {
              list: [
                {
                  instance: {id: 166}
                }
              ]
            }
          };
          return bindingData[mappingName];
        }
      });
    });

    afterAll(function () {
      viewModel = GGRC.Components.getViewModel('revisionLog');
    });
    it('returns current max role when no revisions exist', function () {
      var roleHistory = viewModel._computeRoleChanges([]);
      expect(roleHistory).toEqual({
        '166': [{
          role: 'Verifier',
          updated_at: new Date(2016, 0, 1)
        }]
      });
    });

    it('returns correct full history when present', function () {
      var roleHistory = viewModel._computeRoleChanges(revisions);
      expect(roleHistory).toEqual({
        '166': [
          {
            updated_at: new Date(2016, 0, 1),
            role: 'Assignee'
          },
          {
            updated_at: new Date(2016, 0, 2),
            role: 'Verifier'
          },
          {
            updated_at: new Date(2016, 0, 4),
            role: 'Requester'
          },
          {
            updated_at: new Date(2016, 0, 5),
            role: 'none'
          }
        ]
      });
    });

    it('builds correct full history when creation is not present', function () {
      var roleHistory;
      revisions.mappings.shift(); // remove first ("created") mapping
      roleHistory = viewModel._computeRoleChanges(revisions);
      expect(roleHistory).toEqual({
        '166': [
          {
            updated_at: new Date(2016, 0, 1),
            role: 'none'
          },
          {
            updated_at: new Date(2016, 0, 2),
            role: 'Verifier'
          },
          {
            updated_at: new Date(2016, 0, 4),
            role: 'Requester'
          },
          {
            updated_at: new Date(2016, 0, 5),
            role: 'none'
          }
        ]
      });
    });

    it('builds correct history when data is corrupted', function () {
      var roleHistory;

      roleHistory = viewModel._computeRoleChanges(corruptedRevision);
      expect(roleHistory).toEqual({
        '166': [
          {
            updated_at: new Date(2016, 0, 1),
            role: 'none'
          }
        ]
      });
    });
  });

  describe('_getRoleAtTime() method', function () {
    beforeAll(function () {
      viewModel.attr('roleHistory', {});
      viewModel.attr('roleHistory')[1] =
        [{
          role: 'creator',
          updated_at: new Date(2016, 0, 1)
        }, {
          role: 'verifier',
          updated_at: new Date(2016, 1, 2)
        }, {
          role: 'assignee',
          updated_at: new Date(2016, 2, 3)
        }];
    });

    afterAll(function () {
      viewModel = GGRC.Components.getViewModel('revisionLog');
    });
    it('returns correct role for a given person at initial time', function () {
      expect(viewModel
        ._getRoleAtTime(1, new Date(2016, 0, 1))).toEqual('creator');
    });
    it('returns correct role for a given person on first change', function () {
      expect(viewModel
        ._getRoleAtTime(1, new Date(2016, 1, 2))).toEqual('verifier');
    });
    it('returns correct role for a given person in the middle of interval',
      function () {
        expect(viewModel
          ._getRoleAtTime(1, new Date(2016, 1, 15))).toEqual('verifier');
      });
    it('returns correct role for a given person on third change', function () {
      expect(viewModel
        ._getRoleAtTime(1, new Date(2016, 2, 3))).toEqual('assignee');
    });
    it('returns correct role for a given person after last change',
      function () {
        expect(viewModel
          ._getRoleAtTime(1, new Date(2016, 3, 1))).toEqual('assignee');
      });

    it('returns "none" if there is no known role at that time', function () {
      expect(viewModel
        ._getRoleAtTime(1, new Date(2015, 1, 1))).toEqual('none');
    });
    it('returns "none" if there is no known role if no user history exists',
      function () {
        expect(viewModel
          ._getRoleAtTime(0, new Date(2016, 1, 10))).toEqual('none');
      });
    it('returns "none" if there is no known role and no user history ' +
       'exists on specific dates',
        function () {
          expect(viewModel
            ._getRoleAtTime(0, new Date(2016, 1, 2))).toEqual('none');
        });
  });
});
