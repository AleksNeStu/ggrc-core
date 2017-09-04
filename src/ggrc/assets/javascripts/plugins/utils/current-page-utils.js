/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (GGRC) {
  'use strict';

  /**
   * Util methods for work with Current Page.
   */
  GGRC.Utils.CurrentPage = (function () {
    var queryAPI = GGRC.Utils.QueryAPI;
    var relatedToCurrentInstance = new can.Map({
      define: {
        initialized: {
          type: 'boolean',
          value: false
        }
      }
    });

    var widgetsCounts = new can.Map({});

    var QueryAPI = GGRC.Utils.QueryAPI;
    var SnapshotUtils = GGRC.Utils.Snapshots;

    function initMappedInstances() {
      var currentPageInstance = GGRC.page_instance();
      var models = GGRC.Mappings.getMappingList(currentPageInstance.type);
      var reqParams = [];

      relatedToCurrentInstance.attr('initialized', true);
      models = can.makeArray(models);

      models.forEach(function (model) {
        var query = queryAPI.buildRelevantIdsQuery(
          model,
          {},
          {
            type: currentPageInstance.type,
            id: currentPageInstance.id,
            operation: 'relevant'
          });
        if (SnapshotUtils.isSnapshotRelated(currentPageInstance.type, model)) {
          query = SnapshotUtils.transformQuery(query);
        }
        reqParams.push(queryAPI.batchRequests(query));
      });

      return can.when.apply(can, reqParams)
        .then(function () {
          var response = can.makeArray(arguments);

          models.forEach(function (model, idx) {
            var ids = response[idx][model] ?
              response[idx][model].ids :
              response[idx].Snapshot.ids;
            var map = ids.reduce(function (mapped, id) {
              mapped[id] = true;
              return mapped;
            }, {});
            relatedToCurrentInstance.attr(model, map);
          });
          return relatedToCurrentInstance;
        });
    }

    // To identify pages like My Work, My Assessments and Admin Dashboard on the Server-side
    // was defined variable GGRC.pageType, because for all of them GGRC.page_instance().type = 'Person'.
    // For other pages using GGRC.page_instance() object.
    function getPageType() {
      return GGRC.pageType ? GGRC.pageType : GGRC.page_instance().type;
    }

    function isMyAssessments() {
      return getPageType() === 'MY_ASSESSMENTS';
    }

    function isMyWork() {
      return getPageType() === 'MY_WORK';
    }

    function isAdmin() {
      return getPageType() === 'ADMIN';
    }

    /**
     *
     * @return {boolean} False for My Work, All Objects and My Assessments pages and True for the rest.
     */
    function isObjectContextPage() {
      return !GGRC.pageType;
    }

    /**
     * Should return list of widgets required for rendering
     * @param {String} modelName - Page Object Model Name
     * @param {String} path - Application location path
     * @return {Object} - widget list object
     */
    function getWidgetList(modelName, path) {
      var widgetList = {};
      var isAssessmentsView;

      if (!modelName) {
        return widgetList;
      }
      widgetList = GGRC.WidgetList.get_widget_list_for(modelName);
      // Needs refactoring: Should be removed and replaced with Routing!!!
      isAssessmentsView = /^\/assessments_view/.test(path);

      // the assessments_view only needs the Assessments widget
      if (isAssessmentsView) {
        widgetList = {
          assessment: widgetList.assessment
        };
        widgetList.assessment.treeViewDepth = 0;
      }

      return widgetList;
    }

    function getWidgetModels(modelName, path) {
      var widgetList = getWidgetList(modelName, path);
      var defaults = getDefaultWidgets(widgetList, path);

      return defaults.map(function (widgetName) {
        var isObjectVersion = GGRC.Utils.ObjectVersions
          .isObjectVersion(widgetName);

        if (isObjectVersion) {
          return widgetName;
        }

        return widgetList[widgetName]
          .content_controller_options.model.shortName;
      });
    }

    function getDefaultWidgets(widgetList, path) {
      var defaults = Object.keys(widgetList);
      // Needs refactoring: Should be removed and replaced with Routing!!!
      var isObjectBrowser = /^\/objectBrowser\/?$/.test(path);

      // Remove info tab from object-browser list of tabs
      if (isObjectBrowser) {
        defaults.splice(defaults.indexOf('info'), 1);
      }
      return defaults;
    }

    /**
     * Counts for related objects.
     *
     * @return {can.Map} Promise which return total count of objects.
     */
    function getCounts() {
      return widgetsCounts;
    }

    /**
     * Update Page Counts
     * @param {Array|Object} widgets - list of widgets
     * @param {String} type - Type of parent object
     * @param {Number} id - ID of parent object
     * @return {can.Deferred} - resolved deferred object
     */
    function initCounts(widgets, type, id) {
      // Request params generation logic should be moved in
      // a separate place
      var widgetsObject = GGRC.Utils.ObjectVersions
        .getWidgetConfigs(can.makeArray(widgets));

      var params = widgetsObject.map(function (widgetObject) {
        var param;
        var expression = GGRC.Utils.TreeView
          .makeRelevantExpression(widgetObject.name, type, id);

        if (SnapshotUtils.isSnapshotRelated(type, widgetObject.name)) {
          param = QueryAPI.buildParam('Snapshot', {}, expression, null,
            GGRC.query_parser.parse('child_type = ' + widgetObject.name));
        } else {
          param = QueryAPI.buildParam(widgetObject.responseType,
            {}, expression, null,
            widgetObject.additionalFilter ?
              GGRC.query_parser.parse(widgetObject.additionalFilter) :
              null
            );
        }

        param.type = 'count';
        return param;
      });

      // Perform requests only if params are defined
      if (!params.length) {
        return can.Deferred().resolve();
      }

      return QueryAPI.makeRequest({
        data: params
      }).then(function (data) {
        var countsMap = {};
        data.forEach(function (info, i) {
          var widget = widgetsObject[i];
          var name = widget.responseType;
          var countsName = widget.countsName || widget.name;

          if (SnapshotUtils.isSnapshotRelated(type, name)) {
            name = 'Snapshot';
          }
          countsMap[countsName] = info[name].total;
        });
        getCounts().attr(countsMap);
      });
    }

    function refreshCounts() {
      var pageInstance = GGRC.page_instance();
      var widgets;
      var location = window.location.pathname;

      if (!pageInstance) {
        return can.Deferred().resolve();
      }

      widgets = GGRC.Utils.CurrentPage
        .getWidgetModels(pageInstance.constructor.shortName, location);

      return initCounts(widgets, pageInstance.type, pageInstance.id);
    }

    return {
      related: relatedToCurrentInstance,
      initMappedInstances: initMappedInstances,
      getPageType: getPageType,
      isMyAssessments: isMyAssessments,
      isMyWork: isMyWork,
      isAdmin: isAdmin,
      isObjectContextPage: isObjectContextPage,
      getWidgetList: getWidgetList,
      getWidgetModels: getWidgetModels,
      getDefaultWidgets: getDefaultWidgets,
      getCounts: getCounts,
      initCounts: initCounts,
      refreshCounts: refreshCounts
    };
  })();
})(window.GGRC);
