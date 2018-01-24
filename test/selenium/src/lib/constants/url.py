# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Constants for URLs construction."""
# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import

import re
from urlparse import urldefrag

from lib.constants import regex
from lib.constants.objects import *  # noqa; the names are later exported

# URL's parts for work with objects and REST API queries
API = "api"
DASHBOARD = "dashboard"
ADMIN_DASHBOARD = "admin"
AUDIT = AUDITS + "/{0}"
RELATIONSHIPS = "relationships"
OBJECT_OWNERS = "object_owners"
USER_ROLES = "user_roles"
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
  CUSTOM_ATTRIBUTES = "#!custom_attribute_widget"
  EVENTS = "#!events_list_widget"
  ROLES = "#!roles_list_widget"
  PEOPLE = "#!people_list_widget"
  # widgets
  INFO = "#!info_widget"
  AUDITS = "#!audit_widget"
  SUMMARY = "#!Summary_widget"  # audits
  ASSESSMENTS = "#!assessment_widget"
  ASSESSMENT_TEMPLATES = "#!assessment_template_widget"
  CONTROLS = "#!control_widget"
  ISSUES = "#!issue_widget"
  PROGRAMS = "#!program_widget"


class Utils(object):
  """Utils to manipulate with URLs."""

  @staticmethod
  def split_url_into_parts(url):
    """Split URL into parts using logic from regular expression, return
    dictionary of URL's parts.
    """
    (source_obj_plural, source_obj_id, widget_name,
     mapped_obj_singular, mapped_obj_id) = (
        re.search(regex.URL_WIDGET_INFO, url + "/").groups())
    return {
        "source_obj_from_url": source_obj_plural,
        "source_obj_id_from_url": source_obj_id,
        "widget_name_from_url": widget_name.split("_")[0],
        "mapped_obj_from_url": mapped_obj_singular,
        "mapped_obj_id_from_url": mapped_obj_id
    }

  @staticmethod
  def get_widget_name_of_mapped_objs(obj_name, is_versions_widget=False):
    """Get and return widget name for mapped objects (URL's parts for widgets)
    based on object name. If 'is_versions_widget' then destinations objects's
    widget will be snapshots' versions.
    """
    middle_part = (get_singular(obj_name) if not is_versions_widget else
                   get_singular(obj_name, title=True) + "_versions")
    return "#!" + middle_part + "_widget"

  @staticmethod
  def get_src_obj_url(url):
    """Get and return source object's URL part from full URL."""
    return urldefrag(url)[0]
