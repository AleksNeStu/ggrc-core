/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (GGRC, can, _) {
  'use strict';

  var customAttributesType = {
    Text: 'input',
    'Rich Text': 'text',
    'Map:Person': 'person',
    Date: 'date',
    Input: 'input',
    Checkbox: 'checkbox',
    Dropdown: 'dropdown'
  };
  /**
   * Util methods for custom attributes.
   */
  GGRC.Utils.CustomAttributes = (function () {
    /**
     * Return normalized Custom Attribute Type from Custom Attribute Definition
     * @param {String} type - String Custom Attribute Value from JSON
     * @return {String} - Normalized Custom Attribute Type
     */
    function getCustomAttributeType(type) {
      return customAttributesType[type] || 'input';
    }

    function isEmptyCustomAttribute(value, type, cav) {
      var result = false;
      var types = ['Text', 'Rich Text', 'Date', 'Checkbox', 'Dropdown',
        'Map:Person'];
      var options = {
        Checkbox: function (value) {
          return !value || value === '0';
        },
        'Rich Text': function (value) {
          value = GGRC.Utils.getPlainText(value);
          return _.isEmpty(value);
        },
        'Map:Person': function (value, cav) {
          // Special case, Map:Person has 'Person' value by default
          if (cav) {
            return !cav.attribute_object;
          }
          return _.isEmpty(value);
        }
      };
      if (value === undefined) {
        return true;
      }
      if (types.indexOf(type) > -1 && options[type]) {
        result = options[type](value, cav);
      } else if (types.indexOf(type) > -1) {
        result = _.isEmpty(value);
      }
      return result;
    }

    /**
     * Converts custom attribute value for UI controls.
     * @param {String} type - Custom attribute type
     * @param {Object} value - Custom attribute value
     * @param {Object} valueObj - Custom attribute object
     * @return {Object} Converted value
     */
    function convertFromCaValue(type, value, valueObj) {
      if (type === 'checkbox') {
        return value === '1';
      }

      if (type === 'input') {
        if (!value) {
          return null;
        }
        return value.trim();
      }

      if (type === 'person') {
        if (valueObj) {
          return valueObj;
        }
        return null;
      }

      if (type === 'dropdown') {
        if (value === null || value === undefined) {
          return '';
        }
      }
      return value;
    }

    /**
     * Custom Attributes specific parsing logic to simplify business logic of Custom Attributes
     * @param {Array} definitions - original list of Custom Attributes Definition
     * @param {Array} values - original list of Custom Attributes Values
     * @return {Array} Updated Custom attributes
     */
    function prepareCustomAttributes(definitions, values) {
      return definitions.map(function (def) {
        var valueData = false;
        var id = def.id;
        var options = (def.multi_choice_options || '').split(',');
        var optionsRequirements = (def.multi_choice_mandatory || '').split(',');
        var type = getCustomAttributeType(def.attribute_type);
        var stub = {
          id: null,
          custom_attribute_id: id,
          attribute_value: null,
          attribute_object: null,
          validation: {
            empty: true,
            mandatory: def.mandatory,
            valid: true
          },
          def: def,
          attributeType: type,
          preconditions_failed: [],
          errorsMap: {
            comment: false,
            evidence: false
          }
        };

        values.forEach(function (value) {
          var errors = [];
          if (value.custom_attribute_id === id) {
            errors = value.preconditions_failed || [];
            value.def = def;
            value.attributeType = type;
            value.validation = {
              empty: errors.indexOf('value') > -1,
              mandatory: def.mandatory,
              valid: errors.indexOf('comment') < 0 &&
              errors.indexOf('evidence') < 0
            };
            value.errorsMap = {
              comment: errors.indexOf('comment') > -1,
              evidence: errors.indexOf('evidence') > -1
            };
            valueData = value;
          }
        });

        valueData = valueData || stub;

        if (type === 'dropdown') {
          valueData.validationConfig = {};
          options.forEach(function (item, index) {
            valueData.validationConfig[item] =
              Number(optionsRequirements[index]);
          });
        }
        return valueData;
      });
    }

    /**
     * Converts value from UI controls back to CA value.
     * @param {String} type - Custom attribute type
     * @param {Object} value - Control value
     * @return {Object} Converted value
     */
    function convertToCaValue(type, value) {
      if (type === 'checkbox') {
        return value ? 1 : 0;
      }

      if (type === 'person') {
        if (value && value instanceof can.Map) {
          value = value.serialize();
          return 'Person:' + value.id;
        }
        return 'Person:None';
      }
      return value || null;
    }

    /**
     * Converts CA values array to form fields.
     * @param {can.List|undefined} customAttributeValues - Custom attributes values
     * @return {Array} From fields array
     */
    function convertValuesToFormFields(customAttributeValues) {
      return (customAttributeValues || new can.List([]))
        .map(convertToEditableField);
    }

    function convertToFormViewField(attr) {
      var options = attr.def.multi_choice_options;
      return {
        type: attr.attributeType,
        id: attr.def.id,
        value: convertFromCaValue(
          attr.attributeType,
          attr.attribute_value,
          attr.attribute_object
        ),
        title: attr.def.title,
        placeholder: attr.def.placeholder,
        options: options &&
        typeof options === 'string' ?
          options.split(',') : [],
        helptext: attr.def.helptext
      };
    }

    function convertToEditableField(attr) {
      var options = attr.def.multi_choice_options;
      return {
        type: attr.attributeType,
        id: attr.def.id,
        value: convertFromCaValue(
          attr.attributeType,
          attr.attribute_value,
          attr.attribute_object
        ),
        title: attr.def.title,
        placeholder: attr.def.placeholder,
        options: options &&
        typeof options === 'string' ?
          options.split(',') : [],
        helptext: attr.def.helptext,
        validation: attr.validation.attr(),
        validationConfig: attr.validationConfig,
        errorsMap: attr.errorsMap.attr(),
        valueId: can.compute(function () {
          return attr.attr('id');
        })
      };
    }

    function prepareLocalAttribute(attr) {
      var options;
      var value;
      var validation;
      var validationConfig;
      var type;
      var isValid;
      var isDropdown;
      var showValidation;
      var validationMap;
      var hasMissingInfo;

      if (!attr || !attr.values) {
        console.warn('Attribute is mandatory argument');
        return {};
      }

      options = can.Map.keys(attr.options || {});
      type = getCustomAttributeType(attr.attribute_type);
      value = new can.Map(attr.values[0] || {});
      validationMap = new can.Map(value.attr('preconditions_failed') || {});
      isDropdown = type === 'dropdown';
      showValidation = attr.mandatory || isDropdown;
      isValid = showValidation ? !attr.attr('is_preconditions_failed') : true;

      if (isDropdown) {
        validationConfig = attr.options || {};
        hasMissingInfo = validationMap.attr('comment') ||
          validationMap.attr('evidence');
      }
      validation = {
        show: showValidation,
        valid: isValid,
        hasMissingInfo: hasMissingInfo
      };
      return {
        type: type,
        id: attr.id,
        value: value.attr('value'),
        title: attr.title,
        placeholder: attr.placeholder,
        options: options,
        helptext: attr.helptext,
        required: attr.mandatory,
        isDropdown: isDropdown,
        validation: validation,
        validationConfig: validationConfig,
        errorsMap: {
          value: false,
          comment: false,
          evidence: false
        },
        valueId: can.compute(function () {
          return value.attr('id');
        })
      };
    }

    function prepareGlobalAttribute(attr) {
      var options;
      var value;
      var type;

      if (!attr || !attr.values) {
        console.warn('Attribute is mandatory argument');
        return {};
      }

      options = can.Map.keys(attr.options || {});
      type = getCustomAttributeType(attr.attribute_type);
      value = new can.Map(attr.values[0] || {});

      return {
        type: type,
        id: attr.id,
        value: value.value,
        title: attr.title,
        placeholder: attr.placeholder,
        options: options,
        helptext: attr.helptext
      };
    }

    /**
     * Simple function to update Custom Attributes
     * Temporary as Custom Attributes doesn't support multiple values value parameter is single object
     * @param {can.Map} attr - attribute to update
     * @param {Object} value - updated value object
     */
    function updateAttribute(attr, value) {
      if (!attr || !attr.values) {
        console.warn('Attribute is mandatory argument');
        return;
      }
      // Start Temporary: Till Custom Attributes support only single Value we transform passed "value" object to Array
      value = can.makeArray(value);
      // End of Temporary
      attr.values.replace(value);
    }

    return {
      convertFromCaValue: convertFromCaValue,
      convertToCaValue: convertToCaValue,
      convertValuesToFormFields: convertValuesToFormFields,
      prepareCustomAttributes: prepareCustomAttributes,
      isEmptyCustomAttribute: isEmptyCustomAttribute,
      getCustomAttributeType: getCustomAttributeType,
      convertToFormViewField: convertToFormViewField,
      prepareLocalAttribute: prepareLocalAttribute,
      prepareGlobalAttribute: prepareGlobalAttribute,
      updateAttribute: updateAttribute
    };
  })();
})(window.GGRC, window.can, window._);
