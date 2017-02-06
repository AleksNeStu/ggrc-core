/*!
 Copyright (C) 2017 Google Inc., authors, and contributors
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, GGRC) {
  'use strict';

  var tpl = can.view(GGRC.mustache_path +
    '/components/assessment/mapped-objects/' +
    'mapped-related-information.mustache');
  var tag = 'assessment-mapped-related-information';
  /**
   * Assessment specific mapped related information view component
   */
  can.Component.extend({
    tag: tag,
    template: tpl,
    viewModel: {
      titleText: '@',
      mappedSnapshots: true,
      filter: {
        exclude: ['Control'],
        only: []
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
