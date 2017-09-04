/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

import './tree-header-selector';
import './tree-type-selector';
import './sub-tree-expander';
import './sub-tree-wrapper';
import './sub-tree-item';
import './sub-tree-models';
import './tree-item-extra-info';
import './tree-item-actions';
import './tree-item-map';
import './tree-view';
import './tree-item';
import './tree-header';
import './tree-filter-input';
import './tree-status-filter';
import './tree-item-status-for-workflow';
import './tree-no-results';
import './tree-assignee-field';
import './tree-people-list-field';
import './tree-people-with-role-list-field';
import '../advanced-search/advanced-search-filter-container';
import '../advanced-search/advanced-search-mapping-container';
import template from './templates/tree-widget-container.mustache';

(function (can, GGRC) {
  'use strict';

  var TreeViewUtils = GGRC.Utils.TreeView;
  var CurrentPageUtils = GGRC.Utils.CurrentPage;
  var viewModel;

  if (!GGRC.tree_view) {
    GGRC.tree_view = new can.Map();
  }
  GGRC.tree_view.attr('basic_model_list', []);
  GGRC.tree_view.attr('sub_tree_for', {});

  viewModel = can.Map.extend({
    define: {
      /**
       * Condition that adds into all request to server-side Query API
       */
      additionalFilter: {
        type: String,
        value: '',
        get: function () {
          return this.attr('options').additional_filter;
        }
      },
      /**
       *
       */
      currentFilter: {
        type: String,
        get: function () {
          var filters = can.makeArray(this.attr('filters'));
          var additionalFilter = this.attr('additionalFilter');
          var optionsData;
          var objectVersionfilter;
          var isObjectVersion = this.attr('options.objectVersion');

          if (this.attr('advancedSearch.filter')) {
            return this.attr('advancedSearch.filter');
          }

          if (isObjectVersion || additionalFilter) {
            if (isObjectVersion) {
              optionsData = this.attr('optionsData');
              objectVersionfilter = optionsData.additionalFilter;
            }
            if (additionalFilter) {
              additionalFilter = objectVersionfilter ?
                objectVersionfilter + ' AND ' + additionalFilter :
                additionalFilter;
            }

            additionalFilter = GGRC.query_parser
              .parse(additionalFilter || objectVersionfilter);
          }

          return filters.filter(function (options) {
            return options.filter;
          }).reduce(this._concatFilters, additionalFilter);
        }
      },
      modelName: {
        type: String,
        get: function () {
          return this.attr('model').shortName;
        }
      },
      optionsData: {
        get: function () {
          var modelName = this.attr('modelName');
          if (!this.attr('options.objectVersion')) {
            return {
              name: modelName,
              loadItemsModelName: modelName,
              widgetId: modelName,
              countsName: modelName
            };
          }

          return GGRC.Utils.ObjectVersions
            .getWidgetConfig(modelName, true);
        }
      },
      statusFilterVisible: {
        type: Boolean,
        get: function () {
          return GGRC.Utils.State.hasFilter(this.attr('modelName'));
        }
      },
      statusTooltipVisible: {
        type: Boolean,
        get: function () {
          return GGRC.Utils.State.hasFilterTooltip(this.attr('modelName'));
        }
      },
      cssClasses: {
        type: String,
        get: function () {
          var classes = [];

          if (this.attr('loading')) {
            classes.push('loading');
          }

          if (CurrentPageUtils.isMyAssessments()) {
            classes.push('my-assessments');
          }

          return classes.join(' ');
        }
      },
      parent_instance: {
        type: '*',
        get: function () {
          return this.attr('options').parent_instance;
        }
      },
      allow_mapping: {
        type: Boolean,
        get: function () {
          var allowMapping = true;
          var options = this.attr('options');

          if ('allow_mapping' in options) {
            allowMapping = options.allow_mapping;
          }

          return allowMapping;
        }
      },
      allow_creating: {
        type: Boolean,
        get: function () {
          var allowCreating = true;
          var options = this.attr('options');

          if ('allow_creating' in options) {
            allowCreating = options.allow_creating;
          }

          return allowCreating;
        }
      },
      addItem: {
        type: String,
        get: function () {
          return this.attr('options.objectVersion') ?
            false :
            this.attr('options').add_item_view ||
            this.attr('model').tree_view_options.add_item_view;
        }
      },
      isSnapshots: {
        type: Boolean,
        get: function () {
          var Snapshots = GGRC.Utils.Snapshots;
          var parentInstance = this.attr('parent_instance');
          var model = this.attr('model');

          return (Snapshots.isSnapshotScope(parentInstance) &&
            Snapshots.isSnapshotModel(model.model_singular)) ||
            this.attr('options.objectVersion');
        }
      },
      showGenerateAssessments: {
        type: Boolean,
        get: function () {
          var parentInstance = this.attr('parent_instance');
          var model = this.attr('model');

          return parentInstance.type === 'Audit' &&
            model.shortName === 'Assessment';
        }
      },
      show3bbs: {
        type: Boolean,
        get: function () {
          return !CurrentPageUtils.isMyAssessments();
        }
      },
      noResults: {
        type: Boolean,
        get: function () {
          return !this.attr('loading') && !this.attr('showedItems').length;
        }
      },
      pageInfo: {
        value: function () {
          return new GGRC.VM.Pagination({
            pageSizeSelect: [10, 25, 50],
            pageSize: 10});
        }
      }
    },
    /**
     *
     */
    allow_mapping_or_creating: null,
    sortingInfo: {
      sortDirection: null,
      sortBy: null
    },
    /**
     *
     */
    model: null,
    /**
     *
     */
    showedItems: [],
    /**
     *
     */
    limitDepthTree: 0,
    /**
     * Legacy options which were built for a previous implementation of TreeView based on CMS.Controllers.TreeView
     */
    options: {},
    $el: null,
    loading: false,
    /**
     *
     */
    displayPrefs: {},
    columns: {
      selected: [],
      available: []
    },
    filters: [],
    loaded: null,
    refreshLoaded: true,
    canOpenInfoPin: true,
    loadItems: function () {
      var optionsData = this.attr('optionsData');
      var pageInfo = this.attr('pageInfo');
      var sortingInfo = this.attr('sortingInfo');
      var parent = this.attr('parent_instance');
      var filter = this.attr('currentFilter');
      var page = {
        current: pageInfo.current,
        pageSize: pageInfo.pageSize,
        sortBy: sortingInfo.sortBy,
        sortDirection: sortingInfo.sortDirection
      };
      var request = this.attr('advancedSearch.request');

      pageInfo.attr('disabled', true);
      this.attr('loading', true);

      return TreeViewUtils
        .loadFirstTierItems(optionsData.widgetId, parent, page, filter,
          request)
        .then(function (data) {
          var total = data.total;
          var widget = optionsData.widgetId;
          var countsName = this.attr('options').countsName || widget;

          this.attr('showedItems', data.values);
          this.attr('pageInfo.total', total);
          this.attr('pageInfo.disabled', false);
          this.attr('loading', false);

          if (!this._getFilterByName('custom') &&
            !this._getFilterByName('status') &&
            total !== CurrentPageUtils.getCounts().attr(countsName)) {
            CurrentPageUtils.getCounts().attr(countsName, total);
          }

          if (this._getFilterByName('status')) {
            CurrentPageUtils
              .initCounts([widget], parent.type, parent.id);
          }
        }.bind(this));
    },
    display: function (needToRefresh) {
      var that = this;
      var loadedItems;

      if (!this.attr('loaded') || needToRefresh) {
        loadedItems = this
        .loadItems()
        .then(function () {
          that.setRefreshFlag(false); // refreshed
        });

        this.attr('loaded', loadedItems);
      }

      return this.attr('loaded');
    },
    setColumnsConfiguration: function () {
      var columns = TreeViewUtils.getColumnsForModel(
        // todo: Fix of col config
        this.attr('model').model_singular,
        this.attr('displayPrefs'),
        true
      );

      this.attr('columns.available', columns.available);
      this.attr('columns.selected', columns.selected);
      this.attr('columns.mandatory', columns.mandatory);
      this.attr('columns.disableConfiguration', columns.disableConfiguration);
    },
    onUpdateColumns: function (event) {
      var selectedColumns = event.columns;
      // todo: fix
      var columns = TreeViewUtils.setColumnsForModel(
        this.attr('model').model_singular,
        selectedColumns,
        this.attr('displayPrefs')
      );

      this.attr('columns.selected', columns.selected);
    },
    onSort: function (event) {
      var field = event.field;
      var sortingInfo = this.attr('sortingInfo');
      var order;

      if (field !== sortingInfo.sortBy) {
        sortingInfo.attr('sortBy', field);
        sortingInfo.attr('sortDirection', 'desc');
      } else {
        order = sortingInfo.sortDirection === 'asc' ? 'desc' : 'asc';
        sortingInfo.attr('sortDirection', order);
      }

      this.attr('pageInfo.current', 1);
      this.loadItems();
      this.closeInfoPane();
    },
    onFilter: function () {
      this.attr('pageInfo.current', 1);
      this.loadItems();
      this.closeInfoPane();
    },
    getDepthFilter: function () {
      var filters = can.makeArray(this.attr('filters'));

      return filters.filter(function (options) {
        return options.filter && options.depth;
      }).reduce(this._concatFilters, '');
    },
    setRefreshFlag: function (refresh) {
      this.attr('refreshLoaded', refresh);
    },
    needToRefresh: function (refresh) {
      return this.attr('refreshLoaded');
    },
    initCount: function () {
      var $el = this.attr('$el');
      var counts = CurrentPageUtils.getCounts();
      var countsName = this.attr('options').countsName ||
        this.attr('optionsData.widgetId');

      if ($el) {
        can.trigger($el, 'updateCount', [counts.attr(countsName)]);
      }

      counts.on(countsName, function (ev, newVal, oldVal) {
        can.trigger($el, 'updateCount', [newVal]);
      });
    },
    registerFilter: function (option) {
      this.attr('filters').push(option);
    },
    /**
     * Concatenation active filters.
     *
     * @param {String} filter - Parsed filter string
     * @param {Object} options - Filter parameters
     * @return {string} - Result of concatenation filters.
     * @private
     */
    _concatFilters: function (filter, options) {
      var operation = options.operation || 'AND';

      if (filter) {
        filter = GGRC.query_parser.join_queries(
          filter,
          GGRC.query_parser.parse(options.filter),
          operation);
      } else if (options.filter) {
        filter = GGRC.query_parser.parse(options.filter);
      }

      return filter;
    },
    _getFilterByName: function (name) {
      var filter = _.findWhere(this.attr('filters'), {name: name});

      return filter && filter.filter ? filter.filter : null;
    },
    _widgetHidden: function () {
      this._triggerListeners(true);
    },
    _widgetShown: function () {
      var modelName = this.attr('optionsData').widgetId;
      var loaded = this.attr('loaded');
      var total = this.attr('pageInfo.total');
      var counts = _.get(CurrentPageUtils.getCounts(), modelName);

      if ((modelName === 'Issue') && !_.isNull(loaded) && (total !== counts)) {
        this.loadItems();
      }

      this._triggerListeners();
    },
    _triggerListeners: (function () {
      var activeTabModel;
      var self;

      function onCreated(ev, instance) {
        var parentInstance = self.attr('parent_instance');

        function callback() {
          parentInstance.unbind('change', callback);
          _refresh(true);
        }

        if (_verifyRelationship(instance, activeTabModel, parentInstance)) {
          parentInstance.on('change', callback);
        } else if (activeTabModel === instance.type) {
          _refresh(true);
        } else if (activeTabModel === 'Person' && isPerson(instance)) {
          parentInstance.refresh().then(function () {
            _refresh();
          });
        }
      }

      function onDestroyed(ev, instance) {
        var current;
        var destType;
        var srcType;

        if (_verifyRelationship(instance, activeTabModel) ||
          instance instanceof CMS.Models[activeTabModel] ||
          isPerson(instance)) {
          if (self.attr('showedItems').length === 1) {
            current = self.attr('pageInfo.current');
            self.attr('pageInfo.current',
              current > 1 ? current - 1 : 1);
          }

          // if unmapping e.g. an URL (a "Document") or an assignee from
          // the info pin, refreshing the latter is not needed
          if (instance instanceof CMS.Models.Relationship) {
            srcType = instance.source ?
              instance.source.type : null;
            destType = instance.destination ?
              instance.destination.type : null;
            if (srcType === 'Person' || destType === 'Person' ||
              srcType === 'Document' || destType === 'Document') {
              return;
            }
          } else if (instance instanceof CMS.Models.UserRole &&
            activeTabModel === 'Audit') {
            return;
          }

          _refresh();

          // TODO: This is a workaround.We need to update communication between
          //       info-pin and tree views through Observer
          if (!self.attr('$el').closest('.cms_controllers_info_pin').length) {
            $('.cms_controllers_info_pin').control().unsetInstance();
          }
        }
      }

      function _refresh(sortByUpdatedAt) {
        if (self.attr('loading')) {
          return;
        }
        if (sortByUpdatedAt) {
          self.attr('sortingInfo.sortDirection', 'desc');
          self.attr('sortingInfo.sortBy', 'updated_at');
          self.attr('pageInfo.current', 1);
        }
        self.loadItems();
        self.closeInfoPane();
      }

      function _verifyRelationship(instance, shortName, parentInstance) {
        if (!(instance instanceof CMS.Models.Relationship)) {
          return false;
        }

        if (parentInstance && instance.destination && instance.source) {
          if (instance.source.type === parentInstance.type &&
            (instance.destination.type === shortName ||
            instance.destination.type === 'Snapshot')) {
            return true;
          }
          return false;
        }
        if (instance.destination &&
          (instance.destination.type === shortName ||
          instance.destination.type === 'Snapshot')) {
          return true;
        }
        if (instance.source &&
          (instance.source.type === shortName ||
          instance.source.type === 'Snapshot')) {
          return true;
        }
        return false;
      }

      function isPerson(instance) {
        return _.includes(['ObjectPerson', 'WorkflowPerson', 'UserRole'],
          instance.type);
      }

      return function (needDestroy) {
        activeTabModel = this.options.model.shortName;
        self = this;
        if (needDestroy) {
          // Remove listeners for inactive tabs
          can.Model.Cacheable.unbind('created', onCreated);
          can.Model.Cacheable.unbind('destroyed', onDestroyed);
        } else {
          // Add listeners on creations instance or mappings objects for current tab
          // and refresh page after that.
          can.Model.Cacheable.bind('created', onCreated);
          can.Model.Cacheable.bind('destroyed', onDestroyed);
        }
      };
    })(),

    advancedSearch: {
      open: false,
      filter: null,
      request: can.List(),
      filterItems: can.List(),
      appliedFilterItems: can.List(),
      mappingItems: can.List(),
      appliedMappingItems: can.List()
    },
    openAdvancedFilter: function () {
      this.attr('advancedSearch.filterItems',
        this.attr('advancedSearch.appliedFilterItems').slice());

      this.attr('advancedSearch.mappingItems',
        this.attr('advancedSearch.appliedMappingItems').slice());

      this.attr('advancedSearch.open', true);
    },
    applyAdvancedFilters: function () {
      var filters = this.attr('advancedSearch.filterItems');
      var mappings = this.attr('advancedSearch.mappingItems');
      var request = can.List();
      var advancedFilters;

      this.attr('advancedSearch.appliedFilterItems', filters);
      this.attr('advancedSearch.appliedMappingItems', mappings);

      advancedFilters = GGRC.query_parser.join_queries(
        GGRC.query_parser
          .parse(GGRC.Utils.AdvancedSearch.buildFilter(filters, request)),
        GGRC.query_parser
          .parse(GGRC.Utils.AdvancedSearch.buildFilter(mappings, request))
      );
      this.attr('advancedSearch.request', request);

      this.attr('advancedSearch.filter', advancedFilters);

      this.attr('advancedSearch.open', false);
      this.onFilter();
    },
    removeAdvancedFilters: function () {
      this.attr('advancedSearch.appliedFilterItems', can.List());
      this.attr('advancedSearch.appliedMappingItems', can.List());
      this.attr('advancedSearch.request', can.List());
      this.attr('advancedSearch.filter', null);
      this.attr('advancedSearch.open', false);
      this.onFilter();
    },
    resetAdvancedFilters: function () {
      this.attr('advancedSearch.filterItems', can.List());
      this.attr('advancedSearch.mappingItems', can.List());
    },
    closeInfoPane: function () {
      $('.pin-content')
        .control()
        .close();
    },
    getAbsoluteItemNumber: function (instance) {
      var showedItems = this.attr('showedItems');
      var pageInfo = this.attr('pageInfo');
      var startIndex = pageInfo.pageSize * (pageInfo.current - 1);
      var relativeItemIndex = _.findIndex(showedItems,
        {id: instance.id, type: instance.type});
      return relativeItemIndex > -1 ?
        startIndex + relativeItemIndex :
        relativeItemIndex;
    },
    getRelativeItemNumber: function (absoluteNumber, pageSize) {
      var pageNumber = Math.floor(absoluteNumber / pageSize);
      var startIndex = pageSize * pageNumber;
      return absoluteNumber - startIndex;
    },
    getNextItemPage: function (absoluteNumber, pageInfo) {
      var pageNumber = Math.floor(absoluteNumber / pageInfo.pageSize) + 1;
      var dfd = can.Deferred().resolve();

      if (pageInfo.current !== pageNumber) {
        this.attr('loading', true);
        this.attr('pageInfo.current', pageNumber);
        dfd = this.loadItems();
      }

      return dfd;
    },
    updateActiveItemIndicator: function (index) {
      var element = this.attr('$el');
      element
        .find('.item-active')
        .removeClass('item-active');
      element
        .find('tree-item:nth-of-type(' + (index + 1) +
          ') .tree-item-content')
        .addClass('item-active');
    }
  });

  /**
   *
   */
  GGRC.Components('treeWidgetContainer', {
    tag: 'tree-widget-container',
    template: template,
    viewModel: viewModel,
    init: function () {
      var viewModel = this.viewModel;
      var parentInstance = viewModel.attr('parent_instance');
      var allowMapping = viewModel.attr('allow_mapping');
      var allowCreating = viewModel.attr('allow_creating');

      function setAllowMapping() {
        var isAccepted = parentInstance.attr('status') === 'Accepted';
        var admin = Permission.is_allowed('__GGRC_ADMIN__');

        viewModel.attr('allow_mapping_or_creating',
          (admin || !isAccepted) && (allowMapping || allowCreating));
      }

      CMS.Models.DisplayPrefs.getSingleton().then(function (displayPrefs) {
        viewModel.attr('displayPrefs', displayPrefs);

        if (parentInstance && 'status' in parentInstance) {
          setAllowMapping();
          parentInstance.bind('change', setAllowMapping);
        } else {
          viewModel.attr('allow_mapping_or_creating',
            allowMapping || allowCreating);
        }

        viewModel.setColumnsConfiguration();
      });
    },
    events: {
      '{viewModel.pageInfo} current': function () {
        if (!this.viewModel.attr('loading')) {
          this.viewModel.loadItems();
          this.viewModel.closeInfoPane();
        }
      },
      '{viewModel.pageInfo} pageSize': function () {
        this.viewModel.loadItems();
      },
      ' selectTreeItem': function (el, ev, selectedEl, instance) {
        var parent = this.viewModel.attr('parent_instance');
        var setInstanceDfd;
        var infoPaneOptions = new can.Map({
          instance: instance,
          parent_instance: parent,
          options: this.viewModel
        });
        var itemNumber = this.viewModel.getAbsoluteItemNumber(instance);
        var isSubTreeItem = itemNumber === -1;

        ev.stopPropagation();

        if (!this.viewModel.attr('canOpenInfoPin')) {
          return;
        }

        if (!isSubTreeItem) {
          this.viewModel.attr('selectedItem', itemNumber);
        }

        this.viewModel.attr('canOpenInfoPin', false);
        this.viewModel.attr('isSubTreeItem', isSubTreeItem);
        el.find('.item-active').removeClass('item-active');
        selectedEl.addClass('item-active');

        setInstanceDfd = $('.pin-content').control()
          .setInstance(infoPaneOptions, selectedEl, true);

        setInstanceDfd.then(function () {
          this.viewModel.attr('canOpenInfoPin', true);
        }.bind(this));
      },
      '{viewModel} selectedItem': function () {
        var componentSelector = 'assessment-info-pane';
        var itemIndex = this.viewModel.attr('selectedItem');
        var pageInfo = this.viewModel.attr('pageInfo');
        var newInstance;
        var items;

        var relativeIndex = this.viewModel
          .getRelativeItemNumber(itemIndex, pageInfo.pageSize);
        var pageLoadDfd = this.viewModel
          .getNextItemPage(itemIndex, pageInfo);
        var pinControl = $('.pin-content').control();

        if (!this.viewModel.attr('canOpenInfoPin')) {
          return;
        }

        pinControl.setLoadingIndicator(componentSelector, true);

        pageLoadDfd
          .then(function () {
            items = this.viewModel.attr('showedItems');
            newInstance = items[relativeIndex];

            return newInstance
              .refresh();
          }.bind(this))
          .then(function () {
            pinControl
              .updateInstance(componentSelector, newInstance);
            newInstance.dispatch('refreshRelatedDocuments');
            newInstance.dispatch('refreshRelatedAssessments');

            this.viewModel.updateActiveItemIndicator(relativeIndex);
          }.bind(this))
          .fail(function () {
            $('body').trigger('ajax:flash', {
              error: 'Failed to fetch an object.'
            });
          })
          .always(function () {
            pinControl.setLoadingIndicator(componentSelector, false);
          });
      },
      ' refreshTree': function (el, ev) {
        ev.stopPropagation();

        this.viewModel.loadItems();
      },
      inserted: function () {
        var viewModel = this.viewModel;
        viewModel.attr('$el', this.element);

        this.element.closest('.widget')
          .on('widget_hidden', viewModel._widgetHidden.bind(viewModel));
        this.element.closest('.widget')
          .on('widget_shown', viewModel._widgetShown.bind(viewModel));
        viewModel._widgetShown();
      }
    }
  });
})(window.can, window.GGRC);
