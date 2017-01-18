# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""The module contains functionality for working with json templates"""
# pylint: disable=too-few-public-methods
# pylint: disable=redefined-builtin
# pylint: disable=invalid-name

import copy
import json

import os

from lib.constants import url, objects


class TemplateProvider(object):
  """Processes JSON templates."""
  RELATIVE_PATH_TEMPLATE = "template/{0}.json"
  parsed_data = dict()

  @staticmethod
  def get_template_as_dict(type, **kwargs):
    """Return object representation based on JSON template."""
    try:
      obj = copy.deepcopy(TemplateProvider.parsed_data[type])
    except KeyError:
      path = os.path.join(
          os.path.dirname(__file__),
          TemplateProvider.RELATIVE_PATH_TEMPLATE.format(type))
      with open(path) as json_file:
        json_data = json_file.read()
      data = json.loads(json_data)
      TemplateProvider.parsed_data[type] = data
      obj = copy.deepcopy(data)
    obj.update(kwargs)
    if type != "relationship" and "object_owner":
      contact = (
          {"contact": TemplateProvider.generate_object(1, objects.PEOPLE)})
      obj.update(contact)
    return {type: obj}

  @staticmethod
  def generate_object(id, type):
    """Return minimal object representation by id and type."""
    result = {}
    result["id"] = id
    result["href"] = "/".join([url.API, type, str(id)])
    result["type"] = objects.get_singular(type)
    return result
