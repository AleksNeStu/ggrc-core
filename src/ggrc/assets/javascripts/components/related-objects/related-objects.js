/*
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

import '../sortable-column/sortable-column';
import {REFRESH_RELATED} from '../../events/eventTypes';

(function (can, GGRC, CMS) {
  'use strict';

  var defaultOrderBy = 'created_at';

  GGRC.Components('relatedObjects', {
    tag: 'related-objects',
    viewModel: {
      define: {
        noRelatedObjectsMessage: {
          type: 'string',
          get: function () {
            return 'No Related ' + this.attr('relatedItemsType') + 's ' +
              'were found';
          },
        },
        isLoading: {
          type: 'boolean',
          value: false,
        },
        paging: {
          value: function () {
            return new GGRC.VM.Pagination({pageSizeSelect: [5, 10, 15]});
          },
        },
        relatedObjects: {
          Value: can.List,
        },
        predefinedFilter: {
          type: '*',
        },
      },
      baseInstance: null,
      relatedItemsType: '@',
      orderBy: {},
      initialOrderBy: '@',
      selectedItem: {},
      objectSelectorEl: '.grid-data__action-column button',
      getFilters: function (id, type) {
        var predefinedFilter = this.attr('predefinedFilter');
        var filters;

        var hasSimilar = _.includes(['Assessment', 'Control', 'Objective'],
          this.attr('baseInstance.type'));

        if (predefinedFilter) {
          filters = predefinedFilter;
        } else {
          filters = {
            expression: {
              object_name: type,
              op: hasSimilar ? {name: 'similar'} : {name: 'relevant'},
              ids: [id],
            },
          };
        }
        return filters;
      },
      getParams: function () {
        var id;
        var type;
        var relatedType = this.attr('relatedItemsType');
        var isSnapshot = !!this.attr('baseInstance.snapshot');
        var filters;
        var params = {};

        if (isSnapshot) {
          id = this.attr('baseInstance.snapshot.child_id');
          type = this.attr('baseInstance.snapshot.child_type');
        } else {
          id = this.attr('baseInstance.id');
          type = this.attr('baseInstance.type');
        }
        filters = this.getFilters(id, type);
        params.data = [{
          limit: this.attr('paging.limits'),
          object_name: relatedType,
          order_by: this.getSortingInfo(),
          filters: filters,
        }];
        return params;
      },
      loadRelatedItems: function () {
        var dfd = can.Deferred();
        var params = this.getParams();
        this.attr('isLoading', true);
        GGRC.Utils.QueryAPI
          .makeRequest(params)
          .done(function (responseArr) {
            var relatedType = this.attr('relatedItemsType');
            var data = responseArr[0];
            var values = data[relatedType].values;
            var result = values.map(function (item) {
              return {
                instance: CMS.Models[relatedType].model(item),
              };
            });
            // Update paging object
            this.attr('paging.total', data[relatedType].total);
            dfd.resolve(result);
          }.bind(this))
          .fail(function () {
            dfd.resolve([]);
          })
          .always(function () {
            this.attr('isLoading', false);
          }.bind(this));
        return dfd;
      },
      getSortingInfo: function () {
        var orderBy = this.attr('orderBy');
        var defaultOrder;

        if (!orderBy.attr('field')) {
          defaultOrder = this.attr('initialOrderBy') || defaultOrderBy;
          return defaultOrder.split(',').map(function (field) {
            return {name: field, desc: true};
          });
        }

        return [{
          name: orderBy.attr('field'),
          desc: orderBy.attr('direction') === 'desc'}];
      },
      setRelatedItems: function () {
        this.attr('relatedObjects').replace(this.loadRelatedItems());
      },
    },
    init: function () {
      this.viewModel.setRelatedItems();
    },
    events: {
      '{viewModel.paging} current': function () {
        this.viewModel.setRelatedItems();
      },
      '{viewModel.paging} pageSize': function () {
        this.viewModel.setRelatedItems();
      },
      '{viewModel.baseInstance} refreshInstance': function () {
        this.viewModel.setRelatedItems();
      },
      [`{viewModel.baseInstance} ${REFRESH_RELATED.type}`]:
        function (scope, event) {
        let vm = this.viewModel;

        if (vm.attr('relatedItemsType') === event.model) {
          vm.setRelatedItems();
        }
      },
      '{viewModel.orderBy} changed': function () {
        this.viewModel.setRelatedItems();
      },
    },
  });
})(window.can, window.GGRC, window.CMS);
