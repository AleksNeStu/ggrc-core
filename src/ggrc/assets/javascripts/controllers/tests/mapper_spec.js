/*!
    Copyright (C) 2017 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

describe('GGRC.Controllers.ObjectMapper', function () {
  'use strict';
  var Ctrl;

  beforeAll(function () {
    Ctrl = GGRC.Controllers.ObjectMapper;
  });

  describe('static openMapper method()', function () {
    var method;
    var fakeCtrlInst;
    var fakeData;
    var originalModel;
    var updateScopeObject;
    var scopeObject;

    beforeAll(function () {
      originalModel = CMS.Models.Assessment;
    });

    afterAll(function () {
      CMS.Models.Assessment = originalModel;
    });

    beforeEach(function () {
      updateScopeObject = can.Deferred().resolve();
      scopeObject = new can.Map({
        id: 1
      });

      CMS.Models.Assessment = {
        store: [
          new can.Map({
            updateScopeObject: jasmine.createSpy('updateScopeObject')
              .and
              .returnValue(updateScopeObject),
            scopeObject: scopeObject
          })
        ]
      };
      fakeCtrlInst = {
        launch: jasmine.createSpy('launch')
      };
      fakeData = {
        toggle: 'unified-mapper',
        join_object_type: 'Assessment',
        join_object_id: 0,
        join_option_type: 'Type'
      };
      method = Ctrl.openMapper.bind(fakeCtrlInst);
      spyOn(GGRC.Errors, 'notifier');
    });

    it('interrupts own work if disableMapper param is true', function () {
      method(fakeData, true);

      expect(fakeCtrlInst.launch).not.toHaveBeenCalled();
    });

    it('throws Error with message if data.join_object_type does not exist',
    function () {
      var closure = function () {
        method({});
      };

      expect(closure).toThrowError();
    });

    describe('shows mapper for snapshots', function () {
      it('calls launch method with params',
      function (done) {
        var btn = {};
        method(fakeData, false, btn);

        updateScopeObject.then(function () {
          expect(fakeCtrlInst.launch).toHaveBeenCalledWith(
            btn,
            jasmine.objectContaining({
              general: jasmine.any(Object),
              special: jasmine.any(Array)
            })
          );

          done();
        });
      });

      it('extends generalConfig with "object", "type" and "relevantTo" if ' +
      'data has is_new',
      function (done) {
        var args;
        method(_.extend(fakeData, {
          is_new: true
        }), false);

        args = fakeCtrlInst.launch.calls.argsFor(0);

        // so hard:(
        updateScopeObject.then(function () {
          expect(args[1]).toEqual(
            jasmine.objectContaining({
              general: jasmine.objectContaining({
                object: fakeData.join_object_type,
                type: fakeData.join_option_type,
                relevantTo: jasmine.any(Array)
              })
            })
          );
          expect(args[1].general['join-object-id']).toBeNull();
          done();
        });
      });

      it('throws Error with message if data.join_object_id does not exist',
      function () {
        var closure = function () {
          method(_.omit(fakeData, 'join_object_id'));
        };

        expect(closure).toThrowError();
      });
    });

    describe('shows mapper for common objects', function () {
      var fakeDataForCommon;

      beforeEach(function () {
        fakeDataForCommon = _.extend({}, fakeData, {
          toggle: 'unified unified-search'
        });
        spyOn(GGRC.Controllers.ObjectSearch, 'launch');
      });

      it('sets config without relevantTo section if data.join_object_type ' +
      'is not in scope model', function () {
        var args;
        method(fakeDataForCommon, false, {});
        args = GGRC.Controllers.ObjectSearch.launch.calls.argsFor(0);

        expect(args[1]).not.toEqual(jasmine.objectContaining({
          relevantTo: jasmine.any(Array)
        }));
      });

      it('calls launch for ObjectSearch with passed btn and config if ' +
      'data.toggle contains "unified-search" string', function () {
        var btn = {};
        method(fakeDataForCommon, false, btn);

        expect(GGRC.Controllers.ObjectSearch.launch).toHaveBeenCalledWith(
          btn,
          jasmine.any(Object)
        );
      });

      it('calls launch for ObjectMapper with passed btn and config if ' +
      'data.toggle contains "unified-search" string', function () {
        var btn = {};
        fakeDataForCommon.toggle = '';
        method(fakeDataForCommon, false, btn);

        expect(fakeCtrlInst.launch).toHaveBeenCalledWith(
          btn,
          jasmine.any(Object)
        );
      });
    });
  });
});
