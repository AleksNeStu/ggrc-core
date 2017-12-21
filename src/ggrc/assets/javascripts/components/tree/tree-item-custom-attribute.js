/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

import template from './templates/tree-item-custom-attribute.mustache';

var viewModel = can.Map.extend({
  instance: null,
  values: [],
  column: {},
});

var helpers = {
  /*
    Used to get the string value for custom attributes
  */
  get_custom_attr_value: function (attr, instance, options) {
    var value = '';
    var definition;
    var customAttrItem;
    var formatValueMap = {
      Checkbox: function (item) {
        return ['No', 'Yes'][item.attr('attribute_value')];
      },
      Date: function (item) {
        return GGRC.Utils.formatDate(item.attr('attribute_value'), true);
      },
    };

    attr = Mustache.resolve(attr);
    instance = Mustache.resolve(instance);

    definition = _.find(GGRC.custom_attr_defs, function (item) {
      return item.definition_type === instance.class.table_singular &&
        item.title === attr.attr_name;
    });

    if (definition) {
      // reify all CA models (with the exception of the Assessment)
      // to load custom_attribute_id, attribute_value and attribute_object
      if (!(instance instanceof CMS.Models.Assessment)) {
        _prepareCAVs();
      }

      customAttrItem = _.find(instance.attr('custom_attribute_values'),
        function (cav) {
          return cav.custom_attribute_id === definition.id;
        });

      if (customAttrItem) {
        if (formatValueMap[definition.attribute_type]) {
          value =
            formatValueMap[definition.attribute_type](customAttrItem);
        } else {
          value = customAttrItem.attr('attribute_value');
        }
      }
    }

    function _prepareCAVs() {
      _.forEach(instance.attr('custom_attribute_values'),
        function (cav, index) {
          instance.custom_attribute_values.attr(index, cav.reify());
        });
    }

    return value || '';
  },
};

GGRC.Components('treeItemCustomAttribute', {
  tag: 'tree-item-custom-attribute',
  template: template,
  viewModel: viewModel,
  helpers: helpers,
});

export default helpers;
