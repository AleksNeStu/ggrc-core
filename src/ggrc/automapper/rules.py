# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Automapping rules generator."""

import collections
import itertools
from logging import getLogger


class AutomappingRuleConfigError(ValueError):
  pass


TYPE_ORDERING = [['Program'],
                 ['Regulation', 'Policy', 'Standard', 'Contract'],
                 ['Section', 'Clause'], ['Objective'], ['Control']]

TYPE_ORDERING += [["Issue"], ["Assessment"], ["Audit", "Snapshot"]]

# pylint: disable=invalid-name
logger = getLogger(__name__)


def get_type_levels():
  """Translate TYPE_ORDERING into type->level map to check rule ordering."""
  indices = dict()
  for i, layer in enumerate(TYPE_ORDERING):
    for type_ in layer:
      indices[type_] = i
  return indices


Rule = collections.namedtuple("Rule", ["top", "mid", "bottom"])


def _check_rule_type_order(type_levels, *type_sets):
  """Raise exception if types violate type ordering.

  In a correct Rule, the levels of types must not be decreasing.
  """
  try:
    levels = [{(type_levels[type_]) for type_ in set_}
              for set_ in type_sets]
  except KeyError as e:
    raise AutomappingRuleConfigError("Unknown level for {}"
                                     .format(e.args[0]))

  for i, level in enumerate(levels[1:], 1):
    if max(level) < min(levels[i - 1]):
      raise AutomappingRuleConfigError(
          "All types {} must be higher than all types {}"
          .format(type_sets[i - 1], type_sets[i]))


def validate_rules(rule_list):
  """Validate te order of types in every rule from a list."""
  type_levels = get_type_levels()
  for rule in rule_list:
    _check_rule_type_order(type_levels, rule.top, rule.mid, rule.bottom)


def explode_rules(rule_list):
  for rule in rule_list:
    for top, mid, bottom in itertools.product(rule.top, rule.mid,
                                              rule.bottom):
      yield (bottom, mid, top)
      yield (top, mid, bottom)


def make_rule_set(rule_list):
  """Validate and explode rule list into elementary rules."""
  validate_rules(rule_list)

  rule_set = collections.defaultdict(frozenset)
  for src, dst, mapping in explode_rules(rule_list):
    rule_set[src, dst] |= {mapping}

  return rule_set


def rules_to_str(rules):
  """Make rules printable in a pretty format for debugging.

  Usage:
    from ggrc.automapper import rules
    print rules.rules_to_str(rules.rules)
  """
  lines = []
  for key in rules:
    src, dst = key
    for mapping in rules[key]:
      rule = ("%s <--> %s <--> %s" % (src, dst, mapping))
      lines.append(rule)
  lines.sort()
  return "\n".join(lines)


class Types(object):
  """Model names and collections to use in Rule initialization."""
  all = {'Program', 'Regulation', 'Policy', 'Standard', 'Contract',
         'Section', 'Clause', 'Objective', 'Control'}
  directives = {'Regulation', 'Policy', 'Standard', 'Contract'}
  assets_business = {'System', 'Process', 'DataAsset', 'Product', 'Project',
                     'Facility', 'Market'}
  people_groups = {'AccessGroup', 'Person', 'OrgGroup', 'Vendor'}


rules = make_rule_set(rule_list=[
    Rule(
        # mapping directive to a program
        {'Program'},
        Types.directives,
        Types.all - {'Program'} - Types.directives,
    ),

    Rule(
        # mapping to sections and clauses
        Types.directives,
        {'Section', 'Clause'},
        {'Objective', 'Control'},
    ),

    Rule(
        # mapping to objective
        {'Section'},
        {'Objective'},
        {'Objective', 'Control'},
    ),

    Rule(
        # mapping nested controls
        {'Objective'},
        {'Control'},
        {'Control'},
    ),

    Rule(
        # mappings for 'raise an issue' on assessment page
        {"Issue"},
        {"Assessment"},
        {"Audit", "Snapshot"},
    ),
])
