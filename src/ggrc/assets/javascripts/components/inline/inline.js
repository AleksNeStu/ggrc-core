/*!
    Copyright (C) 2017 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

(function (can, GGRC) {
  'use strict';

  GGRC.Components('inlineEditControl', {
    tag: 'inline-edit-control',
    template: can.view(
      GGRC.mustache_path + '/components/inline/inline.mustache'
    ),
    viewModel: {
      define: {
        isShowContent: {
          get: function () {
            return this.attr('hideContentInEditMode') ?
              this.attr('editMode') :
              true;
          }
        }
      },
      instance: {},
      editMode: false,
      withReadMore: false,
      isLoading: false,
      type: '@',
      value: '@',
      placeholder: '@',
      propName: '@',
      dropdownOptions: [],
      dropdownNoValue: false,
      isLastOpenInline: false,
      isEditIconDenied: false,
      hideContentInEditMode: false,
      context: {
        value: null
      },
      setEditModeInline: function (args) {
        this.attr('isLastOpenInline', args.isLastOpenInline);
        this.attr('editMode', true);
      },
      setPerson: function (scope, el, ev) {
        this.attr('context.value', ev.selectedItem.serialize().id);
      },
      unsetPerson: function (scope, el, ev) {
        ev.preventDefault();
        this.attr('context.value', null);
      },
      save: function () {
        var oldValue = this.attr('value');
        var value = this.attr('context.value');

        this.attr('editMode', false);
        // In case value is String and consists only of spaces - do nothing
        if (typeof value === 'string' && !value.trim()) {
          this.attr('context.value', '');
          value = null;
        }

        if (oldValue === value) {
          return;
        }

        this.attr('value', value);

        this.dispatch({
          type: 'inlineSave',
          value: value,
          propName: this.attr('propName')
        });
      },
      cancel: function () {
        var value = this.attr('value');
        this.attr('editMode', false);
        this.attr('context.value', value);
      },
      updateContext: function () {
        var value = this.attr('value');
        this.attr('context.value', value);
      },
      fieldValueChanged: function (args) {
        this.attr('context.value', args.value);
      }
    },
    events: {
      init: function () {
        this.viewModel.updateContext();
      },
      '{viewModel} value': function () {
        // update value in the readonly mode
        if (!this.viewModel.attr('editMode')) {
          this.viewModel.updateContext();
        }
      },
      '{window} mousedown': function (el, ev) {
        var viewModel = this.viewModel;
        var isInside;
        var editMode;

        // prevent closing of current inline after opening...
        if (viewModel.attr('isLastOpenInline')) {
          viewModel.attr('isLastOpenInline', false);
          return;
        }

        isInside = GGRC.Utils.events
          .isInnerClick(this.element, ev.target);
        editMode = viewModel.attr('editMode');

        if (editMode && !isInside) {
          viewModel.cancel();
        }
      }
    }
  });
})(window.can, window.GGRC);
