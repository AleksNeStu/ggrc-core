# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Constants and methods for work with REST and QUERY API interactions."""


class Query(object):
  """Query API constants, templates, methods."""
  # pylint: disable=too-few-public-methods

  @staticmethod
  def expression_get_snapshoted_obj(obj_type, obj_id, parent_type, parent_id):
    """Expression to get snapshoted object according to original and parent
    objects attributes.
    """
    return {
        "expression": {
            "left": {
                "left": {
                    "left": "child_type",
                    "op": {"name": "="},
                    "right": obj_type
                },
                "op": {"name": "AND"},
                "right": {
                    "left": "child_id",
                    "op": {"name": "="},
                    "right": str(obj_id)
                }
            },
            "op": {"name": "AND"},
            "right": {
                "object_name": parent_type,
                "op": {"name": "relevant"},
                "ids": [str(parent_id)]
            }
        }
    }
