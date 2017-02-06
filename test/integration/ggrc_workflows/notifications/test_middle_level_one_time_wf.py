# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

import textwrap
from integration.ggrc import TestCase
from freezegun import freeze_time
from datetime import date, datetime

from ggrc import db
from ggrc.notifications import common
from ggrc.models import Notification
from integration.ggrc_workflows.generator import WorkflowsGenerator
from integration.ggrc.api_helper import Api
from integration.ggrc.generator import ObjectGenerator


class TestOneTimeWorkflowNotification(TestCase):

  """ Tests are defined in the g-sheet test grid under:
    WF EMAILS for unit tests (middle level)
  """

  def setUp(self):
    super(TestOneTimeWorkflowNotification, self).setUp()
    self.api = Api()
    self.wf_generator = WorkflowsGenerator()
    self.object_generator = ObjectGenerator()

    self.random_objects = self.object_generator.generate_random_objects()
    self.random_people = [
        self.object_generator.generate_person(user_role="Administrator")[1]
        for _ in range(5)]
    self.create_test_cases()

    self.create_users()

    db.session.query(Notification).delete()

    def init_decorator(init):
      def new_init(self, *args, **kwargs):
        init(self, *args, **kwargs)
        if hasattr(self, "created_at"):
          self.created_at = datetime.now()
      return new_init

    Notification.__init__ = init_decorator(Notification.__init__)

  def tearDown(self):
    db.session.query(Notification).delete()

  def short_dict(self, obj, plural):
    return {
        "href": "/api/%s/%d" % (plural, obj.id),
        "id": obj.id,
        "type": obj.__class__.__name__,
    }

  def test_one_time_wf(self):
    # setup
    with freeze_time("2015-04-07 03:21:34"):
      wf_response, wf = self.wf_generator.generate_workflow(data={
          "frequency": "one_time",
          "owners": None,  # owner will be the current user
          "notify_on_change": True,  # force real time updates
          "title": "One-time WF",
          "notify_custom_message": textwrap.dedent("""\
              Hi all.
              Did you know that Irelnd city namd Newtownmountkennedy has 19
              letters? But it's not the longest one. The recordsman is the
              city in New Zealand that contains 97 letter."""),
      })

      _, tg = self.wf_generator.generate_task_group(wf, data={
          "title": "TG #1 for the One-time WF",
          "contact": self.short_dict(self.tgassignee1, "people"),
      })

      self.wf_generator.generate_task_group_task(tg, {
          "title": "task #1 for one-time workflow",
          "contact": self.short_dict(self.member1, "people"),
          "start_date": "04/07/2015",
          "end_date": "04/15/2015",
      })

      self.wf_generator.generate_task_group_object(tg, self.random_objects[0])
      self.wf_generator.generate_task_group_object(tg, self.random_objects[1])

    # test
    with freeze_time("2015-04-07 03:21:34"):
      cycle_response, cycle = self.wf_generator.generate_cycle(wf)
      self.wf_generator.activate_workflow(wf)

      db.session.add(self.owner1)
      db.session.add(self.tgassignee1)
      db.session.add(self.member1)

      common.get_daily_notifications()

  def create_test_cases(self):
    def person_dict(person_id):
      return {
          "href": "/api/people/%d" % person_id,
          "id": person_id,
          "type": "Person"
      }

    self.one_time_workflow_1 = {
        "title": "one time test workflow",
        "description": "some test workflow",
        "owners": [person_dict(self.random_people[3].id)],
        "task_groups": [{
            "title": "one time task group",
            "task_group_tasks": [{
                "title": "task 1",
                "description": "some task",
                "contact": person_dict(self.random_people[0].id),
                "start_date": date(2015, 5, 1),  # friday
                "end_date": date(2015, 5, 5),
            }, {
                "title": "task 2",
                "description": "some task",
                "contact": person_dict(self.random_people[1].id),
                "start_date": date(2015, 5, 4),
                "end_date": date(2015, 5, 7),
            }],
            "task_group_objects": self.random_objects[:2]
        }, {
            "title": "another one time task group",
            "task_group_tasks": [{
                "title": "task 1 in tg 2",
                "description": "some task",
                "contact": person_dict(self.random_people[0].id),
                "start_date": date(2015, 5, 8),  # friday
                "end_date": date(2015, 5, 12),
            }, {
                "title": "task 2 in tg 2",
                "description": "some task",
                "contact": person_dict(self.random_people[2].id),
                "start_date": date(2015, 5, 1),  # friday
                "end_date": date(2015, 5, 5),
            }],
            "task_group_objects": []
        }]
    }

  def create_users(self):
    _, self.owner1 = self.object_generator.generate_person(
        # data={"name": "User1 Owner1", "email": "user1.owner1@gmail.com"},
        user_role="Administrator")
    _, self.tgassignee1 = self.object_generator.generate_person(
        # data={"name": "User2 TGassignee1",
        #       "email": "user2.tgassignee1@gmail.com"},
        user_role="Administrator")
    _, self.member1 = self.object_generator.generate_person(
        # data={"name": "User3 Member1", "email": "user3.member1@gmail.com"},
        user_role="Administrator")
    _, self.member2 = self.object_generator.generate_person(
        # data={"name": "User4 Member2", "email": "user4.member2@gmail.com"},
        user_role="Administrator")
