# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Module containing Cycle tasks.
"""

from sqlalchemy import orm
from sqlalchemy.ext.associationproxy import association_proxy

from ggrc import db
from ggrc.models.computed_property import computed_property
from ggrc.models.mixins import Described
from ggrc.models.mixins import Notifiable
from ggrc.models.mixins import Slugged
from ggrc.models.mixins import Stateful
from ggrc.models.mixins import Timeboxed
from ggrc.models.mixins import Titled
from ggrc.models.mixins import WithContact
from ggrc.models.reflection import PublishOnly
from ggrc.models.relationship import Relatable
from ggrc.models.types import JsonType
from ggrc_workflows.models.cycle import Cycle
from ggrc_workflows.models.cycle_task_group import CycleTaskGroup


class CycleTaskGroupObjectTask(
        WithContact, Stateful, Timeboxed, Relatable, Notifiable,
        Described, Titled, Slugged, db.Model):
  """Cycle task model
  """
  __tablename__ = 'cycle_task_group_object_tasks'
  _title_uniqueness = False

  IMPORTABLE_FIELDS = ('slug', 'title', 'description', 'start_date',
                       'end_date', 'finished_date', 'verified_date')

  @classmethod
  def generate_slug_prefix_for(cls, obj):
    return "CYCLETASK"

  VALID_STATES = (None, 'InProgress', 'Assigned',
                  'Finished', 'Declined', 'Verified')

  # Note: this statuses are used in utils/query_helpers to filter out the tasks
  # that should be visible on My Tasks pages.
  ACTIVE_STATES = ("Assigned", "InProgress", "Finished", "Declined")

  cycle_id = db.Column(
      db.Integer,
      db.ForeignKey('cycles.id', ondelete="CASCADE"),
      nullable=False,
  )
  cycle_task_group_id = db.Column(
      db.Integer,
      db.ForeignKey('cycle_task_groups.id', ondelete="CASCADE"),
      nullable=False,
  )
  task_group_task_id = db.Column(
      db.Integer, db.ForeignKey('task_group_tasks.id'), nullable=True)
  task_group_task = db.relationship(
      "TaskGroupTask",
      foreign_keys="CycleTaskGroupObjectTask.task_group_task_id"
  )
  task_type = db.Column(
      db.String(length=250), nullable=False)
  response_options = db.Column(
      JsonType(), nullable=False, default=[])
  selected_response_options = db.Column(
      JsonType(), nullable=False, default=[])

  sort_index = db.Column(
      db.String(length=250), default="", nullable=False)

  finished_date = db.Column(db.DateTime)
  verified_date = db.Column(db.DateTime)

  object_approval = association_proxy('cycle', 'workflow.object_approval')
  object_approval.publish_raw = True

  @property
  def cycle_task_objects_for_cache(self):
    """Changing task state must invalidate `workflow_state` on objects
    """
    return [(object_.__class__.__name__, object_.id) for object_ in
            self.related_objects]  # pylint: disable=not-an-iterable

  _publish_attrs = [
      'cycle',
      'cycle_task_group',
      'task_group_task',
      'cycle_task_entries',
      'sort_index',
      'task_type',
      'response_options',
      'selected_response_options',
      PublishOnly('object_approval'),
      PublishOnly('finished_date'),
      PublishOnly('verified_date')
  ]

  default_description = "<ol>"\
                        + "<li>Expand the object review task.</li>"\
                        + "<li>Click on the Object to be reviewed.</li>"\
                        + "<li>Review the object in the Info tab.</li>"\
                        + "<li>Click \"Approve\" to approve the object.</li>"\
                        + "<li>Click \"Decline\" to decline the object.</li>"\
                        + "</ol>"

  _aliases = {
      "title": "Summary",
      "description": "Task Details",
      "contact": {
          "display_name": "Assignee",
          "mandatory": True,
          "filter_by": "_filter_by_contact",
      },
      "secondary_contact": None,
      "start_date": "Start Date",
      "end_date": "End Date",
      "finished_date": "Actual Finish Date",
      "verified_date": "Actual Verified Date",
      "cycle": {
          "display_name": "Cycle",
          "filter_by": "_filter_by_cycle",
      },
      "cycle_task_group": {
          "display_name": "Task Group",
          "mandatory": True,
          "filter_by": "_filter_by_cycle_task_group",
      },
      "task_type": {
          "display_name": "Task Type",
          "mandatory": True,
      },
  }

  @computed_property
  def related_objects(self):
    """Compute and return a list of all the objects related to this cycle task.

    Related objects are those that are found either on the "source" side, or
    on the "destination" side of any of the instance's relations.

    Returns:
      (list) All objects related to the instance.
    """
    # pylint: disable=not-an-iterable
    sources = [r.source for r in self.related_sources]
    destinations = [r.destination for r in self.related_destinations]
    return sources + destinations

  @classmethod
  def _filter_by_cycle(cls, predicate):
    """Get query that filters cycle tasks by related cycles.

    Args:
      predicate: lambda function that excepts a single parameter and returns
      true of false.

    Returns:
      An sqlalchemy query that evaluates to true or false and can be used in
      filtering cycle tasks by related cycles.
    """
    return Cycle.query.filter(
        (Cycle.id == cls.cycle_id) &
        (predicate(Cycle.slug) | predicate(Cycle.title))
    ).exists()

  @classmethod
  def _filter_by_cycle_task_group(cls, predicate):
    """Get query that filters cycle tasks by related cycle task groups.

    Args:
      predicate: lambda function that excepts a single parameter and returns
      true of false.

    Returns:
      An sqlalchemy query that evaluates to true or false and can be used in
      filtering cycle tasks by related cycle task groups.
    """
    return CycleTaskGroup.query.filter(
        (CycleTaskGroup.id == cls.cycle_id) &
        (predicate(CycleTaskGroup.slug) | predicate(CycleTaskGroup.title))
    ).exists()

  @classmethod
  def eager_query(cls):
    """Add cycle task entries to cycle task eager query

    This function adds cycle_task_entries as a join option when fetching cycles
    tasks, and makes sure that with one query we fetch all cycle task related
    data needed for generating cycle taks json for a response.

    Returns:
      a query object with cycle_task_entries added to joined load options.
    """
    query = super(CycleTaskGroupObjectTask, cls).eager_query()
    return query.options(
        orm.joinedload('cycle')
           .joinedload('workflow')
           .undefer_group('Workflow_complete'),
        orm.joinedload('cycle_task_entries'),
    )


class CycleTaskable(object):
  """ Requires the Relatable mixin, otherwise cycle_task_group_object_tasks
  fails to fetch related objects
  """
  @computed_property
  def cycle_task_group_object_tasks(self):
    """ Lists all the cycle tasks related to a certain object
    """
    sources = [r.CycleTaskGroupObjectTask_source
               for r in self.related_sources
               if r.CycleTaskGroupObjectTask_source is not None]
    destinations = [r.CycleTaskGroupObjectTask_destination
                    for r in self.related_destinations
                    if r.CycleTaskGroupObjectTask_destination is not None]
    return sources + destinations

  @classmethod
  def eager_query(cls):
    query = super(CycleTaskable, cls).eager_query()
    return query.options(
        orm.subqueryload('related_sources')
           .joinedload('CycleTaskGroupObjectTask_source')
           .undefer_group('CycleTaskGroupObjectTask_complete')
           .joinedload('cycle'),
        orm.subqueryload('related_destinations')
           .joinedload('CycleTaskGroupObjectTask_destination')
           .undefer_group('CycleTaskGroupObjectTask_complete')
           .joinedload('cycle')
    )
