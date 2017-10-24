/*
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

var viewModel = GGRC.VM.DeletablePeopleGroup.extend({
  title: '@',
  editableMode: false,
  canEdit: {},
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
