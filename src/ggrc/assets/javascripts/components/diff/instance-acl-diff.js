/*
 Copyright (C) 2017 Google Inc., authors, and contributors
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

import {buildModifiedACL} from '../../plugins/utils/object-history-utils';
import {REFRESH_PROPOSAL_DIFF} from '../../events/eventTypes';
import DiffBaseVM from './diff-base-vm';
import template from './templates/instance-diff-items.mustache';
const tag = 'instance-acl-diff';

const viewModel = DiffBaseVM.extend({
  modifiedAcl: {},

  buildDiffObject() {
    const modifiedRoles = this.attr('modifiedAcl');
    const instance = this.attr('currentInstance');
    const currentAcl = instance.attr('access_control_list');
    const modifiedAcl = buildModifiedACL(instance, modifiedRoles);

    const rolesDiff = can.Map.keys(modifiedRoles).map((roleId) => {
      let currentVal;
      let modifiedVal;

      // convert to number
      roleId = Number(roleId);
      const currentRoleAcl = this.getRoleACL(currentAcl, roleId);
      const modifiedRoleAcl = this.getRoleACL(modifiedAcl, roleId);

      const role = _.first(
        GGRC.access_control_roles.filter((item) => item.id === roleId)
      );

      if (!role) {
        return;
      }

      modifiedVal = this.getEmailsOrEmpty(modifiedRoleAcl);
      currentVal = this.getEmailsOrEmpty(currentRoleAcl);

      return {
        attrName: role.name,
        currentVal,
        modifiedVal,
      };
    }).filter((diff) => !!diff);

    this.attr('diff', rolesDiff);
  },
  getRoleACL(acl, roleId) {
    return acl
      .filter((aclItem) => aclItem.ac_role_id === roleId)
      .map((aclItem) => {
        return {
          id: aclItem.person_id,
          email: aclItem.person_email,
        };
      });
  },
  getEmailsOrEmpty(value) {
    if (!value || !value.length) {
      return [this.attr('emptyValue')];
    }

    return value.map((item) => item.email).sort();
  },
});

export default can.Component.extend({
  tag,
  template,
  viewModel: viewModel,
  events: {
    buildDiff() {
      const instance = this.viewModel.attr('currentInstance');
      const modifiedACL = this.viewModel.attr('modifiedAcl');

      if (!instance || !modifiedACL) {
        return;
      }
      this.viewModel.buildDiffObject();
    },
    inserted() {
      this.buildDiff();
    },
    [`{viewModel.currentInstance} ${REFRESH_PROPOSAL_DIFF.type}`]() {
      this.buildDiff();
    },
  },
});
