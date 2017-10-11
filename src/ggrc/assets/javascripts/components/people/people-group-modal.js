/*
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

import template from './templates/people-group-modal.mustache';

export default GGRC.Components('peopleGroupModal', {
  tag: 'people-group-modal',
  template: template,
  viewModel: {
    define: {
      selectedCount: {
        get: function () {
          return `${this
            .attr('people.length')} ${this.attr('title')} Selected`;
        },
      },
    },
    modalState: {
      open: true,
    },
    isLoading: false,
    emptyListMessage: '',
    title: '',
    people: [],
  },
});
