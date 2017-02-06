# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Tests for workflow cycle state propagation between tasks and task groups"""

# pylint: disable=invalid-name

from freezegun import freeze_time

from ggrc import db
from ggrc_workflows.models import Cycle
from ggrc_workflows.models import CycleTaskGroupObjectTask
from ggrc_workflows.models import CycleTaskGroup
from ggrc_workflows.models import Workflow
from integration.ggrc import TestCase
from integration.ggrc_workflows.generator import WorkflowsGenerator
from integration.ggrc.api_helper import Api
from integration.ggrc.generator import ObjectGenerator


class TestWorkflowCycleStatePropagantion(TestCase):
  """Test case for cycle task to cycle task group status propagation"""

  def setUp(self):
    super(TestWorkflowCycleStatePropagantion, self).setUp()
    self.api = Api()
    self.generator = WorkflowsGenerator()
    self.object_generator = ObjectGenerator()

    self.weekly_wf = {
        "title": "weekly thingy",
        "description": "start this many a time",
        "frequency": "weekly",
        "task_groups": [{
            "title": "weekly task group",
            "task_group_tasks": [{
                "title": "weekly task 1",
                "relative_end_day": 1,
                "relative_end_month": None,
                "relative_start_day": 5,
                "relative_start_month": None,
            }, {
                "title": "weekly task 1",
                "relative_end_day": 1,
                "relative_end_month": None,
                "relative_start_day": 1,
                "relative_start_month": None,
            }
            ]},
        ]
    }

  def test_weekly_state_transitions_assigned_inprogress(self):
    "Test that starting one cycle task changes cycle task group"
    _, wf = self.generator.generate_workflow(self.weekly_wf)

    with freeze_time("2016-6-10 13:00:00"):  # Friday, 6/10/2016
      self.generator.activate_workflow(wf)

      ctg = db.session.query(CycleTaskGroup).join(
          Cycle).join(Workflow).filter(Workflow.id == wf.id).all()[0]
      self.assertEqual(ctg.status, "Assigned")

      cycle_tasks = db.session.query(CycleTaskGroupObjectTask).join(
          Cycle).join(Workflow).filter(Workflow.id == wf.id).all()
      first_ct, second_ct = cycle_tasks

      for cycle_task in cycle_tasks:
        self.assertEqual(cycle_task.status, "Assigned")

      # Move one task to InProgress
      _, first_ct = self.generator.modify_object(
          first_ct, {"status": "InProgress"})

      self.assertEqual(first_ct.status, "InProgress")
      ctg = db.session.query(CycleTaskGroup).get(ctg.id)
      self.assertEqual(ctg.status, "InProgress")

      # Undo operation
      _, first_ct = self.generator.modify_object(
          first_ct, {"status": "Assigned"})

      self.assertEqual(first_ct.status, "Assigned")
      ctg = db.session.query(CycleTaskGroup).get(ctg.id)
      self.assertEqual(ctg.status, "Assigned")

      # Move both to in progress
      for cycle_task in cycle_tasks:
        self.generator.modify_object(
            cycle_task, {"status": "InProgress"})

      ctg = db.session.query(CycleTaskGroup).get(ctg.id)
      self.assertEqual(ctg.status, "InProgress")

      # Undo one cycle task
      _, first_ct = self.generator.modify_object(
          first_ct, {"status": "Assigned"})
      second_ct = db.session.query(CycleTaskGroupObjectTask).get(second_ct.id)
      ctg = db.session.query(CycleTaskGroup).get(ctg.id)

      self.assertEqual(first_ct.status, "Assigned")
      self.assertEqual(second_ct.status, "InProgress")
      self.assertEqual(ctg.status, "InProgress")

      # Undo second cycle task
      _, second_ct = self.generator.modify_object(
          second_ct, {"status": "Assigned"})
      first_ct = db.session.query(CycleTaskGroupObjectTask).get(first_ct.id)
      ctg = db.session.query(CycleTaskGroup).get(ctg.id)

      self.assertEqual(first_ct.status, "Assigned")
      self.assertEqual(second_ct.status, "Assigned")
      self.assertEqual(ctg.status, "Assigned")

  def test_weekly_state_transitions_inprogress_finished(self):
    "Test In Progress to Finished transitions"
    _, wf = self.generator.generate_workflow(self.weekly_wf)

    with freeze_time("2016-6-10 13:00:00"):  # Friday, 6/10/2016
      self.generator.activate_workflow(wf)

      ctg = db.session.query(CycleTaskGroup).join(
          Cycle).join(Workflow).filter(Workflow.id == wf.id).all()[0]

      cycle_tasks = db.session.query(CycleTaskGroupObjectTask).join(
          Cycle).join(Workflow).filter(Workflow.id == wf.id).all()
      first_ct, second_ct = cycle_tasks

      # Move both tasks to InProgress
      for cycle_task in cycle_tasks:
        self.generator.modify_object(
            cycle_task, {"status": "InProgress"})

      # Test that moving one task to finished doesn't finish entire cycle
      _, first_ct = self.generator.modify_object(
          first_ct, {"status": "Finished"})
      second_ct = db.session.query(CycleTaskGroupObjectTask).get(second_ct.id)
      ctg = db.session.query(CycleTaskGroup).get(ctg.id)

      self.assertEqual(first_ct.status, "Finished")
      self.assertEqual(second_ct.status, "InProgress")
      self.assertEqual(ctg.status, "InProgress")

      # Test moving second task to Finished - entire cycle should be finished
      _, second_ct = self.generator.modify_object(
          second_ct, {"status": "Finished"})
      first_ct = db.session.query(CycleTaskGroupObjectTask).get(first_ct.id)
      ctg = db.session.query(CycleTaskGroup).get(ctg.id)

      self.assertEqual(second_ct.status, "Finished")
      self.assertEqual(first_ct.status, "Finished")
      self.assertEqual(ctg.status, "Finished")

      # Undo one task, cycle should be InProgress
      _, first_ct = self.generator.modify_object(
          first_ct, {"status": "InProgress"})
      second_ct = db.session.query(CycleTaskGroupObjectTask).get(second_ct.id)
      ctg = db.session.query(CycleTaskGroup).get(ctg.id)

      self.assertEqual(first_ct.status, "InProgress")
      self.assertEqual(second_ct.status, "Finished")
      self.assertEqual(ctg.status, "InProgress")

  def test_weekly_state_transitions_finished_verified(self):
    "Test Finished to Verified transitions"
    _, wf = self.generator.generate_workflow(self.weekly_wf)

    with freeze_time("2016-6-10 13:00:00"):  # Friday, 6/10/2016
      self.generator.activate_workflow(wf)

      ctg = db.session.query(CycleTaskGroup).join(
          Cycle).join(Workflow).filter(Workflow.id == wf.id).all()[0]

      cycle_tasks = db.session.query(CycleTaskGroupObjectTask).join(
          Cycle).join(Workflow).filter(Workflow.id == wf.id).all()
      first_ct, second_ct = cycle_tasks

      # Move both tasks to InProgress
      for cycle_task in cycle_tasks:
        self.generator.modify_object(
            cycle_task, {"status": "InProgress"})
        self.generator.modify_object(
            cycle_task, {"status": "Finished"})

      ctg = db.session.query(CycleTaskGroup).get(ctg.id)
      self.assertEqual(ctg.status, "Finished")

      for cycle_task in cycle_tasks:
        cycle_task = db.session.query(CycleTaskGroupObjectTask).get(
            cycle_task.id)
        self.assertEqual(cycle_task.status, "Finished")

      # Verify first CT
      _, first_ct = self.generator.modify_object(
          first_ct, {"status": "Verified"})

      second_ct = db.session.query(CycleTaskGroupObjectTask).get(second_ct.id)
      ctg = db.session.query(CycleTaskGroup).get(ctg.id)

      self.assertEqual(first_ct.status, "Verified")
      self.assertEqual(second_ct.status, "Finished")
      self.assertEqual(ctg.status, "Finished")

      # Verify second CT
      _, second_ct = self.generator.modify_object(
          second_ct, {"status": "Verified"})

      first_ct = db.session.query(CycleTaskGroupObjectTask).get(first_ct.id)
      ctg = db.session.query(CycleTaskGroup).get(ctg.id)

      self.assertEqual(first_ct.status, "Verified")
      self.assertEqual(second_ct.status, "Verified")
      self.assertEqual(ctg.status, "Verified")

  def test_weekly_state_transitions_finished_declined(self):
    "Test Finished to Declined transitions"
    _, wf = self.generator.generate_workflow(self.weekly_wf)

    with freeze_time("2016-6-10 13:00:00"):  # Friday, 6/10/2016
      self.generator.activate_workflow(wf)

      ctg = db.session.query(CycleTaskGroup).join(
          Cycle).join(Workflow).filter(Workflow.id == wf.id).all()[0]

      cycle_tasks = db.session.query(CycleTaskGroupObjectTask).join(
          Cycle).join(Workflow).filter(Workflow.id == wf.id).all()
      first_ct, second_ct = cycle_tasks

      # Move both tasks to InProgress
      for cycle_task in cycle_tasks:
        self.generator.modify_object(
            cycle_task, {"status": "InProgress"})
        self.generator.modify_object(
            cycle_task, {"status": "Finished"})

      ctg = db.session.query(CycleTaskGroup).get(ctg.id)
      self.assertEqual(ctg.status, "Finished")

      # Decline first CT
      _, first_ct = self.generator.modify_object(
          first_ct, {"status": "Declined"})

      second_ct = db.session.query(CycleTaskGroupObjectTask).get(second_ct.id)
      ctg = db.session.query(CycleTaskGroup).get(ctg.id)

      self.assertEqual(first_ct.status, "Declined")
      self.assertEqual(second_ct.status, "Finished")
      self.assertEqual(ctg.status, "InProgress")
