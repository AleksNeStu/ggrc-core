# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

from ggrc import db
from ggrc.models.deferred import deferred
from ggrc.models.mixins import BusinessObject, Timeboxed, CustomAttributable
from .object_person import Personable
from .object_owner import Ownable
from .relationship import Relatable
from .utils import validate_option

from sqlalchemy.orm import validates
from .track_object_state import HasObjectState


class Directive(HasObjectState, Timeboxed, BusinessObject, db.Model):
  __tablename__ = 'directives'

  version = deferred(db.Column(db.String), 'Directive')
  organization = deferred(db.Column(db.String), 'Directive')
  scope = deferred(db.Column(db.Text), 'Directive')
  kind_id = deferred(db.Column(db.Integer), 'Directive')
  audit_start_date = deferred(db.Column(db.DateTime), 'Directive')
  audit_frequency_id = deferred(db.Column(db.Integer), 'Directive')
  audit_duration_id = deferred(db.Column(db.Integer), 'Directive')
  meta_kind = db.Column(db.String)
  kind = deferred(db.Column(db.String), 'Directive')

  # TODO: FIX jost!
  # sections = db.relationship(
  #     'Section', backref='directive',
  #     order_by='Section.slug', cascade='all, delete-orphan')
  controls = db.relationship(
      'Control', backref='directive', order_by='Control.slug')
  audit_frequency = db.relationship(
      'Option',
      primaryjoin='and_(foreign(Directive.audit_frequency_id) == Option.id, '
                  'Option.role == "audit_frequency")',
      uselist=False,
  )
  audit_duration = db.relationship(
      'Option',
      primaryjoin='and_(foreign(Directive.audit_duration_id) == Option.id, '
                  'Option.role == "audit_duration")',
      uselist=False,
  )

  __mapper_args__ = {
      'polymorphic_on': meta_kind
  }

  _publish_attrs = [
      'audit_start_date',
      'audit_frequency',
      'audit_duration',
      'controls',
      'kind',
      'organization',
      'scope',
      'version',
  ]

  _sanitize_html = [
      'organization',
      'scope',
      'version',
  ]

  _include_links = []

  _aliases = {'directive_kind': "Kind/Type", }

  @validates('kind')
  def validate_kind(self, key, value):
    if not value:
      return None
    if value not in self.VALID_KINDS:
      message = "Invalid value '{}' for attribute {}.{}.".format(
                value, self.__class__.__name__, key)
      raise ValueError(message)
    return value

  @validates('audit_duration', 'audit_frequency')
  def validate_directive_options(self, key, option):
    return validate_option(self.__class__.__name__, key, option, key)

  @classmethod
  def eager_query(cls):
    from sqlalchemy import orm

    query = super(Directive, cls).eager_query()
    return cls.eager_inclusions(query, Directive._include_links).options(
        orm.joinedload('audit_frequency'),
        orm.joinedload('audit_duration'),
        orm.subqueryload('controls'))

  @staticmethod
  def _extra_table_args(cls):
    return (
        db.Index('ix_{}_meta_kind'.format(cls.__tablename__), 'meta_kind'),
    )


# FIXME: For subclasses, restrict kind
class Policy(CustomAttributable, Relatable,
             Personable, Ownable, Directive):
  __mapper_args__ = {
      'polymorphic_identity': 'Policy'
  }

  _table_plural = 'policies'

  VALID_KINDS = frozenset([
      "Company Policy", "Org Group Policy", "Data Asset Policy",
      "Product Policy", "Contract-Related Policy", "Company Controls Policy"
  ])

  _aliases = {"url": "Policy URL"}

  @validates('meta_kind')
  def validates_meta_kind(self, key, value):
    return 'Policy'


class Regulation(CustomAttributable, Relatable,
                 Personable, Ownable, Directive):
  __mapper_args__ = {
      'polymorphic_identity': 'Regulation'
  }

  _table_plural = 'regulations'

  VALID_KINDS = ("Regulation",)

  _aliases = {
      "url": "Regulation URL",
      "directive_kind": None,
  }

  @validates('meta_kind')
  def validates_meta_kind(self, key, value):
    return 'Regulation'


class Standard(CustomAttributable, Relatable,
               Personable, Ownable, Directive):
  __mapper_args__ = {
      'polymorphic_identity': 'Standard'
  }

  _table_plural = 'standards'

  VALID_KINDS = ("Standard",)

  _aliases = {
      "url": "Standard URL",
      "directive_kind": None,
  }

  @validates('meta_kind')
  def validates_meta_kind(self, key, value):
    return 'Standard'


class Contract(CustomAttributable, Relatable,
               Personable, Ownable, Directive):
  __mapper_args__ = {
      'polymorphic_identity': 'Contract'
  }

  _table_plural = 'contracts'

  VALID_KINDS = ("Contract",)

  _aliases = {
      "url": "Contract URL",
      "directive_kind": None,
  }

  @validates('meta_kind')
  def validates_meta_kind(self, key, value):
    return 'Contract'
