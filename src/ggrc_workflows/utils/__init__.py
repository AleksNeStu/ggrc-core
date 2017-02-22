# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Module with Workflow-context Relationship validation rules."""


def get_mapping_validation_rules():
  """Rules to validate Relationships to Workflow-related objects."""
  ctgot_mappings = {
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
      "Threat",
      "Vendor",
  }
  validation_rules = {
      "CycleTaskGroupObjectTask": ctgot_mappings,
  }
  for mapping in ctgot_mappings:
    validation_rules[mapping] = (validation_rules.get(mapping, set()) |
                                 {"CycleTaskGroupObjectTask"})

  return validation_rules
