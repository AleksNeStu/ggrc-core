/*!
 Copyright (C) 2017 Google Inc., authors, and contributors
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, GGRC) {
  'use strict';

  var tpl = can.view(GGRC.mustache_path +
    '/components/object-list-item/detailed-business-object-list-item.mustache');
  var tag = 'detailed-business-object-list-item';
  /**
   * Assessment specific mapped objects popover view component
   */
  GGRC.Components('detailedBusinessObjectListItem', {
    tag: tag,
    template: tpl,
    viewModel: {
      instance: {},
      customAttributes: null,
      adminRole: ['Admin'],
      deletableAdmin: false,
      define: {
        isSnapshot: {
          get: function () {
            return this.attr('instance.type') === 'Snapshot';
          }
        },
        itemData: {
          get: function () {
            return this.attr('isSnapshot') ?
              this.attr('instance.revision.content') :
              this.attr('instance');
          }
        },
        objectLink: {
          get: function () {
            return this.attr('isSnapshot') ?
              GGRC.Utils.Snapshots.getParentUrl(this.attr('instance')) :
              this.attr('itemData.viewLink');
          }
        },
        objectTitle: {
          get: function () {
            return this.attr('itemData.title') ||
              this.attr('itemData.description_inline') ||
              this.attr('itemData.name') ||
              this.attr('itemData.email') || false;
          }
        }
      }
    }
  });
})(window.can, window.GGRC);
