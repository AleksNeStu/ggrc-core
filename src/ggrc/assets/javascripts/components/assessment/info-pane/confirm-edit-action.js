/*!
    Copyright (C) 2017 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

import '../../inline/base-inline-control-title';

(function (can) {
  'use strict';

  GGRC.Components('confirmEditAction', {
    tag: 'confirm-edit-action',
    viewModel: {
      instance: {},
      setInProgress: null,
      editMode: false,
      isEditIconDenied: false,
      onStateChangeDfd: can.Deferred().resolve(),
      openEditMode: function (el) {
        this.attr('onStateChangeDfd').then(function () {
          if (this.isInEditableState()) {
            this.dispatch('setEditMode');
          }
        }.bind(this));
      },
      isInEditableState: function () {
        var editableStates = ['In Progress', 'Not Started', 'Rework Needed'];
        return _.contains(editableStates, this.attr('instance.status'));
      },
      showConfirm: function () {
        var self = this;
        var confirmation = can.Deferred();
        GGRC.Controllers.Modals.confirm({
          modal_title: 'Confirm moving Assessment to "In Progress"',
          modal_description: 'You are about to move Assessment from "' +
            this.instance.status +
            '" to "In Progress" - are you sure about that?',
          button_view: GGRC.mustache_path + '/modals/prompt_buttons.mustache'
        }, confirmation.resolve, confirmation.reject);

        return confirmation.then(function (data) {
          self.dispatch('setInProgress');
          self.openEditMode();
        });
      },
      confirmEdit: function () {
        if (!this.isInEditableState()) {
          return this.showConfirm();
        }

        // send 'isLastOpenInline' when inline is opening without confirm
        this.dispatch({
          type: 'setEditMode',
          isLastOpenInline: true
        });
      }
    }
  });
})(window.can);
