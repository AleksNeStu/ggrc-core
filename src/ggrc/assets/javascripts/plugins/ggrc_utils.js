/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function ($, GGRC, moment, Permission, CMS) {
  'use strict';
  var ROLE_TYPES = ['Assessor', 'Creator', 'Verifier'];
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
      return inst.tz(currentTimezone).format('MM/DD/YYYY hh:mm:ss A Z');
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
      var TMP_FILENAME = 'export_objects.csv';

      // a helper for opening the "Save File" dialog to save downloaded data
      function promptSaveFile() {
        var downloadURL = [
          'filesystem:', window.location.origin, '/temporary/', TMP_FILENAME
        ].join('');

        var link = document.createElement('a');

        link.setAttribute('href', downloadURL);
        link.setAttribute('download', TMP_FILENAME);
        link.style.display = 'none';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }

      function errorHandler(error) {
        console.error('LocalFileSys error:', error);
      }

      // a callback for when the browser's virtual file system is obtained
      function fileSystemObtained(localstorage) {
        localstorage.root.getFile(
          TMP_FILENAME, {create: true}, fileEntryObtained, errorHandler);
      }

      // a helper that writes thee downloaded data to a tmeporary file
      // and then opens the "Save File" dialog
      function fileEntryObtained(fileEntry) {
        fileEntry.createWriter(function (fileWriter) {
          var truncated = false;

          // the onwriteevent fires twice - once after truncating the file,
          // and then after writing the downloaded text content to it
          fileWriter.onwriteend = function (ev) {
            var blob;
            if (!truncated) {
              truncated = true;
              blob = new Blob([text], {type: 'text/plain'});
              fileWriter.write(blob);
            } else {
              promptSaveFile();
            }
          };

          fileWriter.onerror = function (ev) {
            console.error('Writing temp file failed: ' + ev.toString());
          };

          fileWriter.truncate(0);  // in case the file exists and is non-empty
        }, errorHandler);
      }

      // start storing the downloaded data to a temporary file for the user to
      // save it on his/her computers storage
      window.webkitRequestFileSystem(
        window.TEMPORARY, text.length, fileSystemObtained, errorHandler);
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

      var FORBIDDEN = Object.freeze({
        oneWay: Object.freeze({
          'issue audit': true // mapping audit to issue is not allowed
        }),
        // NOTE: the names in every type pair must be sorted alphabetically!
        twoWay: Object.freeze({
          'audit program': true,
          'audit request': true,
          'program riskassessment': true,
          'assessmenttemplate cacheable': true,
          'cacheable person': true,
          'person risk': true,
          'person threat': true
        })
      });

      if (target instanceof can.Model) {
        targetType = target.constructor.shortName;
      } else {
        targetType = target.type || target;
      }
      sourceType = source.constructor.shortName || source;
      types = [sourceType.toLowerCase(), targetType.toLowerCase()];

      // One-way check
      // special case check:
      // - mapping an Audit to a Issue is not allowed
      // (but vice versa is allowed)
      if (FORBIDDEN.oneWay[types.join(' ')]) {
        return false;
      }

      // Two-way check:
      // special case check:
      // - mapping an Audit to a Program is not allowed
      // - mapping an Audit to a Request is not allowed
      // (and vice versa)
      if (FORBIDDEN.twoWay[types.sort().join(' ')]) {
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
     * Remove all HTML tags from the string
     * @param {String} originalText - original string for parsing
     * @return {string} - plain text without tags
     */
    getPlainText: function (originalText) {
      originalText = originalText || '';
      return originalText.replace(/<[^>]*>?/g, '').trim();
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

    /**
     * Compute a list of people IDs that have `roleName` granted on `instance`.

     * @param {CMS.Models.Cacheable} instance - a model instance
     * @param {String} roleName - the name of the custom role
     *
     * @return {Array} - list of people
     */
    peopleWithRoleName: function (instance, roleName) {
      var modelRoles;
      var peopleIds;
      var roleId;

      // get role ID by roleName
      modelRoles = _.filter(
        GGRC.access_control_roles,
        {object_type: instance.class.model_singular, name: roleName});

      if (modelRoles.length === 0) {
        console.warn('peopleWithRole: role not found for instance type');
        return [];
      } else if (modelRoles.length > 1) {
        console.warn('peopleWithRole: found more than a single role');
        // We do not exit, as we have a reasonable fallback - picking
        // the first match.
      }

      roleId = modelRoles[0].id;

      peopleIds = _
          .chain(instance.access_control_list)
          .filter({ac_role_id: roleId})
          .map('person')
          .value();

      return peopleIds;
    },
    hasRoleForContext: function (userId, contextId, roleName) {
      var deferred = $.Deferred();
      var contextRoles;
      var filteredRoles;
      var hasRole;
      var userDfd =
        CMS.Models.Person.findInCacheById(userId) ||
        CMS.Models.Person.findOne({id: userId});

      $.when(userDfd)
        .then(function (user) {
          return user.get_mapping_deferred('authorizations');
        })
        .then(function (uRoles) {
          contextRoles = _.filter(uRoles, function (role) {
            return role.context_id === contextId;
          }).map(function (role) {
            return role.reify();
          });

          filteredRoles = GGRC.roles.filter(function (role) {
            return contextRoles.some(function (cr) {
              return cr.role.id === role.id;
            });
          });

          hasRole = filteredRoles.some(function (cr) {
            return cr.name === roleName;
          });

          deferred.resolve(hasRole);
        });

      return deferred;
    },
    getAssigneeType: function (instance) {
      var currentUser = GGRC.current_user;
      var userType = null;

      if (!instance || !currentUser) {
        return;
      }
      _.each(ROLE_TYPES, function (type) {
        var users = instance.assignees.attr(type);
        var isMapping;
        if (!users.length) {
          return;
        }

        isMapping = _.filter(users, function (user) {
          return user.id === currentUser.id;
        }).length;

        if (isMapping) {
          type = can.capitalize(type);
          userType = userType ? userType + ',' + type : type;
        }
      });
      return userType;
    }
  };

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

    function _buildACL(content) {
      /**
      * Build acl from deprecated contact fields. This is needed when
      * displaying old revisions that do not have the access_control_list
      * property.
      * @param {Object} content - revision contant dict
      * @return {Array} Access Control List created from old contact fields
      */
      var mapper = {
        contact_id: 'Primary Contacts',
        secondary_contact_id: 'Secondary Contacts',
        principal_assessor_id: 'Principal Assignees',
        secondary_assessor_id: 'Secondary Assignees'
      };
      return _.filter(_.map(mapper, function (v, k) {
        var role = _.find(GGRC.access_control_roles, function (acr) {
          return acr.name === v && acr.object_type === content.type;
        });
        if (!role || !content[k]) {
          return;
        }
        return {
          ac_role_id: role.id,
          person_id: content[k]
        };
      }), Boolean);
    }

    /**
     * Convert snapshot to object
     * @param {Object} instance - Snapshot instance
     * @return {Object} The object
     */
    function toObject(instance) {
      var object;
      var model = CMS.Models[instance.child_type];
      var content = instance.revision.content;
      var type = model.root_collection;
      var audit;

      content.isLatestRevision = instance.is_latest_revision;
      content.originalLink = '/' + type + '/' + content.id;
      content.snapshot = new can.Map(instance);
      content.related_sources = [];
      content.related_destinations = [];
      content.viewLink = content.snapshot.viewLink;
      content.selfLink = content.snapshot.selfLink;
      content.type = instance.child_type;
      content.id = instance.id;
      content.originalObjectDeleted = instance.original_object_deleted;
      content.canRead = Permission.is_allowed_for('read', {
        type: instance.child_type,
        id: instance.child_id
      });
      content.canUpdate = Permission.is_allowed_for('update', {
        type: instance.child_type,
        id: instance.child_id
      });

      if (content.access_control_list === undefined) {
        content.access_control_list = _buildACL(content);
      }

      if (content.access_control_list) {
        content.access_control_list.forEach(function (item) {
          item.person = new CMS.Models.Person({id: item.person_id}).stub();
        });
      }

      if (instance.child_type === 'Control' ||
        instance.child_type === 'Objective') {
        content.last_assessment_date = instance.last_assessment_date;
      }

      object = new model(content);
      object.attr('originalLink', content.originalLink);
      // Update archived flag in content when audit is archived:
      if (instance.parent &&
        CMS.Models.Audit.findInCacheById(instance.parent.id)) {
        audit = CMS.Models.Audit.findInCacheById(instance.parent.id);
        audit.bind('change', function () {
          var field = arguments[1];
          var newValue = arguments[3];
          if (field !== 'archived' || !object.snapshot) {
            return;
          }
          object.snapshot.attr('archived', newValue);
        });
      }
      model.removeFromCacheById(content.id);  /* removes snapshot object from cache */

      return object;
    }

    /**
     * Build url for snapshot's parent
     * @param {Object} instance - Snapshot instance
     * @return {String} Url
     */
    function getParentUrl(instance) {
      var model = CMS.Models[instance.child_type];
      var plural = model.table_plural;
      var link = '/' + plural + '/' + instance.child_id;

      return link;
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

    /**
     * Check whether object type is snapshot
     * @param {Object} instance - Object instance
     * @return {Boolean} True or False
     */
    function isSnapshotType(instance) {
      return instance && instance.type === 'Snapshot';
    }

    /**
     * build query for getting a snapshot.
     * @param {String} instance - Relevant instance
     * @param {String} childId - Child id of snapshot
     * @param {String} childType - Child type of snapshot
     * @return {Object} Query object
     */
    function getSnapshotItemQuery(instance, childId, childType) {
      var relevantFilters = [{
        type: instance.type,
        id: instance.id,
        operation: 'relevant'
      }];
      var filters = {
        expression: {
          left: {
            left: 'child_type',
            op: {name: '='},
            right: childType
          },
          op: {name: 'AND'},
          right: {
            left: 'child_id',
            op: {name: '='},
            right: childId
          }
        }
      };
      var query = GGRC.Utils.QueryAPI
        .buildParam('Snapshot', {}, relevantFilters, [], filters);
      return {data: [query]};
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
      setAttrs: setAttrs,
      getSnapshotItemQuery: getSnapshotItemQuery,
      isSnapshotType: isSnapshotType,
      getParentUrl: getParentUrl
    };
  })();
})(jQuery, window.GGRC = window.GGRC || {}, moment, window.Permission,
  window.CMS = window.CMS || {});
