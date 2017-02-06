# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import orm

from ggrc import db
from ggrc.models.deferred import deferred
from ggrc.models.mixins import Base
from ggrc.models.mixins import Timeboxed
from ggrc.models.reflection import PublishOnly


class ObjectPerson(Timeboxed, Base, db.Model):
  __tablename__ = 'object_people'

  role = deferred(db.Column(db.String), 'ObjectPerson')
  notes = deferred(db.Column(db.Text), 'ObjectPerson')
  person_id = db.Column(db.Integer, db.ForeignKey('people.id'), nullable=False)
  personable_id = db.Column(db.Integer, nullable=False)
  personable_type = db.Column(db.String, nullable=False)

  @property
  def personable_attr(self):
    return '{0}_personable'.format(self.personable_type)

  @property
  def personable(self):
    return getattr(self, self.personable_attr)

  @personable.setter
  def personable(self, value):
    self.personable_id = value.id if value is not None else None
    self.personable_type = value.__class__.__name__ if value is not None \
        else None
    return setattr(self, self.personable_attr, value)

  @staticmethod
  def _extra_table_args(cls):
    return (
        db.UniqueConstraint('person_id', 'personable_id', 'personable_type'),
        db.Index('ix_person_id', 'person_id'),
    )

  _publish_attrs = [
      'role',
      'notes',
      'person',
      'personable',
  ]
  _sanitize_html = [
      'notes',
  ]

  @classmethod
  def eager_query(cls):
    from sqlalchemy import orm

    query = super(ObjectPerson, cls).eager_query()
    return query.options(
        orm.subqueryload('person'))

  def _display_name(self):
    return self.personable.display_name + '<->' + self.person.display_name


class Personable(object):

  @declared_attr
  def object_people(cls):
    cls.people = association_proxy(
        'object_people', 'person',
        creator=lambda person: ObjectPerson(
            person=person,
            personable_type=cls.__name__,
        )
    )
    joinstr = 'and_(foreign(ObjectPerson.personable_id) == {type}.id, '\
        'foreign(ObjectPerson.personable_type) == "{type}")'
    joinstr = joinstr.format(type=cls.__name__)
    return db.relationship(
        'ObjectPerson',
        primaryjoin=joinstr,
        backref='{0}_personable'.format(cls.__name__),
        cascade='all, delete-orphan',
    )

  _publish_attrs = [
      PublishOnly('people'),
      'object_people',
  ]
  _include_links = []

  @classmethod
  def eager_query(cls):
    query = super(Personable, cls).eager_query()
    return cls.eager_inclusions(query, Personable._include_links).options(
        orm.subqueryload('object_people'))
