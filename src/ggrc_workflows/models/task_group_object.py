# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""A module containing the workflow TaskGroupObject model."""


from sqlalchemy.ext.associationproxy import association_proxy

from ggrc import db
from ggrc.models.mixins import Base
from ggrc.models.mixins import Timeboxed
from ggrc.models.reflection import PublishOnly


class TaskGroupObject(Timeboxed, Base, db.Model):
  """Workflow TaskGroupObject model."""

  __tablename__ = 'task_group_objects'

  task_group_id = db.Column(
      db.Integer,
      db.ForeignKey('task_groups.id', ondelete="CASCADE"),
      nullable=False,
  )
  object_id = db.Column(db.Integer, nullable=False)
  object_type = db.Column(db.String, nullable=False)

  @property
  def object_attr(self):
    return '{0}_object'.format(self.object_type)

  @property
  def object(self):
    return getattr(self, self.object_attr)

  @object.setter
  def object(self, value):
    self.object_id = value.id if value is not None else None
    self.object_type = value.__class__.__name__ if value is not None \
        else None
    return setattr(self, self.object_attr, value)

  @staticmethod
  def _extra_table_args(klass):
    # pylint: disable=unused-argument
    return (
        db.UniqueConstraint('task_group_id', 'object_id', 'object_type'),
        db.Index('ix_task_group_id', 'task_group_id'),
    )

  _publish_attrs = [
      'task_group',
      'object',
  ]
  _sanitize_html = []

  @classmethod
  def eager_query(cls):
    from sqlalchemy import orm

    query = super(TaskGroupObject, cls).eager_query()
    return query.options(
        orm.subqueryload('task_group'))

  def _display_name(self):
    return self.object.display_name + '<->' + self.task_group.display_name

  def copy(self, _other=None, **kwargs):
    columns = [
        'task_group', 'object_id', 'object_type'
    ]
    target = self.copy_into(_other, columns, **kwargs)
    return target


class TaskGroupable(object):
  @classmethod
  def late_init_task_groupable(cls):
    def make_task_group_objects(cls):
      cls.task_groups = association_proxy(
          'task_group_objects', 'task_group',
          creator=lambda task_group: TaskGroupObject(
              task_group=task_group,
              object_type=cls.__name__,
          )
      )
      joinstr = 'and_(foreign(TaskGroupObject.object_id) == {type}.id, '\
                'foreign(TaskGroupObject.object_type) == "{type}")'
      joinstr = joinstr.format(type=cls.__name__)
      return db.relationship(
          'TaskGroupObject',
          primaryjoin=joinstr,
          backref='{0}_object'.format(cls.__name__),
          cascade='all, delete-orphan',
      )
    cls.task_group_objects = make_task_group_objects(cls)

  _publish_attrs = [
      PublishOnly('task_groups'),
      'task_group_objects',
  ]

  _include_links = []

  @classmethod
  def eager_query(cls):
    from sqlalchemy import orm

    query = super(TaskGroupable, cls).eager_query()
    return cls.eager_inclusions(query, TaskGroupable._include_links).options(
        orm.subqueryload('task_group_objects'))
