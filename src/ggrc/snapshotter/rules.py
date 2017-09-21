# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Generate rules for snapshoting"""

from ggrc.snapshotter.datastructures import Attr


class Types(object):
  """Get default types for snapshotting"""

  # pylint: disable=too-few-public-methods

  all = {
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
      "Regulation",
      "Section",
      "Standard",
      "System",
      "Vendor",
      "Risk",
      "Threat",
  }

  parents = {
      "Audit",
  }

  scoped = {
      "Assessment",
  }

  trans_scope = {
      "Issue",
  }

  ignore = {
      "Assessment",
      "AssessmentTemplate",
      "Issue",
      "Workflow",
      "Audit",
      "Person"
  }


class Rules(object):
  """Returns a dictionary of rules

  Expected format of rule_list is the following:

  [
    {"master_object_type", ...},
    {"first degree object types"},
    {"second degree object types"}
  ]

  For all master objects of type master_object_type, it will gather all
  related objects from first degree object types (which can be related via
  relationships table or via direct mapping (in which case you should wrap
  the attribute name in Attr) and gather all of first degrees related objects
  of the types listed in the second degree object type.

  Example:
  [
    {"object_type_1", ["object_type_2", ...]},
    {"type_of_related_object_or_attribute", ["second..."]},
    {"type_of_object_to_snapshot_1", ["type_2", ...]}
  ]

  From it, it will build a dictionary of format:
  {
      "parent_type": {
        "fst": {"type_of_related_object_or_attribute_1", ...},
        "snd": {"type_1", "type_2", ...}
      },
      ...
  }

  """

  # pylint: disable=too-few-public-methods

  def __init__(self, rule_list):
    self.rules = dict()

    for parents, fstdeg, snddeg in rule_list:
      for parent in parents:
        self.rules[parent] = {
            "fst": fstdeg,
            "snd": snddeg
        }


DEFAULT_RULE_LIST = [
    [
        {"Audit"},
        {Attr("program")},
        Types.all - Types.ignore
    ]
]


def get_rules(rule_list=None):
  """Get the rules governing the snapshot creation

  Args:
    rule_list: List of rules
  Returns:
    Rules object with attribute `rules`. See Rules object for detailed doc.
  """
  if not rule_list:
    rule_list = DEFAULT_RULE_LIST
  return Rules(rule_list)
