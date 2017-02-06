/*!
    Copyright (C) 2017 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

(function (can) {
  'use strict';

  GGRC.Components('viewObjectButtons', {
    tag: 'view-object-buttons',
    template: can.view(
      GGRC.mustache_path +
      '/components/view-object-buttons/view-object-buttons.mustache'
    ),
    scope: {
      instance: null,
      openIsHidden: false,
      maximizeObject: function (scope, el, ev) {
        var tree = el.closest('.cms_controllers_tree_view_node');
        var node = tree.control();
        ev.preventDefault();
        ev.stopPropagation();
        if (node) {
          node.select(true);
        }
      },
      openObject: function (scope, el, ev) {
        ev.stopPropagation();
      }
    }
  });
})(window.can);
