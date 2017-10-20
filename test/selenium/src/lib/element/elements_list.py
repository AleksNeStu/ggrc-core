# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Module of classes inherited from ElementsList control."""
from lib import base
from lib.utils import selenium_utils


class DropdownMenu(base.ElementsList):
  """Class for common DropdownMenu Element."""

  def __init__(self, driver, element_or_locator):
    super(DropdownMenu, self).__init__(driver, element_or_locator)
    self._driver = driver
    self.item_class = base.DropdownMenuItem

  def get_dropdown_item(self, out_item_type):
    """Return DropdownItem element according to type"""
    return next(elem_val for elem_val in self.get_items()
                if out_item_type in elem_val.item_type)

  def is_item_exist(self, condition_property):
    """Check if element enable on dropdown and return Bool, by comparing
    aliases.
    Return bool if element exist
    """
    return any(elem_val.item_type for elem_val in self.get_items()
               if condition_property in elem_val.item_type)

  def is_item_enabled(self, out_item_type):
    """Check if element enable on dropdown, by comparing
    aliases.
    Return bool if element exist
    If element not found raise exception
    """
    return self.get_dropdown_item(out_item_type).enabled


class TabController(base.ElementsList):
  """Controller of navigation tabs."""
  def __init__(self, driver, element):
    super(TabController, self).__init__(driver, element)
    self._driver = driver
    self._active_tab = None

  @property
  def active_tab(self):
    """Getter for active tab. Raise StopIteration If currently TabController
    hasn't active tab.
    """
    if self._active_tab is None:
      self._active_tab = next((
          tab for tab in self.get_items()
          if selenium_utils.is_value_in_attr(tab.element)))
    return self._active_tab

  @active_tab.setter
  def active_tab(self, tab_name):
    """Set active tab according to passed 'tab_name'. If passed 'tab_name'
    equal current active_tab do nothing.
    """
    if tab_name != self.active_tab.text:
      self._active_tab = self.get_item(tab_name)
      selenium_utils.scroll_into_view(self._driver, self._active_tab.element)
      self._active_tab.click()
      selenium_utils.wait_for_js_to_load(self._driver)
