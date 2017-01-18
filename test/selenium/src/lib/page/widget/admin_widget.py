# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Module for widgets on Admin Dashboard page."""
# pylint: disable=too-few-public-methods

from lib import base
from lib import environment
from lib import exception
from lib.constants import locator
from lib.constants import url
from lib.page.widget import widget_base
from lib.utils import selenium_utils


class Widget(base.Widget):
  """Base class for admin widgets"""


class Events(Widget):
  """Model for event widget on admin dashboard"""
  _locator = locator.WidgetAdminEvents

  URL = environment.APP_URL \
      + url.ADMIN_DASHBOARD \
      + url.Widget.EVENTS

  def __init__(self, driver):
    super(Events, self).__init__(driver)
    self.widget_header = base.Label(driver, self._locator.TREE_VIEW_HEADER)

  def get_events(self):
    """Get list of WebElements that displayed in tree view at Event widget"""
    selenium_utils.get_when_clickable(
        self._driver,
        self._locator.FIRST_TREE_VIEW_ITEM)
    return self._driver.find_elements(*self._locator.TREE_VIEW_ITEMS)


class People(Widget):
  """Model for people widget on admin dashboard"""
  URL = environment.APP_URL \
      + url.ADMIN_DASHBOARD \
      + url.Widget.PEOPLE


class Roles(Widget):
  """Model for the widget admin roles on admin dashboard."""
  _locator = locator.WidgetAdminRoles

  URL = environment.APP_URL \
      + url.ADMIN_DASHBOARD \
      + url.Widget.ROLES

  def __init__(self, driver):
    super(Roles, self).__init__(driver)
    self.roles_tree_view = base.TreeView(
        self._driver, obj_name=self._locator.widget_name)

  def get_role_scopes_text_as_dict(self):
    """Get dictionary of labels that displayed in tree view at Event widget."""
    tree_view_items = self.roles_tree_view.tree_view_items_elements()
    return dict([item.text.splitlines() for item in tree_view_items])


class CustomAttributes(widget_base.WidgetAdminCustomAttributes):
  """Model for custom attributes widget on the admin dashboard page."""
  _locator = locator.AdminCustomAttributes
  URL = (
      environment.APP_URL + url.ADMIN_DASHBOARD + url.Widget.CUSTOM_ATTRIBUTES
  )

  def __init__(self, driver):
    super(CustomAttributes, self).__init__(driver)
    self.ca_tree_view = base.TreeView(
        self._driver, obj_name=self._locator.widget_name)

  def expand_collapse_group(self, item_title, expand=True):
    """Expand/collapse 2-nd tier of tree-view item."""
    items = self.get_items_list()
    for i in items:
      if i.text == item_title:
        if expand:
          return i.expand()
        else:
          return i.collapse()
    raise exception.ElementNotFound('{} in list {}'.format(item_title, items))

  def get_items_list(self):
    """Return TreeViewItem objects from the current widget."""
    return self.ca_tree_view.tree_view_items()

  def add_custom_attribute(self, ca_object):
    """Add a Custom Attribute from CustomAttribute object given."""
    ca_item_content = self.expand_collapse_group(
        ca_object.definition_type, expand=True)
    ca_item_content.add_new_custom_attribute(ca_object)
    self.check_success_ca_created_msg(ca_object.title)
    self.expand_collapse_group(ca_object.definition_type, expand=False)

  def check_success_ca_created_msg(self, ca_title):
    """Awaiting for success message with given CA title."""
    text = "New Custom Attribute Definition {} added successfully"\
        .format(ca_title)
    selenium_utils.wait_for_element_text(
        self._driver, self._locator.CA_ADDED_SUCCESS_ALERT, text)

  def get_custom_attributes_list(self, ca_group):
    """Collect custom attributes from the expanded CA group tree-view."""
    ca_item_content = self.expand_collapse_group(ca_group, expand=True)
    return ca_item_content.get_custom_attributes_list_from_group()


class ModalCustomAttributes(widget_base.CustomAttributeModal,
                            widget_base.CreateNewCustomAttributeModal):
  """Model for the custom attribute modal"""
