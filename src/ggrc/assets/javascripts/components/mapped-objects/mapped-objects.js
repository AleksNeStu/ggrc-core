/*!
 Copyright (C) 2017 Google Inc., authors, and contributors
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, GGRC) {
  'use strict';

  var tpl = can.view(GGRC.mustache_path +
    '/components/mapped-objects/mapped-objects.mustache');
  var tag = 'mapped-objects';
  /**
   * Mapped objects view component
   */
  can.Component.extend({
    tag: tag,
    template: tpl,
    viewModel: {
      define: {
        relatedTypes: {
          type: '*',
          value: function () {
            return [];
          }
        },
        mappedSnapshots: {
          type: Boolean,
          value: false
        },
        requireLimit: {
          get: function () {
            return this.attr('mappedItems.length') > this.attr('visibleItems');
          }
        },
        showItems: {
          type: can.List,
          get: function () {
            return this.attr('showAll') ?
              this.attr('mappedItems') :
              this.attr('mappedItems').slice(0, this.attr('visibleItems'));
          }
        },
        showAll: {
          value: false,
          type: Boolean
        },
        showAllButtonText: {
          get: function () {
            return !this.attr('showAll') ?
            'Show All (' + this.attr('mappedItems.length') + ')' :
              'Show Less';
          }
        },
        visibleItems: {
          type: Number,
          value: 3
        }
      },
      isLoading: false,
      mapping: '@',
      parentInstance: null,
      selectedItem: {},
      mappedItems: [],
      filter: {
        only: [],
        exclude: []
      },
      toggleShowAll: function () {
        var isShown = this.attr('showAll');
        this.attr('showAll', !isShown);
      },
      filterMappedObjects: function (items) {
        function getTypeFromInstance(item) {
          return item.instance.type;
        }

        return GGRC.Utils.filters
          .applyTypeFilter(items,
            this.attr('filter').attr(), getTypeFromInstance);
      },
      getBinding: function () {
        return this.attr('parentInstance').get_binding(this.attr('mapping'));
      },
      getSnapshotQueryFilters: function () {
        var includeTypes = this.attr('filter.only').attr();
        var excludeTypes = this.attr('filter.exclude').attr();
        var includeFilters = {
          keys: [],
          expression: {}
        };
        var excludeFilters = excludeTypes.map(function (type) {
          return {
            expression: {
              op: {name: '!='},
              left: 'child_type',
              right: type
            },
            keys: []
          };
        });
        includeTypes.forEach(function (type) {
          includeFilters = GGRC.query_parser.join_queries({
            expression: {
              op: {name: '='},
              left: 'child_type',
              right: type
            },
            keys: []
          }, includeFilters, 'OR');
        });
        excludeFilters.push(includeFilters);
        return excludeFilters;
      },
      getSnapshotQuery: function () {
        var relevantFilters = [{
          type: this.attr('parentInstance.type'),
          id: this.attr('parentInstance.id')
        }];
        var filters = this.getSnapshotQueryFilters();
        var query = GGRC.Utils.QueryAPI
          .buildParam('Snapshot', {}, relevantFilters, [], filters);
        return {data: [query]};
      },
      getObjectQuery: function () {
        var relevantFilters = [{
          type: this.attr('parentInstance.type'),
          id: this.attr('parentInstance.id')
        }];
        var query = this.attr('relatedTypes').map(function (type) {
          return GGRC.Utils.QueryAPI
            .buildParam(type, {}, relevantFilters, [], []);
        });
        return {data: query};
      },
      loadSnapshots: function () {
        var dfd = can.Deferred();
        var query = this.getSnapshotQuery();
        this.attr('isLoading', true);
        GGRC.Utils.QueryAPI
          .makeRequest(query)
          .done(function (responseArr) {
            var data = responseArr[0];
            var values = data.Snapshot.values;
            var result = values.map(function (item) {
              return {instance: item, isSelected: false};
            });
            dfd.resolve(result);
          })
          .always(function () {
            this.attr('isLoading', false);
          }.bind(this));
        return dfd;
      },
      loadObjects: function () {
        var dfd = can.Deferred();
        var query = this.getObjectQuery();
        this.attr('isLoading', true);
        GGRC.Utils.QueryAPI
          .makeRequest(query)
          .done(function (responseArr) {
            var result = [];
            responseArr.forEach(function (responseObject) {
              var type = Object.keys(responseObject)[0];
              var values = responseObject[type].values;
              values.forEach(function (item) {
                result.push({instance: item, isSelected: false});
              });
            });

            dfd.resolve(result);
          })
          .always(function () {
            this.attr('isLoading', false);
          }.bind(this));
        return dfd;
      },
      load: function () {
        var dfd = can.Deferred();
        var binding = this.getBinding();

        if (!binding) {
          dfd.resolve([]);
          return dfd;
        }
        // Set Loading Status
        this.attr('isLoading', true);
        binding
          .refresh_instances()
          .done(function (items) {
            dfd.resolve(this.filterMappedObjects(items));
          }.bind(this))
          .fail(function () {
            dfd.resolve([]);
          })
          .always(function () {
            this.attr('isLoading', false);
          }.bind(this));
        return dfd;
      },
      setMappedObjects: function () {
        this.attr('mappedItems').replace(
          this.attr('mappedSnapshots') ?
            this.loadSnapshots() :
            this.attr('mapping') ?
              this.load() :
              this.loadObjects());
      }
    },
    init: function () {
      this.viewModel.setMappedObjects();
    },
    events: {
      '{viewModel.parentInstance} related_sources': function () {
        this.viewModel.setMappedObjects();
      },
      '{viewModel.parentInstance} related_destinations': function () {
        this.viewModel.setMappedObjects();
      }
    }
  });
})(window.can, window.GGRC);
