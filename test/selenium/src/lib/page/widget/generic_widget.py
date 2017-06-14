# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Widgets other than Info widget."""

import re

from selenium.common import exceptions
from selenium.webdriver.common.by import By

from lib import base, factory
from lib.constants import locator, regex
from lib.page.modal import unified_mapper
from lib.utils import selenium_utils


class Widget(base.Widget):
  """All widgets with Tree View and Filters."""
  # pylint: disable=too-many-instance-attributes
  def __init__(self, driver, obj_name):
    self.obj_name = obj_name
    self._locators_filter = factory.get_cls_locators_generic_widget(
        object_name=obj_name)
    self._locator_widget = factory.get_locator_widget(self.obj_name.upper())
    self.info_widget_cls = factory.get_cls_widget(
        object_name=obj_name, is_info=True)
    # Filter
    self.cls_without_state_filtering = (AssessmentTemplates, )
    # Persons, Workflows, TaskGroups, Cycles, CycleTaskGroupObjectTasks
    self.common_filter_locators = dict(
        text_box_locator=self._locators_filter.TEXTFIELD_TO_FILTER,
        bt_submit_locator=self._locators_filter.BUTTON_FILTER,
        bt_clear_locator=self._locators_filter.BUTTON_RESET)
    self.button_help = base.Button(driver, self._locators_filter.BUTTON_HELP)
    self.filter = base.FilterCommon(driver, **self.common_filter_locators)
    if self.__class__ not in self.cls_without_state_filtering:
      self.dropdown_states = base.DropdownStatic(
          driver, dropdown_locator=self._locators_filter.DROPDOWN,
          elements_locator=self._locators_filter.DROPDOWN_STATES)
    super(Widget, self).__init__(driver)
    # Tree View
    self.tree_view = TreeView(driver, self.info_widget_cls, self.obj_name)
    # Tab count
    self.members_listed = None
    self.member_count = None
    self._set_members_listed()

  def _set_member_count(self):
    """Parses widget name and number of items from widget tab title."""
    widget_label = selenium_utils.get_when_visible(
        self._driver, self._locator_widget).text
    # The widget label has 2 forms: "widget_name_plural (number_of_items)"
    # and "number_of_items" and they change depending on how many widgets
    # are open. In order to handle both forms, we first try to parse the
    # first form and only then the second one.
    parsed_label = re.match(regex.WIDGET_TITLE_AND_COUNT, widget_label)
    item_count = (
        widget_label if parsed_label is None else parsed_label.group(2))
    self.member_count = int(item_count)

  def _set_members_listed(self):
    """Wait for listed members to loaded and add them to local container."""
    self._set_member_count()
    if self.member_count:
      # wait until the elements are loaded
      selenium_utils.get_when_invisible(
          self._driver, locator.ObjectWidget.LOADING)
      self.members_listed = self._driver.find_elements(
          *locator.ObjectWidget.MEMBERS_TITLE_LIST)
    else:
      self.members_listed = []

  def wait_for_counter_loaded(self):
    """Wait for elements' counter on Filter panel to be visible."""
    return selenium_utils.get_when_visible(
        self._driver, locator.BaseWidgetGeneric.FILTER_PANE_COUNTER)

  def verify_counter_not_loaded(self):
    """Check that in case of empty table, counter not loaded on filter panel.
    """
    selenium_utils.wait_for_element_text(
        self._driver, locator.TreeView.NO_RESULTS_MESSAGE, "No results")

  def get_items_count(self):
    """Get elements' count from counter on filter panel."""
    selenium_utils.wait_for_js_to_load(self._driver)
    return self.wait_for_counter_loaded().text.split()[2]

  def wait_member_deleted(self, count):
    """Wait until elements' counter on filter panel refreshed with new value.
    Args: count (str)
    """
    selenium_utils.wait_for_js_to_load(self._driver)
    if count != '1':
      new_count = ' {}'.format(int(count) - 1)
      selenium_utils.wait_for_element_text(
          self._driver, locator.BaseWidgetGeneric.FILTER_PANE_COUNTER,
          new_count)
    else:
      self.verify_counter_not_loaded()

  def select_member_by_num(self, num):
    """Select member from list of members by number (start from 0).
    Args: num (int)
    Return: lib.page.widget.info.Widget
    """
    # pylint: disable=not-callable
    selenium_utils.wait_for_js_to_load(self._driver)
    self._set_members_listed()
    try:
      member = self.members_listed[num]
      # wait for the listed items animation to stop
      selenium_utils.wait_until_stops_moving(member)
      selenium_utils.click_via_js(self._driver, member)
      # wait for the info pane animation to stop
      info_panel = selenium_utils.get_when_clickable(
          self._driver, locator.ObjectWidget.INFO_PANE)
      selenium_utils.wait_until_stops_moving(info_panel)
      return self.info_widget_cls(self._driver)
    except exceptions.StaleElementReferenceException:
      self.members_listed = self._driver.find_elements(
          *locator.ObjectWidget.MEMBERS_TITLE_LIST)
      return self.select_member_by_num(num)
    except exceptions.TimeoutException:
      # sometimes the click to the listed member results in hover
      return self.select_member_by_num(num)


class TreeView(base.TreeView):
  """Genetic Tree Views."""
  # pylint: disable=too-many-instance-attributes
  _locators = locator.TreeView

  def __init__(self, driver, info_widget_cls, obj_name):
    super(TreeView, self).__init__(driver, obj_name=obj_name)
    self.info_widget_cls = info_widget_cls
    self.obj_name = obj_name
    self.create_obj_cls = factory.get_cls_create_obj(object_name=obj_name)
    self.dropdown_settings_cls = factory.get_cls_3bbs_dropdown_settings(
        object_name=obj_name, is_tree_view_not_info=True)
    self.dropdown_tree_view_item_cls = factory.get_cls_dropdown_tree_view_item(
        object_name=obj_name)
    self.fields_to_set = factory.get_fields_to_set(object_name=obj_name)
    self.locator_set_visible_fields = (
        By.CSS_SELECTOR,
        self._locators.BUTTON_SHOW_FIELDS.format(self.widget_name))

  def open_create(self):
    """Click to Create button on Tree View to open new object creation modal.
    Return: lib.page.modal.create_new_object."create_obj_cls"
    """
    _locator_create = (
        By.CSS_SELECTOR,
        self._locators.BUTTON_CREATE.format(self.widget_name))
    base.Button(self._driver, _locator_create).click()
    return self.create_obj_cls(self._driver)

  def open_map(self):
    """Click to Map button on Tree View to open unified mapper modal.
    Return: lib.page.modal.unified_mapper.MapObjectsModal
    """
    _locator_map = (By.CSS_SELECTOR,
                    self._locators.BUTTON_MAP.format(self.widget_name))
    base.Button(self._driver, _locator_map).click()
    return unified_mapper.MapObjectsModal(self._driver, self.obj_name)

  def open_3bbs(self):
    """Click to 3BBS button on Tree View to open tree view 3BBS modal.
    Return: lib.element.tree_view."obj_name"DropdownSettings
    """
    _locator_3bbs = (
        By.CSS_SELECTOR, self._locators.BUTTON_3BBS.format(self.widget_name))
    base.Button(self._driver, _locator_3bbs).click()
    return self.dropdown_settings_cls(
        self._driver, self.obj_name)

  def select_member_by_title(self, title):
    """Select member on Tree View by title.
    Return: lib.page.widget.info_widget."obj_name"
    """
    item_num = self._get_item_num_by_title(title)
    return Widget(self._driver, self.obj_name).select_member_by_num(item_num)

  def _get_item_num_by_title(self, title):
    """Return number of item by title"""
    list_items = [item.text.splitlines() for item in
                  self.tree_view_items_elements()]
    item_num = next(num for num, item in enumerate(list_items)
                    if title in item)
    return item_num

  def open_tree_actions_dropdown_by_title(self, title):
    """Open dropdown of obj on Tree View by title. Hover mouse on dropdown
    button.
    Return: lib.element.tree_view."dropdown_obj"
    """
    button_num = self._get_item_num_by_title(title)
    item_dropdown_button = self.tree_view_items()[button_num].item_btn
    selenium_utils.hover_over_element(
        self._driver, item_dropdown_button)
    return self.dropdown_tree_view_item_cls(self._driver, self.obj_name,
                                            item_dropdown_button)


class Audits(Widget):
  """Model for Audits generic widgets."""


class AssessmentTemplates(Widget):
  """Model for Assessment Templates generic widgets."""


class Assessments(Widget):
  """Model for Assessments generic widgets."""


class Controls(Widget):
  """Model for Controls generic widgets."""


class Issues(Widget):
  """Model for Issues generic widgets"""


class Programs(Widget):
  """Model for Programs generic widgets"""


class Processes(Widget):
  """Model for Process generic widgets."""


class DataAssets(Widget):
  """Model for Data Assets generic widgets."""


class Systems(Widget):
  """Model for Systems generic widgets."""


class Products(Widget):
  """Model for Products generic widgets."""


class Projects(Widget):
  """Model for Projects generic widgets."""
