/*!
 Copyright (C) 2017 Google Inc., authors, and contributors
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, GGRC) {
  'use strict';
  var tag = 'form-required-check';
  /**
   * Form Required Information Verification Component
   */
  GGRC.Components('formRequiredCheck', {
    tag: tag,
    viewModel: {
      define: {
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
      fields: [],
      updateEvidenceValidation: function () {
        var isEvidenceRequired = this.attr('isEvidenceRequired');
        this.attr('fields')
          .filter(function (item) {
            return item.attr('isDropdown');
          })
          .each(function (item) {
            var isCommentRequired;
            if (this.requireEvidence(item, item.attr('value'))) {
              isCommentRequired = item.attr('errorsMap.comment');
              item.attr('errorsMap.evidence', isEvidenceRequired);
              item.attr('validation.valid',
                !isEvidenceRequired && !isCommentRequired);
            }
          }.bind(this));
      },
      hasMissingEvidence: function () {
        var optionsWithEvidence = this.attr('fields')
          .filter(function (item) {
            return this.requireEvidence(item, item.attr('value'));
          }.bind(this)).length;
        return optionsWithEvidence > this.attr('evidenceAmount');
      },
      getPreconditions: function (field, value) {
        return field.attr('validationConfig')[value] || {};
      },
      requireEvidence: function (field, value) {
        return field.attr('isDropdown') &&
          this.getPreconditions(field, value).evidence_required;
      },
      requireComment: function (field, value) {
        return field.attr('isDropdown') &&
          this.getPreconditions(field, value).comment_required;
      },
      performValidation: function (event) {
        var field = event.field;
        var value = event.value;
        var hasMissingEvidence;
        var hasMissingComment;
        var isEvidenceRequired = this.attr('isEvidenceRequired');
        this.updateEvidenceValidation();
        field.attr('validation.valid', !!(value));
        if (field.attr('isDropdown')) {
          hasMissingEvidence =
            isEvidenceRequired && this.requireEvidence(field, value);
          hasMissingComment = this.requireComment(field, value);
          field.attr('errorsMap.evidence', hasMissingEvidence);
          field.attr('errorsMap.comment', hasMissingComment);
          field.attr('validation.valid',
            !!(value) && !(hasMissingEvidence || hasMissingComment));
          field.attr('validation.hasMissingInfo',
            hasMissingEvidence || hasMissingComment);
          if (hasMissingEvidence || hasMissingComment) {
            this.dispatch({
              type: 'validationChanged',
              field: field
            });
          }
        }
      }
    }
  });
})(window.can, window.GGRC);
