/*!
    Copyright (C) 2017 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

(function (can, $) {
  'use strict';

  GGRC.Components('inlineEdit', {
    tag: 'inline-edit',
    template: can.view(
      GGRC.mustache_path + '/components/inline_edit/inline.mustache'
    ),
    scope: {
      instance: null,
      caId: null,
      property: '@',
      value: null,
      values: null,
      readonly: false,  // whether or not the value can be edited
      isSaving: false,
      mandatory: null,
      context: {
        isEdit: false,
        value: null,
        values: null
      },
      emptyText: '@',
      $rootEl: null,
      type: '@',

      // event names definitions
      _EV_INSTANCE_SAVE: 'on-save',  // "save" button is clicked
      _EV_BEFORE_EDIT: 'before-edit',  // before entering the edit mode

      /**
       * Enter the edit mode if editing is allowed (i.e. the readonly option is
       * not set).
       *
       * If the readonly option is enabled, do not do anything. The same if the
       * beforeEdit handler is not defined, or if the promise it returns is not
       * resolved.
       *
       * @param {can.Map} scope - the scope object itself (this)
       * @param {jQuery.Element} $el - the DOM element that triggered the event
       * @param {jQuery.Event} ev - the event object
       */
      enableEdit: function (scope, $el, ev) {
        var confirmation;
        var onBeforeEdit = this.$rootEl.attr('can-' + scope._EV_BEFORE_EDIT);

        ev.preventDefault();

        if (this.attr('readonly')) {
          return;
        }

        if (!onBeforeEdit) {
          this.attr('context.isEdit', true);
          return;
        }

        confirmation = this.$rootEl.triggerHandler({
          type: this._EV_BEFORE_EDIT
        });

        confirmation.done(function () {
          this.attr('context.isEdit', true);
        }.bind(this));   // and do nothing if no confirmation by the user
      },

      onCancel: function (ctx, el, ev) {
        ev.preventDefault();
        this.attr('context.isEdit', false);
        this.attr('context.value', this.attr('_value'));
      },
      onSave: function (ctx, el, ev) {
        var caid = this.attr('caId');
        var property = this.attr('property');
        var instance = this.attr('instance');
        var oldValue = this.attr('value');
        var onSaveHandler = this.$rootEl.attr('can-' + this._EV_INSTANCE_SAVE);
        var value = this.attr('context.value');
        var type = this.attr('type');

        ev.preventDefault();

        // If a custom onSave handler is provided, trigger it, otherwise use
        // the component's onSave logic (deprecated, should be moved out of the
        // component as it is not the latter's resposnisiblity).
        if (onSaveHandler) {
          // CAUTION: triggering the event must come before changing any of the
          // scope attributes, otherwise the event gets lost for some reason
          this.$rootEl.triggerHandler({
            type: this._EV_INSTANCE_SAVE,
            oldVal: oldValue,
            newVal: value
          });

          this.attr('context.isEdit', false);
          return;
        }

        this.attr('context.isEdit', false);
        if (oldValue === value) {
          return;
        } else if (type === 'checkbox' && Number(oldValue) === Number(value)) {
          // cast to Number and compare. return if equal.
          return;
        } else if (type === 'person') {
          if (value && oldValue && oldValue.id === value.id) {
            // check instances of value and oldValue.
            // return if instances are exist and ids are equal.
            return;
          } else if (!value && !oldValue) {
            // return if instances are not exist.
            return;
          }
        }

        this.attr('_value', value);
        this.attr('isSaving', true);

        if (this.attr('caId')) {
          if (type === 'checkbox') {
            value = value ? 1 : 0;
          }
          if (type === 'person') {
            value = value ? ('Person:' + value.id) : 'Person:None';
          }
          if (type === 'dropdown') {
            if (value && value === '') {
              value = undefined;
            }
          }
          instance.attr('custom_attributes.' + caid, value);
        } else {
          instance.attr(property, value);
        }
        instance.attr('isReadyForRender', false);
        instance.save()
          .done(function () {
            $(document.body).trigger('ajax:flash', {
              success: 'Saved'
            });
          })
          .fail(function () {
            this.attr('context.value', this.attr('_value'));
            $(document.body).trigger('ajax:flash', {
              error: 'There was a problem saving'
            });
          }.bind(this))
          .always(function () {
            this.attr('isSaving', false);
          }.bind(this));
      }
    },
    init: function (element, options) {
      var scope = this.scope;
      var value = scope.attr('value');
      var values = scope.attr('values');
      var property = scope.attr('property');
      var instance = scope.attr('instance');
      var type = scope.attr('type');

      scope.attr('$rootEl', $(element));

      if (scope.attr('caId')) {
        if (type === 'checkbox') {
          value = value === '1';
        } else if (type === 'person') {
          if (value && value instanceof can.Map) {
            value = value.serialize();
          }
          value = _.isEmpty(value) ? undefined : value;
        }

        if (type === 'dropdown') {
          if (_.isNull(value) || _.isUndefined(value)) {
            value = '';
          }
        }

        if (!scope.attr('emptyText')) {
          scope.attr('emptyText', 'None');  // default for custom attributes
        }
      }

      if (property) {
        value = instance.attr(property);
      }
      scope.attr('_value', value);
      scope.attr('context.value', value);

      if (values && _.isString(values)) {
        values = values.split(',');
      }
      scope.attr('context.values', values);
    },
    events: {
      '{window} mousedown': function (el, ev) {
        var isInside = this.element.has(ev.target).length ||
                   this.element.is(ev.target);

        if (!isInside &&
            this.scope.attr('context.isEdit')) {
          _.defer(function () {
            this.scope.onCancel(this.scope, this.element, ev);
          }.bind(this));
        }
      }
    }
  });
})(window.can, window.can.$);
