# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

from datetime import date
from datetime import datetime

from freezegun import freeze_time
from mock import patch
from sqlalchemy import and_

from ggrc.app import db
from ggrc.models import Notification
from ggrc.models import NotificationType
from ggrc.models import Person
from ggrc.notifications import common
from ggrc_workflows.models import Cycle
from ggrc_workflows.models import CycleTaskGroupObjectTask
from integration.ggrc import TestCase
from integration.ggrc.api_helper import Api
from integration.ggrc.generator import ObjectGenerator
from integration.ggrc_workflows.generator import WorkflowsGenerator


class TestCycleTaskStatusChange(TestCase):

  """ This class contains simple one time workflow tests that are not
  in the gsheet test grid
  """

  def setUp(self):
    super(TestCycleTaskStatusChange, self).setUp()
    self.api = Api()
    self.wf_generator = WorkflowsGenerator()
    self.object_generator = ObjectGenerator()
    Notification.query.delete()

    self.random_objects = self.object_generator.generate_random_objects(2)
    _, self.user = self.object_generator.generate_person(
        user_role="Administrator")
    self.create_test_cases()

    def init_decorator(init):
      def new_init(self, *args, **kwargs):
        init(self, *args, **kwargs)
        if hasattr(self, "created_at"):
          self.created_at = datetime.now()
      return new_init

    Notification.__init__ = init_decorator(Notification.__init__)

  def test_task_declined_notification_created(self):
    with freeze_time("2015-05-01"):
      _, workflow = self.wf_generator.generate_workflow(
          self.one_time_workflow_1)

      _, cycle = self.wf_generator.generate_cycle(workflow)
      self.wf_generator.activate_workflow(workflow)

      cycle = Cycle.query.get(cycle.id)
      task1 = CycleTaskGroupObjectTask.query.get(
          cycle.cycle_task_group_object_tasks[0].id)

      self.task_change_status(task1, "Declined")

      notif = db.session.query(Notification).filter(and_(
          Notification.object_id == task1.id,
          Notification.object_type == task1.type,
          Notification.sent_at == None,  # noqa
          Notification.notification_type == self.get_notification_type(
              "cycle_task_declined"
          )
      )).all()

      self.assertEqual(len(notif), 1, "notifications: {}".format(str(notif)))

  def test_all_tasks_finished_notification_created(self):
    with freeze_time("2015-05-01"):
      _, workflow = self.wf_generator.generate_workflow(
          self.one_time_workflow_1)

      _, cycle = self.wf_generator.generate_cycle(workflow)
      self.wf_generator.activate_workflow(workflow)

      cycle = Cycle.query.get(cycle.id)
      task1 = CycleTaskGroupObjectTask.query.get(
          cycle.cycle_task_group_object_tasks[0].id)

      self.task_change_status(task1)

      notif = db.session.query(Notification).filter(and_(
          Notification.object_id == cycle.id,
          Notification.object_type == cycle.type,
          Notification.sent_at == None,  # noqa
          Notification.notification_type == self.get_notification_type(
              "all_cycle_tasks_completed"
          )
      )).all()

      self.assertEqual(len(notif), 1, "notifications: {}".format(str(notif)))

      notif = db.session.query(Notification).filter(and_(
          Notification.object_id == task1.id,
          Notification.object_type == task1.type,
          Notification.sent_at == None,  # noqa
          Notification.notification_type != self.get_notification_type(
              "all_cycle_tasks_completed"
          )
      )).all()

      self.assertEqual(notif, [])

  def test_multi_all_tasks_finished_notification_created(self):

    with freeze_time("2015-05-01"):
      _, workflow = self.wf_generator.generate_workflow(
          self.one_time_workflow_2)

      _, cycle = self.wf_generator.generate_cycle(workflow)
      self.wf_generator.activate_workflow(workflow)

      cycle = Cycle.query.get(cycle.id)
      task1 = CycleTaskGroupObjectTask.query.get(
          cycle.cycle_task_group_object_tasks[0].id)

      self.task_change_status(task1)

      notif = db.session.query(Notification).filter(and_(
          Notification.object_id == cycle.id,
          Notification.object_type == cycle.type,
          Notification.sent_at == None,  # noqa
          Notification.notification_type == self.get_notification_type(
              "all_cycle_tasks_completed"
          )
      )).all()

      # there is still one task in the cycle, so there should be no
      # notifications for all tasks completed
      self.assertEqual(notif, [])

      notif = db.session.query(Notification).filter(and_(
          Notification.object_id == task1.id,
          Notification.object_type == task1.type,
          Notification.sent_at == None,  # noqa
          Notification.notification_type != self.get_notification_type(
              "all_cycle_tasks_completed"
          )
      )).all()

      # The task was verified, so there should be no notifications left for due
      # dates.
      self.assertEqual(notif, [])

      task2 = CycleTaskGroupObjectTask.query.get(
          cycle.cycle_task_group_object_tasks[1].id)

      self.task_change_status(task2)

      notif = db.session.query(Notification).filter(and_(
          Notification.object_id == cycle.id,
          Notification.object_type == cycle.type,
          Notification.sent_at == None,  # noqa
          Notification.notification_type == self.get_notification_type(
              "all_cycle_tasks_completed"
          )
      )).all()

      self.assertEqual(len(notif), 1, "notifications: {}".format(str(notif)))

  @patch("ggrc.notifications.common.send_email")
  def test_single_task_declined(self, mock_mail):
    """
    test moving the end date to the future, befor due_in and due_today
    notifications have been sent
    """

    with freeze_time("2015-05-01"):
      _, workflow = self.wf_generator.generate_workflow(
          self.one_time_workflow_1)

      _, cycle = self.wf_generator.generate_cycle(workflow)
      self.wf_generator.activate_workflow(workflow)

    with freeze_time("2015-05-02"):
      common.send_daily_digest_notifications()

      cycle = Cycle.query.get(cycle.id)
      task1 = CycleTaskGroupObjectTask.query.get(
          cycle.cycle_task_group_object_tasks[0].id)

      self.task_change_status(task1, "Finished")

      _, notif_data = common.get_daily_notifications()
      self.assertEqual(notif_data, {})

    with freeze_time("2015-05-02"):
      common.send_daily_digest_notifications()

      cycle = Cycle.query.get(cycle.id)
      task1 = CycleTaskGroupObjectTask.query.get(
          cycle.cycle_task_group_object_tasks[0].id)

      self.task_change_status(task1, "Declined")

      user = Person.query.get(self.user.id)
      _, notif_data = common.get_daily_notifications()

      self.assertIn(user.email, notif_data)
      self.assertIn("task_declined", notif_data[user.email])

  @patch("ggrc.notifications.common.send_email")
  def test_single_task_accepted(self, mock_mail):
    """
    test moving the end date to the future, befor due_in and due_today
    notifications have been sent
    """

    with freeze_time("2015-05-01"):
      _, workflow = self.wf_generator.generate_workflow(
          self.one_time_workflow_1)

      _, cycle = self.wf_generator.generate_cycle(workflow)
      self.wf_generator.activate_workflow(workflow)

    with freeze_time("2015-05-02"):
      common.send_daily_digest_notifications()

      cycle = Cycle.query.get(cycle.id)
      task1 = CycleTaskGroupObjectTask.query.get(
          cycle.cycle_task_group_object_tasks[0].id)

      self.task_change_status(task1, "Finished")

      _, notif_data = common.get_daily_notifications()
      self.assertEqual(notif_data, {})

    with freeze_time("2015-05-03"):
      cycle = Cycle.query.get(cycle.id)
      task1 = CycleTaskGroupObjectTask.query.get(
          cycle.cycle_task_group_object_tasks[0].id)

      self.task_change_status(task1)

      user = Person.query.get(self.user.id)
      _, notif_data = common.get_daily_notifications()
      self.assertNotIn(user.email, notif_data)
      self.assertIn("all_tasks_completed", notif_data["user@example.com"])

  @patch("ggrc.notifications.common.send_email")
  def test_end_cycle(self, mock_mail):
    """
    manaually ending a cycle should stop all notifications for that cycle
    """

    with freeze_time("2015-05-01"):
      _, workflow = self.wf_generator.generate_workflow(
          self.one_time_workflow_1)
      _, cycle = self.wf_generator.generate_cycle(workflow)
      self.wf_generator.activate_workflow(workflow)

    with freeze_time("2015-05-03"):
      _, notif_data = common.get_daily_notifications()
      cycle = Cycle.query.get(cycle.id)
      user = Person.query.get(self.user.id)
      self.assertIn(user.email, notif_data)
      self.wf_generator.modify_object(cycle, data={"is_current": False})
      cycle = Cycle.query.get(cycle.id)
      self.assertFalse(cycle.is_current)

      _, notif_data = common.get_daily_notifications()
      self.assertNotIn(user.email, notif_data)

  def create_test_cases(self):
    def person_dict(person_id):
      return {
          "href": "/api/people/%d" % person_id,
          "id": person_id,
          "type": "Person"
      }

    self.one_time_workflow_1 = {
        "title": "one time test workflow",
        "notify_on_change": True,
        "description": "some test workflow",
        "owners": [person_dict(self.user.id)],
        "task_groups": [{
            "title": "single task group",
            "contact": person_dict(self.user.id),
            "task_group_tasks": [{
                "title": "task 1",
                "description": "single task in a wf",
                "contact": person_dict(self.user.id),
                "start_date": date(2015, 5, 1),  # friday
                "end_date": date(2015, 5, 5),
            }],
        }]
    }

    self.one_time_workflow_2 = {
        "title": "one time test workflow",
        "notify_on_change": True,
        "description": "some test workflow",
        "owners": [person_dict(self.user.id)],
        "task_groups": [{
            "title": "one time task group",
            "contact": person_dict(self.user.id),
            "task_group_tasks": [{
                "title": "task 1",
                "description": "two taks in wf with different objects",
                "contact": person_dict(self.user.id),
                "start_date": date(2015, 5, 1),  # friday
                "end_date": date(2015, 5, 5),
            }, {
                "title": "task 2",
                "description": "two taks in wf with different objects",
                "contact": person_dict(self.user.id),
                "start_date": date(2015, 5, 1),  # friday
                "end_date": date(2015, 5, 5),
            }],
            "task_group_objects": self.random_objects
        }]
    }

  def get_notification_type(self, name):
    return db.session.query(NotificationType).filter(
        NotificationType.name == name).one()

  def task_change_status(self, task, status="Verified"):
    self.wf_generator.modify_object(
        task, data={"status": status})

    task = CycleTaskGroupObjectTask.query.get(task.id)

    self.assertEqual(task.status, status)
