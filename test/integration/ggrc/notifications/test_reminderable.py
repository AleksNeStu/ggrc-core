# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Tests for reminders for models with reminderable mixin."""

from datetime import datetime
from freezegun import freeze_time
from sqlalchemy import and_

from ggrc import db
from ggrc import models
from ggrc.notifications import common

from integration.ggrc import TestCase
from integration.ggrc import api_helper
from integration.ggrc.models import factories


class TestReminderable(TestCase):

  """Test sending reminder."""

  def setUp(self):
    super(TestReminderable, self).setUp()
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

    models.Notification.__init__ = init_decorator(models.Notification.__init__)

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
      notif_filter = models.Notification.sent_at.isnot(None)
    else:
      notif_filter = models.Notification.sent_at.is_(None)

    if notif_type:
      notif_filter = and_(notif_filter,
                          models.NotificationType.name == notif_type)

    return db.session.query(models.Notification).join(
        models.NotificationType).filter(notif_filter)

  @classmethod
  def create_assignees(cls, obj, persons):
    """Create assignees for object.

    Args:
      obj: Assignable object.
      persons: [("(string) email", "Assignee roles"), ...] A list of people
        and their roles
    Returns:
      [(person, object-person relationship,
        object-person relationship attributes), ...] A list of persons with
      their relationships and relationship attributes.
    """
    assignees = []
    for person, roles in persons:
      person = factories.PersonFactory(email=person)

      object_person_rel = factories.RelationshipFactory(
          source=obj,
          destination=person
      )

      object_person_rel_attrs = factories.RelationshipAttrFactory(
          relationship_id=object_person_rel.id,
          attr_name="AssigneeType",
          attr_value=roles
      )
      assignees += [(person, object_person_rel, object_person_rel_attrs)]
    return assignees

  def create_assessment(self, people=None):
    """Create default assessment with some default assignees in all roles.

    Args:
      people: List of tuples with email address and their assignee roles for
              Assessments.
    Returns:
      Assessment object.
    """
    assessment = factories.AssessmentFactory()

    if not people:
      people = [
          ("creator@example.com", "Creator"),
          ("assessor_1@example.com", "Assessor"),
          ("assessor_2@example.com", "Assessor"),
          ("verifier_1@example.com", "Verifier"),
          ("verifier_2@example.com", "Verifier"),
      ]

    self.create_assignees(assessment, people)

    creators = [assignee for assignee, roles in assessment.assignees
                if "Creator" in roles]
    assignees = [assignee for assignee, roles in assessment.assignees
                 if "Assessor" in roles]
    verifiers = [assignee for assignee, roles in assessment.assignees
                 if "Verifier" in roles]

    self.assertEqual(len(creators), 1)
    self.assertEqual(len(assignees), 2)
    self.assertEqual(len(verifiers), 2)
    return assessment

  @classmethod
  def refresh_object(cls, obj):
    """Returns a new instance of a model, fresh and warm from the database."""
    return obj.query.filter_by(id=obj.id).first()

  def change_status(self, obj, status):
    """Change status of an object."""
    self.api_helper.modify_object(obj, {
        "status": status
    })
    obj = self.refresh_object(obj)
    self.assertEqual(obj.status, status)
    return obj

  def send_reminder(self, obj, reminder_type=None):
    """Sends reminder to object."""
    if not reminder_type:
      reminder_type = "statusToPerson"
    return self.api_helper.modify_object(obj, {
        "reminderType": reminder_type
    })

  def test_assessment_open_reminder(self):
    """Tests that notifications get generated when in `Open` state."""

    with freeze_time("2015-04-01 17:13:15"):
      assessment = self.create_assessment()

      self.api_helper.modify_object(assessment, {
          "reminderType": "statusToPerson"
      })

      notifications = self._get_notifications(
          False, "assessment_assessor_reminder",
      ).all()
      self.assertEqual(len(notifications), 1)

      notif = notifications[0]
      revisions = models.Revision.query.filter_by(resource_type='Notification',
                                                  resource_id=notif.id).count()
      self.assertEqual(revisions, 1)

    with freeze_time("2015-04-02 01:01:01"):
      self.client.get("/_notifications/send_daily_digest")
      self.assertEqual(self._get_notifications().count(), 0)

  def test_assessment_inprogress_reminder(self):
    """Tests that notifications get generated when in `In Progress` state."""
    # pylint: disable=invalid-name
    with freeze_time("2015-04-01 17:13:15"):
      assessment = self.create_assessment()

      assessment = self.change_status(assessment, "In Progress")

      self.send_reminder(assessment)

      notifications = self._get_notifications(
          False, "assessment_assessor_reminder",
      ).all()
      self.assertEqual(len(notifications), 1)

      notif = notifications[0]
      revisions = models.Revision.query.filter_by(resource_type='Notification',
                                                  resource_id=notif.id).count()
      self.assertEqual(revisions, 1)

    with freeze_time("2015-04-02 01:01:01"):
      self.client.get("/_notifications/send_daily_digest")
      self.assertEqual(self._get_notifications().count(), 0)

  def test_assessment_finished_reminder(self):
    """Tests that there are no notifications when in `Finished` state"""
    # pylint: disable=invalid-name
    with freeze_time("2015-04-01 17:13:15"):
      assessment = self.create_assessment()

      assessment = self.change_status(assessment,
                                      models.Assessment.PROGRESS_STATE)
      assessment = self.change_status(assessment, models.Assessment.DONE_STATE)

      self.send_reminder(assessment)

      self.assertEqual(
          self._get_notifications(
              False, "assessment_assessor_reminder").count(),
          0)

    with freeze_time("2015-04-02 01:01:01"):
      self.client.get("/_notifications/send_daily_digest")
      self.assertEqual(self._get_notifications().count(), 0)

  def test_assessment_inprogress_reminder_finish_afterwards(self):
    """Tests that notifications don't get sent if Finished already.

    Tests that notifications don't get sent out if assessment has been moved to
    `Finished` state since reminder was activated.
    """
    # pylint: disable=invalid-name

    with freeze_time("2015-04-01 17:13:15"):
      assessment = self.create_assessment()

      assessment = self.change_status(assessment,
                                      models.Assessment.PROGRESS_STATE)

      self.send_reminder(assessment)

      notifications = self._get_notifications(
          False, "assessment_assessor_reminder",
      ).all()
      self.assertEqual(len(notifications), 1)

      notif = notifications[0]
      revisions = models.Revision.query.filter_by(resource_type='Notification',
                                                  resource_id=notif.id).count()
      self.assertEqual(revisions, 1)

      self.change_status(assessment, models.Assessment.DONE_STATE)

      _, notif_data = common.get_daily_notifications()
      self.assertEqual(notif_data, {})
