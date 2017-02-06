# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

from datetime import datetime
from freezegun import freeze_time

from ggrc import db
from ggrc_workflows.models import Cycle
from ggrc_workflows.models import CycleTaskGroupObjectTask
from ggrc_workflows.models import TaskGroup
from ggrc_workflows.models import Workflow
from integration.ggrc import TestCase
from integration.ggrc_workflows.generator import WorkflowsGenerator
from integration.ggrc.api_helper import Api
from integration.ggrc.generator import ObjectGenerator
from integration.ggrc.models import factories


class TestBasicWorkflowActions(TestCase):

  def setUp(self):
    super(TestBasicWorkflowActions, self).setUp()
    self.api = Api()
    self.generator = WorkflowsGenerator()
    self.object_generator = ObjectGenerator()

    self.random_objects = self.object_generator.generate_random_objects()
    self.create_test_cases()

  def tearDown(self):
    pass

  def test_create_workflows(self):
    _, wflow = self.generator.generate_workflow(self.one_time_workflow_1)
    self.assertIsInstance(wflow, Workflow)

    task_groups = db.session.query(TaskGroup)\
        .filter(TaskGroup.workflow_id == wflow.id).all()

    self.assertEqual(len(task_groups),
                     len(self.one_time_workflow_1["task_groups"]))

  def test_workflows(self):
    for workflow in self.all_workflows:
      _, wflow = self.generator.generate_workflow(workflow)
      self.assertIsInstance(wflow, Workflow)

      task_groups = db.session.query(TaskGroup)\
          .filter(TaskGroup.workflow_id == wflow.id).all()

      self.assertEqual(len(task_groups),
                       len(workflow["task_groups"]))

  def test_activate_wf(self):
    for workflow in self.all_workflows:
      _, wflow = self.generator.generate_workflow(workflow)
      response, wflow = self.generator.activate_workflow(wflow)

      self.assert200(response)

  def test_one_time_workflow_edits(self):
    _, wflow = self.generator.generate_workflow(self.one_time_workflow_1)

    wf_dict = {"title": "modified one time wf"}
    self.generator.modify_workflow(wflow, data=wf_dict)

    modified_wf = db.session.query(Workflow).filter(
        Workflow.id == wflow.id).one()
    self.assertEqual(wf_dict["title"], modified_wf.title)

  def test_one_time_wf_activate(self):
    _, wflow = self.generator.generate_workflow(self.one_time_workflow_1)
    self.generator.generate_cycle(wflow)
    self.generator.activate_workflow(wflow)

    tasks = [len(tg.get("task_group_tasks", []))
             for tg in self.one_time_workflow_1["task_groups"]]

    cycle_tasks = db.session.query(CycleTaskGroupObjectTask).join(
        Cycle).join(Workflow).filter(Workflow.id == wflow.id).all()
    active_wf = db.session.query(Workflow).filter(
        Workflow.id == wflow.id).one()

    self.assertEqual(sum(tasks), len(cycle_tasks))
    self.assertEqual(active_wf.status, "Active")

  def test_one_time_wf_state_transition_dates(self):
    _, wflow = self.generator.generate_workflow(self.one_time_workflow_1)
    self.generator.generate_cycle(wflow)
    self.generator.activate_workflow(wflow)

    cycle_tasks = db.session.query(CycleTaskGroupObjectTask).join(
        Cycle).join(Workflow).filter(Workflow.id == wflow.id).all()
    with freeze_time("2015-6-9 13:00:00"):
      today = datetime.now()
      transitions = [
          ("InProgress", None, None),
          ("Finished", today, None),
          ("Declined", None, None),
          ("Finished", today, None),
          ("Verified", today, today),
          ("Finished", today, None),
      ]
      # Iterate over possible transitions and check if dates got set correctly
      for (status, expected_finished, expected_verified) in transitions:
        cycle_task = cycle_tasks[0]
        _, task = self.generator.modify_object(cycle_task, {"status": status})
        self.assertEqual(task.finished_date, expected_finished)
        self.assertEqual(task.verified_date, expected_verified)

  def test_delete_calls(self):
    _, workflow = self.generator.generate_workflow()
    self.generator.generate_task_group(workflow)
    _, task_group = self.generator.generate_task_group(workflow)
    task_groups = db.session.query(TaskGroup).filter(
        TaskGroup.workflow_id == workflow.id).all()
    self.assertEqual(len(task_groups), 2)

    response = self.generator.api.delete(task_group)
    self.assert200(response)

    task_groups = db.session.query(TaskGroup).filter(
        TaskGroup.workflow_id == workflow.id).all()
    self.assertEqual(len(task_groups), 1)

  def create_test_cases(self):

    self.quarterly_wf_1 = {
        "title": "quarterly wf 1",
        "description": "",
        "frequency": "quarterly",
        "task_groups": [{
            "title": "tg_1",
            "task_group_tasks": [{
                "description": factories.random_str(100),
                "relative_start_day": 5,
                "relative_start_month": 1,
                "relative_end_day": 25,
                "relative_end_month": 2,
            }, {
                "description": factories.random_str(100),
                "relative_start_day": 15,
                "relative_start_month": 2,
                "relative_end_day": 28,
                "relative_end_month": 2,
            }, {
                "description": factories.random_str(100),
                "relative_start_day": 1,
                "relative_start_month": 1,
                "relative_end_day": 1,
                "relative_end_month": 1,
            },
            ],
        },
        ]
    }

    self.weekly_wf_1 = {
        "title": "weekly thingy",
        "description": "start this many a time",
        "frequency": "weekly",
        "task_groups": [{
            "title": "tg_2",
            "task_group_tasks": [{
                "description": factories.random_str(100),
                "relative_end_day": 1,
                "relative_end_month": None,
                "relative_start_day": 5,
                "relative_start_month": None,
            }, {
                "title": "monday task",
                "relative_end_day": 1,
                "relative_end_month": None,
                "relative_start_day": 1,
                "relative_start_month": None,
            }, {
                "title": "weekend task",
                "relative_end_day": 4,
                "relative_end_month": None,
                "relative_start_day": 1,
                "relative_start_month": None,
            },
            ],
            "task_group_objects": self.random_objects
        },
        ]
    }

    self.one_time_workflow_1 = {
        "title": "one time wf test",
        "description": "some test workflow",
        "task_groups": [{
            "title": "tg_1",
            "task_group_tasks": [{}, {}, {}]
        }, {
            "title": "tg_2",
            "task_group_tasks": [{
                "description": factories.random_str(100)
            }, {}
            ],
            "task_group_objects": self.random_objects[:2]
        }, {
            "title": "tg_3",
            "task_group_tasks": [{
                "title": "simple task 1",
                "description": factories.random_str(100)
            }, {
                "title": factories.random_str(),
                "description": factories.random_str(100)
            }, {
                "title": factories.random_str(),
                "description": factories.random_str(100)
            }
            ],
            "task_group_objects": self.random_objects
        }
        ]
    }
    self.one_time_workflow_2 = {
        "title": "test_wf_title",
        "description": "some test workflow",
        "task_groups": [
            {
                "title": "tg_1",
                "task_group_tasks": [{}, {}, {}]
            },
            {
                "title": "tg_2",
                "task_group_tasks": [{
                    "description": factories.random_str(100)
                }, {}],
                "task_group_objects": self.random_objects[:2]
            },
            {
                "title": "tg_3",
                "task_group_tasks": [{
                    "title": "simple task 1",
                    "description": factories.random_str(100)
                }, {
                    "title": factories.random_str(),
                    "description": factories.random_str(100)
                }, {
                    "title": factories.random_str(),
                    "description": factories.random_str(100)
                }],
                "task_group_objects": []
            }
        ]
    }

    self.monthly_workflow_1 = {
        "title": "monthly test wf",
        "description": "start this many a time",
        "frequency": "monthly",
        "task_groups": [
            {
                "title": "tg_2",
                "task_group_tasks": [{
                     "description": factories.random_str(100),
                     "relative_end_day": 1,
                     "relative_end_month": None,
                     "relative_start_day": 5,
                     "relative_start_month": None,
                }, {
                    "title": "monday task",
                    "relative_end_day": 1,
                    "relative_end_month": None,
                    "relative_start_day": 1,
                    "relative_start_month": None,
                }, {
                    "title": "weekend task",
                    "relative_end_day": 4,
                    "relative_end_month": None,
                    "relative_start_day": 1,
                    "relative_start_month": None,
                }],
                "task_group_objects": self.random_objects
            },
        ]
    }
    self.all_workflows = [
        self.one_time_workflow_1,
        self.one_time_workflow_2,
        self.weekly_wf_1,
        self.monthly_workflow_1,
        self.quarterly_wf_1,
    ]
