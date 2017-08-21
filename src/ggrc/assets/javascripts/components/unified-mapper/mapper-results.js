/*!
    Copyright (C) 2017 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/
import './mapper-results-item';
import './mapper-results-items-header';
import './mapper-results-columns-configuration';
import '../object-selection/object-selection';
import template from './templates/mapper-results.mustache';

(function (can, GGRC, CMS, $) {
  'use strict';

  var DEFAULT_PAGE_SIZE = 5;
  var DEFAULT_SORT_DIRECTION = 'asc';

  GGRC.Components('mapperResults', {
    tag: 'mapper-results',
    template: template,
    viewModel: {
      define: {
        paging: {
          value: function () {
            return new GGRC.VM.Pagination({pageSizeSelect: [5, 10, 15]});
          }
        }
      },
      columns: {
        selected: [],
        available: []
      },
      sort: {
        key: '',
        direction: DEFAULT_SORT_DIRECTION
      },
      isLoading: false,
      items: [],
      allItems: [],
      allSelected: false,
      baseInstance: null,
      filterItems: [],
      mappingItems: [],
      statusItem: {},
      selected: [],
      refreshItems: false,
      submitCbs: null,
      displayPrefs: null,
      disableColumnsConfiguration: false,
      objectsPlural: false,
      relatedAssessments: {
        state: {},
        instance: null,
        show: false
      },
      searchOnly: false,
      useSnapshots: false,
      entries: [],
      relevantTo: [],
      objectGenerator: false,
      deferredList: [],
      disabledIds: [],
      init: function () {
        var self = this;
        this.attr('submitCbs').add(this.onSearch.bind(this, true));
        CMS.Models.DisplayPrefs.getSingleton().then(function (displayPrefs) {
          self.attr('displayPrefs', displayPrefs);
        });
      },
      destroy: function () {
        this.attr('submitCbs').remove(this.onSearch.bind(this));
      },
      setItems: function () {
        var self = this;
        this.attr('items').replace([]);
        return self.load()
          .then(function (items) {
            self.attr('items', items);
            self.attr('entries', items.map(function (item) {
              return item.data;
            }));
            self.setColumnsConfiguration();
            self.setRelatedAssessments();
            self.attr('isBeforeLoad', false);
          });
      },
      setColumnsConfiguration: function () {
        var columns =
          GGRC.Utils.TreeView.getColumnsForModel(
            this.getDisplayModel().model_singular,
            this.attr('displayPrefs')
          );
        this.attr('columns.available', columns.available);
        this.attr('columns.selected', columns.selected);
        this.attr('disableColumnsConfiguration', columns.disableConfiguration);
      },
      setRelatedAssessments: function () {
        var Model = this.getDisplayModel();
        if (this.attr('useSnapshots')) {
          this.attr('relatedAssessments.show', false);
          return;
        }
        this.attr('relatedAssessments.show',
          !!Model.tree_view_options.show_related_assessments);
      },
      resetSearchParams: function () {
        this.attr('paging.current', 1);
        this.attr('paging.pageSize', DEFAULT_PAGE_SIZE);
        this.attr('sort.key', '');
        this.attr('sort.direction', DEFAULT_SORT_DIRECTION);
      },
      onSearch: function (resetParams) {
        if (resetParams) {
          this.resetSearchParams();
        }
        this.attr('refreshItems', true);
      },
      prepareRelevantQuery: function () {
        var relevantList = this.attr('relevantTo');
        var filters = relevantList.map(function (relevant) {
          return {
            type: relevant.type,
            operation: 'relevant',
            id: relevant.id
          };
        });
        return filters;
      },
      prepareRelatedQuery: function (filter) {
        if (!this.attr('baseInstance')) {
          return null;
        }

        return GGRC.Utils.QueryAPI
          .buildRelevantIdsQuery(this.attr('type'), {}, {
            type: this.attr('baseInstance.type'),
            id: this.attr('baseInstance.id'),
            operation: 'relevant'
          }, filter);
      },
      prepareUnlockedFilter: function () {
        var filterString = GGRC.Utils.State.unlockedFilter();
        return GGRC.query_parser.parse(filterString);
      },
      shouldApplyUnlockedFilter: function (modelName) {
        return modelName === 'Audit' && !this.attr('searchOnly');
      },
      loadAllItems: function () {
        this.attr('allItems', this.loadAllItemsIds());
      },
      getQuery: function (queryType, addPaging) {
        var result = {};
        var paging = {};
        var modelName = this.attr('type');
        var query;
        var relatedQuery;

        // prepare QueryAPI data from advanced search
        var request = [];
        var status;
        var filters = GGRC.query_parser.parse(
          GGRC.Utils.AdvancedSearch.buildFilter(this.attr('filterItems'),
          request));
        var mappings = GGRC.query_parser.parse(
          GGRC.Utils.AdvancedSearch.buildFilter(this.attr('mappingItems'),
          request));
        var advancedFilters = GGRC.query_parser.join_queries(filters, mappings);

        // the edge case caused by stateless objects
        if (this.attr('statusItem.value.items')) {
          status = GGRC.query_parser.parse(
            GGRC.Utils.AdvancedSearch.buildFilter([this.attr('statusItem')],
            request));
          advancedFilters = GGRC.query_parser
            .join_queries(advancedFilters, status);
        }
        result.request = request;

        // prepare pagination
        if (addPaging) {
          paging.current = this.attr('paging.current');
          paging.pageSize = this.attr('paging.pageSize');
          if (this.attr('sort.key')) {
            paging.sortBy = this.attr('sort.key');
            paging.sortDirection = this.attr('sort.direction');
          }
        }
        if (this.shouldApplyUnlockedFilter(modelName)) {
          advancedFilters = GGRC.query_parser.join_queries(
            advancedFilters,
            this.prepareUnlockedFilter());
        }

        // prepare and add main query to request
        query = GGRC.Utils.QueryAPI.buildParam(
          modelName,
          paging,
          this.prepareRelevantQuery(),
          null,
          advancedFilters);
        if (this.attr('useSnapshots')) {
          // Transform Base Query to Snapshot
          query = GGRC.Utils.Snapshots.transformQuery(query);
        }
        // Add Permission check
        query.permissions = (modelName === 'Person') ||
          this.attr('searchOnly') ? 'read' : 'update';
        query.type = queryType || 'values';
        // we need it to find result in response from backend
        result.queryIndex = request.push(query) - 1;

        // prepare and add related query to request
        // the query is used to select already mapped items
        relatedQuery = this.prepareRelatedQuery(filters);
        if (relatedQuery) {
          if (this.attr('useSnapshots')) {
            // Transform Related Query to Snapshot
            relatedQuery = GGRC.Utils.Snapshots.transformQuery(relatedQuery);
          }
          // we need it to find result in response from backend
          result.relatedQueryIndex = request.push(relatedQuery) - 1;
        }

        return result;
      },
      getModelKey: function () {
        return this.attr('useSnapshots') ?
          CMS.Models.Snapshot.model_singular :
          this.attr('type');
      },
      getModel: function () {
        return CMS.Models[this.getModelKey()];
      },
      getDisplayModel: function () {
        return CMS.Models[this.attr('type')];
      },
      setDisabledItems: function (allItems, relatedIds) {
        if (this.attr('searchOnly') || this.attr('objectGenerator')) {
          return;
        }
        allItems.forEach(function (item) {
          item.isDisabled = relatedIds.indexOf(item.data.id) !== -1;
        });
      },
      setSelectedItems: function (allItems) {
        var selectedItems;

        // get items which were selected before adding of new entries
        if (this.attr('prevSelected') && this.attr('prevSelected').length > 0) {
          this.attr('selected', this.attr('prevSelected').slice());
          this.attr('prevSelected', []);
        }

        selectedItems = can.makeArray(this.attr('selected'));
        allItems.forEach(function (item) {
          item.isSelected =
            selectedItems.some(function (selectedItem) {
              return selectedItem.id === item.id;
            });
          if (item.isSelected) {
            item.markedSelected = true;
          }
        });
      },
      transformValue: function (value) {
        var Model = this.getDisplayModel();
        if (this.attr('useSnapshots')) {
          value.snapshotObject =
            GGRC.Utils.Snapshots.toObject(value);
          value.revision.content =
            Model.model(value.revision.content);
          return value;
        }
        return Model.model(value);
      },
      load: function () {
        var self = this;
        var modelKey = this.getModelKey();
        var dfd = can.Deferred();
        var query = this.getQuery('values', true);
        this.attr('isLoading', true);
        GGRC.Utils.QueryAPI
          .makeRequest({data: query.request})
          .done(function (responseArr) {
            var data = responseArr[query.queryIndex];
            var relatedData = this.buildRelatedData(
              responseArr[query.relatedQueryIndex],
              modelKey);
            var disabledIds;

            var result =
              data[modelKey].values.map(function (value) {
                return {
                  id: value.id,
                  type: value.type,
                  data: self.transformValue(value)
                };
              });
            this.setSelectedItems(result);
            if (!this.attr('objectGenerator') && relatedData) {
              disabledIds = relatedData[modelKey].ids;
              this.attr('disabledIds', disabledIds);
              this.setDisabledItems(result, disabledIds);
            }
            // Update paging object
            this.paging.attr('total', data[modelKey].total);
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
      buildRelatedData: function (relatedData, type) {
        var deferredList = this.attr('deferredList');
        var ids;
        var empty = {};

        if (!deferredList || !deferredList.length) {
          return relatedData;
        } else if (!relatedData) {
          relatedData = {};
          relatedData[type] = {};
          ids = deferredList
            .map(function (item) {
              return item.id;
            });
        } else {
          ids = deferredList
            .filter(function (item) {
              return relatedData[item.type];
            })
            .map(function (item) {
              return item.id;
            });

          if (!ids.length) {
            // return empty data
            empty[type] = {
              ids: []
            };
            return empty;
          }
        }

        relatedData[type].ids = ids;
        return relatedData;
      },
      loadAllItemsIds: function () {
        var modelKey = this.getModelKey();
        var dfd = can.Deferred();
        var queryType = 'ids';
        var query = this.getQuery(queryType, false);

        GGRC.Utils.QueryAPI
          .makeRequest({data: query.request})
          .done(function (responseArr) {
            var data = responseArr[query.queryIndex];
            var relatedData = responseArr[query.relatedQueryIndex];
            var values = data[modelKey][queryType];
            var result = values.map(function (item) {
              return {
                id: item,
                type: modelKey
              };
            });
            // Do not perform extra mapping validation in case object generation
            if (!this.attr('objectGenerator') && relatedData) {
              result = result.filter(function (item) {
                return relatedData[modelKey].ids.indexOf(item.id) < 0;
              });
            }
            dfd.resolve(result);
          }.bind(this))
          .fail(function () {
            dfd.resolve([]);
          });
        return dfd;
      },
      setItemsDebounced: function () {
        clearTimeout(this.attr('_setItemsTimeout'));
        this.attr('_setItemsTimeout', setTimeout(this.setItems.bind(this)));
      },
      showRelatedAssessments: function (ev) {
        this.attr('relatedAssessments.instance', ev.instance);
        this.attr('relatedAssessments.state.open', true);
      }
    },
    events: {
      '{viewModel} allSelected': function (scope, ev, allSelected) {
        if (allSelected) {
          this.viewModel.loadAllItems();
        }
      },
      '{viewModel} refreshItems': function (scope, ev, refreshItems) {
        if (refreshItems) {
          this.viewModel.setItemsDebounced();
          this.viewModel.attr('refreshItems', false);
        }
      },
      '{viewModel.paging} current': function () {
        this.viewModel.setItemsDebounced();
      },
      '{viewModel.paging} pageSize': function () {
        this.viewModel.setItemsDebounced();
      },
      '{viewModel.sort} key': function () {
        this.viewModel.setItemsDebounced();
      },
      '{viewModel.sort} direction': function () {
        this.viewModel.setItemsDebounced();
      }
    }
  });
})(window.can, window.GGRC, window.CMS, window.jQuery);
