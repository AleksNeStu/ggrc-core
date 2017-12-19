/*
 Copyright (C) 2017 Google Inc., authors, and contributors
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

import template from './templates/apply-decline-proposal.mustache';
import {REFRESH_TAB_CONTENT} from '../../events/eventTypes';
const tag = 'apply-decline-proposal';

export default can.Component.extend({
  tag,
  template,
  viewModel: {
    define: {
      canDisplayApplyButton: {
        get() {
          const proposalStatus = this.attr('proposal.status');
          return proposalStatus === 'proposed' ||
            proposalStatus === 'declined';
        },
      },
      canDisplayDeclineButton: {
        get() {
          const proposalStatus = this.attr('proposal.status');
          return proposalStatus === 'proposed';
        },
      },
    },
    proposal: {},
    instance: {},
    isLoading: false,
    title: '',
    description: '',
    actionComment: '',
    isApplyAction: false,
    modalState: {
      open: false,
    },
    getModalDescriptionText(isDecline) {
      const date = GGRC.Utils.formatDate(this.attr('proposal.created_at'));
      const email = this.attr('proposal.proposed_by.email');
      const action = isDecline ? 'declining' : 'applying';

      return `You're ${action} the version - ${email}, ${date}`;
    },
    closeModal() {
      this.attr('actionComment', '');
      this.attr('modalState.open', false);
    },
    declineProposal() {
      this.attr('title', 'Decline confirmation');
      this.attr('description', this.getModalDescriptionText(true));
      this.attr('isApplyAction', false);
      this.attr('modalState.open', true);
    },
    applyProposal() {
      this.attr('title', 'Apply confirmation');
      this.attr('description', this.getModalDescriptionText(false));
      this.attr('isApplyAction', true);
      this.attr('modalState.open', true);
    },
    confirm(isApply) {
      this.attr('isLoading', true);

      // refresh for getting E-tag
      this.attr('proposal').refresh().then(() => {
        this.prepareDataAndSave(isApply);
      });
    },
    prepareDataAndSave(isApply) {
      const comment = this.attr('actionComment');
      // create new model. No need to 'PUT' full object data
      const proposalModel = new CMS.Models.Proposal();

      if (isApply) {
        proposalModel.attr('apply_reason', comment);
        proposalModel.attr('status', 'applied');
      } else {
        proposalModel.attr('decline_reason', comment);
        proposalModel.attr('status', 'declined');
      }

      proposalModel.attr('id', this.attr('proposal.id'));

      proposalModel.save().then(
        () => {
          this.attr('isLoading', false);
          this.attr('modalState.open', false);
          this.attr('actionComment', '');

          if (isApply) {
            this.refreshPage();
          }
        },
        (error) => {
          console.log(error);
        }
      );
    },
    refreshPage() {
      const instance = this.attr('instance');
      instance.refresh().then(() => {
        instance.dispatch({
          ...REFRESH_TAB_CONTENT,
          tabId: 'tab-related-proposals',
        });
      });
    },
  },
});
