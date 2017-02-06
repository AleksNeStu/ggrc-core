# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

# pylint: disable=invalid-name

"""Tests for notifications for models with assignable mixin."""

from datetime import datetime
from freezegun import freeze_time
from mock import patch
from sqlalchemy import and_

from ggrc import db
from ggrc.models import Assessment
from ggrc.models import Notification
from ggrc.models import NotificationType
from ggrc.models import Revision
from integration.ggrc import TestCase
from integration.ggrc import api_helper


class TestAssignableNotification(TestCase):

  """Test setting notifications for assignable mixin."""

  def setUp(self):
    super(TestAssignableNotification, self).setUp()
    self.client.get("/login")
    self._fix_notification_init()
    self.api_helper = api_helper.Api()

  def _fix_notification_init(self):
    """Fix Notification object init function.

    This is a fix needed for correct created_at field when using freezgun. By
    default the created_at field is left empty and filed by database, which
    uses system time and not the fake date set by freezugun plugin. This fix
    makes sure that object created in freeze_time block has all dates set with
    the correct date and time.
    """

    def init_decorator(init):
      """Wrapper for Notification init function."""

      def new_init(self, *args, **kwargs):
        init(self, *args, **kwargs)
        if hasattr(self, "created_at"):
          self.created_at = datetime.now()
      return new_init

    Notification.__init__ = init_decorator(Notification.__init__)

  @classmethod
  def _get_notifications(cls, sent=False, notif_type=None):
    """Get a notification query.

    Args:
      sent (boolean): flag to filter out only notifications that have been
        sent.
      notif_type (string): name of the notification type.

    Returns:
      sqlalchemy query for selected notifications.
    """
    if sent:
      notif_filter = Notification.sent_at.isnot(None)
    else:
      notif_filter = Notification.sent_at.is_(None)

    if notif_type:
      notif_filter = and_(notif_filter, NotificationType.name == notif_type)

    return db.session.query(Notification).join(NotificationType).filter(
        notif_filter
    )

  @patch("ggrc.notifications.common.send_email")
  def test_assessment_without_verifiers(self, _):
    """Test setting notification entries for simple assessments.

    This function tests that each assessment gets an entry in the
    notifications table after it's been created.
    Second part of the tests is to make sure that assessment status
    does not add any new notification entries if the assessment
    does not have a verifier.
    """

    with freeze_time("2015-04-01"):

      self.assertEqual(self._get_notifications().count(), 0)
      self.import_file("assessment_with_templates.csv")
      asmts = {asmt.slug: asmt for asmt in Assessment.query}

      notifications = self._get_notifications().all()
      self.assertEqual(len(notifications), 6)

      revisions = Revision.query.filter(
          Revision.resource_type == 'Notification',
          Revision.resource_id.in_([notif.id for notif in notifications])
      ).count()
      self.assertEqual(revisions, 6)

      self.api_helper.delete(asmts["A 1"])
      self.api_helper.delete(asmts["A 6"])

      self.assertEqual(self._get_notifications().count(), 4)

      self.client.get("/_notifications/send_daily_digest")
      self.assertEqual(self._get_notifications().count(), 0)

      asmt = Assessment.query.get(asmts["A 5"].id)

      self.api_helper.modify_object(asmt, {"status": Assessment.FINAL_STATE})
      self.assertEqual(self._get_notifications().count(), 0)
      self.api_helper.modify_object(asmt, {"status": Assessment.START_STATE})
      self.assertEqual(self._get_notifications().count(), 0)
      self.api_helper.modify_object(asmt,
                                    {"status": Assessment.PROGRESS_STATE})
      self.assertEqual(self._get_notifications().count(), 0)
      self.api_helper.modify_object(asmt, {"status": Assessment.FINAL_STATE})
      self.assertEqual(self._get_notifications().count(), 0)
      self.api_helper.modify_object(asmt,
                                    {"status": Assessment.PROGRESS_STATE})
      self.assertEqual(self._get_notifications().count(), 0)

  @patch("ggrc.notifications.common.send_email")
  def test_assessment_with_verifiers(self, _):
    """Test notifications entries for declined assessments.

    This tests makes sure there are extra notification entries added when a
    assessment has been declined.
    """

    with freeze_time("2015-04-01"):

      self.assertEqual(self._get_notifications().count(), 0)
      self.import_file("assessment_with_templates.csv")
      asmts = {asmt.slug: asmt for asmt in Assessment.query}

      notifications = self._get_notifications().all()
      self.assertEqual(len(notifications), 6)

      revisions = Revision.query.filter(
          Revision.resource_type == 'Notification',
          Revision.resource_id.in_([notif.id for notif in notifications])
      ).count()
      self.assertEqual(revisions, 6)

      self.client.get("/_notifications/send_daily_digest")
      self.assertEqual(self._get_notifications().count(), 0)

      asmt1 = Assessment.query.get(asmts["A 5"].id)
      # start and finish assessment 1
      self.api_helper.modify_object(asmt1,
                                    {"status": Assessment.PROGRESS_STATE})
      self.assertEqual(self._get_notifications().count(), 0)
      self.api_helper.modify_object(asmt1, {"status": Assessment.DONE_STATE})
      self.assertEqual(self._get_notifications().count(), 0)
      # decline assessment 1
      self.api_helper.modify_object(asmt1,
                                    {"status": Assessment.PROGRESS_STATE})
      self.assertEqual(self._get_notifications().count(), 1)
      self.api_helper.modify_object(asmt1, {"status": Assessment.DONE_STATE})
      self.assertEqual(self._get_notifications().count(), 1)
      # decline assessment 1 the second time
      self.api_helper.modify_object(asmt1,
                                    {"status": Assessment.PROGRESS_STATE})
      self.assertEqual(self._get_notifications().count(), 1)

      asmt6 = Assessment.query.get(asmts["A 6"].id)
      # start and finish assessment 6
      self.api_helper.modify_object(asmt6,
                                    {"status": Assessment.PROGRESS_STATE})
      self.assertEqual(self._get_notifications().count(), 1)
      self.api_helper.modify_object(asmt6, {"status": Assessment.DONE_STATE})
      self.assertEqual(self._get_notifications().count(), 1)
      # decline assessment 6
      self.api_helper.modify_object(asmt6,
                                    {"status": Assessment.PROGRESS_STATE})
      self.assertEqual(self._get_notifications().count(), 2)

      # send all notifications
      self.client.get("/_notifications/send_daily_digest")
      self.assertEqual(self._get_notifications().count(), 0)

      # Refresh the object because of the lost session due to the get call.
      asmt6 = Assessment.query.get(asmts["A 6"].id)
      self.api_helper.modify_object(asmt6,
                                    {"status": Assessment.PROGRESS_STATE})
      self.assertEqual(self._get_notifications().count(), 0)
      self.api_helper.modify_object(asmt6,
                                    {"status": Assessment.DONE_STATE})
      self.assertEqual(self._get_notifications().count(), 0)
      self.api_helper.modify_object(asmt6,
                                    {"status": Assessment.VERIFIED_STATE})
      self.assertEqual(self._get_notifications().count(), 0)
      self.api_helper.modify_object(asmt6,
                                    {"status": Assessment.PROGRESS_STATE})
      self.assertEqual(self._get_notifications().count(), 0)
      # decline assessment 6
      self.api_helper.modify_object(asmt6, {"status": Assessment.DONE_STATE})
      self.assertEqual(self._get_notifications().count(), 0)
      self.api_helper.modify_object(asmt6,
                                    {"status": Assessment.PROGRESS_STATE})
      self.assertEqual(self._get_notifications().count(), 1)
