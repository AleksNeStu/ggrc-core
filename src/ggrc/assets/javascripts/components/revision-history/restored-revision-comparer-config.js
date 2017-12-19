/*
 Copyright (C) 2017 Google Inc., authors, and contributors
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

const tag = 'restored-revision-comparer-config';

export default can.Component.extend({
  tag,
  viewModel: {
    instance: {},
    rightRevision: {},
    leftRevisionId: '@',
    modalTitle: 'Restore Version: Compare to Current',
    buttonView: `${GGRC.mustache_path}/modals/restore_revision.mustache`,
  },
});
