# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Models for widgets other than the info widget."""

import re
from selenium.common import exceptions
from selenium.webdriver.common.by import By

from lib import base, environment
from lib.constants import locator, url, regex, element
from lib.page.modal import base as modal_base
from lib.page.modal.create_new_object import (
    AssessmentTemplates as new_asmt_tmpls, Assessments as new_asmts,
    AssessmentsGenerate as new_asmts_gen)
from lib.page.widget import info_widget
from lib.utils import selenium_utils


class Widget(base.Widget):
  """Class representing all widgets with filters that list objects."""
  _info_pane_cls = None
  _locator_widget = None
  _locator_filter = None
  members_listed = None

  def __init__(self, driver):
    # wait for the elements to load
    self.member_count = None
    self.label_filter = base.Label(driver, self._locator_filter.TITLE)
    self.button_filter_question = base.Button(
        driver, self._locator_filter.BUTTON_HELP)
    self.filter = base.Filter(
        driver,
        self._locator_filter.TEXTFIELD,
        self._locator_filter.BUTTON_SUBMIT,
        self._locator_filter.BUTTON_RESET)

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
      selenium_utils.get_when_visible(
          self._driver,
          locator.ObjectWidget.MEMBERS_TITLE_LIST)

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
    selenium_utils.get_when_invisible(
        self._driver,
        locator.BaseWidgetGeneric.FILTER_PANE_COUNTER)

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


class TreeView(base.TreeView):
  """Class representing genetic widgets tree views."""
  _locators = locator.TreeView

  def __init__(self, driver, widget_name):
    """
    Args:
        driver (CustomDriver)
        widget_name (#widget_name according URL)
    """
    super(TreeView, self).__init__(driver, widget_name)
    self.widget_name = widget_name
    self.button_create = None
    self.button_3bbs = None
    self.button_generate = None
    self.button_set_fields = None
    self.visible_fields = modal_base.SetFieldsModal(
        driver, widget_name=self.widget_name)

  def open_create_obj(self):
    """Open modal from tree view to create new object."""
    _locator_create = (By.CSS_SELECTOR, self._locators.BUTTON_CREATE.
                       format(self.widget_name))
    self.button_create = base.Button(self._driver, _locator_create)
    self.button_create.click()

  def open_3bbs(self):
    """Click to 3bbs button to open modal for further selection of actions."""
    _locator_3bbs = (By.CSS_SELECTOR, self._locators.BUTTON_3BBS.
                     format(self.widget_name))
    self.button_3bbs = base.Button(self._driver, _locator_3bbs)
    self.button_3bbs.click()

  def open_generate_objs(self):
    """Open modal previously clicked to 3bbs button from tree view to generate
    new object(s).
    """
    self.open_3bbs()
    _locator_generate = (By.CSS_SELECTOR, self._locators.BUTTON_GENERATE.
                         format(self.widget_name))
    self.button_generate = base.Button(self._driver, _locator_generate)
    self.button_generate.click()

  def open_set_fields(self):
    """Open modal previously clicked to 3bbs button from tree view to set
    visible fields for represent tree view objects.
    """
    self.open_3bbs()
    _locator_set_fields = (By.CSS_SELECTOR, self._locators.BUTTON_SET_FIELDS.
                           format(self.widget_name))
    self.button_set_fields = base.Button(self._driver, _locator_set_fields)
    self.button_set_fields.click()

  def create_obj(self, new_obj):
    """Create new object from widget used tree view."""
    self.open_create_obj()
    return new_obj(self._driver)

  def generate_objs(self, new_obj):
    """Create new object(s) from widget used tree view."""
    self.open_generate_objs()
    return new_obj(self._driver)

  def set_visible_fields_for_objs(self, fields):
    """Set and save visible fields to display objects on tree view."""
    self.open_set_fields()
    self.visible_fields.set_and_save_visible_fields(fields)

  def get_objs_as_list_of_dicts(self, fields):
    """Get list of dicts from objects (text scopes) which displayed on
    tree view at the widget according set of visible fields.
    """
    header = [_item.text.splitlines()[:len(fields)] for
              _item in self.tree_view_header_elements()]
    items = [_item.text.splitlines()[:len(fields)] for
             _item in self.tree_view_items_elements()]
    return [dict(zip(header[0], item)) for item in items]


class AsmtTmpls(Widget):
  """Model for the Assessment Templates widget."""
  _info_pane_cls = info_widget.AssessmentTemplates
  _locator_widget = locator.WidgetBar.ASSESSMENT_TEMPLATES
  _locator_filter = locator.WidgetAssessmentTemplates
  _asmt_tmpls_fields = (
      element.AsmtTmplModalSetVisibleFields.DEFAULT_SET_FIELDS)

  URL = environment.APP_URL + url.AUDIT.format({}) + (
      _locator_filter.widget_name)

  def __init__(self, driver):
    super(AsmtTmpls, self).__init__(driver)
    self.tree_view = TreeView(driver,
                              widget_name=self._locator_filter.widget_name)

  def create(self):
    """Create assessment template from widget."""
    return self.tree_view.create_obj(new_asmt_tmpls)

  def set_visible_fields(self):
    """Set visible fields for display assessment templates on tree view."""
    self.tree_view.set_visible_fields_for_objs(self._asmt_tmpls_fields)

  def get_list_of_objs_scopes(self):
    """Get list of assessment templates scopes which displayed on tree view."""
    self.set_visible_fields()
    return self.tree_view.get_objs_as_list_of_dicts(self._asmt_tmpls_fields)


class Asmts(Widget):
  """Model for the Assessments widget."""
  _info_pane_cls = info_widget.Assessments
  _locator_widget = locator.WidgetBar.ASSESSMENTS
  _locator_filter = locator.WidgetAssessments
  _asmts_fields = element.AsmtModalSetVisibleFields.DEFAULT_SET_FIELDS

  URL = environment.APP_URL + url.AUDIT.format({}) + (
      _locator_filter.widget_name)

  def __init__(self, driver):
    super(Asmts, self).__init__(driver)
    self.tree_view = TreeView(driver,
                              widget_name=self._locator_filter.widget_name)

  def create(self):
    """Create assessment from widget."""
    return self.tree_view.create_obj(new_asmts)

  def generate(self):
    """Generate assessment(s) from widget."""
    return self.tree_view.generate_objs(new_asmts_gen)

  def set_visible_fields(self):
    """Set visible fields for display assessments on tree view."""
    self.tree_view.set_visible_fields_for_objs(self._asmts_fields)

  def get_list_of_objs_scopes(self):
    """Get list of assessments scopes which displayed on tree view."""
    self.set_visible_fields()
    return self.tree_view.get_objs_as_list_of_dicts(self._asmts_fields)


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
