/*
 Copyright (C) 2017 Google Inc., authors, and contributors
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

import Proposal from '../../models/proposal';
import template from './templates/create-proposal.mustache';
const tag = 'create-proposal';

export default can.Component.extend({
  tag,
  template,
  viewModel: {
    instance: {},
    proposalAgenda: '',
    loading: false,
    create(element, event) {
      const instance = this.attr('instance').attr();
      let proposal;

      event.preventDefault();
      this.attr('loading', true);

      proposal = {
        agenda: this.attr('proposalAgenda'),
        instance: {
          id: instance.id,
          type: instance.type,
        },
        full_instance_content: instance,
        context: instance.context,
      };

      new Proposal(proposal).save()
        .then(() => {
          this.attr('loading', false);
          this.closeModal(element);
        }, (error) => {
          this.attr('loading', false);
          console.error(error.statusText);
        });
    },
    closeModal(element) {
      // TODO: fix
      $(element).closest('.modal')
        .find('.modal-dismiss')
        .trigger('click');
    },
  },
});
