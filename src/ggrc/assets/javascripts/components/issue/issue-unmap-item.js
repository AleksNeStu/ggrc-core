/*
    Copyright (C) 2017 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/
import template from './issue-unmap-item.mustache';

var LoadRelatedError = 'loadRelated';
var UnmapRelatedError = 'unmapRelated';
var errorsMap = {
  loadRelated: 'There was a problem with retrieving related objects.',
  unmapRelated: 'There was a problem with unmapping.',
};
var queryApi = GGRC.Utils.QueryAPI;

export default GGRC.Components('issueUnmapItem', {
  tag: 'issue-unmap-item',
  template: template,
  viewModel: {
    define: {
      paging: {
        value: function () {
          return new GGRC.VM.Pagination({pageSizeSelect: [5, 10, 15]});
        },
      },
    },
    issueInstance: {},
    target: {},
    modalTitle: 'Unmapping',
    showRelatedObjects: false,
    isLoading: false,
    relatedSnapshots: [],
    relatedAudit: {},
    total: null,
    modalState: {
      open: false,
    },
    canUnmap: function () {
      return GGRC.Utils.allowed_to_map(this.attr('issueInstance'),
        this.attr('target'), {isIssueUnmap: true});
    },

    processRelatedSnapshots: function () {
      this.loadRelatedObjects().done(function () {
        if (this.attr('total')) {
          this.showModal();
        } else {
          this.unmap();
        }
      }.bind(this));
    },
    buildQuery: function (type) {
      return GGRC.Utils.QueryAPI.buildParam(
        type,
        this.attr('paging'),
        null,
        null,
        {
          expression: {
            op: {name: 'cascade_unmappable'},
            issue: {id: this.attr('issueInstance.id')},
            assessment: {id: this.attr('target.id')},
          },
        }
      );
    },
    loadRelatedObjects: function () {
      var snapshotsQuery = this.buildQuery('Snapshot');
      var auditsQuery = this.buildQuery('Audit');

      this.attr('isLoading', true);
      return queryApi.makeRequest({data: [snapshotsQuery, auditsQuery]})
        .done(function (resp) {
          var snapshots = resp[0].Snapshot;
          var audits = resp[1].Audit;
          this.attr('total', snapshots.total + audits.total);
          this.attr('relatedAudit', audits.values[0]);
          this.attr('relatedSnapshots', snapshots.values);
          this.attr('paging.total', snapshots.total);
        }.bind(this))
        .fail(this.showError.bind(this, LoadRelatedError))
        .always(function () {
          this.attr('isLoading', false);
        }.bind(this));
    },
    showModal: function () {
      var total = this.attr('total');
      var title = 'Unmapping (' + total +
        (total > 1 ? ' objects' : ' object') + ')';
      this.attr('modalTitle', title);
      this.attr('modalState.open', true);
    },
    openObject: function (relatedObject) {
      var model;
      var type;
      var url;
      var objectType = relatedObject.type;
      var id = relatedObject.id;

      if (relatedObject.type === 'Snapshot') {
        objectType = relatedObject.child_type;
        id = relatedObject.child_id;
      }

      model = CMS.Models[objectType];
      type = model.root_collection;
      url = '/' + type + '/' + id;

      window.open(url, '_blank');
    },
    unmap: function () {
      var sourceIds = _.union(
        _.pluck(this.attr('issueInstance.related_sources'), 'id'),
        _.pluck(this.attr('issueInstance.related_destinations'), 'id'));
      var destinationIds = _.union(
        _.pluck(this.attr('target.related_sources'), 'id'),
        _.pluck(this.attr('target.related_destinations'), 'id'));

      var relId = _.intersection(sourceIds, destinationIds);
      var relationship = CMS.Models.Relationship.findInCacheById(relId);
      var currentObject = GGRC.page_instance();

      this.attr('isLoading', true);

      relationship
       .refresh()
       .then(function () {
         return relationship.unmap(true);
       })
       .done(function () {
        if (currentObject === this.attr('issueInstance')) {
          GGRC.navigate(this.attr('issueInstance.viewLink'));
        } else {
          this.attr('modalState.open', false);
        }
       }.bind(this))
       .fail(this.showError.bind(this, UnmapRelatedError))
       .always(function () {
         this.attr('isLoading', false);
       }.bind(this));
    },
    showError: function (errorKey) {
      GGRC.Errors.notifier('error', errorsMap[errorKey]);
    },
  },
  events: {
    click: function (el, ev) {
      ev.preventDefault();
      if (this.viewModel.attr('target.type') === 'Assessment' &&
        !this.viewModel.attr('issueInstance.allow_unmap_from_audit')) {
        this.viewModel.processRelatedSnapshots();
      } else {
        this.viewModel.dispatch('unmapIssue');
      }
    },
    '{viewModel.paging} current': function () {
      this.viewModel.loadRelatedObjects();
    },
    '{viewModel.paging} pageSize': function () {
      this.viewModel.loadRelatedObjects();
    },
  },
});
