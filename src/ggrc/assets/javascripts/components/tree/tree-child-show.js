/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, $) {
  GGRC.Components('treeChildShow', {
    tag: 'tree-child-show',
    template: '<content/>',
    viewModel: {
      onChildShowStateChange: null,
      isChildShow: null
    },
    events: {
      init: function (element, options) {
      },
      'a click': function () {
        var isChildShow = this.viewModel.attr('isChildShow');
        var onChildShowStateChange = this.viewModel.onChildShowStateChange;

        this.viewModel.attr('isChildShow', !isChildShow);
        onChildShowStateChange(!isChildShow);
      }
    }
  });
})(window.can, window.can.$);
