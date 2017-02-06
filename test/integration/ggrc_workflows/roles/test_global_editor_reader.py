# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""
Test if global editor and global reader role has the permission to access
the workflow objects, owned by Admin.
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


class GlobalEditorReaderGetTest(WorkflowRolesTestCase):
  """ Get workflow objects owned by another user
  as global editor and global reader.
  """

  def setUp(self):
    super(GlobalEditorReaderGetTest, self).setUp()

  def assert200_helper(self, response, message=None):
    """Helper that adds the info of the current user to the message.
    """
    message = message or \
        "Requests as user: '{}' Response returned {} instead of 200."\
        .format(self.api.person_name, response.status_code)
    self.assert200(response, message)

  def test_get_obj_as_editor(self):
    """ Get workflow object from draft workflow as a editor """
    self._get_workflow_objects(self.users['editor'])

  def test_get_active_obj_as_editor(self):
    """ Get workflow object from active workflow as a editor """
    self._get_active_workflow_objects(self.users['editor'])

  def test_get_obj_as_reader(self):
    """ Get workflow object from draft workflow as a reader """
    self._get_workflow_objects(self.users['reader'])

  def test_get_active_obj_as_reader(self):
    """ Get workflow object from active workflow as a reader """
    self._get_active_workflow_objects(self.users['reader'])

  def _get_workflow_objects(self, user):
    """ Helper method that runs tests for draft workflow
    Args:
       user: Person object
    """

    self.api.set_user(user)
    workflow_res = self.api.get(Workflow, self.workflow_obj.id)
    self.assert200_helper(workflow_res)

    task_group_res = self.api.get(TaskGroup, self.first_task_group.id)
    self.assert200_helper(task_group_res)

    task_group_object_res = self.api.get(
        TaskGroupObject, self.first_task_group_object.id)
    self.assert200_helper(task_group_object_res)

    task_group_task_res = self.api.get(
        TaskGroupTask, self.first_task_group_task.id)
    self.assert200_helper(task_group_task_res)

    workflow_person_res = self.api.get(
        WorkflowPerson, self.first_workflow_person.id)
    self.assert200_helper(workflow_person_res)

  def _get_active_workflow_objects(self, user):
    """ Helper method that runs tests for active workflow
    Args:
       user: Person object
    """
    self.api.set_user(user)
    self.workflow_res, self.workflow_obj = \
        self.activate_workflow_with_cycle(self.workflow_obj)
    self.get_first_objects()

    workflow_res = self.api.get(Workflow, self.workflow_obj.id)
    self.assert200_helper(workflow_res)

    task_group_res = self.api.get(TaskGroup, self.first_task_group.id)
    self.assert200_helper(task_group_res)

    task_group_object_res = self.api.get(
        TaskGroupObject, self.first_task_group_object.id)
    self.assert200_helper(task_group_object_res)

    task_group_task_res = self.api.get(
        TaskGroupTask, self.first_task_group_task.id)
    self.assert200_helper(task_group_task_res)

    workflow_person_res = self.api.get(
        WorkflowPerson, self.first_workflow_person.id)
    self.assert200_helper(workflow_person_res)

    cycle_obj = self.session.query(Cycle)\
        .filter(Cycle.workflow_id == self.workflow_obj.id)\
        .first()
    cycle_res = self.api.get(
        Cycle, cycle_obj.id)
    self.assert200_helper(cycle_res)

    cycle_task_group_obj = self.session.query(CycleTaskGroup)\
        .filter(CycleTaskGroup.cycle_id == cycle_obj.id)\
        .first()
    cycle_task_group_res = self.api.get(
        CycleTaskGroup, cycle_task_group_obj.id)
    self.assert200_helper(cycle_task_group_res)

    # cycle_object is cycle task group object task
    cycle_object_obj =\
        self.session.query(CycleTaskGroupObjectTask)\
        .filter(
            CycleTaskGroupObjectTask.cycle_task_group_id ==
            cycle_task_group_obj.id)\
        .first()
    cycle_object_res = self.api.get(
        CycleTaskGroupObjectTask, cycle_object_obj.id)
    self.assert200_helper(cycle_object_res)
