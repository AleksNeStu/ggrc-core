/*
 Copyright (C) 2017 Google Inc., authors, and contributors
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

import template from './templates/restore-revision.mustache';
const tag = 'restore-revision';

export default can.Component.extend({
  tag,
  template,
  viewModel: {
    instance: {},
    restoredRevision: {},
    restore() {
      console.log('restore');
    },
  },
});
