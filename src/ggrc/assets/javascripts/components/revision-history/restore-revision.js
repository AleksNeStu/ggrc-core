/*
 Copyright (C) 2017 Google Inc., authors, and contributors
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

import {
  buildModifiedACL,
  buildModifiedListField,
  buildModifiedAttValues,
} from '../../plugins/utils/object-history-utils';

import template from './templates/restore-revision.mustache';
const tag = 'restore-revision';

export default can.Component.extend({
  tag,
  template,
  viewModel: {
    instance: {},
    restoredRevision: {},
    loading: false,
    restore(element) {
      const instance = this.attr('instance');
      const diff = this.attr('restoredRevision.diff_with_current');
      let attrValues;

      if (!diff || !instance) {
        return;
      }

      this.attr('loading', true);
      attrValues = diff.attr('custom_attribute_values');

      this.applyFields(instance, diff.attr('fields'));
      this.applyFields(instance, diff.attr('mapping_fields'));
      this.applyAcl(instance, diff.attr('access_control_list'));
      this.applyListFields(instance, diff.attr('mapping_list_fields'));

      // use legacy approach to save custom attribute
      this.applyCustomAttributes(instance, attrValues, true);

      this.saveInstance(instance, element);
    },
    saveInstance(instance, element) {
      instance.save().then(() => {
        this.attr('loading', false);
        this.closeDiff(element);
      });
    },
    applyFields(instance, modifiedFields) {
      const fieldNames = can.Map.keys(modifiedFields);

      fieldNames.forEach((fieldName) => {
        const modifiedField = modifiedFields[fieldName];
        instance.attr(fieldName, modifiedField);
      });
    },
    applyAcl(instance, modifiedRoles) {
      const modifiedACL = buildModifiedACL(instance, modifiedRoles);
      instance.attr('access_control_list', modifiedACL);
    },
    applyListFields(instance, modifiedFields) {
      const fieldNames = can.Map.keys(modifiedFields);
      fieldNames.forEach((fieldName) => {
        const items = instance.attr(fieldName);
        const modifiedItems = modifiedFields.attr(fieldName);
        const modifiedField = buildModifiedListField(items, modifiedItems);
        instance.attr(fieldName, modifiedField);
      });
    },
    applyCustomAttributes(instance, modifiedAttributes, useLegacy) {
      const values = instance
        .attr('custom_attribute_values')
        .map((value) => value.reify())
        .attr();

      const definitions = instance
        .attr('custom_attribute_definitions')
        .attr();

      const modifiedValues =
        buildModifiedAttValues(values, definitions, modifiedAttributes);

      if (useLegacy) {
        instance.attr('custom_attributes',
          this.convertToLegacyAttributes(modifiedValues, definitions));
      } else {
        instance.attr('custom_attribute_values', modifiedValues);
      }
    },
    convertToLegacyAttributes(values, definitions) {
      const customAttributes = {};

      values.forEach((value) => {
        const def = definitions
          .find((def) => value.custom_attribute_id === def.id);
        let caValue;

        if (def.attribute_type === 'Map:Person') {
          caValue = `Person:${value.attribute_object.id}`;
        } else if (def.attribute_type === 'Checkbox') {
          caValue = value.attribute_value === '1' ? true : false;
        } else {
          caValue = value.attribute_value;
        }

        customAttributes[value.custom_attribute_id] = caValue;
      });

      return customAttributes;
    },
    closeDiff(element) {
      // TODO: fix
      $(element).closest('.modal').find('.modal-dismiss').trigger('click');
    },
  },
});
