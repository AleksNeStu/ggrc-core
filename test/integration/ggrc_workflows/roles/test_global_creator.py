# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""
Test if global creator role has the permission to access the workflow objects,
owned by Admin.
"""
# T0D0: write tests for create, update, delete

from ggrc_workflows.models import Workflow
from ggrc_workflows.models import WorkflowPerson
from ggrc_workflows.models import TaskGroup
from ggrc_workflows.models import TaskGroupObject
from ggrc_workflows.models import TaskGroupTask
from ggrc_workflows.models import Cycle
from ggrc_workflows.models import CycleTaskGroup
from ggrc_workflows.models import CycleTaskGroupObjectTask

from integration.ggrc_workflows.roles import WorkflowRolesTestCase


class GlobalCreatorGetTest(WorkflowRolesTestCase):
  """ Get workflow objects owned by another user as global creator.
  """

  def setUp(self):
    super(GlobalCreatorGetTest, self).setUp()
    self.api.set_user(self.users['creator'])

  def test_get_obj(self):
    """ Get workflow objects from draft workflow """
    workflow_res = self.api.get(Workflow, self.workflow_obj.id)
    self.assert403(workflow_res)

    task_group_res = self.api.get(TaskGroup, self.first_task_group.id)
    self.assert403(task_group_res)

    task_group_object_res = self.api.get(
        TaskGroupObject, self.first_task_group_object.id)
    self.assert403(task_group_object_res)

    task_group_task_res = self.api.get(
        TaskGroupTask, self.first_task_group_task.id)
    self.assert403(task_group_task_res)

    workflow_person_res = self.api.get(
        WorkflowPerson, self.first_workflow_person.id)
    self.assert403(workflow_person_res)

  def test_get_active_obj(self):
    """ Get workflow objects from active workflow """
    self.workflow_res, self.workflow_obj = \
        self.activate_workflow_with_cycle(self.workflow_obj)
    self.get_first_objects()

    workflow_res = self.api.get(Workflow, self.workflow_obj.id)
    self.assert403(workflow_res)

    task_group_res = self.api.get(TaskGroup, self.first_task_group.id)
    self.assert403(task_group_res)

    task_group_object_res = self.api.get(
        TaskGroupObject, self.first_task_group_object.id)
    self.assert403(task_group_object_res)

    task_group_task_res = self.api.get(
        TaskGroupTask, self.first_task_group_task.id)
    self.assert403(task_group_task_res)

    workflow_person_res = self.api.get(
        WorkflowPerson, self.first_workflow_person.id)
    self.assert403(workflow_person_res)

    cycle_obj = self.session.query(Cycle)\
        .filter(Cycle.workflow_id == self.workflow_obj.id)\
        .first()
    cycle_res = self.api.get(
        Cycle, cycle_obj.id)
    self.assert403(cycle_res)

    cycle_task_group_obj = self.session.query(CycleTaskGroup)\
        .filter(CycleTaskGroup.cycle_id == cycle_obj.id)\
        .first()
    cycle_task_group_res = self.api.get(
        CycleTaskGroup, cycle_task_group_obj.id)
    self.assert403(cycle_task_group_res)

    # cycle_object is cycle task group object task
    cycle_object_obj =\
        self.session.query(CycleTaskGroupObjectTask)\
        .filter(
            CycleTaskGroupObjectTask.cycle_task_group_id ==
            cycle_task_group_obj.id)\
        .first()
    cycle_object_res = self.api.get(
        CycleTaskGroupObjectTask, cycle_object_obj.id)
    self.assert403(cycle_object_res)
