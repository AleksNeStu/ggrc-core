/*
 Copyright (C) 2017 Google Inc., authors, and contributors
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

import template from './templates/related-proposals.mustache';
const tag = 'related-proposals';

export default can.Component.extend({
  tag,
  template,
  viewModel: {
    baseInstance: {},
    define: {
      predefinedFilter: {
        get() {
          const filter = {
            expression: {
              left: {
                left: 'instance_type',
                op: {name: '='},
                right: this.attr('baseInstance.type'),
              },
              op: {name: 'AND'},
              right: {
                left: 'instance_id',
                op: {name: '='},
                right: this.attr('baseInstance.id'),
              },
            },
          };

          return filter;
        },
      },
    },
    proposals: [],
    checkTabWarning() {
      const proposals = this.attr('proposals');
      let proposed;
      if (!proposals || !proposals.length) {
        return;
      }

      proposed = proposals.filter((item) => {
        return item.instance.status === 'proposed';
      });

      this.dispatch({
        type: 'updateProposalsWarning',
        warning: proposed.length > 0,
      });
    },
  },
  events: {
    '{viewModel.proposals} change'() {
      this.viewModel.checkTabWarning();
    },
  },
});
