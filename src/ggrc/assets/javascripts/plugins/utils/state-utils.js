/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (GGRC) {
  'use strict';
  /**
   * Utils for state.
   */
  var snapshotableObject = GGRC.config.snapshotable_objects;
  var objectVersions = _.map(snapshotableObject, function (obj) {
    return obj + '_versions';
  });

  GGRC.Utils.State = (function () {
    var statesModels = [
      {
        models: ['Assessment Template', 'Project', 'Program']
          .concat(snapshotableObject)
          .concat(objectVersions),
        states: ['Active', 'Draft', 'Deprecated']
      },
      {
        models: ['Assessment'],
        states: [
          'Not Started', 'In Progress', 'In Review',
          'Completed and Verified', 'Completed (no verification)'
        ]
      },
      {
        models: ['Audit'],
        states: [
          'Planned', 'In Progress', 'Manager Review',
          'Ready for External Review', 'Completed'
        ]
      },
      {
        models: [
          'Person', 'CycleTaskGroupObjectTask',
          'AssessmentTemplate', 'Workflow',
          'TaskGroup', 'Cycle'
        ],
        states: []
      },
      {
        models: ['Issue'],
        states: [
          'Active', 'Draft', 'Deprecated', 'Fixed', 'Fixed and Verified'
        ]
      }
    ];

    /**
     * Check if model has state.
     * @param {String} model - The model name
     * @return {Boolean} True or False
     */
    function hasState(model) {
      var pair = getStatesModelsPair(model);

      if (!pair) {
        return false;
      }

      return pair.states.length > 0;
    }

    /**
     * Check if model should have filter by state.
     * @param {String} model - The model name
     * @return {Boolean} True or False
     */
    function hasFilter(model) {
      return hasState(model);
    }

    /**
     * Check if tooltip should be shown for filter by state
     * @param {String} model - The model name
     * @return {Boolean} True or False
     */
    function hasFilterTooltip(model) {
      return model === 'Product' || model === 'System';
    }

    /**
     * Get States-Models pair.
     * @param {String} model - The model name
     * @return {Object} object with 'models' and 'states' properties
     */
    function getStatesModelsPair(model) {
      var pairs = statesModels.filter(function (item) {
        return item.models.indexOf(model) > -1;
      });

      return pairs.length > 0 ? pairs[0] : null;
    }

     /**
     * Get states for model.
     * @param {String} model - The model name
     * @return {Array} array of strings
     */
    function getStatesForModel(model) {
      var pair = getStatesModelsPair(model);
      return pair ? pair.states : [];
    }

    /**
     * Transform query for objects into query which filter them by state.
     * @param {Array} statuses - array of active statuses
     * @param {String} filterString - original query string
     * @param {String} modelName - model name
     * @return {String} The transformed query
     */
    function statusFilter(statuses, filterString, modelName) {
      var filter = modelName === 'Assessment' ?
        buildAssessmentFilter(statuses, buildStatusesFilterString) :
        buildStatusesFilterString(statuses);

      filterString = filterString || '';
      if (filter !== '') {
        if (filterString !== '') {
          return filterString + ' And ' + filter;
        }
        return filter;
      }

      return filterString;
    }

    /**
     * Return query for unlocked objects
     * @return {String} The unlocked query
     */
    function unlockedFilter() {
      return '"Archived"="False"';
    }

    /**
     * Transform query for objects into query which filter them by state.
     * @param {Array} statuses - array of active statuses
     * @param {function} builder - function building a query
     * @param {String} modelName - model name
     * @return {String} The transformed query
     */
    function buildStatusFilter(statuses, builder, modelName) {
      var filter = modelName === 'Assessment' ?
        buildAssessmentFilter(statuses, builder) :
        builder(statuses);
      return filter;
    }

    /**
     * Build statuses filter string
     * @param {Array} statuses - array of active statuses
     * @return {String} statuses filter
     */
    function buildStatusesFilterString(statuses) {
      return statuses.map(function (item) {
        // wrap in quotes
        return '"Status"="' + item + '"';
      }).join(' Or ');
    }

    /**
     * Build statuses filter for Assessment model
     * @param {Array} statuses - array of active statuses
     * @param {function} builder - function building a query
     * @return {String} statuses filter
     */
    function buildAssessmentFilter(statuses, builder) {
      var verifiedIndex = statuses.indexOf('Completed and Verified');
      var completedIndex = statuses.indexOf('Completed (no verification)');
      var isVerified = false;
      var filter;

      // copy array. Do not change original
      statuses = statuses.slice();

      // do not update statuses
      if (verifiedIndex === -1 && completedIndex === -1) {
        return builder(statuses);
      }

      if (verifiedIndex > -1 && completedIndex > -1) {
        // server doesn't know about "Completed (no verification)"
        // we replace it with "Completed"
        statuses.splice(completedIndex, 1, 'Completed');

        // database doesn't have "Verified" status
        // remove it
        statuses.splice(verifiedIndex, 1);

        return builder(statuses);
      }

      if (completedIndex > -1 && verifiedIndex === -1) {
        statuses.splice(completedIndex, 1, 'Completed');
      } else if (verifiedIndex > -1 && completedIndex === -1) {
        isVerified = true;
        statuses.splice(verifiedIndex, 1);
        statuses.push('Completed');
      }

      filter = builder(statuses);
      return filter + ' AND verified=' + isVerified;
    }

    /**
     * Get default states for model.
     * @param {String} model - The model name
     * @return {Array} List of default states for model
     */
    function getDefaultStatesForModel(model) {
      return GGRC.Utils.CurrentPage.isMyAssessments() ?
        ['Not Started', 'In Progress'] :
        getStatesForModel(model);
    }

    return {
      hasState: hasState,
      hasFilter: hasFilter,
      hasFilterTooltip: hasFilterTooltip,
      statusFilter: statusFilter,
      unlockedFilter: unlockedFilter,
      getStatesForModel: getStatesForModel,
      getDefaultStatesForModel: getDefaultStatesForModel,
      buildStatusFilter: buildStatusFilter
    };
  })();
})(window.GGRC);
