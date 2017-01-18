# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""The module provide service for working with GGRC's URLs."""

import objects

# URL's parts for objects
API = "api"
DASHBOARD = "dashboard"
ADMIN_DASHBOARD = "admin"
PROGRAMS = "programs"
WORKFLOWS = "workflows"
AUDITS = "audits"
AUDIT = AUDITS + "/{0}"
ASSESSMENTS = "assessments"
ASSESSMENT_TEMPLATES = "assessment_templates"
ISSUES = "issues"
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
RELATIONSHIPS = "relationships"
OBJECT_OWNERS = "object_owners"

# default
DEFAULT_EMAIL_DOMAIN = "example.com"
DEFAULT_EMAIL = "user@" + DEFAULT_EMAIL_DOMAIN
DEFAULT_URL_USER_API = "/".join([API, objects.PEOPLE, str(1)])

class Widget(object):
  """URL's parts for widgets."""

  # pylint: disable=too-few-public-methods

  # common
  INFO = "#info_widget"
  # admin dashboard page
  CUSTOM_ATTRIBUTES = "#custom_attribute_widget"
  EVENTS = "#events_list_widget"
  ROLES = "#roles_list_widget"
  PEOPLE = "#people_list_widget"
  ASSESSMENTS = "#assessment_widget"
  ASSESSMENT_TEMPLATES = "#assessment_template_widget"
