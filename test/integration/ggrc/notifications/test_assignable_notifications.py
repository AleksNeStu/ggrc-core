# -*- coding: utf-8 -*-

# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

# pylint: disable=invalid-name,too-many-lines

"""Tests for notifications for models with assignable mixin."""

import unittest

from collections import OrderedDict
from datetime import datetime
from freezegun import freeze_time
from mock import patch
from sqlalchemy import and_

from ggrc import db
from ggrc.models import Assessment
from ggrc.models import Notification
from ggrc.models import NotificationType
from ggrc.models import Revision
from ggrc.models import Relationship
from integration.ggrc import TestCase
from integration.ggrc import api_helper, generator
from integration.ggrc.models import factories

from integration.ggrc.models.factories import \
    CustomAttributeDefinitionFactory as CAD


class TestAssignableNotification(TestCase):
  """Base class for testing notification creation for assignable mixin."""

  def setUp(self):
    super(TestAssignableNotification, self).setUp()
    self.client.get("/login")
    self._fix_notification_init()
    factories.AuditFactory(slug="Audit")

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


class TestAssignableNotificationUsingImports(TestAssignableNotification):
  """Tests for notifications when interacting with objects through imports."""

  @patch("ggrc.notifications.common.send_email")
  def test_assessment_created_notifications(self, send_email):
    """Test if importing new assessments results in notifications for all."""
    self.assertEqual(self._get_notifications().count(), 0)

    self.import_file("assessment_with_templates.csv")
    titles = [asmt.title for asmt in Assessment.query]

    query = self._get_notifications(notif_type="assessment_open")
    self.assertEqual(query.count(), 6)

    # check email content
    self.client.get("/_notifications/send_daily_digest")
    recipient, _, content = send_email.call_args[0]

    self.assertEqual(recipient, u"user@example.com")
    self.assertIn(u"New assessments were created", content)
    for asmt_title in titles:
      self.assertIn(asmt_title, content)

  @patch("ggrc.notifications.common.send_email")
  def test_assessment_updated_notifications(self, send_email):
    """Test if updating an assessment results in a notification."""
    self.import_file("assessment_with_templates.csv")

    asmts = {asmt.slug: asmt for asmt in Assessment.query}
    asmt = Assessment.query.get(asmts["A 1"].id)
    asmt_id, asmt_slug = asmt.id, asmt.slug

    asmt.status = Assessment.PROGRESS_STATE
    db.session.commit()

    self.client.get("/_notifications/send_daily_digest")
    self.assertEqual(self._get_notifications().count(), 0)
    asmt = Assessment.query.get(asmt_id)

    self.import_data(OrderedDict([
        (u"object_type", u"Assessment"),
        (u"Code*", asmt.slug),
        (u"Title", u"New Assessment 1 title"),
    ]))

    query = self._get_notifications(notif_type="assessment_updated")
    self.assertEqual(query.count(), 1)

    # check email content
    self.client.get("/_notifications/send_daily_digest")
    recipient, _, content = send_email.call_args[0]

    self.assertEqual(recipient, u"user@example.com")
    self.assertIn(u"Assessments have been updated", content)

    # the assessment updated notification should not be sent if there exists a
    # status change notification , regardless of the order of actions
    self.import_data(OrderedDict([
        (u"object_type", u"Assessment"),
        (u"Code*", asmt_slug),
        (u"Title", u"New Assessment 1 title 2"),
    ]))
    query = self._get_notifications(notif_type="assessment_updated")
    self.assertEqual(query.count(), 1)

    self.import_data(OrderedDict([
        (u"object_type", u"Assessment"),
        (u"Code*", asmt_slug),
        (u"State*", Assessment.DONE_STATE),
    ]))

    self.import_data(OrderedDict([
        (u"object_type", u"Assessment"),
        (u"Code*", asmt_slug),
        (u"Title", u"New Assessment 1 title 3"),
    ]))

    self.client.get("/_notifications/send_daily_digest")
    recipient, _, content = send_email.call_args[0]
    self.assertNotIn(u"Assessments have been updated", content)

  @unittest.skip("An issue needs to be fixed.")
  @patch("ggrc.notifications.common.send_email")
  def test_assessment_ca_updated_notifications(self, send_email):
    """Test if updating assessment custom attr. results in a notification."""
    CAD(definition_type="assessment", title="CA_misc_remarks")

    self.import_file("assessment_with_templates.csv")
    self.client.get("/_notifications/send_daily_digest")
    self.assertEqual(self._get_notifications().count(), 0)

    asmts = {asmt.slug: asmt for asmt in Assessment.query}
    asmt = Assessment.query.get(asmts["A 1"].id)

    self.import_data(OrderedDict([
        (u"object_type", u"Assessment"),
        (u"Code*", asmt.slug),
        (u"CA_misc_remarks", u"CA new value"),
    ]))

    asmt = Assessment.query.get(asmts["A 1"].id)

    query = self._get_notifications(notif_type="assessment_updated")
    self.assertEqual(query.count(), 1)

    # check email content
    self.client.get("/_notifications/send_daily_digest")
    recipient, _, content = send_email.call_args[0]

    self.assertEqual(recipient, u"user@example.com")
    self.assertIn(u"Assessments have been updated", content)

  @unittest.skip("An issue needs to be fixed.")
  @patch("ggrc.notifications.common.send_email")
  def test_assessment_url_updated_notifications(self, send_email):
    """Test if updating assessment URLs results in a notification."""
    self.import_file("assessment_with_templates.csv")

    asmts = {asmt.slug: asmt for asmt in Assessment.query}
    asmt = Assessment.query.get(asmts["A 1"].id)
    asmt_id = asmt.id

    asmt.status = Assessment.PROGRESS_STATE
    db.session.commit()

    self.client.get("/_notifications/send_daily_digest")
    self.assertEqual(self._get_notifications().count(), 0)
    asmt = Assessment.query.get(asmt_id)

    self.import_data(OrderedDict([
        (u"object_type", u"Assessment"),
        (u"Code*", asmt.slug),
        (u"Url", u"www.foo-url.bar"),
    ]))

    query = self._get_notifications(notif_type="assessment_updated")
    self.assertEqual(query.count(), 1)

    # check email content
    self.client.get("/_notifications/send_daily_digest")
    recipient, _, content = send_email.call_args[0]

    self.assertEqual(recipient, u"user@example.com")
    self.assertIn(u"Assessments have been updated", content)

  @unittest.skip("An issue needs to be fixed.")
  @patch("ggrc.notifications.common.send_email")
  def test_attaching_assessment_evidence_notifications(self, send_email):
    """Test if attaching assessment evidence results in a notification."""
    self.import_file("assessment_with_templates.csv")

    asmts = {asmt.slug: asmt for asmt in Assessment.query}
    asmt = Assessment.query.get(asmts["A 1"].id)
    asmt_id = asmt.id

    asmt.status = Assessment.PROGRESS_STATE
    db.session.commit()

    self.client.get("/_notifications/send_daily_digest")
    self.assertEqual(self._get_notifications().count(), 0)
    asmt = Assessment.query.get(asmt_id)

    self.import_data(OrderedDict([
        (u"object_type", u"Assessment"),
        (u"Code*", asmt.slug),
        (u"Evidence", u"https://gdrive.com/qwerty1/view evidence.txt"),
    ]))

    query = self._get_notifications(notif_type="assessment_updated")
    self.assertEqual(query.count(), 1)

    # check email content
    self.client.get("/_notifications/send_daily_digest")
    recipient, _, content = send_email.call_args[0]

    self.assertEqual(recipient, u"user@example.com")
    self.assertIn(u"Assessments have been updated", content)

  @unittest.skip("An issue needs to be fixed.")
  @patch("ggrc.notifications.common.send_email")
  def test_assessment_person_updated_notifications(self, send_email):
    """Test if updating assessment people results in a notification."""
    self.import_file("assessment_with_templates.csv")

    asmts = {asmt.slug: asmt for asmt in Assessment.query}
    asmt = Assessment.query.get(asmts["A 1"].id)
    asmt_id = asmt.id

    asmt.status = Assessment.PROGRESS_STATE
    db.session.commit()

    self.client.get("/_notifications/send_daily_digest")
    self.assertEqual(self._get_notifications().count(), 0)
    asmt = Assessment.query.get(asmt_id)

    # change assignee
    self.import_data(OrderedDict([
        (u"object_type", u"Assessment"),
        (u"Code*", asmt.slug),
        (u"Assignee*", u"john@doe.com"),
    ]))

    query = self._get_notifications(notif_type="assessment_updated")
    self.assertEqual(query.count(), 1)

    # clear notifications
    self.client.get("/_notifications/send_daily_digest")
    self.assertEqual(self._get_notifications().count(), 0)
    asmt = Assessment.query.get(asmt_id)

    # change verifier
    asmt = Assessment.query.get(asmt_id)
    self.import_data(OrderedDict([
        (u"object_type", u"Assessment"),
        (u"Code*", asmt.slug),
        (u"Verifier", u"bob@dylan.com"),
    ]))

    query = self._get_notifications(notif_type="assessment_updated")
    self.assertEqual(query.count(), 1)

    # check email content
    self.client.get("/_notifications/send_daily_digest")
    recipient, _, content = send_email.call_args[0]

    self.assertEqual(recipient, u"user@example.com")
    self.assertIn(u"Assessments have been updated", content)

  @patch("ggrc.notifications.common.send_email")
  def test_assessment_state_change_notifications(self, send_email):
    """Test if updating assessment state results in notifications."""
    # pylint: disable=too-many-statements

    self.import_file("assessment_with_templates.csv")

    asmts = {asmt.slug: asmt for asmt in Assessment.query}
    asmt = Assessment.query.get(asmts["A 1"].id)
    asmt_id, asmt_slug = asmt.id, asmt.slug

    # test starting an assessment
    self.import_data(OrderedDict([
        (u"object_type", u"Assessment"),
        (u"Code*", asmt_slug),
        (u"State*", Assessment.PROGRESS_STATE),
    ]))

    self.client.get("/_notifications/send_daily_digest")
    recipient, _, content = send_email.call_args[0]

    self.assertEqual(recipient, u"user@example.com")
    self.assertRegexpMatches(content, ur"Assessment\s+has\s+been\s+started")

    # test submitting assessment for review
    self.client.get("/_notifications/send_daily_digest")
    self.assertEqual(self._get_notifications().count(), 0)

    self.import_data(OrderedDict([
        (u"object_type", u"Assessment"),
        (u"Code*", asmt_slug),
        (u"State*", Assessment.DONE_STATE),
    ]))

    query = self._get_notifications(notif_type="assessment_ready_for_review")
    self.assertEqual(query.count(), 1)

    self.client.get("/_notifications/send_daily_digest")
    recipient, _, content = send_email.call_args[0]
    self.assertEqual(recipient, u"user@example.com")
    self.assertIn(u"Assessments ready for review", content)

    # test verifying an assessment
    self.assertEqual(self._get_notifications().count(), 0)

    self.import_data(OrderedDict([
        (u"object_type", u"Assessment"),
        (u"Code*", asmt_slug),
        (u"State*", Assessment.FINAL_STATE),
        # (will get verified, because there is a verifier assigned)
    ]))

    query = self._get_notifications(notif_type="assessment_verified")
    self.assertEqual(query.count(), 1)

    self.client.get("/_notifications/send_daily_digest")
    recipient, _, content = send_email.call_args[0]
    self.assertEqual(recipient, u"user@example.com")
    self.assertIn(u"Verified assessments", content)

    # test reopening a verified assessment
    self.assertEqual(self._get_notifications().count(), 0)

    self.import_data(OrderedDict([
        (u"object_type", u"Assessment"),
        (u"Code*", asmt_slug),
        (u"State*", Assessment.PROGRESS_STATE),
    ]))

    query = self._get_notifications(notif_type="assessment_reopened")
    self.assertEqual(query.count(), 1)

    self.client.get("/_notifications/send_daily_digest")
    recipient, _, content = send_email.call_args[0]
    self.assertEqual(recipient, u"user@example.com")
    self.assertIn(u"Reopened assessments", content)

    # sending an assessment back to "in review" (i.e. the undo action)
    asmt = Assessment.query.get(asmt_id)
    asmt.status = Assessment.VERIFIED_STATE
    db.session.commit()

    self.assertEqual(self._get_notifications().count(), 0)

    self.import_data(OrderedDict([
        (u"object_type", u"Assessment"),
        (u"Code*", asmt_slug),
        (u"State*", Assessment.DONE_STATE),
    ]))

    query = self._get_notifications()
    self.assertEqual(query.count(), 0)  # there should be no notification!

    # test declining an assessment
    asmt = Assessment.query.get(asmt_id)
    asmt.status = Assessment.DONE_STATE
    db.session.commit()

    self.client.get("/_notifications/send_daily_digest")
    self.assertEqual(self._get_notifications().count(), 0)

    self.import_data(OrderedDict([
        (u"object_type", u"Assessment"),
        (u"Code*", asmt_slug),
        (u"State*", Assessment.PROGRESS_STATE),
    ]))

    query = self._get_notifications(notif_type="assessment_declined")
    self.assertEqual(query.count(), 1)
    query = self._get_notifications(notif_type="assessment_reopened")
    self.assertEqual(query.count(), 1)

    self.client.get("/_notifications/send_daily_digest")
    recipient, _, content = send_email.call_args[0]
    self.assertEqual(recipient, u"user@example.com")
    self.assertIn(u"Declined assessments", content)
    self.assertIn(u"Reopened assessments", content)

    # directly submitting a not started assessment for review
    asmt = Assessment.query.get(asmt_id)
    asmt.status = Assessment.START_STATE
    db.session.commit()

    self.client.get("/_notifications/send_daily_digest")
    self.assertEqual(self._get_notifications().count(), 0)

    self.import_data(OrderedDict([
        (u"object_type", u"Assessment"),
        (u"Code*", asmt_slug),
        (u"State*", Assessment.DONE_STATE),
    ]))

    query = self._get_notifications(notif_type="assessment_ready_for_review")
    self.assertEqual(query.count(), 1)

    self.client.get("/_notifications/send_daily_digest")
    recipient, _, content = send_email.call_args[0]
    self.assertEqual(recipient, u"user@example.com")
    self.assertIn(u"Assessments ready for review", content)

    # directly completing a not started assessment
    self.import_data(OrderedDict([
        (u"object_type", u"Assessment"),
        (u"Code*", asmt_slug),
        (u"Verifier", None),
        (u"State*", Assessment.START_STATE),
    ]))

    self.client.get("/_notifications/send_daily_digest")
    self.assertEqual(self._get_notifications().count(), 0)

    self.import_data(OrderedDict([
        (u"object_type", u"Assessment"),
        (u"Code*", asmt_slug),
        (u"State*", Assessment.FINAL_STATE),
    ]))

    query = self._get_notifications(notif_type="assessment_completed")
    self.assertEqual(query.count(), 1)

    self.client.get("/_notifications/send_daily_digest")
    recipient, _, content = send_email.call_args[0]
    self.assertEqual(recipient, u"user@example.com")
    self.assertIn(u"Completed assessments", content)

    # test reopening a completed assessment
    self.assertEqual(self._get_notifications().count(), 0)

    self.import_data(OrderedDict([
        (u"object_type", u"Assessment"),
        (u"Code*", asmt_slug),
        (u"State*", Assessment.PROGRESS_STATE),
    ]))

    query = self._get_notifications(notif_type="assessment_reopened")
    self.assertEqual(query.count(), 1)

    self.client.get("/_notifications/send_daily_digest")
    recipient, _, content = send_email.call_args[0]
    self.assertEqual(recipient, u"user@example.com")
    self.assertIn(u"Reopened assessments", content)

    # completing an assessment in progress
    self.assertEqual(self._get_notifications().count(), 0)

    self.import_data(OrderedDict([
        (u"object_type", u"Assessment"),
        (u"Code*", asmt_slug),
        (u"State*", Assessment.FINAL_STATE),
    ]))

    query = self._get_notifications(notif_type="assessment_completed")
    self.assertEqual(query.count(), 1)

    self.client.get("/_notifications/send_daily_digest")
    recipient, _, content = send_email.call_args[0]
    self.assertEqual(recipient, u"user@example.com")
    self.assertIn(u"Completed assessments", content)

  @patch("ggrc.notifications.common.send_email")
  def test_multiple_assessment_state_changes_notification(self, send_email):
    """Test if several assessment state changes result in a single notification.

    Users should only be notificed about the last state change, and not about
    every state change that happened.
    """
    self.import_file("assessment_with_templates.csv")

    asmts = {asmt.slug: asmt for asmt in Assessment.query}
    asmt = Assessment.query.get(asmts["A 1"].id)
    asmt_slug = asmt.slug

    asmt.status = Assessment.START_STATE
    db.session.commit()

    self.client.get("/_notifications/send_daily_digest")
    self.assertEqual(self._get_notifications().count(), 0)

    # make multiple state transitions and check that only the last one is
    # actually retained
    states = (
        Assessment.PROGRESS_STATE,
        Assessment.DONE_STATE,
        Assessment.PROGRESS_STATE,
        Assessment.FINAL_STATE,
    )

    for new_state in states:
      self.import_data(OrderedDict([
          (u"object_type", u"Assessment"),
          (u"Code*", asmt_slug),
          (u"State*", new_state),
      ]))

    self.client.get("/_notifications/send_daily_digest")
    recipient, _, content = send_email.call_args[0]
    self.assertEqual(recipient, u"user@example.com")
    self.assertNotIn(u"Assessments ready for review", content)
    self.assertNotIn(u"Declined assessments", content)
    self.assertNotIn(u"Reopened assessments", content)
    self.assertIn(u"Completed assessments", content)

  @patch("ggrc.notifications.common.send_email")
  def test_assessment_reopen_notifications_on_edit(self, send_email):
    """Test if updating assessment results in reopen notification."""
    self.import_file("assessment_with_templates.csv")

    asmts = {asmt.slug: asmt for asmt in Assessment.query}
    asmt = Assessment.query.get(asmts["A 1"].id)
    asmt_id, asmt_slug = asmt.id, asmt.slug

    for i, new_state in enumerate(Assessment.DONE_STATES):
      asmt = Assessment.query.get(asmt_id)
      asmt.status = new_state
      db.session.commit()

      self.client.get("/_notifications/send_daily_digest")
      self.assertEqual(self._get_notifications().count(), 0)

      self.import_data(OrderedDict([
          (u"object_type", u"Assessment"),
          (u"Code*", asmt_slug),
          (u"Title", u"New Assessment 1 title - " + unicode(i)),
      ]))

      query = self._get_notifications(notif_type="assessment_reopened")
      self.assertEqual(query.count(), 1)

      self.client.get("/_notifications/send_daily_digest")
      recipient, _, content = send_email.call_args[0]
      self.assertEqual(recipient, u"user@example.com")
      self.assertIn(u"Reopened assessments", content)

  @unittest.skip("An issue needs to be fixed.")
  @patch("ggrc.notifications.common.send_email")
  def test_assessment_reopen_notifications_on_ca_edit(self, send_email):
    """Test if updating assessment's CA value in reopen notification."""
    CAD(definition_type="assessment", title="CA_misc_remarks")

    self.import_file("assessment_with_templates.csv")

    asmts = {asmt.slug: asmt for asmt in Assessment.query}
    asmt = Assessment.query.get(asmts["A 1"].id)
    asmt_id, asmt_slug = asmt.id, asmt.slug

    for i, new_state in enumerate(Assessment.DONE_STATES):
      asmt = Assessment.query.get(asmt_id)
      asmt.status = new_state
      db.session.commit()

      self.client.get("/_notifications/send_daily_digest")
      self.assertEqual(self._get_notifications().count(), 0)

      self.import_data(OrderedDict([
          (u"object_type", u"Assessment"),
          (u"Code*", asmt_slug),
          (u"CA_misc_remarks", u"CA new value" + unicode(i)),
      ]))

      query = self._get_notifications(notif_type="assessment_reopened")
      self.assertEqual(query.count(), 1)

      self.client.get("/_notifications/send_daily_digest")
      recipient, _, content = send_email.call_args[0]
      self.assertEqual(recipient, u"user@example.com")
      self.assertIn(u"Reopened assessments", content)

  @unittest.skip("An issue needs to be fixed.")
  @patch("ggrc.notifications.common.send_email")
  def test_assessment_reopen_notifications_on_url_edit(self, send_email):
    """Test if updating assessment's URLs results in reopen notification."""
    self.import_file("assessment_with_templates.csv")

    asmts = {asmt.slug: asmt for asmt in Assessment.query}
    asmt = Assessment.query.get(asmts["A 1"].id)
    asmt_id, asmt_slug = asmt.id, asmt.slug

    for i, new_state in enumerate(Assessment.DONE_STATES):
      asmt = Assessment.query.get(asmt_id)
      asmt.status = new_state
      db.session.commit()

      self.client.get("/_notifications/send_daily_digest")
      self.assertEqual(self._get_notifications().count(), 0)

      self.import_data(OrderedDict([
          (u"object_type", u"Assessment"),
          (u"Code*", asmt_slug),
          (u"Url", u"www.foo-url-{}.bar".format(i)),
      ]))

      query = self._get_notifications(notif_type="assessment_reopened")
      self.assertEqual(query.count(), 1)

      self.client.get("/_notifications/send_daily_digest")
      recipient, _, content = send_email.call_args[0]
      self.assertEqual(recipient, u"user@example.com")
      self.assertIn(u"Reopened assessments", content)

  @unittest.skip("An issue needs to be fixed.")
  @patch("ggrc.notifications.common.send_email")
  def test_assessment_reopen_notifications_on_evidence_change(
      self, send_email
  ):
    """Test if assessment evidence change results in reopen notification."""
    self.import_file("assessment_with_templates.csv")

    asmts = {asmt.slug: asmt for asmt in Assessment.query}
    asmt = Assessment.query.get(asmts["A 1"].id)
    asmt_id, asmt_slug = asmt.id, asmt.slug

    for i, new_state in enumerate(Assessment.DONE_STATES):
      asmt = Assessment.query.get(asmt_id)
      asmt.status = new_state
      db.session.commit()

      self.client.get("/_notifications/send_daily_digest")
      self.assertEqual(self._get_notifications().count(), 0)

      self.import_data(OrderedDict([
          (u"object_type", u"Assessment"),
          (u"Code*", asmt_slug),
          (
              u"Evidence",
              u"https://gdrive.com/qwerty{0}/view evidence-{0}.txt".format(i)
          ),
      ]))

      query = self._get_notifications(notif_type="assessment_reopened")
      self.assertEqual(query.count(), 1)

      self.client.get("/_notifications/send_daily_digest")
      recipient, _, content = send_email.call_args[0]
      self.assertEqual(recipient, u"user@example.com")
      self.assertIn(u"Reopened assessments", content)

  @unittest.skip("An issue needs to be fixed.")
  @patch("ggrc.notifications.common.send_email")
  def test_assessment_reopen_notifications_on_person_change(self, send_email):
    """Test if updating assessment people results in a reopen notification."""
    self.import_file("assessment_with_templates.csv")

    asmts = {asmt.slug: asmt for asmt in Assessment.query}
    asmt = Assessment.query.get(asmts["A 1"].id)
    asmt_id, asmt_slug = asmt.id, asmt.slug

    for i, new_state in enumerate(Assessment.DONE_STATES):
      asmt = Assessment.query.get(asmt_id)
      asmt.status = new_state
      db.session.commit()

      self.client.get("/_notifications/send_daily_digest")
      self.assertEqual(self._get_notifications().count(), 0)

      self.import_data(OrderedDict([
          (u"object_type", u"Assessment"),
          (u"Code*", asmt_slug),
          (u"Assignee*", u"john{}@doe.com".format(i)),
      ]))

      query = self._get_notifications(notif_type="assessment_reopened")
      self.assertEqual(query.count(), 1)

      self.client.get("/_notifications/send_daily_digest")
      recipient, _, content = send_email.call_args[0]
      self.assertEqual(recipient, u"user@example.com")
      self.assertIn(u"Reopened assessments", content)


class TestAssignableNotificationUsingAPI(TestAssignableNotification):
  """Tests for notifications when interacting with objects through an API."""

  def setUp(self):
    super(TestAssignableNotificationUsingAPI, self).setUp()
    self.api_helper = api_helper.Api()
    self.objgen = generator.ObjectGenerator()

  @patch("ggrc.notifications.common.send_email")
  def test_assessment_without_verifiers(self, send_email):
    """Test setting notification entries for simple assessments.

    This function tests that each assessment gets an entry in the
    notifications table after it's been created.
    """
    with freeze_time("2015-04-01"):

      self.assertEqual(self._get_notifications().count(), 0)
      self.import_file("assessment_with_templates.csv")
      asmts = {asmt.slug: asmt for asmt in Assessment.query}

      notifs = self._get_notifications(notif_type="assessment_open").all()
      self.assertEqual(len(notifs), 6)

      revisions = Revision.query.filter(
          Revision.resource_type == 'Notification',
          Revision.resource_id.in_([notif.id for notif in notifs])
      ).count()
      self.assertEqual(revisions, 6)

      self.api_helper.delete(asmts["A 1"])
      self.api_helper.delete(asmts["A 6"])

      self.assertEqual(self._get_notifications().count(), 4)

      self.client.get("/_notifications/send_daily_digest")
      self.assertEqual(self._get_notifications().count(), 0)

      # editing an assessment in an active state should result in an
      # "updated" notification
      asmt = Assessment.query.get(asmts["A 5"].id)
      self.api_helper.modify_object(
          asmt, {"status": Assessment.PROGRESS_STATE})
      self.client.get("/_notifications/send_daily_digest")
      self.assertEqual(self._get_notifications().count(), 0)

      asmt = Assessment.query.get(asmts["A 5"].id)
      self.api_helper.modify_object(asmt, {"description": "new description"})

      query = self._get_notifications(notif_type="assessment_updated")
      self.assertEqual(query.count(), 1)

      # the assessment updated notification should not be sent if there exists
      # a status change notification, regardless of the order of actions
      asmt = Assessment.query.get(asmts["A 5"].id)
      self.api_helper.modify_object(
          asmt, {"status": Assessment.DONE_STATE})

      asmt = Assessment.query.get(asmts["A 5"].id)
      self.api_helper.modify_object(asmt, {"description": "new description 2"})

      self.client.get("/_notifications/send_daily_digest")
      _, _, content = send_email.call_args[0]

      self.assertNotIn(u"Assessments have been updated", content)

  @patch("ggrc.notifications.common.send_email")
  def test_assessment_with_verifiers(self, _):
    """Test notifications entries for declined assessments.

    This tests makes sure that there are extra notification entries added when
    an assessment has been declined.
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
      self.assertEqual(self._get_notifications().count(), 1)

      self.api_helper.modify_object(asmt1, {"status": Assessment.DONE_STATE})
      self.assertEqual(self._get_notifications().count(), 1)

      # decline assessment 1
      self.api_helper.modify_object(asmt1,
                                    {"status": Assessment.PROGRESS_STATE})
      self.assertEqual(self._get_notifications().count(), 2)
      self.api_helper.modify_object(asmt1, {"status": Assessment.DONE_STATE})
      self.assertEqual(self._get_notifications().count(), 1)
      # decline assessment 1 the second time
      self.api_helper.modify_object(asmt1,
                                    {"status": Assessment.PROGRESS_STATE})
      self.assertEqual(self._get_notifications().count(), 2)

      asmt6 = Assessment.query.get(asmts["A 6"].id)

      # start and finish assessment 6
      self.api_helper.modify_object(asmt6,
                                    {"status": Assessment.PROGRESS_STATE})
      self.assertEqual(self._get_notifications().count(), 3)
      self.api_helper.modify_object(asmt6, {"status": Assessment.DONE_STATE})
      self.assertEqual(self._get_notifications().count(), 3)
      # decline assessment 6
      self.api_helper.modify_object(asmt6,
                                    {"status": Assessment.PROGRESS_STATE})
      self.assertEqual(self._get_notifications().count(), 4)

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
      self.assertEqual(self._get_notifications().count(), 1)
      self.api_helper.modify_object(asmt6,
                                    {"status": Assessment.VERIFIED_STATE})
      self.assertEqual(self._get_notifications().count(), 1)
      self.api_helper.modify_object(asmt6,
                                    {"status": Assessment.PROGRESS_STATE})
      self.assertEqual(self._get_notifications().count(), 1)
      # decline assessment 6
      self.api_helper.modify_object(asmt6, {"status": Assessment.DONE_STATE})
      self.assertEqual(self._get_notifications().count(), 1)
      self.api_helper.modify_object(asmt6,
                                    {"status": Assessment.PROGRESS_STATE})
      self.assertEqual(self._get_notifications().count(), 2)

  @patch("ggrc.notifications.common.send_email")
  def test_assessment_started_notification(self, send_email):
    """Test that starting an Assessment results in a notification."""

    with freeze_time("2015-04-01"):
      self.import_file("assessment_with_templates.csv")
      asmts = {asmt.slug: asmt for asmt in Assessment.query}
      self.client.get("/_notifications/send_daily_digest")
      self.assertEqual(self._get_notifications().count(), 0)

      asmt1 = Assessment.query.get(asmts["A 5"].id)

      self.api_helper.modify_object(asmt1,
                                    {"status": Assessment.PROGRESS_STATE})

      self.client.get("/_notifications/send_daily_digest")
      recipient, _, content = send_email.call_args[0]

      self.assertEqual(recipient, u"user@example.com")
      self.assertRegexpMatches(content, ur"Assessment\s+has\s+been\s+started")

  @patch("ggrc.notifications.common.send_email")
  def test_editing_not_started_assessment(self, send_email):
    """Test that Assessment started notification masks updated notification.
    """
    with freeze_time("2015-04-01"):
      self.import_file("assessment_with_templates.csv")
      asmts = {asmt.slug: asmt for asmt in Assessment.query}
      self.client.get("/_notifications/send_daily_digest")
      self.assertEqual(self._get_notifications().count(), 0)

      asmt1 = Assessment.query.get(asmts["A 5"].id)

      self.api_helper.modify_object(
          asmt1, {"description": "new asmt5 description"})

      self.client.get("/_notifications/send_daily_digest")
      recipient, _, content = send_email.call_args[0]

      self.assertEqual(recipient, u"user@example.com")
      self.assertRegexpMatches(content, ur"Assessment\s+has\s+been\s+started")
      self.assertNotIn(u"Assessments have been updated", content)

  @patch("ggrc.notifications.common.send_email")
  def test_reverting_assessment_status_changes(self, _):
    """Test that undoing a stautus change might NOT trigger a notification.

    One use case is when a user verifies an assessment in review, but then
    clicks the Undo button to revert the change. A status change notification
    should not be sent in such cases.
    """
    self.import_file("assessment_with_templates.csv")
    asmts = {asmt.slug: asmt for asmt in Assessment.query}

    self.client.get("/_notifications/send_daily_digest")
    self.assertEqual(self._get_notifications().count(), 0)

    # mark Assessment as ready for review, verify it, then revert the change
    asmt = Assessment.query.get(asmts["A 4"].id)
    self.api_helper.modify_object(
        asmt, {"status": Assessment.DONE_STATE})
    asmt = Assessment.query.get(asmts["A 4"].id)

    self.api_helper.modify_object(
        asmt,
        {"status": Assessment.FINAL_STATE, "verified_date": datetime.now()}
    )

    # clear notifications
    self.client.get("/_notifications/send_daily_digest")
    self.assertEqual(self._get_notifications().count(), 0)

    # changing the status back to the previous one is effectively reopening
    # an Assessment
    asmt = Assessment.query.get(asmts["A 4"].id)
    self.api_helper.modify_object(
        asmt, {"status": Assessment.DONE_STATE, "verified_date": None})

    query = self._get_notifications(notif_type="assessment_reopened")
    self.assertEqual(query.count(), 0)

    # there should also be no change notification
    query = self._get_notifications(notif_type="assessment_updated")
    self.assertEqual(query.count(), 0)

  @patch("ggrc.notifications.common.send_email")
  def test_multiple_assessment_state_changes_notification(self, send_email):
    """Test if several assessment state changes result in a single notification.

    Users should only be notificed about the last state change, and not about
    every state change that happened.
    """
    self.import_file("assessment_with_templates.csv")

    asmts = {asmt.slug: asmt for asmt in Assessment.query}
    asmt = Assessment.query.get(asmts["A 1"].id)
    asmt_id = asmt.id

    asmt.status = Assessment.START_STATE
    db.session.commit()

    self.client.get("/_notifications/send_daily_digest")
    self.assertEqual(self._get_notifications().count(), 0)

    # make multiple state transitions and check that only the last one is
    # actually retained
    states = (
        Assessment.PROGRESS_STATE,
        Assessment.DONE_STATE,
        Assessment.PROGRESS_STATE,
        Assessment.FINAL_STATE,
    )

    for new_state in states:
      asmt = Assessment.query.get(asmt_id)
      self.api_helper.modify_object(asmt, {"status": new_state})

    self.client.get("/_notifications/send_daily_digest")
    recipient, _, content = send_email.call_args[0]
    self.assertEqual(recipient, u"user@example.com")
    self.assertNotIn(u"Assessments ready for review", content)
    self.assertNotIn(u"Declined assessments", content)
    self.assertNotIn(u"Reopened assessments", content)
    self.assertIn(u"Completed assessments", content)

  @patch("ggrc.notifications.common.send_email")
  def test_assessment_reopen_notifications_on_edit(self, send_email):
    """Test if updating assessment results in reopen notification."""
    self.import_file("assessment_with_templates.csv")

    asmts = {asmt.slug: asmt for asmt in Assessment.query}
    asmt = Assessment.query.get(asmts["A 1"].id)
    asmt_id, asmt_slug = asmt.id, asmt.slug

    for i, new_state in enumerate(Assessment.DONE_STATES):
      asmt = Assessment.query.get(asmt_id)
      asmt.status = new_state
      db.session.commit()

      self.client.get("/_notifications/send_daily_digest")
      self.assertEqual(self._get_notifications().count(), 0)

      self.import_data(OrderedDict([
          (u"object_type", u"Assessment"),
          (u"Code*", asmt_slug),
          (u"Title", u"New Assessment 1 title - " + unicode(i)),
      ]))

      query = self._get_notifications(notif_type="assessment_reopened")
      self.assertEqual(query.count(), 1)

      self.client.get("/_notifications/send_daily_digest")
      recipient, _, content = send_email.call_args[0]
      self.assertEqual(recipient, u"user@example.com")
      self.assertIn(u"Reopened assessments", content)

  @patch("ggrc.notifications.common.send_email")
  def test_changing_custom_attributes_triggers_change_notification(self, _):
    """Test that updating Assessment's CA value results in change notification.
    """
    CAD(definition_type="assessment", title="CA 1")
    cad2_id = CAD(definition_type="assessment", title="CA 2").id
    self.import_file("assessment_with_templates.csv")
    Notification.query.delete()
    asmts = {asmt.slug: asmt for asmt in Assessment.query}
    self.client.get("/_notifications/send_daily_digest")
    self.assertEqual(self._get_notifications().count(), 0)

    asmt4 = Assessment.query.get(asmts["A 4"].id)
    self.api_helper.modify_object(
        asmt4, {
            "global_attributes": [{
                "id": cad2_id,
                "values": [{"value": "1a2b3"}],
            }],
        }
    )
    # there should still be no notifications...
    self.assertEqual(
        self._get_notifications(notif_type="assessment_updated").count(), 0)

    # now change the CA value and check if notification gets generated
    started = self._get_notifications(notif_type="assessment_started").all()
    self.assertEqual(1, len(started))
    db.session.delete(started[0])
    db.session.commit()
    asmt4 = Assessment.query.get(asmts["A 4"].id)
    vals = asmt4.global_attributes
    for val in vals:
      if val["id"] == cad2_id:
        val["values"][0]["value"] = "NEW"
    self.api_helper.modify_object(asmt4, {"global_attributes": vals})

    notifs = self._get_notifications(notif_type="assessment_updated").all()
    self.assertEqual(len(notifs), 1)

  @patch("ggrc.notifications.common.send_email")
  def test_directly_completing_assessments(self, _):
    """Test that immediately finishing an Assessment produces a notification.

    "Immediately" here means directly sending an Assessment to either the
    "Completed", or the "Ready for Review" state, skipping the "In Progress"
    state.
    """
    self.import_file("assessment_with_templates.csv")
    asmts = {asmt.slug: asmt for asmt in Assessment.query}

    self.client.get("/_notifications/send_daily_digest")
    self.assertEqual(self._get_notifications().count(), 0)

    # directly sending an Assessment to the "Ready for Review" state
    asmt4 = Assessment.query.get(asmts["A 4"].id)
    self.api_helper.modify_object(asmt4,
                                  {"status": Assessment.DONE_STATE})
    self.assertEqual(self._get_notifications().count(), 1)

    # clear notifications
    self.client.get("/_notifications/send_daily_digest")
    self.assertEqual(self._get_notifications().count(), 0)

    # directly sending an Assessment to the "Completed" state
    asmt5 = Assessment.query.get(asmts["A 5"].id)
    self.api_helper.modify_object(asmt5,
                                  {"status": Assessment.FINAL_STATE})
    self.assertEqual(self._get_notifications().count(), 1)

  @patch("ggrc.notifications.common.send_email")
  def test_changing_assigned_people_triggers_notifications(self, _):
    """Test that changing Assessment people results in change notification.

    Adding (removing) a person to (from) Assessment should be detected and
    considered an Assessment change.
    """
    self.import_file("assessment_with_templates.csv")
    asmts = {asmt.slug: asmt for asmt in Assessment.query}

    self.client.get("/_notifications/send_daily_digest")
    self.assertEqual(self._get_notifications().count(), 0)

    asmt = Assessment.query.get(asmts["A 5"].id)

    # add an Assessor, there should be no notifications because the Assessment
    # has not been started yet
    person = factories.PersonFactory()
    response, relationship = self.objgen.generate_relationship(
        person, asmt, attrs={"AssigneeType": "Assessor"})
    self.assertEqual(response.status_code, 201)

    change_notifs = self._get_notifications(notif_type="assessment_updated")
    self.assertEqual(change_notifs.count(), 0)
    asmt = Assessment.query.get(asmts["A 5"].id)

    # move Assessment to to "In Progress" state and clear notifications
    self.api_helper.modify_object(
        asmt, {"status": Assessment.PROGRESS_STATE})

    self.client.get("/_notifications/send_daily_digest")
    self.assertEqual(self._get_notifications().count(), 0)
    asmt = Assessment.query.get(asmts["A 5"].id)

    # assign another Assignee, change notification should be created
    person2 = factories.PersonFactory()
    response, relationship2 = self.objgen.generate_relationship(
        person2, asmt, attrs={"AssigneeType": "Assessor"})
    self.assertEqual(response.status_code, 201)
    rel2_id = relationship2.id

    change_notifs = self._get_notifications(notif_type="assessment_updated")
    self.assertEqual(change_notifs.count(), 1)

    # clear notifications, assign the same person as Verfier, check for
    # change notification
    self.client.get("/_notifications/send_daily_digest")
    self.assertEqual(change_notifs.count(), 0)
    asmt = Assessment.query.get(asmts["A 5"].id)
    relationship2 = Relationship.query.get(rel2_id)

    self.api_helper.modify_object(
        relationship2, {"AssigneeType": "Assessor,Verifier"})

    change_notifs = self._get_notifications(notif_type="assessment_updated")
    self.assertEqual(change_notifs.count(), 1)

    # clear notifications, delete an Assignee, test for change notification
    self.client.get("/_notifications/send_daily_digest")
    self.assertEqual(change_notifs.count(), 0)
    asmt = Assessment.query.get(asmts["A 5"].id)

    self.api_helper.delete(relationship)

    change_notifs = self._get_notifications(notif_type="assessment_updated")
    self.assertEqual(change_notifs.count(), 1)

    # clear notifications, delete one of the person's roles, test for
    # change notification
    self.client.get("/_notifications/send_daily_digest")
    self.assertEqual(change_notifs.count(), 0)
    asmt = Assessment.query.get(asmts["A 5"].id)
    relationship2 = Relationship.query.get(rel2_id)

    self.api_helper.modify_object(
        relationship2, {"AssigneeType": "Assessor"})  # not Verifier anymore

    change_notifs = self._get_notifications(notif_type="assessment_updated")
    self.assertEqual(change_notifs.count(), 1)

    # changing people if completed should result in "reopened" notification

    # TODO: contrary to how relations to Documents behave, assigning a Person
    # to an Assessment causes the latter to be immediately moved to the
    # "In Progress" state, making the relationship change handler to think that
    # the Assessment was modified in the "In Progress" state, resulting in
    # a missing assessment_reopened notification. We thus skip this check for
    # the time being.

    # asmt = Assessment.query.get(asmts["A 5"].id)
    # self.api_helper.modify_object(
    #     asmt, {"status": Assessment.FINAL_STATE})
    # self.client.get("/_notifications/send_daily_digest")
    # self.assertEqual(self._get_notifications().count(), 0)
    # asmt = Assessment.query.get(asmts["A 5"].id)

    # person = factories.PersonFactory()
    # response, relationship = self.objgen.generate_relationship(
    #     person, asmt, attrs={"AssigneeType": "Assessor"})
    # self.assertEqual(response.status_code, 201)

    # reopened_notifs = self._get_notifications(
    #     notif_type="assessment_reopened")
    # self.assertEqual(reopened_notifs.count(), 1)

  @patch("ggrc.notifications.common.send_email")
  def test_changing_assessment_urls_triggers_notifications(self, _):
    """Test that changing Assessment URLs results in change notification.

    Adding (removing) a URL to (from) Assessment should be detected and
    considered an Assessment change.
    """
    self.import_file("assessment_with_templates.csv")
    asmts = {asmt.slug: asmt for asmt in Assessment.query}

    self.client.get("/_notifications/send_daily_digest")
    self.assertEqual(self._get_notifications().count(), 0)

    asmt = Assessment.query.get(asmts["A 5"].id)

    # add a URL, there should be no notifications because the Assessment
    # has not been started yet
    url = factories.DocumentFactory(link="www.foo.com")
    response, relationship = self.objgen.generate_relationship(url, asmt)
    self.assertEqual(response.status_code, 201)

    change_notifs = self._get_notifications(notif_type="assessment_updated")
    self.assertEqual(change_notifs.count(), 0)
    asmt = Assessment.query.get(asmts["A 5"].id)

    # move Assessment to to "In Progress" state and clear notifications
    self.api_helper.modify_object(
        asmt, {"status": Assessment.PROGRESS_STATE})

    self.client.get("/_notifications/send_daily_digest")
    self.assertEqual(self._get_notifications().count(), 0)
    asmt = Assessment.query.get(asmts["A 5"].id)

    # add another URL, change notification should be created
    url2 = factories.DocumentFactory(link="www.bar.com")
    response, _ = self.objgen.generate_relationship(url2, asmt)
    self.assertEqual(response.status_code, 201)

    change_notifs = self._get_notifications(notif_type="assessment_updated")
    self.assertEqual(change_notifs.count(), 1)

    # clear notifications, delete a URL, test for change notification
    self.client.get("/_notifications/send_daily_digest")
    self.assertEqual(change_notifs.count(), 0)
    asmt = Assessment.query.get(asmts["A 5"].id)

    self.api_helper.delete(relationship)

    change_notifs = self._get_notifications(notif_type="assessment_updated")
    self.assertEqual(change_notifs.count(), 1)

    # changing URLs if completed should result in "reopened" notification
    asmt = Assessment.query.get(asmts["A 5"].id)
    self.api_helper.modify_object(
        asmt, {"status": Assessment.FINAL_STATE})
    self.client.get("/_notifications/send_daily_digest")
    self.assertEqual(self._get_notifications().count(), 0)
    asmt = Assessment.query.get(asmts["A 5"].id)

    url = factories.DocumentFactory(link="www.abc.com")
    response, relationship = self.objgen.generate_relationship(url, asmt)
    self.assertEqual(response.status_code, 201)

    reopened_notifs = self._get_notifications(notif_type="assessment_reopened")
    self.assertEqual(reopened_notifs.count(), 1)
