/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, $) {
  'use strict';

  can.Map.extend('GGRC.VM.ObjectOperationsBaseVM', {
    define: {
      parentInstance: {
        get: function () {
          return CMS.Models
            .get_instance(this.attr('object'), this.attr('join_object_id'));
        }
      },
      model: {
        get: function () {
          return this.modelFromType(this.attr('type'));
        }
      }
    },
    showSearch: true,
    showResults: true,
    type: 'Control', // We set default as Control
    availableTypes: function () {
      var types = GGRC.Mappings.getMappingTypes(
        this.attr('object'),
        [],
        GGRC.Utils.Snapshots.inScopeModels);
      return types;
    },
    object: '',
    bindings: {},
    is_loading: false,
    is_saving: false,
    assessmentTemplate: '',
    join_object_id: '',
    selected: [],
    entries: [],
    options: [],
    newEntries: [],
    relevant: [],
    submitCbs: $.Callbacks(),
    useSnapshots: false,
    modelFromType: function (type) {
      var types = _.reduce(_.values(
        this.availableTypes()), function (memo, val) {
        if (val.items) {
          return memo.concat(val.items);
        }
        return memo;
      }, []);
      return _.findWhere(types, {value: type});
    },
    onSubmit: function () {
      this.attr('submitCbs').fire();
    }
  });
})(window.can, window.can.$);
