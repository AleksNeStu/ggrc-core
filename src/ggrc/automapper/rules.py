# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

import itertools
from collections import namedtuple
from logging import getLogger

from ggrc import models

Attr = namedtuple('Attr', ['name'])


type_ordering = [['Audit'], ['Program'],
                 ['Regulation', 'Policy', 'Standard', 'Contract'],
                 ['Section', 'Clause'], ['Objective'], ['Control'],
                 ['Assessment']]


# pylint: disable=invalid-name
logger = getLogger(__name__)


def get_type_indices():
  indices = dict()
  for i, layer in enumerate(type_ordering):
    for type_ in layer:
      indices[type_] = i
  return indices


class Rule(object):
  def __init__(self, name, top, mid, bottom):
    def wrap(o):
      return o if isinstance(o, set) else {o}
    self.name = name
    self.top = wrap(top)
    self.mid = wrap(mid)
    self.bottom = wrap(bottom)


class RuleSet(object):
  Entry = namedtuple('RuleSetEntry', ['explicit', 'implicit'])
  entry_empty = Entry(frozenset(set()), frozenset(set()))
  _type_indices = get_type_indices()

  @classmethod
  def _check_type_order(self, type1, type2):
    i1 = self._type_indices.get(type1, None)
    if i1 is None:
      return "Unknown level for %s" % type1
    i2 = self._type_indices.get(type2, None)
    if i2 is None:
      return "Unknown level for %s" % type2
    if not i1 <= i2:
      return "Type %s does not occur higher than type %s" % (type1, type2)

  @classmethod
  def _explode_rules(cls, rule_list):
    for rule in rule_list:
      for top, mid, bottom in itertools.product(rule.top, rule.mid,
                                                rule.bottom):
        if Attr in map(type, [top, mid, bottom]):
          # if this is a direct mapping
          # there is only one way to form the triangle
          # TODO rule sanity check
          yield (mid, bottom, top, rule)
        else:
          err1 = cls._check_type_order(top, mid)
          err2 = cls._check_type_order(mid, bottom)
          if err1 is not None or err2 is not None:
            logger.warning("Automapping rule ordering violation")
            if err1 is not None:
              logger.warning(err1)
            if err2 is not None:
              logger.warning(err2)
            logger.warning("Skipping bad rule (%s, %s, %s)", top, mid, bottom)
            continue
          yield (mid, bottom, top, rule)
          yield (mid, top, bottom, rule)

  def __init__(self, count_limit, rule_list):
    self.count_limit = count_limit
    self._rule_list = rule_list
    self._rules = dict()
    self._rule_source = dict()

    def available(m, l):
      return hasattr(getattr(models, m), l + '_id')

    for src, dst, mapping, source in self._explode_rules(rule_list):
      key = (src, dst)
      entry = self._rules.get(key, RuleSet.Entry(set(), set()))
      if isinstance(mapping, Attr):
        entry = RuleSet.Entry(entry.explicit, entry.implicit | {mapping})
      else:
        entry = RuleSet.Entry(entry.explicit | {mapping}, entry.implicit)
      self._rules[key] = entry

      sources = self._rule_source.get((src, dst, mapping), set())
      sources.add(source)
      self._rule_source[src, dst, mapping] = sources

    self._freeze()

  def _freeze(self):
    for key in self._rules:
      explicit, implicit = self._rules[key]
      self._rules[key] = RuleSet.Entry(frozenset(explicit),
                                       frozenset(implicit))

  def __getitem__(self, key):
    if key in self._rules:
      return self._rules[key]
    else:
      return RuleSet.entry_empty

  def __repr__(self):
    return 'Rules(%s)' % repr(self._rule_list)

  def __str__(self):
    rules = []
    for key in self._rules:
      src, dst = key
      for mapping in self._rules[key].explicit | self._rules[key].implicit:
        source = ','.join(r.name for r in self._rule_source[src, dst, mapping])
        rule = ('  -> %s <--> %s <--> %s <- )' % (dst, src, mapping))
        rule += ' ' * (70 - len(rule))
        rule += source
        rules.append(rule)
    rules.sort()
    return 'RulesSet\n' + '\n'.join(rules)


class Types(object):
  all = {'Program', 'Regulation', 'Policy', 'Standard', 'Contract',
         'Section', 'Clause', 'Objective', 'Control', 'Assessment'}
  directives = {'Regulation', 'Policy', 'Standard', 'Contract'}
  assets_business = {'System', 'Process', 'DataAsset', 'Product', 'Project',
                     'Facility', 'Market'}
  people_groups = {'AccessGroup', 'Person', 'OrgGroup', 'Vendor'}


rules = RuleSet(count_limit=10000, rule_list=[
    Rule(
        'mapping directive to a program',
        'Program',
        Types.directives,
        Types.all - {'Program'} - Types.directives,
    ),

    Rule(
        'mapping to sections and clauses',
        Types.directives,
        {'Section', 'Clause'},
        {'Objective', 'Control'},
    ),

    Rule(
        'mapping to objective',
        {'Section'},
        {'Objective'},
        {'Objective', 'Control'},
    ),

    Rule(
        'mapping nested controls',
        {'Objective'},
        {'Control'},
        {'Control'},
    ),

])
