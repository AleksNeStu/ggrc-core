# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Module for control model and related classes."""

from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import validates

from ggrc import db
from ggrc.models.audit_object import Auditable
from ggrc.models.categorization import Categorizable
from ggrc.models.category import CategoryBase
from ggrc.models.mixins import BusinessObject
from ggrc.models.mixins import CustomAttributable
from ggrc.models.mixins import Hierarchical
from ggrc.models.mixins import TestPlanned
from ggrc.models.mixins import Timeboxed
from ggrc.models.deferred import deferred
from ggrc.models.object_owner import Ownable
from ggrc.models.object_person import Personable
from ggrc.models.option import Option
from ggrc.models.person import Person
from ggrc.models.reflection import PublishOnly
from ggrc.models.relationship import Relatable
from ggrc.models.track_object_state import HasObjectState
from ggrc.models.utils import validate_option


class ControlCategory(CategoryBase):
  __mapper_args__ = {
      'polymorphic_identity': 'ControlCategory'
  }
  _table_plural = 'control_categories'


class ControlAssertion(CategoryBase):
  __mapper_args__ = {
      'polymorphic_identity': 'ControlAssertion'
  }
  _table_plural = 'control_assertions'


class ControlCategorized(Categorizable):

  @declared_attr
  def categorizations(cls):
    return cls.declare_categorizable(
        "ControlCategory", "category", "categories", "categorizations")

  _publish_attrs = [
      'categories',
      PublishOnly('categorizations'),
  ]

  _include_links = []

  _aliases = {
      "categories": {
          "display_name": "Categories",
          "filter_by": "_filter_by_categories",
      },
  }

  @classmethod
  def _filter_by_categories(cls, predicate):
    return cls._filter_by_category("ControlCategory", predicate)

  @classmethod
  def eager_query(cls):
    from sqlalchemy import orm
    query = super(ControlCategorized, cls).eager_query()
    return query.options(
        orm.subqueryload('categorizations').joinedload('category'),
    )


class AssertionCategorized(Categorizable):

  @declared_attr
  def categorized_assertions(cls):
    return cls.declare_categorizable(
        "ControlAssertion", "assertion", "assertions",
        "categorized_assertions")

  _publish_attrs = [
      'assertions',
      PublishOnly('categorized_assertions'),
  ]
  _include_links = []
  _aliases = {
      "assertions": {
          "display_name": "Assertions",
          "filter_by": "_filter_by_assertions",
      },
  }

  @classmethod
  def _filter_by_assertions(cls, predicate):
    return cls._filter_by_category("ControlAssertion", predicate)

  @classmethod
  def eager_query(cls):
    from sqlalchemy import orm
    query = super(AssertionCategorized, cls).eager_query()
    return query.options(
        orm.subqueryload('categorized_assertions').joinedload('category'),
    )


class Control(HasObjectState, Relatable, CustomAttributable,
              Personable, ControlCategorized, AssertionCategorized,
              Hierarchical, Timeboxed, Ownable, Auditable,
              TestPlanned, BusinessObject, db.Model):
  __tablename__ = 'controls'

  company_control = deferred(db.Column(db.Boolean), 'Control')
  directive_id = deferred(
      db.Column(db.Integer, db.ForeignKey('directives.id')), 'Control')
  kind_id = deferred(db.Column(db.Integer), 'Control')
  means_id = deferred(db.Column(db.Integer), 'Control')
  version = deferred(db.Column(db.String), 'Control')
  documentation_description = deferred(db.Column(db.Text), 'Control')
  verify_frequency_id = deferred(db.Column(db.Integer), 'Control')
  fraud_related = deferred(db.Column(db.Boolean), 'Control')
  key_control = deferred(db.Column(db.Boolean), 'Control')
  active = deferred(db.Column(db.Boolean), 'Control')
  principal_assessor_id = deferred(
      db.Column(db.Integer, db.ForeignKey('people.id')), 'Control')
  secondary_assessor_id = deferred(
      db.Column(db.Integer, db.ForeignKey('people.id')), 'Control')

  principal_assessor = db.relationship(
      'Person', uselist=False, foreign_keys='Control.principal_assessor_id')
  secondary_assessor = db.relationship(
      'Person', uselist=False, foreign_keys='Control.secondary_assessor_id')

  kind = db.relationship(
      'Option',
      primaryjoin='and_(foreign(Control.kind_id) == Option.id, '
                  'Option.role == "control_kind")',
      uselist=False)
  means = db.relationship(
      'Option',
      primaryjoin='and_(foreign(Control.means_id) == Option.id, '
                  'Option.role == "control_means")',
      uselist=False)
  verify_frequency = db.relationship(
      'Option',
      primaryjoin='and_(foreign(Control.verify_frequency_id) == Option.id, '
                  'Option.role == "verify_frequency")',
      uselist=False)

  @staticmethod
  def _extra_table_args(_):
    return (
        db.Index('ix_controls_principal_assessor', 'principal_assessor_id'),
        db.Index('ix_controls_secondary_assessor', 'secondary_assessor_id'),
    )

  # REST properties
  _publish_attrs = [
      'active',
      'company_control',
      'directive',
      'documentation_description',
      'fraud_related',
      'key_control',
      'kind',
      'means',
      'verify_frequency',
      'version',
      'principal_assessor',
      'secondary_assessor',
  ]

  _sanitize_html = [
      'documentation_description',
      'version',
  ]

  _include_links = []

  _aliases = {
      "url": "Control URL",
      "kind": {
          "display_name": "Kind/Nature",
          "filter_by": "_filter_by_kind",
      },
      "means": {
          "display_name": "Type/Means",
          "filter_by": "_filter_by_means",
      },
      "verify_frequency": {
          "display_name": "Frequency",
          "filter_by": "_filter_by_verify_frequency",
      },
      "fraud_related": "Fraud Related",
      "principal_assessor": {
          "display_name": "Principal Assessor",
          "filter_by": "_filter_by_principal_assessor",
      },
      "secondary_assessor": {
          "display_name": "Secondary Assessor",
          "filter_by": "_filter_by_secondary_assessor",
      },
      "key_control": {
          "display_name": "Significance",
          "description": "Allowed values are:\nkey\nnon-key\n---",
      }
  }

  @validates('kind', 'means', 'verify_frequency')
  def validate_control_options(self, key, option):
    desired_role = key if key == 'verify_frequency' else 'control_' + key
    return validate_option(self.__class__.__name__, key, option, desired_role)

  @classmethod
  def _filter_by_kind(cls, predicate):
    return Option.query.filter(
        (Option.id == cls.kind_id) & predicate(Option.title)
    ).exists()

  @classmethod
  def _filter_by_means(cls, predicate):
    return Option.query.filter(
        (Option.id == cls.means_id) & predicate(Option.title)
    ).exists()

  @classmethod
  def _filter_by_principal_assessor(cls, predicate):
    return Person.query.filter(
        (Person.id == cls.principal_assessor_id) &
        (predicate(Person.name) | predicate(Person.email))
    ).exists()

  @classmethod
  def _filter_by_secondary_assessor(cls, predicate):
    return Person.query.filter(
        (Person.id == cls.secondary_assessor_id) &
        (predicate(Person.name) | predicate(Person.email))
    ).exists()

  @classmethod
  def _filter_by_verify_frequency(cls, predicate):
    return Option.query.filter(
        (Option.id == cls.verify_frequency_id) & predicate(Option.title)
    ).exists()

  @classmethod
  def eager_query(cls):
    from sqlalchemy import orm
    query = super(Control, cls).eager_query()
    return cls.eager_inclusions(query, Control._include_links).options(
        orm.joinedload('directive'),
        orm.joinedload('principal_assessor'),
        orm.joinedload('secondary_assessor'),
    )

  def log_json(self):
    out_json = super(Control, self).log_json()
    # so that event log can refer to deleted directive
    if self.directive:
      out_json["mapped_directive"] = self.directive.display_name
    return out_json
