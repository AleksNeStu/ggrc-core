# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>


"""Tests for task group task specific export."""
from ggrc import db
from ggrc.models import all_models
from integration.ggrc.models import factories
from integration.ggrc import TestCase


class TestExportControls(TestCase):
  """Test imports for basic control objects."""

  model = all_models.Control

  def setUp(self):
    with factories.single_commit():
      super(TestExportControls, self).setUp()
      self.client.get("/login")
      self.headers = {
          'Content-Type': 'application/json',
          "X-Requested-By": "GGRC",
          "X-export-view": "blocks",
      }
      self.basic_owner = factories.PersonFactory(name="basic owner")
      self.control = factories.ControlFactory()
      self.acr_id = all_models.AccessControlRole.query.filter_by(
          object_type=self.control.type,
          name="Admin"
      ).first().id
      self.owner_object = factories.AccessControlListFactory(
          person=self.basic_owner,
          object=self.control,
          ac_role_id=self.acr_id
      )

  def test_search_by_owner_email(self):
    self.assert_slugs("Admin",
                      self.basic_owner.email,
                      [self.control.slug])

  def test_search_by_owner_name(self):
    self.assert_slugs("Admin",
                      self.basic_owner.name,
                      [self.control.slug])

  def test_search_by_new_owner(self):
    """Filter by added new owner and old owner"""
    basic_email, basic_name = self.basic_owner.email, self.basic_owner.name
    new_owner = factories.PersonFactory(name="new owner")
    factories.AccessControlListFactory(
        person=new_owner,
        object=self.control,
        ac_role_id=self.acr_id
    )
    self.assert_slugs("Admin",
                      new_owner.email,
                      [self.control.slug])
    self.assert_slugs("Admin",
                      new_owner.name,
                      [self.control.slug])
    self.assert_slugs("Admin",
                      basic_email,
                      [self.control.slug])
    self.assert_slugs("Admin",
                      basic_name,
                      [self.control.slug])

  def test_search_by_deleted_owner(self):
    """Filter by deleted owner"""
    db.session.delete(self.owner_object)
    db.session.commit()
    self.assert_slugs("owners", self.basic_owner.email, [])
    self.assert_slugs("owners", self.basic_owner.name, [])
