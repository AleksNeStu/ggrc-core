/*!
    Copyright (C) 2017 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

(function (can, GGRC, CMS) {
  /* function sortCustomAttributables
   *
   * Groups custom attributes by category.
   *
   */
  function sortCustomAttributables(a, b) {
    if (a.category < b.category) {
      return 1;
    } else if (a.category > b.category) {
      return -1;
    }
    return 0;
  }

  /* class CustomAttributable
   *
   * CustomAttributable does not query the backend, it is used to display a
   * list of objects in the custom attributes widget. It inherits from
   * cacheable because it needs getBinding to properly display
   * CustomAttributeDefinitions as children
   *
   */
  can.Model.Cacheable('CMS.Models.CustomAttributable', {
    findAll: function () {
      var types;
      types = GGRC.custom_attributable_types.sort(sortCustomAttributables);
      return can.when(can.map(types, function (type, i) {
        return new CMS.Models.CustomAttributable(can.extend(type, {
          id: i
        }));
      }));
    }
  }, {
    // Cacheable checks if selfLink is set when the findAll deferred is done
    selfLink: '/custom_attribute_list'
  });

  can.Model.Cacheable('CMS.Models.CustomAttributeDefinition', {
    // static properties
    root_object: 'custom_attribute_definition',
    root_collection: 'custom_attribute_definitions',
    category: 'custom_attribute_definitions',
    findAll: 'GET /api/custom_attribute_definitions',
    findOne: 'GET /api/custom_attribute_definitions/{id}',
    create: 'POST /api/custom_attribute_definitions',
    update: 'PUT /api/custom_attribute_definitions/{id}',
    destroy: 'DELETE /api/custom_attribute_definitions/{id}',
    mixins: [],
    attributes: {
      values: 'CMS.Models.CustomAttributeValue.stubs',
      modified_by: 'CMS.Models.Person.stub'
    },
    links_to: {},
    defaults: {
      title: '',
      attribute_type: 'Text'
    },
    attributeTypes: ['Text', 'Rich Text', 'Date', 'Checkbox', 'Dropdown'],

    _customValidators: {
      /**
       * Validate a comma-separated list of possible values defined by the
       * custom attribute definition.
       *
       * This validation is only applicable to multi-choice CA types such as
       * Dropdown, and does not do anything for other CA types.
       *
       * There must be at most one empty value defined (whitespace trimmed),
       * and the values must be unique.
       *
       * @param {*} newVal - the new value of the property
       * @param {String} propName - the instance property to validate
       *
       * @return {String} - A validation error message, if any. An empty string
       *   is returned if the validation passes.
       */
      multiChoiceOptions: function (newVal, propName) {
        var choices;
        var nonBlanks;
        var uniques;

        if (propName !== 'multi_choice_options') {
          return '';  // nothing  to validate here
        }

        if (this.attribute_type !== 'Dropdown') {
          return '';  // all ok, the value of multi_choice_options not needed
        }

        choices = _.splitTrim(newVal, ',');

        if (!choices.length) {
          return 'At least one possible value required.';
        }

        nonBlanks = _.compact(choices);
        if (nonBlanks.length < choices.length) {
          return 'Blank values not allowed.';
        }

        uniques = _.unique(nonBlanks);
        if (uniques.length < nonBlanks.length) {
          return 'Duplicate values found.';
        }

        return '';  // no errors
      }
    },

    init: function () {
      this.validateNonBlank('title');

      // Besides multi_choice_options we need toset the validation on the
      // attribute_type field as well, even though its validation always
      // succeeds. For some reson this is required for the modal UI buttons to
      // properly update themselves when choosing a different attribute type.
      this.validate(
        ['multi_choice_options', 'attribute_type'],
        this._customValidators.multiChoiceOptions
      );

      this._super.apply(this, arguments);
    }
  }, {
    init: function () {
      this._super.apply(this, arguments);
    }
  });

  can.Model.Cacheable('CMS.Models.CustomAttributeValue', {
    // static properties
    root_object: 'custom_attribute_value',
    root_collection: 'custom_attribute_values',
    category: 'custom_attribute_values',
    findAll: 'GET /api/custom_attribute_values',
    findOne: 'GET /api/custom_attribute_values/{id}',
    create: 'POST /api/custom_attribute_values',
    update: 'PUT /api/custom_attribute_values/{id}',
    destroy: 'DELETE /api/custom_attribute_values/{id}',
    mixins: [],
    attributes: {
      definition: 'CMS.Models.CustomAttributeDefinition.stub',
      modified_by: 'CMS.Models.Person.stub'
    },
    links_to: {},
    init: function () {
      this._super.apply(this, arguments);
    }
  }, {
    init: function () {
      this._super.apply(this, arguments);
    }
  });
})(window.can, window.GGRC, window.CMS);
