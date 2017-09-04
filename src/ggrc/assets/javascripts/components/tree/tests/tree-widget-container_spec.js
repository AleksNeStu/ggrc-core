/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

describe('GGRC.Components.treeWidgetContainer', function () {
  'use strict';

  var vm;
  var CurrentPageUtils;

  beforeEach(function () {
    vm = GGRC.Components.getViewModel('treeWidgetContainer');
    CurrentPageUtils = GGRC.Utils.CurrentPage;
  });

  describe('optionsData get() method', function () {
    var shortModelName = 'ModelName';

    beforeEach(function () {
      vm.attr('model', {
        shortName: shortModelName,
      });
    });

    describe('if options.objectVersion has a false value', function () {
      beforeEach(function () {
        vm.removeAttr('options.objectVersion', null);
      });

      it('returns appopriate object', function () {
        var modelName = shortModelName;
        var expectedResult = {
          name: modelName,
          loadItemsModelName: modelName,
          widgetId: modelName,
          countsName: modelName,
        };

        expect(vm.attr('optionsData')).toEqual(expectedResult);
      });
    });

    describe('returns widget config which', function () {
      beforeEach(function () {
        vm.attr('options.objectVersion', {
          data: 'Data',
        });
      });

      it('returns result of GGRC.Utils.ObjectVersions.getWidgetConfig with ' +
      'passed params', function () {
        var expectedResult = {};
        var getWidgetConfig = spyOn(
          GGRC.Utils.ObjectVersions,
          'getWidgetConfig'
        ).and.returnValue(expectedResult);
        var result = vm.attr('optionsData');

        expect(result).toBe(expectedResult);
        expect(getWidgetConfig).toHaveBeenCalledWith(shortModelName, true);
      });
    });
  });

  describe('display() method', function () {
    var display;
    var dfd;

    beforeEach(function () {
      dfd = new $.Deferred();

      display = vm.display.bind(vm);
      spyOn(vm, 'loadItems').and.returnValue(dfd);
      vm.attr('loaded', null);
      vm.attr('refreshLoaded', true);
    });

    it('sets loaded field if it does not exist', function () {
      display();
      expect(vm.attr('loaded')).not.toBeNull();
    });

    it('sets loaded field if needToRefresh param is true', function () {
      vm.attr('loaded', dfd);
      display(true);
      expect(vm.attr('loaded')).not.toBeNull();
    });

    it('sets refreshLoaded flag in false after resolve loaded field',
    function () {
      display(true);
      dfd.resolve();
      expect(vm.attr('refreshLoaded')).toBe(false);
    });

    it('returns value of loaded field', function () {
      var result;
      vm.attr('loaded', dfd);
      result = display();
      expect(result).toBe(dfd);
    });
  });

  describe('addItem get() method', function () {
    describe('if there is options.objectVersion', function () {
      beforeEach(function () {
        vm.attr('options.objectVersion', {data: 1});
      });

      it('returns false', function () {
        expect(vm.attr('addItem')).toBe(false);
      });
    });

    describe('if there is no options.objectVersion', function () {
      beforeEach(function () {
        vm.attr('options.objectVersion', null);
      });

      it('returns options.add_item_view if it exists', function () {
        var expectedData = new can.Map({});
        vm.attr('options.add_item_view', expectedData);
        expect(vm.attr('addItem')).toBe(expectedData);
      });

      it('returns model.tree_view_options.add_item_view by default',
      function () {
        var expectedData = new can.Map({});
        vm.attr('options.add_item_view', null);
        vm.attr('model', {
          tree_view_options: {
            add_item_view: expectedData,
          },
        });
        expect(vm.attr('addItem')).toBe(expectedData);
      });
    });
  });

  describe('isSnapshot get() method', function () {
    var isSnapshotScope;
    var isSnapshotModel;

    beforeEach(function () {
      isSnapshotScope = spyOn(GGRC.Utils.Snapshots, 'isSnapshotScope');
      isSnapshotModel = spyOn(GGRC.Utils.Snapshots, 'isSnapshotModel');
    });

    describe('if parent_instance is a snapshot scope and ' +
    'model.model_singular is a snapshot model', function () {
      beforeEach(function () {
        vm.attr('parent_instance', {data: 'Data'});
        vm.attr('model', {model_singular: 'modelSingular'});

        isSnapshotScope.and.returnValue({data: '1'});
        isSnapshotModel.and.returnValue({data: '2'});
      });

      it('returns true value', function () {
        expect(vm.attr('isSnapshots')).toBeTruthy();
        expect(isSnapshotScope).toHaveBeenCalledWith(
          vm.attr('parent_instance')
        );
        expect(isSnapshotModel).toHaveBeenCalledWith(
          vm.attr('model.model_singular')
        );
      });
    });

    it('returns options.objectVersion by default', function () {
      vm.attr('options.objectVersion', {data: 'Data'});
      expect(vm.attr('isSnapshots')).toBeTruthy();
    });

    describe('if parent_instance is not a snapshot scope or ' +
    'model.model_singular is not a snapshot model', function () {
      beforeEach(function () {
        isSnapshotScope.and.returnValue(null);
        isSnapshotModel.and.returnValue(null);
      });

      it('returns true value if there is options.objectVersion', function () {
        vm.attr('options.objectVersion', {data: 'Data'});
        expect(vm.attr('isSnapshots')).toBeTruthy();
      });

      it('returns false value if there is no options.objectVersion',
      function () {
        vm.attr('options.objectVersion', null);
        expect(vm.attr('isSnapshots')).toBeFalsy();
      });
    });
  });

  describe('onSort() method', function () {
    var onSort;

    beforeEach(function () {
      onSort = vm.onSort.bind(vm);
      vm.attr('pageInfo.count', 3);

      spyOn(vm, 'loadItems');
      spyOn(vm, 'closeInfoPane');
    });

    it('sets current order properties', function () {
      onSort({
        field: 'col1'
      });

      expect(vm.attr('sortingInfo.sortBy')).toEqual('col1');
      expect(vm.attr('sortingInfo.sortDirection')).toEqual('desc');
      expect(vm.attr('pageInfo.current')).toEqual(1);
      expect(vm.loadItems).toHaveBeenCalled();
      expect(vm.closeInfoPane).toHaveBeenCalled();
    });

    it('changes sortDirection for current column', function () {
      vm.attr('sortingInfo', {
        sortBy: 'field',
        sortDirection: 'desc'
      });
      onSort({
        field: 'field'
      });

      expect(vm.attr('sortingInfo.sortBy')).toEqual('field');
      expect(vm.attr('sortingInfo.sortDirection')).toEqual('asc');
      expect(vm.attr('pageInfo.current')).toEqual(1);
      expect(vm.loadItems).toHaveBeenCalled();
      expect(vm.closeInfoPane).toHaveBeenCalled();
    });

    it('changes sortBy property', function () {
      vm.attr('sortingInfo', {
        sortBy: 'field1',
        sortDirection: 'asc'
      });
      onSort({
        field: 'newField'
      });

      expect(vm.attr('sortingInfo.sortBy')).toEqual('newField');
      expect(vm.attr('sortingInfo.sortDirection')).toEqual('desc');
      expect(vm.attr('pageInfo.current')).toEqual(1);
      expect(vm.loadItems).toHaveBeenCalled();
    });
  });

  describe('loadItems() method', function () {
    var loadItems;

    beforeEach(function () {
      vm.attr({
        model: {shortName: 'modelName'},
        options: {
          parent_instance: {}
        }
      });
      loadItems = vm.loadItems.bind(vm);
    });

    it('', function (done) {
      spyOn(GGRC.Utils.TreeView, 'loadFirstTierItems')
        .and.returnValue(can.Deferred().resolve({
          total: 100,
          values: []
        }));

      loadItems().then(function () {
        expect(vm.attr('pageInfo.total')).toEqual(100);
        expect(can.makeArray(vm.attr('showedItems'))).toEqual([]);
        done();
      });
    });
  });

  describe('setRefreshFlag() method', function () {
    var setRefreshFlag;

    beforeEach(function () {
      setRefreshFlag = vm.setRefreshFlag.bind(vm);
      vm.attr('refreshLoaded', null);
    });

    it('sets refreshLoaded state in true if refresh param is true',
    function () {
      setRefreshFlag(true);
      expect(vm.attr('refreshLoaded')).toBe(true);
    });

    it('sets refreshLoaded state in false if refresh param is false',
    function () {
      setRefreshFlag(false);
      expect(vm.attr('refreshLoaded')).toBe(false);
    });
  });

  describe('needToRefresh() method', function () {
    var needToRefresh;
    var setRefreshFlag;

    beforeEach(function () {
      needToRefresh = vm.needToRefresh.bind(vm);
      setRefreshFlag = vm.setRefreshFlag.bind(vm);
      vm.attr('refreshLoaded', null);
    });

    it('returns true if refreshLoaded field is true',
    function () {
      var result;
      setRefreshFlag(true);
      result = needToRefresh();

      expect(result).toBe(true);
    });

    it('returns false if refreshLoaded field is false',
    function () {
      var result;
      setRefreshFlag(false);
      result = needToRefresh();

      expect(result).toBe(false);
    });
  });

  describe('on widget appearing', function () {
    var _widgetShown;

    beforeEach(function () {
      _widgetShown = vm._widgetShown.bind(vm);
      spyOn(vm, '_triggerListeners');
      spyOn(vm, 'loadItems');
    });

    describe('for any viewModel except Issue', function () {
      beforeEach(function () {
        var modelName = 'Model';
        spyOn(CurrentPageUtils, 'getCounts').and.returnValue(
          _.set({}, modelName, 123)
        );
        vm.attr({
          model: {
            shortName: modelName
          },
          modelName: modelName,
          loaded: {},
          pageInfo: {
            total: 123
          }
        });
      });

      it('should only add listeners', function () {
        _widgetShown();
        expect(vm._triggerListeners).toHaveBeenCalled();
        expect(vm.loadItems).not.toHaveBeenCalled();
      });
    });

    describe('for Issue viewModel that wasn\'t loaded before', function () {
      var modelName = 'Issue';

      beforeEach(function () {
        vm.attr({
          model: {
            shortName: modelName
          },
          modelName: modelName
        });
        vm.attr('loaded', null);
        vm.attr('pageInfo', {
          total: 123
        });
        spyOn(CurrentPageUtils, 'getCounts').and.returnValue(
          _.set({}, modelName, 123)
        );
      });

      it('should only add listeners', function () {
        _widgetShown();
        expect(vm._triggerListeners).toHaveBeenCalled();
        expect(vm.loadItems).not.toHaveBeenCalled();
      });
    });

    describe('for Issue viewModel that was loaded before' +
      'in case of equality between counts on tab ' +
      'and total counts in viewModel',
      function () {
        var modelName = 'Issue';

        beforeEach(function () {
          vm.attr({
            model: {
              shortName: modelName
            },
            modelName: modelName
          });
          vm.attr('loaded', {});
          vm.attr('pageInfo', {
            total: 123
          });
          spyOn(CurrentPageUtils, 'getCounts').and.returnValue(
            _.set({}, modelName, 123)
          );
        });

        it('should only add listeners', function () {
          _widgetShown();
          expect(vm._triggerListeners).toHaveBeenCalled();
          expect(vm.loadItems).not.toHaveBeenCalled();
        });
      }
    );

    describe('for Issue viewModel that was loaded before' +
      'in case of inequality between counts on tab ' +
      'and total counts in viewModel',
      function () {
        var modelName = 'Issue';

        beforeEach(function () {
          vm.attr({
            model: {
              shortName: modelName
            },
            modelName: modelName
          });
          vm.attr('loaded', {});
          vm.attr('pageInfo', {
            total: 123
          });
          spyOn(CurrentPageUtils, 'getCounts').and.returnValue(
            _.set({}, modelName, 124)
          );
        });

        it('should add listeners and update viewModel', function () {
          _widgetShown();
          expect(vm._triggerListeners).toHaveBeenCalled();
          expect(vm.loadItems).toHaveBeenCalled();
        });
      }
    );
  });

  describe('openAdvancedFilter() method', function () {
    it('copies applied filter and mapping items', function () {
      var appliedFilterItems = new can.List([
        GGRC.Utils.AdvancedSearch.create.attribute()
      ]);
      var appliedMappingItems = new can.List([
        GGRC.Utils.AdvancedSearch.create.mappingCriteria({
          filter: GGRC.Utils.AdvancedSearch.create.attribute()
        })
      ]);
      vm.attr('advancedSearch.appliedFilterItems', appliedFilterItems);
      vm.attr('advancedSearch.appliedMappingItems', appliedMappingItems);
      vm.attr('advancedSearch.filterItems', can.List());
      vm.attr('advancedSearch.mappingItems', can.List());

      vm.openAdvancedFilter();

      expect(vm.attr('advancedSearch.filterItems').attr())
        .toEqual(appliedFilterItems.attr());
      expect(vm.attr('advancedSearch.mappingItems').attr())
        .toEqual(appliedMappingItems.attr());
    });

    it('opens modal window', function () {
      vm.attr('advancedSearch.open', false);

      vm.openAdvancedFilter();

      expect(vm.attr('advancedSearch.open')).toBe(true);
    });
  });

  describe('applyAdvancedFilters() method', function () {
    var filterItems = new can.List([
      GGRC.Utils.AdvancedSearch.create.attribute()
    ]);
    var mappingItems = new can.List([
      GGRC.Utils.AdvancedSearch.create.mappingCriteria({
        filter: GGRC.Utils.AdvancedSearch.create.attribute()
      })
    ]);
    beforeEach(function () {
      vm.attr('advancedSearch.filterItems', filterItems);
      vm.attr('advancedSearch.mappingItems', mappingItems);
      vm.attr('advancedSearch.appliedFilterItems', can.List());
      vm.attr('advancedSearch.appliedMappingItems', can.List());
      spyOn(vm, 'onFilter');
      spyOn(GGRC.Utils.AdvancedSearch, 'buildFilter')
        .and.callFake(function (items, request) {
          request.push({name: 'item'});
        });
    });

    it('copies filter and mapping items to applied', function () {
      vm.applyAdvancedFilters();

      expect(vm.attr('advancedSearch.appliedFilterItems').attr())
        .toEqual(filterItems.attr());
      expect(vm.attr('advancedSearch.appliedMappingItems').attr())
        .toEqual(mappingItems.attr());
    });

    it('initializes advancedSearch.filter property', function () {
      spyOn(GGRC.query_parser, 'join_queries').and.returnValue({
        name: 'test'
      });
      vm.attr('advancedSearch.filter', null);

      vm.applyAdvancedFilters();

      expect(vm.attr('advancedSearch.filter.name')).toBe('test');
    });

    it('initializes advancedSearch.request property', function () {
      vm.attr('advancedSearch.request', can.List());
      spyOn(GGRC.query_parser, 'join_queries');

      vm.applyAdvancedFilters();

      expect(vm.attr('advancedSearch.request.length')).toBe(2);
    });

    it('closes modal window', function () {
      vm.attr('advancedSearch.open', true);

      vm.applyAdvancedFilters();

      expect(vm.attr('advancedSearch.open')).toBe(false);
    });

    it('calls onFilter() method', function () {
      vm.applyAdvancedFilters();

      expect(vm.onFilter).toHaveBeenCalled();
    });
  });

  describe('removeAdvancedFilters() method', function () {
    beforeEach(function () {
      spyOn(vm, 'onFilter');
    });

    it('removes applied filter and mapping items', function () {
      vm.attr('advancedSearch.appliedFilterItems', new can.List([
        {title: 'item'}
      ]));
      vm.attr('advancedSearch.appliedMappingItems', new can.List([
        {title: 'item'}
      ]));

      vm.removeAdvancedFilters();

      expect(vm.attr('advancedSearch.appliedFilterItems.length')).toBe(0);
      expect(vm.attr('advancedSearch.appliedMappingItems.length')).toBe(0);
    });

    it('cleans advancedSearch.filter property', function () {
      vm.attr('advancedSearch.filter', {});

      vm.removeAdvancedFilters();

      expect(vm.attr('advancedSearch.filter')).toBe(null);
    });

    it('closes modal window', function () {
      vm.attr('advancedSearch.open', true);

      vm.removeAdvancedFilters();

      expect(vm.attr('advancedSearch.open')).toBe(false);
    });

    it('calls onFilter() method', function () {
      vm.removeAdvancedFilters();

      expect(vm.onFilter).toHaveBeenCalled();
    });

    it('resets advancedSearch.request list', function () {
      vm.attr('advancedSearch.request', new can.List([{data: 'test'}]));

      vm.removeAdvancedFilters();

      expect(vm.attr('advancedSearch.request.length')).toBe(0);
    });
  });

  describe('resetAdvancedFilters() method', function () {
    it('resets filter items', function () {
      vm.attr('advancedSearch.filterItems', new can.List([
        {title: 'item'}
      ]));

      vm.resetAdvancedFilters();

      expect(vm.attr('advancedSearch.filterItems.length')).toBe(0);
    });

    it('resets mapping items', function () {
      vm.attr('advancedSearch.mappingItems', new can.List([
        {title: 'item'}
      ]));

      vm.resetAdvancedFilters();

      expect(vm.attr('advancedSearch.mappingItems.length')).toBe(0);
    });
  });

  describe('getAbsoluteItemNumber() method', function () {
    beforeEach(function () {
      vm.attr({
        pageInfo: {
          pageSize: 10,
          count: 5
        },
        showedItems: [{id: 1, type: 'object'},
          {id: 2, type: 'object'},
          {id: 3, type: 'object'}]
      });
      vm.attr('pageInfo.current', 3);
    });

    it('should return correct item number when item is on page',
      function () {
        var result;

        result = vm.getAbsoluteItemNumber({id: 2, type: 'object'});

        expect(result).toEqual(21);
      });

    it('should return "-1" when item is not on page',
       function () {
         var result;

         result = vm.getAbsoluteItemNumber({id: 4, type: 'object'});

         expect(result).toEqual(-1);
       });
    it('should return "-1" when item is of different type',
      function () {
        var result;

        result = vm.getAbsoluteItemNumber({id: 3, type: 'snapshot'});

        expect(result).toEqual(-1);
      });
    it('should return correct item number for first item on non first page',
       function () {
         var result;

         result = vm.getAbsoluteItemNumber({id: 1, type: 'object'});

         expect(result).toEqual(20);
       });
  });

  describe('getRelativeItemNumber() method', function () {
    it('should return correct item number on page', function () {
      var result = vm.getRelativeItemNumber(12, 5);

      expect(result).toEqual(2);
    });
  });

  describe('getNextItemPage() method', function () {
    beforeEach(function () {
      spyOn(vm, 'loadItems');
    });

    it('should load items for appropriate page when item is not loaded',
      function () {
        vm.getNextItemPage(10, {current: 2, pageSize: 5});

        expect(vm.attr('loading')).toBeTruthy();
        expect(vm.loadItems).toHaveBeenCalled();
      });

    it('shouldn\'t load items when current item was already loaded',
      function () {
        vm.getNextItemPage(10, {current: 3, pageSize: 5});

        expect(vm.attr('loading')).toBeFalsy();
        expect(vm.loadItems).not.toHaveBeenCalled();
      });
  });
});
