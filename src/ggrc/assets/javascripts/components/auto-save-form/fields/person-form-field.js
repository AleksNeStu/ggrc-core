/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */
(function (can, GGRC) {
  'use strict';

  GGRC.Components('personFormField', {
    tag: 'person-form-field',
    template: can.view(
      GGRC.mustache_path +
      '/components/auto-save-form/fields/person-form-field.mustache'
    ),
    viewModel: {
      define: {
        _value: {
          set: function (newValue, setValue, onError, oldValue) {
            setValue(newValue);
            if (oldValue === undefined ||
              oldValue === newValue) {
              return;
            }
            this.valueChanged(newValue);
          }
        },
        value: {
          set: function (newValue, setValue) {
            setValue(newValue);
            this.attr('_value', newValue);
          }
        },
        fieldId: {
          type: 'number'
        }
      },
      withDetails: false,
      setPerson: function (ev) {
        this.attr('_value', ev.selectedItem.serialize().id);
      },
      unsetPerson: function (scope, el, ev) {
        ev.preventDefault();
        this.attr('_value', null);
      },
      valueChanged: function (newValue) {
        this.dispatch({
          type: 'valueChanged',
          fieldId: this.attr('fieldId'),
          value: newValue
        });
      }
    }
  });
})(window.can, window.GGRC);
