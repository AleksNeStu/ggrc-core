/*
 Copyright (C) 2017 Google Inc., authors, and contributors
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

import Proposal from '../../models/proposal';
import template from './templates/create-proposal.mustache';
import {REFRESH_TAB_CONTENT} from '../../events/eventTypes';
const tag = 'create-proposal';

export default can.Component.extend({
  tag,
  template,
  viewModel: {
    define: {
      isDisabledButton: {
        get() {
          return !this.hasChanges() || this.attr('loading');
        },
      },
    },
    instance: {},
    proposalAgenda: '',
    loading: false,
    create(element, event) {
      const instance = this.attr('instance');
      const instanceFields = instance.attr();
      let proposal;

      event.preventDefault();
      this.attr('loading', true);

      proposal = {
        agenda: this.attr('proposalAgenda'),
        instance: {
          id: instanceFields.id,
          type: instanceFields.type,
        },
        full_instance_content: instanceFields,
        context: instanceFields.context,
      };

      this.saveProposal(proposal, element);
    },
    saveProposal(proposal, element) {
      const instance = this.attr('instance');

      new Proposal(proposal).save().then(
        () => {
          this.attr('loading', false);
          instance.refresh().then(() => {
            instance.dispatch({
              ...REFRESH_TAB_CONTENT,
              tabId: 'tab-related-proposals',
            });
          });
          this.closeModal(element);
        }, (error) => {
          this.attr('loading', false);
          console.error(error.statusText);
        }
      );
    },
    closeModal(element) {
      // TODO: fix
      $(element).closest('.modal')
        .find('.modal-dismiss')
        .trigger('click');
    },
    hasChanges() {
      const instance = this.attr('instance');
      const hasPending = GGRC.Utils.hasPending(instance);
      const isDirty = instance.isDirty(true);

      return isDirty || hasPending;
    },
  },
});
