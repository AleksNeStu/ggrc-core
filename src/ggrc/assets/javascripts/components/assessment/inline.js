/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (_, can, GGRC) {
  'use strict';

  var tpl = can.view(GGRC.mustache_path +
    '/components/assessment/inline/inline.mustache');
  var innerTplFolder = GGRC.mustache_path + '/components/assessment/inline';

  function getTemplateByType(type) {
    type = can.Mustache.resolve(type);
    return innerTplFolder + '/' + type + '.mustache';
  }

  GGRC.Components('assessmentInlineEdit', {
    tag: 'assessment-inline-edit',
    template: tpl,
    scope: {
      titleText: null,
      type: null,
      value: null,
      options: null,
      readonly: false, // whether or not the value can be edited
      isSaving: false,
      isEdit: false,
      context: {
        value: null,
        options: null
      },

      _EV_BEFORE_EDIT: 'before-edit',  // before entering the edit mode

      setPerson: function (scope, el, ev) {
        this.attr('context.value', ev.selectedItem.serialize());
      },
      unsetPerson: function (scope, el, ev) {
        ev.preventDefault();
        this.attr('context.value', undefined);
      },

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
          this.attr('isEdit', true);
          return;
        }

        confirmation = this.$rootEl.triggerHandler({
          type: this._EV_BEFORE_EDIT
        });

        confirmation.done(function () {
          this.attr('isEdit', true);
        }.bind(this));   // and do nothing if no confirmation by the user
      },
      onCancel: function (scope) {
        var value = scope.attr('_value');
        scope.attr('isEdit', false);
        scope.attr('context.value', value);
      },
      onSave: function () {
        var oldValue = this.attr('value');
        var value = this.attr('context.value');

        this.attr('isEdit', false);
        // In case value is String and consists only of spaces - do nothing
        if (typeof value === 'string' && !value.trim()) {
          this.attr('context.value', '');
          value = null;
        }

        if (oldValue === value) {
          return;
        } else if (this.attr('type') === 'person') {
          if (value && oldValue && oldValue.id === value.id) {
            // check instances of value and oldValue.
            // return if instances are exist and ids are equal.
            return;
          }
        }

        this.attr('_value', value);
        this.attr('value', value);
        this.attr('isSaving', true);
      }
    },
    init: function (element, options) {
      var scope = this.scope;
      var value = scope.attr('value');

      scope.attr('_value', value);
      scope.attr('context.value', value);

      scope.attr('$rootEl', $(element));
    },
    events: {
      '{window} mousedown': function (el, ev) {
        var scope = this.scope;
        var isInside = this.element.has(ev.target).length ||
          this.element.is(ev.target);

        if (!isInside && scope.attr('isEdit')) {
          _.defer(function () {
            scope.onCancel(scope);
          });
        }
      }
    },
    helpers: {
      renderInnerTemplateByType: function (type, options) {
        return can.view.render(getTemplateByType(type), options.context);
      }
    }
  });
})(window._, window.can, window.GGRC);
