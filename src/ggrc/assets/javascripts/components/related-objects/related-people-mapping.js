/*!
  Copyright (C) 2017 Google Inc.
  Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

import '../people/deletable-people-group';
import '../people/editable-people-group';

(function (can) {
  'use strict';

  GGRC.Components('relatedPeopleMapping', {
    tag: 'related-people-mapping',
    viewModel: {
      mapping: null,
      required: '@',
      type: null,
      heading: null,
      mapped_people: [],
      results: [],
      list_pending: [],
      list_mapped: [],
      computed_mapping: false,
      _EV_BEFORE_EDIT: 'before-edit',
      editableMode: false,
      isLoading: false,
      validation: {mandatory: true, empty: true, valid: true},
      roleConflicts: false,

      backUpPendings: [],
      saveChanges: function () {
        var instance = this.attr('instance');
        var self = this;
        this.attr('editableMode', false);

        if (this.attr('instance._pending_joins').length) {
          this.attr('isLoading', true);
          instance.constructor.resolve_deferred_bindings(instance)
            .then(function (data) {
              instance.dispatch('refreshInstance');
              self.updateResult();
              self.attr('isLoading', false);
              self._checkConflict();
            });
        }
      },
      changeEditableGroup: function (args) {
        var pendingJoins = this.attr('instance._pending_joins');

        if (args.editableMode) {
          this.attr('editableMode', true);
          this.attr('backUpPendings').replace(pendingJoins);
        } else {
          this.attr('editableMode', false);
          pendingJoins.replace(this.attr('backUpPendings'));
          this.updateResult();
        }
      },
      personSelected: function (args) {
        this.addRole(args.person, args.groupId);
      },
      addRole: function (person, groupId) {
        var self = this;
        var role = can.capitalize(groupId);
        this.attr('isLoading', true);
        this.deferred_add_role(person, role).then(function () {
          self.updateResult();
          self.attr('isLoading', false);
        });
      },
      removeRole: function (args) {
        var self = this;
        var person = args.person;
        var role = can.capitalize(args.groupId);
        this.attr('isLoading', true);
        this.deferred_remove_role(person, role).then(function () {
          self.updateResult();
          self.attr('isLoading', false);
        });
      },

      /*
       * Checks whether there are any conflicts between assignable roles.
       *
       * If `conflicts` is specified on an object with assignable mixin,
       * bind to the role's mapping and on any change to it check if any
       * user is holding roles that are in violation of the rules.
       *
       * @prop {Array of Arrays} conflicts - Array of an array containing
       *  conflicting roles that no single user should hold at the same time.
       * @prop {Array of objects} assignable_list - A list of available roles
       *  with mappins to those roles.
       */
      _checkConflict: function () {
        var conflicts = this.instance.class.conflicts;
        var assignableList = this.instance.class.assignable_list;
        var bindings = {};

        if (_.isUndefined(conflicts)) {
          return;
        }

        function checkConflicts() {
          // Verify that there is not intersections between role bindings and
          // show warning if it exists.
          _.each(conflicts, function (conflictRoles) {
            var rolePeople = _.map(conflictRoles, function (role) {
              return _.map(bindings[role].list, function (person) {
                return person.instance.id;
              });
            });
            var hasConflicts = !_.isEmpty(
                _.intersection.apply(null, rolePeople));
            this.attr('roleConflicts', hasConflicts);
          }.bind(this));
        }

        // Set up listening to change event on role bindings.
        _.each(conflicts, function (conflictRoles) {
          _.each(conflictRoles, function (role) {
            var roleMapping = _.find(
              assignableList, _.matchesProperty('type', role)).mapping;
            var roleBinding = this.instance.get_binding(roleMapping);
            bindings[role] = roleBinding;
            roleBinding.list.bind('change', checkConflicts.bind(this));
          }.bind(this));
        }.bind(this));
        checkConflicts.call(this);
      },

      /**
        * Get people mapped to this instance
        *
        * @return {Promise} - a promise that returns the list of current mapped people
        */
      get_mapped_deferred: function () {
        // We call get_mapping only once because canjs events can get caught in a loop
        // computed_mapping needs to be in scope so its separated from other people lists
        if (!this.computed_mapping) {
          return this.attr('instance')
            .get_mapping_deferred(this.attr('mapping'))
            .then(function (data) {
              this.attr('list_mapped', data);
              this.computed_mapping = true;
              return data;
            }.bind(this));
        }
        return $.when(this.attr('list_mapped'));
      },
      /**
        * Get the first (or only) pending join for a person
        *
        * @param {CMS.Models.Person} person - the person whose join to get
        *
        * @return {Object} - the pending join for the person if available
        *                    or undefined
        */
      get_pending_operation: function (person) {
        return _.find(this.attr('instance._pending_joins'), function (join) {
          return join.what === person;
        });
      },

      /**
        * Change pending joins list to add a role to a person
        *
        * If there is a pending 'add' or 'update', extends roles list in it.
        * If there is a pending 'remove', cancels it and creates a new 'update'
        * with the role.
        * If there is no pending join and the person already has roles assigned,
        * creates a new 'update' with extended roles list.
        * If there is no pending join and the person has no roles assigned yet,
        * creates a new 'add' with the role.
        *
        * @param {CMS.Models.Person} person - the person who gets the new role
        * @param {String} role - the role that is added
        *
        * @return {Object} - dfd
        */
      deferred_add_role: function (person, role) {
        var dfd = new can.Deferred();
        var pendingOperation = this.get_pending_operation(person);
        if (!pendingOperation) {
          // no pending join for this person
          this.get_roles(person, this.instance).then(function (result) {
            var roles = result.roles;

            if (roles.length) {
              // the person already has roles assigned, create 'update'
              this.add_or_replace_operation(
                person,
                {
                  how: 'update',
                  roles: _.union(roles, [role])
                }
              );
            } else {
              // the person was not yet assigned, create 'add'
              this.add_or_replace_operation(
                person,
                {
                  how: 'add',
                  roles: [role]
                }
              );
            }

            dfd.resolve();
          }.bind(this));
        } else if (pendingOperation.how === 'remove') {
          // 'remove' pending for this person, cancel it and create 'update'
          // with single role
          this.add_or_replace_operation(
            person,
            {
              how: 'update',
              roles: [role]
            }
          );
          dfd.resolve();
        } else if (pendingOperation.how === 'add' ||
                   pendingOperation.how === 'update') {
          // 'add' or 'update' pending, extend the roles list with the role
          this.add_or_replace_operation(
            person,
            {
              how: pendingOperation.how,
              roles: _.union(this.parse_roles_list(pendingOperation), [role])
            }
          );
          dfd.resolve();
        }

        return dfd;
      },

      /**
        * Change pending joins list to remove a role from a person
        *
        * If there is a pending 'add' or 'update', cancels this role addition.
        * If there is a pending 'remove', does nothing.
        * If there is no pending join and the person has several roles assigned,
        * creates a new 'update' with all stored roles except the role.
        * If there is no pending join and the person has a single role assigned,
        * creates a new 'remove'.
        *
        * @param {CMS.Model.Person} person - the person who loses the role
        * @param {String} role - the role that is removed
        *
        * @return {Object} - dfd
        */
      deferred_remove_role: function (person, role) {
        var pendingOperation = this.get_pending_operation(person);
        var roles;
        var dfd = new can.Deferred();

        if (!pendingOperation) {
          // no pending join for this person
          this.get_roles(person, this.instance).then(function (result) {
            var roles = result.roles;

            roles = _.without(roles, role);
            if (roles.length) {
              // there are still roles remaining, create 'update'
              this.add_or_replace_operation(
                person,
                {
                  how: 'update',
                  roles: roles
                }
              );
            } else {
              // there are no roles remaining, create 'remove'
              this.add_or_replace_operation(
                person,
                {
                  how: 'remove'
                }
              );
            }

            dfd.resolve();
          }.bind(this));
        } else if (pendingOperation.how === 'remove') {
          // no action required
          dfd.resolve();
          return;
        } else if (pendingOperation.how === 'add' ||
                   pendingOperation.how === 'update') {
          // 'add' or 'update' pending, cancel the role addition
          roles = this.parse_roles_list(pendingOperation);
          roles = _.without(roles, role);
          if (roles.length) {
            // update the roles list in the pending join
            this.add_or_replace_operation(
              person,
              {
                how: pendingOperation.how,
                roles: roles
              }
            );
          } else if (pendingOperation.how === 'add') {
            // cancel the pending 'add'
            this.add_or_replace_operation(
              person,
              null
            );
          } else if (pendingOperation.how === 'update') {
            // replace the 'update' with 'remove'
            this.add_or_replace_operation(
              person,
              {
                how: 'remove'
              }
            );
          }

          dfd.resolve();
        }

        return dfd;
      },
      /**
        * Add a new pending join, remove all pending joins for same person
        *
        * @param {CMS.Model.Person} person - the person to be joined
        * @param {Object} operation - a description of the new pending join;
        * if operation is false-value, all pending joins would be removed,
        * but none will be added.
        * @param {String} operation.how - the type of the operation
        * ('add', 'remove' or 'update')
        * @param {String} operation.roles - the list of added/updated roles
        */
      add_or_replace_operation: function (person, operation) {
        var roles;
        if (!operation) {
          // just remove all pending joins for person
          this.instance.remove_duplicate_pending_joins(person);
        } else {
          // convert roles list to a string
          if (_.isArray(operation.roles)) {
            roles = operation.roles.join(',');
          }
          if (operation.how === 'add') {
            this.instance.mark_for_addition(
              'related_objects_as_destination',
              person,
              {
                attrs: {
                  AssigneeType: roles
                },
                context: this.instance.context
              }
            );
          } else if (operation.how === 'update') {
            this.instance.mark_for_update(
              'related_objects_as_destination',
              person,
              {
                attrs: {
                  AssigneeType: roles
                }
              }
            );
          } else if (operation.how === 'remove') {
            this.instance.mark_for_deletion(
              'related_objects_as_destination',
              person
            );
          }
        }
      },
      /**
        * Get roles list from a pending join and split it into a list.
        *
        * Returns [] if no roles list exists.
        *
        * @param {Object} operation - a pending join object
        *
        * @return {Array} - an array of roles
        */
      parse_roles_list: function (operation) {
        var roles = _.exists(operation, 'extra.attrs.AssigneeType');
        return roles ? roles.split(',') : [];
      },
      /**
        * Get saved roles list for a person
        *
        * @param {CMS.Models.Person} person - the person whose roles to get
        * @param {Object} instance - the object to which the person is assigned
        *
        * @return {jQuery.Deferred} - a promise with the role list
        */
      get_roles: function (person, instance) {
        var rolesDfd = $.Deferred();

        CMS.Models.Relationship
          .getRelationshipBetweenInstances(person, instance, true)
          .done(function (relationships) {
            var found = false;
            _.map(relationships, function (relationship) {
              if (!found && _.exists(relationship, 'attrs.AssigneeType')) {
                found = true;
                relationship.refresh().then(function (relationship) {
                  var roles = relationship.attrs.AssigneeType.split(',');
                  var result = {roles: roles,
                    relationship: relationship};
                  rolesDfd.resolve(result);
                });
              }
            });
            if (!found) {
              rolesDfd.resolve({roles: []});
            }
          })
          .fail(function (e) {
            rolesDfd.resolve({roles: []});
          });

        return rolesDfd;
      },
      /**
        * Trigger Assessment state changing confirmation modal display
        *
        * @return {can.Deferred} - a promise with the state changing confirmation
        */
      confirmEdit: function () {
        var confirmation;

        confirmation = this.$rootEl.triggerHandler({
          type: this._EV_BEFORE_EDIT
        });
        return confirmation;
      },
      /**
        * Hides controls for editing People in Assessment Attributes
        *
        * Called with a person-add hiding button
        */
      disableEdit: function () {
        this.attr('isEdit', false);
      },
      setRoles: function () {
        this.get_mapped_deferred().then(function (data) {
          this.attr('list_pending',
            this.attr('instance._pending_joins'));
          this.attr('list_mapped', data);
          this.updateMappedResult(data);
          if (!this.attr('required')) {
            return;
          }
          this.attr('mapped_people', data);
          if (this.instance.isNew() && this.validate) {
            this.validate();
          }
        }.bind(this));
      },
      validate: function () {
        if (!(this.required && this.validate)) {
          return;
        }
        this.attr('instance').attr('validate_' +
          this.attr('type'), !!this.results.length);
      },
      updateMappedResult: function (data) {
        var type = can.capitalize(this.type);
        var mapped = _.map(data, function (item) {
          return item.instance;
        });
        var pending = _.filter(
          this.attr('instance._pending_joins'), function (item) {
            return item.what.type === 'Person';
          });
        var added = _.filter(pending, function (item) {
          // any person who has `type` in their `add` or `update` roles list
          var roles = this.parse_roles_list(item);
          return (item.how === 'add' || item.how === 'update') &&
            _.includes(roles, type);
        }.bind(this));
        var removed = _.filter(pending, function (item) {
          // any person who was mapped and has `remove` join or has no `type`
          // in their `update` roles list
          var roles = this.parse_roles_list(item);
          var personMapped = _.find(mapped, function (map) {
            return map.id === item.what.id;
          });
          return personMapped &&
            (item.how === 'remove' ||
             item.how === 'update' && !_.includes(roles, type));
        }.bind(this));

        function getInstances(arr) {
          return _.map(arr, function (item) {
            return item.what;
          });
        }
        this.instance.attr('_disabled', 'disabled');
        added = getInstances(added);
        removed = getInstances(removed);
        this.attr('results').replace(
          _.union(_.filter(mapped, function (item) {
            return !_.findWhere(removed, {id: item.id});
          }
        ), added));
        this.instance.attr('_disabled', '');
      },
      updateResult: function () {
        this.get_mapped_deferred().then(function (data) {
          this.updateMappedResult(data);
        }.bind(this));
      }
    },
    events: {
      inserted: function (el) {
        this.viewModel.setRoles();
        this.viewModel._checkConflict();
      },
      validate: function () {
        if (!(this.viewModel.required && this.viewModel.validate)) {
          return;
        }
        this.viewModel.attr('instance').attr('validate_' +
          this.viewModel.attr('type'), !!this.viewModel.results.length);
      },
      updateResult: function () {
        this.viewModel.updateResult();
      },
      '{viewModel.list_mapped} change': 'updateResult',
      '{viewModel.list_pending} change': 'updateResult',
      '{viewModel.results} change': 'validate',
      '{viewModel.instance} modal:dismiss': function () {
        this.viewModel.attr('instance').removeAttr(
          'validate_' + this.viewModel.attr('type'));
      },
      'modal:success': function () {
        // prevent navigating to a new object page when a new user is created
        return false;
      }
    }
  });
})(window.can);
