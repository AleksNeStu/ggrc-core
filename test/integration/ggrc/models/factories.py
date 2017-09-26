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
from contextlib import contextmanager

import factory

from ggrc import db
from ggrc import models

from ggrc.access_control.role import AccessControlRole
from ggrc.access_control.list import AccessControlList
from ggrc.access_control.roleable import Roleable
from ggrc.models.mixins import CustomAttributable

from ggrc_risks import models as risk_models

from integration.ggrc.models.model_factory import ModelFactory
from integration.ggrc_basic_permissions.models \
    import factories as rbac_factories


def random_str(length=8, prefix="", chars=None):
  chars = chars or string.ascii_uppercase + string.digits + "  _.-"
  return prefix + "".join(random.choice(chars) for _ in range(length))


@contextmanager
def single_commit():
  """Run all factory create calls in single commit."""
  db.session.single_commit = False
  try:
    yield
  except:
    raise
  else:
    db.session.commit()
  finally:
    db.session.single_commit = True


class TitledFactory(ModelFactory):
  title = factory.LazyAttribute(lambda m: random_str(prefix='title '))


class WithACLandCAFactory(ModelFactory):
  """Factory class to create object with ACL and CA in one step"""
  @classmethod
  def _create(cls, target_class, *args, **kwargs):
    """Create instance of model"""
    acls = []
    if "access_control_list_" in kwargs:
      acls = kwargs.pop("access_control_list_")
    cavs = []
    if "custom_attribute_values_" in kwargs:
      cavs = kwargs.pop("custom_attribute_values_")

    instance = target_class(**kwargs)
    db.session.add(instance)
    db.session.flush()

    if acls and isinstance(instance, Roleable):
      for acl in acls:
        db.session.add(models.AccessControlList(
            object=instance,
            ac_role_id=acl.get("ac_role_id"),
            person_id=acl.get("person_id"),
        ))
    if cavs and isinstance(instance, CustomAttributable):
      for cav in cavs:
        db.session.add(models.CustomAttributeValue(
            attributable=instance,
            attribute_value=cav.get("attribute_value"),
            attribute_object_id=cav.get("attribute_object_id"),
            custom_attribute_id=cav.get("custom_attribute_id"),
        ))

    if isinstance(instance, models.CustomAttributeValue):
      cls._log_event(instance.attributable)
    if hasattr(instance, "log_json"):
      cls._log_event(instance)
    if getattr(db.session, "single_commit", True):
      db.session.commit()
    return instance


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

  directive = factory.LazyAttribute(lambda m: RegulationFactory())


class IssueFactory(TitledFactory):

  class Meta:
    model = models.Issue


class AssessmentFactory(TitledFactory):

  class Meta:
    model = models.Assessment

  audit = factory.LazyAttribute(lambda m: AuditFactory())


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

  @classmethod
  def _create(cls, target_class, *args, **kwargs):
    """Fix context related_object when audit is created"""
    instance = super(AuditFactory, cls)._create(target_class, *args, **kwargs)
    instance.context.related_object = instance

    rbac_factories.ContextImplicationFactory(
        context=instance.context,
        source_context=instance.program.context,
        context_scope="Audit",
        source_context_scope="Program")

    if getattr(db.session, "single_commit", True):
      db.session.commit()
    return instance


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
  default_people = {"assessors": "Admin",
                    "verifiers": "Admin"}


class ContractFactory(TitledFactory):

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

  title = "some link"
  link = "some link"


class UrlFactory(DocumentFactory):
  document_type = models.Document.URL


class EvidenceFactory(DocumentFactory):
  document_type = models.Document.ATTACHMENT


class ReferenceUrlFactory(DocumentFactory):
  document_type = models.Document.REFERENCE_URL


class ObjectiveFactory(TitledFactory):

  class Meta:
    model = models.Objective


class RegulationFactory(TitledFactory):

  class Meta:
    model = models.Regulation


class OrgGroupFactory(TitledFactory):

  class Meta:
    model = models.OrgGroup


class SystemFactory(TitledFactory):

  class Meta:
    model = models.System


class ProcessFactory(TitledFactory):

  class Meta:
    model = models.Process


class PolicyFactory(TitledFactory):

  class Meta:
    model = models.Policy


class MarketFactory(TitledFactory):

  class Meta:
    model = models.Market


class AccessControlListFactory(ModelFactory):
  """Access Control List factory class"""

  class Meta:
    model = AccessControlList


class AccessControlRoleFactory(ModelFactory):
  """Access Control Role factory class"""

  class Meta:
    model = AccessControlRole

  name = factory.LazyAttribute(
      lambda _: random_str(prefix="Access Control Role - ")
  )
  non_editable = False


class AccessControlRoleAdminFactory(AccessControlRoleFactory):
  """Access Control Role Admin factory class"""
  mandatory = u"1"
  name = "Admin"


class AccessGroupFactory(TitledFactory):
  """Access Group factory class"""

  class Meta:
    model = models.AccessGroup


class ClauseFactory(TitledFactory):
  """Clause factory class"""

  class Meta:
    model = models.Clause


class DataAssetFactory(TitledFactory):
  """DataAsset factory class"""

  class Meta:
    model = models.DataAsset


class FacilityFactory(TitledFactory):
  """Facility factory class"""

  class Meta:
    model = models.Facility


class ProductFactory(TitledFactory):
  """Product factory class"""

  class Meta:
    model = models.Product


class SectionFactory(TitledFactory):
  """Section factory class"""

  class Meta:
    model = models.Section


class StandardFactory(TitledFactory):
  """Standard factory class"""

  class Meta:
    model = models.Standard

  description = factory.LazyAttribute(lambda _: random_str(length=100))


class VendorFactory(TitledFactory):
  """Vendor factory class"""

  class Meta:
    model = models.Vendor


class RiskFactory(TitledFactory):
  """Risk factory class"""

  class Meta:
    model = risk_models.Risk

  description = factory.LazyAttribute(lambda _: random_str(length=100))


class ThreatFactory(TitledFactory):
  """Threat factory class"""

  class Meta:
    model = risk_models.Threat


def get_model_factory(model_name):
  """Get object factory for provided model name"""
  from integration.ggrc_workflows.models import factories as wf_factories
  model_factories = {
      "AccessControlRole": AccessControlRoleFactory,
      "AccessControlList": AccessControlListFactory,
      "AccessGroup": AccessGroupFactory,
      "Assessment": AssessmentFactory,
      "AssessmentTemplate": AssessmentTemplateFactory,
      "Audit": AuditFactory,
      "Clause": ClauseFactory,
      "Contract": ContractFactory,
      "Control": ControlFactory,
      "TaskGroupFactory": wf_factories.TaskGroupFactory,
      "TaskGroupObjectFactory": wf_factories.TaskGroupObjectFactory,
      "TaskGroupTaskFactory": wf_factories.TaskGroupTaskFactory,
      "CycleFactory": wf_factories.CycleFactory,
      "CycleTaskGroupFactory": wf_factories.CycleTaskGroupFactory,
      "CycleTaskFactory": wf_factories.CycleTaskFactory,
      "CycleTaskEntryFactory": wf_factories.CycleTaskEntryFactory,
      "DataAsset": DataAssetFactory,
      "Facility": FacilityFactory,
      "Issue": IssueFactory,
      "Market": MarketFactory,
      "Objective": ObjectiveFactory,
      "OrgGroup": OrgGroupFactory,
      "Person": PersonFactory,
      "Policy": PolicyFactory,
      "Process": ProcessFactory,
      "Product": ProductFactory,
      "Regulation": RegulationFactory,
      "Section": SectionFactory,
      "Standard": StandardFactory,
      "System": SystemFactory,
      "Vendor": VendorFactory,
      "Risk": RiskFactory,
      "Threat": ThreatFactory,
      "Workflow": wf_factories.WorkflowFactory,
  }
  return model_factories[model_name]
