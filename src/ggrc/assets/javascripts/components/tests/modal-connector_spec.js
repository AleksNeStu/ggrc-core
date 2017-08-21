/*!
  Copyright (C) 2017 Google Inc.
  Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

describe('GGRC.Components.modalConnector', function () {
  'use strict';

  var Component;
  var viewModel;
  var events;

  beforeAll(function () {
    Component = GGRC.Components.get('modalConnector');
    events = Component.prototype.events;
  });
  beforeEach(function () {
    viewModel = new can.Map();
  });
  describe('init() method', function () {
    var handler;
    var that;
    var reifiedInstance;
    var binding;
    beforeEach(function () {
      binding = {
        refresh_instances: jasmine.createSpy()
          .and.returnValue(can.Deferred().resolve('mockList'))
      };
      viewModel.attr({
        parent_instance: {
          _transient: {
            _mockSource: 'transientList'
          }
        },
        default_mappings: [{
          id: 123,
          type: 'Assessment'
        }],
        mapping: 'mockSource',
        setListItems: jasmine.createSpy(),
        instance_attr: ''
      });
      viewModel.instance = {
        reify: jasmine.createSpy().and.returnValue(reifiedInstance),
        mark_for_addition: jasmine.createSpy(),
        get_binding: jasmine.createSpy().and.returnValue(binding)
      };
      reifiedInstance = new can.Map(viewModel.instance);
      that = {
        viewModel: viewModel,
        addListItem: jasmine.createSpy(),
        setListItems: jasmine.createSpy(),
        options: {},
        on: jasmine.createSpy()
      };
      spyOn(CMS.Models.Assessment, 'findInCacheById')
        .and.returnValue('mockObject');
      handler = events.init.bind(that);
    });
    it('sets instance of component to viewModel.controller', function () {
      handler();
      expect(viewModel.attr('controller').viewModel)
        .toEqual(that.viewModel);
    });
    it('sets true to viewModel.deferred if viewModel.instance is undefined',
      function () {
        viewModel.instance = undefined;
        viewModel.default_mappings = [];
        handler();
        expect(viewModel.attr('deferred')).toEqual(true);
      });
    it('sets reified instance to viewModel if it is defined',
      function () {
        handler();
        expect(viewModel.attr('instance'))
          .toEqual(jasmine.any(can.Map));
        expect(!!viewModel.attr('instance').get_binding)
          .toEqual(true);
      });
    it('marks for addition mapped objects', function () {
      handler();
      expect(viewModel.instance.mark_for_addition)
        .toHaveBeenCalledWith('related_objects_as_source', 'mockObject',
          {});
    });
    it('adds to list mapped objects', function () {
      handler();
      expect(that.addListItem).toHaveBeenCalledWith('mockObject');
    });
    it('sets mapping to source_mapping if source_mapping is undefined',
      function () {
        handler();
        expect(viewModel.attr('source_mapping')).toEqual('mockSource');
      });
    it('sets "instance" to source_mapping_source if source_mapping_source' +
    ' is undefined',
      function () {
        handler();
        expect(viewModel.source_mapping_source)
          .toEqual('instance');
      });
    it('calls setListItems() after getting mapper list' +
    ' if mapper getter is defined', function () {
      handler();
      expect(that.setListItems).toHaveBeenCalledWith('mockList');
    });
    it('calls setListItems after refresing binding' +
    ' if mapper getter is undefined', function () {
      handler();
      expect(that.setListItems).toHaveBeenCalledWith('mockList');
    });
    it('sets empty array to viewModel.list' +
    ' and parent_instance._transient[key]' +
    ' if source mapping and parent_instance.transient[key] is undefined',
      function () {
        viewModel.source_mapping_source = 'a';
        viewModel.parent_instance._transient._mockSource = undefined;
        viewModel.attr('list', [1, 2, 3]);
        handler();
        expect(viewModel.attr('list').length).toEqual(0);
        expect(viewModel.parent_instance.attr('_transient._mockSource').length)
          .toEqual(0);
      });
    it('sets parent_instance._transient[key] to viewModel.list' +
    ' if source mapping is undefined',
      function () {
        viewModel.source_mapping_source = '';
        viewModel.attr('list', ['transientList']);
        handler();
        expect(viewModel.attr('list')[0]).toEqual('transientList');
      });
    it('sets parent_instance form viewModel to options', function () {
      handler();
      expect(that.options.parent_instance).toEqual(viewModel.parent_instance);
    });
    it('sets instance form viewModel to options', function () {
      handler();
      expect(that.options.instance).toEqual(viewModel.instance);
    });
    it('calls on() method', function () {
      handler();
      expect(that.on).toHaveBeenCalled();
    });
  });
  describe('destroy() method', function () {
    var handler;
    var that;
    beforeEach(function () {
      that = {
        viewModel: {
          parent_instance: new can.Map()
        }
      };
      handler = events.destroy.bind(that);
    });
    it('removes changes from parent_instance', function () {
      that.viewModel.parent_instance.attr('changes', [1, 2]);
      handler();
      expect(that.viewModel.parent_instance._changes).toEqual(undefined);
    });
  });
  describe('setListItems() method', function () {
    var handler;
    var that;
    beforeEach(function () {
      that = {
        viewModel: new can.Map({
          list: [123]
        })
      };
      handler = events.setListItems.bind(that);
    });
    it('sets concatenated list with current list to viewModel.list',
      function () {
        handler([{
          instance: 321
        }]);
        expect(that.viewModel.list.length).toEqual(2);
        expect(that.viewModel.list[0]).toEqual(123);
        expect(that.viewModel.list[1]).toEqual(321);
      });
  });
  describe('[data-toggle=unmap] click', function () {
    var handler;
    var that;
    var element;
    var result;
    var event;
    beforeEach(function () {
      element = $('body');
      result = $('<div class="result"></div>');
      result.data('result', 'mock');
      element.append(result);
      event = {
        stopPropagation: jasmine.createSpy()
      };
      that = {
        viewModel: new can.Map({
          list: [1, 2],
          deferred: true,
          changes: ['firstChange'],
          parent_instance: new can.Map()
        })
      };
      handler = events['[data-toggle=unmap] click'].bind(that);
    });
    afterEach(function () {
      $('body').html('');
    });
    it('calls stopPropagation of event', function () {
      handler(element, event);
      expect(event.stopPropagation).toHaveBeenCalled();
    });
    it('adds remove-change to viewModel.changes if it is deferred',
      function () {
        handler(element, event);
        expect(that.viewModel.changes[1])
          .toEqual(jasmine.objectContaining({what: 'mock', how: 'remove'}));
      });
    it('adds all changes to parent_instance if it is deferred', function () {
      that.viewModel.parent_instance._changes = [];
      handler(element, event);
      expect(that.viewModel.parent_instance._changes.length).toEqual(2);
    });
  });
  describe('addMapings() method', function () {
    var handler;
    var that;
    var event;
    beforeEach(function () {
      event = {
        stopPropagation: jasmine.createSpy()
      };
      that = {
        viewModel: new can.Map({
          list: [1, 2],
          deferred: true,
          changes: ['firstChange'],
          parent_instance: new can.Map()
        }),
        addListItem: jasmine.createSpy()
      };
      handler = events.addMapings.bind(that);
    });
    it('calls stopPropagation of event', function () {
      handler({}, event, {data: 1});
      expect(event.stopPropagation).toHaveBeenCalled();
    });
    it('adds add-change to viewModel.changes if it is deferred',
      function () {
        handler({}, event, {data: 1});
        expect(that.viewModel.changes[1])
          .toEqual(jasmine.objectContaining({how: 'add'}));
      });
    it('adds all changes to parent_instance if it is deferred', function () {
      that.viewModel.parent_instance._changes = [];
      handler({}, event, {data: [1, 2]});
      expect(that.viewModel.parent_instance._changes.length).toEqual(2);
    });
  });
  describe('autocomplete_select() method', function () {
    var handler;
    var that;
    var element;
    beforeEach(function () {
      element = $('body');
      that = {
        viewModel: new can.Map({
          list: [1, 2],
          deferred: true,
          changes: ['firstChange'],
          parent_instance: new can.Map()
        }),
        element: element,
        addListItem: jasmine.createSpy()
      };
      handler = events.autocomplete_select.bind(that);
    });
    it('adds add-change with extra attributes' +
    ' to viewModel.changes if it is deferred',
      function () {
        handler(element, {}, {item: 'mock'});
        expect(that.viewModel.changes[1])
          .toEqual(jasmine.objectContaining({
            what: 'mock', how: 'add', extra: jasmine.any(can.Map)
          }));
      });
    it('adds all changes to parent_instance if it is deferred', function () {
      that.viewModel.parent_instance._changes = [];
      handler(element, {}, {item: 'mock'});
      expect(that.viewModel.parent_instance._changes.length).toEqual(2);
    });
  });

  describe('buildQuery() method', function () {
    var handler;
    var eventScope;
    var viewModel;

    beforeEach(function () {
      viewModel = new (can.Map.extend(Component.prototype.viewModel));
      eventScope = {
        viewModel: viewModel,
      };
      handler = events.buildQuery.bind(eventScope);
    });

    it('returns array which contains one item', function () {
      eventScope = {
        viewModel: viewModel,
      };
      handler = events.buildQuery.bind(eventScope);
    });

    describe('returns as a first array item a query param which contains',
    function () {
      var type;

      beforeEach(function () {
        type = 'Type';
      });

      it('object_name equals to type', function () {
        var result = _.flow(handler, _.first)(type);
        expect(result.object_name).toBe(type);
      });

      it('filters.expression.op.name equals to "relevant"', function () {
        var result = _.flow(handler, _.first)(type);
        expect(result.filters.expression.op.name).toBe('relevant');
      });

      it('filters.expression.object_name equals to instance.type', function () {
        var result;
        var instanceType = 'instanceType';

        viewModel.attr('instance', {type: instanceType});
        result = _.flow(handler, _.first)(type);

        expect(result.filters.expression.object_name).toBe(instanceType);
      });

      it('filters.expression.ids array contains only id from instance.id ' +
      'converted to string',
      function () {
        var result;
        var instanceId = 12345;

        viewModel.attr('instance', {id: instanceId});
        result = _.flow(handler, _.first)(type);

        expect(result.filters.expression.ids.length).toBe(1);
        expect(result.filters.expression.ids[0]).toBe(String(instanceId));
      });

      it('has default order_by object', function () {
        var expectedOrderByObject = {
          keys: [],
          order: '',
          compare: null,
        };
        var result = _.flow(handler, _.first)(type);
        expect(result.filters.order_by).toEqual(expectedOrderByObject);
      });
    });
  });

  describe('getMappedObjects() method', function () {
    var handler;
    var eventScope;
    var makeRequestDfd;
    var makeRequest;
    var ORDER;

    beforeAll(function () {
      ORDER = {
        FIRST: 0,
        SECOND: 1,
        THIRD: 2,
      };
    });

    beforeEach(function () {
      makeRequestDfd = can.Deferred();
      makeRequest = spyOn(
        GGRC.Utils.QueryAPI, 'makeRequest'
      ).and.returnValue(makeRequestDfd);
      eventScope = {
        viewModel: {},
        buildQuery: jasmine.createSpy('buildQuery'),
      };
      handler = events.getMappedObjects.bind(eventScope);
    });

    describe('makes request which', function () {
      var getParam;

      beforeAll(function () {
        getParam = function (spy, index) {
          return spy.calls.argsFor(0)[index];
        };
      });

      it('contains query to Audit', function () {
        var object = {type: 'Audit'};
        var data;

        eventScope.buildQuery.and.returnValue([object]);
        handler();
        data = getParam(makeRequest, ORDER.FIRST).data;

        expect(eventScope.buildQuery).toHaveBeenCalledWith(object.type);
        expect(data[ORDER.FIRST]).toBe(object);
      });

      it('contains query to Issue', function () {
        var object = {type: 'Issue'};
        var data;

        eventScope.buildQuery.and.returnValue([object]);
        handler();
        data = getParam(makeRequest, ORDER.FIRST).data;

        expect(eventScope.buildQuery).toHaveBeenCalledWith(object.type);
        expect(data[ORDER.SECOND]).toBe(object);
      });

      it('contains query to Snapshot', function () {
        var object = {type: 'Snapshot'};
        var data;

        eventScope.buildQuery.and.returnValue([object]);
        handler();
        data = getParam(makeRequest, ORDER.FIRST).data;

        expect(eventScope.buildQuery).toHaveBeenCalledWith(object.type);
        expect(data[ORDER.SECOND]).toBe(object);
      });
    });

    describe('when request was resolved', function () {
      var response;

      beforeEach(function () {
        response = [
          {Audit: {values: [{data: 1}, {data: 2}]}},
          {Issue: {values: [{data: 2}, {data: 3}]}},
          {Snapshot: {values: [{data: 3}, {data: 4}]}},
        ];
        makeRequestDfd.resolve(response);
        eventScope.buildQuery.and.returnValue([]);
        spyOn(GGRC.Utils.Snapshots, 'toObject').and.returnValue({
          'class': 'class',
          title: 'title',
          description: 'description',
          originalLink: 'originalLink',
        });
      });

      describe('returns a list which', function () {
        it('contains values for Audit type',
        function (done) {
          handler()
            .then(function (list) {
              var objects = response[ORDER.FIRST].Audit.values;

              _.each(objects, function (object) {
                expect(list).toContain(object);
              });

              done();
            });
        });

        it('contains values for Issue type',
        function (done) {
          handler()
            .then(function (list) {
              var objects = response[ORDER.SECOND].Issue.values;

              _.each(objects, function (object) {
                expect(list).toContain(object);
              });

              done();
            });
        });

        it('contains values for Snapshot type converted to Object type',
        function (done) {
          handler()
            .then(function (list) {
              var objects = response[ORDER.THIRD].Snapshot.values;
              _.each(objects, function (snapshot) {
                var convertedObject = GGRC.Utils.Snapshots.toObject(snapshot);

                snapshot.class = convertedObject.class;
                snapshot.snapshot_object_class = 'snapshot-object';
                snapshot.title = convertedObject.title;
                snapshot.description = convertedObject.description;
                snapshot.viewLink = convertedObject.originalLink;
              });

              _.each(objects, function (object) {
                expect(list).toContain(object);
              });

              done();
            });
        });
      });
    });
  });
});
