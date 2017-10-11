/*!
  Copyright (C) 2017 Google Inc.
  Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

import './related-people-access-control-group';

(function (can, _, GGRC) {
  'use strict';

  GGRC.Components('relatedPeopleAccessControl', {
    tag: 'related-people-access-control',
    viewModel: {
      instance: {},
      includeRoles: [],
      groups: [],
      updatableGroupId: null,
      isNewInstance: false,

      updateRoles: function (args) {
        this.updateAccessContolList(args.people, args.roleId);
        this.dispatch({
          type: 'saveCustomRole',
          groupId: args.roleId
        });
      },
      updateAccessContolList: function (people, roleId) {
        var instance = this.attr('instance');

        // remove all people with current role
        var listWithoutRole = instance
          .attr('access_control_list').filter(function (item) {
            return item.ac_role_id !== roleId;
          });

        // push update people with current role
        people.forEach(function (person) {
          listWithoutRole.push({
            ac_role_id: roleId,
            person: {id: person.id, type: 'Person'}
          });
        });

        instance.attr('access_control_list')
          .replace(listWithoutRole);
      },

      buildGroups: function (role, roleAssignments) {
        var includeRoles = this.attr('includeRoles');
        var groupId = role.id;
        var title = role.name;
        var group;
        var people;

        if (includeRoles.length && includeRoles.indexOf(title) === -1) {
          return;
        }

        group = roleAssignments[groupId];
        people = group ?
          group.map(function (groupItem) {
            return {
              id: groupItem.person.id,
              type: 'Person'
            };
          }) :
          [];

        return {
          title: title,
          groupId: groupId,
          people: people,
          required: role.mandatory
        };
      },
      getRoleList: function () {
        var roleAssignments;
        var roles;
        var groups;
        var instance = this.attr('instance');

        if (!instance) {
          this.attr('rolesInfo', []);
          return;
        }

        roleAssignments = _.groupBy(instance
          .attr('access_control_list'), 'ac_role_id');

        roles = _.filter(GGRC.access_control_roles, {
          object_type: instance.class.model_singular
        });

        groups = _.map(roles, function (role) {
          return this.buildGroups(role, roleAssignments);
        }.bind(this))
        .filter(function (group) {
          return typeof group !== 'undefined';
        })
        // sort by required
        .sort(function (a, b) {
          if (a.required === b.required) {
            return 0;
          }

          return a.required ? -1 : 1;
        });

        return groups;
      }
    },
    events: {
      refreshGroups: function () {
        this.viewModel.attr('groups',
          this.viewModel.getRoleList());
      },
      inserted: function () {
        this.refreshGroups();
      },
      '{viewModel.instance.access_control_list} change':
      function () {
        this.refreshGroups();
      }
    }
  });
})(window.can, window._, window.GGRC);
