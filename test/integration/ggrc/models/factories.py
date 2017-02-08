# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Factories for ggrc models.

These are factories for generating regular ggrc models. The factories create a
model and log a post event with the model revision. These do not however
trigger signals. For tests that rely on proper signals being triggered, we must
use the object generator in the ggrc.generator module.
"""

# pylint: disable=too-few-public-methods,missing-docstring,old-style-class
# pylint: disable=no-init

import random
import string

import factory

from ggrc import db
from ggrc import models
from ggrc.login import noop
from ggrc.fulltext import get_indexer
from ggrc.fulltext.recordbuilder import fts_record_for


def random_str(length=8, prefix="", chars=None):
  chars = chars or string.ascii_uppercase + string.digits + "  _.-"
  return prefix + "".join(random.choice(chars) for _ in range(length))


class ModelFactory(factory.Factory):

  @classmethod
  def _create(cls, target_class, *args, **kwargs):
    instance = target_class(*args, **kwargs)
    db.session.add(instance)
    if isinstance(instance, models.CustomAttributeValue):
      cls._log_event(instance.attributable)
    if hasattr(instance, "log_json"):
      cls._log_event(instance)
    db.session.commit()
    return instance

  @classmethod
  def _log_event(cls, instance):
    indexer = get_indexer()
    db.session.flush()
    user = cls._get_user()
    revision = models.Revision(
        instance, user.id, 'created', instance.log_json())
    event = models.Event(
        modified_by=user,
        action="POST",
        resource_id=instance.id,
        resource_type=instance.type,
        context=instance.context,
        revisions=[revision],
    )
    db.session.add(revision)
    db.session.add(event)
    indexer.update_record(fts_record_for(instance), commit=False)

  @staticmethod
  def _get_user():
    user = models.Person.query.first()
    if not user:
      user = models.Person(
          name=noop.default_user_name,
          email=noop.default_user_email,
      )
      db.session.add(user)
      db.session.flush()
    return user


class TitledFactory(ModelFactory):
  title = factory.LazyAttribute(lambda m: random_str(prefix='title '))


class CustomAttributeDefinitionFactory(TitledFactory):

  class Meta:
    model = models.CustomAttributeDefinition

  definition_type = None
  definition_id = None
  attribute_type = "Text"
  multi_choice_options = None


class CustomAttributeValueFactory(ModelFactory):

  class Meta:
    model = models.CustomAttributeValue

  custom_attribute = None
  attributable_id = None
  attributable_type = None
  attribute_value = None
  attribute_object_id = None


class DirectiveFactory(TitledFactory):

  class Meta:
    model = models.Directive


class ControlFactory(TitledFactory):

  class Meta:
    model = models.Control

  directive = factory.SubFactory(DirectiveFactory)
  kind_id = None
  version = None
  documentation_description = None
  verify_frequency_id = None
  fraud_related = None
  key_control = None
  active = None
  notes = None


class AssessmentFactory(TitledFactory):

  class Meta:
    model = models.Assessment


class ControlCategoryFactory(ModelFactory):

  class Meta:
    model = models.ControlCategory

  name = factory.LazyAttribute(lambda m: random_str(prefix='name'))
  lft = None
  rgt = None
  scope_id = None
  depth = None
  required = None


class CategorizationFactory(ModelFactory):

  class Meta:
    model = models.Categorization

  category = None
  categorizable = None
  category_id = None
  categorizable_id = None
  categorizable_type = None


class ContextFactory(ModelFactory):

  class Meta:
    model = models.Context

  name = factory.LazyAttribute(
      lambda obj: random_str(prefix="SomeObjectType Context"))
  related_object = None


class ProgramFactory(TitledFactory):

  class Meta:
    model = models.Program

  context = factory.LazyAttribute(lambda _: ContextFactory())


class AuditFactory(TitledFactory):

  class Meta:
    model = models.Audit

  status = "Planned"
  contact = factory.LazyAttribute(lambda _: PersonFactory())
  program = factory.LazyAttribute(lambda _: ProgramFactory())
  context = factory.LazyAttribute(lambda _: ContextFactory())


class SnapshotFactory(ModelFactory):

  class Meta:
    model = models.Snapshot

  parent = factory.LazyAttribute(lambda _: AuditFactory())
  child_id = 0
  child_type = ""
  revision_id = 0


class AssessmentTemplateFactory(TitledFactory):

  class Meta:
    model = models.AssessmentTemplate

  template_object_type = None
  test_plan_procedure = False
  procedure_description = factory.LazyAttribute(
      lambda _: random_str(length=100))
  default_people = {"assessors": "Object Owners",
                    "verifiers": "Object Owners"}


class ContractFactory(ModelFactory):

  class Meta:
    model = models.Contract


class EventFactory(ModelFactory):

  class Meta:
    model = models.Event
  revisions = []


class RelationshipFactory(ModelFactory):

  class Meta:
    model = models.Relationship
  source = None
  destination = None


class RelationshipAttrFactory(ModelFactory):

  class Meta:
    model = models.RelationshipAttr

  relationship_id = None
  attr_name = None
  attr_value = None


class PersonFactory(ModelFactory):

  class Meta:
    model = models.Person

  email = factory.LazyAttribute(
      lambda _: random_str(chars=string.ascii_letters) + "@example.com"
  )


class CommentFactory(ModelFactory):

  class Meta:
    model = models.Comment


class DocumentFactory(ModelFactory):

  class Meta:
    model = models.Document


class ObjectDocumentFactory(ModelFactory):

  class Meta:
    model = models.ObjectDocument


class ObjectiveFactory(TitledFactory):

  class Meta:
    model = models.Objective


class RegulationFactory(TitledFactory):

  class Meta:
    model = models.Regulation


class OrgGroupFactory(TitledFactory):

  class Meta:
    model = models.OrgGroup


class ProcessFactory(TitledFactory):

  class Meta:
    model = models.Process


class PolicyFactory(TitledFactory):

  class Meta:
    model = models.Policy


class MarketFactory(TitledFactory):

  class Meta:
    model = models.Market
