/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, GGRC) {
  'use strict';

  var tpl = can.view(GGRC.mustache_path +
    '/components/simple-modal/simple-modal.mustache');
  /**
   * Simple Modal Component is a general abstraction to visualize
   * modal and pop-ups with overlay.
   * Simple Modal can be initialized in any part of the HTML.
   * Simple Modal provides only logic less basic markup. All business logic should be placed on the level of inner components.
   * To simplify styling additional helper CSS classes were created: 'simple-modal__footer', 'simple-modal__body' and 'simple-modal__header'
   */
  can.Component.extend({
    tag: 'simple-modal',
    template: tpl,
    viewModel: {
      extraCssClass: '@',
      instance: null,
      modalTitle: '',
      state: {
        open: false
      },
      hide: function () {
        this.attr('state.open', false);
      },
      show: function () {
        this.attr('state.open', true);
      }
    }
  });
})(window.can, window.GGRC);
