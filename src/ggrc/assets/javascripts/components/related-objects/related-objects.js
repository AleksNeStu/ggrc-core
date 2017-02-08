/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, GGRC, CMS) {
  'use strict';

  var defaultOrderBy = 'created_at';

  can.Component.extend({
    tag: 'related-objects',
    viewModel: {
      isLoading: false,
      baseInstance: null,
      relatedObjects: [],
      relatedItemsType: '@',
      orderBy: '@',
      paging: {
        current: 1,
        pageSize: 5,
        pageSizeSelect: [5, 10, 15]
      },
      getParams: function () {
        var id = this.attr('baseInstance.id');
        var type = this.attr('baseInstance.type');
        var relatedType = this.attr('relatedItemsType');
        var page = this.attr('paging');
        var orderBy = this.attr('orderBy') || defaultOrderBy;
        var params = {};
        var first;
        var last;

        if (page.current && page.pageSize) {
          first = (page.current - 1) * page.pageSize;
          last = page.current * page.pageSize;
        }
        params.data = [{
          limit: [first, last],
          object_name: relatedType,
          order_by: [{name: orderBy, desc: true}],
          filters: {
            expression: {
              object_name: type,
              op: {name: 'similar'},
              ids: [id]
            }
          }
        }];
        return params;
      },
      updatePaging: function (total) {
        var count = Math.ceil(total / this.attr('paging.pageSize'));
        this.attr('paging.total', total);
        this.attr('paging.count', count);
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
              item.instance = new CMS.Models[relatedType](item);
              return item;
            });
            // Update paging object
            this.updatePaging(data[relatedType].total);
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
      setRelatedItems: function () {
        this.attr('relatedObjects').replace(this.loadRelatedItems());
      }
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
      '{viewModel.baseInstance} related_destinations': function () {
        if (!this.viewModel.attr('isLoading')) {
          this.viewModel.setRelatedItems();
        }
      },
      '{viewModel.baseInstance} related_sources': function () {
        if (!this.viewModel.attr('isLoading')) {
          this.viewModel.setRelatedItems();
        }
      }
    }
  });
})(window.can, window.GGRC, window.CMS);
