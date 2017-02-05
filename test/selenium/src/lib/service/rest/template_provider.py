# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""The module contains functionality for working with json templates"""
# pylint: disable=too-few-public-methods
# pylint: disable=redefined-builtin
# pylint: disable=invalid-name

import copy
import json
import os

from lib.constants import objects, url


class TemplateProvider(object):
  """Processes JSON templates."""
  RELATIVE_PATH_TEMPLATE = "template/{0}.json"
  parsed_data = dict()

  @classmethod
  def get_template_as_dict(cls, obj_type, **kwargs):
    """Return object representation based on JSON template."""
    try:
      obj = copy.deepcopy(cls.parsed_data[obj_type])
    except KeyError:
      path = os.path.join(
          os.path.dirname(__file__),
          cls.RELATIVE_PATH_TEMPLATE.format(obj_type))
      with open(path) as json_file:
        json_data = json_file.read()
      data = json.loads(json_data)
      cls.parsed_data[obj_type] = data
      obj = copy.deepcopy(data)
    obj.update(kwargs)
    if obj_type not in {"relationship", "object_owner"}:
      contact = (
          {"contact": cls.generate_object(1, objects.PEOPLE)})
      obj.update(contact)
    return {obj_type: obj}

  @staticmethod
  def generate_object(obj_id, obj_type):
    """Return minimal object representation by id and type."""
    result = {}
    result["id"] = obj_id
    result["href"] = "/".join([url.API, obj_type, str(obj_id)])
    result["type"] = objects.get_singular(obj_type)
    return result
