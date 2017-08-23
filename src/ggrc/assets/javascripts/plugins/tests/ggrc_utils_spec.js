/*!
  Copyright (C) 2017 Google Inc.
  Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

'use strict';

describe('GGRC utils allowed_to_map() method', function () {
  var allowedToMap;
  var fakeOptions;
  var fakeProgram;
  var fakeAudit;

  beforeAll(function () {
    allowedToMap = GGRC.Utils.allowed_to_map;
  });

  beforeEach(function () {
    fakeOptions = {};
  });

  describe('given an Audit and Program pair', function () {
    beforeEach(function () {
      fakeProgram = new CMS.Models.Program({type: 'Program'});
      fakeAudit = new CMS.Models.Audit({type: 'Audit'});

      spyOn(GGRC.Mappings, 'get_canonical_mapping_name')
        .and.returnValue('audits');

      spyOn(Permission, 'is_allowed_for').and.returnValue(true);
    });

    it('returns false for Audit as source and Program as target', function () {
      var result = allowedToMap(fakeAudit, fakeProgram, fakeOptions);
      expect(result).toBe(false);
    });

    it('returns false for Program as source and Audit as target', function () {
      var result = allowedToMap(fakeProgram, fakeAudit, fakeOptions);
      expect(result).toBe(false);
    });
  });

  describe('given a Person instance', function () {
    var origShortName;
    var otherInstance;
    var person;

    beforeAll(function () {
      origShortName = can.Model.shortName;
      can.Model.shortName = 'cacheable';
    });

    afterAll(function () {
      can.Model.shortName = origShortName;
    });

    beforeEach(function () {
      person = new CMS.Models.Person({type: 'Person'});
      otherInstance = new can.Model({type: 'Foo'});
    });

    it('returns false for any object', function () {
      var result = allowedToMap(otherInstance, person);
      expect(result).toBe(false);
    });
  });
});

describe('GGRC utils getMappableTypes() method', function () {
  var mapper;

  beforeAll(function () {
    var canonicalMappings = {};
    var OBJECT_TYPES = [
      'DataAsset', 'Facility', 'Market', 'OrgGroup', 'Vendor', 'Process',
      'Product', 'Project', 'System', 'Regulation', 'Policy', 'Contract',
      'Standard', 'Program', 'Issue', 'Control', 'Section', 'Clause',
      'Objective', 'Audit', 'Assessment', 'AccessGroup',
      'Document', 'Risk', 'Threat'
    ];
    mapper = GGRC.Utils.getMappableTypes;
    OBJECT_TYPES.forEach(function (item) {
      canonicalMappings[item] = {};
    });
    spyOn(GGRC.Mappings, 'get_canonical_mappings_for')
      .and.returnValue(canonicalMappings);
  });

  it('excludes the References type from the result', function () {
    var result = mapper('Reference');
    expect(_.contains(result, 'Reference')).toBe(false);
  });
  it('returns no results for Person', function () {
    var result = mapper('Person');
    expect(result.length).toBe(0);
  });
  it('returns no results for AssessmentTemplate', function () {
    var result = mapper('AssessmentTemplate');
    expect(result.length).toBe(0);
  });
  it('always returns whitelisted items', function () {
    var whitelisted = ['Hello', 'World'];
    var result = mapper('AssessmentTemplate', {
      whitelist: whitelisted
    });
    expect(_.intersection(result, whitelisted)).toEqual(whitelisted);
  });
  it('always remove forbidden items', function () {
    var forbidden = ['Policy', 'Process', 'Product', 'Program'];
    var list = mapper('DataAsset');
    var result = mapper('DataAsset', {
      forbidden: forbidden
    });
    expect(_.difference(list, result).sort()).toEqual(forbidden.sort());
  });
  it('always leave whitelisted and remove forbidden items', function () {
    var forbidden = ['Policy', 'Process', 'Product', 'Program'];
    var whitelisted = ['Hello', 'World'];
    var list = mapper('DataAsset');
    var result = mapper('DataAsset', {
      forbidden: forbidden,
      whitelist: whitelisted
    });
    var input = _.difference(list, result).concat(_.difference(result, list));
    var output = forbidden.concat(whitelisted);

    expect(input.sort()).toEqual(output.sort());
  });
});

describe('GGRC utils isMappableType() method', function () {
  it('returns false for Person and any type', function () {
    var result = GGRC.Utils.isMappableType('Person', 'Program');
    expect(result).toBe(false);
  });
  it('returns false for AssessmentTemplate and  any type', function () {
    var result = GGRC.Utils.isMappableType('AssessmentTemplate', 'Program');
    expect(result).toBe(false);
  });
  it('returns true for Program and Control', function () {
    var result = GGRC.Utils.isMappableType('Program', 'Control');
    expect(result).toBe(true);
  });
});

describe('GGRC utils peopleWithRoleName() method', function () {
  var instance;
  var method;  // the method under test
  var origRoleList;

  beforeAll(function () {
    method = GGRC.Utils.peopleWithRoleName;

    origRoleList = GGRC.access_control_roles;
    GGRC.access_control_roles = [
      {id: 5, name: 'Role A', object_type: 'Market'},
      {id: 9, name: 'Role A', object_type: 'Audit'},
      {id: 1, name: 'Role B', object_type: 'Market'},
      {id: 7, name: 'Role A', object_type: 'Policy'},
      {id: 3, name: 'Role B', object_type: 'Audit'},
      {id: 2, name: 'Role B', object_type: 'Policy'}
    ];
  });

  afterAll(function () {
    GGRC.access_control_roles = origRoleList;
  });

  beforeEach(function () {
    var acl = [
      {person: {id: 3}, ac_role_id: 1},
      {person: {id: 5}, ac_role_id: 3},
      {person: {id: 6}, ac_role_id: 9},
      {person: {id: 2}, ac_role_id: 3},
      {person: {id: 7}, ac_role_id: 9},
      {person: {id: 5}, ac_role_id: 2},
      {person: {id: 9}, ac_role_id: 9}
    ];

    instance = new can.Map({
      id: 42,
      type: 'Audit',
      'class': {model_singular: 'Audit'},
      access_control_list: acl
    });
  });

  it('returns users that have a role granted on a particular instance',
    function () {
      var result = method(instance, 'Role B');
      expect(result.map(function (person) {
        return person.id;
      }).sort()).toEqual([2, 5]);
    }
  );

  it('returns empty array if role name not found', function () {
    var result = method(instance, 'Role X');
    expect(result).toEqual([]);
  });

  it('returns empty array if no users are granted a particular role',
    function () {
      var result;

      instance.attr('type', 'Policy');
      instance.attr('class.model_singular', 'Policy');

      result = method(instance, 'Role A');

      expect(result).toEqual([]);
    }
  );
});

describe('GGRC utils resolveQueue() method', function () {
  var method;

  beforeAll(function () {
    method = GGRC.Utils.resolveQueue;
  });

  it('returns empty object if queue is empty', function () {
    var result = method([]);
    var expected = {};

    expect(result).toEqual(expected);
  });

  it('returns merged object if queue has objects', function () {
    var result = method([{a: 1}, {b: 2}, {a: 3}]);
    var expected = {
      a: 3,
      b: 2
    };

    expect(result).toEqual(expected);
  });

  it('returns object like first item of queue if queue has single item',
  function () {
    var result = method([{a: 1}]);
    var expected = {a: 1};

    expect(result).toEqual(expected);
    expect(result).not.toBe(expected);
  });

  it('does not modify original queue if a clean param is falsy', function () {
    var queue = [{a: 1}];
    var expectedQueue = queue.slice();

    method(queue);
    expect(queue).toEqual(expectedQueue);
  });

  it('clears original queue if clean param is truthy', function () {
    var queue = [{a: 1}];

    method(queue, true);
    expect(queue).toEqual([]);
  });
});
