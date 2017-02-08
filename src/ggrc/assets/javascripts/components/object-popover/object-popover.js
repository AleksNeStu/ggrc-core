/*!
 Copyright (C) 2017 Google Inc., authors, and contributors
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, GGRC) {
  'use strict';

  var tpl = can.view(GGRC.mustache_path +
    '/components/object-popover/object-popover.mustache');
  var tag = 'object-popover';
  var defaultMaxInnerHeight = 400;
  /**
   * Assessment specific mapped objects popover view component
   */
  GGRC.Components('objectPopover', {
    tag: tag,
    template: tpl,
    viewModel: {
      expanded: false,
      maxInnerHeight: defaultMaxInnerHeight,
      openStyle: '',
      item: null,
      itemData: function () {
        var isSnapshot = this.attr('item.data.type') === 'Snapshot';
        return isSnapshot ? this.attr('item.data.revision.content') : this.attr('item.data');
      },
      isActive: function () {
        return this.attr('active');
      },
      setPopoverStyle: function (el) {
        var pos = el[0].getBoundingClientRect();
        var top = Math.floor(el.position().top);
        var left = Math.floor(pos.width / 2);
        var width = Math
          .floor(window.innerWidth - (pos.right - pos.width / 2));
        var topStyle = 'top: ' + top + 'px;';
        var leftStyle = 'left: ' + left + 'px;';
        var widthStyle = 'width: ' + width + 'px;';
        return topStyle + leftStyle + widthStyle;
      },
      setStyle: function (el) {
        var style = el ? this.setPopoverStyle(el) : '';
        this.attr('active', style.length);
        this.attr('openStyle', style);
      }
    },
    events: {
      '{viewModel.item} el': function (scope, ev, el) {
        this.viewModel.setStyle(el);
      },
      '.object-popover-wrapper click': function (el, event) {
        event.stopPropagation();
      },
      '{viewModel} expanded': function (scope, ev, isExpanded) {
        // Double max height property in case additional content is expanded and visible
        var maxInnerHeight = isExpanded ?
          defaultMaxInnerHeight * 2 :
          defaultMaxInnerHeight;
        this.viewModel.attr('maxInnerHeight', maxInnerHeight);
      }
    }
  });
})(window.can, window.GGRC);
