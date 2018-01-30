# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Objects' constants class model w/ related methods and properties."""


class Names(object):
  """All objects' names and properties."""
  PROGRAMS = "programs"
  WORKFLOWS = "workflows"
  AUDITS = "audits"
  ASSESSMENTS = "assessments"
  ASSESSMENT_TEMPLATES = "assessment_templates"
  ISSUES = "issues"
  DIRECTIVES = "directives"
  REGULATIONS = "regulations"
  POLICIES = "policies"
  STANDARDS = "standards"
  CONTRACTS = "contracts"
  CLAUSES = "clauses"
  SECTIONS = "sections"
  CONTROLS = "controls"
  OBJECTIVES = "objectives"
  PEOPLE = "people"
  ORG_GROUPS = "org_groups"
  VENDORS = "vendors"
  ACCESS_GROUPS = "access_groups"
  SYSTEMS = "systems"
  PROCESSES = "processes"
  DATA_ASSETS = "data_assets"
  PRODUCTS = "products"
  PROJECTS = "projects"
  FACILITIES = "facilities"
  MARKETS = "markets"
  RISKS = "risks"
  THREATS = "threats"
  RISK_ASSESSMENTS = "risk_assessments"
  CUSTOM_ATTRIBUTES = "custom_attribute_definitions"
  COMMENTS = "comments"
  SNAPSHOTS = "snapshots"
  TASK_GROUPS = "task_groups"
  TASK_GROUP_TASKS = "task_group_tasks"
  CYCLE_TASK_GROUP_OBJECT_TASKS = "cycle_task_group_object_tasks"
  CYCLES = "cycles"

  @property
  def consts(self):
    """All objects' names constants' items (names and values) in upper case."""
    return {k: v for k, v in self.__class__.__dict__.items()
            if not k.startswith("_") and "ALL" not in k and k.isupper()}

  @property
  def snapshotable_values(self):
    """Snapshotable objects' names constants' values."""
    return (
      self.ACCESS_GROUPS, self.CLAUSES, self.CONTRACTS, self.CONTROLS,
      self.DATA_ASSETS, self.FACILITIES, self.MARKETS, self.OBJECTIVES,
      self.ORG_GROUPS, self.POLICIES, self.PROCESSES, self.PRODUCTS,
      self.REGULATIONS, self.SECTIONS, self.STANDARDS, self.SYSTEMS,
      self.VENDORS, self.RISKS, self.THREATS)

  @property
  def not_yet_snapshotable_values(self):
    """Not yet snapshotable objects' names constants' values."""
    return (self.RISK_ASSESSMENTS, self.PROJECTS)


  @property
  def w_cas_values(self):
    """W/ custom attributes objects' names constants' values."""
    return self.snapshotable_values + self.not_yet_snapshotable_values + (
        self.WORKFLOWS, self.PROGRAMS, self.AUDITS, self.ISSUES,
        self.ASSESSMENTS, self.PEOPLE)

  @property
  def wo_state_filtering(self):
    """W/o state filtering objects' names constants' values."""
    return (
        self.PEOPLE, self.WORKFLOWS, self.TASK_GROUPS, self.CYCLES,
        self.CYCLE_TASK_GROUP_OBJECT_TASKS)

  @property
  def plural_names(self):
    """All objects' names constants' names in plural form."""
    return self.consts.keys()

  @property
  def plural_values(self):
    """All objects' names constants' values in plural form."""
    return self.consts.values()

  @property
  def singular_names(self):
    """All objects' names constants' names in singular form."""
    return Utils._get_singular(self.plural_names)


class Utils(object):
  """Utils to manipulate with objects."""

  @staticmethod
  def _get_singular(plurals):
    """Return: list of basestring: Capitalized object names in singular form.
    """
    singulars = []
    for name in plurals:
      name = name.lower()
      if name == Names.PEOPLE:
        singular = "person"
      elif name == Names.POLICIES:
        singular = "policy"
      elif name == Names.PROCESSES:
        singular = "process"
      elif name == Names.FACILITIES:
        singular = "facility"
      else:
        singular = name[:-1]
      singulars.append(singular.upper())
    return singulars

  @staticmethod
  def _get_plural(singulars):
    """
    Return: list of basestring: Capitalized object names in plural form.
    """
    plurals = []
    for name in singulars:
      name = name.lower()
      if name == "people":
        plural = Names.PEOPLE
      elif name == "policy":
        plural = Names.POLICIES
      elif name == "process":
        plural = Names.PROCESSES
      elif name == "facility":
        plural = Names.FACILITIES
      else:
        plural = name + "s"
      plurals.append(plural.upper())
    return plurals

  @classmethod
  def get_singular(cls, plural, title=False):
    """Transform object name to singular and lower or title form.
   Example: risk_assessments -> risk_assessment
   """
    _singular = cls._get_singular([plural])[0]
    return _singular.title() if title else _singular.lower()

  @classmethod
  def get_plural(cls, singular, title=False):
    """Transform object name to plural and lower form or title form.
    Example: risk_assessment -> risk_assessments
    """
    _plural = cls._get_plural([singular])[0]
    return _plural.title() if title else _plural.lower()

  @staticmethod
  def get_normal_form(obj_name, with_space=True):
    """Transform object name to title form.
   Example:
   if with_space=True then risk_assessments -> Risk Assessments
   if with_space=False then risk_assessments -> RiskAssessments
   """
    normal = obj_name.replace("_", " ").title()
    return normal if with_space else normal.replace(" ", "")

  @classmethod
  def get_obj_type(cls, obj_name):
    """Get object's type based on object's name."""
    return cls.get_singular(
        obj_name, title=obj_name != Names.CUSTOM_ATTRIBUTES)


class Types(object):
  """All objects' types."""
  class __metaclass__(type):
    def __init__(cls, *args):
      for name_, value_ in Names().consts.items():
        setattr(cls, name_, Utils.get_obj_type(value_))
