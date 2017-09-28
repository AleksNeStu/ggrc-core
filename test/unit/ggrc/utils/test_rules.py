# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Unit test for checking fields in mapping and unmapping."""

import unittest

from ddt import data, ddt, unpack

import ggrc.utils.rules


class BaseTestMappingRules(unittest.TestCase):
  """Base TestCase for mapping and unmapping check."""

  rules = {}

  def assertRules(self, model, *rules):  # pylint: disable=C0103
    """Assert to check rules for current model in mapping rules."""
    self.assertIn(model, self.rules)
    self.assertEqual(set(rules), self.rules[model])


@ddt
class TestMappingRules(BaseTestMappingRules):
  """Test case for mapping rules."""

  rules = ggrc.utils.rules.get_mapping_rules()

  all_rules = ['AccessGroup', 'Clause', 'Contract', 'Control',
               'CycleTaskGroupObjectTask', 'DataAsset', 'Facility', 'Market',
               'Objective', 'OrgGroup', 'Person', 'Policy', 'Process',
               'Product', 'Program', 'Project', 'Regulation', 'Risk',
               'Section', 'Standard', 'System', 'Threat', 'Vendor', ]
  assessment_rules = ['Issue']
  audit_rules = ['Assessment', 'Issue']
  accessgroup_rules = ['Clause', 'Contract', 'Control',
                       'CycleTaskGroupObjectTask', 'DataAsset', 'Facility',
                       'Market', 'Objective', 'OrgGroup', 'Person', 'Policy',
                       'Process', 'Product', 'Program', 'Project',
                       'Regulation', 'Risk', 'Section', 'Standard', 'System',
                       'Threat', 'Vendor']
  contract_rules = ['AccessGroup', 'Clause', 'Control',
                    'CycleTaskGroupObjectTask', 'DataAsset', 'Facility',
                    'Market', 'Objective', 'OrgGroup', 'Person', 'Process',
                    'Product', 'Program', 'Project', 'Risk', 'Section',
                    'System', 'Threat', 'Vendor']
  cycletaskgroupobjecttask_rules = ['AccessGroup', 'Clause', 'Contract',
                                    'Control', 'DataAsset', 'Facility',
                                    'Market', 'Objective', 'OrgGroup',
                                    'Person', 'Policy', 'Process', 'Product',
                                    'Program', 'Project', 'Regulation', 'Risk',
                                    'Section', 'Standard', 'System', 'Threat',
                                    'Vendor']
  clause_rules = ['AccessGroup', 'Contract', 'Control',
                  'CycleTaskGroupObjectTask', 'DataAsset', 'Facility',
                  'Market', 'Objective', 'OrgGroup', 'Person', 'Policy',
                  'Process', 'Product', 'Program', 'Project', 'Regulation',
                  'Risk', 'Section', 'Standard', 'System', 'Threat', 'Vendor']
  issue_rules = ['AccessGroup', 'Assessment', 'Audit', 'Clause',
                 'Contract', 'Control', 'DataAsset', 'Facility',
                 'Market', 'Objective', 'OrgGroup', 'Policy',
                 'Process', 'Product', 'Regulation', 'Risk',
                 'Section', 'Standard', 'System', 'Threat', 'Vendor']
  person_rules = ['AccessGroup', 'Clause', 'Contract', 'Control',
                  'CycleTaskGroupObjectTask', 'DataAsset', 'Facility',
                  'Market', 'Objective', 'OrgGroup', 'Policy', 'Process',
                  'Product', 'Program', 'Project', 'Regulation', 'Risk',
                  'Section', 'Standard', 'System', 'Threat', 'Vendor', ]
  policy_rules = ['AccessGroup', 'Clause', 'Control',
                  'CycleTaskGroupObjectTask', 'DataAsset', 'Facility',
                  'Market', 'Objective', 'OrgGroup', 'Person', 'Process',
                  'Product', 'Program', 'Project', 'Risk', 'Section', 'System',
                  'Threat', 'Vendor', ]
  program_rules = ['AccessGroup', 'Clause', 'Contract', 'Control',
                   'CycleTaskGroupObjectTask', 'DataAsset', 'Facility',
                   'Market', 'Objective', 'OrgGroup', 'Person', 'Policy',
                   'Process', 'Product', 'Project', 'Regulation', 'Risk',
                   'Section', 'Standard', 'System', 'Threat', 'Vendor', ]
  regulation_rules = ['AccessGroup', 'Clause', 'Control',
                      'CycleTaskGroupObjectTask', 'DataAsset', 'Facility',
                      'Market', 'Objective', 'OrgGroup', 'Person', 'Process',
                      'Product', 'Program', 'Project', 'Risk', 'Section',
                      'System', 'Threat', 'Vendor', ]
  risk_rules = ['AccessGroup', 'Clause', 'Contract', 'Control',
                'CycleTaskGroupObjectTask', 'DataAsset', 'Facility', 'Market',
                'Objective', 'OrgGroup', 'Person', 'Policy', 'Process',
                'Product', 'Program', 'Project', 'Regulation', 'Section',
                'Standard', 'System', 'Threat', 'Vendor', ]
  standard_rules = ['AccessGroup', 'Clause', 'Control',
                    'CycleTaskGroupObjectTask', 'DataAsset', 'Facility',
                    'Market', 'Objective', 'OrgGroup', 'Person', 'Process',
                    'Product', 'Program', 'Project', 'Risk', 'Section',
                    'System', 'Threat', 'Vendor', ]
  threat_rules = ['AccessGroup', 'Clause', 'Contract', 'Control',
                  'CycleTaskGroupObjectTask', 'DataAsset', 'Facility',
                  'Market', 'Objective', 'OrgGroup', 'Person', 'Policy',
                  'Process', 'Product', 'Program', 'Project', 'Regulation',
                  'Risk', 'Section', 'Standard', 'System', 'Vendor', ]

  @data(("AccessGroup", accessgroup_rules),
        ("Assessment", assessment_rules),
        ("Audit", audit_rules),
        ("Clause", clause_rules),
        ("Contract", contract_rules),
        ("Control", all_rules),
        ("CycleTaskGroupObjectTask", cycletaskgroupobjecttask_rules),
        ("DataAsset", all_rules),
        ("Facility", all_rules),
        ("Issue", issue_rules),
        ("Market", all_rules),
        ("Objective", all_rules),
        ("OrgGroup", all_rules),
        ("Person", person_rules),
        ("Policy", policy_rules),
        ("Process", all_rules),
        ("Product", all_rules),
        ("Program", program_rules),
        ("Project", all_rules),
        ("Regulation", regulation_rules),
        ("Risk", risk_rules),
        ("Section", all_rules),
        ("Standard", standard_rules),
        ("System", all_rules),
        ("Threat", threat_rules),
        ("Vendor", all_rules))
  @unpack
  def test_field(self, field, rules):
    self.assertRules(field, *rules)


@ddt
class TestUnMappingRules(BaseTestMappingRules):
  """Test case for unmapping rules."""

  rules = ggrc.utils.rules.get_unmapping_rules()

  all_rules = ['AccessGroup', 'Clause', 'Contract', 'Control',
               'CycleTaskGroupObjectTask', 'DataAsset', 'Facility', 'Market',
               'Objective', 'OrgGroup', 'Person', 'Policy', 'Process',
               'Product', 'Program', 'Project', 'Regulation', 'Risk',
               'Section', 'Standard', 'System', 'Threat', 'Vendor']
  assessment_rules = ['Issue']
  audit_rules = ['Issue']
  accessgroup_rules = ['Clause', 'Contract', 'Control',
                       'CycleTaskGroupObjectTask', 'DataAsset', 'Facility',
                       'Market', 'Objective', 'OrgGroup', 'Person', 'Policy',
                       'Process', 'Product', 'Program', 'Project',
                       'Regulation', 'Risk', 'Section', 'Standard', 'System',
                       'Threat', 'Vendor']
  contract_rules = ['AccessGroup', 'Clause', 'Control',
                    'CycleTaskGroupObjectTask', 'DataAsset', 'Facility',
                    'Market', 'Objective', 'OrgGroup', 'Person', 'Process',
                    'Product', 'Program', 'Project', 'Risk', 'Section',
                    'System', 'Threat', 'Vendor']
  cycletaskgroupobjecttask_rules = ['AccessGroup', 'Clause', 'Contract',
                                    'Control', 'DataAsset', 'Facility',
                                    'Market', 'Objective', 'OrgGroup',
                                    'Person', 'Policy', 'Process', 'Product',
                                    'Program', 'Project', 'Regulation', 'Risk',
                                    'Section', 'Standard', 'System', 'Threat',
                                    'Vendor']
  clause_rules = ['AccessGroup', 'Contract', 'Control',
                  'CycleTaskGroupObjectTask', 'DataAsset', 'Facility',
                  'Market', 'Objective', 'OrgGroup', 'Person', 'Policy',
                  'Process', 'Product', 'Program', 'Project', 'Regulation',
                  'Risk', 'Section', 'Standard', 'System', 'Threat', 'Vendor']
  issue_rules = ['AccessGroup', 'Assessment', 'Audit', 'Clause',
                 'Contract', 'Control', 'DataAsset', 'Facility',
                 'Market', 'Objective', 'OrgGroup', 'Policy',
                 'Process', 'Product', 'Regulation', 'Risk',
                 'Section', 'Standard', 'System', 'Threat', 'Vendor']
  person_rules = ['AccessGroup', 'Clause', 'Contract', 'Control',
                  'CycleTaskGroupObjectTask', 'DataAsset', 'Facility',
                  'Market', 'Objective', 'OrgGroup', 'Policy', 'Process',
                  'Product', 'Program', 'Project', 'Regulation', 'Risk',
                  'Section', 'Standard', 'System', 'Threat', 'Vendor']
  policy_rules = ['AccessGroup', 'Clause', 'Control',
                  'CycleTaskGroupObjectTask', 'DataAsset', 'Facility',
                  'Market', 'Objective', 'OrgGroup', 'Person', 'Process',
                  'Product', 'Program', 'Project', 'Risk', 'Section', 'System',
                  'Threat', 'Vendor']
  program_rules = ['AccessGroup', 'Clause', 'Contract', 'Control',
                   'CycleTaskGroupObjectTask', 'DataAsset', 'Facility',
                   'Market', 'Objective', 'OrgGroup', 'Person', 'Policy',
                   'Process', 'Product', 'Project', 'Regulation', 'Risk',
                   'Section', 'Standard', 'System', 'Threat', 'Vendor']
  regulation_rules = ['AccessGroup', 'Clause', 'Control',
                      'CycleTaskGroupObjectTask', 'DataAsset', 'Facility',
                      'Market', 'Objective', 'OrgGroup', 'Person', 'Process',
                      'Product', 'Program', 'Project', 'Risk', 'Section',
                      'System', 'Threat', 'Vendor']
  risk_rules = ['AccessGroup', 'Clause', 'Contract', 'Control',
                'CycleTaskGroupObjectTask', 'DataAsset', 'Facility', 'Market',
                'Objective', 'OrgGroup', 'Person', 'Policy', 'Process',
                'Product', 'Program', 'Project', 'Regulation', 'Section',
                'Standard', 'System', 'Threat', 'Vendor']
  standard_rules = ['AccessGroup', 'Clause', 'Control',
                    'CycleTaskGroupObjectTask', 'DataAsset', 'Facility',
                    'Market', 'Objective', 'OrgGroup', 'Person', 'Process',
                    'Product', 'Program', 'Project', 'Risk', 'Section',
                    'System', 'Threat', 'Vendor']
  threat_rules = ['AccessGroup', 'Clause', 'Contract', 'Control',
                  'CycleTaskGroupObjectTask', 'DataAsset', 'Facility',
                  'Market', 'Objective', 'OrgGroup', 'Person', 'Policy',
                  'Process', 'Product', 'Program', 'Project', 'Regulation',
                  'Risk', 'Section', 'Standard', 'System', 'Vendor']

  @data(("AccessGroup", accessgroup_rules),
        ("Assessment", assessment_rules),
        ("Audit", audit_rules),
        ("Clause", clause_rules),
        ("Contract", contract_rules),
        ("Control", all_rules),
        ("CycleTaskGroupObjectTask", cycletaskgroupobjecttask_rules),
        ("DataAsset", all_rules),
        ("Facility", all_rules),
        ("Issue", issue_rules),
        ("Market", all_rules),
        ("Objective", all_rules),
        ("OrgGroup", all_rules),
        ("Person", person_rules),
        ("Policy", policy_rules),
        ("Process", all_rules),
        ("Product", all_rules),
        ("Program", program_rules),
        ("Project", all_rules),
        ("Regulation", regulation_rules),
        ("Risk", risk_rules),
        ("Section", all_rules),
        ("Standard", standard_rules),
        ("System", all_rules),
        ("Threat", threat_rules),
        ("Vendor", all_rules))
  @unpack
  def test_field(self, field, rules):
    self.assertRules(field, *rules)


@ddt
class TestSnapshotMappingRules(BaseTestMappingRules):
  """Test case for snapshot mapping rules."""

  rules = ggrc.utils.rules.get_snapshot_mapping_rules()

  all_rules = []
  assessment_rules = ["AccessGroup", "Clause", "Contract", "Control",
                      "DataAsset", "Facility", "Market", "Objective",
                      "OrgGroup", "Policy", "Process", "Product",
                      "Regulation", "Section", "Standard", "System",
                      "Vendor", "Risk", "Threat"]
  audit_rules = ["AccessGroup", "Clause", "Contract", "Control",
                 "DataAsset", "Facility", "Market", "Objective",
                 "OrgGroup", "Policy", "Process", "Product",
                 "Regulation", "Section", "Standard", "System",
                 "Vendor", "Risk", "Threat"]
  issue_rules = ["AccessGroup", "Clause", "Contract", "Control",
                 "DataAsset", "Facility", "Market", "Objective",
                 "OrgGroup", "Policy", "Process", "Product",
                 "Regulation", "Section", "Standard", "System",
                 "Vendor", "Risk", "Threat"]

  @data(("AccessGroup", all_rules),
        ("Assessment", assessment_rules),
        ("Audit", audit_rules),
        ("Clause", all_rules),
        ("Contract", all_rules),
        ("Control", all_rules),
        ("CycleTaskGroupObjectTask", all_rules),
        ("DataAsset", all_rules),
        ("Facility", all_rules),
        ("Issue", issue_rules),
        ("Market", all_rules),
        ("Objective", all_rules),
        ("OrgGroup", all_rules),
        ("Person", all_rules),
        ("Policy", all_rules),
        ("Process", all_rules),
        ("Product", all_rules),
        ("Program", all_rules),
        ("Project", all_rules),
        ("Regulation", all_rules),
        ("Risk", all_rules),
        ("Section", all_rules),
        ("Standard", all_rules),
        ("System", all_rules),
        ("Threat", all_rules),
        ("Vendor", all_rules))
  @unpack
  def test_field(self, field, rules):
    self.assertRules(field, *rules)
