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
        mappedSnapshots: {
          type: Boolean,
          value: true
        },
        // Load only Controls and Objectives
        filter: {
          value: function () {
            return {
              only: ['Control', 'Objective'],
              exclude: []
            };
          }
        }
      }
    }
  });
})(window.can);
