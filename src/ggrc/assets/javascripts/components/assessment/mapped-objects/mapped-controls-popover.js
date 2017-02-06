/*!
 Copyright (C) 2017 Google Inc., authors, and contributors
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, GGRC) {
  'use strict';

  var tpl = can.view(GGRC.mustache_path +
    '/components/assessment/mapped-objects/mapped-controls-popover.mustache');
  var tag = 'assessment-mapped-controls-popover';
  /**
   * Assessment specific mapped controls popover view component
   */
  var defaultResponseArr = [{
    Snapshot: {
      values: []
    }
  }, {
    Snapshot: {
      values: []
    }
  }];

  can.Component.extend({
    tag: tag,
    template: tpl,
    viewModel: {
      item: null,
      expanded: false,
      objectives: [],
      regulations: [],
      queries: [
        {type: 'objectives'},
        {type: 'regulations'}
      ],
      isLoading: false,
      getParams: function (id) {
        var params = {};
        var relevant = {
          id: id,
          type: 'Snapshot'
        };
        var fields = ['revision'];
        params.data = [
          GGRC.Utils.Snapshots.transformQuery(
            GGRC.Utils.QueryAPI.buildParam('Objective', {}, relevant, fields)
          ),
          GGRC.Utils.Snapshots.transformQuery(
            GGRC.Utils.QueryAPI.buildParam('Regulation', {}, relevant, fields)
          )
        ];
        return params;
      },
      setItems: function (responseArr) {
        responseArr.forEach(function (item, i) {
          var type = this.attr('queries').attr(i).type;
          this.attr(type).replace(item.Snapshot.values
            .map(function (item) {
              return item.revision.content;
            }));
        }.bind(this));
      },
      loadItems: function () {
        var id = this.attr('item.data.id');
        var params;

        if (!id) {
          this.setItems(defaultResponseArr);
          return;
        }
        params = this.getParams(id);

        this.attr('isLoading', true);

        GGRC.Utils.QueryAPI
          .makeRequest(params)
          .done(this.setItems.bind(this))
          .fail(function () {
            console.warn('Errors are: ', arguments);
            this.setItems(defaultResponseArr);
          }.bind(this))
          .always(function () {
            this.attr('isLoading', false);
          }.bind(this));
      }
    },
    events: {
      '{viewModel} expanded': function (scope, ev, isExpanded) {
        if (isExpanded) {
          this.viewModel.loadItems();
        }
      }
    }
  });
})(window.can, window.GGRC);
