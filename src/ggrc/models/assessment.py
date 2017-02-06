# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Module for Assessment object"""

from sqlalchemy import and_
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import remote
from sqlalchemy.orm import validates

from ggrc import db
from ggrc.models import reflection
from ggrc.models.audit import Audit
from ggrc.models.comment import Commentable
from ggrc.models.custom_attribute_definition import CustomAttributeDefinition
from ggrc.models.mixins import BusinessObject
from ggrc.models.mixins import CustomAttributable
from ggrc.models.mixins import FinishedDate
from ggrc.models.mixins import Notifiable
from ggrc.models.mixins import TestPlanned
from ggrc.models.mixins import Timeboxed
from ggrc.models.mixins import VerifiedDate
from ggrc.models.mixins import reminderable
from ggrc.models.mixins import statusable
from ggrc.models.mixins.assignable import Assignable
from ggrc.models.mixins.autostatuschangeable import AutoStatusChangeable
from ggrc.models.mixins.validate_on_complete import ValidateOnComplete
from ggrc.models.mixins.with_similarity_score import WithSimilarityScore
from ggrc.models.deferred import deferred
from ggrc.models.object_document import EvidenceURL
from ggrc.models.object_person import Personable
from ggrc.models.reflection import PublishOnly
from ggrc.models.relationship import Relatable
from ggrc.models.relationship import Relationship
from ggrc.models.track_object_state import HasObjectState


class AuditRelationship(object):

  """Mixin for mandatory link to an Audit via Relationships."""

  _aliases = {
      "audit": {
          "display_name": "Audit",
          "mandatory": True,
          "filter_by": "_filter_by_audit",
          "ignore_on_update": True,
          "type": reflection.AttributeInfo.Type.MAPPING,
      },
  }

  @classmethod
  def _filter_by_audit(cls, predicate):
    """Get filter for objects related to an Audit."""
    return Relationship.query.filter(
        Relationship.source_type == cls.__name__,
        Relationship.source_id == cls.id,
        Relationship.destination_type == Audit.__name__,
    ).join(Audit, Relationship.destination_id == Audit.id).filter(
        predicate(Audit.slug)
    ).exists() | Relationship.query.filter(
        Relationship.destination_type == cls.__name__,
        Relationship.destination_id == cls.id,
        Relationship.source_type == Audit.__name__,
    ).join(Audit, Relationship.source_id == Audit.id).filter(
        predicate(Audit.slug)
    ).exists()


class Assessment(statusable.Statusable, AuditRelationship,
                 AutoStatusChangeable, Assignable, HasObjectState, TestPlanned,
                 CustomAttributable, EvidenceURL, Commentable, Personable,
                 reminderable.Reminderable, Timeboxed, Relatable,
                 WithSimilarityScore, FinishedDate, VerifiedDate,
                 ValidateOnComplete, Notifiable, BusinessObject, db.Model):
  """Class representing Assessment.

  Assessment is an object representing an individual assessment performed on
  a specific object during an audit to ascertain whether or not
  certain conditions were met for that object.
  """

  __tablename__ = 'assessments'
  _title_uniqueness = False

  ASSIGNEE_TYPES = (u"Creator", u"Assessor", u"Verifier")

  REMINDERABLE_HANDLERS = {
      "statusToPerson": {
          "handler":
              reminderable.Reminderable.handle_state_to_person_reminder,
          "data": {
              statusable.Statusable.START_STATE: "Assessor",
              "In Progress": "Assessor"
          },
          "reminders": {"assessment_assessor_reminder", }
      }
  }

  design = deferred(db.Column(db.String), "Assessment")
  operationally = deferred(db.Column(db.String), "Assessment")

  @declared_attr
  def object_level_definitions(self):
    """Set up a backref so that we can create an object level custom
       attribute definition without the need to do a flush to get the
       assessment id.

      This is used in the relate_ca method in hooks/assessment.py.
    """
    return db.relationship(
        'CustomAttributeDefinition',
        primaryjoin=lambda: and_(
            remote(CustomAttributeDefinition.definition_id) == Assessment.id,
            remote(CustomAttributeDefinition.definition_type) == "assessment"),
        foreign_keys=[
            CustomAttributeDefinition.definition_id,
            CustomAttributeDefinition.definition_type
        ],
        backref='assessment_definition',
        cascade='all, delete-orphan')

  object = {}  # we add this for the sake of client side error checking
  audit = {}

  VALID_CONCLUSIONS = frozenset([
      "Effective",
      "Ineffective",
      "Needs improvement",
      "Not Applicable"
  ])

  # REST properties
  _publish_attrs = [
      'design',
      'operationally',
      PublishOnly('audit'),
      PublishOnly('object')
  ]

  _tracked_attrs = {
      'contact_id',
      'description',
      'design',
      'notes',
      'operationally',
      'reference_url',
      'secondary_contact_id',
      'test_plan',
      'title',
      'url',
      'start_date',
      'end_date'
  }

  _aliases = {
      "owners": None,
      "assessment_template": {
          "display_name": "Template",
          "ignore_on_update": True,
          "filter_by": "_ignore_filter",
          "type": reflection.AttributeInfo.Type.MAPPING,
      },
      "url": "Assessment URL",
      "design": "Conclusion: Design",
      "operationally": "Conclusion: Operation",
      "related_creators": {
          "display_name": "Creator",
          "mandatory": True,
          "filter_by": "_filter_by_related_creators",
          "type": reflection.AttributeInfo.Type.MAPPING,
      },
      "related_assessors": {
          "display_name": "Assessor",
          "mandatory": True,
          "filter_by": "_filter_by_related_assessors",
          "type": reflection.AttributeInfo.Type.MAPPING,
      },
      "related_verifiers": {
          "display_name": "Verifier",
          "filter_by": "_filter_by_related_verifiers",
          "type": reflection.AttributeInfo.Type.MAPPING,
      },
  }

  similarity_options = {
      "relevant_types": {
          "Audit": {"weight": 5},
          "Regulation": {"weight": 3},
          "Control": {"weight": 10},
      },
      "threshold": 5,
  }

  def validate_conclusion(self, value):
    return value if value in self.VALID_CONCLUSIONS else ""

  @validates("operationally")
  def validate_opperationally(self, key, value):
    # pylint: disable=unused-argument
    return self.validate_conclusion(value)

  @validates("design")
  def validate_design(self, key, value):
    # pylint: disable=unused-argument
    return self.validate_conclusion(value)

  @classmethod
  def _filter_by_related_creators(cls, predicate):
    return cls._get_relate_filter(predicate, "Creator")

  @classmethod
  def _filter_by_related_assessors(cls, predicate):
    return cls._get_relate_filter(predicate, "Assessor")

  @classmethod
  def _filter_by_related_verifiers(cls, predicate):
    return cls._get_relate_filter(predicate, "Verifier")

  @classmethod
  def _ignore_filter(cls, _):
    return None
