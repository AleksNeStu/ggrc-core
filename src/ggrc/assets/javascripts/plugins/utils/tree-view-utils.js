/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (GGRC) {
  'use strict';

  /**
   * TreeView-specific utils.
   */
  GGRC.Utils.TreeView = (function () {

    var baseWidgets = GGRC.tree_view.attr('base_widgets_by_type');
    var defaultOrderTypes = GGRC.tree_view.attr('defaultOrderTypes');
    var allTypes = Object.keys(baseWidgets.serialize());
    var orderedModelsForSubTier = {};

    var QueryAPI = GGRC.Utils.QueryAPI;
    var CurrentPage = GGRC.Utils.CurrentPage;
    var SnapshotUtils = GGRC.Utils.Snapshots;

    var SUB_TREE_ELEMENTS_LIMIT = 20;
    var SUB_TREE_FIELDS = Object.freeze([
      'child_id',
      'child_type',
      'context',
      'email',
      'id',
      'is_latest_revision',
      'name',
      'revision',
      'revisions',
      'selfLink',
      'slug',
      'status',
      'title',
      'type',
      'viewLink',
      'workflow_state'
    ]);

    var FULL_SUB_LEVEL_LIST = Object.freeze(['Cycle', 'CycleTaskGroup']);

    allTypes.forEach(function (type) {
      var related = baseWidgets[type].slice(0);

      orderedModelsForSubTier[type] = _.chain(related)
        .map(function (type) {
          return {
            name: type,
            order: defaultOrderTypes[type]
          };
        })
        .sortByAll(['order', 'name'])
        .map('name')
        .value();
    });

    // Define specific rules for Workflow models
    orderedModelsForSubTier.Cycle = ['CycleTaskGroup'];
    orderedModelsForSubTier.CycleTaskGroup = ['CycleTaskGroupObjectTask'];

    /**
     * Get available and selected columns for Model type
     * @param {String} modelType - Model type.
     * @param {Object} displayPrefs - Display preferences.
     * @return {Object} Table columns configuration.
     */
    function getColumnsForModel(modelType, displayPrefs) {
      var Cacheable = can.Model.Cacheable;
      var Model = CMS.Models[modelType];
      var modelDefinition = Model().class.root_object;
      var modelName = Model.model_singular;
      var mandatoryAttrNames =
        Model.tree_view_options.mandatory_attr_names ||
        Cacheable.tree_view_options.mandatory_attr_names;
      var savedAttrList = displayPrefs ?
        displayPrefs.getTreeViewHeaders(modelName) : [];
      var displayAttrNames =
        savedAttrList.length ? savedAttrList :
          (Model.tree_view_options.display_attr_names ||
          Cacheable.tree_view_options.display_attr_names);
      var disableConfiguration =
        !!Model.tree_view_options.disable_columns_configuration;
      var mandatoryColumns;
      var displayColumns;

      var attrs =
        can.makeArray(
          Model.tree_view_options.mapper_attr_list ||
          Model.tree_view_options.attr_list ||
          Cacheable.attr_list
        ).map(function (attr) {
          attr = _.assign({}, attr);
          if (!attr.attr_sort_field) {
            attr.attr_sort_field = attr.attr_name;
          }
          return attr;
        }).sort(function (a, b) {
          if (a.order && !b.order) {
            return -1;
          } else if (!a.order && b.order) {
            return 1;
          }
          return a.order - b.order;
        });

      var customAttrs = disableConfiguration ?
        [] :
        GGRC.custom_attr_defs
          .filter(function (def) {
            return def.definition_type === modelDefinition &&
              def.attribute_type !== 'Rich Text';
          }).map(function (def) {
            return {
              attr_title: def.title,
              attr_name: def.title,
              attr_sort_field: def.title,
              display_status: false,
              attr_type: 'custom'
            };
          });

      var allAttrs = attrs.concat(customAttrs);

      if (disableConfiguration) {
        return {
          available: allAttrs,
          selected: allAttrs,
          disableConfiguration: true
        };
      }

      displayAttrNames = displayAttrNames.concat(mandatoryAttrNames);

      allAttrs.forEach(function (attr) {
        attr.display_status = displayAttrNames.indexOf(attr.attr_name) !== -1;
        attr.mandatory = mandatoryAttrNames.indexOf(attr.attr_name) !== -1;
      });

      mandatoryColumns = allAttrs.filter(function (attr) {
        return attr.mandatory;
      });

      displayColumns = allAttrs.filter(function (attr) {
        return attr.display_status && !attr.mandatory;
      });

      return {
        available: allAttrs,
        selected: mandatoryColumns.concat(displayColumns),
        mandatory: mandatoryAttrNames,
        disableConfiguration: false
      };
    }

    /**
     * Set selected columns for Model type
     * @param {String} modelType - Model type.
     * @param {Array} columnNames - Array of column names.
     * @param {Object} displayPrefs - Display preferences.
     * @return {Object} Table columns configuration.
     */
    function setColumnsForModel(modelType, columnNames, displayPrefs) {
      var availableColumns =
        getColumnsForModel(modelType, displayPrefs).available;
      var selectedColumns = [];
      var selectedNames = [];

      availableColumns.forEach(function (attr) {
        if (columnNames.indexOf(attr.attr_name) !== -1) {
          attr.display_status = true;
          selectedColumns.push(attr);
          if (!attr.mandatory) {
            selectedNames.push(attr.attr_name);
          }
        } else {
          attr.display_status = false;
        }
      });

      if (displayPrefs) {
        displayPrefs.setTreeViewHeaders(
          CMS.Models[modelType].model_singular,
          selectedNames
        );
        displayPrefs.save();
      }

      return {
        available: availableColumns,
        selected: selectedColumns
      };
    }

    /**
     * Returns map where key is name of field
     * and value True if column selected and False or not.
     * @param {Array} available - Full list of available columns.
     * @param {Array} selected - List of selected columns.
     * @return Map with selected columns.
     */
    function createSelectedColumnsMap(available, selected) {
      var selectedColumns = can.makeArray(selected);
      var availableColumns = can.makeArray(available);
      var columns = new can.Map();

      availableColumns
        .forEach(function (attr) {
          var value = {};
          value[attr.attr_name] = selectedColumns
            .some(function (selectedAttr) {
              return selectedAttr.attr_name === attr.attr_name;
            });
          columns.attr(value);
        });

      return columns;
    }

    function displayTreeSubpath(el, path, attemptCounter) {
      var rest = path.split('/');
      var type = rest.shift();
      var id = rest.shift();
      var selector = '[data-object-type=\'' + type +
        '\'][data-object-id=' + id + ']';
      var $node;
      var nodeController;
      var controller;

      if (!attemptCounter) {
        attemptCounter = 0;
      }

      rest = rest.join('/');

      if (type || id) {
        $node = el.find(selector);

        // sometimes nodes haven't loaded yet, wait for them
        if (!$node.size() && attemptCounter < 5) {
          setTimeout(function () {
            displayTreeSubpath(el, path, attemptCounter + 1);
          }, 100);
          return undefined;
        }

        if (!rest.length) {
          controller = $node
            .closest('.cms_controllers_tree_view_node')
            .control();

          if (controller) {
            controller.select();
          }
        } else {
          nodeController = $node.control();
          if (nodeController && nodeController.display_path) {
            return nodeController.display_path(rest);
          }
        }
      }
      return can.Deferred().resolve();
    }

    function getModelsForSubTier(model) {
      return orderedModelsForSubTier[model] || [];
    }

    /**
     *
     * @param {String} modelName - Name of requested objects.
     * @param {Object} parent - Information about parent object.
     * @param {String} parent.type - Type of parent object.
     * @param {Number} parent.id - ID of parent object.
     * @param {Object} filterInfo - Information about pagination, sorting and filtering
     * @param {Number} filterInfo.current -
     * @param {Number} filterInfo.pageSize -
     * @param {Number} filterInfo.sortBy -
     * @param {Number} filterInfo.sortDirection -
     * @param {Number} filterInfo.filter -
     * @return {Promise}
     */
    function loadFirstTierItems(modelName, parent, filterInfo, filter) {
      var params = QueryAPI.buildParam(
        modelName,
        filterInfo,
        makeRelevantExpression(modelName, parent.type, parent.id),
        null,
        filter
      );
      var requestedType;

      if (SnapshotUtils.isSnapshotScope(parent) &&
        SnapshotUtils.isSnapshotModel(modelName)) {
        params = SnapshotUtils.transformQuery(params);
      }

      requestedType = params.object_name;
      return QueryAPI.makeRequest({data: [params]})
        .then(function (response) {
          response = response[0][requestedType];

          response.values = response.values.map(function (source) {
            return _createInstance(source, modelName);
          });

          return response;
        });
    }

    /**
     *
     * @param {Array} models - Array of models for load in sub tree
     * @param type - Type of parent object.
     * @param id - ID of parent object.
     * @param {String} filter - Filter.
     * @return {Promise} - Items for sub tier.
     */
    function loadItemsForSubTier(models, type, id, filter) {
      var loadedModels = [];
      var relevant = {
        type: type,
        id: id,
        operation: 'relevant'
      };
      var showMore = false;

      return _buildSubTreeCountMap(models, relevant, filter)
        .then(function (result) {
          var countMap = result.countsMap;
          var reqParams;

          loadedModels = Object.keys(countMap);
          showMore = result.showMore;

          reqParams = loadedModels.map(function (model) {
            var pageInfo = {
              filter: filter
            };

            if (countMap[model]) {
              pageInfo.current = 1;
              pageInfo.pageSize = countMap[model];
            }
            return QueryAPI.buildParam(
              model,
              pageInfo,
              relevant,
              !_isFullSubTree(type) ? SUB_TREE_FIELDS : null);
          });

          if (SnapshotUtils.isSnapshotParent(relevant.type) ||
            SnapshotUtils.isInScopeModel(relevant.type)) {
            reqParams = reqParams.map(function (item) {
              if (SnapshotUtils.isSnapshotModel(item.object_name)) {
                item = SnapshotUtils.transformQuery(item);
              }
              return item;
            });
          }

          return QueryAPI.makeRequest({data: reqParams});
        })
        .then(function (response) {
          var directlyRelated = [];
          var notRelated = [];

          loadedModels.forEach(function (modelName, index) {
            var values;

            if (SnapshotUtils.isSnapshotModel(modelName) &&
              response[index].Snapshot) {
              values = response[index].Snapshot.values;
            } else {
              values = response[index][modelName].values;
            }

            values.forEach(function (source) {
              var instance = _createInstance(source, modelName);

              if (_isDirectlyRelated(instance)) {
                directlyRelated.push(instance);
              } else {
                notRelated.push(instance);
              }
            });
          });

          return {
            directlyItems: directlyRelated,
            notDirectlyItems: notRelated,
            showMore: showMore
          };
        });
    }

    /**
     *
     * @param {String} requestedType - Type of requested object.
     * @param {String} relevantToType - Type of parent object.
     * @param {Number} relevantToId - ID of parent object.
     * @param {String} [operation] - Type of operation
     * @return {object} Returns expression for load items for 1st level of tree view.
     */
    function makeRelevantExpression(requestedType,
                                    relevantToType,
                                    relevantToId,
                                    operation) {
      var isObjectBrowser = /^\/objectBrowser\/?$/
        .test(window.location.pathname);
      var expression;

      if (!isObjectBrowser) {
        expression = {
          type: relevantToType,
          id: relevantToId
        };

        expression.operation = operation ? operation :
          _getTreeViewOperation(requestedType);
      }
      return expression;
    }

    /**
     *
     * @param {Array} models - Type of model.
     * @param {Object} relevant - Relevant description
     * @param {String} filter - Filter string.
     * @return {Promise} - Counts for limitation load items for sub tier
     * @private
     */
    function _buildSubTreeCountMap(models, relevant, filter) {
      var countQuery;
      var result;
      var countMap = {};

      if (_isFullSubTree(relevant.type)) {
        models.forEach(function (model) {
          countMap[model] = false;
        });
        result = can.Deferred().resolve({
          countsMap: countMap,
          showMore: false
        });
      } else {
        countQuery = QueryAPI.buildCountParams(models, relevant, filter);

        result = QueryAPI.makeRequest({data: countQuery})
          .then(function (response) {
            var total = 0;
            var showMore = models.some(function (model, index) {
              var count = response[index][model].total;

              if (!count) {
                return;
              }

              if (total + count < SUB_TREE_ELEMENTS_LIMIT) {
                countMap[model] = count;
              } else {
                countMap[model] = SUB_TREE_ELEMENTS_LIMIT - total;
              }

              total += count;

              return total >= SUB_TREE_ELEMENTS_LIMIT;
            });

            return {
              countsMap: countMap,
              showMore: showMore
            };
          });
      }

      return result;
    }

    function _isFullSubTree(type) {
      return FULL_SUB_LEVEL_LIST.indexOf(type) >= 0;
    }

    /**
     * @param {Object} source - Instance object.
     * @param {String} modelName - Name of model.
     * @return {CMS.Models} - Instance of model.
     * @private
     */
    function _createInstance(source, modelName) {
      var instance;

      if (source.type === 'Snapshot') {
        instance = SnapshotUtils.toObject(source);
      } else {
        instance = CMS.Models[modelName].model(source);
      }
      return instance;
    }

    /**
     * Check if object directly mapped to the current context.
     * @param {Object} instance - Instance of model.
     * @private
     * @return {Boolean} Is associated with the current context.
     */
    function _isDirectlyRelated(instance) {
      var needToSplit = CurrentPage.isObjectContextPage() &&
        CurrentPage.getPageType() !== 'Workflow';
      var relates = CurrentPage.related.attr(instance.type);
      var result = true;
      var instanceId = SnapshotUtils.isSnapshot(instance) ?
        instance.snapshot.child_id :
        instance.id;

      if (needToSplit) {
        result = !!(relates && relates[instanceId]);
      }

      return result;
    }

    function _getTreeViewOperation(objectName) {
      var isDashboard = /dashboard/.test(window.location);
      var operation;
      if (isDashboard) {
        operation = 'owned';
      } else if (!isDashboard && objectName === 'Person') {
        operation = 'related_people';
      }
      return operation;
    }

    return {
      getColumnsForModel: getColumnsForModel,
      setColumnsForModel: setColumnsForModel,
      displayTreeSubpath: displayTreeSubpath,
      getModelsForSubTier: getModelsForSubTier,
      loadFirstTierItems: loadFirstTierItems,
      loadItemsForSubTier: loadItemsForSubTier,
      makeRelevantExpression: makeRelevantExpression,
      createSelectedColumnsMap: createSelectedColumnsMap
    };
  })();
})(window.GGRC);
