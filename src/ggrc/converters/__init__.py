# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

""" This module is used for import and export of data with csv files """

from ggrc.extensions import get_extension_modules
from ggrc.models import AccessGroup
from ggrc.models import Assessment
from ggrc.models import AssessmentTemplate
from ggrc.models import Audit
from ggrc.models import Clause
from ggrc.models import Contract
from ggrc.models import Control
from ggrc.models import DataAsset
from ggrc.models import Facility
from ggrc.models import Issue
from ggrc.models import Market
from ggrc.models import Objective
from ggrc.models import OrgGroup
from ggrc.models import Person
from ggrc.models import Policy
from ggrc.models import Process
from ggrc.models import Product
from ggrc.models import Program
from ggrc.models import Project
from ggrc.models import Regulation
from ggrc.models import Section
from ggrc.models import Standard
from ggrc.models import System
from ggrc.models import Vendor


def get_shared_unique_rules():
  """ get rules for all cross checks betveen classes

  used for checking unique constraints on colums such as code and title
  """

  shared_tables = [
      (System, Process),
      (Section, Clause),
      (Policy, Regulation, Standard, Contract),
  ]
  rules = {}
  for tables in shared_tables:
    for table in tables:
      rules[table] = tables

  return rules


GGRC_IMPORTABLE = {
    "access group": AccessGroup,
    "access_group": AccessGroup,
    "accessgroup": AccessGroup,
    "assessment template": AssessmentTemplate,
    "assessment": Assessment,
    "assessment_template": AssessmentTemplate,
    "audit": Audit,
    "clause": Clause,
    "contract": Contract,
    "control assessment": Assessment,
    "control": Control,
    "data asset": DataAsset,
    "data_asset": DataAsset,
    "dataasset": DataAsset,
    "facility": Facility,
    "issue": Issue,
    "market": Market,
    "objective": Objective,
    "org group": OrgGroup,
    "org_group": OrgGroup,
    "orggroup": OrgGroup,
    "person": Person,
    "policy": Policy,
    "process": Process,
    "product": Product,
    "program": Program,
    "project": Project,
    "regulation": Regulation,
    "section": Section,
    "standard": Standard,
    "system": System,
    "vendor": Vendor,
}

GGRC_EXPORTABLE = {}


def _get_types(attr):
  """Get contributed attribute types.

  Args:
    attr: String containing selected type. Either contributed_importables or
      contributed_exportables.
  """
  res = {}
  for extension_module in get_extension_modules():
    contributed = getattr(extension_module, attr, None)
    if callable(contributed):
      res.update(contributed())
    elif isinstance(contributed, dict):
      res.update(contributed)
  return res


def get_importables():
  """ Get a dict of all importable objects from all modules """
  importable = GGRC_IMPORTABLE
  importable.update(_get_types("contributed_importables"))
  return importable


def get_exportables():
  """ Get a dict of all exportable objects from all modules """
  exportable = GGRC_EXPORTABLE
  exportable.update(get_importables())
  exportable.update(_get_types("contributed_exportables"))
  return exportable
