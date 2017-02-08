/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, GGRC) {
  'use strict';

  GGRC.Components('mapperResultsItemDetails', {
    tag: 'mapper-results-item-details',
    template: can.view(
      GGRC.mustache_path +
      '/components/unified-mapper/mapper-results-item-details.mustache'
    ),
    viewModel: {
      item: {}
    }
  });
})(window.can, window.GGRC);
