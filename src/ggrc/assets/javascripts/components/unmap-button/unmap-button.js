/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, GGRC, CMS) {
  'use strict';

  var defaultType = 'Relationship';

  GGRC.Components('unmapButton', {
    tag: 'unmap-button',
    viewModel: {
      mappingType: '@',
      objectProp: '@',
      destination: {},
      source: {},
      preventClick: false,
      unmapInstance: function () {
        var self = this;
        this.dispatch({type: 'beforeUnmap', item: this.attr('source')});
        this.getMapping()
          .refresh()
          .done(function (item) {
            item.destroy()
              .then(function () {
                self.dispatch('unmapped');
                self.attr('destination').dispatch('refreshInstance');
                self.dispatch('afterUnmap');
              });
          });
      },
      getMapping: function () {
        var type = this.attr('mappingType') || defaultType;
        var destinations;
        var sources;
        var mapping;
        if (type === defaultType) {
          destinations = this.attr('destination.related_destinations')
          .concat(this.attr('destination.related_sources'));
          sources = this.attr('source.related_destinations')
          .concat(this.attr('source.related_sources'));
        } else {
          destinations = this.attr('destination')
              .attr(this.attr('objectProp')) || [];
          sources = this.attr('source')
              .attr(this.attr('objectProp')) || [];
        }
        sources = sources
          .map(function (item) {
            return item.id;
          });
        mapping = destinations
          .filter(function (dest) {
            return sources.indexOf(dest.id) > -1;
          })[0];
        return new CMS.Models[type](mapping || {});
      }
    },
    events: {
      click: function () {
        if (this.viewModel.attr('preventClick')) {
          return;
        }

        this.viewModel.unmapInstance();
      }
    }
  });
})(window.can, window.GGRC, window.CMS);
