/*
 Copyright (C) 2017 Google Inc., authors, and contributors
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

import '../proposal/apply-decline-proposal-buttons';
import '../diff/instance-fields-diff';
import '../diff/instance-acl-diff';
import template from './templates/related-proposals-item.mustache';
const tag = 'related-proposals-item';

export default can.Component.extend({
  tag,
  template,
  viewModel: {
    define: {
      proposal: {
        value: {},
        set(newValue, setValue) {
          if (newValue) {
            this.setPeople(newValue);
          }

          setValue(newValue);
        },
      },
      fields: {
        get() {
          return this.attr('proposal.content.fields');
        },
      },
      status: {
        get() {
          return this.attr('proposal.status');
        },
      },
      stateTooltip: {
        get() {
          return this.getStateTooltip();
        },
      },
    },
    instance: {},
    setPeople(proposal) {
      GGRC.Utils.getPersonInfo(proposal.created_by)
        .then((person) => {
          proposal.attr('created_by', person);
      });

      GGRC.Utils.getPersonInfo(proposal.applied_by)
        .then((person) => {
          proposal.attr('applied_by', person);
      });

      GGRC.Utils.getPersonInfo(proposal.declined_by)
        .then((person) => {
          proposal.attr('declined_by', person);
      });
    },
    getStateTooltip() {
      const proposal = this.attr('proposal');
      const status = this.attr('status');
      let text;
      let date;

      if (status === 'declined') {
        date = GGRC.Utils.formatDate(proposal.attr('decline_datetime'));
        text = this.buildTooltipMessage(
          'Declined',
          proposal.attr('declined_by.email'),
          date,
          proposal.attr('decline_reason'));
      } else if (status === 'applied') {
        date = GGRC.Utils.formatDate(proposal.attr('apply_datetime'));
        text = this.buildTooltipMessage(
          'Applied',
          proposal.attr('applied_by.email'),
          date,
          proposal.attr('apply_reason'));
      }

      return text;
    },

    // TODO: fix messages
    buildTooltipMessage(startWord, email, date, comment) {
      const text = `${startWord} by ${email}, ${date}

        Comment:
        ${comment}`;

      return text;
    },
  },
});
