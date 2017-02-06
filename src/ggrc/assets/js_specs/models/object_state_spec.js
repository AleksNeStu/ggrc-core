/*!
    Copyright (C) 2017 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

describe('Model states test', function () {
  var basicStateObjects = ['AccessGroup', 'Clause', 'Contract',
      'Control', 'DataAsset', 'Facility', 'Issue', 'Market',
      'Objective', 'OrgGroup', 'Policy', 'Process', 'Product', 'Program',
      'Project', 'Regulation', 'Risk', 'Section', 'Standard', 'System',
      'Threat', 'Vendor'];

  basicStateObjects.forEach(function (object) {
    var expectedStatuses = ['Draft', 'Deprecated', 'Active'];
    it('checks if ' + object + ' has expected statuses', function () {
      expect(CMS.Models[object].statuses).toEqual(
          expectedStatuses, 'for object ' + object);
    });
  });
  it('checks if Audit has expected statuses', function () {
    var expectedStatuses = ['Planned', 'In Progress', 'Manager Review',
        'Ready for External Review', 'Completed'];
    expect(CMS.Models.Audit.statuses).toEqual(expectedStatuses);
  });
  it('checks if Assessment has correct statuses', function () {
    var expectedStatuses = ['Not Started', 'In Progress', 'Ready for Review',
        'Verified', 'Completed'];
    expect(CMS.Models.Assessment.statuses).toEqual(expectedStatuses);
  });
});

describe('Model review state test', function () {
  var reviewObjects = ['AccessGroup', 'Assessment', 'Audit', 'Clause',
      'Contract', 'Control', 'DataAsset', 'Facility', 'Issue', 'Market',
      'Objective', 'OrgGroup', 'Policy', 'Process', 'Product', 'Program',
      'Project', 'Regulation', 'Risk', 'Section', 'Standard', 'System',
      'Threat', 'Vendor'];
  reviewObjects.forEach(function (object) {
    it('checks if ' + object + ' has os state in attr_list', function () {
      expect(CMS.Models[object].attr_list).toContain(
          {attr_title: 'Review State', attr_name: 'os_state'},
          'for object ' + object);
    });
  });
});
