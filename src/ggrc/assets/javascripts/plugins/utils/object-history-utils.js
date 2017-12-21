/*
  Copyright (C) 2017 Google Inc.
  Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

// #region ACL
const buildAclObject = (person, roleId) => {
  return {
    ac_role_id: roleId,
    person: {
      id: person.id,
    },
    person_id: person.id,
    person_email: person.email,
  };
};

const buildRoleACL = (modifiedRoleId, currentRoleACL, modifiedRole) => {
  let shouldBeAdded;
  let modifiedRoleACL;

  // people list for current role is empty. return only added
  if (!currentRoleACL || !currentRoleACL.length) {
    modifiedRoleACL = modifiedRole.added.map((person) =>
      buildAclObject(person, modifiedRoleId));

    return modifiedRoleACL;
  }

  // copy 'currentRoleACL' array
  modifiedRoleACL = currentRoleACL.slice();

  shouldBeAdded = modifiedRole.added.filter((person) =>
    _.findIndex(currentRoleACL, {person_id: person.id}) === -1
  ).map((person) => buildAclObject(person, modifiedRoleId));

  // add new people
  modifiedRoleACL.push(...shouldBeAdded);

  // remove existed people
  _.remove(modifiedRoleACL, (aclItem) =>
    _.findIndex(modifiedRole.deleted, {id: aclItem.person_id}) > -1
  );

  return modifiedRoleACL;
};

const buildModifiedACL = (instance, modifiedRoles) => {
  const modifiedRolesKeys = can.Map.keys(modifiedRoles)
    .map((key) => Number(key));
  const modifiedAcl = [];
  let aclRoles;
  let allRoles = [];

  if (!modifiedRolesKeys.length) {
    return instance.access_control_list;
  }

  aclRoles = _.groupBy(instance.access_control_list, 'ac_role_id');
  allRoles = _.union(
    _.keys(aclRoles).map((key) => Number(key)),
    modifiedRolesKeys
  );

  allRoles.forEach((roleId) => {
    if (modifiedRolesKeys.indexOf(roleId) === -1) {
      modifiedAcl.push(...aclRoles[roleId]);
    } else {
      const roleAcl =
        buildRoleACL(roleId, aclRoles[roleId], modifiedRoles[roleId]);

      modifiedAcl.push(...roleAcl);
    }
  });

  return modifiedAcl;
};
// #endregion

// #region list-fields
const buildModifiedListField = (currentField, modifiedItem) => {
  let modifiedField;

  if (!currentField) {
    currentField = [];
  }

  modifiedField = currentField.slice();

  modifiedItem.added.forEach((item) => {
    const index = _.findIndex(modifiedField, {id: item.id});

    if (!item.hasOwnProperty('display_name')) {
      item.display_name = item.title || item.name;
    }

    if (index > -1) {
      // replace item because current field item can be stub
      modifiedField[index] = item;
    } else {
      modifiedField.push(item);
    }
  });

  // remove deleted items
  _.remove(modifiedField, (item) =>
    _.findIndex(modifiedItem.deleted, {id: item.id}) > -1);

  return modifiedField;
};
// #endregion

// #region GCA
const getValueAndDefinition = (values, definitions, attrId) => {
  const value = values
    .find((val) => val.custom_attribute_id === attrId);
  const definition = definitions
    .find((def) => def.id === attrId);

  return {
    value: value,
    def: definition,
  };
};

const getModifiedValue = (modifiedAttr, attr) => {
  const isPerson = attr.def.attribute_type === 'Map:Person';
  const contentProperty = isPerson ? 'attribute_object' : 'attribute_value';
  let value = attr.value;

  if (!modifiedAttr || !modifiedAttr.hasOwnProperty(contentProperty)) {
    return value;
  }

  if (value && value.hasOwnProperty(contentProperty)) {
    value[contentProperty] = modifiedAttr[contentProperty];
  } else {
    value = {
      [contentProperty]: modifiedAttr[contentProperty],
      custom_attribute_id: attr.def.id,
    };
  }

  if (isPerson && value.attribute_object) {
    value.attribute_object_id = value.attribute_object.id;
  }

  return value;
};

const buildModifiedAttValues = (values, definitions, modifiedAttrs) => {
  // convert to string.
  const valueKeys = values.map((val) => `${val.custom_attribute_id}`);
  const caKeys = can.Map.keys(modifiedAttrs);
  const modifiedValues = _.union(valueKeys, caKeys).map((attrId) => {
    let attr;
    let modifiedAttr;
    attrId = Number(attrId);

    attr = getValueAndDefinition(values, definitions, attrId);
    modifiedAttr = modifiedAttrs[attrId];

    // attr was deleted
    if (!attr.def) {
      return;
    }

    return getModifiedValue(modifiedAttr, attr);
  })
  .filter((value) => !!value);

  return modifiedValues;
};
// #endregion

export {
  buildRoleACL,
  buildModifiedACL,
  buildModifiedListField,
  buildModifiedAttValues,
};
