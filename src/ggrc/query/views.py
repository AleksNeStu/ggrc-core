# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""This module contains logic to handle '/query' endpoint."""

import time
import logging
from wsgiref.handlers import format_date_time

from flask import request
from flask import current_app
from werkzeug.exceptions import BadRequest

from ggrc.models import inflector
from ggrc.query.exceptions import BadQueryException
from ggrc.query.default_handler import DefaultHandler
from ggrc.query.assessment_related_objects import AssessmentRelatedObjects
from ggrc.login import login_required
from ggrc.models.inflector import get_model
from ggrc.services.common import etag
from ggrc.utils import as_json
from ggrc.utils import benchmark


logger = logging.getLogger()


OPTIMIZED_HANDLERS = [
    AssessmentRelatedObjects,
]


def build_collection_representation(model, description):
  """Enclose collection description into a type-describing block."""
  # pylint: disable=protected-access
  collection = {
      model.__name__: description,
  }
  return collection


def json_success_response(response_object, last_modified=None, status=200):
  """Build a 200-response with metadata headers."""
  headers = [
      ('Etag', etag(response_object)),
      ('Content-Type', 'application/json'),
  ]
  if last_modified is not None:
    headers.append(('Last-Modified', http_timestamp(last_modified)))

  return current_app.make_response(
      (as_json(response_object), status, headers),
  )


def http_timestamp(timestamp):
  return format_date_time(time.mktime(timestamp.utctimetuple()))


def _get_query_handler(query):
  """Get the first matching query handler for a given query."""
  for optimized_handler in OPTIMIZED_HANDLERS:
    try:
      if optimized_handler.match(query):
        return optimized_handler
    except Exception:  # pylint: disable=broad-except
      # No exception in the query matcher should affect the response of the
      # request. We need to safely fallback to default query handler if
      # anything happens.
      logger.info("Error matching %s handler.", optimized_handler.__name__)
  return DefaultHandler


def get_handler_results(query):
  """Get results from the best matching query handler.

  Args:
    query: dict containing query parameters.
  Returns:
    dict containing json serializable query results.
  """

  handler_class = _get_query_handler(query)

  query_handler = handler_class(query)
  name = query_handler.__class__.__name__
  with benchmark("Get query Handler results from: {}".format(name)):
    return query_handler.get_results()


def get_objects_by_query():
  """Return objects corresponding to a POST'ed query list."""
  query = request.json

  results = get_handler_results(query)

  last_modified_list = [result["last_modified"] for result in results
                        if result["last_modified"]]
  last_modified = max(last_modified_list) if last_modified_list else None
  collections = []
  collection_fields = ["ids", "values", "count", "total", "object_name"]

  for result in results:
    model = get_model(result["object_name"])

    collection = build_collection_representation(
        model,
        {
            field: result[field] for field in collection_fields
            if field in result
        }
    )
    collections.append(collection)

  return json_success_response(collections, last_modified)


def init_query_views(app):
  # pylint: disable=unused-variable
  @app.route('/query', methods=['POST'])
  @login_required
  def query_objects():
    """Advanced object collection queries view."""
    try:
      return get_objects_by_query()
    except (NotImplementedError, BadQueryException) as exc:
      raise BadRequest(exc.message)


def init_clone_views(app):
  # pylint: disable=unused-variable
  @app.route('/api/<model>/clone', methods=['POST'])
  @login_required
  def clone_objects(model):
    """Clone object view."""
    try:
      model_cls = inflector.get_model(model)
      if hasattr(model_cls, "clone"):
        return model_cls.handle_model_clone(request.json[0])
      else:
        raise NotImplementedError
    except (NotImplementedError, BadQueryException) as exc:
      raise BadRequest(exc.message)
