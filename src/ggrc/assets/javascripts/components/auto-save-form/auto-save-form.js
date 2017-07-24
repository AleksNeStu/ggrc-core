/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */
(function (can, GGRC, $) {
  'use strict';

  var AUTO_SAVE_DELAY = 1000;

  GGRC.Components('autoSaveForm', {
    tag: 'auto-save-form',
    template: can.view(
      GGRC.mustache_path +
      '/components/auto-save-form/auto-save-form.mustache'
    ),
    viewModel: {
      define: {
        fieldsToSave: {
          Value: can.Map
        },
        isDirty: {
          type: 'boolean',
          get: function () {
            return can.Map.keys(this.attr('fieldsToSave') || {}).length;
          }
        },
        hasValidationErrors: {
          type: 'boolean',
          get: function () {
            return this.attr('fields')
              .filter(function (field) {
                var isEmpty = field.attr('validation.mandatory') &&
                  field.attr('validation.empty');
                var isNotValid = !field.attr('validation.valid');
                return isEmpty || isNotValid;
              }).length;
          }
        },
        evidenceAmount: {
          type: 'number',
          set: function (newValue, setValue) {
            setValue(newValue);
            this.updateEvidenceValidation();
          }
        },
        isEvidenceRequired: {
          get: function () {
            return this.hasMissingEvidence();
          }
        }
      },
      formSavedDeferred: can.Deferred().resolve(),
      editMode: false,
      saving: false,
      allSaved: true,
      fieldsToSaveAvailable: false,
      autoSaveScheduled: false,
      autoSaveAfterSave: false,
      autoSaveTimeoutHandler: null,
      fields: [],
      saveCallback: null,
      triggerSaveCbs: null,
      init: function () {
        this._save = this.save.bind(this);
        this.attr('triggerSaveCbs').add(this._save);
      },
      unsubscribe: function () {
        this.attr('triggerSaveCbs').remove(this._save);
      },
      updateEvidenceValidation: function () {
        var isEvidenceRequired = this.attr('isEvidenceRequired');
        this.attr('fields')
          .filter(function (item) {
            return item.attr('type') === 'dropdown';
          })
          .each(function (item) {
            var isCommentRequired;
            if ((item.attr('validationConfig')[item.attr('value')] === 2 ||
                item.attr('validationConfig')[item.attr('value')] === 3)) {
              isCommentRequired = item.attr('errorsMap.comment');
              item.attr('errorsMap.evidence', isEvidenceRequired);
              item.attr('validation.valid',
                !isEvidenceRequired && !isCommentRequired);
            }
          });
      },
      hasMissingEvidence: function () {
        var optionsWithEvidence = this.attr('fields')
              .filter(function (item) {
                return item.attr('type') === 'dropdown' &&
                  (item.attr('validationConfig')[item.attr('value')] === 2 ||
                item.attr('validationConfig')[item.attr('value')] === 3);
              }).length;
        return optionsWithEvidence > this.attr('evidenceAmount');
      },
      performValidation: function (field, value) {
        var isEvidenceRequired = this.attr('isEvidenceRequired');
        this.updateEvidenceValidation();
        field.attr('validation.empty', !(value));
        if (field.attr('type') === 'dropdown') {
          if (!field.attr('validationConfig')[value]) {
            field.attr('errorsMap.evidence', false);
            field.attr('errorsMap.comment', false);
            field.attr('validation.valid', true);
          }
          if (field.attr('validationConfig')[value] === 0) {
            field.attr('errorsMap.evidence', false);
            field.attr('errorsMap.comment', false);
            field.attr('validation.valid', true);
          }
          if (field.attr('validationConfig')[value] === 2) {
            field.attr('errorsMap.evidence', isEvidenceRequired);
            field.attr('errorsMap.comment', false);
            field.attr('validation.valid', !isEvidenceRequired);
            if (isEvidenceRequired) {
              this.dispatch({
                type: 'validationChanged',
                field: field
              });
            }
          }
          if (field.attr('validationConfig')[value] === 1) {
            field.attr('errorsMap.evidence', false);
            field.attr('errorsMap.comment', true);
            field.attr('validation.valid', false);
            this.dispatch({
              type: 'validationChanged',
              field: field
            });
          }
          if (field.attr('validationConfig')[value] === 3) {
            field.attr('errorsMap.evidence', isEvidenceRequired);
            field.attr('errorsMap.comment', true);
            field.attr('validation.valid', false);
            this.dispatch({
              type: 'validationChanged',
              field: field
            });
          }
        }
      },
      fieldValueChanged: function (e, field) {
        field.attr('value', e.value);
        this.fieldsToSave.attr(e.fieldId, e.value);
        this.attr('fieldsToSaveAvailable', true);
        this.performValidation(field, e.value);
        this.attr('formSavedDeferred', can.Deferred());
        this.triggerAutoSave();
      },
      save: function () {
        var self = this;
        var toSave = {};

        this.attr('fieldsToSave').each(function (v, k) {
          toSave[k] = v;
        });

        this.attr('fieldsToSave', {}, true);
        this.attr('fieldsToSaveAvailable', false);

        clearTimeout(this.attr('autoSaveTimeoutHandler'));
        this.attr('autoSaveScheduled', false);

        this.attr('saving', true);
        this.saveCallback(new can.Map(toSave))
          .done(function () {
            if (self.attr('autoSaveAfterSave')) {
              self.attr('autoSaveAfterSave', false);
              setTimeout(self.save.bind(self));
            }

            self.attr('allSaved', true);
            self.attr('formSavedDeferred').resolve();
          })
          // todo: error handling
          .always(function () {
            self.attr('saving', false);
          });
      },
      triggerAutoSave: function () {
        if (this.attr('autoSaveScheduled')) {
          return;
        }
        if (this.attr('saving')) {
          this.attr('autoSaveAfterSave', true);
          return;
        }

        this.attr('allSaved', false);

        this.attr(
          'autoSaveTimeoutHandler',
          setTimeout(this.save.bind(this), AUTO_SAVE_DELAY)
        );
        this.attr('autoSaveScheduled', true);
      }
    },
    events: {
      removed: function () {
        this.viewModel.unsubscribe();
      }
    }
  });
})(window.can, window.GGRC, window.jQuery);
