/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function ($, GGRC, moment, Permission) {
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
   * A module containing various utility functions.
   */
  GGRC.Utils = {
    win: window,
    filters: {
      /**
       * Performs filtering on provided array like instances
       * @param {Array} items - array like instance
       * @param {Function} filter - filtering function
       * @param {Function} selectFn - function to select proper attributes
       * @return {Array} - filtered array
       */
      applyFilter: function (items, filter, selectFn) {
        selectFn = selectFn ||
          function (x) {
            return x;
          };
        return Array.prototype.filter.call(items, function (item) {
          return filter(selectFn(item));
        });
      },
      /**
       * Helper function to create a filtering function
       * @param {Object|null} filterObj - filtering params
       * @return {Function} - filtering function
       */
      makeTypeFilter: function (filterObj) {
        function checkIsNotEmptyArray(arr) {
          return arr && Array.isArray(arr) && arr.length;
        }
        return function (type) {
          type = type.toString().toLowerCase();
          if (!filterObj) {
            return true;
          }
          if (checkIsNotEmptyArray(filterObj.only)) {
            // Do sanity transformation
            filterObj.only = filterObj.only.map(function (item) {
              return item.toString().toLowerCase();
            });
            return filterObj.only.indexOf(type) > -1;
          }
          if (checkIsNotEmptyArray(filterObj.exclude)) {
            // Do sanity transformation
            filterObj.exclude = filterObj.exclude.map(function (item) {
              return item.toString().toLowerCase();
            });
            return filterObj.exclude.indexOf(type) === -1;
          }
          return true;
        };
      },
      applyTypeFilter: function (items, filterObj, getTypeSelectFn) {
        var filter = GGRC.Utils.filters.makeTypeFilter(filterObj);
        return GGRC.Utils.filters.applyFilter(items, filter, getTypeSelectFn);
      }
    },
    sortingHelpers: {
      commentSort: function (a, b) {
        if (a.created_at < b.created_at) {
          return 1;
        } else if (a.created_at > b.created_at) {
          return -1;
        }
        return 0;
      }
    },
    events: {
      isInnerClick: function (el, target) {
        el = el instanceof $ ? el : $(el);
        return el.has(target).length || el.is(target);
      }
    },
    inViewport: function (el) {
      var bounds;
      var isVisible;

      el = el instanceof $ ? el[0] : el;
      bounds = el.getBoundingClientRect();

      isVisible = this.win.innerHeight > bounds.bottom &&
        this.win.innerWidth > bounds.right;

      return isVisible;
    },
    firstWorkingDay: function (date) {
      date = moment(date);
      // 6 is Saturday 0 is Sunday
      while (_.contains([0, 6], date.day())) {
        date.add(1, 'day');
      }
      return date.toDate();
    },
    formatDate: function (date, hideTime) {
      var currentTimezone = moment.tz.guess();
      var inst;

      if (date === undefined || date === null) {
        return '';
      }

      if (typeof date === 'string') {
        // string dates are assumed to be in ISO format
        return moment.utc(date, 'YYYY-MM-DD', true).format('MM/DD/YYYY');
      }

      inst = moment(new Date(date.isComputed ? date() : date));
      if (hideTime === true) {
        return inst.format('MM/DD/YYYY');
      }
      return inst.tz(currentTimezone).format('MM/DD/YYYY hh:mm:ss A z');
    },
    getPickerElement: function (picker) {
      return _.find(_.values(picker), function (val) {
        if (val instanceof Node) {
          return /picker\-dialog/.test(val.className);
        }
        return false;
      });
    },
    download: function (filename, text) {
      var element = document.createElement('a');
      element.setAttribute(
        'href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(text));
      element.setAttribute('download', filename);
      element.style.display = 'none';
      document.body.appendChild(element);
      element.click();
      document.body.removeChild(element);
    },
    loadScript: function (url, callback) {
      var script = document.createElement('script');
      script.type = 'text/javascript';
      if (script.readyState) {
        script.onreadystatechange = function () {
          if (script.readyState === 'loaded' ||
            script.readyState === 'complete') {
            script.onreadystatechange = null;
            callback();
          }
        };
      } else {
        script.onload = function () {
          callback();
        };
      }
      script.src = url;
      document.getElementsByTagName('head')[0].appendChild(script);
    },
    export_request: function (request) {
      return $.ajax({
        type: 'POST',
        dataType: 'text',
        headers: $.extend({
          'Content-Type': 'application/json',
          'X-export-view': 'blocks',
          'X-requested-by': 'GGRC'
        }, request.headers || {}),
        url: '/_service/export_csv',
        data: JSON.stringify(request.data || {})
      });
    },
    hasPending: function (parentInstance, instance, how) {
      var list = parentInstance._pending_joins;
      how = how || 'add';

      if (!list || !list.length) {
        return false;
      }
      if (list instanceof can.List) {
        list = list.serialize();
      }

      return _.find(list, function (pending) {
        var method = pending.how === how;
        if (!instance) {
          return method;
        }
        return method && pending.what === instance;
      });
    },
    is_mapped: function (target, destination, mapping) {
      var tablePlural;
      var bindings;

      // Should check all passed arguments are presented
      if (!target || !destination) {
        console.error('Incorrect arguments list: ', arguments);
        return false;
      }
      if (_.isUndefined(mapping)) {
        tablePlural = CMS.Models[destination.type].table_plural;
        mapping = (target.has_binding(tablePlural) ? '' : 'related_') +
          tablePlural;
      }
      bindings = target.get_binding(mapping);
      if (bindings && bindings.list && bindings.list.length) {
        return _.find(bindings.list, function (item) {
          return item.instance.id === destination.id;
        });
      }
      if (target.objects && target.objects.length) {
        return _.find(target.objects, function (item) {
          return item.id === destination.id && item.type === destination.type;
        });
      }
    },
    /**
     * Get list of mappable objects for certain type
     *
     * @param {String} type - Type of object we want to
     *                      get list of mappable objects for
     * @param {Object} options - Options
     *   @param {Array} options.whitelist - List of objects that will always appear
     *   @param {Array} options.forbidden - List of objects that will always be removed
     *
     * @return {Array} - List of mappable objects
     */
    getMappableTypes: function (type, options) {
      var result;
      var canonical = GGRC.Mappings.get_canonical_mappings_for(type);
      var list = GGRC.tree_view.base_widgets_by_type[type];
      var forbidden;
      var forbiddenList = {
        Program: ['Audit', 'RiskAssessment'],
        Audit: ['Assessment', 'Program'],
        Assessment: ['Workflow', 'TaskGroup'],
        Person: '*',
        AssessmentTemplate: '*'
      };
      options = options || {};
      if (!type) {
        return [];
      }
      if (options.forbidden) {
        forbidden = options.forbidden;
      } else {
        forbidden = forbiddenList[type] || [];
      }
      result = _.intersection.apply(_, _.compact([_.keys(canonical), list]));
      if (_.isString(forbidden) && forbidden === '*') {
        forbidden = [];
        result = [];
      }
      result = _.partial(_.without, result);
      result = result.apply(result, forbidden);

      if (options.whitelist) {
        result = _.union(result, options.whitelist);
      }
      return result;
    },
    /**
     * Determine if two types of models can be mapped
     *
     * @param {String} target - the target type of model
     * @param {String} source - the source type of model
     * @param {Object} options - accepts:
     *        {Array} whitelist - list of added objects
     *        {Array} forbidden - list blacklisted objects
     *
     * @return {Boolean} - true if mapping is allowed, false otherwise
     */
    isMappableType: function (target, source, options) {
      var result;
      if (!target || !source) {
        return false;
      }
      result = this.getMappableTypes(target, options);
      return _.contains(result, source);
    },
    /**
     * Determine if `source` is allowed to be mapped to `target`.
     *
     * By symmetry, this method can be also used to check whether `source` can
     * be unmapped from `target`.
     *
     * @param {Object} source - the source object the mapping
     * @param {Object} target - the target object of the mapping
     * @param {Object} options - the options objects, similar to the one that is
     *   passed as an argument to Mustache helpers
     *
     * @return {Boolean} - true if mapping is allowed, false otherwise
     */
    allowed_to_map: function (source, target, options) {
      var canMap = false;
      var types;
      var targetType;
      var sourceType;
      var targetContext;
      var sourceContext;
      var createContexts;
      var canonical;
      var hasWidget;
      var canonicalMapping;

      // NOTE: the names in every type pair must be sorted alphabetically!
      var FORBIDDEN = Object.freeze({
        'audit issue': true,
        'audit program': true,
        'audit request': true,
        'program riskassessment': true,
        'assessmenttemplate cacheable': true,
        'cacheable person': true,
        'person risk': true,
        'person threat': true
      });

      if (target instanceof can.Model) {
        targetType = target.constructor.shortName;
      } else {
        targetType = target.type || target;
      }
      sourceType = source.constructor.shortName || source;

      // special case check:
      // - mapping an Audit to a Program is not allowed
      // - mapping an Audit to a Request is not allowed
      // (and vice versa)
      types = [sourceType.toLowerCase(), targetType.toLowerCase()].sort();
      if (FORBIDDEN[types.join(' ')]) {
        return false;
      }

      // special check for snapshot:
      if (options &&
        options.context &&
        options.context.parent_instance &&
        options.context.parent_instance.snapshot) {
        // Avoid add mapping for snapshot
        return false;
      }

      canonical = GGRC.Mappings.get_canonical_mapping_name(
        sourceType, targetType);
      canonicalMapping = GGRC.Mappings.get_canonical_mapping(
        sourceType, targetType);

      if (canonical && canonical.indexOf('_') === 0) {
        canonical = null;
      }

      hasWidget = _.contains(
        GGRC.tree_view.base_widgets_by_type[sourceType] || [],
        targetType);

      if (_.exists(options, 'hash.join') && (!canonical || !hasWidget) ||
        (canonical && !canonicalMapping.model_name)) {
        return false;
      }
      targetContext = _.exists(target, 'context.id');
      sourceContext = _.exists(source, 'context.id');
      createContexts = _.exists(
        GGRC, 'permissions.create.Relationship.contexts');

      canMap = Permission.is_allowed_for('update', source) ||
        sourceType === 'Person' ||
        _.contains(createContexts, sourceContext) ||
        // Also allow mapping to source if the source is about to be created.
        _.isUndefined(source.created_at);

      if (target instanceof can.Model) {
        canMap = canMap &&
          (Permission.is_allowed_for('update', target) ||
          targetType === 'Person' ||
          _.contains(createContexts, targetContext));
      }
      return canMap;
    },
    /**
     * Return Model Constructor Instance
     * @param {String} type - Model type
     * @return {CMS.Model.Cacheble|null} - Return Model Constructor
     */
    getModelByType: function (type) {
      if (!type || typeof type !== 'string') {
        console.debug('Type is not provided or has incorrect format',
          'Value of Type is: ', type);
        return null;
      }
      return CMS.Models[type] || GGRC.Models[type];
    },
    /**
     * Return normalized Custom Attribute Type from Custom Attribute Definition
     * @param {String} type - String Custom Attribute Value from JSON
     * @return {String} - Normalized Custom Attribute Type
     */
    mapCAType: function (type) {
      return customAttributesType[type] || 'input';
    },
    isEmptyCA: function (value, type, cav) {
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
    },
    /**
     * Remove all HTML tags from the string
     * @param {String} originalText - original string for parsing
     * @return {string} - plain text without tags
     */
    getPlainText: function (originalText) {
      originalText = originalText || '';
      return originalText.replace(/<[^>]*>?/g, '').trim();
    },
    /**
     * Add subtree for object tree view
     * @param {Number} depth - for subtree
     * @return {Object} - mapping of related objects
     */
    getRelatedObjects: function (depth) {
      var basedRelatedObjects;
      var relatedObject;
      var mustachePath = GGRC.mustache_path;
      if (!depth) {
        return {};
      }

      basedRelatedObjects = {
        model: can.Model.Cacheable,
        mapping: 'related_objects',
        show_view: mustachePath + '/base_objects/tree.mustache',
        footer_view: mustachePath + '/base_objects/tree_footer.mustache',
        add_item_view: mustachePath + '/base_objects/tree_add_item.mustache',
        draw_children: false
      };

      relatedObject = $.extend(basedRelatedObjects, {
        child_options: [this.getRelatedObjects(depth - 1)]
      });

      if (depth === 1) {
        return relatedObject;
      }

      relatedObject.draw_children = true;

      return relatedObject;
    },
    /**
     * A function that returns the highest role in an array of strings of roles
     * or a comma-separated string of roles.
     *
     * @param {CMS.Models.Cacheable} obj - Assignable object with defined
     *   assignable_list class property holding assignable roles ordered in
     *   increasing importance.
     * Return highest assignee role from a list of roles
     * @param {Array|String} roles - An Array of strings or a String with comma
     *   separated values of roles.
     * @return {string} - Highest role from an array of strings or 'none' if
     *   none found.
     */
    get_highest_assignee_role: function (obj, roles) {
      var roleOrder = _.map(
        _.map(obj.class.assignable_list, 'type'),
        _.capitalize);

      if (_.isString(roles)) {
        roles = roles.split(',');
      }

      roles = _.map(roles, _.capitalize);

      roles.unshift('none');
      return _.max(roles, Array.prototype.indexOf.bind(roleOrder));
    },
    _display_tree_subpath: function display_subpath(el, path, attempt_counter) {
    var rest = path.split('/');
    var type = rest.shift();
    var id = rest.shift();
    var selector = '[data-object-type=\'' + type + '\'][data-object-id=' + id + ']';
    var $node;
    var node_controller;
    var controller;

    if (!attempt_counter) {
      attempt_counter = 0;
    }

    rest = rest.join('/');

    if (type || id) {
      $node = el.find(selector);

      // sometimes nodes haven't loaded yet, wait for them
      if (!$node.size() && attempt_counter < 5) {
        setTimeout(function () {
          display_subpath(el, path, attempt_counter + 1);
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
        node_controller = $node.control();
        if (node_controller && node_controller.display_path) {
          return node_controller.display_path(rest);
        }
      }
    }
    return can.Deferred().resolve();
  }
  };

  /**
   * Util methods for work with QueryAPI.
   */
  GGRC.Utils.QueryAPI = (function () {
    /**
     * @typedef LimitArray
     * @type {array}
     * @property {number} 0  - Lower bound is inclusive.
     * @property {number} 1  - Upper bound is exclusive.
     */

    /**
     * @typedef QueryAPIRequest
     * @type {Object}
     * @property {string} object_name - The name of object
     * @property {LimitArray} limit - The boundaries of the requested values.
     * @property {object} filters - Filter properties
     */

    var widgetsCounts = new can.Map({});

    /**
     * Build params for request on Query API.
     *
     * @param {String} objName - Name of requested object
     * @param {Object} page - Information about page state.
     * @param {Number} page.current - Current page
     * @param {Number} page.pageSize - Page size
     * @param {String} page.sortBy - sortBy
     * @param {String} page.sortDirection - sortDirection
     * @param {String} page.filter - Filter string
     * @param {Object} relevant - Information about relevant object
     * @param {Object} relevant.type - Type of relevant object
     * @param {Object} relevant.id - Id of relevant object
     * @param {Object} relevant.operation - Type of operation.
     * @param {Object} additionalFilter - An additional filter to be applied
     * @return {Array} Array of QueryAPIRequest
     */
    function buildParams(objName, page, relevant, additionalFilter) {
      return [buildParam(objName, page, relevant, undefined, additionalFilter)];
    }

    /**
     * Build params for ids type request on Query API.
     *
     * @param {String} objName - Name of requested object
     * @param {Object} page - Information about page state.
     * @param {Number} page.current - Current page
     * @param {Number} page.pageSize - Page size
     * @param {String} page.sortBy - sortBy
     * @param {String} page.sortDirection - sortDirection
     * @param {String} page.filter - Filter string
     * @param {Object} relevant - Information about relevant object
     * @param {Object} relevant.type - Type of relevant object
     * @param {Object} relevant.id - Id of relevant object
     * @param {Object} relevant.operation - Type of operation.
     * @param {Object|Array} additionalFilter - Additional filters to be applied
     * @return {Object} Object of QueryAPIRequest
     */
    function buildRelevantIdsQuery(objName, page, relevant, additionalFilter) {
      var params = {};

      if (!objName) {
        return {};
      }

      params.object_name = objName;
      params.filters =
        _makeFilter(objName, page.filter, relevant, additionalFilter);
      params.type = 'ids';

      return params;
    }

    /**
     * Build params for request on Query API.
     *
     * @param {String} objName - Name of requested object
     * @param {Object} page - Information about page state.
     * @param {Number} page.current - Current page
     * @param {Number} page.pageSize - Page size
     * @param {String} page.sortBy - sortBy
     * @param {String} page.sortDirection - sortDirection
     * @param {String} page.filter - Filter string
     * @param {Object|Object[]} relevant - Information about relevant object
     * @param {Object} relevant.type - Type of relevant object
     * @param {Object} relevant.id - Id of relevant object
     * @param {Object} relevant.operation - Type of operation.
     * @param {Array} fields - Array of requested fields.
     * @param {Object|Array} additionalFilter - Additional filters to be applied
     * @return {Object} Object of QueryAPIRequest
     */
    function buildParam(objName, page, relevant, fields, additionalFilter) {
      var first;
      var last;
      var params = {};

      if (!objName) {
        return {};
      }

      params.object_name = objName;
      params.filters =
        _makeFilter(objName, page.filter, relevant, additionalFilter);

      if (page.current && page.pageSize) {
        first = (page.current - 1) * page.pageSize;
        last = page.current * page.pageSize;
        params.limit = [first, last];
      }
      if (page.sortBy) {
        params.order_by = [{
          name: page.sortBy,
          desc: page.sortDirection === 'desc'
        }];
      }
      if (fields) {
        params.fields = fields;
      }
      return params;
    }

    /**
     * Counts for related objects.
     *
     * @return {can.Map} Promise which return total count of objects.
     */
    function getCounts() {
      return widgetsCounts;
    }

    function initCounts(widgets, relevant) {
      var params = can.makeArray(widgets)
        .map(function (widget) {
          var param;
          if (GGRC.Utils.Snapshots.isSnapshotRelated(relevant.type, widget)) {
            param = buildParam('Snapshot', {},
              makeExpression(widget, relevant.type, relevant.id), null,
              GGRC.query_parser.parse('child_type = ' + widget));
          } else if (typeof widget === 'string') {
            param = buildParam(widget, {},
              makeExpression(widget, relevant.type, relevant.id));
          } else {
            param = buildParam(widget.name, {},
              makeExpression(widget.name, relevant.type, relevant.id),
              null, widget.additionalFilter);
          }
          param.type = 'count';
          return param;
        });

      return makeRequest({
        data: params
      }).then(function (data) {
        data.forEach(function (info, i) {
          var widget = widgets[i];
          var name = typeof widget === 'string' ? widget : widget.name;
          var countsName = typeof widget === 'string' ?
            widget : (widget.countsName || widget.name);
          if (GGRC.Utils.Snapshots.isSnapshotRelated(relevant.type, name)) {
            name = 'Snapshot';
          }
          widgetsCounts.attr(countsName, info[name].total);
        });
      });
    }

    /**
     * Params for request on Query API
     * @param {Object} params - Params for request
     * @param {Object} params.headers - Custom headers for request.
     * @param {Object} params.data - Object with parameters on Query API needed.
     * @return {Promise} Promise on Query API request.
     */
    function makeRequest(params) {
      var reqParams = params.data || [];
      return can.ajax({
        type: 'POST',
        headers: $.extend({
          'Content-Type': 'application/json'
        }, params.headers || {}),
        url: '/query',
        data: JSON.stringify(reqParams)
      });
    }

    function makeExpression(parent, type, id, operation) {
      var isObjectBrowser = /^\/objectBrowser\/?$/
        .test(window.location.pathname);
      var expression;

      if (!isObjectBrowser) {
        expression = {
          type: type,
          id: id
        };

        expression.operation = operation ? operation :
          _getTreeViewOperation(parent);
      }
      return expression;
    }

    function _makeRelevantFilter(filter, objName) {
      var relevantFilter = GGRC.query_parser.parse('#' + filter.type + ',' +
        filter.id + '#');

      if (filter && !filter.operation) {
        filter.operation = _getTreeViewOperation(objName);
      }

      if (filter.operation &&
        filter.operation !== relevantFilter.expression.op.name) {
        relevantFilter.expression.op.name = filter.operation;
      }

      return relevantFilter;
    }

    function _makeFilter(objName, filter, relevant, additionalFilter) {
      var relevantFilters;
      var filterList = [];

      if (relevant) {
        relevant = Array.isArray(relevant) ?
          relevant :
          can.makeArray(relevant);
        relevantFilters = relevant.map(function (filter) {
          return _makeRelevantFilter(filter, objName);
        });
        filterList = filterList.concat(relevantFilters);
      }

      if (filter) {
        filterList.push(GGRC.query_parser.parse(filter));
      }

      if (additionalFilter) {
        additionalFilter = Array.isArray(additionalFilter) ?
          additionalFilter :
          can.makeArray(additionalFilter);
        filterList = filterList.concat(additionalFilter);
      }
      if (filterList.length) {
        return filterList.reduce(function (left, right) {
          return GGRC.query_parser.join_queries(left, right);
        });
      }
      return {expression: {}};
    }

    function _getTreeViewOperation(objectName) {
      var isDashboard = /dashboard/.test(window.location);
      var operation;
      if (isDashboard) {
        operation = 'owned';
      } else if (objectName === 'Person') {
        operation = 'related_people';
      }
      return operation;
    }

    return {
      buildParam: buildParam,
      buildParams: buildParams,
      buildRelevantIdsQuery: buildRelevantIdsQuery,
      makeRequest: makeRequest,
      getCounts: getCounts,
      makeExpression: makeExpression,
      initCounts: initCounts
    };
  })();

  /**
   * Browser-specific utils.
   */
  GGRC.Utils.Browser = (function () {
    /**
     * Refresh current page
     * @param {Boolean} force - Force refresh and don't wait for GGRC queue.
     */
    function refreshPage(force) {
      if (force) {
        window.onbeforeunload = null;
      }
      window.location.reload(force);
    }

    return {
      refreshPage: refreshPage
    };
  })();

  /**
   * Util methods for work with Snapshots.
   */
  GGRC.Utils.Snapshots = (function () {
    /**
     * Set extra attrs for snapshoted objects or snapshots
     * @param {Object} instance - Object instance
     */
    function setAttrs(instance) {
      // Get list of objects that supports 'snapshot scope' from config
      var className = instance.type;
      if (isSnapshotParent(className)) {
        instance.attr('is_snapshotable', true);
      }
    }

    /**
     * Check whether object is snapshot
     * @param {Object} instance - Object instance
     * @return {Boolean} True or False
     */
    function isSnapshot(instance) {
      return instance && (instance.snapshot || instance.isRevision);
    }

    /**
     * Check whether object is in spanshot scope
     * @param {Object} parentInstance - Object (parent) instance
     * @return {Boolean} True or False
     */
    function isSnapshotScope(parentInstance) {
      var instance = parentInstance || GGRC.page_instance();
      return instance ?
        instance.is_snapshotable || isInScopeModel(instance.type) :
        false;
    }

    /**
     * Check whether provided model name is snapshot parent
     * @param {String} parent - Model name
     * @return {Boolean} True or False
     */
    function isSnapshotParent(parent) {
      return GGRC.config.snapshotable_parents.indexOf(parent) > -1;
    }

    /**
     * Check whether provided model name should be snapshot or default one
     * @param {String} modelName - model to check
     * @return {Boolean} True or False
     */
    function isSnapshotModel(modelName) {
      return GGRC.config.snapshotable_objects.indexOf(modelName) > -1;
    }

    /**
     * Check if the relationship is of type snapshot.
     * @param {String} parent - Parent of the related objects
     * @param {String} child - Child of the related objects
     * @return {Boolean} True or False
     */
    function isSnapshotRelated(parent, child) {
      return isSnapshotParent(parent) && isSnapshotModel(child) ||
        isInScopeModel(parent) && isSnapshotModel(child);
    }

    function isInScopeModel(model) {
      return GGRC.Utils.Snapshots.inScopeModels.indexOf(model) > -1;
    }

    /**
     * Convert snapshot to object
     * @param {Object} instance - Snapshot instance
     * @return {Object} The object
     */
    function toObject(instance) {
      var model = CMS.Models[instance.child_type];
      var content = instance.revision.content;
      var type = model.root_collection;
      content.isLatestRevision = instance.is_latest_revision;
      content.originalLink = '/' + type + '/' + content.id;
      content.snapshot = new CMS.Models.Snapshot(instance);
      content.related_sources = [];
      content.related_destinations = [];
      content.viewLink = content.snapshot.viewLink;
      content.selfLink = content.snapshot.selfLink;
      content.type = instance.child_type;
      content.id = instance.id;
      return new model(content);
    }

    /**
     * Convert array of snapshots to array of object
     * @param {Object} values - array of snapshots
     * @return {Object} The array of objects
     */
    function toObjects(values) {
      return new can.List(values.map(toObject));
    }

    /**
     * Transform query for objects into query for snapshots of the same type
     * @param {Object} query - original query
     * @return {Object} The transformed query
     */
    function transformQuery(query) {
      var type = query.object_name;
      var expression = query.filters.expression;
      query.object_name = 'Snapshot';
      query.filters.expression = {
        left: {
          left: 'child_type',
          op: {name: '='},
          right: type
        },
        op: {name: 'AND'},
        right: expression
      };
      return query;
    }

    return {
      inScopeModels: ['Assessment', 'Issue', 'AssessmentTemplate'],
      outOfScopeModels: ['Person', 'Program'],
      isSnapshot: isSnapshot,
      isSnapshotScope: isSnapshotScope,
      isSnapshotParent: isSnapshotParent,
      isSnapshotRelated: isSnapshotRelated,
      isSnapshotModel: isSnapshotModel,
      isInScopeModel: isInScopeModel,
      toObject: toObject,
      toObjects: toObjects,
      transformQuery: transformQuery,
      setAttrs: setAttrs
    };
  })();

  /**
   * Utils for state.
   */
  GGRC.Utils.State = (function () {
    var assignableModels = ['Assessment', 'Workflow'];
    var stateModels = ['AccessGroup', 'Clause', 'Contract',
       'Control', 'DataAsset', 'Facility', 'Issue', 'Market',
       'Objective', 'OrgGroup', 'Policy', 'Process', 'Product', 'Program',
       'Project', 'Regulation', 'Risk', 'Section', 'Standard', 'System',
       'Threat', 'Vendor'];
    var notFilterableModels = ['Person', 'AssessmentTemplate', 'Workflow',
        'TaskGroup', 'Cycle', 'CycleTaskGroupObjectTask'];

    function isAssignable(model) {
      return assignableModels.indexOf(model) > -1;
    }

    function hasState(model) {
      return stateModels.indexOf(model) > -1;
    }

    function hasFilter(model) {
      return notFilterableModels.indexOf(model) < 0;
    }

    function statusFilter(statuses, filterString) {
      var filter = statuses
        .map(function (item) {
          return 'Status=' + item;
        }).join(' Or ');

      filterString = filterString || '';
      if (filter !== '') {
        if (filterString !== '') {
          return filterString + ' And ' + filter;
        }
        return filter;
      }

      return filterString;
    }

    return {
      isAssignable: isAssignable,
      hasState: hasState,
      hasFilter: hasFilter,
      statusFilter: statusFilter
    };
  })();

})(jQuery, window.GGRC = window.GGRC || {}, window.moment, window.Permission);
