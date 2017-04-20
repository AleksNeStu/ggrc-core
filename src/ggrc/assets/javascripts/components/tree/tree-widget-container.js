/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, GGRC) {
  'use strict';

  var template = can.view(GGRC.mustache_path +
    '/components/tree/tree-widget-container.mustache');
  var TreeViewUtils = GGRC.Utils.TreeView;

  var viewModel = can.Map.extend({
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

          if (additionalFilter) {
            additionalFilter = GGRC.query_parser.parse(additionalFilter);
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
      statusFilterVisible: {
        type: Boolean,
        get: function () {
          return GGRC.Utils.State.hasFilter(this.attr('modelName'));
        }
      },
      cssClasses: {
        type: String,
        get: function () {
          var classes = [];

          if (this.attr('loading')) {
            classes.push('loading');
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
          return this.attr('options').add_item_view ||
            this.attr('model').tree_view_options.add_item_view;
        }
      },
      hideImportExport: {
        type: Boolean,
        get: function () {
          var Snapshots = GGRC.Utils.Snapshots;
          var parentInstance = this.attr('parent_instance');
          var model = this.attr('model');

          return Snapshots.isSnapshotScope(parentInstance) &&
            Snapshots.isSnapshotModel(model.model_singular);
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
          return this.attr('hideImportExport') ||
            this.attr('showGenerateAssessments');
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
    loadItems: function () {
      var modelName = this.attr('modelName');
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

      pageInfo.attr('disabled', true);
      this.attr('loading', true);

      return TreeViewUtils.loadFirstTierItems(modelName, parent, page, filter)
        .then(function (data) {
          var total = data.total;
          var modelName = this.attr('modelName');
          var countsName = this.attr('options').countsName || modelName;

          this.attr('showedItems', data.values);
          this.attr('pageInfo.total', total);
          this.attr('pageInfo.disabled', false);
          this.attr('loading', false);

          if (!this._getFilterByName('custom') &&
            !this._getFilterByName('status') &&
            total !== GGRC.Utils.CurrentPage.getCounts().attr(countsName)) {
            GGRC.Utils.CurrentPage.getCounts().attr(countsName, total);
          }

          if (this._getFilterByName('status')) {
            GGRC.Utils.CurrentPage
              .initCounts([modelName], parent.type, parent.id);
          }
        }.bind(this));
    },
    display: function () {
      if (!this.attr('loaded')) {
        this.attr('loaded', this.loadItems());
      }

      return this.attr('loaded');
    },
    setColumnsConfiguration: function () {
      var columns = TreeViewUtils.getColumnsForModel(
        this.attr('model').model_singular,
        this.attr('displayPrefs')
      );

      this.attr('columns.available', columns.available);
      this.attr('columns.selected', columns.selected);
      this.attr('columns.mandatory', columns.mandatory);
      this.attr('columns.disableConfiguration', columns.disableConfiguration);
    },
    onUpdateColumns: function (event) {
      var selectedColumns = event.columns;
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
    },
    onFilter: function () {
      this.attr('pageInfo.current', 1);
      this.loadItems();
    },
    getDepthFilter: function () {
      var filters = can.makeArray(this.attr('filters'));

      return filters.filter(function (options) {
        return options.filter && options.depth;
      }).reduce(this._concatFilters, '');
    },
    initCount: function () {
      var $el = this.attr('$el');
      var counts = GGRC.Utils.CurrentPage.getCounts();
      var countsName = this.attr('options').countsName ||
        this.attr('model').shortName;

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

        if (_verifyRelationship(instance, activeTabModel)) {
          parentInstance.on('change', callback);
        } else if (activeTabModel === instance.type) {
          _refresh(true);
        } else if (activeTabModel === 'Person' &&
          _.includes(['ObjectPerson', 'WorkflowPerson', 'UserRole'],
            instance.type)) {
          _refresh();
        }
      }

      function onDestroyed(ev, instance) {
        var current;
        var destType;
        var srcType;

        if (_verifyRelationship(instance, activeTabModel) ||
          instance instanceof CMS.Models[activeTabModel]) {
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
        if (sortByUpdatedAt) {
          self.attr('sortingInfo.sortDirection', 'desc');
          self.attr('sortingInfo.sortBy', 'updated_at');
          self.attr('pageInfo.current', 1);
        }
        self.loadItems();
      }

      function _verifyRelationship(instance, shortName) {
        if (!(instance instanceof CMS.Models.Relationship)) {
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
    })()
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
        this.viewModel.loadItems();
      },
      '{viewModel.pageInfo} pageSize': function () {
        this.viewModel.loadItems();
      },
      ' childTreeTypes': function () {
      },
      ' selectTreeItem': function (el, ev, selectedEl, instance) {
        var parent = this.viewModel.attr('parent_instance');
        var infoPaneOptions = new can.Map({
          instance: instance,
          parent_instance: parent
        });

        ev.stopPropagation();
        el.find('.item-active').removeClass('item-active');
        selectedEl.addClass('item-active');

        $('.pin-content').control()
          .setInstance(infoPaneOptions, selectedEl);
      },
      inserted: function () {
        var viewModel = this.viewModel;
        viewModel.attr('$el', this.element);

        viewModel.initCount();

        this.element.closest('.widget')
          .on('widget_hidden', viewModel._widgetHidden.bind(viewModel));
        this.element.closest('.widget')
          .on('widget_shown', viewModel._widgetShown.bind(viewModel));
      }
    }
  });
})(window.can, window.GGRC);
