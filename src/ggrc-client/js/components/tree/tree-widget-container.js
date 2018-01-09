/*
 Copyright (C) 2018 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

import './tree-header-selector';
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
import './tree-field';
import './get-owner-people-list';
import './tree-people-with-role-list-field';
import '../advanced-search/advanced-search-filter-container';
import '../advanced-search/advanced-search-mapping-container';
import '../bulk-update-button/bulk-update-button';
import '../assessment-template-clone-button/assessment-template-clone-button';
import '../dropdown/multiselect-dropdown';
import '../assessment_generator';
import '../three-dots-menu/three-dots-menu';
import template from './templates/tree-widget-container.mustache';
import * as StateUtils from '../../plugins/utils/state-utils';
import {
  isSnapshotModel,
  isSnapshotScope,
} from '../../plugins/utils/snapshot-utils';
import {REFRESH_RELATED} from '../../events/eventTypes';
import * as TreeViewUtils from '../../plugins/utils/tree-view-utils';
import {
  isMyAssessments,
  getCounts,
  initCounts,
  initMappedInstances,
} from '../../plugins/utils/current-page-utils';
import * as AdvancedSearch from '../../plugins/utils/advanced-search-utils';
import {
  getWidgetConfig,
} from '../../plugins/utils/object-versions-utils';
import Pagination from '../base-objects/pagination';
import tracker from '../../tracker';
import router from '../../router';
import Permission from '../../permission';

let viewModel;

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
      },
    },
    /**
     *
     */
    currentFilter: {
      type: String,
      get: function () {
        let filters = can.makeArray(this.attr('filters'));
        let additionalFilter = this.attr('additionalFilter');
        let optionsData;
        let objectVersionfilter;
        let isObjectVersion = this.attr('options.objectVersion');

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
      },
    },
    modelName: {
      type: String,
      get: function () {
        return this.attr('model').shortName;
      },
    },
    optionsData: {
      get: function () {
        let modelName = this.attr('modelName');
        if (!this.attr('options.objectVersion')) {
          return {
            name: modelName,
            loadItemsModelName: modelName,
            widgetId: modelName,
            countsName: modelName,
          };
        }

        return getWidgetConfig(modelName, true);
      },
    },
    statusFilterVisible: {
      type: Boolean,
      get: function () {
        return StateUtils.hasFilter(this.attr('modelName'));
      },
    },
    statusTooltipVisible: {
      type: Boolean,
      get: function () {
        return StateUtils.hasFilterTooltip(this.attr('modelName'));
      },
    },
    cssClasses: {
      type: String,
      get: function () {
        let classes = [];

        if (this.attr('loading')) {
          classes.push('loading');
        }

        if (isMyAssessments()) {
          classes.push('my-assessments');
        }

        return classes.join(' ');
      },
    },
    parent_instance: {
      type: '*',
      get: function () {
        return this.attr('options').parent_instance;
      },
    },
    allow_mapping: {
      type: Boolean,
      get: function () {
        let allowMapping = true;
        let options = this.attr('options');

        if ('allow_mapping' in options) {
          allowMapping = options.allow_mapping;
        }

        return allowMapping;
      },
    },
    allow_creating: {
      type: Boolean,
      get: function () {
        let allowCreating = true;
        let options = this.attr('options');

        if ('allow_creating' in options) {
          allowCreating = options.allow_creating;
        }

        return allowCreating;
      },
    },
    addItem: {
      type: String,
      get: function () {
        return this.attr('options.objectVersion') ?
          false :
          this.attr('options').add_item_view ||
          this.attr('model').tree_view_options.add_item_view;
      },
    },
    isSnapshots: {
      type: Boolean,
      get: function () {
        let parentInstance = this.attr('parent_instance');
        let model = this.attr('model');

        return (isSnapshotScope(parentInstance) &&
          isSnapshotModel(model.model_singular)) ||
          this.attr('options.objectVersion');
      },
    },
    showGenerateAssessments: {
      type: Boolean,
      get: function () {
        let parentInstance = this.attr('parent_instance');
        let model = this.attr('model');

        return parentInstance.type === 'Audit' &&
          model.shortName === 'Assessment';
      },
    },
    showBulkUpdate: {
      type: 'boolean',
      get: function () {
        return this.attr('options.showBulkUpdate');
      },
    },
    show3bbs: {
      type: Boolean,
      get: function () {
        return !isMyAssessments();
      },
    },
    noResults: {
      type: Boolean,
      get: function () {
        return !this.attr('loading') && !this.attr('showedItems').length;
      },
    },
    pageInfo: {
      value: function () {
        return new Pagination({
          pageSizeSelect: [10, 25, 50],
          pageSize: 10});
      },
    },
  },
  /**
   *
   */
  allow_mapping_or_creating: null,
  sortingInfo: {
    sortDirection: null,
    sortBy: null,
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
    available: [],
  },
  filters: [],
  loaded: null,
  refreshLoaded: true,
  canOpenInfoPin: true,
  loadItems: function () {
    let {widgetId} = this.attr('optionsData');
    let pageInfo = this.attr('pageInfo');
    let sortingInfo = this.attr('sortingInfo');
    let parent = this.attr('parent_instance');
    let filter = this.attr('currentFilter');
    let page = {
      current: pageInfo.current,
      pageSize: pageInfo.pageSize,
      sortBy: sortingInfo.sortBy,
      sortDirection: sortingInfo.sortDirection,
    };
    let request = this.attr('advancedSearch.request');

    pageInfo.attr('disabled', true);
    this.attr('loading', true);

    if (!!this._getFilterByName('status')) {
      initCounts([widgetId], parent.type, parent.id);
    }

    return TreeViewUtils
      .loadFirstTierItems(widgetId, parent, page, filter, request)
      .then((data) => {
        const total = data.total;
        const countsName = this.attr('options').countsName || widgetId;

        this.attr('showedItems', data.values);
        this.attr('pageInfo.total', total);
        this.attr('pageInfo.disabled', false);
        this.attr('loading', false);

        if (!this._getFilterByName('custom') &&
          !this._getFilterByName('status') &&
          total !== getCounts().attr(countsName)) {
          getCounts().attr(countsName, total);
        }
      });
  },
  display: function (needToRefresh) {
    let loadedItems;

    if (!this.attr('loaded') || needToRefresh || router.attr('refetch')) {
      loadedItems = this.loadItems()
        .then(() => this.setRefreshFlag(false)); // refreshed

      this.attr('loaded', loadedItems);
    }

    return this.attr('loaded');
  },
  setColumnsConfiguration: function () {
    let columns = TreeViewUtils.getColumnsForModel(
      this.attr('model').model_singular,
      this.attr('displayPrefs'),
      this.attr('optionsData').widgetId
    );

    this.attr('columns.available', columns.available);
    this.attr('columns.selected', columns.selected);
    this.attr('columns.mandatory', columns.mandatory);
    this.attr('columns.disableConfiguration', columns.disableConfiguration);
  },
  setSortingConfiguration: function () {
    let sortingInfo = TreeViewUtils
      .getSortingForModel(this.attr('modelName'));

    this.attr('sortingInfo.sortBy', sortingInfo.key);
    this.attr('sortingInfo.sortDirection', sortingInfo.direction);
  },
  onUpdateColumns: function (event) {
    let selectedColumns = event.columns;
    let columns = TreeViewUtils.setColumnsForModel(
      this.attr('model').model_singular,
      selectedColumns,
      this.attr('displayPrefs'),
      this.attr('optionsData').widgetId
    );

    this.attr('columns.selected', columns.selected);
  },
  onSort: function (event) {
    this.attr('sortingInfo.sortBy', event.field);
    this.attr('sortingInfo.sortDirection', event.sortDirection);

    this.attr('pageInfo.current', 1);
    this.loadItems();
    this.closeInfoPane();
  },
  onFilter: function () {
    const stopFn = tracker.start(this.attr('modelName'),
      tracker.USER_JOURNEY_KEYS.LOADING,
      tracker.USER_ACTIONS.MULTISELECT_FILTER);
    this.attr('pageInfo.current', 1);
    this.loadItems().then(stopFn);
    this.closeInfoPane();
  },
  getDepthFilter: function (deepLevel) {
    let filters = can.makeArray(this.attr('filters'));

    return filters.filter(function (options) {
      return options.filter &&
        options.depth &&
        options.filterDeepLimit > deepLevel;
    }).reduce(this._combineFilters, '');
  },
  setRefreshFlag: function (refresh) {
    this.attr('refreshLoaded', refresh);
  },
  needToRefresh: function (refresh) {
    return this.attr('refreshLoaded');
  },
  initCount: function () {
    let $el = this.attr('$el');
    let counts = getCounts();
    let countsName = this.attr('options').countsName ||
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
    let operation = options.operation || 'AND';

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
  /**
   * Concatenation active filters into one string.
   *
   * @param {String} filter - Filter string
   * @param {Object} options - Filter parameters
   * @return {string} - Result of concatenation filters.
   * @private
   */
  _combineFilters(filter, options) {
    let operation = options.operation || 'AND';

    if (filter) {
      filter += ' ' + operation + ' ' + options.filter;
    } else if (options.filter) {
      filter = options.filter;
    }

    return filter;
  },
  _getFilterByName: function (name) {
    let filter = _.findWhere(this.attr('filters'), {name: name});

    return filter && filter.filter ? filter.filter : null;
  },
  _widgetHidden: function () {
    this._triggerListeners(true);
  },
  _widgetShown: function () {
    let modelName = this.attr('optionsData').widgetId;
    let loaded = this.attr('loaded');
    let total = this.attr('pageInfo.total');
    let counts = _.get(getCounts(), modelName);

    if ((modelName === 'Issue') && !_.isNull(loaded) && (total !== counts)) {
      this.loadItems();
    }

    this._triggerListeners();
  },
  _triggerListeners: (function () {
    let activeTabModel;
    let self;

    function onCreated(ev, instance) {
      let parentInstance = self.attr('parent_instance');

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
      let current;
      let destType;
      let srcType;

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
      } else {
        // reinit mapped instances (subTree uses mapped instances)
        initMappedInstances();
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
      return _.includes(['ObjectPerson', 'UserRole'],
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
    appliedMappingItems: can.List(),
  },
  openAdvancedFilter: function () {
    this.attr('advancedSearch.filterItems',
      this.attr('advancedSearch.appliedFilterItems').slice());

    this.attr('advancedSearch.mappingItems',
      this.attr('advancedSearch.appliedMappingItems').slice());

    this.attr('advancedSearch.open', true);
  },
  applyAdvancedFilters: function () {
    let filters = this.attr('advancedSearch.filterItems');
    let mappings = this.attr('advancedSearch.mappingItems');
    let request = can.List();
    let advancedFilters;

    this.attr('advancedSearch.appliedFilterItems', filters);
    this.attr('advancedSearch.appliedMappingItems', mappings);

    advancedFilters = GGRC.query_parser.join_queries(
      GGRC.query_parser
        .parse(AdvancedSearch.buildFilter(filters, request)),
      GGRC.query_parser
        .parse(AdvancedSearch.buildFilter(mappings, request))
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
    let showedItems = this.attr('showedItems');
    let pageInfo = this.attr('pageInfo');
    let startIndex = pageInfo.pageSize * (pageInfo.current - 1);
    let relativeItemIndex = _.findIndex(showedItems,
      {id: instance.id, type: instance.type});
    return relativeItemIndex > -1 ?
      startIndex + relativeItemIndex :
      relativeItemIndex;
  },
  getRelativeItemNumber: function (absoluteNumber, pageSize) {
    let pageNumber = Math.floor(absoluteNumber / pageSize);
    let startIndex = pageSize * pageNumber;
    return absoluteNumber - startIndex;
  },
  getNextItemPage: function (absoluteNumber, pageInfo) {
    let pageNumber = Math.floor(absoluteNumber / pageInfo.pageSize) + 1;
    let dfd = can.Deferred().resolve();

    if (pageInfo.current !== pageNumber) {
      this.attr('loading', true);
      this.attr('pageInfo.current', pageNumber);
      dfd = this.loadItems();
    }

    return dfd;
  },
  updateActiveItemIndicator: function (index) {
    let element = this.attr('$el');
    element
      .find('.item-active')
      .removeClass('item-active');
    element
      .find('tree-item:nth-of-type(' + (index + 1) +
        ') .tree-item-content')
      .addClass('item-active');
  },
});

/**
 *
 */
export default GGRC.Components('treeWidgetContainer', {
  tag: 'tree-widget-container',
  template: template,
  viewModel: viewModel,
  init: function () {
    let viewModel = this.viewModel;
    let parentInstance = viewModel.attr('parent_instance');
    let allowMapping = viewModel.attr('allow_mapping');
    let allowCreating = viewModel.attr('allow_creating');

    function setAllowMapping() {
      let isAccepted = parentInstance.attr('status') === 'Accepted';
      let admin = Permission.is_allowed('__GGRC_ADMIN__');

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
      viewModel.setSortingConfiguration();
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
      let parent = this.viewModel.attr('parent_instance');
      let setInstanceDfd;
      let infoPaneOptions = new can.Map({
        instance: instance,
        parent_instance: parent,
        options: this.viewModel,
      });
      let itemNumber = this.viewModel.getAbsoluteItemNumber(instance);
      let isSubTreeItem = itemNumber === -1;

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
      let componentSelector = 'assessment-info-pane';
      let itemIndex = this.viewModel.attr('selectedItem');
      let pageInfo = this.viewModel.attr('pageInfo');
      let newInstance;
      let items;

      let relativeIndex = this.viewModel
        .getRelativeItemNumber(itemIndex, pageInfo.pageSize);
      let pageLoadDfd = this.viewModel
        .getNextItemPage(itemIndex, pageInfo);
      let pinControl = $('.pin-content').control();

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
          newInstance.dispatch({
              ...REFRESH_RELATED,
            model: 'Assessment',
          });

          this.viewModel.updateActiveItemIndicator(relativeIndex);
        }.bind(this))
        .fail(function () {
          $('body').trigger('ajax:flash', {
            error: 'Failed to fetch an object.',
          });
        })
        .always(function () {
          pinControl.setLoadingIndicator(componentSelector, false);
        });
    },
    ' refreshTree': function (el, ev) {
      ev.stopPropagation();

      this.viewModel.closeInfoPane();
      this.viewModel.loadItems();
    },
    inserted: function () {
      let viewModel = this.viewModel;
      viewModel.attr('$el', this.element);

      this.element.closest('.widget')
        .on('widget_hidden', viewModel._widgetHidden.bind(viewModel));
      this.element.closest('.widget')
        .on('widget_shown', viewModel._widgetShown.bind(viewModel));
      viewModel._widgetShown();
    },
  },
});
