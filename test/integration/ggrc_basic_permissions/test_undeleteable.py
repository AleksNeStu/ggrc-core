# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""
Test that some objects cannot be deleted by anyone.
"""

from integration.ggrc import TestCase
from integration.ggrc.api_helper import Api
from integration.ggrc.generator import ObjectGenerator


class TestReader(TestCase):
  """Test that some objects cannot be deleted by anyone."""

  def setUp(self):
    super(TestReader, self).setUp()
    self.api = Api()
    self.object_generator = ObjectGenerator()
    self.init_users()
    self.init_objects()

  def init_users(self):
    """ Init users needed by the test cases """
    users = [("creator", "Creator"), ("reader", "Reader"),
             ("editor", "Editor"), ("admin", "Administrator")]
    self.users = {}
    for (name, role) in users:
      _, user = self.object_generator.generate_person(
          data={"name": name}, user_role=role)
      self.users[name] = user

  def init_objects(self):
    """Creates the objects used by all the tests"""
    self.api.set_user(self.users["admin"])
    _, person = self.object_generator.generate_person()

    self.objects = [person]

  def test_undeletable_objects(self):
    """No user shoud be allowed to delete these objects."""
    for role, user in self.users.iteritems():
      self.api.set_user(user)
      for obj in self.objects:
        response = self.api.delete(obj)
        self.assertEqual(response.status_code, 403,
                         "{} can delete {}".format(role, obj.type))
