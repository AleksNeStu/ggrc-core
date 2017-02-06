# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Tests for notifications for models with assignable mixin."""

from sqlalchemy import and_

from ggrc import db
from ggrc import contributions
from ggrc.models import Notification
from ggrc.models import NotificationType
from ggrc.models import Assessment
from ggrc.models import Revision
from integration.ggrc import api_helper
from integration.ggrc import TestCase
from integration.ggrc import generator


class TestAssessmentDataHandlers(TestCase):
  """Test data handlers for various Assessment notifications."""

  def setUp(self):
    super(TestAssessmentDataHandlers, self).setUp()
    self.client.get("/login")
    self.api_helper = api_helper.Api()
    self.import_file("assessment_notifications.csv")
    self.asmt1 = Assessment.query.filter_by(slug="A 1").one()
    self.asmt3 = Assessment.query.filter_by(slug="A 3").one()
    self.generator = generator.ObjectGenerator()
    self.handlers = contributions.contributed_notifications()

  def _call_notif_handler(self, notif):
    """Call the default data handler for the notification object.

    Args:
      notif (Notification): notification for which we want te get data

    Returns:
      Result of the data handler for the given object.
    """
    return self.handlers[notif.object_type](notif)

  @classmethod
  def _get_notification(cls, obj, notif_type):
    return db.session.query(Notification).join(NotificationType).filter(and_(
        Notification.object_id == obj.id,
        Notification.object_type == obj.type,
        NotificationType.name == notif_type,
    ))

  def test_open_assessment(self):
    """Test data handlers for opened requests."""
    notif = self._get_notification(self.asmt1, "assessment_open").first()

    revisions = Revision.query.filter_by(resource_type='Notification',
                                         resource_id=notif.id).count()
    self.assertEqual(revisions, 1)

    open_data = self._call_notif_handler(notif)
    asmt_1_expected_keys = {
        "user1@example.com",
        "user2@example.com",
        "user3@example.com"
    }

    self.assertEqual(set(open_data.keys()), asmt_1_expected_keys)

    notif = self._get_notification(self.asmt3, "assessment_open").first()

    revisions = Revision.query.filter_by(resource_type='Notification',
                                         resource_id=notif.id).count()
    self.assertEqual(revisions, 1)

    open_data = self._call_notif_handler(notif)
    asmt_4_expected_keys = {"user1@example.com", "user2@example.com"}

    self.assertEqual(set(open_data.keys()), asmt_4_expected_keys)

  def test_declined_assessment(self):
    """Test data handlers for declined assessments"""

    # decline assessment 1
    asmt1 = Assessment.query.filter_by(slug="A 1").first()
    self.api_helper.modify_object(asmt1, {"status": Assessment.DONE_STATE})
    self.api_helper.modify_object(asmt1, {"status": Assessment.PROGRESS_STATE})

    notif = self._get_notification(self.asmt1, "assessment_declined").first()

    revisions = Revision.query.filter_by(resource_type='Notification',
                                         resource_id=notif.id).count()
    self.assertEqual(revisions, 1)

    declined_data = self._call_notif_handler(notif)
    requester_emails = {"user1@example.com", }

    self.assertEqual(set(declined_data.keys()), requester_emails)

  def test_assessment_comments(self):
    """Test data handlers for comment to assessment"""
    asmt1 = Assessment.query.filter_by(slug="A 1").first()
    _, comment = self.generator.generate_comment(
        asmt1, "Verifier", "some comment", send_notification="true")

    notif = self._get_notification(comment, "comment_created").first()

    revisions = Revision.query.filter_by(resource_type='Notification',
                                         resource_id=notif.id).count()
    self.assertEqual(revisions, 1)

    declined_data = self._call_notif_handler(notif)
    requester_emails = {
        "user1@example.com",
        "user2@example.com",
        "user3@example.com"
    }

    self.assertEqual(set(declined_data.keys()), requester_emails)
