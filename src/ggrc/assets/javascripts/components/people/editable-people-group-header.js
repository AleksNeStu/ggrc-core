/* !
    Copyright (C) 2017 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

(function (can, GGRC) {
  'use strict';

  GGRC.Components('editablePeopleGroupHeader', {
    tag: 'editable-people-group-header',
    template: can.view(
      GGRC.mustache_path +
      '/components/people/editable-people-group-header.mustache'
    ),
    viewModel: {
      define: {
        peopleCount: {
          get: function () {
            return this.attr('people.length');
          },
        },
      },
      editableMode: false,
      isLoading: false,
      canEdit: true,
      required: false,
      people: [],
      openEditMode: function () {
        this.dispatch('editPeopleGroup');
      },
    },
  });
})(window.can, window.GGRC);
