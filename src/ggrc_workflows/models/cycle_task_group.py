# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Module for cycle task group model.
"""

from sqlalchemy import orm

from ggrc import db
from ggrc.models.mixins import Described
from ggrc.models.mixins import Slugged
from ggrc.models.mixins import Stateful
from ggrc.models.mixins import Timeboxed
from ggrc.models.mixins import Titled
from ggrc.models.mixins import WithContact
from ggrc_workflows.models.cycle import Cycle


class CycleTaskGroup(WithContact, Stateful, Timeboxed, Described,
                     Titled, Slugged, db.Model):
  """Cycle Task Group model.
  """
  __tablename__ = 'cycle_task_groups'
  _title_uniqueness = False

  @classmethod
  def generate_slug_prefix_for(cls, obj):
    return "CYCLEGROUP"

  VALID_STATES = (
      u'Assigned', u'InProgress', u'Finished', u'Verified', u'Declined')

  cycle_id = db.Column(
      db.Integer,
      db.ForeignKey('cycles.id', ondelete="CASCADE"),
      nullable=False,
  )
  task_group_id = db.Column(
      db.Integer, db.ForeignKey('task_groups.id'), nullable=True)
  cycle_task_group_tasks = db.relationship(
      'CycleTaskGroupObjectTask',
      backref='cycle_task_group',
      cascade='all, delete-orphan'
  )
  sort_index = db.Column(
      db.String(length=250), default="", nullable=False)
  next_due_date = db.Column(db.Date)

  _publish_attrs = [
      'cycle',
      'task_group',
      'cycle_task_group_tasks',
      'sort_index',
      'next_due_date'
  ]

  _aliases = {
      "cycle": {
          "display_name": "Cycle",
          "filter_by": "_filter_by_cycle",
      },
  }

  @classmethod
  def _filter_by_cycle(cls, predicate):
    """Get query that filters cycle task groups.

    Args:
      predicate: lambda function that excepts a single parameter and returns
      true of false.

    Returns:
      An sqlalchemy query that evaluates to true or false and can be used in
      filtering cycle task groups by related cycle.
    """
    return Cycle.query.filter(
        (Cycle.id == cls.cycle_id) &
        (predicate(Cycle.slug) | predicate(Cycle.title))
    ).exists()

  @classmethod
  def eager_query(cls):
    """Add cycle tasks and objects to cycle task group eager query.

    Make sure we load all cycle task group relevant data in a single query.

    Returns:
      a query object with cycle_task_group_tasks added to joined load options.
    """
    query = super(CycleTaskGroup, cls).eager_query()
    return query.options(
        orm.joinedload('cycle_task_group_tasks')
    )
