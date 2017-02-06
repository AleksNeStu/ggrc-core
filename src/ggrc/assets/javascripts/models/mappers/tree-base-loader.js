/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (GGRC, can) {
  'use strict';

  GGRC.ListLoaders.BaseListLoader('GGRC.ListLoaders.TreeBaseLoader', {}, {
    init: function (model, instance, mapping) {
      mapping = mapping || 'related_objects';
      this.model = model;
      this.binding = instance.get_binding(mapping);
    },
    insertInstancesFromMappings: function (mappings) {
      var self = this;
      var result;

      result = can.map(can.makeArray(mappings), function (mapping) {
        return self.getResultFromMapping(mapping);
      });
      return $.when.apply($, result).then(function () {
        return new can.List(Array.prototype.slice.call(arguments));
      });
    },
    getResultFromMapping: function (mapping) {
      var binding = this.binding;
      return this.makeResult(mapping.reify(), binding);
    },
    makeResult: function (instance, binding) {
      var result;
      if (instance instanceof CMS.Models.Person) {
        if (binding.instance.workflow_people) {
          result = CMS.Models.Person
            .getPersonMappings(binding.instance, instance, 'workflow_people');
        } else if (binding.instance.object_people.length) {
          result = CMS.Models.Person
            .getPersonMappings(binding.instance, instance, 'object_people');
        } else {
          result = CMS.Models.Person
            .getUserRoles(binding.instance, instance);
        }
      } else {
        result = CMS.Models.Relationship
          .getRelationshipBetweenInstances(binding.instance, instance, true);
      }
      return result
        .then(function (relationships) {
          return new GGRC.ListLoaders.MappingResult(
            instance, can.map(relationships, function (relationship) {
              return {
                binding: binding,
                instance: relationship,
                mappings: [{
                  instance: true,
                  mappings: [],
                  binding: binding
                }]
              };
            }), binding);
        });
    }
  });
})(GGRC, can);
