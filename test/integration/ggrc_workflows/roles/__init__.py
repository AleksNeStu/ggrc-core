# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Test how different roles can access Workflow specific object"""

from datetime import date

from ggrc import db
from ggrc_workflows.models import TaskGroup
from ggrc_workflows.models import TaskGroupTask
from ggrc_workflows.models import TaskGroupObject
from ggrc_workflows.models import WorkflowPerson
from integration.ggrc_workflows import WorkflowTestCase


class WorkflowRolesTestCase(WorkflowTestCase):
  """Workflow roles test case"""

  def setUp(self):
    super(WorkflowRolesTestCase, self).setUp()

    self.workflow_res = None
    self.workflow_obj = None

    self.users = {}

    self.session = db.session
    self.init_users()
    self.random_objects = self.object_generator.generate_random_objects()
    self.init_workflow()
    self.get_first_objects()

  def get_first_objects(self):
    """ Get the first object from the database set them as attributes """
    self.first_task_group = self.get_task_groups(self.workflow_obj.id)[0]
    self.first_task_group_task = self.get_task_group_tasks(
        self.first_task_group.id)[0]
    self.first_task_group_object = self.get_task_group_objects(
        self.first_task_group.id)[0]
    self.first_workflow_person = self.get_workflow_persons(
        self.workflow_obj.id)[0]

  def init_users(self):
    """Initializes users needed by the test"""

    users = [
        ("creator", "Creator"),
        ("reader", "Reader"),
        ("editor", "Editor"),
        ("admin", "Administrator")
    ]
    for (name, role) in users:
      _, user = self.object_generator.generate_person(
          data={"name": name}, user_role=role)
      self.users[name] = user

  def init_workflow(self):
    """Creates a workflow which is owned by an user with Admin role"""

    initial_workflow_data = {
        "title": "test workflow",
        "description": "test workflow",
        "owners": [self.person_dict(self.users['admin'].id)],
        "status": "Draft",
        "task_groups": [{
            "title": "task group 1",
            "contact": self.person_dict(self.users['admin'].id),
            "task_group_tasks": [{
                "title": "task 1",
                "description": "some task",
                "contact": self.person_dict(self.users['admin'].id),
                "start_date": date(2016, 5, 26),
                "end_date": date(2016, 5, 28),
            }],
            "task_group_objects": self.random_objects[:2]
        }]
    }

    self.workflow_res, self.workflow_obj =\
        self.generator.generate_workflow(initial_workflow_data)

  def activate_workflow_with_cycle(self, workflow_obj):
    """
    Args:
        workflow_obj: Workflow model instance
    Returns:
        A tuple with a response object and the reference to mutated workflow
    """
    self.generator.generate_cycle(workflow_obj)
    workflow_res, workflow_obj = \
        self.generator.activate_workflow(self.workflow_obj)

    return workflow_res, workflow_obj

  def get_task_groups(self, workflow_id):
    """ Gets all the task groups in a workflow.
    Args:
        workflow_id: Id of the workflow. Integer.
    Returns:
        List of TaskGroup model instances
    """
    task_groups = self.session.query(TaskGroup)\
        .filter(TaskGroup.workflow_id == workflow_id)\
        .all()

    return task_groups

  def get_task_group_tasks(self, task_group_id):
    """ Gets al the task group tasks in a task group.
    Args:
        taks_group_id: Integer.
    Returns:
        List of TaskGroupTask model instances
    """
    task_group_tasks = self.session.query(TaskGroupTask)\
        .filter(TaskGroupTask.task_group_id == task_group_id)\
        .all()

    return task_group_tasks

  def get_task_group_objects(self, task_group_id):
    """ Gets al the task group objects in a task group.
    Args:
        taks_group_id: Integer.
    Returns:
        List of TaskGroupObject model instances
    """
    task_group_objects = self.session.query(TaskGroupObject)\
        .filter(TaskGroupTask.task_group_id == task_group_id)\
        .all()

    return task_group_objects

  def get_workflow_persons(self, workflow_id):
    """ Gets al the task group objects in a task group.
    Args:
        taks_group_id: Integer.
    Returns:
        List of TaskGroupObject model instances
    """
    workflow_persons = self.session.query(WorkflowPerson)\
        .filter(WorkflowPerson.workflow_id == workflow_id)\
        .all()

    return workflow_persons

  def person_dict(self, person_id):
    """
    Args:
        person_id: Integer.

    Returns:
        A dict which can be later serialized to JSON for person creation
    """
    return {
        "href": "/api/people/%d" % person_id,
        "id": person_id,
        "type": "Person"
    }
