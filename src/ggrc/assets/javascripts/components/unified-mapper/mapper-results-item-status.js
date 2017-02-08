/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, GGRC) {
  'use strict';

  GGRC.Components('mapperResultsItemStatus', {
    tag: 'mapper-results-item-status',
    template: can.view(
      GGRC.mustache_path +
      '/components/unified-mapper/mapper-results-item-status.mustache'
    ),
    viewModel: {
      itemData: {}
    }
  });
})(window.can, window.GGRC);
