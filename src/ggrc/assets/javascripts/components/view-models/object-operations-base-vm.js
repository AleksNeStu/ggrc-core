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
      },
      type: {
      /*
       * When object type is changed it should be needed to change a config.
       * For example, if not set a special config for type [TYPE] then is used
       * general config, otherwise special config.
       */
        set: function (mapType) {
          var config = this.attr('config') || {};
          var type = this.attr('type');
          var resultConfig;
          var configHandler;
          var special = _.result(
            _.find(
              config.attr('special'),
              function (special) {
                return _.contains(special.types, mapType);
              }),
            'config'
          );

          resultConfig = !_.isEmpty(special) ? special : config.attr('general');

          // We remove type because update action can make recursion (when we set
          // type)
          resultConfig.removeAttr('type');

          // if we set type first time then update config immediately
          if (!type) {
            configHandler = this.update.bind(this);
          } else {
            configHandler = this.prepareConfig.bind(this);
          }

          configHandler(resultConfig.serialize());

          return mapType;
        }
      }
    },
    /**
     *  @typedef SpecialConfig
     *  @type {Object}
     *  @property {String[]} types - An array contains typenames for which is set a
     *                               special config.
     *  @property {Object} config - Has fields with special values for viewModel.
     */

    /**
     * Config is an object with general and special settings.
     *
     * @namespace
     * @property {Object} general - Has fields with general values for viewModel.
     * @property {SpecialConfig[]} special - Has array of special configs.
     */
    config: {
      general: {},
      special: []
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
    },
    prepareConfig: function (config) {
      this.update(config);
    },
    /**
     * Updates view model fields to values from config.
     *
     * @param {Object} config - Plain object with values for updating
     */
    update: function (config) {
      can.batch.start();

      // do not update fields with the same values in VM and config
      _.each(config, function (value, key) {
        var vmValue = this.attr(key);
        var hasSerialize = Boolean(vmValue && vmValue.serialize);

        if (hasSerialize) {
          vmValue = vmValue.serialize();
        }

        if (!_.isEqual(vmValue, value)) {
          this.attr(key, value);
        }
      }.bind(this));

      can.batch.stop();
    }
  });
})(window.can, window.can.$);
