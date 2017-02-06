# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

from ggrc import db
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declared_attr
from ggrc.models.mixins import Base
from ggrc.models.reflection import PublishOnly


class AuditObject(Base, db.Model):
  __tablename__ = 'audit_objects'

  audit_id = db.Column(
      db.Integer, db.ForeignKey('audits.id'), nullable=False)
  auditable_id = db.Column(db.Integer, nullable=False)
  auditable_type = db.Column(db.String, nullable=False)

  @property
  def auditable_attr(self):
    return '{0}_auditable'.format(self.auditable_type)

  @property
  def auditable(self):
    return getattr(self, self.auditable_attr)

  @auditable.setter
  def auditable(self, value):
    self.auditable_id = value.id if value is not None else None
    self.auditable_type = value.__class__.__name__ if value is not None \
        else None
    return setattr(self, self.auditable_attr, value)

  @staticmethod
  def _extra_table_args(cls):
    return (
        db.UniqueConstraint(
            'audit_id', 'auditable_id', 'auditable_type'),
        db.Index('ix_audit_id', 'audit_id'),
    )

  _publish_attrs = [
      'audit',
      'auditable',
  ]

  @classmethod
  def eager_query(cls):
    from sqlalchemy import orm

    query = super(AuditObject, cls).eager_query()
    return query.options(
        orm.subqueryload('audit'))

  def _display_name(self):
    return '{} <-> {} {}'.format(str(self.audit.display_name),
                                 str(self.auditable_type),
                                 str(self.auditable_id))


class Auditable(object):

  @declared_attr
  def audit_objects(cls):
    cls.audits = association_proxy(
        'audit_objects', 'audit',
        creator=lambda control: AuditObject(
            audit=audit,  # noqa
            auditable_type=cls.__name__,
        )
    )
    joinstr = 'and_(foreign(AuditObject.auditable_id) == {type}.id, '\
        'foreign(AuditObject.auditable_type) == "{type}")'
    joinstr = joinstr.format(type=cls.__name__)
    return db.relationship(
        'AuditObject',
        primaryjoin=joinstr,
        backref='{0}_auditable'.format(cls.__name__),
        cascade='all, delete-orphan',
    )

  _publish_attrs = [
      PublishOnly('audits'),
      'audit_objects',
  ]
  _include_links = []

  @classmethod
  def eager_query(cls):
    from sqlalchemy import orm

    query = super(Auditable, cls).eager_query()
    return cls.eager_inclusions(query, Auditable._include_links).options(
        orm.subqueryload('audit_objects'))
