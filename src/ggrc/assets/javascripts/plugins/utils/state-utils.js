/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (GGRC) {
  'use strict';
  /**
   * Utils for state.
   */
  GGRC.Utils.State = (function () {
    var stateModels = ['AccessGroup', 'Clause', 'Contract',
       'Control', 'DataAsset', 'Facility', 'Issue', 'Market',
       'Objective', 'OrgGroup', 'Policy', 'Process', 'Product', 'Program',
       'Project', 'Regulation', 'Risk', 'Section', 'Standard', 'System',
       'Threat', 'Vendor'];
    var notFilterableModels = ['Person', 'AssessmentTemplate', 'Workflow',
        'TaskGroup', 'Cycle', 'CycleTaskGroupObjectTask'];

    /**
     * Check if model has state.
     * @param {String} model - The model name
     * @return {Boolean} True or False
     */
    function hasState(model) {
      return stateModels.indexOf(model) > -1;
    }

    /**
     * Check if model should have filter by state.
     * @param {String} model - The model name
     * @return {Boolean} True or False
     */
    function hasFilter(model) {
      return notFilterableModels.indexOf(model) < 0;
    }

    /**
     * Transform query for objects into query which filter them by state.
     * @param {Array} statuses - array of active statuses
     * @param {String} filterString - original query string
     * @return {String} The transformed query
     */
    function statusFilter(statuses, filterString) {
      var filter = statuses
        .map(function (item) {
          return 'Status=' + item;
        }).join(' Or ');

      filterString = filterString || '';
      if (filter !== '') {
        if (filterString !== '') {
          return filterString + ' And ' + filter;
        }
        return filter;
      }

      return filterString;
    }

    return {
      hasState: hasState,
      hasFilter: hasFilter,
      statusFilter: statusFilter
    };
  })();
})(window.GGRC);
