# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Widgets on Admin Dashboard page."""
# pylint: disable=too-few-public-methods

from lib import base, environment, exception
from lib.constants import locator, url, objects
from lib.page.widget import widget_base
from lib.utils import selenium_utils


class Widget(base.Widget):
  """Base class for Admin widgets."""


class Events(Widget):
  """Event widget on Admin Dashboard."""
  _locators = locator.WidgetAdminEvents

  URL = environment.APP_URL + url.ADMIN_DASHBOARD + url.Widget.EVENTS

  def __init__(self, driver):
    super(Events, self).__init__(driver)
    self.widget_header = base.Label(driver, self._locators.TREE_VIEW_HEADER)

  def get_events(self):
    """Get list of elements that displayed in Tree View on Event widget."""
    selenium_utils.get_when_clickable(
        self._driver, self._locators.FIRST_TREE_VIEW_ITEM)
    return self._driver.find_elements(*self._locators.TREE_VIEW_ITEMS)


class People(Widget):
  """People widget on Admin Dashboard."""
  URL = environment.APP_URL + url.ADMIN_DASHBOARD + url.Widget.PEOPLE


class Roles(Widget):
  """Admin roles widget on Admin Dashboard."""

  URL = environment.APP_URL + url.ADMIN_DASHBOARD + url.Widget.ROLES

  def __init__(self, driver):
    super(Roles, self).__init__(driver)
    self.roles_tree_view = base.AdminTreeView(self._driver)

  def get_role_scopes_text_as_dict(self):
    """Get dictionary of labels that displayed in Tree View on Roles widget.
    """
    tree_view_items = self.roles_tree_view.tree_view_items()
    return dict([item.text.splitlines() for item in tree_view_items])


class CustomAttributes(widget_base.WidgetAdminCustomAttributes):
  """Custom attributes widget on Admin Dashboard page."""

  URL = (environment.APP_URL + url.ADMIN_DASHBOARD +
         url.Widget.CUSTOM_ATTRIBUTES)

  def __init__(self, driver):
    super(CustomAttributes, self).__init__(driver)
    self.ca_tree_view = base.AdminTreeView(self._driver)

  def expand_collapse_group(self, item_title, expand=True):
    """Expand/collapse 2-nd tier of Tree View item."""
    items = self.get_items_list()
    for i in items:
      if i.text == item_title:
        if expand:
          return i.expand()
        else:
          return i.collapse()
    raise exception.ElementNotFound('{} in list {}'.format(item_title, items))

  def get_items_list(self):
    """Return Tree View item objects from current widget."""
    return self.ca_tree_view.tree_view_items()

  def add_custom_attribute(self, ca_obj):
    """Add custom attribute from custom attribute object given."""
    ca_item_content = self.expand_collapse_group(
        objects.get_normal_form(ca_obj.definition_type), expand=True)
    ca_item_content.add_new_custom_attribute(ca_obj)
    self.check_success_ca_created_msg(ca_obj.title)
    self.expand_collapse_group(
        objects.get_normal_form(ca_obj.definition_type), expand=False)

  def check_success_ca_created_msg(self, ca_title):
    """Await for success message with given custom attribute title."""
    text = ("New Custom Attribute Definition {} added successfully"
            .format(ca_title))
    selenium_utils.wait_for_element_text(
        self._driver, self._locators.CA_ADDED_SUCCESS_ALERT, text)

  def get_custom_attributes_list(self, ca_group):
    """Collect custom attributes from expanded custom attribute group
    Tree View."""
    ca_item_content = self.expand_collapse_group(
        objects.get_normal_form(ca_group.definition_type), expand=True)
    return ca_item_content.get_ca_list_from_group()


class ModalCustomAttributes(widget_base.CustomAttributeModal):
  """Custom attributes modal."""
