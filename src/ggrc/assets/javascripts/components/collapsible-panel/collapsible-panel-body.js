/*!
 Copyright (C) 2016 Google Inc., authors, and contributors
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, GGRC) {
  'use strict';

  var tag = 'collapsible-panel-body';
  var tpl = can.view(GGRC.mustache_path +
    '/components/collapsible-panel/collapsible-panel-body.mustache');
  /**
   * Collapsible Panel component to add collapsing behavior
   */
  GGRC.Components('collapsiblePanelBody', {
    tag: tag,
    template: tpl,
    scope: {
      content: '<content></content>',
      expanded: null,
      isVisible: false
    },
    events: {
      '{scope} expanded': function (scope, ev, val) {
        console.info('Was triggered!!!');
        this.scope.attr('isVisible', val);
      }
    }
  });
})(window.can, window.GGRC);
