# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Relationship validation rules for mappings with Risks/Threats."""


def get_mapping_validation_rules():
  """Get module-specific extension to mapping validation rules."""
  risk_mappings = {
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
  threat_mappings = {
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
      "Risk": risk_mappings,
      "Threat": threat_mappings,
  }
  for mapping in risk_mappings:
    validation_rules[mapping] = (validation_rules.get(mapping, set()) |
                                 {"Risk"})
  for mapping in threat_mappings:
    validation_rules[mapping] = (validation_rules.get(mapping, set()) |
                                 {"Threat"})

  return validation_rules
