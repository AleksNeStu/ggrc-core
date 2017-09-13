# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Tests for /api/<model> endpoints."""

import mock

import json
import time
from urlparse import urlparse
from wsgiref.handlers import format_date_time
from sqlalchemy import and_

from integration.ggrc.services import TestCase
from integration.ggrc.api_helper import Api
from integration.ggrc.generator import ObjectGenerator
from ggrc.models import all_models
from ggrc import db


COLLECTION_ALLOWED = ["HEAD", "GET", "POST", "OPTIONS"]
RESOURCE_ALLOWED = ["HEAD", "GET", "PUT", "DELETE", "OPTIONS"]


class TestServices(TestCase):
  """Integration tests suite for /api/<model> endpoints common logic."""

  @staticmethod
  def get_location(response):
    """Ignore the `http://localhost` prefix of the Location"""
    return response.headers["Location"][16:]

  def assert_required_headers(self, response, headers=None):
    """Check if response has the provided list of headers."""
    if headers is None:
      headers = {"Content-Type": "application/json"}
    self.assertIn("Etag", response.headers)
    self.assertIn("Last-Modified", response.headers)
    self.assertIn("Content-Type", response.headers)
    for header, value in headers.items():
      self.assertEqual(value, response.headers.get(header))

  def assert_allow(self, response, allowed=None):
    self.assert405(response)
    self.assertIn("Allow", response.headers)
    if allowed:
      self.assertItemsEqual(allowed, response.headers["Allow"].split(", "))

  def assert_options(self, response, allowed):
    self.assertIn("Allow", response.headers)
    self.assertItemsEqual(allowed, response.headers["Allow"].split(", "))

  @staticmethod
  def get_headers(*args, **kwargs):
    ret = list(args)
    ret.append(("X-Requested-By", "Unit Tests"))
    ret.extend(kwargs.items())
    return ret

  def test_x_requested_by_required(self):
    response = self.client.post(self.mock_url())
    self.assert400(response)
    self.assertEqual(response.json['message'],
                     "X-Requested-By header is REQUIRED.")
    response = self.client.put(self.mock_url() + "/1", data="blah")
    self.assert400(response)
    self.assertEqual(response.json['message'],
                     "X-Requested-By header is REQUIRED.")
    response = self.client.delete(self.mock_url() + "/1")
    self.assert400(response)
    self.assertEqual(response.json['message'],
                     "X-Requested-By header is REQUIRED.")

  def test_empty_collection_get(self):
    response = self.client.get(self.mock_url(), headers=self.get_headers())
    self.assert200(response)

  def test_missing_resource_get(self):
    response = self.client.get(self.mock_url("foo"),
                               headers=self.get_headers())
    self.assert404(response)

  def test_collection_put(self):
    self.assert_allow(
        self.client.put(self.mock_url(), headers=self.get_headers()),
        COLLECTION_ALLOWED)

  def test_collection_delete(self):
    self.assert_allow(
        self.client.delete(self.mock_url(), headers=self.get_headers()),
        COLLECTION_ALLOWED)

  def _prepare_model_for_put(self, foo_param="buzz"):
    """Common object initializing sequence."""
    mock = self.mock_model(foo=foo_param)
    response = self.client.get(self.mock_url(mock.id),
                               headers=self.get_headers())
    self.assert200(response)
    self.assert_required_headers(response)
    return response

  @mock.patch("ggrc.views.start_compute_attributes")
  def test_put_successful(self, _):
    """PUT with correct headers and data succeeds and returns new object."""
    response = self._prepare_model_for_put(foo_param="buzz")
    obj = response.json
    self.assertEqual("buzz", obj["services_test_mock_model"]["foo"])
    obj["services_test_mock_model"]["foo"] = "baz"
    url = urlparse(obj["services_test_mock_model"]["selfLink"]).path
    original_headers = dict(response.headers)
    # wait a moment so that we can be sure to get differing Last-Modified
    # after the put - the lack of latency means it's easy to end up with
    # the same HTTP timestamp thanks to the standard's lack of precision.
    time.sleep(1.1)
    response = self.client.put(
        url,
        data=json.dumps(obj),
        headers=self.get_headers(
            ("If-Unmodified-Since", original_headers["Last-Modified"]),
            ("If-Match", original_headers["Etag"]),
        ),
        content_type="application/json",
    )
    self.assert200(response)
    response = self.client.get(url, headers=self.get_headers())
    self.assert200(response)
    self.assertNotEqual(
        original_headers["Last-Modified"], response.headers["Last-Modified"])
    self.assertNotEqual(
        original_headers["Etag"], response.headers["Etag"])
    self.assertEqual("baz", response.json["services_test_mock_model"]["foo"])

  def test_put_required_attribute_error(self):  # pylint: disable=invalid-name
    """Test response for put request with wrong required attribute error."""
    response = self._prepare_model_for_put(foo_param="buzz")
    obj = response.json
    url = urlparse(obj["services_test_mock_model"]["selfLink"]).path
    original_headers = dict(response.headers)
    del obj["services_test_mock_model"]
    response = self.client.put(
        url,
        data=json.dumps(obj),
        headers=self.get_headers(
            ("If-Unmodified-Since", original_headers["Last-Modified"]),
            ("If-Match", original_headers["Etag"]),
        ),
        content_type="application/json",
    )
    self.assert400(response)
    self.assertEqual(
        response.json['message'],
        'Required attribute "services_test_mock_model" not found')

  def test_put_value_error(self):
    """Test response code for put request with value errors."""
    response = self._prepare_model_for_put(foo_param="buzz")
    obj = response.json
    obj["services_test_mock_model"]["validated"] = "Value Error"
    url = urlparse(obj["services_test_mock_model"]["selfLink"]).path
    original_headers = dict(response.headers)
    response = self.client.put(
        url,
        data=json.dumps(obj),
        headers=self.get_headers(
            ("If-Unmodified-Since", original_headers["Last-Modified"]),
            ("If-Match", original_headers["Etag"]),
        ),
        content_type="application/json",
    )
    self.assert400(response)
    self.assertEqual(response.json['message'], "raised Value Error")

  def test_put_bad_request(self):
    """PUT of an invalid object data returns HTTP 400."""
    response = self._prepare_model_for_put(foo_param="tough")
    url = urlparse(response.json["services_test_mock_model"]["selfLink"]).path
    response = self.client.put(
        url,
        content_type="application/json",
        data="This is most definitely not valid content.",
        headers=self.get_headers(
            ("If-Unmodified-Since", response.headers["Last-Modified"]),
            ("If-Match", response.headers["Etag"]))
    )
    self.assert400(response)
    self.assertEqual(response.json['message'],
                     "The browser (or proxy) sent a request that "
                     "this server could not understand.")

  def test_put_428(self):
    """Headers "If-Match" and "If-Unmodified-Since" are required on PUT."""
    response = self._prepare_model_for_put(foo_param="bar")

    def put_with_headers(*headers):
      """Issue a PUT request with some headers."""
      url = urlparse(response.json
                     ["services_test_mock_model"]
                     ["selfLink"]).path
      obj = response.json
      return self.client.put(
          url,
          content_type="application/json",
          data=json.dumps(obj),
          headers=self.get_headers(*headers),
      )

    def check_response_428(response, missing_headers):
      """Make common assertions about 428-response, check missing headers."""
      self.assertEqual(response.status_code, 428)
      self.assertIn("message", response.json)
      error_message = response.json["message"]
      self.assertTrue(error_message.startswith("Missing headers: "))
      self.assertSetEqual(
          set(header.strip() for header in
              error_message[len("Missing headers: "):].split(",")),
          set(missing_headers),
      )

    response_etag_and_date_missing = put_with_headers()
    check_response_428(response_etag_and_date_missing,
                       missing_headers={"If-Match", "If-Unmodified-Since"})

    response_etag_missing = put_with_headers(
        ("If-Unmodified-Since", response.headers["Last-Modified"]),
    )
    check_response_428(response_etag_missing,
                       missing_headers={"If-Match"})

    response_date_missing = put_with_headers(
        ("If-Match", response.headers["Etag"]),
    )
    check_response_428(response_date_missing,
                       missing_headers={"If-Unmodified-Since"})

  def test_put_409(self):
    """Last modified timestamp and etag are checked on PUT."""
    response = self._prepare_model_for_put(foo_param="bas")

    def put_with_headers(*headers):
      """Issue a PUT request with some headers."""
      url = urlparse(response.json
                     ["services_test_mock_model"]
                     ["selfLink"]).path
      obj = response.json
      return self.client.put(
          url,
          content_type="application/json",
          data=json.dumps(obj),
          headers=self.get_headers(*headers),
      )

    def check_response_409(response):
      """Make common assertions about 428-response, check error message."""
      self.assertEqual(response.status_code, 409)
      self.assertIn("message", response.json)
      self.assertIsInstance(response.json["message"], basestring)

    def invalid_date():
      return format_date_time(0)  # 1970-01-01

    def invalid_etag():
      return "Definitely invalid etag"

    response_etag_and_date_invalid = put_with_headers(
        ("If-Unmodified-Since", invalid_date()),
        ("If-Match", invalid_etag()),
    )
    check_response_409(response_etag_and_date_invalid)

    response_etag_invalid = put_with_headers(
        ("If-Unmodified-Since", response.headers["Last-Modified"]),
        ("If-Match", invalid_etag()),
    )
    check_response_409(response_etag_invalid)

    response_date_invalid = put_with_headers(
        ("If-Unmodified-Since", invalid_date()),
        ("If-Match", response.headers["Etag"]),
    )
    check_response_409(response_date_invalid)

  def test_options(self):
    mock = self.mock_model()
    response = self.client.open(
        self.mock_url(mock.id), method="OPTIONS", headers=self.get_headers())
    self.assert_options(response, RESOURCE_ALLOWED)

  def test_collection_options(self):
    response = self.client.open(
        self.mock_url(), method="OPTIONS", headers=self.get_headers())
    self.assert_options(response, COLLECTION_ALLOWED)

  def test_get_bad_accept(self):
    mock1 = self.mock_model(foo="baz")
    response = self.client.get(
        self.mock_url(mock1.id),
        headers=self.get_headers(("Accept", "text/plain")))
    self.assertStatus(response, 406)
    self.assertEqual("text/plain", response.headers.get("Content-Type"))
    self.assertEqual("application/json", response.data)

  def test_collection_get_bad_accept(self):
    response = self.client.get(
        self.mock_url(),
        headers=self.get_headers(("Accept", "text/plain")))
    self.assertStatus(response, 406)
    self.assertEqual("text/plain", response.headers.get("Content-Type"))
    self.assertEqual("application/json", response.data)

  def test_get_if_none_match(self):
    mock1 = self.mock_model(foo="baz")
    response = self.client.get(
        self.mock_url(mock1.id),
        headers=self.get_headers(("Accept", "application/json")))
    self.assert200(response)
    previous_headers = dict(response.headers)
    response = self.client.get(
        self.mock_url(mock1.id),
        headers=self.get_headers(
            ("Accept", "application/json"),
            ("If-None-Match", previous_headers["Etag"]),
        ),
    )
    self.assertStatus(response, 304)
    self.assertIn("Etag", response.headers)


class TestFilteringByRequest(TestCase):
  """Test filter query by request"""

  def setUp(self):
    super(TestFilteringByRequest, self).setUp()
    self.object_generator = ObjectGenerator()
    self.api = Api()
    self.init_users()

  def init_users(self):
    """ Init users needed by the test cases """
    users = (
        ("creator", "Creator"),
        ("admin", "Administrator"),
        ("john", "WorkflowOwner")
    )
    self.users = {}
    for (name, role) in users:
      _, user = self.object_generator.generate_person(
          data={"name": name}, user_role=role)
      self.users[name] = user
    context = (
        db.session.query(all_models.Context).filter(
            all_models.Context.id != 0
        ).first()
    )
    user_role = (
        db.session.query(all_models.UserRole).join(all_models.Person).
        filter(
            and_(
                all_models.UserRole.person_id == all_models.Person.id,
                all_models.Person.name == "john"
            )
        ).first()
    )
    user_role.context_id = context.id
    db.session.commit()
    db.session.flush()

  def test_no_role_users_filtering(self):
    """Test 'No Role' users filtering"""
    self.api.set_user(self.users['admin'])
    response = self.api.get_query(all_models.Person, "__no_role=true")

    self.assertEqual(response.status_code, 200)
    self.assertEqual(len(response.json['people_collection']['people']), 1)
    self.assertEqual(
        response.json['people_collection']['people'][0]['name'],
        'john'
    )
