/*
 Copyright (C) 2017 Google Inc., authors, and contributors
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

import Pagination from '../../base-objects/pagination';
import template from './templates/related-revisions.mustache';
import './related-revisions-item';
const tag = 'related-revisions';

export default can.Component.extend({
  tag,
  template,
  viewModel: {
    define: {
      paging: {
        value: function () {
          return new Pagination({pageSizeSelect: [5, 10, 15]});
        },
      },
    },
    instance: {},
    visibleRevisions: [],
    revisions: [],
    loading: false,
    setVisibleRevisions() {
      const visibleRevisions = this.attr('revisions')
        .slice(...this.attr('paging.limits'));
      this.attr('visibleRevisions', visibleRevisions);

      // recalculate pages
      this.attr('paging.total', this.attr('revisions').length);
    },
    loadRevisions() {
      const instance = this.attr('instance');

      if (!instance) {
        return;
      }

      this.attr('loading', true);

      this.buildRevisionRequest('resource').then((data) => {
        this.attr('paging.total', data.length);
        this.attr('revisions', data);
        this.attr('loading', false);

        this.setVisibleRevisions();
      });
    },
    buildRevisionRequest(attr) {
      const query = {__sort: '-updated_at'};
      query[attr + '_type'] = this.attr('instance.type');
      query[attr + '_id'] = this.attr('instance.id');
      return CMS.Models.Revision.findAll(query);
    },
  },
  events: {
    inserted() {
      this.viewModel.loadRevisions();
    },
    '{viewModel.paging} current': function () {
      this.viewModel.setVisibleRevisions();
    },
    '{viewModel.paging} pageSize': function () {
      this.viewModel.setVisibleRevisions();
    },
  },
});
