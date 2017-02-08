/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, GGRC) {
  'use strict';

  var queryAPI = GGRC.Utils.QueryAPI;
  var REQUESTED_TYPE = 'Assessment';
  var FILTER_OPTIONS = Object.freeze({
    current: 1,
    pageSize: 1,
    sortBy: 'finished_date',
    sortDirection: 'desc'
  });
  var REQUIRED_FIELDS = Object.freeze(['finished_date']);

  can.Component.extend({
    tag: 'last-assessment-date',
    template: '<content/>',
    viewModel: {
      controlId: null,
      lastAssessmentDate: null
    },
    init: function () {
      this.loadLastAssessment(this.viewModel.controlId);
    },
    loadLastAssessment: function (id) {
      var viewModel = this.viewModel;
      var params = queryAPI.buildParam(REQUESTED_TYPE, FILTER_OPTIONS, {
        type: 'Control',
        id: id
      }, REQUIRED_FIELDS);

      queryAPI.makeRequest({data: [params]}).then(function (response) {
        var assessment = response[0][REQUESTED_TYPE].values[0];
        var finishedDate;
        if (assessment) {
          finishedDate = assessment.finished_date;
        }
        viewModel.attr('lastAssessmentDate', finishedDate);
      });
    }
  });
})(window.can, window.GGRC);
