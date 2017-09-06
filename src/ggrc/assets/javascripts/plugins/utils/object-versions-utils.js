/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (GGRC) {
  'use strict';
  /**
   * Util methods for work with Object versions.
   */
  GGRC.Utils.ObjectVersions = (function () {
    var cachedObjects = {};
    var modelsIncludeVersions = [
      'Issue'
    ];

    /**
     * Check provided model name.
     * Returns true if model name contains '_version'
     * @param {String} modelName - model to check
     * @return {Boolean} True or False
     */
    function isObjectVersion(modelName) {
      return modelName && typeof modelName === 'string' ?
        modelName.indexOf('_version') > -1 :
        false;
    }

    /**
     * Check provided parent model name.
     * Returns true if parent model has object versions tabs
     * @param {String} modelName - model to check
     * @return {Boolean} True or False
     */
    function parentHasObjectVersions(parentModelName) {
      return modelsIncludeVersions.indexOf(parentModelName) > -1;
    }

    function _getObjectVersionConfig(modelName, forceBuildFromOriginal) {
      var originalModelName;
      var objectVersion = {};
      if (!forceBuildFromOriginal) {
        if (!isObjectVersion(modelName)) {
          return objectVersion;
        }
        originalModelName = modelName.split('_')[0];

        return {
          originalModelName: originalModelName,
          widgetId: modelName,
          widgetName: CMS.Models[originalModelName].title_plural +
            ' Versions'
        };
      }

      return {
        originalModelName: modelName,
        widgetId: modelName + '_versions',
        widgetName: CMS.Models[modelName].title_plural +
          ' Versions'
      };
    }

    function getWidgetConfig(modelName, buildVersionFromOriginal) {
      var config;
      var isObjectVersion;
      var originalModelName;
      var additionalFilter;
      var responseType;
      var configObject;

      // Workflow approach
      if (_.isObject(modelName)) {
        modelName.responseType = modelName.name;
        modelName.widgetName = modelName.name;
        modelName.widgetId = modelName.name;
        return modelName;
      }

      if (cachedObjects[modelName]) {
        return cachedObjects[modelName];
      }

      config = _getObjectVersionConfig(modelName, buildVersionFromOriginal);
      isObjectVersion = !!config.originalModelName;
      originalModelName = config.originalModelName || modelName;
      additionalFilter = isObjectVersion ?
        'child_type = ' + originalModelName :
        '';
      responseType = isObjectVersion ?
        'Snapshot' :
        modelName;

      configObject = {
        name: originalModelName,
        widgetId: config.widgetId || modelName,
        widgetName: config.widgetName || modelName,
        countsName: modelName,
        responseType: responseType,
        additionalFilter: additionalFilter,
        isObjectVersion: isObjectVersion
      };

      cachedObjects.modelName = configObject;
      return configObject;
    }

    function getWidgetConfigs(modelNames) {
      var configs = modelNames.map(function (modelName) {
        return getWidgetConfig(modelName);
      });
      return configs;
    }

    return {
      isObjectVersion: isObjectVersion,
      parentHasObjectVersions: parentHasObjectVersions,
      getWidgetConfig: getWidgetConfig,
      getWidgetConfigs: getWidgetConfigs
    };
  })();
})(window.GGRC);
