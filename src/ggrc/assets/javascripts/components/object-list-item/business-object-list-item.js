/*!
 Copyright (C) 2017 Google Inc., authors, and contributors
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, GGRC) {
  'use strict';

  var tpl = can.view(GGRC.mustache_path +
    '/components/object-list-item/business-object-list-item.mustache');
  var tag = 'business-object-list-item';
  /**
   * Mapped objects item view component
   */
  can.Component.extend({
    tag: tag,
    template: tpl,
    viewModel: {
      instance: {},
      define: {
        type: {
          type: String
        },
        isSnapshot: {
          get: function () {
            return this.attr('instance.type') === 'Snapshot';
          }
        },
        iconCls: {
          get: function () {
            return !this.attr('isSnapshot') ?
            'fa-' + this.attr('instance.type').toLowerCase() :
            'fa-' + this.attr('instance.child_type').toLowerCase();
          }
        },
        itemData: {
          get: function () {
            return !this.attr('isSnapshot') ?
              this.attr('instance') :
              this.attr('instance.revision.content');
          }
        },
        itemTitle: {
          get: function () {
            return this.attr('itemData.title') ||
              this.attr('itemData.description_inline') ||
              this.attr('itemData.name') ||
              this.attr('itemData.email') ||
              '<span class="empty-message">None</span>';
          }
        }
      }
    }
  });
})(window.can, window.GGRC);
