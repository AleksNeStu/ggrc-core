# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""The module contains classes for working with REST API."""
# pylint: disable=redefined-builtin

import Cookie
import json
import urlparse

import requests

from lib import environment
from lib.constants import url
from lib.service.rest.template_provider import TemplateProvider


class RestClient(object):
  """Used for HTTP interactions with App's REST API."""
  BASIC_HEADERS = {'X-Requested-By': 'GGRC',
                   'Content-Type': 'application/json',
                   'Accept-Encoding': 'gzip, deflate'}

  def __init__(self, endpoint):
    self.url = urlparse.urljoin(environment.APP_URL,
                                "/".join([url.API, endpoint]))
    self.session = None

  def init_session(self):
    """Return authorization cookie value."""
    response = requests.get(urlparse.urljoin(environment.APP_URL, "/login"))
    cookie = Cookie.SimpleCookie()
    cookie.load(response.headers["Set-Cookie"])
    self.session = cookie["session"].value

  def get_headers(self):
    """Return prepared header for HTTP call."""
    headers = self.BASIC_HEADERS
    if self.session is None:
      self.init_session()
    headers["Cookie"] = "session={0}".format(self.session)
    return headers

  def create_object(self, type, title=None, title_postfix=None, **kwargs):
    """Send HTTP request used POST method to create object via REST API."""
    request_body = generate_body_by_template(
        template_name=type, title=title, title_postfix=title_postfix, **kwargs)
    headers = self.get_headers()
    response = requests.post(url=self.url, data=request_body, headers=headers)
    return response


def generate_body_by_template(template_name, title, title_postfix, **kwargs):
  """Generate object based on object type or relationships between
  objects. Object type can be assessment, control, etc from JSON templates.
  """
  def upgrade_template(template_name, title, title_postfix, **kwargs):
    """Return updated JSON template according requirements."""
    if template_name == "relationship" or template_name == "object_owner":
      return TemplateProvider.get_template_as_dict(template_name, **kwargs)
    else:
      if title_postfix is not None:
        title += title_postfix
      return TemplateProvider.get_template_as_dict(template_name,
                                                   title=title, **kwargs)
  object = [upgrade_template(template_name=template_name, title=title,
                             title_postfix=title_postfix, **kwargs)]
  return json.dumps(object)
