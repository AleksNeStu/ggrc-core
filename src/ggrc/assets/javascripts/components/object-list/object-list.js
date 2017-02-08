/*!
 Copyright (C) 2017 Google Inc., authors, and contributors
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, GGRC) {
  'use strict';

  var tag = 'object-list';
  var tpl = can.view(GGRC.mustache_path +
    '/components/object-list/object-list.mustache');
  /**
   * Object List component
   */
  can.Component.extend({
    tag: tag,
    template: tpl,
    viewModel: {
      spinnerCss: '@',
      isLoading: false,
      selectedItem: {},
      items: [],
      selectItem: function (el, selectedItem) {
        var type = selectedItem.type;
        var id = selectedItem.id;
        this.attr('items').forEach(function (item) {
          var isSelected =
            item.attr('instance.type') === type &&
            item.attr('instance.id') === id;

          if (isSelected) {
            this.attr('selectedItem.data', item.instance);
            this.attr('selectedItem.el', el);
          }
          item.attr('isSelected', isSelected);
        }.bind(this));
      },
      clearSelection: function () {
        this.attr('items').forEach(function (item) {
          item.attr('isSelected', false);
        });
        this.attr('selectedItem.el', null);
        this.attr('selectedItem.data', null);
      },
      onClickHandler: function (el, ev) {
        var isInnerClick = GGRC.Utils.events.isInnerClick(el, ev.target);
        if (!isInnerClick) {
          this.clearSelection();
        }
        ev.stopPropagation();
      }
    },
    events: {
      'object-list-item selectItem': function (el, ev, instance) {
        this.viewModel.selectItem(el, instance);
      },
      '{window} click': function (el, ev) {
        this.viewModel.onClickHandler(this.element, ev);
      }
    }
  });
})(window.can, window.GGRC);
