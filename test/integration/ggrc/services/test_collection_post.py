# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Tests for collection post service."""

import json

from ggrc import db
from ggrc import models
from integration.ggrc.services import TestCase


class TestCollectionPost(TestCase):
  """Test for collection post api calls."""

  @staticmethod
  def get_location(response):
    """Ignore the `http://localhost` prefix of the Location"""
    return response.headers['Location'][16:]

  @staticmethod
  def get_headers(*args, **kwargs):
    """Get request headers."""
    ret = list(args)
    ret.append(('X-Requested-By', 'Unit Tests'))
    ret.extend(kwargs.items())
    return ret

  def test_collection_post_successful(self):
    """Test normal successful collection post call."""
    data = json.dumps(
        {'services_test_mock_model': {'foo': 'bar', 'context': None}})
    self.client.get("/login")
    response = self.client.post(
        self.mock_url(),
        content_type='application/json',
        data=data,
        headers=self.get_headers(),
    )
    self.assertStatus(response, 201)
    self.assertIn('Location', response.headers)
    response = self.client.get(
        self.get_location(response), headers=self.get_headers())
    self.assert200(response)
    self.assertIn('Content-Type', response.headers)
    self.assertEqual('application/json', response.headers['Content-Type'])
    self.assertIn('services_test_mock_model', response.json)
    self.assertIn('foo', response.json['services_test_mock_model'])
    self.assertEqual('bar', response.json['services_test_mock_model']['foo'])
    # check the collection, too
    response = self.client.get(self.mock_url(), headers=self.get_headers())
    self.assert200(response)
    self.assertEqual(
        1, len(response.json['test_model_collection']['test_model']))
    self.assertEqual(
        'bar', response.json['test_model_collection']['test_model'][0]['foo'])

  def test_successful_single_array(self):
    """Test collection post successful single array."""
    data = json.dumps(
        [{'services_test_mock_model': {'foo': 'bar', 'context': None}}])
    self.client.get("/login")
    response = self.client.post(
        self.mock_url(),
        content_type='application/json',
        data=data,
        headers=self.get_headers(),
    )
    self.assert200(response)
    self.assertEqual(type(response.json), list)
    self.assertEqual(len(response.json), 1)

    response = self.client.get(self.mock_url(), headers=self.get_headers())
    self.assert200(response)
    self.assertEqual(
        1, len(response.json['test_model_collection']['test_model']))
    self.assertEqual(
        'bar', response.json['test_model_collection']['test_model'][0]['foo'])

  def test_successful_multiple(self):
    """Test collection post successful multiple."""
    data = json.dumps([
        {'services_test_mock_model': {'foo': 'bar1', 'context': None}},
        {'services_test_mock_model': {'foo': 'bar2', 'context': None}},
    ])
    self.client.get("/login")
    response = self.client.post(
        self.mock_url(),
        content_type='application/json',
        data=data,
        headers=self.get_headers(),
    )
    self.assert200(response)
    self.assertEqual(type(response.json), list)
    self.assertEqual(len(response.json), 2)
    self.assertEqual(
        'bar1', response.json[0][1]['services_test_mock_model']['foo'])
    self.assertEqual(
        'bar2', response.json[1][1]['services_test_mock_model']['foo'])
    response = self.client.get(self.mock_url(), headers=self.get_headers())
    self.assert200(response)
    self.assertEqual(
        2, len(response.json['test_model_collection']['test_model']))

  def test_multiple_with_errors(self):
    """Test collection post successful multiple with errors."""
    data = json.dumps([
        {'services_test_mock_model':
         {'foo': 'bar1', 'code': 'f1', 'context': None}},
        {'services_test_mock_model':
            {'foo': 'bar1', 'code': 'f1', 'context': None}},
        {'services_test_mock_model':
            {'foo': 'bar2', 'code': 'f2', 'context': None}},
        {'services_test_mock_model':
            {'foo': 'bar2', 'code': 'f2', 'context': None}},
    ])
    self.client.get("/login")
    response = self.client.post(
        self.mock_url(),
        content_type='application/json',
        data=data,
        headers=self.get_headers(),
    )

    self.assertEqual(400, response.status_code)
    self.assertEqual([400], [i[0] for i in response.json])
    response = self.client.get(self.mock_url(), headers=self.get_headers())
    self.assert200(response)
    self.assertEqual(
        0, len(response.json['test_model_collection']['test_model']))

  def test_post_bad_request(self):
    """Test collection post with invalid content."""
    response = self.client.post(
        self.mock_url(),
        content_type='application/json',
        data='This is most definitely not valid content.',
        headers=self.get_headers(),
    )
    self.assert400(response)
    self.assertEqual(
        response.json['message'],
        "The browser (or proxy) sent a request that this server "
        "could not understand.",
    )

  def test_bad_content_type(self):
    """Test post with bad content type."""
    response = self.client.post(
        self.mock_url(),
        content_type='text/plain',
        data="Doesn't matter, now does it?",
        headers=self.get_headers(),
    )
    self.assertStatus(response, 415)

  def test_post_relationship(self):
    """Test integrity error on relationship collection post.

    Posting duplicate relationships should have a mechanism for removing
    duplicates from the post request and fixing unique integrity errors.
    """
    db.session.add(models.Policy(id=144, title="hello"))
    db.session.add(models.Policy(id=233, title="world"))
    db.session.add(models.Policy(id=377, title="bye"))
    db.session.commit()

    self.client.get("/login")
    data = json.dumps([{
        "relationship": {
            "source": {"id": 144, "type": "Policy"},
            "destination": {"id": 233, "type": "Policy"},
            "context": None,
        },
    }])
    response = self.client.post(
        "/api/relationships",
        content_type='application/json',
        data=data,
        headers=self.get_headers(),
    )

    self.assert200(response)
    relationships = models.Relationship.eager_query().all()
    self.assertEqual(len(relationships), 1)
    rel1 = relationships[0]
    self.assertEqual({144, 233}, {rel1.source.id, rel1.destination.id})

    data = json.dumps([{
        "relationship": {  # this should be ignored
            "source": {"id": 144, "type": "Policy"},
            "destination": {"id": 233, "type": "Policy"},
            "context": None,
        },
    }, {
        "relationship": {
            "source": {"id": 377, "type": "Policy"},
            "destination": {"id": 144, "type": "Policy"},
            "context": None,
        },
    }, {
        "relationship": {  # Refactored api will ignore this
            "source": {"id": 144, "type": "Policy"},
            "destination": {"id": 377, "type": "Policy"},
            "context": None,
        },
    }])
    response = self.client.post(
        "/api/relationships",
        content_type='application/json',
        data=data,
        headers=self.get_headers(),
    )

    self.assert200(response)
    relationships = models.Relationship.eager_query().all()
    self.assertEqual(len(relationships), 3)  # This should be 2
    rel1 = relationships[0]
