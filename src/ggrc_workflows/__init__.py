# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

from datetime import datetime, date
from flask import Blueprint
from sqlalchemy import inspect, and_, orm

from ggrc import db
from ggrc.login import get_current_user
from ggrc.models import all_models
from ggrc.models.relationship import Relationship
from ggrc.rbac.permissions import is_allowed_update
from ggrc.services.common import Resource, log_event
from ggrc.services.registry import service
from ggrc_workflows import models, notification
from ggrc_workflows.models import relationship_helper
from ggrc_workflows.models import WORKFLOW_OBJECT_TYPES
from ggrc_workflows.converters import IMPORTABLE, EXPORTABLE
from ggrc_workflows.converters.handlers import COLUMN_HANDLERS
from ggrc_workflows.services.common import Signals
from ggrc_workflows.services import workflow_cycle_calculator
from ggrc_workflows.roles import (
    WorkflowOwner, WorkflowMember, BasicWorkflowReader, WorkflowBasicReader
)
from ggrc_workflows import utils
from ggrc_basic_permissions.models import Role, UserRole, ContextImplication
from ggrc_basic_permissions.contributed_roles import (
    RoleContributions, RoleDeclarations, DeclarativeRoleImplications
)


# Initialize Flask Blueprint for extension
blueprint = Blueprint(
    'ggrc_workflows',
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/static/ggrc_workflows',
)


for type_ in WORKFLOW_OBJECT_TYPES:
  model = getattr(all_models, type_)
  model.__bases__ = (
      models.task_group_object.TaskGroupable,
      models.cycle_task_group_object_task.CycleTaskable,
      models.workflow.WorkflowState,
  ) + model.__bases__
  model.late_init_task_groupable()


def get_public_config(current_user):  # noqa
  """Expose additional permissions-dependent config to client.
  """
  return {}

# Initialize service endpoints


def contributed_services():
  return [
      service('workflows', models.Workflow),
      service('workflow_people', models.WorkflowPerson),
      service('task_groups', models.TaskGroup),
      service('task_group_tasks', models.TaskGroupTask),
      service('task_group_objects', models.TaskGroupObject),

      service('cycles', models.Cycle),
      service('cycle_task_entries', models.CycleTaskEntry),
      service('cycle_task_groups', models.CycleTaskGroup),
      service('cycle_task_group_object_tasks', models.CycleTaskGroupObjectTask)
  ]


def contributed_object_views():
  """Contributed object views"""
  from ggrc.views.registry import object_view

  return [
      object_view(models.Workflow),
  ]


DONE_STATUSES = ("Verified",)


def _get_min_next_due_date(due_dated_objects, exclude_statuses=DONE_STATUSES):
  next_due_date = None

  for obj in due_dated_objects:
    if obj.status not in exclude_statuses:
      obj_next_due_date = obj.next_due_date
      if isinstance(obj_next_due_date, datetime):
        obj_next_due_date = obj_next_due_date.date()
      if obj_next_due_date is not None:
        if next_due_date is None or next_due_date > obj_next_due_date:
          next_due_date = obj_next_due_date

  return next_due_date


def _get_min_end_date(timeboxed_objects, exclude_statuses=DONE_STATUSES):
  end_date = None

  for obj in timeboxed_objects:
    if obj.status not in exclude_statuses:
      obj_end_date = obj.end_date
      if isinstance(obj_end_date, datetime):
        obj_end_date = obj_end_date.date()
      if obj_end_date is not None:
        if end_date is None or end_date > obj_end_date:
          end_date = obj_end_date
  return end_date


def _get_date_range(timeboxed_objects):
  start_date = None
  end_date = None

  for obj in timeboxed_objects:
    obj_start_date = obj.start_date
    if isinstance(obj_start_date, datetime):
      obj_start_date = obj_start_date.date()
    obj_end_date = obj.end_date
    if isinstance(obj_end_date, datetime):
      obj_end_date = obj_end_date.date()
    if obj_start_date is not None:
      if start_date is None or start_date > obj_start_date:
        start_date = obj_start_date
    if obj_end_date is not None:
      if end_date is None or end_date < obj_end_date:
        end_date = obj_end_date
  return start_date, end_date


def update_cycle_dates(cycle):
  """ This gets all cycle task groups and tasks associated with a cycle and
  calculates the start and end date for the cycle by aggregating cycle task
  dates to cycle task groups and then cycle task group dates to cycle.

  Args:
    cycle: Cycle for which we want to calculate the start and end dates.

  """
  if cycle.id:
    # If `cycle` is already in the database, then eager load required objects
    cycle = models.Cycle.query.filter_by(id=cycle.id).\
        options(orm
                .joinedload('cycle_task_groups')
                .joinedload('cycle_task_group_tasks')
                ).one()

  if not cycle.cycle_task_group_object_tasks and \
     cycle.workflow.kind != "Backlog":
    cycle.start_date, cycle.end_date = None, None
    cycle.next_due_date = None
    cycle.is_current = False
    db.session.add(cycle)
    return

  # Don't update cycle and cycle task group dates for backlog workflows
  if cycle.workflow.kind == "Backlog":
    return

  for ctg in cycle.cycle_task_groups:
    ctg.start_date, ctg.end_date = _get_date_range(
        ctg.cycle_task_group_tasks)
    ctg.next_due_date = _get_min_end_date(
        ctg.cycle_task_group_tasks)

  cycle.start_date, cycle.end_date = _get_date_range(cycle.cycle_task_groups)
  cycle.next_due_date = _get_min_next_due_date(cycle.cycle_task_groups)


@Resource.model_posted.connect_via(models.Cycle)
def handle_cycle_post(sender, obj=None, src=None, service=None):  # noqa pylint: disable=unused-argument
  if src.get('autogenerate', False):
    # When called via a REST POST, use current user.
    current_user = get_current_user()
    workflow = obj.workflow
    obj.calculator = workflow_cycle_calculator.get_cycle_calculator(workflow)

    if workflow.non_adjusted_next_cycle_start_date:
      base_date = workflow.non_adjusted_next_cycle_start_date
    else:
      base_date = date.today()
    build_cycle(obj, current_user=current_user, base_date=base_date)

    adjust_next_cycle_start_date(obj.calculator, workflow, move_forward=True)
    update_workflow_state(workflow)
    db.session.add(workflow)


def _create_cycle_task(task_group_task, cycle, cycle_task_group,
                       current_user, base_date=None):
  """Create a cycle task along with relations to other objects"""
  # TaskGroupTasks for one_time workflows don't save relative start/end
  # month/day. They only saves start and end dates.
  # TaskGroupTasks for all other workflow frequencies save the relative
  # start/end days.
  if not base_date:
    base_date = date.today()

  description = models.CycleTaskGroupObjectTask.default_description if \
      task_group_task.object_approval else task_group_task.description

  date_range = cycle.calculator.task_date_range(
      task_group_task, base_date=base_date)
  start_date, end_date = date_range

  cycle_task_group_object_task = models.CycleTaskGroupObjectTask(
      context=cycle.context,
      cycle=cycle,
      cycle_task_group=cycle_task_group,
      task_group_task=task_group_task,
      title=task_group_task.title,
      description=description,
      sort_index=task_group_task.sort_index,
      start_date=start_date,
      end_date=end_date,
      contact=task_group_task.contact,
      status="Assigned",
      modified_by=current_user,
      task_type=task_group_task.task_type,
      response_options=task_group_task.response_options,
  )
  return cycle_task_group_object_task


def create_old_style_cycle(cycle, task_group, cycle_task_group, current_user,
                           base_date):
  """ This function preserves the old style of creating cycles, so each object
  gets its own task assigned to it.
  """
  if len(task_group.task_group_objects) == 0:
    for task_group_task in task_group.task_group_tasks:
      cycle_task_group_object_task = _create_cycle_task(
          task_group_task, cycle, cycle_task_group,
          current_user, base_date)

  for task_group_object in task_group.task_group_objects:
    object_ = task_group_object.object
    for task_group_task in task_group.task_group_tasks:
      cycle_task_group_object_task = _create_cycle_task(
          task_group_task, cycle, cycle_task_group,
          current_user, base_date)
      db.session.add(Relationship(source=cycle_task_group_object_task,
                                  destination=object_))


def build_cycle(cycle, current_user=None, base_date=None):
  """Build a cycle with it's child objects"""

  if not base_date:
    base_date = date.today()

  # Determine the relevant Workflow
  workflow = cycle.workflow

  # Use WorkflowOwner role when this is called via the cron job.
  if not current_user:
    for user_role in workflow.context.user_roles:
      if user_role.role.name == "WorkflowOwner":
        current_user = user_role.person
        break

  # Populate the top-level Cycle object
  cycle.context = workflow.context
  cycle.title = workflow.title
  cycle.description = workflow.description
  cycle.status = 'Assigned'

  # Populate CycleTaskGroups based on Workflow's TaskGroups
  for task_group in workflow.task_groups:
    cycle_task_group = models.CycleTaskGroup(
        context=cycle.context,
        cycle=cycle,
        task_group=task_group,
        title=task_group.title,
        description=task_group.description,
        end_date=cycle.end_date,
        modified_by=current_user,
        contact=task_group.contact,
        status="Assigned",
        sort_index=task_group.sort_index,
    )

    # preserve the old cycle creation for old workflows, so each object
    # gets its own cycle task
    if workflow.is_old_workflow:
      create_old_style_cycle(cycle, task_group, cycle_task_group, current_user,
                             base_date)
    else:
      for task_group_task in task_group.task_group_tasks:
        cycle_task_group_object_task = _create_cycle_task(
            task_group_task, cycle, cycle_task_group, current_user, base_date)

        for task_group_object in task_group.task_group_objects:
          object_ = task_group_object.object
          db.session.add(Relationship(source=cycle_task_group_object_task,
                                      destination=object_))

  update_cycle_dates(cycle)

  Signals.workflow_cycle_start.send(
      cycle.__class__,
      obj=cycle,
      new_status=cycle.status,
      old_status=None
  )

# 'InProgress' states propagate via these links
_cycle_task_parent_attr = {
    models.CycleTaskGroupObjectTask: ['cycle_task_group'],
    models.CycleTaskGroup: ['cycle']
}

# 'Finished' and 'Verified' states are determined via these links
_cycle_task_children_attr = {
    models.CycleTaskGroup: ['cycle_task_group_tasks'],
    models.Cycle: ['cycle_task_groups']
}


def update_cycle_task_child_state(obj):

  status_order = (None, 'Assigned', 'InProgress',
                  'Declined', 'Finished', 'Verified')
  status = obj.status
  children_attrs = _cycle_task_children_attr.get(type(obj), [])
  for children_attr in children_attrs:
    if children_attr:
      children = getattr(obj, children_attr, None)
      for child in children:
        if status == 'Declined' or \
           status_order.index(status) > status_order.index(child.status):
          if is_allowed_update(child.__class__.__name__,
                               child.id, child.context.id):
            old_status = child.status
            child.status = status
            db.session.add(child)
            Signals.status_change.send(
                child.__class__,
                obj=child,
                new_status=child.status,
                old_status=old_status
            )
          update_cycle_task_child_state(child)


def update_cycle_task_parent_state(obj):  # noqa
  """Propagate changes to obj's parents"""

  if not is_allowed_update(obj.__class__.__name__,
                           obj.id, obj.context.id):
    return

  def update_parent(parent, old_status, new_status):
    """Update a parent element and emit a signal about the change"""
    parent.status = new_status
    db.session.add(parent)
    Signals.status_change.send(
        parent.__class__,
        obj=parent,
        old_status=old_status,
        new_status=new_status,
    )
    update_cycle_task_parent_state(parent)

  parent_attrs = _cycle_task_parent_attr.get(type(obj), [])
  for parent_attr in parent_attrs:
    if not parent_attr:
      continue

    parent = getattr(obj, parent_attr, None)
    old_status = parent.status
    if not parent:
      continue

    # Don't propagate changes to CycleTaskGroup if it's a part of backlog wf
    if isinstance(parent, models.CycleTaskGroup) \
       and parent.cycle.workflow.kind == "Backlog":
      continue

    # If any child is `InProgress`, then parent should be `InProgress`
    if obj.status in {"InProgress", "Declined"} and old_status != "InProgress":
      new_status = "InProgress"
      update_parent(parent, old_status, new_status)
    # If all children are `Finished` or `Verified`, then parent should be same
    elif obj.status in {"Finished", "Verified", "Assigned"}:
      children_attrs = _cycle_task_children_attr.get(type(parent), [])
      for children_attr in children_attrs:
        children = getattr(parent, children_attr, None)
        if not children:
          continue

        children_statues = [c.status for c in children]
        unique_statuses = set(children_statues)
        for status in ["Verified", "Finished", "Assigned"]:
          # Check if all elements match a certain state
          if children_statues[0] == status and len(unique_statuses) == 1:
            new_status = status
            update_parent(parent, old_status, new_status)


def ensure_assignee_is_workflow_member(workflow, assignee):
  """Checks what role assignee has in the context of
  a workflow. If he has none he gets the Workflow Member role."""
  if not assignee:
    return

  if any(assignee == wp.person for wp in workflow.workflow_people):
    return

  # Check if assignee is mapped to the Workflow
  workflow_people = models.WorkflowPerson.query.filter(
      models.WorkflowPerson.workflow_id == workflow.id,
      models.WorkflowPerson.person_id == assignee.id).count()
  if not workflow_people:
    workflow_person = models.WorkflowPerson(
        person=assignee,
        workflow=workflow,
        context=workflow.context
    )
    db.session.add(workflow_person)

  # Check if assignee has a role assignment
  from ggrc_basic_permissions.models import UserRole
  user_roles = UserRole.query.filter(
      UserRole.context_id == workflow.context_id,
      UserRole.person_id == assignee.id).count()
  if not user_roles:
    workflow_member_role = _find_role('WorkflowMember')
    user_role = UserRole(
        person=assignee,
        role=workflow_member_role,
        context=workflow.context,
        modified_by=get_current_user(),
    )
    db.session.add(user_role)


@Resource.model_put.connect_via(models.TaskGroupTask)
def handle_task_group_task_put(sender, obj=None, src=None, service=None):  # noqa pylint: disable=unused-argument
  if inspect(obj).attrs.contact.history.has_changes():
    ensure_assignee_is_workflow_member(obj.task_group.workflow, obj.contact)

  # If relative days were change we must update workflow next cycle start date
  workflow_modifying_attrs = [
      "relative_start_day", "relative_start_month",
      "relative_end_day", "relative_end_month"]

  if any(getattr(inspect(obj).attrs, attr).history.has_changes()
         for attr in workflow_modifying_attrs):
    db.session.add(obj)
    update_workflow_state(obj.task_group.workflow)


@Resource.model_posted.connect_via(models.TaskGroupTask)
def handle_task_group_task_post(sender, obj=None, src=None, service=None):  # noqa pylint: disable=unused-argument
  ensure_assignee_is_workflow_member(obj.task_group.workflow, obj.contact)
  update_workflow_state(obj.task_group.workflow)


@Resource.model_deleted.connect_via(models.TaskGroupTask)
def handle_task_group_task_delete(sender, obj=None, src=None, service=None):  # noqa pylint: disable=unused-argument
  db.session.flush()
  update_workflow_state(obj.task_group.workflow)


@Resource.model_put.connect_via(models.TaskGroup)
def handle_task_group_put(sender, obj=None, src=None, service=None):  # noqa pylint: disable=unused-argument
  if inspect(obj).attrs.contact.history.has_changes():
    ensure_assignee_is_workflow_member(obj.workflow, obj.contact)


@Resource.model_posted.connect_via(models.TaskGroup)
def handle_task_group_post(sender, obj=None, src=None, service=None):  # noqa pylint: disable=unused-argument
  source_task_group = None

  if src.get('clone'):
    source_task_group_id = src.get('clone')
    source_task_group = models.TaskGroup.query.filter_by(
        id=source_task_group_id
    ).first()
    source_task_group.copy(
        obj,
        clone_people=src.get('clone_people', False),
        clone_tasks=src.get('clone_tasks', False),
        clone_objects=src.get('clone_objects', False)
    )

    db.session.add(obj)
    db.session.flush()

    obj.title = source_task_group.title + ' (copy ' + str(obj.id) + ')'

  ensure_assignee_is_workflow_member(obj.workflow, obj.contact)


@Resource.model_deleted.connect_via(models.TaskGroup)
def handle_task_group_delete(sender, obj=None, src=None, service=None):  # noqa pylint: disable=unused-argument
  db.session.flush()
  update_workflow_state(obj.workflow)


@Resource.model_deleted.connect_via(models.CycleTaskGroupObjectTask)
def handle_cycle_task_group_object_task_delete(sender, obj=None,
                                               src=None, service=None):  # noqa pylint: disable=unused-argument
  db.session.flush()
  update_cycle_dates(obj.cycle)


@Resource.model_put.connect_via(models.CycleTaskGroupObjectTask)
def handle_cycle_task_group_object_task_put(
        sender, obj=None, src=None, service=None):  # noqa pylint: disable=unused-argument

  if inspect(obj).attrs.contact.history.has_changes():
    ensure_assignee_is_workflow_member(obj.cycle.workflow, obj.contact)

  if inspect(obj).attrs.start_date.history.has_changes() \
          or inspect(obj).attrs.end_date.history.has_changes():
    update_cycle_dates(obj.cycle)

  if inspect(obj).attrs.status.history.has_changes():
    # TODO: check why update_cycle_object_parent_state destroys object history
    # when accepting the only task in a cycle. The listener below is a
    # workaround because of that.
    Signals.status_change.send(
        obj.__class__,
        obj=obj,
        new_status=obj.status,
        old_status=inspect(obj).attrs.status.history.deleted.pop(),
    )
    update_cycle_task_parent_state(obj)

  # Doing this regardless of status.history.has_changes() is important in order
  # to update objects that have been declined. It updates the os_last_updated
  # date and last_updated_by.
  if getattr(obj.task_group_task, 'object_approval', None):
    for tgobj in obj.task_group_task.task_group.objects:
      if obj.status == 'Verified':
        tgobj.set_reviewed_state()
        db.session.add(tgobj)
    db.session.flush()


@Resource.model_posted.connect_via(models.CycleTaskGroupObjectTask)
def handle_cycle_task_group_object_task_post(
        sender, obj=None, src=None, service=None):  # noqa pylint: disable=unused-argument

  if obj.cycle.workflow.kind != "Backlog":
    ensure_assignee_is_workflow_member(obj.cycle.workflow, obj.contact)
  update_cycle_dates(obj.cycle)

  Signals.status_change.send(
      obj.__class__,
      obj=obj,
      new_status=obj.status,
      old_status=None,
  )
  update_cycle_task_parent_state(obj)
  db.session.flush()


@Resource.model_put.connect_via(models.CycleTaskGroup)
def handle_cycle_task_group_put(
        sender, obj=None, src=None, service=None):  # noqa pylint: disable=unused-argument
  if inspect(obj).attrs.status.history.has_changes():
    update_cycle_task_parent_state(obj)
    update_cycle_task_child_state(obj)


def update_workflow_state(workflow):
  today = date.today()
  calculator = workflow_cycle_calculator.get_cycle_calculator(workflow)

  # Start the first cycle if min_start_date < today < max_end_date
  if workflow.status == "Active" and workflow.recurrences and calculator.tasks:
    start_date, end_date = calculator.workflow_date_range()
    # Only create the cycle if we're mid-cycle
    if (start_date <= today <= end_date) \
            and not workflow.cycles:
      cycle = models.Cycle()
      cycle.workflow = workflow
      cycle.calculator = calculator
      # Other cycle attributes will be set in build_cycle.
      build_cycle(
          cycle,
          None,
          base_date=workflow.non_adjusted_next_cycle_start_date)
      notification.handle_cycle_created(None, obj=cycle)

    adjust_next_cycle_start_date(calculator, workflow)

    db.session.add(workflow)
    db.session.flush()
    return

  if not calculator.tasks:
    workflow.next_cycle_start_date = None
    workflow.non_adjusted_next_cycle_start_date = None
    return

  for cycle in workflow.cycles:
    if cycle.is_current:
      return

  if workflow.status == 'Draft':
    return

  if workflow.status == "Inactive":
    if workflow.cycles:
      workflow.status = "Active"
      db.session.add(workflow)
      db.session.flush()
      return

  # Active workflow with no recurrences and no active cycles, workflow is
  # now Inactive
  workflow.status = 'Inactive'
  db.session.add(workflow)
  db.session.flush()

# Check if workflow should be Inactive after end current cycle


@Resource.model_put.connect_via(models.Cycle)
def handle_cycle_put(
        sender, obj=None, src=None, service=None):  # noqa pylint: disable=unused-argument
  if inspect(obj).attrs.is_current.history.has_changes():
    update_workflow_state(obj.workflow)

# Check if workflow should be Inactive after recurrence change


@Resource.model_put.connect_via(models.Workflow)
def handle_workflow_put(
        sender, obj=None, src=None, service=None):  # noqa pylint: disable=unused-argument  # noqa pylint: disable=unused-argument
  update_workflow_state(obj)


@Resource.model_posted.connect_via(models.CycleTaskEntry)
def handle_cycle_task_entry_post(
        sender, obj=None, src=None, service=None):  # noqa pylint: disable=unused-argument
  if src['is_declining_review'] == '1':
    task = obj.cycle_task_group_object_task
    task.status = 'Declined'
    db.session.add(obj)
  else:
    src['is_declining_review'] = 0

# Check if workflow should be Inactive after cycle status change


@Signals.status_change.connect_via(models.Cycle)
def handle_cycle_status_change(sender, obj=None, new_status=None,  # noqa pylint: disable=unused-argument
                               old_status=None):  # noqa pylint: disable=unused-argument  # noqa pylint: disable=unused-argument
  if inspect(obj).attrs.status.history.has_changes():
    if obj.status == 'Verified':
      obj.is_current = False
      db.session.add(obj)
      update_workflow_state(obj.workflow)


@Signals.status_change.connect_via(models.CycleTaskGroupObjectTask)
def handle_cycle_task_status_change(sender, obj=None, new_status=None,  # noqa pylint: disable=unused-argument
                                    old_status=None):  # noqa pylint: disable=unused-argument
  if inspect(obj).attrs.status.history.has_changes():
    if new_status == 'Verified':
      obj.verified_date = datetime.now()
    elif new_status == 'Finished':
      obj.finished_date = datetime.now()
      obj.verified_date = None
    else:
      obj.finished_date = None
      obj.verified_date = None


def _get_or_create_personal_context(user):
  personal_context = user.get_or_create_object_context(
      context=1,
      name='Personal Context for {0}'.format(user.id),
      description='',
  )
  personal_context.modified_by = get_current_user()
  db.session.add(personal_context)
  db.session.flush()
  return personal_context


def _find_role(role_name):
  return db.session.query(Role).filter(Role.name == role_name).first()


@Resource.model_posted.connect_via(models.WorkflowPerson)
def handle_workflow_person_post(sender, obj=None, src=None, service=None):  # noqa pylint: disable=unused-argument
  db.session.flush()

  # add a user_roles mapping assigning the user creating the workflow
  # the WorkflowOwner role in the workflow's context.
  workflow_member_role = _find_role('WorkflowMember')
  user_role = UserRole(
      person=obj.person,
      role=workflow_member_role,
      context=obj.context,
      modified_by=get_current_user(),
  )
  db.session.add(user_role)


@Resource.model_posted.connect_via(models.Workflow)
def handle_workflow_post(sender, obj=None, src=None, service=None):  # noqa pylint: disable=unused-argument
  source_workflow = None

  if src.get('clone'):
    source_workflow_id = src.get('clone')
    source_workflow = models.Workflow.query.filter_by(
        id=source_workflow_id
    ).first()
    source_workflow.copy(obj)
    db.session.add(obj)
    db.session.flush()
    obj.title = source_workflow.title + ' (copy ' + str(obj.id) + ')'

  db.session.flush()
  # get the personal context for this logged in user
  user = get_current_user()
  personal_context = _get_or_create_personal_context(user)
  context = obj.build_object_context(
      context=personal_context,
      name='{object_type} Context {timestamp}'.format(
          object_type=service.model.__name__,
          timestamp=datetime.now()),
      description='',
  )
  context.modified_by = get_current_user()

  db.session.add(obj)
  db.session.flush()
  db.session.add(context)
  db.session.flush()
  obj.contexts.append(context)
  obj.context = context

  # add a user_roles mapping assigning the user creating the workflow
  # the WorkflowOwner role in the workflow's context.
  workflow_owner_role = _find_role('WorkflowOwner')
  user_role = UserRole(
      person=user,
      role=workflow_owner_role,
      context=context,
      modified_by=get_current_user(),
  )
  db.session.add(models.WorkflowPerson(
      person=user,
      workflow=obj,
      context=context,
      modified_by=get_current_user(),
  ))
  # pass along a temporary attribute for logging the events.
  user_role._display_related_title = obj.title
  db.session.add(user_role)
  db.session.flush()

  # Create the context implication for Workflow roles to default context
  db.session.add(ContextImplication(
      source_context=context,
      context=None,
      source_context_scope='Workflow',
      context_scope=None,
      modified_by=get_current_user(),
  ))

  if not src.get('private'):
    # Add role implication - all users can read a public workflow
    add_public_workflow_context_implication(context)

  if src.get('clone'):
    source_workflow.copy_task_groups(
        obj,
        clone_people=src.get('clone_people', False),
        clone_tasks=src.get('clone_tasks', False),
        clone_objects=src.get('clone_objects', False)
    )

    if src.get('clone_people'):
      workflow_member_role = _find_role('WorkflowMember')
      for authorization in source_workflow.context.user_roles:
        # Current user has already been added as workflow owner
        if authorization.person != user:
          db.session.add(UserRole(
              person=authorization.person,
              role=workflow_member_role,
              context=context,
              modified_by=user))
      for person in source_workflow.people:
        if person != user:
          db.session.add(models.WorkflowPerson(
              person=person,
              workflow=obj,
              context=context))


def add_public_workflow_context_implication(context, check_exists=False):
  if check_exists and db.session.query(ContextImplication).filter(
      and_(ContextImplication.context_id == context.id,
           ContextImplication.source_context_id == None)).count() > 0:  # noqa
    return
  db.session.add(ContextImplication(
      source_context=None,
      context=context,
      source_context_scope=None,
      context_scope='Workflow',
      modified_by=get_current_user(),
  ))


def init_extra_views(app):
  from . import views
  views.init_extra_views(app)


def start_recurring_cycles():
  # Get all workflows that should start a new cycle today
  # The next_cycle_start_date is precomputed and stored when a cycle is created
  today = date.today()
  workflows = db.session.query(models.Workflow)\
      .filter(
      models.Workflow.next_cycle_start_date == today,
      models.Workflow.recurrences == True  # noqa
  ).all()

  # For each workflow, start and save a new cycle.
  for workflow in workflows:
    cycle = models.Cycle()
    cycle.workflow = workflow
    cycle.calculator = workflow_cycle_calculator.get_cycle_calculator(workflow)
    cycle.context = workflow.context
    # We can do this because we selected only workflows with
    # next_cycle_start_date = today
    cycle.start_date = date.today()

    # Flag the cycle to be saved
    db.session.add(cycle)

    if workflow.non_adjusted_next_cycle_start_date:
      base_date = workflow.non_adjusted_next_cycle_start_date
    else:
      base_date = date.today()

    # Create the cycle (including all child objects)
    build_cycle(cycle, base_date=base_date)

    # Update the workflow next_cycle_start_date to push it ahead based on the
    # frequency.
    adjust_next_cycle_start_date(cycle.calculator, workflow, move_forward=True)

    db.session.add(workflow)

    notification.handle_workflow_modify(None, workflow)
    notification.handle_cycle_created(None, obj=cycle)

  log_event(db.session)
  db.session.commit()


def get_cycles(workflow):
  def is_valid_cycle(cycle):
    return ([ct for ct in cycle.cycle_task_group_object_tasks] and
            isinstance(cycle.start_date, (date, datetime)))
  return [c for c in workflow.cycles if is_valid_cycle(c)]


def adjust_next_cycle_start_date(
        calculator,
        workflow,
        base_date=None,
        move_forward=False):
  """Sets new cycle start date - it either recalculates a start date or moves
  it forward one interval if manual cycle start was requested or cycle
  was generated with start_recurring_cycles on next cycle start date.

  Args:
    calculator: Calculator that should be used for calculations
    workflow: Workflow that will have non adjusted and adjusted next cycle
              start date calculated.
    base_date: Date to be used for calculations
    move_forward: If true, NCSD will be calculated for next time unit,
                  otherwise it will recalculate on current time unit.
  """
  if not workflow.recurrences:
    return

  # If cycles were not generated already, recalculate start date with
  # fresh start.
  cycles = get_cycles(workflow)
  if not cycles:
    workflow.next_cycle_start_date = None
    workflow.non_adjusted_next_cycle_start_date = None
  else:
    # When all tasks got deleted we take last cycle start date as a base_date
    # from which to calculate
    if not workflow.non_adjusted_next_cycle_start_date:
      last_cycle_start_date = max([c.start_date for c in cycles])
      first_task = calculator.tasks[0]
      first_task_reified = calculator.relative_day_to_date(
          relative_day=first_task.relative_start_day,
          relative_month=first_task.relative_start_month,
          base_date=last_cycle_start_date
      )

      # In an edge case where reified first task happens before last cycle
      # start date, we should be calculating on the next time unit.
      if last_cycle_start_date >= first_task_reified:
        last_cycle_start_date = last_cycle_start_date + calculator.time_delta

      result = calculator.relative_day_to_date(
          relative_day=first_task.relative_start_day,
          relative_month=first_task.relative_start_month,
          base_date=last_cycle_start_date
      )
      if isinstance(result, datetime):
        result = result.date()
      workflow.non_adjusted_next_cycle_start_date = result

  # Unless we are moving forward one interval we just want to recalculate
  # the next_cycle_start_date to reflect the latest changes to the
  # task(s) - therefore, we just unwind one time unit backward and calculate
  # new next cycle start date.
  if not move_forward and workflow.non_adjusted_next_cycle_start_date:
    workflow.non_adjusted_next_cycle_start_date = (
        workflow.non_adjusted_next_cycle_start_date - calculator.time_delta)

  non_adjusted_ncsd = calculator.non_adjusted_next_cycle_start_date(
      base_date=workflow.non_adjusted_next_cycle_start_date)

  # In an edge case where we unwinded into the past for editing and
  # the next cycle start date returned back is less than or equal today,
  # we shouldn't have unwinded - therefore, we recalculate with
  # original value.
  if non_adjusted_ncsd <= date.today():
    workflow.non_adjusted_next_cycle_start_date = (
        workflow.non_adjusted_next_cycle_start_date + calculator.time_delta)
    non_adjusted_ncsd = calculator.non_adjusted_next_cycle_start_date(
        base_date=workflow.non_adjusted_next_cycle_start_date)

  workflow.non_adjusted_next_cycle_start_date = non_adjusted_ncsd
  workflow.next_cycle_start_date = calculator.adjust_date(non_adjusted_ncsd)


class WorkflowRoleContributions(RoleContributions):
  contributions = {
      'ProgramCreator': {
          'read': ['Workflow'],
          'create': ['Workflow'],
      },
      'Creator': {
          'create': ['Workflow', 'CycleTaskGroupObjectTask']
      },
      'Editor': {
          'read': ['Workflow', 'CycleTaskGroupObjectTask'],
          'create': ['Workflow', 'CycleTaskGroupObjectTask'],
          'update': ['CycleTaskGroupObjectTask'],
          'edit': ['CycleTaskGroupObjectTask'],
          'delete': ['CycleTaskGroupObjectTask']
      },
      'Reader': {
          'read': ['Workflow', 'CycleTaskGroupObjectTask'],
          'create': ['Workflow', 'CycleTaskGroupObjectTask'],
      },
      'ProgramEditor': {
          'read': ['Workflow'],
          'create': ['Workflow'],
      },
      'ProgramOwner': {
          'read': ['Workflow'],
          'create': ['Workflow'],
      },
  }


class WorkflowRoleDeclarations(RoleDeclarations):

  def roles(self):
    return {
        'WorkflowOwner': WorkflowOwner,
        'WorkflowMember': WorkflowMember,
        'BasicWorkflowReader': BasicWorkflowReader,
        'WorkflowBasicReader': WorkflowBasicReader,
    }


class WorkflowRoleImplications(DeclarativeRoleImplications):
  # (Source Context Type, Context Type)
  #   -> Source Role -> Implied Role for Context
  implications = {
      (None, 'Workflow'): {
          'ProgramCreator': ['BasicWorkflowReader'],
          'Editor': ['WorkflowOwner'],
          'Reader': ['BasicWorkflowReader'],
          'Creator': ['WorkflowBasicReader'],
      },
      ('Workflow', None): {
          'WorkflowOwner': ['WorkflowBasicReader'],
          'WorkflowMember': ['WorkflowBasicReader'],
      },
  }

ROLE_CONTRIBUTIONS = WorkflowRoleContributions()
ROLE_DECLARATIONS = WorkflowRoleDeclarations()
ROLE_IMPLICATIONS = WorkflowRoleImplications()

contributed_notifications = notification.contributed_notifications
contributed_importables = IMPORTABLE
contributed_exportables = EXPORTABLE
contributed_column_handlers = COLUMN_HANDLERS
contributed_get_ids_related_to = relationship_helper.get_ids_related_to
CONTRIBUTED_CRON_JOBS = [start_recurring_cycles]
NOTIFICATION_LISTENERS = [notification.register_listeners]
MAPPING_VALIDATION_WHITELIST = [utils.get_mapping_validation_rules()]
