/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, GGRC) {
  'use strict';

  var StateUtils = GGRC.Utils.State;

  var viewModel = can.Map.extend({
    define: {
      operation: {
        type: String,
        value: 'AND'
      },
      depth: {
        type: Boolean,
        value: false
      },
      useLocalStorage: {
        type: Boolean,
        value: true
      },
      selectedStates: {
        type: '*',
        set: function (selected) {
          this.attr('filterStates').forEach(function (item) {
            item.attr('checked', (selected.indexOf(item.value) > -1));
          });

          this.attr('options.filter',
            StateUtils.statusFilter(selected, '', this.attr('modelName')));
        }
      }
    },
    disabled: false,
    options: {},
    filters: null,
    filterStates: [],
    widgetId: null,
    modelName: null,
    displayPrefs: null,
    init: function () {
      var options = this.attr('options');
      var filter = this.attr('filter');
      var operation = this.attr('operation');
      var depth = this.attr('depth');
      var filterName = this.attr('widgetId') ||
        this.attr('modelName');
      var filterStates = StateUtils.getStatesForModel(this.attr('modelName'))
        .map(function (state) {
          return {
            value: state
          };
        });

      options.attr('filter', filter);
      options.attr('operation', operation);
      options.attr('depth', depth);
      options.attr('name', 'status');

      if (this.registerFilter) {
        this.registerFilter(options);
      }

      this.attr('filterStates', filterStates);

      if (this.attr('useLocalStorage')) {
        CMS.Models.DisplayPrefs.getSingleton().then(function (displayPrefs) {
          this.attr('displayPrefs', displayPrefs);

          this.loadTreeStates(filterName);
        }.bind(this));
      }
    },
    loadTreeStates: function (modelName) {
      // Get the status list from local storage
      var savedStates = this.attr('displayPrefs')
        .getTreeViewStates(modelName);
      var actualStates = StateUtils.getStatesForModel(modelName);
      var selectedStates = savedStates.filter(function (state) {
        return actualStates.includes(state);
      });

      if (selectedStates.length === 0) {
        selectedStates = StateUtils.getDefaultStatesForModel(modelName);
      }

      this.attr('selectedStates', selectedStates);
    },
    saveTreeStates: function (selectedStates) {
      var stateToSave;
      var filterName = this.attr('widgetId') ||
        this.attr('modelName');

      // in this case we save previous states
      if (!selectedStates) {
        return;
      }

      stateToSave = selectedStates.map(function (state) {
        return state.value;
      });

      this.attr('selectedStates', stateToSave);

      if (this.attr('useLocalStorage')) {
        this.attr('displayPrefs').setTreeViewStates(filterName, stateToSave);
      }
    }
  });

  /**
   *
   */
  GGRC.Components('treeStatusFilter', {
    tag: 'tree-status-filter',
    template: '<content/>',
    viewModel: viewModel,
    events: {
      'multiselect-dropdown multiselect:closed': function (el, ev, selected) {
        ev.stopPropagation();
        this.viewModel.saveTreeStates(selected);
        this.viewModel.dispatch('filter');
      },
      '{viewModel} disabled': function () {
        if (this.viewModel.attr('disabled')) {
          this.viewModel.attr('selectedStates', []);
        } else {
          this.viewModel.loadTreeStates(this.viewModel.attr('modelName'));
        }
      }
    }
  });
})(window.can, window.GGRC);
