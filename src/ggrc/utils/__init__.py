# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

import datetime
import json
import re
import sys
import sqlalchemy

from flask import request
from ggrc.settings import CUSTOM_URL_ROOT
from ggrc.utils import benchmarks


class GrcEncoder(json.JSONEncoder):

  """Custom JSON Encoder to handle datetime objects and sets

  from:
     `http://stackoverflow.com/questions/12122007/python-json-encoder-to-support-datetime`_
  also consider:
     `http://hg.tryton.org/2.4/trytond/file/ade5432ac476/trytond/protocols/jsonrpc.py#l53`_
  """

  def default(self, obj):
    if isinstance(obj, datetime.datetime):
      if not obj.time():
        return obj.date().isoformat()
      return obj.isoformat()
    elif isinstance(obj, datetime.date):
      return obj.isoformat()
    elif isinstance(obj, datetime.timedelta):
      return (datetime.datetime.min + obj).time().isoformat()
    elif isinstance(obj, set):
      return list(obj)
    else:
      return super(GrcEncoder, self).default(obj)


def as_json(obj, **kwargs):
  return json.dumps(obj, cls=GrcEncoder, **kwargs)


def service_for(obj):
  module = sys.modules['ggrc.services']
  if type(obj) is str or type(obj) is unicode:  # noqa
    model_type = obj
  else:
    model_type = obj.__class__.__name__
  return getattr(module, model_type, None)


def url_for(obj, id=None):
  service = service_for(obj)
  if service is None:
    return None
  if not hasattr(service, 'url_for'):
    return None
  if id is not None:
    return service.url_for(id=id)
  return service.url_for(obj)


def view_service_for(obj):
  module = sys.modules['ggrc.views']
  if type(obj) is str or type(obj) is unicode:  # noqa
    model_type = obj
  else:
    model_type = obj.__class__.__name__
  return getattr(module, model_type, None)


def view_url_for(obj, id=None):
  service = view_service_for(obj)
  if service is None:
    return None
  if not hasattr(service, 'url_for'):
    return None
  if id is not None:
    return service.url_for(id=id)
  return service.url_for(obj)


def encoded_dict(in_dict):
  # http://stackoverflow.com/questions/6480723/urllib-urlencode-doesn't-like-unicode-values-how-about-this-workaround
  out_dict = {}
  for k, v in in_dict.iteritems():
    if isinstance(v, unicode):  # noqa
      v = v.encode('utf8')
    elif isinstance(v, str):
      # Must be encoded in UTF-8
      v.decode('utf8')
    out_dict[k] = v
  return out_dict


def merge_dict(destination, source, path=None):
  """merges source into destination"""
  if path is None:
    path = []
  for key in source:
    if key in destination:
      if isinstance(destination[key], dict) and isinstance(source[key], dict):
        merge_dict(destination[key], source[key], path + [str(key)])
      elif destination[key] == source[key]:
        pass  # same leaf value
      else:
        raise Exception('Conflict at %s' % '.'.join(path + [str(key)]))
    else:
      destination[key] = source[key]
  return destination


def merge_dicts(*args):
  result = {}
  for arg in args:
    result = merge_dict(result, arg)
  return result


def get_url_root():
  if CUSTOM_URL_ROOT is not None:
    return CUSTOM_URL_ROOT
  return request.url_root


def get_mapping_rules():
  """ Get mappings rules as defined in business_object.js

  Special cases:
    Aduit has direct mapping to Program with program_id
    Section has a direct mapping to Standard/Regulation/Poicy with directive_id
  """
  # these rules are copy pasted from
  # src/ggrc/assets/javascripts/apps/base_widgets.js line: 9
  # WARNING ########################################################
  # Manually added Risks and threats to the list from base_widgets #
  ##################################################################
  # TODO: Read these rules from different modules and combine them here.
  all_rules = set(['AccessGroup', 'Assessment', 'Audit', 'Clause', 'Contract',
                   'Control', 'CycleTaskGroupObjectTask', 'DataAsset',
                   'Facility', 'Issue', 'Market', 'Objective', 'OrgGroup',
                   'Person', 'Policy', 'Process', 'Product', 'Program',
                   'Project', 'Regulation', 'Risk', 'Section', 'Standard',
                   'System', 'Threat', 'Vendor'])

  business_object_rules = {
      "AccessGroup": all_rules - set(['AccessGroup']),
      "Assessment": all_rules - set(['Assessment']),
      "Audit": all_rules - set(['CycleTaskGroupObjectTask', 'Audit',
                                'Risk', 'Threat']),
      "Clause": all_rules - set(['Clause']),
      "Contract": all_rules - set(['Policy', 'Regulation',
                                   'Contract', 'Standard']),
      "Control": all_rules,
      "CycleTaskGroupObjectTask": all_rules - set(['CycleTaskGroupObjectTask',
                                                   'Audit']),
      "DataAsset": all_rules,
      "Facility": all_rules,
      "Issue": all_rules,
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
      "Risk": all_rules - set(['Audit', 'Risk']),
      "Section": all_rules,
      "Standard": all_rules - set(['Policy', 'Regulation',
                                   'Contract', 'Standard']),
      "System": all_rules,
      "Threat": all_rules - set(['Audit', 'Threat']),
      "Vendor": all_rules,
  }

  return business_object_rules


def _prefix_camelcase(name, prefix):
  name = name[:1].lower() + name[1:]
  return re.sub(r'[A-Z]', lambda pat: prefix + pat.group(0).lower(), name)


def underscore_from_camelcase(name):
  return _prefix_camelcase(name, "_")


def title_from_camelcase(name):
  return _prefix_camelcase(name, " ")


def get_fuzzy_date(delta_date):
  """Get a human readable date string.

  This function returns a human friendly time delta compared to today.

  Args:
    delta_date (date): Date that we want to show to the user.

  Returns:
    string: A human readable representation date delta.

  Examples:
    >>> get_fuzzy_date(datetime.date.today() + datetime.timedelta(2))
    'in 2 days'
    >>> get_fuzzy_date(datetime.date.today())
    'today'
    >>> get_fuzzy_date(datetime.date.today() + datetime.timedelta(-1))
    '1 day ago'
  """
  if not delta_date:
    return ""
  if isinstance(delta_date, datetime.datetime):
    delta_date = delta_date.date()
  delta = delta_date - datetime.date.today()
  if delta.days < 0:
    days = abs(delta.days)
    return "{} day{} ago".format(days, "s" if days > 1 else "")
  if delta.days == 0:
    return "today"
  # TODO: use format_timedelta from babel package.
  return "in {} day{}".format(delta.days, "s" if delta.days > 1 else "")


def get_digest_date_statement(delta_date, word, is_change_tense=False):
  """Get statement created from word in appropriate tense and readable date.

  This function returns phrase created using concatenation of a word in
  appropriate tense with human readable date value.

  Args:
    delta_date (date): Date that we want to show to the user
    word (str): With which date should be concatenated
    is_change_tense: Flag which shows is tense of the word should be changed

  Returns:
    string: A human readable statement, created from word and date
            concatenation
  """
  fuzzy_date = get_fuzzy_date(delta_date)
  word_end = ''
  if is_change_tense:
    if "in" in fuzzy_date:
      word_end = 's'
    else:
      word_end = 'ed'
  return '{}{} {}'.format(word, word_end, fuzzy_date)


# pylint: disable=too-few-public-methods
# because this is a small context manager
class QueryCounter(object):
  """Context manager for counting sqlalchemy database queries.

  Usage:
    with QueryCounter() as counter:
      query_count = counter.get
  """

  def __init__(self):
    self.queries = []

    def after_cursor_execute(*args):
      self.queries.append(args[2])

    self.listener = after_cursor_execute

  def __enter__(self):
    sqlalchemy.event.listen(sqlalchemy.engine.Engine,
                            "after_cursor_execute",
                            self.listener)
    return self

  def __exit__(self, *_):
    sqlalchemy.event.remove(sqlalchemy.engine.Engine,
                            "after_cursor_execute",
                            self.listener)

  @property
  def get(self):
    return len(self.queries)


benchmark = benchmarks.get_benchmark()
with_nop = benchmarks.WithNop


def convert_date_format(date, format_from, format_to):
  """Convert string date format from one to another."""
  return datetime.datetime.strptime(date, format_from).strftime(format_to)
