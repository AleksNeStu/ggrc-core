/*!
  Copyright (C) 2017 Google Inc.
  Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

describe('GGRC.Components.objectMapper', function () {
  'use strict';

  var Component;
  var events;
  var viewModel;
  var handler;
  var helpers;

  beforeAll(function () {
    Component = GGRC.Components.get('objectMapper');
    events = Component.prototype.events;
    helpers = Component.prototype.helpers;
  });

  describe('viewModel() method', function () {
    var parentViewModel;
    beforeEach(function () {
      parentViewModel = new can.Map({
        generalConfig: {
          useSnapshots: false
        },
        specialConfigs: []
      });
    });
    it('returns object with function "isLoadingOrSaving"', function () {
      var result = Component.prototype.viewModel({}, parentViewModel)();
      expect(result.isLoadingOrSaving).toEqual(jasmine.any(Function));
    });

    describe('initializes useSnapshots flag', function () {
      it('with true if set with help a general config', function () {
        var result;
        parentViewModel.generalConfig.useSnapshots = true;
        result = Component.prototype.viewModel({}, parentViewModel)();
        expect(result.attr('useSnapshots')).toEqual(true);
      });

      it('do not use Snapshots if not an in-scope model', function () {
        var result;
        spyOn(GGRC.Utils.Snapshots, 'isInScopeModel')
          .and.returnValue(false);
        result = Component.prototype.viewModel({}, parentViewModel)();
        expect(result.attr('useSnapshots')).toEqual(false);
      });
    });

    describe('isLoadingOrSaving() method', function () {
      beforeEach(function () {
        viewModel = new Component.prototype.viewModel({}, parentViewModel)();
      });
      it('returns true if it is saving', function () {
        viewModel.attr('is_saving', true);
        expect(viewModel.isLoadingOrSaving()).toEqual(true);
      });
      it('returns true if it is loading', function () {
        viewModel.attr('is_loading', true);
        expect(viewModel.isLoadingOrSaving()).toEqual(true);
      });
      it('returns false if page is not loading, it is not saving,' +
      ' type change is not blocked and it is not loading', function () {
        viewModel.attr('is_saving', false);
        viewModel.attr('is_loading', false);
        expect(viewModel.isLoadingOrSaving()).toEqual(false);
      });
    });

    describe('onSubmit() method', function () {
      var vm;
      var queue;

      beforeEach(function () {
        vm = new Component.prototype.viewModel({}, parentViewModel)();
        queue = [{
          a: 1
        }, {
          a: 2
        }, {
          b: 3
        }];
        vm.attr('pendingConfigQueue', queue);
        spyOn(vm, 'update');
      });

      it('updates VM with help resolved configs from pendingConfigQueue ' +
      'to one common config',
      function () {
        vm.onSubmit();

        expect(vm.update).toHaveBeenCalledWith(
          GGRC.Utils.resolveQueue(queue)
        );
      });
    });

    describe('prepareConfig() method', function () {
      var vm;

      beforeEach(function () {
        vm = new Component.prototype.viewModel({}, parentViewModel)();
        spyOn(vm, 'update');
      });

      it('pushes config to pending config queue', function () {
        var config = {};
        var addedConfig;

        vm.prepareConfig(config);
        addedConfig = vm.attr('pendingConfigQueue')[0].serialize();
        expect(addedConfig).toEqual(config);
      });

      it('updates relatedTo field for VM', function () {
        var config = {
          relevantTo: [{}]
        };
        vm.prepareConfig(config);

        expect(vm.update).toHaveBeenCalledWith(config);
      });
    });
  });

  describe('".create-control modal:success" event', function () {
    var spyObj;

    beforeEach(function () {
      viewModel.attr({
        newEntries: []
      });
      handler = events['.create-control modal:success'];
      spyObj = jasmine.createSpy();
    });

    it('adds model to newEntries', function () {
      viewModel.attr('newEntries', []);
      handler.call({
        viewModel: viewModel,
        mapObjects: spyObj
      }, {}, {}, 'model');
      expect(viewModel.attr('newEntries').length).toEqual(1);
      expect(viewModel.attr('newEntries')[0]).toEqual('model');
    });

    it('calls mapObjects to map results', function () {
      handler.call({
        viewModel: viewModel,
        mapObjects: spyObj
      }, {}, {}, 'model');
      expect(spyObj).toHaveBeenCalledWith(viewModel.attr('newEntries'));
    });
  });

  describe('".create-control click" event', function () {
    var element = {};

    beforeEach(function () {
      viewModel.attr({});
      handler = events['.create-control click'];
      element.trigger = jasmine.createSpy();
    });

    it('sets empty array to newEntries', function () {
      handler.call({viewModel: viewModel, element: element});
      expect(viewModel.attr('newEntries').length)
        .toEqual(0);
    });

    it('triggers "hideModal" event', function () {
      handler.call({viewModel: viewModel, element: element});
      expect(element.trigger).toHaveBeenCalledWith('hideModal');
    });
  });

  describe('".create-control modal:added" event', function () {
    beforeEach(function () {
      viewModel.attr({newEntries: []});
      handler = events['.create-control modal:added'];
    });

    it('adds model to newEntries', function () {
      handler.call({viewModel: viewModel}, {}, {}, 'model');
      expect(viewModel.attr('newEntries').length).toEqual(1);
      expect(viewModel.attr('newEntries')[0]).toEqual('model');
    });
  });

  describe('"{window} modal:dismiss" event', function () {
    var options;
    var spyObj;
    var element = {};

    beforeEach(function () {
      viewModel.attr({
        join_object_id: 123,
        newEntries: [1]
      });
      handler = events['{window} modal:dismiss'];
      spyObj = jasmine.createSpy();
      element.trigger = jasmine.createSpy();
    });

    it('calls mapObjects from mapper-results' +
    'if there are newEntries and ids are equal', function () {
      options = {
        uniqueId: 123
      };
      handler.call({
        viewModel: viewModel,
        mapObjects: spyObj
      }, {}, {}, options);
      expect(spyObj).toHaveBeenCalled();
    });

    it('does not call mapObjects from mapper-results' +
      'if there are newEntries and ids are not equal', function () {
      options = {
        uniqueId: 321
      };
      handler.call({
        viewModel: viewModel,
        mapObjects: spyObj,
        element: element
      }, {}, {}, options);
      expect(spyObj).not.toHaveBeenCalled();
    });

    it('triggers "showModel event"' +
      'if there are newEntries and ids are not equal', function () {
      options = {
        uniqueId: 321
      };
      handler.call({
        viewModel: viewModel,
        mapObjects: spyObj,
        element: element
      }, {}, {}, options);
      expect(element.trigger).toHaveBeenCalledWith('showModal');
    });

    it('does not calls mapObjects from mapper-results' +
    'if there are no newEntries', function () {
      viewModel.attr('newEntries', []);
      options = {
        uniqueId: 123
      };
      handler.call({
        viewModel: viewModel,
        mapObjects: spyObj,
        element: element
      }, {}, {}, options);
      expect(spyObj).not.toHaveBeenCalled();
    });

    it('triggers "showModal"' +
    'if there are no newEntries', function () {
      viewModel.attr('newEntries', []);
      options = {
        uniqueId: 123
      };
      handler.call({
        viewModel: viewModel,
        mapObjects: spyObj,
        element: element
      }, {}, {}, options);
      expect(element.trigger).toHaveBeenCalledWith('showModal');
    });
  });

  describe('"inserted" event', function () {
    var that;

    beforeEach(function () {
      viewModel.attr({
        selected: [1, 2, 3],
        entries: [3, 2, 1],
        onSubmit: function () {}
      });
      that = {
        viewModel: viewModel
      };
      handler = events.inserted;
    });

    it('sets empty array to selected', function () {
      handler.call(that);
      expect(viewModel.attr('selected').length)
        .toEqual(0);
    });
    it('sets empty array to entries', function () {
      handler.call(that);
      expect(viewModel.attr('entries').length)
        .toEqual(0);
    });
  });

  describe('"closeModal" event', function () {
    var element;
    var spyObj;

    beforeEach(function () {
      viewModel.attr({});
      spyObj = {
        trigger: function () {}
      };
      element = {
        find: function () {
          return spyObj;
        }
      };
      spyOn(spyObj, 'trigger');
      handler = events.closeModal;
    });

    it('sets false to is_saving', function () {
      viewModel.attr('is_saving', true);
      handler.call({
        element: element,
        viewModel: viewModel
      });
      expect(viewModel.attr('is_saving')).toEqual(false);
    });
    it('dismiss the modal', function () {
      handler.call({
        element: element,
        viewModel: viewModel
      });
      expect(spyObj.trigger).toHaveBeenCalledWith('click');
    });
  });

  describe('"deferredSave" event', function () {
    var that;
    var spyObj;

    beforeEach(function () {
      spyObj = {
        trigger: function () {}
      };
      viewModel.attr({
        object: 'source'
      });
      viewModel.attr('deferred_to', {
        controller: {element: spyObj}
      });
      spyObj = viewModel.attr('deferred_to').controller.element;
      that = {
        viewModel: viewModel,
        closeModal: function () {}
      };
      spyOn(that, 'closeModal');
      spyOn(spyObj, 'trigger');
      handler = events.deferredSave;
    });

    it('calls deferredSave', function () {
      handler.call(that);
      expect(spyObj.trigger)
        .toHaveBeenCalledWith('defer:add', [
          {multi_map: true, arr: []},
          {map_and_save: true}
        ]);
    });
    it('calls closeModal', function () {
      handler.call(that);
      expect(that.closeModal).toHaveBeenCalled();
    });
  });

  describe('".modal-footer .btn-map click" handler', function () {
    var that;
    var event;
    var element;

    beforeEach(function () {
      viewModel.attr({
        type: 'type',
        object: 'Program',
        join_object_id: '123',
        selected: []
      });
      viewModel.attr('deferred', false);
      spyOn(CMS.Models.Program, 'findInCacheById')
        .and.returnValue('instance');
      event = {
        preventDefault: function () {}
      };
      element = $('<div></div>');
      handler = events['.modal-footer .btn-map click'];
      that = {
        viewModel: viewModel,
        closeModal: jasmine.createSpy(),
        deferredSave: jasmine.createSpy().and.returnValue('deferredSave'),
        mapObjects: events.mapObjects
      };
      spyOn(window, 'RefreshQueue')
        .and.returnValue({
          enqueue: function () {
            return {
              trigger: jasmine.createSpy()
                .and.returnValue(can.Deferred().resolve())
            };
          }
        });
      spyOn($.prototype, 'trigger');
    });

    it('does nothing if element has class "disabled"', function () {
      var result;
      element.addClass('disabled');
      result = handler.call(that, element, event);
      expect(result).toEqual(undefined);
    });

    it('calls deferredSave if it is deferred', function () {
      var result;
      viewModel.attr('deferred', true);
      result = handler.call(that, element, event);
      expect(result).toEqual('deferredSave');
    });
    it('calls closeModal()', function () {
      handler.call(that, element, event);
      expect(that.closeModal).toHaveBeenCalled();
    });
    it('triggers error message if fail', function () {
      spyOn($, 'when')
        .and.returnValue(can.Deferred().reject());
      handler.call(that, element, event);
      expect($.prototype.trigger)
        .toHaveBeenCalledWith('ajax:flash', {error: undefined});
    });
  });

  describe('get_title() helper', function () {
    var helper;
    beforeEach(function () {
      helper = helpers.get_title;
    });

    it('returns title of parentInstance if parentInstance defined',
      function () {
        var result;
        spyOn(CMS.Models, 'get_instance').and.returnValue({
          title: 'mockTitle'
        });
        result = helper.call(viewModel);
        expect(result).toEqual('mockTitle');
      });
    it('returns object if parentInstance undefined',
      function () {
        var result;
        viewModel.attr({
          object: 'mockInstance',
          parentInstance: undefined
        });
        result = helper.call(viewModel);
        expect(result).toEqual('mockInstance');
      });
  });

  describe('get_object() helper', function () {
    var helper;

    beforeEach(function () {
      helper = helpers.get_object;
    });

    it('returns type.title_plural if it is defined', function () {
      var result;
      viewModel.attr({
        type: 'Program'
      });
      result = helper.call(viewModel);
      expect(result).toEqual('Programs');
    });
    it('returns "Objects" if type.title_plural is null', function () {
      var result;
      viewModel.attr({
        type: null
      });
      result = helper.call(viewModel);
      expect(result).toEqual('Objects');
    });
  });

  describe('allowedToCreate() method', function () {
    it('returns true if it is not an in-scope model',
      function () {
        var result;
        spyOn(GGRC.Utils.Snapshots, 'isInScopeModel')
          .and.returnValue(false);
        result = viewModel.allowedToCreate();
        expect(result).toEqual(true);
      });
    it('returns false if it is an in-scope model',
      function () {
        var result;
        spyOn(GGRC.Utils.Snapshots, 'isInScopeModel')
          .and.returnValue(true);
        result = viewModel.allowedToCreate();
        expect(result).toEqual(false);
      });
  });

  describe('showWarning() method', function () {
    it('returns false if is an in-scope model', function () {
      var result;
      spyOn(GGRC.Utils.Snapshots, 'isInScopeModel')
        .and.returnValue(true);
      result = viewModel.showWarning();
      expect(result).toEqual(false);
    });

    it('returns true if source object is a Snapshot parent', function () {
      var result;
      spyOn(GGRC.Utils.Snapshots, 'isInScopeModel')
        .and.returnValue(false);
      spyOn(GGRC.Utils.Snapshots, 'isSnapshotParent')
        .and.callFake(function (v) {
          return v === 'o';
        });
      viewModel.attr('object', 'o');
      viewModel.attr('type', 't');
      result = viewModel.showWarning();
      expect(result).toEqual(true);
    });

    it('returns true if is mapped object is a ' +
      'Snapshot parent', function () {
      var result;
      spyOn(GGRC.Utils.Snapshots, 'isInScopeModel')
        .and.returnValue(false);
      spyOn(GGRC.Utils.Snapshots, 'isSnapshotParent')
        .and.callFake(function (v) {
          return v === 't';
        });
      viewModel.attr('object', 'o');
      viewModel.attr('type', 't');
      result = viewModel.showWarning();
      expect(result).toEqual(true);
    });
  });
});
