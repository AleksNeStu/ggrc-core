# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Workflow object and WorkflowState mixins.

This contains the basic Workflow object and a mixin for determining the state
of the Objects that are mapped to any cycle tasks.
"""

from datetime import date
from sqlalchemy import and_
from sqlalchemy import orm

from ggrc import db
from ggrc.fulltext import get_indexer
from ggrc.fulltext.recordbuilder import fts_record_for
from ggrc.login import get_current_user
from ggrc.models import mixins
from ggrc.models import reflection
from ggrc.models.associationproxy import association_proxy
from ggrc.models.computed_property import computed_property
from ggrc.models.context import HasOwnContext
from ggrc.models.deferred import deferred
from ggrc_workflows.models import cycle
from ggrc_workflows.models import cycle_task_group


class Workflow(mixins.CustomAttributable, HasOwnContext, mixins.Timeboxed,
               mixins.Described, mixins.Titled,
               mixins.Notifiable, mixins.Stateful, mixins.Slugged, db.Model):
  """Basic Workflow first class object.
  """
  __tablename__ = 'workflows'
  _title_uniqueness = False

  VALID_STATES = [u"Draft", u"Active", u"Inactive"]

  VALID_FREQUENCIES = [
      "one_time",
      "weekly",
      "monthly",
      "quarterly",
      "annually"
  ]

  @classmethod
  def default_frequency(cls):
    return 'one_time'

  @orm.validates('frequency')
  def validate_frequency(self, _, value):
    """Make sure that value is listed in valid frequencies.

    Args:
      value: A string value for requested frequency

    Returns:
      default_frequency which is 'one_time' if the value is None, or the value
      itself.

    Raises:
      Value error, if the value is not None or in the VALID_FREQUENCIES array.
    """
    if value is None:
      value = self.default_frequency()
    if value not in self.VALID_FREQUENCIES:
      message = u"Invalid state '{}'".format(value)
      raise ValueError(message)
    return value

  notify_on_change = deferred(
      db.Column(db.Boolean, default=False, nullable=False), 'Workflow')
  notify_custom_message = deferred(
      db.Column(db.Text, nullable=True), 'Workflow')

  frequency = deferred(
      db.Column(db.String, nullable=True, default=default_frequency),
      'Workflow'
  )

  object_approval = deferred(
      db.Column(db.Boolean, default=False, nullable=False), 'Workflow')

  recurrences = db.Column(db.Boolean, default=False, nullable=False)

  workflow_people = db.relationship(
      'WorkflowPerson', backref='workflow', cascade='all, delete-orphan')
  people = association_proxy(
      'workflow_people', 'person', 'WorkflowPerson')

  task_groups = db.relationship(
      'TaskGroup', backref='workflow', cascade='all, delete-orphan')

  cycles = db.relationship(
      'Cycle', backref='workflow', cascade='all, delete-orphan')

  next_cycle_start_date = db.Column(db.Date, nullable=True)

  non_adjusted_next_cycle_start_date = db.Column(db.Date, nullable=True)

  # this is an indicator if the workflow exists from before the change where
  # we deleted cycle objects, which changed how the cycle is created and
  # how objects are mapped to the cycle tasks
  is_old_workflow = deferred(
      db.Column(db.Boolean, default=False, nullable=True), 'Workflow')

  # This column needs to be deferred because one of the migrations
  # uses Workflow as a model and breaks since at that point in time
  # there is no 'kind' column yet
  kind = deferred(
      db.Column(db.String, default=None, nullable=True), 'Workflow')

  @computed_property
  def workflow_state(self):
    return WorkflowState.get_workflow_state(self.cycles)

  _sanitize_html = [
      'notify_custom_message',
  ]

  _publish_attrs = [
      'workflow_people',
      reflection.PublishOnly('people'),
      'task_groups',
      'frequency',
      'notify_on_change',
      'notify_custom_message',
      'cycles',
      'object_approval',
      'recurrences',
      reflection.PublishOnly('next_cycle_start_date'),
      reflection.PublishOnly('non_adjusted_next_cycle_start_date'),
      reflection.PublishOnly('workflow_state'),
      reflection.PublishOnly('kind')
  ]

  _aliases = {
      "frequency": {
          "display_name": "Frequency",
          "mandatory": True,
      },
      "notify_custom_message": "Custom email message",
      "notify_on_change": "Force real-time email updates",
      "workflow_owner": {
          "display_name": "Manager",
          "type": reflection.AttributeInfo.Type.USER_ROLE,
          "mandatory": True,
          "filter_by": "_filter_by_workflow_owner",
      },
      "workflow_member": {
          "display_name": "Member",
          "type": reflection.AttributeInfo.Type.USER_ROLE,
          "filter_by": "_filter_by_workflow_member",
      },
      "status": None,
      "start_date": None,
      "end_date": None,
  }

  @classmethod
  def _filter_by_workflow_owner(cls, predicate):
    return cls._filter_by_role("WorkflowOwner", predicate)

  @classmethod
  def _filter_by_workflow_member(cls, predicate):
    return cls._filter_by_role("WorkflowMember", predicate)

  def copy(self, _other=None, **kwargs):
    """Create a partial copy of the current workflow.
    """
    columns = [
        'title', 'description', 'notify_on_change', 'notify_custom_message',
        'frequency', 'end_date', 'start_date'
    ]
    target = self.copy_into(_other, columns, **kwargs)
    return target

  def copy_task_groups(self, target, **kwargs):
    """Copy all task groups and tasks mapped to this workflow.
    """
    for task_group in self.task_groups:
      obj = task_group.copy(
          workflow=target,
          context=target.context,
          clone_people=kwargs.get("clone_people", False),
          clone_objects=kwargs.get("clone_objects", False),
          modified_by=get_current_user(),
      )
      target.task_groups.append(obj)

      if kwargs.get("clone_tasks"):
        task_group.copy_tasks(
            obj,
            clone_people=kwargs.get("clone_people", False),
            clone_objects=kwargs.get("clone_objects", True)
        )

    return target

  @classmethod
  def eager_query(cls):
    return super(Workflow, cls).eager_query().options(
        orm.subqueryload('cycles').undefer_group('Cycle_complete')
           .subqueryload("cycle_task_group_object_tasks")
           .undefer_group("CycleTaskGroupObjectTask_complete"),
        orm.subqueryload('task_groups'),
        orm.subqueryload('workflow_people'),
    )

  @classmethod
  def ensure_backlog_workflow_exists(cls):
    """Ensures there is at least one backlog workflow with an active cycle.
    If such workflow does not exist it creates one."""

    def any_active_cycle(workflows):
      """Checks if any active cycle exists from given workflows"""
      for workflow in workflows:
        for cur_cycle in workflow.cycles:
          if cur_cycle.is_current:
            return True
      return False

    # Check if backlog workflow already exists
    backlog_workflows = Workflow.query\
                                .filter(and_
                                        (Workflow.kind == "Backlog",
                                         Workflow.frequency == "one_time"))\
                                .all()

    if len(backlog_workflows) > 0 and any_active_cycle(backlog_workflows):
      return "At least one backlog workflow already exists"
    # Create a backlog workflow
    backlog_workflow = Workflow(description="Backlog workflow",
                                title="Backlog (one time)",
                                frequency="one_time",
                                status="Active",
                                recurrences=0,
                                kind="Backlog")

    # create wf context
    wf_ctx = backlog_workflow.get_or_create_object_context(context=1)
    backlog_workflow.context = wf_ctx
    db.session.flush(backlog_workflow)
    # create a cycle
    backlog_cycle = cycle.Cycle(description="Backlog workflow",
                                title="Backlog (one time)",
                                is_current=1,
                                status="Assigned",
                                start_date=None,
                                end_date=None,
                                context=backlog_workflow
                                .get_or_create_object_context(),
                                workflow=backlog_workflow)

    # create a cycletaskgroup
    backlog_ctg = cycle_task_group\
        .CycleTaskGroup(description="Backlog workflow taskgroup",
                        title="Backlog TaskGroup",
                        cycle=backlog_cycle,
                        status="InProgress",
                        start_date=None,
                        end_date=None,
                        context=backlog_workflow
                        .get_or_create_object_context())
    db.session.add_all([backlog_workflow, backlog_cycle, backlog_ctg])
    db.session.flush()

    # add fulltext entries
    get_indexer().create_record(fts_record_for(backlog_workflow))
    get_indexer().create_record(fts_record_for(backlog_cycle))
    get_indexer().create_record(fts_record_for(backlog_ctg))
    return "Backlog workflow created"


class WorkflowState(object):
  """Object state mixin.

  This is a mixin for adding workflow_state to all objects that can be mapped
  to workflow tasks.
  """

  _publish_attrs = [reflection.PublishOnly('workflow_state')]
  _update_attrs = []

  @classmethod
  def _get_state(cls, current_tasks):
    """Get overall state of a group of tasks.

    Rules, the first that is true is selected:
      -if all are verified -> verified
      -if all are finished -> finished
      -if all are at least finished -> finished
      -if any are in progress or declined -> in progress
      -if any are assigned -> assigned

    The function will work correctly only for non Overdue states. If the result
    is overdue, it should be handled outside of this function.

    Args:
      current_tasks: list of tasks that are currently a part of an active
        cycle or cycles that are active in an workflow.

    Returns:
      Overall state according to the rules described above.
    """
    states = [task.status or "Assigned" for task in current_tasks]

    if states.count("Verified") == len(states):
      resulting_state = "Verified"
    elif states.count("Finished") == len(states):
      resulting_state = "Finished"
    elif not set(states).intersection({"InProgress", "Assigned", "Declined"}):
      resulting_state = "Finished"
    elif set(states).intersection({"InProgress", "Declined", "Finished",
                                   "Verified"}):
      resulting_state = "InProgress"
    elif "Assigned" in states:
      resulting_state = "Assigned"
    else:
      resulting_state = None

    return resulting_state

  @classmethod
  def get_object_state(cls, objs):
    """Get lowest state of an object

    Get the lowest possible state of the tasks relevant to one object. States
    are scanned in order: Overdue, InProgress, Finished, Assigned, Verified.

    Args:
      objs: A list of cycle group object tasks, which should all be mapped to
        the same object.

    Returns:
      Name of the lowest state of all active cycle tasks that relate to the
      given objects.
    """
    current_tasks = [task for task in objs if task.cycle.is_current]

    if not current_tasks:
      return None

    today = date.today()
    overdue_tasks = any(task.end_date and
                        task.end_date < today and
                        task.status != "Verified"
                        for task in current_tasks)

    if overdue_tasks:
      return "Overdue"

    return cls._get_state(current_tasks)

  @classmethod
  def get_workflow_state(cls, cycles):
    """Get lowest state of a workflow

    Get the lowest possible state of the tasks relevant to a given workflow.
    States are scanned in order: Overdue, InProgress, Finished, Assigned,
    Verified.

    Args:
      cycles: list of cycles belonging to a single workflow.

    Returns:
      Name of the lowest workflow state, if there are any active cycles.
      Otherwise it returns None.
    """
    current_cycles = [cycle for cycle in cycles if cycle.is_current]

    if not current_cycles:
      return None

    today = date.today()
    for cycle in current_cycles:
      for task in cycle.cycle_task_group_object_tasks:
        if (task.status != "Verified" and
           task.end_date is not None and task.end_date < today):
          return "Overdue"

    return cls._get_state(current_cycles)

  @computed_property
  def workflow_state(self):
    return WorkflowState.get_object_state(self.cycle_task_group_object_tasks)
