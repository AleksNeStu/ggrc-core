/*!
 Copyright (C) 2017 Google Inc., authors, and contributors
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, GGRC) {
  'use strict';
  var tpl = can.view(GGRC.mustache_path +
    '/components/assessment/custom-attributes.mustache');

  can.Component.extend({
    tag: 'assessment-custom-attributes',
    template: tpl,
    viewModel: {
      instance: null,
      modal: {
        open: false
      },
      save: function (scope) {
        var items = this.attr('items');
        var itemToSave;
        var errors;
        var value = scope.attr('value');
        var type = scope.attr('type');
        var defId = scope.attr('def.id');
        var attributeObjectId;
        var valueParts;
        var customAttributeValue;
        if (type === 'person') {
          valueParts = value.split(':');
          attributeObjectId = Number(valueParts[1]);
          value = valueParts[0];
        }

        this.attr('instance').save()
          .done(function () {
            items.each(function (item) {
              if (defId === item.attr('def.id')) {
                itemToSave = item;
                return false;
              }
            });
            errors = itemToSave.attr('preconditions_failed') || [];
            if (!(errors.indexOf('comment') < 0 &&
              errors.indexOf('evidence') < 0)) {
              this.showRequiredModal(errors, {
                value: scope.attr('value'),
                title: scope.attr('def.title'),
                type: scope.attr('type')
              }, {
                defId: defId,
                valueId: itemToSave.id
              });
            }
            if (type === 'person') {
              customAttributeValue =
                can.makeArray(this.attr('instance.custom_attribute_values'))
                  .find(function (v) {
                    return v.id === itemToSave.id;
                  });
              if (customAttributeValue &&
                customAttributeValue.attribute_object &&
                customAttributeValue.attribute_object.id !==
                attributeObjectId) {
                return;
              }
            }
            if (String(value) !== scope.attr('value')) {
              return;
            }
            GGRC.Errors.notifier('success', 'Saved');
          }.bind(this))
          .fail(function (inst, err) {
            GGRC.Errors.notifierXHR('error')(err);
          })
          .always(function () {
            scope.attr('isSaving', false);
          });
      },
      showRequiredModal: function (fields, content, ids) {
        can.batch.start();
        this.attr('modal', {
          content: content,
          caIds: ids,
          modalTitleText: 'Required ' + fields.map(function (field) {
            return can.capitalize(field);
          }).join(' and '),
          fields: fields
        });
        can.batch.stop();
        this.attr('modal.open', true);
      }
    },
    events: {
      'ca-object saveCustomAttribute': function (el, ev, scope) {
        this.viewModel.save(scope);
      }
    }
  });
})(window.can, window.GGRC);
