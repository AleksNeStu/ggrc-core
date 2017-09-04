/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

describe('GGRC.VM.BaseTreeItemVM', function () {
  'use strict';

  var vm;

  beforeEach(function () {
    vm = new GGRC.VM.BaseTreeItemVM();
  });

  describe('initChildTreeDisplay() method', function () {
    beforeEach(function () {
      spyOn(GGRC.Utils.TreeView, 'getModelsForSubTier')
        .and.returnValue(['Foo', 'Bar', 'Baz']);
      spyOn(GGRC.Utils.ObjectVersions, 'getWidgetConfig')
        .and.callFake(function (model) {
          return {
            widgetName: model + 'Widget',
          };
        });

      vm.attr('instance', {type: 'Type'});
    });

    it('initialised child models list', function () {
      var modelsList;
      var displayList;
      vm.initChildTreeDisplay();

      modelsList = vm.attr('selectedChildModels').serialize();
      displayList = vm.attr('childModelsList').serialize();

      expect(modelsList.length).toEqual(3);
      expect(modelsList).toEqual(['Foo', 'Bar', 'Baz']);

      expect(displayList).toEqual([
        {
          name: 'Foo',
          widgetName: 'FooWidget',
          display: true,
        }, {
          name: 'Bar',
          widgetName: 'BarWidget',
          display: true,
        }, {
          name: 'Baz',
          widgetName: 'BazWidget',
          display: true,
        },
      ]);
    });
  });

  describe('onExpand() method', function () {
    it('converts expanded property to the opposite value', function () {
      vm.attr('expanded', true);

      vm.onExpand();

      expect(vm.attr('expanded')).toBeFalsy();
    });

    it('converts expanded property to the opposite value', function () {
      vm.attr('expanded', false);

      vm.onExpand();

      expect(vm.attr('expanded')).toBeTruthy();
    });
  });

  describe('onPreview() method', function () {
    beforeEach(function () {
      spyOn(vm, 'select');
    });

    it('calls the select method woth the element from event', function () {
      var event = {
        element: 'fakeElement'
      };
      vm.onPreview(event);

      expect(vm.select).toHaveBeenCalledWith('fakeElement');
    })
  });

  describe('select() method', function () {
    var fakeElement;

    beforeEach(function () {
      fakeElement = {
        closest: jasmine.createSpy()
      };

      spyOn(can, 'trigger');
    });

    describe('for not Person instances', function () {
      beforeEach(function () {
        vm.attr('instance', 'fakeInstance');
        vm.attr('itemSelector', 'fakeSelector');
      });

      it('triggers event immediately', function () {
        vm.select(fakeElement);

        expect(can.trigger).toHaveBeenCalled();
      });
    });

    describe('for Person instances', function () {
      //
    })
  });
});
