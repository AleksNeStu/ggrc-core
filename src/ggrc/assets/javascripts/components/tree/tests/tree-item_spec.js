/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

describe('GGRC.Components.treeItem', function () {
  'use strict';

  var vm;

  beforeEach(function () {
    vm = GGRC.Components.getViewModel('treeItem');
  });

  describe('selectableSize property', function () {
    it('selectedColumns.length < 4', function () {
      vm.attr('selectedColumns', ['a', 'b', 'c']);

      expect(vm.attr('selectableSize')).toEqual(1);
    });

    it('selectedColumns.length = 5', function () {
      vm.attr('selectedColumns', ['a', 'b', 'c', 'd', 'e']);

      expect(vm.attr('selectableSize')).toEqual(2);
    });

    it('selectedColumns.length > 7', function () {
      vm.attr('selectedColumns', ['a', 'b', 'c', 'd', 'e', 'f', 'g']);

      expect(vm.attr('selectableSize')).toEqual(3);
    });
  });
});
