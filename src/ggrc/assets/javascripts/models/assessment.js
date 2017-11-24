/*
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

import {prepareCustomAttributes} from '../plugins/utils/ca-utils';

(function (can, GGRC, CMS) {
  'use strict';

  can.Model.Cacheable('CMS.Models.Assessment', {
    root_object: 'assessment',
    root_collection: 'assessments',
    findOne: 'GET /api/assessments/{id}',
    findAll: 'GET /api/assessments',
    update: 'PUT /api/assessments/{id}',
    destroy: 'DELETE /api/assessments/{id}',
    create: 'POST /api/assessments',
    mixins: [
      'ownable', 'unique_title',
      'autoStatusChangeable', 'timeboxed', 'mapping-limit',
      'inScopeObjects', 'accessControlList', 'refetchHash',
      'issueTrackerIntegratable',
    ],
    is_custom_attributable: true,
    isRoleable: true,
    defaults: {
      assessment_type: 'Control',
      status: 'Not Started',
      send_by_default: true,  // notifications when a comment is added
      recipients: 'Assignees,Creators,Verifiers'  // user roles to be notified
    },
    statuses: ['Not Started', 'In Progress', 'In Review',
      'Verified', 'Completed', 'Deprecated', 'Rework Needed'],
    tree_view_options: {
      add_item_view: GGRC.mustache_path +
      '/base_objects/tree_add_item.mustache',
      attr_view: GGRC.mustache_path + '/base_objects/tree-item-attr.mustache',
      attr_list: [{
        attr_title: 'Title',
        attr_name: 'title',
        order: 1,
      }, {
        attr_title: 'State',
        attr_name: 'status',
        order: 2,
      }, {
        attr_title: 'Label',
        attr_name: 'label',
        order: 3,
      }, {
        attr_title: 'Verified',
        attr_name: 'verified',
        order: 4,
      }, {
        attr_title: 'Code',
        attr_name: 'slug',
        order: 5,
      }, {
        attr_title: 'Due Date',
        attr_name: 'start_date',
        order: 6,
      }, {
        attr_title: 'Created Date',
        attr_name: 'created_at',
        order: 7,
      }, {
        attr_title: 'Last Updated',
        attr_name: 'updated_at',
        order: 8,
      }, {
        attr_title: 'Last Updated By',
        attr_name: 'modified_by',
        order: 9,
      }, {
        attr_title: 'Verified Date',
        attr_name: 'verified_date',
        order: 10,
      }, {
        attr_title: 'Finished Date',
        attr_name: 'finished_date',
        order: 11,
      }, {
        attr_title: 'Last Deprecated Date',
        attr_name: 'end_date',
        order: 12,
      }, {
        attr_title: 'Reference URL',
        attr_name: 'reference_url',
        order: 13,
      }, {
        attr_title: 'Conclusion: Design',
        attr_name: 'design',
        order: 14,
      }, {
        attr_title: 'Conclusion: Operation',
        attr_name: 'operationally',
        order: 15,
      }, {
        attr_title: 'Archived',
        attr_name: 'archived',
        order: 16,
      }, {
        attr_title: 'Buganizer',
        attr_name: 'issue_url',
        order: 17,
        deny: !GGRC.ISSUE_TRACKER_ENABLED,
      }],
      display_attr_names: ['title', 'status', 'label', 'Assignees', 'Verifiers',
        'start_date', 'updated_at'],
    },
    sub_tree_view_options: {
      default_filter: ['Control'],
    },
    info_pane_options: {
    },
    confirmEditModal: {
      title: 'Confirm moving Assessment to "In Progress"',
      description: 'You are about to move Assessment from ' +
      '"{{status}}" to "In Progress" - are you sure about that?',
      button: 'Confirm'
    },
    conclusions: ['Effective', 'Ineffective', 'Needs improvement',
      'Not Applicable'],
    init: function () {
      if (this._super) {
        this._super.apply(this, arguments);
      }
      this.validatePresenceOf('audit');
      this.validateNonBlank('title');


      this.validate(
        'issue_tracker_title',
        function () {
          if (this.attr('can_use_issue_tracker') &&
            this.attr('issue_tracker.enabled') &&
            !this.attr('issue_tracker.title')) {
            return 'Enter Issue Title';
          }
        }
      );
      this.validate(
        'issue_tracker_component_id',
        function () {
          if (this.attr('can_use_issue_tracker') &&
            this.attr('issue_tracker.enabled') &&
            !this.attr('issue_tracker.component_id')) {
            return 'Enter Component ID';
          }
        }
      );
      this.validate(
        '_gca_valid',
        function () {
          if (!this._gca_valid) {
            return 'Missing required global custom attribute';
          }
        }
      );
    },
    prepareAttributes: function (attrs) {
      return attrs[this.root_object] ? attrs[this.root_object] : attrs;
    },
    /**
     * Assessment specific AJAX data parsing logic
     * @param {Object} attributes - hash of Model key->values
     * @return {Object} - parsed object with normalized data
     */
    parseModel: function (attributes) {
      var values;
      var definitions;
      attributes = this.prepareAttributes(attributes);
      values = attributes.custom_attribute_values || [];
      definitions = attributes.custom_attribute_definitions || [];

      if (!definitions.length) {
        return attributes;
      }

      attributes.custom_attribute_values =
        prepareCustomAttributes(definitions, values);
      return attributes;
    },
    model: function (attributes, oldModel) {
      var model;
      var id;
      var backup;
      if (!attributes) {
        return;
      }

      if (typeof attributes.serialize === 'function') {
        attributes = attributes.serialize();
      } else {
        attributes = this.parseModel(attributes);
      }

      id = attributes[this.id];
      if ((id || id === 0) && this.store[id]) {
        oldModel = this.store[id];
      }

      model = oldModel && can.isFunction(oldModel.attr) ?
        oldModel.attr(attributes) :
          new this(attributes);

      // Sometimes we are updating model partially and asynchronous
      // for example when we load relationships.
      // In this case we have to update backup to solve isDirty issues.
      backup = model._backupStore();
      if (backup) {
        _.extend(backup, attributes);
      }

      // This is a temporary solution
      if (attributes.documents) {
        model.attr('documents', attributes.documents, true);
      }

      return model;
    },
    /**
     * Replace Cacheble#findInCacheById method with the latest feature of can.Model - store
     * @param {String} id - Id of requested Model
     * @return {CMS.Models.Assessment} - already existing model
     */
    findInCacheById: function (id) {
      return this.store[id];
    }
  }, {
    init: function () {
      if (this._super) {
        this._super.apply(this, arguments);
      }
      this.bind('refreshInstance', this.refresh.bind(this));
    },
    _checkIssueTrackerWarnings: function () {
      let warnings;
      let warningMessage;

      if (!this.issue_tracker) {
        return;
      }

      warnings = this.issue_tracker._warnings;

      if (warnings && warnings.length) {
        warningMessage = warnings.join('; ');
        $(document.body).trigger('ajax:flash', {warning: warningMessage});
      }
    },
    after_update: function () {
      this._checkIssueTrackerWarnings();
    },
    after_create: function () {
      this._checkIssueTrackerWarnings();
    },
    before_create: function () {
      if (!this.audit) {
        throw new Error('Cannot save assessment, audit not set.');
      } else if (!this.audit.context) {
        throw new Error(
          'Cannot save assessment, audit context not set.');
      }
      this.attr('context', this.attr('audit.context'));
      this.attr('design', '');
      this.attr('operationally', '');
    },
    _transformBackupProperty: function (badProperties) {
      var backupInstance = this._backupStore();
      if (!backupInstance) {
        return;
      }
      badProperties.forEach(function (property) {
        if (!this[property] && !backupInstance[property] &&
        (this[property] !== backupInstance[property])) {
          backupInstance[property] = this[property];
        }
      }.bind(this));

      if (this.validate_assessor !== undefined) {
        backupInstance.validate_assessor = this.validate_assessor;
      }
      if (this.validate_creator !== undefined) {
        backupInstance.validate_creator = this.validate_creator;
      }
    },
    isDirty: function (checkAssociations) {
      this._transformBackupProperty(['design', 'operationally', '_disabled']);
      return this._super(checkAssociations);
    },
    form_preload: function (newObjectForm) {
      var pageInstance = GGRC.page_instance();
      var currentUser = CMS.Models.get_instance('Person',
        GGRC.current_user.id, GGRC.current_user);
      var auditLead;
      var self = this;

      if (pageInstance && (!this.audit || !this.audit.id || !this.audit.type)) {
        if (pageInstance.type === 'Audit') {
          this.attr('audit', pageInstance);
        } else if (this.scopeObject) {
          this.audit = this.scopeObject;
        }
      }

      if (!newObjectForm) {
        return;
      }

      // Make sure before create is called before save
      this.before_create();

      if (this.audit) {
        const auditors = this.audit.findRoles('Auditors');
        const auditCaptains = this.audit.findRoles('Audit Captains');

        this.initCanUseIssueTracker(this.audit.issue_tracker);

        markForAddition(this, currentUser, 'Creators');
        auditCaptains.forEach((item) => {
          markForAddition(this, item.person, 'Assignees');
        });
        auditors.forEach((item) => {
          markForAddition(this, item.person, 'Verifiers');
        });
      }

      function markForAddition(instance, user, type) {
        var rolesNames = type.split(',');
        var roles = GGRC.access_control_roles;
        var acl = instance.attr('access_control_list');

        rolesNames.forEach((roleName) => {
          var role = _.head(
            roles.filter((role) =>
              role.object_type === 'Assessment' &&
              role.name === roleName)
          );

          if (role) {
            acl.push({
              ac_role_id: role.id,
              person: {
                id: user.id,
              },
              person_id: user.id,
            });
          }
        });
      }
    },
    refresh: function () {
      var dfd;
      var href = this.selfLink || this.href;
      var that = this;

      if (!href) {
        return can.Deferred().reject();
      }
      if (!this._pending_refresh) {
        this._pending_refresh = {
          dfd: can.Deferred(),
          fn: _.throttle(function () {
            var dfd = that._pending_refresh.dfd;
            can.ajax({
              url: href,
              type: 'get',
              dataType: 'json'
            })
          .then(function (model) {
            delete that._pending_refresh;
            if (model) {
              model = CMS.Models.Assessment.model(model, that);
              model.backup();
              return model;
            }
          })
          .done(function () {
            dfd.resolve.apply(dfd, arguments);
          })
          .fail(function () {
            dfd.reject.apply(dfd, arguments);
          });
          }, 300, {trailing: false})
        };
      }
      dfd = this._pending_refresh.dfd;
      this._pending_refresh.fn();
      return dfd;
    },
    info_pane_preload: function () {
      this.refresh();
    }
  });
})(window.can, window.GGRC, window.CMS);
