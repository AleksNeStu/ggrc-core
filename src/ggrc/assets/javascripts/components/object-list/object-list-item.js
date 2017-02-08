/*!
 Copyright (C) 2017 Google Inc., authors, and contributors
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can) {
  'use strict';

  var tag = 'object-list-item';
  /**
   * Object List Item component
   */
  can.Component.extend({
    tag: tag,
    viewModel: {
      instance: {},
      isSelected: false
    },
    events: {
      '{this.element} click': function (el) {
        can.trigger(el, 'selectItem', [this.viewModel.instance]);
      }
    }
  });
})(window.can, window.GGRC);
