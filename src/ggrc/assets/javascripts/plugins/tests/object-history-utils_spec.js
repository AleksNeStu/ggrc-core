/*
  Copyright (C) 2017 Google Inc.
  Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

import {
  buildRoleACL,
} from '../../plugins/utils/object-history-utils';

describe('"buildModifiedACL" method', () => {
  it('should not add duplicates', () => {
    const currentAcl = [
      {ac_role_id: 5, person_id: 3},
      {ac_role_id: 5, person_id: 20},
    ];
    const modifiedRole = {
      added: [{id: 20}, {id: 30}],
      deleted: [],
    };

    const result = buildRoleACL(5, currentAcl, modifiedRole);
    expect(result.length).toBe(3);
  });

  it('should delete 2 items', () => {
    const currentAcl = [
      {ac_role_id: 5, person_id: 3},
      {ac_role_id: 5, person_id: 20},
    ];
    const modifiedRole = {
      added: [],
      deleted: [{id: 20}, {id: 30}, {id: 3}],
    };

    const result = buildRoleACL(5, currentAcl, modifiedRole);
    expect(result.length).toBe(0);
  });

  it('should add all modified people. current ACL is empty', () => {
    const currentAcl = [];
    const modifiedRole = {
      added: [
        {id: 20, email: 'akali@google.com'},
        {id: 30, email: 'twitch@google.com'},
      ],
      deleted: [],
    };

    const result = buildRoleACL(5, currentAcl, modifiedRole);
    expect(result.length).toBe(2);
    expect(result[0].person_email).toEqual('akali@google.com');
    expect(result[1].person_id).toEqual(30);
  });

  it('should add 1 item and remove 2 items', () => {
    const currentAcl = [
      {ac_role_id: 5, person_id: 3},
      {ac_role_id: 5, person_id: 20},
    ];
    const modifiedRole = {
      added: [{id: 25}],
      deleted: [{id: 20}, {id: 3}],
    };

    const result = buildRoleACL(5, currentAcl, modifiedRole);
    expect(result.length).toBe(1);
    expect(result[0].person_id).toEqual(25);
  });
});
