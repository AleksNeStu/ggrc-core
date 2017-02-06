# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

import json
from flask import request, current_app
from flask.views import MethodView

"""RESTful service discovery API for GGRC services."""


class ServiceDescription(MethodView):
  """Flask view providing a RESTful service discovery resource for all GGRC
  resources, resource collections and services.
  """
  def get(self):
    from ggrc import services
    endpoints = {}
    for entry in services.all_services():
      service = getattr(services, entry.model_class.__name__)
      endpoints[service.__name__] = {
          'href': service.url_for(),
          # TODO additional fields
          # 'discoveryVersion': '',
          # 'id': '',
          # 'name': '',
          # 'version': '',
          # 'title': '',
          # 'description': '',
          # 'documentationLink': '',
      }
    endpoints['search'] = {'href': '/search'}
    endpoints['log_event'] = {'href': '/api/log_events'}
    return self.json_success_response({
        'service_description': {
            'name': 'GGRC-Core',
            'endpoints': endpoints,
            'selfLink': request.url,
            # TODO additional fields
            # 'id': '',
            # 'title': '',
            # 'description': '',
            # 'documentationLink': '',
        },
    })

  def json_success_response(self, response_object, status=200):
    headers = [
        # ('Last-Modified', self.http_timestamp(last_modified)),
        # ('Etag', self.etag(response_object)),
        ('Content-Type', 'application/json'),
        # ('Location', self.url_for())
    ]
    return current_app.make_response(
        (json.dumps(response_object), status, headers))
