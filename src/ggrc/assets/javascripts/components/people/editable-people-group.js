/*
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

import './people-group-modal';
import './editable-people-group-header';

const SHOW_MODAL_LIMIT = 4;

var viewModel = GGRC.VM.DeletablePeopleGroup.extend({
  title: '@',
  canEdit: {},
  showPeopleGroupModal: false,
  define: {
    editableMode: {
      set: function (newValue, setValue) {
        this.attr('showPeopleGroupModal',
          this.attr('people.length') > SHOW_MODAL_LIMIT);
        setValue(newValue);
      },
    },
    showSeeMoreLink: {
      get: function () {
        return !this.attr('editableMode') &&
          this.attr('people.length') > SHOW_MODAL_LIMIT;
      },
    },
    readonlyPeople: {
      get: function () {
        if (this.attr('showPeopleGroupModal')) {
          return this.attr('people').attr().slice(0, SHOW_MODAL_LIMIT);
        }

        return this.attr('people').attr();
      },
    },
  },
  personSelected: function (person) {
    this.dispatch({
      type: 'personSelected',
      person: person,
      groupId: this.attr('groupId'),
    });
  },
  save: function () {
    this.dispatch('saveChanges');
  },
  cancel: function () {
    this.changeEditableMode(false);
  },
  changeEditableMode: function (editableMode) {
    this.attr('editableMode', editableMode);
    this.dispatch({
      type: 'changeEditableMode',
      editableMode: editableMode,
      groupId: this.attr('groupId'),
    });
  },
});

export default GGRC.Components('editablePeopleGroup', {
  tag: 'editable-people-group',
  template: can.view(
    GGRC.mustache_path +
    '/components/people/editable-people-group.mustache'
  ),
  viewModel: viewModel,
  events: {
    '{window} mousedown': function (el, ev) {
      var viewModel = this.viewModel;
      var isInside = GGRC.Utils.events.isInnerClick(this.element, ev.target);
      var editableMode = viewModel.attr('editableMode');

      if (!isInside && editableMode) {
        viewModel.save();
      }
    },
  },
});
