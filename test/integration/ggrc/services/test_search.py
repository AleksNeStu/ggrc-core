# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""
Test /search REST API
"""

from ggrc.models import Control
from integration.ggrc import TestCase
from integration.ggrc.api_helper import Api
from integration.ggrc.generator import ObjectGenerator


class TestResource(TestCase):
  """
  Test /search REST API
  """

  def setUp(self):
    super(TestResource, self).setUp()
    self.api = Api()
    self.object_generator = ObjectGenerator()
    self.create_objects()

  def create_objects(self):
    """Create objects to be searched.

    Creates five controls and makes relationships.
    0   1   2   3   4
    |---|   |---|   |
    |-------|-------|
    """
    self.objects = [
        self.object_generator.generate_object(Control)[1].id
        for _ in xrange(5)
    ]
    self.objects = Control.eager_query().filter(
        Control.id.in_(self.objects)
    ).all()
    for src, dst in [(0, 1), (0, 2), (2, 3), (2, 4)]:
      self.object_generator.generate_relationship(
          self.objects[src], self.objects[dst]
      )

  def search(self, *args, **kwargs):
    res, _ = self.api.search(*args, **kwargs)
    return res.json["results"]["entries"]

  def test_search_all(self):
    """Test search for all objects of a type."""
    res, _ = self.api.search("Control")
    self.assertEqual(len(res.json["results"]["entries"]), 5)

  def test_search_query(self):
    """Test search with query by title."""
    entries = self.search("Control", q=self.objects[0].title)
    self.assertEqual({entry["id"] for entry in entries},
                     {self.objects[0].id})

  def test_search_relevant(self):
    """Test search with 'relevant to' single object."""
    relevant_objects = "Control:{}".format(self.objects[0].id)
    entries = self.search("Control", relevant_objects=relevant_objects)
    self.assertEqual({entry["id"] for entry in entries},
                     {self.objects[i].id for i in [1, 2]})

  def test_search_relevant_multi(self):
    """Test search with 'relevant to' multiple objects."""
    ids = ",".join("Control:{}".format(self.objects[i].id) for i in (0, 3))
    entries = self.search("Control", relevant_objects=ids)
    self.assertEqual({entry["id"] for entry in entries},
                     {self.objects[2].id})

  def test_search_fail_with_terms_none(self):
    """Test search to fail with BadRequest (400 Error) when terms are None."""
    query = '/search?types={}&counts_only={}'.format("Control", False)
    response = self.api.tc.get(query)
    self.assert400(response)
    self.assertEqual(response.json['message'], 'Query parameter "q" '
                     'specifying search terms must be provided.')
