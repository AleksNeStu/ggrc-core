# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Models for widgets other than the info widget"""

import re

from selenium.common import exceptions

from lib import base
from lib.page.widget import info_widget
from lib.constants import locator
from lib.constants import regex
from lib.utils import selenium_utils


class Widget(base.Widget):
  """Class representing all widgets with filters that list objects"""
  _info_pane_cls = None
  _locator_widget = None
  _locator_filter = None
  members_listed = None

  def __init__(self, driver):
    # wait for the elements to load
    self.member_count = None
    self.filter = base.Filter(
        driver, text_box=self._locator_filter.TEXTFIELD_TO_FILTER,
        bt_filter=self._locator_filter.BUTTON_FILTER,
        bt_reset=self._locator_filter.BUTTON_RESET,
        bt_help=self._locator_filter.BUTTON_HELP,
        ch_active=self._locator_filter.ACTIVE_CHECKBOX,
        ch_draft=self._locator_filter.DRAFT_CHECKBOX,
        ch_deprecated=self._locator_filter.CHECKBOX_DEPRECATED
    )
    self.filter.show_all_objs()

    super(Widget, self).__init__(driver)
    self._set_members_listed()

  def _set_member_count(self):
    """Parses the widget name and number of items from the widget tab title"""
    widget_label = selenium_utils.get_when_visible(
        self._driver, self._locator_widget).text

    # The widget label has 2 forms: "widget_name_plural (number_of_items)"
    # and "number_of_items" and they change depending on how many widgets
    # are open. In order to handle both forms, we first try to parse the
    # first form and only then the second one.
    parsed_label = re.match(
        regex.WIDGET_TITLE_AND_COUNT, widget_label)

    item_count = widget_label \
        if parsed_label is None \
        else parsed_label.group(2)
    self.member_count = int(item_count)

  def _set_members_listed(self):
    """Waits for the listed members to be loaded and adds them to a local
    container"""
    self._set_member_count()

    if self.member_count:
      # wait until the elements are loaded
      selenium_utils.get_when_invisible(
          self._driver,
          locator.ObjectWidget.LOADING)
      # selenium_utils.get_when_visible(
      #     self._driver,
      #     locator.ObjectWidget.MEMBERS_TITLE_LIST)

      self.members_listed = self._driver.find_elements(
          *locator.ObjectWidget.MEMBERS_TITLE_LIST)
    else:
      self.members_listed = []

  def wait_for_counter_loaded(self):
    """Waits for elements' counter on the filter pane to be visible"""
    return selenium_utils.get_when_visible(
        self._driver,
        locator.BaseWidgetGeneric.FILTER_PANE_COUNTER)

  def verify_counter_not_loaded(self):
    """
    Checks that in case of empty table,
    counter is not loaded on the filter pane
    """
    selenium_utils.wait_for_element_text(
        self._driver,
        locator.BaseWidgetGeneric.FILTER_PANE_COUNTER, "No records")

  def get_items_count(self):
    """Gets elements' count from counter on the filter pane """
    return self.wait_for_counter_loaded().text.split()[2]

  def wait_member_deleted(self, count):
    """
    Waits until elements' counter on the filter pane
    is refreshed with new value.
        Args:
            count (str)
    """
    if count != '1':
      new_count = ' {} '.format(int(count) - 1)
      selenium_utils.wait_for_element_text(
          self._driver,
          locator.BaseWidgetGeneric.FILTER_PANE_COUNTER,
          new_count)
    else:
        self.verify_counter_not_loaded()

  def select_nth_member(self, member):
    """Selects member from the list. Members start from (including) 0.

    Args:
        member (int)

    Returns:
        lib.page.widget.info.Widget
    """
    try:
      element = self.members_listed[member]

      # wait for the listed items animation to stop
      selenium_utils.wait_until_stops_moving(element)
      element.click()

      # wait for the info pane animation to stop
      info_pane = selenium_utils.get_when_clickable(
          self._driver, locator.ObjectWidget.INFO_PANE)
      selenium_utils.wait_until_stops_moving(info_pane)

      return self._info_pane_cls(self._driver)
    except exceptions.StaleElementReferenceException:
      self.members_listed = self._driver.find_elements(
          *locator.ObjectWidget.MEMBERS_TITLE_LIST)
      return self.select_nth_member(member)
    except exceptions.TimeoutException:
      # sometimes the click to the listed member results in hover
      return self.select_nth_member(member)


class Controls(Widget):
  """Model for the control widget"""
  _info_pane_cls = info_widget.Controls
  _locator_widget = locator.WidgetBar.CONTROLS
  _locator_filter = locator.WidgetControls

  def __init__(self, driver,):
    super(Controls, self).__init__(driver)
    self.label_title = base.Label(
        driver,
        locator.ObjectWidget.CONTROL_COLUMN_TITLE)
    self.label_owner = base.Label(driver, locator.ObjectWidget.CONTROL_OWNER)
    self.label_state = base.Label(driver, locator.ObjectWidget.COTNROL_STATE)


class Issues(Widget):
  """Model for the issue widget"""
  _info_pane_cls = info_widget.Issues
  _locator_widget = locator.WidgetBar.ISSUES
  _locator_filter = locator.WidgetIssues


class Processes(Widget):
  """Model for the process widget"""
  _info_pane_cls = info_widget.Processes
  _locator_widget = locator.WidgetBar.PROCESSES
  _locator_filter = locator.WidgetProcesses


class DataAssets(Widget):
  """Model for the data asset widget"""
  _info_pane_cls = info_widget.DataAssets
  _locator_widget = locator.WidgetBar.DATA_ASSETS
  _locator_filter = locator.WidgetDataAssets


class Systems(Widget):
  """Model for the system widget"""
  _info_pane_cls = info_widget.Systems
  _locator_widget = locator.WidgetBar.SYSTEMS
  _locator_filter = locator.WidgetSystems


class Products(Widget):
  """Model for the product widget"""
  _info_pane_cls = info_widget.Products
  _locator_widget = locator.WidgetBar.PRODUCTS
  _locator_filter = locator.WidgetProducts


class Projects(Widget):
  """Model for the project widget"""
  _info_pane_cls = info_widget.Projects
  _locator_widget = locator.WidgetBar.PROJECTS
  _locator_filter = locator.WidgetProjects
