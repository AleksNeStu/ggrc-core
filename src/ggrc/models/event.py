# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

from ggrc import db
from ggrc.models.mixins import Base


class Event(Base, db.Model):
  __tablename__ = 'events'

  action = db.Column(
      db.Enum(u'POST', u'PUT', u'DELETE', u'BULK', u'GET'),
      nullable=False,
  )
  resource_id = db.Column(db.Integer)
  resource_type = db.Column(db.String)

  revisions = db.relationship(
      'Revision',
      backref='event',
      cascade='all, delete-orphan',
  )

  _publish_attrs = [
      'action',
      'resource_id',
      'resource_type',
      'revisions',
  ]

  _include_links = [
      'revisions',
  ]

  @staticmethod
  def _extra_table_args(class_):
    return (
        db.Index('events_modified_by', 'modified_by_id'),
    )

  @classmethod
  def eager_query(cls):
    from sqlalchemy import orm

    query = super(Event, cls).eager_query()
    return query.options(
        orm.subqueryload('revisions').undefer_group('Revision_complete'),
    )
