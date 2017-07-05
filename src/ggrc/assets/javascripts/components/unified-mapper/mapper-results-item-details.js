/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, GGRC, CMS) {
  'use strict';

  GGRC.Components('mapperResultsItemDetails', {
    tag: 'mapper-results-item-details',
    template: can.view(
      GGRC.mustache_path +
      '/components/unified-mapper/mapper-results-item-details.mustache'
    ),
    viewModel: {
      init: function () {
        var instance = this.attr('instance');
        if (instance.snapshotObject) {
          this.attr('instance', instance.snapshotObject);
        } else {
          this.attr('model', CMS.Models[instance.type]);
        }
      },
      item: null,
      instance: null,
      model: null,
      isMapperDetails: true,
      adminRole: ['Admin'],
      deletableAdmin: false
    }
  });
})(window.can, window.GGRC, window.CMS);
