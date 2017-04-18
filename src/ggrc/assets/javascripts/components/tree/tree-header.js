/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, GGRC) {
  'use strict';

  var template = can.view(GGRC.mustache_path +
    '/components/tree/tree-header.mustache');
  var viewModel = can.Map.extend({
    define: {
      cssClasses: {
        type: String,
        get: function () {
          var classes = [];

          if (this.attr('disableConfiguration')) {
            classes.push('disable-conf');
          }

          return classes.join(' ');
        }
      },
      selectableSize: {
        type: Number,
        get: function () {
          var attrCount = this.attr('selectedColumns').length;
          var result = 3;

          if (attrCount < 4) {
            result = 1;
          } else if (attrCount < 7) {
            result = 2;
          }
          return result;
        }
      }
    },
    model: null,
    columns: {},
    selectedColumns: [],
    availableColumns: [],
    disableConfiguration: null,
    mandatory: [],
    sortingInfo: null,
    /**
     * Dispatches the event with names of selected columns.
     *
     * @fires updateColumns
     */
    setColumns: function () {
      var selectedNames = [];

      can.each(this.attr('columns'), function (v, k) {
        if (v) {
          selectedNames.push(k);
        }
      });

      this.dispatch({
        type: 'updateColumns',
        columns: selectedNames
      });
    },
    onChange: function (attr) {
      var columns = this.attr('columns').serialize();

      columns[attr.attr_name] = !columns[attr.attr_name];
      this.columns.attr(columns);
    },
    onOrderChange: function ($element) {
      var field = $element.data('field');

      this.dispatch({
        type: 'sort',
        field: field
      });
    },
    initializeColumns: function () {
      var selectedColumns = this.attr('selectedColumns');
      var availableColumns = this.attr('availableColumns');
      var columns;

      if (selectedColumns.length && availableColumns.length) {
        columns = GGRC.Utils.TreeView
          .createSelectedColumnsMap(availableColumns, selectedColumns);

        this.attr('columns', columns);
      }
    },
    isActiveActioinArea: function () {
      var modelName = this.attr('model').shortName;

      return modelName === 'CycleTaskGroupObjectTask' || modelName === 'Cycle';
    },
    init: function () {
      this.initializeColumns();
    }
  });

  GGRC.Components('treeHeader', {
    tag: 'tree-header',
    template: template,
    viewModel: viewModel,
    events: {
      '{viewModel} availableColumns': function () {
        this.viewModel.initializeColumns();
      },
      '{viewModel} selectedColumns': function () {
        this.viewModel.initializeColumns();
      }
    },
    helpers: {
      sortIcon: function (attr, sortBy, sortDirection) {
        var iconClass = '';
        attr = Mustache.resolve(attr);
        sortBy = Mustache.resolve(sortBy);
        sortDirection = Mustache.resolve(sortDirection);

        if (!sortBy) {
          iconClass = 'sort';
        } else if (sortBy === attr) {
          iconClass = 'sort-' + sortDirection;
        }

        return iconClass;
      }
    }
  });
})(window.can, window.GGRC);
