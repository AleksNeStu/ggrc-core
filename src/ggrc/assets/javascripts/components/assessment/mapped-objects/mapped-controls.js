/*!
 Copyright (C) 2017 Google Inc., authors, and contributors
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, GGRC) {
  'use strict';

  var tpl = can.view(GGRC.mustache_path +
    '/components/assessment/mapped-objects/' +
    'mapped-controls.mustache');
  var tag = 'assessment-mapped-controls';
  /**
   * Assessment specific mapped controls view component
   */
  can.Component.extend({
    tag: tag,
    template: tpl,
    viewModel: {
      mappedSnapshots: true,
      titleText: '@',
      filter: {
        only: ['Control'],
        exclude: []
      },
      mapping: '@',
      mappingType: '@',
      expanded: true,
      selectedItem: {},
      instance: null,
      scopeObject: null
    }
  });
})(window.can, window.GGRC);
