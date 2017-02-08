/*!
 Copyright (C) 2017 Google Inc., authors, and contributors
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, GGRC) {
  'use strict';

  var tpl = can.view(GGRC.mustache_path +
    '/components/object-list-item/document-object-list-item.mustache');
  var tag = 'document-object-list-item';
  /**
   * Simple component to show Document-like Objects
   */
  can.Component.extend({
    tag: tag,
    template: tpl,
    viewModel: {
      instance: {},
      define: {
        showIcon: {
          type: Boolean,
          value: false
        },
        iconCls: {
          get: function () {
            return this.attr('showIcon') ?
            'fa-' + this.attr('itemData.title').toLowerCase() :
            '';
          }
        },
        itemData: {
          get: function () {
            return this.attr('instance');
          }
        },
        itemTitle: {
          get: function () {
            return this.attr('itemData.title') || this.attr('itemData.link');
          }
        }
      }
    }
  });
})(window.can, window.GGRC);
