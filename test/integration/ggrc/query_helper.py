# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Helper to use /query api endpoint."""

import json


class WithQueryApi(object):
  """Used to construct and perform requests to /query endpoint."""

  def _post(self, data):
    """Make a POST to /query endpoint."""
    if not isinstance(data, list):
      data = [data]
    headers = {"Content-Type": "application/json", }
    return self.client.post("/query", data=json.dumps(data), headers=headers)

  def _get_first_result_set(self, data, *keys):
    """Post data, get response, get values from it like in obj["a"]["b"]."""
    response = self._post(data)
    self.assert200(response)
    result = json.loads(response.data)[0]
    for key in keys:
      result = result.get(key)
      self.assertIsNot(result, None)
    return result

  @staticmethod
  def _make_query_dict_base(object_name, type_=None, filters=None,
                            limit=None, order_by=None):
    """Make a dict with query for object_name with optional parameters."""
    query = {
        "object_name": object_name,
        "filters": filters if filters else {"expression": {}},
    }
    if type_:
      query["type"] = type_
    if limit:
      query["limit"] = limit
    if order_by:
      query["order_by"] = order_by
    return query

  @staticmethod
  def make_filter_expression(expression):
    """Convert a three-tuple to a simple expression filter."""
    left, op_name, right = expression
    return {"left": left, "op": {"name": op_name}, "right": right}

  @classmethod
  def _make_query_dict(cls, object_name, expression=None, *args, **kwargs):
    """Make a dict with query for object_name with expression shortcut.

    expression should be in format: (left, op_name, right), like
    ("title", "=", "hello").
    """

    if expression:
      filters = {"expression": cls.make_filter_expression(expression)}
    else:
      filters = None

    return cls._make_query_dict_base(object_name, filters=filters, *args,
                                     **kwargs)

  def simple_query(self, model_name, expression=None, *args, **kwargs):
    return self._get_first_result_set(
        self._make_query_dict(
            model_name,
            expression=expression,
            *args,
            **kwargs
        ),
        model_name, "values"
    )
