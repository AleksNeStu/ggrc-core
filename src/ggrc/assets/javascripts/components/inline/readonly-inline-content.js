/*!
    Copyright (C) 2017 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

(function (can, GGRC) {
  'use strict';

  GGRC.Components('readonlyInlineContent', {
    tag: 'readonly-inline-content',
    template: can.view(
      GGRC.mustache_path + '/components/inline/readonly-inline-content.mustache'
    ),
    viewModel: {
      withReadMore: false,
      value: '@',
      withDetails: false
    }
  });
})(window.can, window.GGRC);
