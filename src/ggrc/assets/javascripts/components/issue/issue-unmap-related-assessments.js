/*!
    Copyright (C) 2017 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/
import template from
  '../../../mustache/components/issue/issue-unmap-related-assessments.mustache';

(function (can, GGRC) {
  'use strict';

  GGRC.Components('issueUnmapRelatedAssessments', {
    tag: 'issue-unmap-related-assessments',
    template: template,
    viewModel: {
      define: {
        showRelatedAssessments: {
          set: function (value) {
            if (value) {
              this.attr('modalState.open', true);
              this.loadRelatedObjects();
            }
          }
        }
      },
      issueInstance: {},
      target: {},
      isLoading: false,
      modalTitle: 'ToDo: Correct message here',
      relatedAssessments: [],
      relatedSnapshots: [],
      modalState: {
        open: false
      },
      buildQuery: function (type) {
        return GGRC.Utils.QueryAPI.buildParams(
          type,
          {},
          [
            {
              type: this.attr('target.type'),
              operation: 'relevant',
              id: this.attr('target.id')
            },
            {
              type: this.attr('issueInstance.type'),
              operation: 'relevant',
              id: this.attr('issueInstance.id')
            }
          ]
        );
      },
      loadRelatedObjects: function () {
        var self = this;
        var queryApi = GGRC.Utils.QueryAPI;
        var assessmentsQuery = this.buildQuery('Assessment');
        var snapshotsQuery = this.buildQuery('Snapshot');

        queryApi
          .makeRequest({data: [assessmentsQuery[0], snapshotsQuery[0]]})
          .then(function (response) {
            var assessements = response[0].Assessment.values;
            var snapshots = response[1].Snapshot.values;
            self.attr('relatedAssessments', assessements);
            self.attr('relatedSnapshots', snapshots);
          });
      },
      openObject: function (relatedObject) {
        var model;
        var type;
        var url;

        if (relatedObject.type === 'Snapshot') {
          model = CMS.Models[relatedObject.child_type];
          type = model.root_collection;
          url = '/' + type + '/' + relatedObject.child_id;
        } else {
          url = relatedObject.viewLink;
        }

        window.open(url, '_blank');
      }
    },
    events: {
      '{viewModel.modalState} change': function () {
        // Close modal handler
        var modalState = this.viewModel.attr('modalState');
        if (!modalState.open) {
          this.viewModel.dispatch('modalClossed');
        }
      }
    }
  });
})(window.can, window.GGRC);
