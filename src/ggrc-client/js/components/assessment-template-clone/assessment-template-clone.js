/*
  Copyright (C) 2018 Google Inc.
  Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

import '../../components/advanced-search/advanced-search-filter-container';
import '../../components/advanced-search/advanced-search-filter-state';
import '../../components/advanced-search/advanced-search-wrapper';
import '../../components/unified-mapper/mapper-results';
import '../../components/collapsible-panel/collapsible-panel';
import ObjectOperationsBaseVM from '../view-models/object-operations-base-vm';
import template from './assessment-template-clone.mustache';

export default can.Component.extend({
  tag: 'assessment-template-clone',
  template,
  viewModel(attrs, parentViewModel) {
    return ObjectOperationsBaseVM.extend({
      type: attrs.type,
      object: attrs.object,
      join_object_id: attrs.join_object_id,
      refreshTreeView: parentViewModel.attr('refreshTreeView'),
    });
  },
  events: {
    inserted() {
      this.viewModel.attr('submitCbs').fire();
    },
    closeModal() {
      if (this.element) {
        this.element.find('.modal-dismiss').trigger('click');
      }
    },
    '{window} preload': function (el, ev) {
      let modal = $(ev.target).data('modal_form');
      let options = modal && modal.options;

      if (options && options.originalTitle === 'Define Assessment template') {
        this.closeModal();
      }
    },
    '.btn-cancel click': function () {
      this.closeModal();
    },
    '.btn-clone click': function () {
      this.cloneObjects()
        .always(() => {
          this.viewModel.attr('is_saving', false);
        })
        .done(() => {
          this.closeModal();
          this.viewModel.refreshTreeView();
        });
    },
    cloneObjects() {
      let sourceIds = _.map(this.viewModel.attr('selected'), (item) => item.id);
      let destinationId = this.viewModel.attr('join_object_id');

      this.viewModel.attr('is_saving', true);

      return $.post('/api/assessment_template/clone', [{
        sourceObjectIds: sourceIds,
        destination: {
          type: 'Audit',
          id: destinationId,
        },
      }]);
    },
  },
});
