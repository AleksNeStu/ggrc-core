# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Tests API response codes."""

import json
from mock import patch

from integration.ggrc.services import TestCase


class TestCollectionPost(TestCase):
  """Test response codes for post requests."""

  def setUp(self):
    super(TestCollectionPost, self).setUp()
    self.client.get("/login")

  def _post(self, data):
    return self.client.post(
        self.mock_url(),
        content_type='application/json',
        data=data,
        headers=[('X-Requested-By', 'Unit Tests')],
    )

  def test_post_successful_response(self):
    """Test successful model post call."""
    data = json.dumps({
        'services_test_mock_model': {
            'foo': 'bar',
            'code': '1',
            'validated': 'good',
            'context': None
        }}
    )
    response = self._post(data)
    self.assertStatus(response, 201)

  def test_post_bad_request(self):
    """Test all bad request calls."""
    data = json.dumps({
        'services_test_mock_model': {
            'foo': 'bar',
            'code': '1',
            'validated': 'Value Error',
            'context': None
        }}
    )
    response = self._post(data)
    self.assert400(response)
    # TODO: check why response.json contains unwrapped string
    self.assertEqual(response.json, "raised Value Error")

    data = json.dumps({
        'services_test_mock_model': {
            'foo': 'bar',
            'code': '1',
            'validated': 'Validation Error',
            'context': None
        }}
    )
    response = self._post(data)
    self.assert400(response)
    # TODO: check why response.json contains unwrapped string
    self.assertEqual(response.json, "raised Validation Error")

    response = self._post("what")
    self.assert400(response)
    self.assertEqual(response.json["message"],
                     "The browser (or proxy) sent a request that this server "
                     "could not understand.")

  @patch("ggrc.rbac.permissions.is_allowed_create_for")
  def test_post_forbidden(self, is_allowed):
    """Test posting a forbidden model."""
    is_allowed.return_value = False
    data = json.dumps({
        'services_test_mock_model': {
            'foo': 'bar',
            'code': '1',
            'validated': 'good',
            'context': None
        }}
    )
    response = self._post(data)
    self.assertStatus(response, 403)
