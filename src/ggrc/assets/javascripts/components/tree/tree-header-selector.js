/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, $) {
  can.Component.extend({
    tag: 'tree-header-selector',
    // <content> in a component template will be replaced with whatever is contained
    //  within the component tag.  Since the views for the original uses of these components
    //  were already created with content, we just used <content> instead of making
    //  new view template files.
    template: '<content/>',
    scope: {},
    events: {
      init: function (element, options) {
        this.scope.attr('controller', this);
        this.scope.attr('$rootEl', $(element));
      },

      disable_attrs: function (el, ev) {
        var MAX_ATTR = 7;
        var $check = this.element.find('.attr-checkbox');
        var $mandatory = $check.filter('.mandatory');
        var $selected = $check.filter(':checked');
        var $not_selected = $check.not(':checked');

        if ($selected.length === MAX_ATTR) {
          $not_selected.prop('disabled', true)
            .closest('li').addClass('disabled');
        } else {
          $check.prop('disabled', false)
            .closest('li').removeClass('disabled');
          // Make sure mandatory items are always disabled
          $mandatory.prop('disabled', true)
            .closest('li').addClass('disabled');
        }
      },

      'input.attr-checkbox click': function (el, ev) {
        this.disable_attrs(el, ev);
        ev.stopPropagation();
      },

      '.dropdown-menu-form click': function (el, ev) {
        ev.stopPropagation();
      },

      '.tview-dropdown-toggle click': function (el, ev) {
        this.disable_attrs(el, ev);
      },

      '.set-tree-attrs,.close-dropdown click': function (el, ev) {
        this.scope.$rootEl.removeClass('open');
        this.scope.$rootEl.parents('.dropdown-menu')
          .parent().removeClass('open');
      }
    }
  });
})(window.can, window.can.$);
