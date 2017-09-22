# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Test suite for DELETE requests."""

from integration.ggrc import TestCase
from integration.ggrc.query_helper import WithQueryApi
from integration.ggrc.models import factories
from integration.ggrc.api_helper import Api

from ggrc import db
from ggrc.models import all_models


class TestDelete(TestCase, WithQueryApi):
  """Test objects deletion."""

  def setUp(self):
    super(TestDelete, self).setUp()
    self.client.get("/login")
    self.api = Api()

  def test_delete(self):
    """Deletion is synchronous and triggers compute_attributes."""
    control = factories.ControlFactory()

    result = self.api.delete(control)

    controls = db.session.query(all_models.Control).all()
    background_tasks = db.session.query(all_models.BackgroundTask).all()

    self.assert200(result)
    self.assertEqual(len(controls), 0)
    self.assertEqual(len(background_tasks), 1)
    self.assertTrue(background_tasks[0].name.startswith("compute_attributes"))

  def test_delete_http400(self):
    """Deletion returns HTTP400 if BadRequest is raised."""
    with factories.single_commit():
      audit = factories.AuditFactory()
      factories.AssessmentFactory(audit=audit)

    result = self.api.delete(audit)

    self.assert400(result)
