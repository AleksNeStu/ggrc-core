/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (GGRC) {
  'use strict';

  GGRC.Components('accessControlListAdminHelper', {
    tag: 'access-control-list-admin-helper',

    viewModel: {
      instance: {},
      isNewInstance: false,
      addAdmin: function () {
        var instance = this.attr('instance');
        var adminRole = _.filter(GGRC.access_control_roles, {
          object_type: instance.class.model_singular,
          name: 'Admin'
        });

        if (!adminRole.length) {
          return;
        }

        if (!instance.attr('access_control_list')) {
          instance.attr('access_control_list', []);
        }

        // Use push because ACL is subscribed on change event.
        instance.attr('access_control_list').push({
          ac_role_id: adminRole[0].id,
          person: {type: 'Person', id: GGRC.current_user.id}
        });
      }
    },
    events: {
      inserted: function () {
        if (this.viewModel.attr('isNewInstance')) {
          this.viewModel.addAdmin();
        }
      }
    }
  });
})(window.GGRC);
