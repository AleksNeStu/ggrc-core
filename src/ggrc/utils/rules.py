# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Mapping rules for Relationship validation and map:model import columns."""

import copy

from ggrc import extensions


def get_mapping_rules():
  """ Get mappings rules as defined in business_object.js

  Special cases:
    Aduit has direct mapping to Program with program_id
    Section has a direct mapping to Standard/Regulation/Poicy with directive_id
  """
  from ggrc import snapshotter
  all_rules = set(['AccessGroup', 'Clause', 'Contract', 'Control',
                   'CycleTaskGroupObjectTask', 'DataAsset', 'Facility',
                   'Market', 'Objective', 'OrgGroup', 'Person', 'Policy',
                   'Process', 'Product', 'Program', 'Project', 'Regulation',
                   'Risk', 'Section', 'Standard', 'System', 'Threat',
                   'Vendor'])

  snapshots = snapshotter.rules.Types.all

  business_object_rules = {
      "AccessGroup": all_rules - set(['AccessGroup']),
      "Clause": all_rules - set(['Clause']),
      "Contract": all_rules - set(['Policy', 'Regulation',
                                   'Contract', 'Standard']),
      "Control": all_rules,
      "CycleTaskGroupObjectTask": (all_rules -
                                   set(['CycleTaskGroupObjectTask'])),
      "DataAsset": all_rules,
      "Facility": all_rules,
      "Market": all_rules,
      "Objective": all_rules,
      "OrgGroup": all_rules,
      "Person": all_rules - set(['Person']),
      "Policy": all_rules - set(['Policy', 'Regulation',
                                 'Contract', 'Standard']),
      "Process": all_rules,
      "Product": all_rules,
      "Program": all_rules - set(['Program']),
      "Project": all_rules,
      "Regulation": all_rules - set(['Policy', 'Regulation',
                                     'Contract', 'Standard']),
      "Risk": all_rules - set(['Risk']),
      "Section": all_rules,
      "Standard": all_rules - set(['Policy', 'Regulation',
                                   'Contract', 'Standard']),
      "System": all_rules,
      "Threat": all_rules - set(['Threat']),
      "Vendor": all_rules,
  }

  # Audit and Audit-scope objects
  # Assessment and Issue have a special Audit field instead of map:audit
  business_object_rules.update({
      "Audit": set(),
      "Assessment": snapshots | {"Issue"},
      "Issue": snapshots | {"Assessment"},
  })

  return business_object_rules


def get_unmapping_rules():
  """Get unmapping rules from mapping dict."""
  unmapping_rules = copy.deepcopy(get_mapping_rules())

  # Audit and Audit-scope objects
  unmapping_rules["Audit"] = set()
  unmapping_rules["Assessment"] = {"Issue"}
  unmapping_rules["Issue"] = {"Assessment"}

  return unmapping_rules


def get_mapping_validation_rules():
  """Get mapping rules to validate a new Relationship.

  The rules must be symmetric, i.e. "MyDst" in rules["MySrc"] <=> "MySrc" in
  rules["MyDst"].
  """
  base_rules = _get_mapping_validation_core_rules()
  # Note: at some point we may want to contribute an additional blacklist here
  contributed_whitelists = extensions.get_module_contributions(
      "MAPPING_VALIDATION_WHITELIST",
  )
  for whitelist in contributed_whitelists:
    for source_type, destination_types in whitelist.iteritems():
      base_rules[source_type] = (base_rules.get(source_type, set()) |
                                 destination_types)

  return base_rules


def _get_mapping_validation_core_rules():
  """Get Relationship validation rules in context of the core app."""
  assignable_rules = {"Person"}
  documentable_rules = {"Document"}
  commentable_rules = {"Comment"}
  audit_scope_rules = {"Assessment", "Issue", "Snapshot"}
  directive_types = {"Contract", "Policy", "Regulation", "Standard"}
  allow_all = {
      "AccessGroup",
      "Clause",
      "Contract",
      "Control",
      "DataAsset",
      "Facility",
      "Market",
      "Objective",
      "OrgGroup",
      "Policy",
      "Process",
      "Product",
      "Program",
      "Project",
      "Regulation",
      "Section",
      "Standard",
      "System",
      "Vendor",
  }
  validation_rules = {
      "AccessGroup": allow_all - {"AccessGroup"},
      "Assessment": ((audit_scope_rules | assignable_rules |
                      documentable_rules | commentable_rules | {"Audit"}) -
                     {"Assessment"}),
      "AssessmentTemplate": {"Audit"},
      "Audit": audit_scope_rules | {"AssessmentTemplate"},
      "Clause": allow_all - {"Clause"},
      "Comment": {"Assessment"},
      "Contract": allow_all - directive_types,
      "Control": allow_all,
      "DataAsset": allow_all,
      "Document": {"Assessment"},
      "Facility": allow_all,
      "Issue": audit_scope_rules | {"Audit"},
      "Market": allow_all,
      "Objective": allow_all,
      "OrgGroup": allow_all,
      "Person": {"Assessment"},
      "Policy": allow_all - directive_types,
      "Process": allow_all,
      "Product": allow_all,
      "Program": allow_all - {"Program", "Audit"},
      "Project": allow_all,
      "Regulation": allow_all - directive_types,
      "Section": allow_all,
      "Snapshot": audit_scope_rules | {"Audit"},
      "Standard": allow_all - directive_types,
      "System": allow_all,
      "Vendor": allow_all,
  }

  return validation_rules


__all__ = [
    "get_mapping_rules",
    "get_mapping_validation_rules",
    "get_unmapping_rules",
]
