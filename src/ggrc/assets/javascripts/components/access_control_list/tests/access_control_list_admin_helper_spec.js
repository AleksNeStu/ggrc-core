/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

describe('GGRC.Components.accessControlListAdminHelper', function () {
  'use strict';

  var viewModel;

  beforeAll(function () {
    GGRC.access_control_roles = [
      {
        object_type: 'Assessment',
        id: 5,
        name: 'Admin'
      },
      {
        object_type: 'Control',
        id: 6,
        name: 'Primary Contact'
      }
    ];
  });

  afterAll(function () {
    delete GGRC.access_control_roles;
  });

  beforeEach(function () {
    viewModel = GGRC.Components
      .getViewModel('accessControlListAdminHelper');
  });

  describe('"addAdmin" method', function () {
    var instance;

    it('should add current user as admin', function () {
      instance = new CMS.Models.Assessment({id: 25});
      viewModel.attr('instance', instance);
      expect(instance.access_control_list).toBe(undefined);
      viewModel.addAdmin();
      expect(instance.access_control_list.length).toEqual(1);
      expect(instance.access_control_list[0].ac_role_id)
        .toEqual(5);
      expect(instance.access_control_list[0].person.id)
        .toEqual(1);
    });

    it('should not add current user as admin', function () {
      instance = new CMS.Models.Control({id: 25});
      viewModel.attr('instance', instance);
      expect(instance.access_control_list).toBe(undefined);
      viewModel.addAdmin();
      expect(instance.access_control_list).toBe(undefined);
    });
  });
});
