/*
  Copyright (C) 2017 Google Inc.
  Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

describe('CMS.Models.Assessment', function () {
  'use strict';

  describe('before_create() method', function () {
    var assessment;
    var audit;
    var auditWithoutContext;
    var context;
    var program;

    beforeEach(function () {
      assessment = new CMS.Models.Assessment();
      context = new CMS.Models.Context({id: 42});
      program = new CMS.Models.Program({id: 54});
      audit = new CMS.Models.Audit({context: context, program: program});
      auditWithoutContext = new CMS.Models.Audit({program: program});
    });

    it('sets the program and context properties', function () {
      assessment.attr('audit', audit);
      assessment.before_create();
      expect(assessment.context.id).toEqual(context.id);
    });

    it('throws an error if audit is not defined', function () {
      expect(function () {
        assessment.before_create();
      }).toThrow(new Error('Cannot save assessment, audit not set.'));
    });

    it('throws an error if audit program/context are not defined', function () {
      assessment.attr('audit', auditWithoutContext);
      expect(function () {
        assessment.before_create();
      }).toThrow(new Error(
        'Cannot save assessment, audit context not set.'));
    });
    it('sets empty string to design property', function () {
      assessment.attr('audit', audit);
      assessment.attr('design', undefined);
      assessment.before_create();
      expect(assessment.attr('design')).toEqual('');
    });
    it('sets empty string to operationally property', function () {
      assessment.attr('audit', audit);
      assessment.attr('operationally', undefined);
      assessment.before_create();
      expect(assessment.attr('operationally')).toEqual('');
    });
  });

  describe('_transformBackupProperty() method', function () {
    var assessment;

    beforeEach(function () {
      assessment = new CMS.Models.Assessment();
    });
    it('does nothing if no backup of instance', function () {
      assessment.attr('name', '');
      assessment._transformBackupProperty(['name']);
      expect(assessment.attr('name')).toEqual('');
    });
    it('transforms backups property if it is falsy in instance and in backup' +
    'but not equal', function () {
      assessment.attr('name', '');
      assessment.backup();
      assessment._backupStore().name = null;
      assessment._transformBackupProperty(['name']);
      expect(assessment._backupStore().name).toEqual('');
    });
    it('updates validate_assessor in backup if it is define in instance',
      function () {
        assessment.backup();
        assessment.attr('validate_assessor', true);
        assessment._backupStore().validate_assessor = undefined;
        assessment._transformBackupProperty(['name']);
        expect(assessment._backupStore().validate_assessor).toEqual(true);
      });
    it('updates validate_creator in backup if it is define in instance',
      function () {
        assessment.backup();
        assessment.attr('validate_creator', true);
        assessment._backupStore().validate_creator = undefined;
        assessment._transformBackupProperty(['name']);
        expect(assessment._backupStore().validate_creator).toEqual(true);
      });
  });
  describe('isDirty() method', function () {
    var assessment;

    beforeEach(function () {
      assessment = new CMS.Models.Assessment();
      spyOn(assessment, '_transformBackupProperty')
        .and.callThrough();
    });
    it('calls _transformBackupProperty() with specified arguments',
      function () {
        assessment.isDirty();
        expect(assessment._transformBackupProperty)
          .toHaveBeenCalledWith(['design', 'operationally', '_disabled']);
      });
    it('returns result of inherited function, true if instance is dirty',
      function () {
        var result;
        assessment.attr('name', 'assessment1');
        assessment.backup();
        assessment.attr('name', 'assessment1.1');
        result = assessment.isDirty();
        expect(result).toEqual(true);
      });
    it('returns result of inherited function, false if instance is not dirty',
      function () {
        var result;
        assessment.attr('name', 'assessment1');
        assessment.backup();
        result = assessment.isDirty();
        expect(result).toEqual(false);
      });
  });

  describe('model() method', function () {
    it('does not update backup if backup was not created', function () {
      spyOn(_, 'extend');
      CMS.Models.Assessment.model({data: 'test'}, new CMS.Models.Assessment());
      expect(_.extend).not.toHaveBeenCalled();
    });

    it('updates backup if backup was created', function () {
      var model = new CMS.Models.Assessment();
      model.backup();
      CMS.Models.Assessment.model({data: 'test'}, model);
      expect(model._backupStore().data).toBe('test');
    });
  });

  describe('form_preload() method', function () {

    function checkAcRoles(model, roleId, peopleIds) {
      const res = can.makeArray(model.access_control_list).filter((acl) => {
        return acl.ac_role_id === roleId;
      }).map((acl) => {
        return acl.person.id;
      }).sort();
      expect(res).toEqual(peopleIds);
    }

    beforeAll(function () {
      GGRC.access_control_roles = [
        {id: 1, name: 'Admin', object_type: 'Assessment'},
        {id: 2, name: 'Admin', object_type: 'Vendor'},
        {id: 4, name: 'Secondary Contacts', object_type: 'Assessment'},
        {id: 5, name: 'Principal Assignees', object_type: 'Control'},
        {id: 7, name: 'Secondary Assignees', object_type: 'Assessment'},
        {id: 10, name: 'Creators', object_type: 'Assessment'},
        {id: 11, name: 'Assignees', object_type: 'Assessment'},
        {id: 12, name: 'Verifiers', object_type: 'Assessment'},
      ];
    });

    afterAll(function () {
      delete GGRC.access_control_roles;
    });

    it('populates access control roles based on audit roles', function () {
      var model = new CMS.Models.Assessment();
      spyOn(model, 'before_create');

      // Mock out the findRoles function
      model.attr('audit', {
        findRoles: (name) => {
          const roles = {
            Auditors: [
              {person: {id: 10, type: 'Person'}},
              {person: {id: 20, type: 'Person'}},
            ],
            'Audit Captains': [
              {person: {id: 20, type: 'Person'}},
              {person: {id: 30, type: 'Person'}},
              {person: {id: 40, type: 'Person'}},
              {person: {id: 50, type: 'Person'}},
            ],
          };
          return roles[name];
        },
      });
      model.form_preload(true);
      // Expect 7 new access_control_roles to be created
      expect(model.access_control_list.length).toBe(7);
      checkAcRoles(model, 10, [1]);
      checkAcRoles(model, 12, [10, 20]);
      checkAcRoles(model, 11, [20, 30, 40, 50]);
    });
    it('defaults correctly when auditors/audit captains are undefined',
       function () {
      var model = new CMS.Models.Assessment();
      spyOn(model, 'before_create');

      // Mock out the findRoles function
      model.attr('audit', {
        findRoles: (name) => {
          const roles = {
            Auditors: [],
            'Audit Captains': [],
          };
          return roles[name];
        },
      });
      model.form_preload(true);
      // Expect 7 new access_control_roles to be created
      expect(model.access_control_list.length).toBe(2);
      checkAcRoles(model, 10, [1]);
      checkAcRoles(model, 11, [1]);
      checkAcRoles(model, 12, []);
    });
  });
});
