/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can) {
  'use strict';

  /**
   * Simple wrapper component to load Related to Parent Object Snapshots of Controls and Objectives
   */
  can.Component.extend({
    tag: 'related-controls-objectives',
    viewModel: {
      define: {
        parentInstance: {
          value: {}
        },
        relatedObjectType: {
          value: null,
        },
        mappedSnapshots: {
          type: 'boolean',
          value: true
        },
        // Load only Controls and Objectives
        filter: {
          get: function () {
            return {
              only: [this.attr('relatedObjectType')],
              exclude: [],
            };
          },
        }
      }
    }
  });
})(window.can);
