/*
 Copyright (C) 2017 Google Inc., authors, and contributors
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

const tag = 'snapshot-comparer-config';

export default can.Component.extend({
  tag,
  viewModel: {
    define: {
      rightRevision: {
        get() {
          return _.last(this.attr('rightRevisions'));
        },
      },
    },
    instance: {},
    leftRevisionId: '@',
    rightRevisions: [],
    modalTitle: 'Compare with the latest version',
    modalConfirm: 'Update',
    buttonView: `${GGRC.mustache_path}/modals/prompt_buttons.mustache`,
  },
});
