# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""All GGRC model classes grouped together for convenience."""

import sys

from ggrc.models import inflector
from ggrc.models.access_group import AccessGroup
from ggrc.models.assessment import Assessment
from ggrc.models.assessment_template import AssessmentTemplate
from ggrc.models.audit import Audit
from ggrc.models.audit_object import AuditObject
from ggrc.models.background_task import BackgroundTask
from ggrc.models.categorization import Categorization
from ggrc.models.category import CategoryBase
from ggrc.models.clause import Clause
from ggrc.models.comment import Comment
from ggrc.models.context import Context
from ggrc.models.control import Control
from ggrc.models.control import ControlAssertion
from ggrc.models.control import ControlCategory
from ggrc.models.custom_attribute_definition import CustomAttributeDefinition
from ggrc.models.custom_attribute_value import CustomAttributeValue
from ggrc.models.data_asset import DataAsset
from ggrc.models.directive import Contract
from ggrc.models.directive import Directive
from ggrc.models.directive import Policy
from ggrc.models.directive import Regulation
from ggrc.models.directive import Standard
from ggrc.models.document import Document
from ggrc.models.event import Event
from ggrc.models.facility import Facility
from ggrc.models.help import Help
from ggrc.models.issue import Issue
from ggrc.models.market import Market
from ggrc.models.meeting import Meeting
from ggrc.models.notification import Notification
from ggrc.models.notification import NotificationConfig
from ggrc.models.notification import NotificationType
from ggrc.models.object_document import ObjectDocument
from ggrc.models.object_owner import ObjectOwner
from ggrc.models.object_person import ObjectPerson
from ggrc.models.objective import Objective
from ggrc.models.option import Option
from ggrc.models.org_group import OrgGroup
from ggrc.models.person import Person
from ggrc.models.product import Product
from ggrc.models.program import Program
from ggrc.models.project import Project
from ggrc.models.relationship import Relationship
from ggrc.models.relationship import RelationshipAttr
from ggrc.models.revision import Revision
from ggrc.models.section import Section
from ggrc.models.snapshot import Snapshot
from ggrc.models.system import Process
from ggrc.models.system import System
from ggrc.models.system import SystemOrProcess
from ggrc.models.vendor import Vendor

all_models = [
    AccessGroup,
    Assessment,
    AssessmentTemplate,
    Audit,
    AuditObject,
    Categorization,
    CategoryBase,
    ControlCategory,
    ControlAssertion,
    Context,
    Control,
    Comment,
    CustomAttributeDefinition,
    CustomAttributeValue,
    DataAsset,
    Directive,
    Contract,
    Policy,
    Regulation,
    Standard,
    Document,
    Facility,
    Help,
    Market,
    Meeting,
    Objective,
    ObjectDocument,
    ObjectOwner,
    ObjectPerson,
    Option,
    OrgGroup,
    Vendor,
    Person,
    Product,
    Program,
    Project,
    Relationship,
    RelationshipAttr,
    Section,
    Clause,
    SystemOrProcess,
    System,
    Process,
    Revision,
    Event,
    BackgroundTask,
    NotificationConfig,
    NotificationType,
    Notification,
    Issue,
    Snapshot,
]

__all__ = [model.__name__ for model in all_models]


def register_model(model):
  """Add model to all models.

  This function is used for adding models from different ggrc modules, such as
  ggrc_workflows or ggrc_risks, to the list of all models in the ggrc module.

  Args:
    model: sqlalchemy model to be added to the list of all models.
  """
  current_module = sys.modules[__name__]
  setattr(current_module, model.__name__, model)
  all_models.append(model)
  __all__.append(model.__name__)


def unregister_model(model):
  """Remove model from all models.

  This function removes the given model from the main ggrc module and the
  all_models list.

  Args:
    model: sqlalchemy model that should be removed from the ggrc module
  """
  current_module = sys.modules[__name__]
  delattr(current_module, model.__name__)
  inflector.unregister_inflector(model._inflector)
  if model in all_models:
    all_models.remove(model)
  if model.__name__ in __all__:
    __all__.remove(model.__name__)
