/*
 Copyright (C) 2017 Google Inc., authors, and contributors
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

import template from './templates/accept-decline-proposal-buttons.mustache';
const tag = 'accept-decline-proposal-buttons';

export default can.Component.extend({
  tag,
  template,
  viewModel: {
    define: {
      canDisplayAcceptButton: {
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
    declineProposal() {
    },
    acceptProposal() {
    },
  },
});

