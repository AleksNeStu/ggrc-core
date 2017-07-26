# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""REST API client."""
# pylint: disable=redefined-builtin

import Cookie
import json
import urlparse

import requests

from lib import environment
from lib.constants import url
from lib.service.rest.template_provider import TemplateProvider


class RestClient(object):
  """Client for HTTP interactions with GGRC's REST API."""
  BASIC_HEADERS = {'X-Requested-By': 'GGRC',
                   'Content-Type': 'application/json',
                   'Accept-Encoding': 'gzip, deflate'}

  STATUS_CODES = {'OK': 200,
                  'FAIL': [400, 404, 500]}

  def __init__(self, endpoint):
    self.is_api = "" if endpoint == url.QUERY else url.API
    self.url = urlparse.urljoin(environment.APP_URL,
                                "/".join([self.is_api, endpoint]))
    self.session_cookie = None

  def get_session_cookie(self):
    """Send GET request to login URL, get response and return session
    cookie from response headers for further usage.
    """
    resp = requests.get(urlparse.urljoin(environment.APP_URL, "/login"))
    cookies = Cookie.SimpleCookie()
    cookies.load(resp.headers["Set-Cookie"])
    self.session_cookie = cookies["session"].value

  def generate_req_headers(self, resp_headers=None):
    """Create request headers for further HTTP calls.
    If 'resp_headers' is 'None' than return request headers from predefined
    basic headers and session cookie.
    If 'resp_headers' is not 'None' than return request headers from
    predefined basic headers, session cookie and response headers.
    """
    req_headers = self.BASIC_HEADERS
    if self.session_cookie is None:
      self.get_session_cookie()
    req_headers["Cookie"] = "session={value}".format(value=self.session_cookie)
    if resp_headers:
      req_headers["If-Match"] = resp_headers["Etag"]
      req_headers["If-Unmodified-Since"] = resp_headers["Last-Modified"]
    return req_headers

  def create_object(self, type, **kwargs):
    """Create object or make other operations used POST request and
    return raw response.
    """
    req_headers = self.generate_req_headers()
    req_body = self.generate_body(type_name=type, **kwargs)
    resp = requests.post(url=self.url, data=req_body, headers=req_headers)
    return resp

  def update_object(self, href, **kwargs):
    """Update object used GET, POST requests and return raw response."""
    obj_url = urlparse.urljoin(environment.APP_URL, href)
    obj_resp_headers = self.get_object(obj_url)["resp_headers"]
    obj_resp_body = self.get_object(obj_url)["resp_body"]
    new_obj_req_headers = self.generate_req_headers(
        resp_headers=obj_resp_headers)
    new_obj_req_body = self.update_body(body=obj_resp_body, **kwargs)
    new_obj_resp = requests.put(url=obj_url, data=new_obj_req_body,
                                headers=new_obj_req_headers)
    return new_obj_resp

  def delete_object(self, href):
    """Delete object used GET, POST requests and return raw response."""
    obj_url = urlparse.urljoin(environment.APP_URL, href)
    obj_resp_headers = self.get_object(obj_url)["resp_headers"]
    del_obj_req_headers = self.generate_req_headers(
        resp_headers=obj_resp_headers)
    del_obj_resp = requests.delete(url=obj_url, headers=del_obj_req_headers)
    return del_obj_resp

  def get_object(self, obj_url):
    """Get object used GET request and return dictionary:
    {"resp_body": resp.text, "resp_headers": resp.headers}.
    """
    req_headers = self.generate_req_headers()
    resp = requests.get(url=obj_url, headers=req_headers)
    return {"resp_body": resp.text, "resp_headers": resp.headers}

  def generate_body(self, type_name, **kwargs):
    """Generate body of HTTP request based on JSON representation."""
    body = TemplateProvider.generate_template_as_dict(
        json_tmpl_name=type_name, **kwargs)
    if not self.is_api:
      body = body[type_name]
    return json.dumps([body])

  @staticmethod
  def update_body(body, **kwargs):
    """Update body of HTTP request based on JSON representation."""
    return json.dumps(TemplateProvider.update_template_as_dict(
        json_tmpl_name=body, **kwargs))
