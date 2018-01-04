/*
 Copyright (C) 2017 Google Inc., authors, and contributors
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

import '../object-list-item/comment-list-item';
import '../object-list/object-list';
import template from './mapped-comments.mustache';

(function (can, GGRC) {
  'use strict';

  var tag = 'mapped-comments';
  /**
   * Assessment specific mapped controls view component
   */
  can.Component.extend({
    tag: tag,
    template: template,
    viewModel: {
      define: {
        noItemsText: {
          type: 'string',
          value: '',
        },
      },
      mappedItems: [],
      baseInstance: {},
    },
  });
})(window.can, window.GGRC);
