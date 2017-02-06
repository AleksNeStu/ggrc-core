# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Test cases which cover backlog workflow functionality"""

import mock
from sqlalchemy import and_

from ggrc import db
from ggrc.models import Person
from ggrc_basic_permissions import load_permissions_for
from ggrc_basic_permissions.models import Role
from ggrc_basic_permissions.models import UserRole
from ggrc_workflows.models import Cycle
from ggrc_workflows.models import CycleTaskGroup
from ggrc_workflows.models import CycleTaskGroupObjectTask
from ggrc_workflows.models import Workflow
from integration.ggrc import TestCase
from integration.ggrc.api_helper import Api
from integration.ggrc.generator import ObjectGenerator
from integration.ggrc_workflows.generator import WorkflowsGenerator


class TestBacklogWorkflow(TestCase):
  """Test cases for backlog workflow"""

  def setUp(self):  # noqa
    super(TestBacklogWorkflow, self).setUp()
    self.api = Api()
    self.generator = WorkflowsGenerator()
    self.object_generator = ObjectGenerator()

    self.random_objects = self.object_generator.generate_random_objects()
    self.create_backlog_workflow()

  def tearDown(self):
    pass

  def create_backlog_workflow(self):  # pylint: disable=no-self-use
    """Creates one time backlog workflow in database."""

    Workflow.ensure_backlog_workflow_exists()

  def test_add_ctgot_to_backlog_workflow(self):  # pylint: disable=invalid-name
    """Check that backlog workflow exists and test it's basic functionality"""
    # find a backlog workflow
    backlog_workflow = db.session\
                         .query(Workflow)\
                         .filter(and_(Workflow.kind == "Backlog",
                                      Workflow.frequency == "one_time")).one()
    backlog_workflow_context_id = backlog_workflow.context.id

    # check that it has an active cycle and a cycle task group
    self.assertEqual(len(backlog_workflow.cycles), 1)
    backlog_cycle = backlog_workflow.cycles[0]
    self.assertEqual(backlog_cycle.is_current, 1)

    # check if it has a cycle task group
    self.assertEqual(len(backlog_cycle.cycle_task_groups), 1)
    backlog_cycle_task_group = backlog_cycle.cycle_task_groups[0]

    # Check that backlog workflow has no workflow people
    self.assertEqual(len(backlog_workflow.people), 0)
    # create a cycle task with creator and put it in backlog workflow
    _, creator = self.object_generator.generate_person(user_role="Creator")
    self.api.set_user(creator)

    # add a task that finishes before the first task in the cycle
    cycle_task_json = {'cycle_task_group_object_task': {
        "title": "Cycle task for backlog",
        "cycle": {"id": backlog_cycle.id, "type": "Cycle"},
        "status": "Assigned",
        "cycle_task_group": {
            "id": backlog_cycle_task_group.id,
            "type": "CycleTaskGroup"
        },
        "start_date": "07/1/2015",
        "end_date": "07/2/2015",
        "task_type": "text",
        "context": {
            "id": backlog_workflow_context_id,
            "type": "Context"
        },
        "task_group_task": {"id": 0, "type": "TaskGroupTask"}
    }}

    response = self.generator.api.post(CycleTaskGroupObjectTask,
                                       cycle_task_json)
    self.assertEqual(response.status_code, 201)

    backlog_cycle_task_group = db.session.query(CycleTaskGroup).filter(
        CycleTaskGroup.cycle_id == backlog_cycle.id).one()
    # Check that changes were not propagated to backlog's CycleTaskGroup
    self.assertEqual(backlog_cycle_task_group.status, "InProgress")
    self.assertEqual(backlog_cycle_task_group.start_date, None)
    self.assertEqual(backlog_cycle_task_group.end_date, None)

    backlog_cycle = db.session.query(Cycle).filter(
        Cycle.id == backlog_cycle.id).one()
    # Check that cycle is still running
    self.assertEqual(backlog_cycle.is_current, 1)
    self.assertEqual(backlog_cycle.status, "Assigned")

  @mock.patch('ggrc_basic_permissions.get_current_user')
  def test_permissions_for_backlog_workflow(self, mock_get_current_user):  # noqa # pylint: disable=invalid-name
    """Tests whether the creator has all the necessary permissions for
    backlog workflow."""

    my_person = Person(name="kekec", email="abc@abc.com")
    creator_role = Role.query.filter(Role.name == "Creator").one()
    user_role = UserRole(role=creator_role, person=my_person)  # noqa # pylint: disable=unused-variable
    mock_get_current_user.return_value = Person(name="Mojca",
                                                email="wha12t@who.com")
    backlog_workflow = db.session\
                         .query(Workflow)\
                         .filter(and_(Workflow.kind == "Backlog",
                                      Workflow.frequency == "one_time")).one()
    workflow_ctx = backlog_workflow.context.id
    user_perms = load_permissions_for(my_person)

    actions = ["read", "edit", "update"]
    _types = ["Workflow", "Cycle", "CycleTaskGroup",
              "CycleTaskGroupObjectTask", "TaskGroup"]

    for action in actions:
      for obj_type in _types:
        self.assertTrue(workflow_ctx in
                        user_perms[action][obj_type]['contexts'])
    ctgot_ctxs = user_perms['delete']['CycleTaskGroupObjectTask']['contexts']
    self.assertTrue(workflow_ctx in ctgot_ctxs)
