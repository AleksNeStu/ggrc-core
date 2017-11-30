/*
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

import RefreshQueue from '../models/refresh_queue';
import Permission from '../permission';

(function ($, GGRC, moment, CMS) {
  'use strict';

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
      var formats = [
        'YYYY-MM-DD',
        'YYYY-MM-DDTHH:mm:ss',
        'YYYY-MM-DDTHH:mm:ss.SSSSSS',
      ];
      var inst;

      if (date === undefined || date === null) {
        return '';
      }

      if (typeof date === 'string') {
        // string dates are assumed to be in ISO format

        if (hideTime) {
          return moment.utc(date, formats, true).format('MM/DD/YYYY');
        }
        return moment.utc(date, formats, true)
          .format('MM/DD/YYYY hh:mm:ss A Z');
      }

      inst = moment(new Date(date.isComputed ? date() : date));
      if (hideTime === true) {
        return inst.format('MM/DD/YYYY');
      }
      return inst.tz(currentTimezone).format('MM/DD/YYYY hh:mm:ss A Z');
    },
    fileSafeCurrentDate() {
      return moment().format('YYYY-MM-DD_HH-mm-ss');
    },
    getPersonInfo(person) {
      const dfd = can.Deferred();
      let actualPerson;

      if (!person || !person.id) {
        dfd.resolve(person);
        return dfd;
      }

      actualPerson = CMS.Models.Person.store[person.id] || {};
      if (actualPerson.email) {
        dfd.resolve(actualPerson);
      } else {
        actualPerson = new CMS.Models.Person({id: person.id});
        new RefreshQueue()
          .enqueue(actualPerson)
          .trigger()
          .done((personItem) => {
            personItem = Array.isArray(personItem) ? personItem[0] : personItem;
            dfd.resolve(personItem);
          })
          .fail(function () {
            GGRC.Errors.notifier('error',
              'Failed to fetch data for person ' + person.id + '.');
            dfd.reject();
          });
      }

      return dfd;
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
      var TMP_FILENAME = filename || 'export_objects.csv';

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
    import_request: function (request, isTest) {
      return $.ajax({
        type: 'POST',
        cache: false,
        contentType: false,
        processData: false,
        headers: $.extend({
          'Content-Type': 'application/json',
          'X-test-only': `${isTest}`,
          'X-requested-by': 'GGRC',
        }, request.headers || {}),
        url: '/_service/import_csv',
        data: JSON.stringify(request.data),
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
        Program: ['Audit'],
        Audit: ['Assessment', 'Program'],
        Assessment: ['Workflow', 'TaskGroup'],
        Person: ['Issue'],
      };
      options = options || {};
      if (!type) {
        return [];
      }
      forbidden = _.union(forbiddenList[type] || [], options.forbidden || []);
      result = _.intersection.apply(_, _.compact([_.keys(canonical), list]));

      result = _.difference(result, forbidden);

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
          // mapping audit to issue is not allowed,
          // but unmap can be possible
          'issue audit': !(options && options.isIssueUnmap)
        }),
        // NOTE: the names in every type pair must be sorted alphabetically!
        twoWay: Object.freeze({
          'audit program': true,
          'audit request': true,
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

    /**
     * Build string of assignees types separated by commas.
     * @param {Object} instance - Object instance
     * @return {String} assignees types separated by commas
     */
    getAssigneeType: function (instance) {
      let currentUser = GGRC.current_user;
      let roles = GGRC.access_control_roles
        .filter((item) => item.object_type === instance.type);
      let userType = null;

      if (!instance || !currentUser) {
        return;
      }

      _.each(roles, function (role) {
        let aclPerson = instance
          .access_control_list
          .filter((item) => item.ac_role_id === role.id &&
            item.person.id == currentUser.id);

        if (!aclPerson.length) {
          return;
        }

        userType = userType ? userType + ',' + role.name : role.name;
      });

      return userType;
    },
  };
})(jQuery, window.GGRC = window.GGRC || {}, moment,
  window.CMS = window.CMS || {});
