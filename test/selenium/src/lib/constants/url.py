# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Constants for URLs construction."""
# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import

from lib.constants.objects import *  # noqa; the names are later exported


# URL's parts for work with objects and REST API queries
API = "api"
DASHBOARD = "dashboard"
ADMIN_DASHBOARD = "admin"
AUDIT = AUDITS + "/{0}"
RELATIONSHIPS = "relationships"
OBJECT_OWNERS = "object_owners"
CONTACTS = "contacts"
QUERY = "query"

# url path for user
DEFAULT_EMAIL_DOMAIN = "example.com"
DEFAULT_USER_EMAIL = "user@" + DEFAULT_EMAIL_DOMAIN
DEFAULT_USER_HREF = "/".join([API, PEOPLE, str(1)])


class Widget(object):
  """URL's constants parts for widgets."""
  # pylint: disable=too-few-public-methods
  # admin dashboard page
  CUSTOM_ATTRIBUTES = "#custom_attribute_widget"
  EVENTS = "#events_list_widget"
  ROLES = "#roles_list_widget"
  PEOPLE = "#people_list_widget"
  # widgets
  INFO = "#info_widget"
  AUDITS = "#audit_widget"
  SUMMARY = "#Summary_widget"  # audits
  ASSESSMENTS = "#assessment_widget"
  ASSESSMENT_TEMPLATES = "#assessment_template_widget"
  CONTROLS = "#control_widget"
  ISSUES = "#issue_widget"
  PROGRAMS = "#program_widget"


def get_widget_name_of_mapped_objs(obj_name, is_versions_widget=False):
  """Get and return widget name for mapped objects (URL's parts for widgets)
  based on object name. If 'is_versions_widget' then destinations objects's
  widget will be snapshots' versions.
  """
  middle_part = (get_singular(obj_name) if not is_versions_widget else
                 get_singular(obj_name, title=True) + "_versions")
  return "#" + middle_part + "_widget"
