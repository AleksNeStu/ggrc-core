# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Base classes."""
# pylint: disable=too-few-public-methods

import re

from selenium import webdriver
from selenium.common import exceptions
from selenium.webdriver.common import keys
from selenium.webdriver.common.by import By

from lib import constants, exception, mixin
from lib.constants import url
from lib.constants.element import MappingStatusAttrs
from lib.constants.test import batch
from lib.utils import selenium_utils, string_utils


class InstanceRepresentation(object):
  def __repr__(self):
    return str(
        {key: value for key, value in self.__dict__.items()
         if "__" not in key})


class CustomDriver(webdriver.Chrome):
  """Extension to web driver."""

  def find_elements_by_visible_locator(self, locator):
    """Sometimes we have to find in list of elements only that one that is
    visible to user.
    Args: locator (tuple)
    Return: selenium.webdriver.remote.webelement.WebElement
    Raises: exception.ElementNotFound
    """
    # pylint: disable=invalid-name
    elements = self.find_elements(*locator)
    for element in elements:
      if element.is_displayed():
        return element
    raise exception.ElementNotFound(locator)


class Test(InstanceRepresentation):
  __metaclass__ = mixin.MetaTestDecorator


class TestUtil(InstanceRepresentation):
  """Abstract class for all test util classes."""


class Element(InstanceRepresentation):
  """Element class represents primitives in models. Initializing by web driver
  and locator (CSS selector (tuple) or webelement element (instance
  of webdriver.Chrome).
  """

  def __init__(self, driver, locator):
    super(Element, self).__init__()
    self._driver = driver
    self._locator = locator
    self.element = (
        locator if isinstance(locator, webdriver.remote.webelement.WebElement)
        else self.get_element())
    self.text = self.element.text

  def get_element(self):
    """
    Return: selenium.webdriver.remote.webelement.WebElement
    """
    return selenium_utils.get_when_visible(self._driver, self._locator)

  def click(self):
    """Click on element."""
    self.element.click()

  def click_via_js(self):
    """Click on element using JS."""
    selenium_utils.click_via_js(self._driver, self.element)

  def click_when_visible(self):
    """Wait for element to be visible and only then performs click."""
    selenium_utils.get_when_visible(self._driver, self._locator).click()


class Label(Element):
  """Generic label."""


class RichTextInputField(Element):
  """Common class for representation of Rich Text input."""
  def __init__(self, driver, locator):
    """
    Args: driver (CustomDriver):
    """
    super(RichTextInputField, self).__init__(driver, locator)
    self._driver = driver
    self._locator = locator
    self.text = self.element.text

  def enter_text(self, text):
    """Clear fields and enteres text."""
    self.click_when_visible()
    self.element.clear()
    self.element.send_keys(text)
    self.text = text

  def paste_from_clipboard(self, element):
    """
    Paste value from clipboard into text input element.
    Details:
    We want to update value of this element after pasting. In order to
    do that, we click on another element.
    Args: element (Element)
    """
    self.element.clear()
    self.element.send_keys(keys.Keys.CONTROL, 'v')
    element.click()
    element = self._driver.find_element(*self._locator)
    self.text = element.get_attribute("value")


class TextInputField(RichTextInputField):
  """Generic model for text input field."""


class TextFilterDropdown(Element):
  """Model for elements which are using autocomplete in text field with
 dropdown list of found results and static dropdown list of text elements.
 """

  def __init__(self, driver, textbox_locator, dropdown_locator):
    super(TextFilterDropdown, self).__init__(driver, textbox_locator)
    self._locator_dropdown = dropdown_locator
    self._elements_dropdown = None
    self.text_to_filter = None

  def _filter_results(self, text):
    """Insert text into textbox field."""
    self.text_to_filter = text
    self.element.click()
    self.element.clear()
    self._driver.find_element(*self._locator).send_keys(text)

  def _select_first_result(self):
    """Wait when dropdown elements appear and select first one."""
    for _ in xrange(batch.TRY_COUNT):
      try:
        selenium_utils.get_when_visible(self._driver, self._locator_dropdown)
        dropdown_elements = self._driver.find_elements(*self._locator_dropdown)
        self.text = dropdown_elements[0].text
        dropdown_elements[0].click()
        break
      except exceptions.StaleElementReferenceException:
        pass

  def filter_and_select_el_by_text(self, text):
    """Make filtering and select first filtered text element in dropdown."""
    self._filter_results(text)
    self._select_first_result()

  def find_and_select_el_by_text(self, text):
    """Find and select text element in dropdown by text."""
    self.text_to_filter = text
    self.element.click()


class Iframe(Element):
  """Iframe element methods."""

  def find_iframe_and_enter_data(self, text):
    """
    Args: text (basestring): string want to enter
    """
    iframe = selenium_utils.get_when_visible(self._driver, self._locator)
    self._driver.switch_to.frame(iframe)
    element = self._driver.find_element_by_tag_name("body")
    element.clear()
    element.send_keys(text)
    self._driver.switch_to.default_content()
    self.text = text


class DatePicker(Element):
  """Date picker element methods."""

  def __init__(self, driver, date_picker_locator, field_locator):
    """
    Args:
    date_picker_locator (tuple)
    field_locator (tuple): locator of field we have to click on to
    activate date picker
    """
    super(DatePicker, self).__init__(driver, field_locator)
    self._locator_datepcker = date_picker_locator
    self._element_datepicker = None

  def get_day_els_current_month(self):
    """Get day elements for current month.
    Return: list of selenium.webdriver.remote.webelement.WebElement
    """
    self.element.click()
    elements = self._driver.find_elements(*self._locator_datepcker)
    return elements

  def select_day_in_current_month(self, day):
    """Select day - sequential element from date picker. Days go from 0 to
    28,29 or 30, depending on current month. Since we're selecting an element
    from list, we can pass e.g. -1 to select last day in month.
    Args: day (int)
    """
    elements = self.get_day_els_current_month()
    elements[day].click()
    # wait for fadeout in case we're above some other element
    selenium_utils.get_when_invisible(self._driver, self._locator_datepcker)
    self.text = self.element.get_attribute("value")

  def select_month_end(self):
    """Select last day of current month."""
    elements = self.get_day_els_current_month()
    elements[-1].click()
    # wait for fadeout in case we're above some other element
    selenium_utils.get_when_invisible(self._driver, self._locator_datepcker)
    self.text = self.element.get_attribute("value")

  def select_month_start(self):
    """Select first day of current month."""
    elements = self.get_day_els_current_month()
    elements[0].click()
    # wait for fadeout in case we're above some other element
    selenium_utils.get_when_invisible(self._driver, self._locator_datepcker)
    self.text = self.element.get_attribute("value")


class Button(Element):
  """Generic button element."""

  def get_element(self):
    return selenium_utils.get_when_clickable(self._driver, self._locator)


class Checkbox(Element):
  """Generic checkbox element."""

  def __init__(self, driver, locator):
    super(Checkbox, self).__init__(driver, locator)
    self.is_checked = self.element.is_selected()

  def get_element(self):
    """Get checkbox when web element clickable."""
    return selenium_utils.get_when_clickable(self._driver, self._locator)

  def check(self):
    """Select checkbox."""
    if not self.is_checked:
      self.element.click()

  def uncheck(self):
    """Unselect checkbox."""
    if self.is_checked:
      self.element.click()

  def is_element_checked(self):
    """Check DOM input element checked property using JS.
    Args: driver (base.CustomDriver), locator (tuple)
    Return: True if element is checked, False if element is not checked.
    """
    return self._driver.execute_script("return arguments[0].checked",
                                       self.element)


class Toggle(Element):
  """Generic toggle element.
 Note that special function is used for detecting if element is active
 which may not work on an arbitrary element.
 """

  def __init__(self, driver, locator, is_active_attr_val="active"):
    super(Toggle, self).__init__(driver, locator)
    self.is_activated = selenium_utils.is_value_in_attr(
        self.element, value=is_active_attr_val)

  def get_element(self):
    return selenium_utils.get_when_clickable(self._driver, self._locator)

  def toggle(self, on_el=True):
    """Click on element based on is_active status and "on" arg.
    Args: on_el (bool)
    """
    if on_el and not self.is_activated:
      self.element.click()
      self.is_activated = True
    elif not on_el and self.is_activated:
      self.element.click()
      self.is_activated = False


class Tab(Element):
  """Generic element representing tab."""
  def __init__(self, driver, locator, is_activated=True):
    super(Tab, self).__init__(driver, locator)
    self.is_activated = is_activated

  def get_element(self):
    return selenium_utils.get_when_clickable(self._driver, self._locator)

  def click(self):
    """When clicking on tab to first make sure it's clickable i.e.
    that this element will receive click."""
    selenium_utils.get_when_clickable(self._driver, self._locator).click()
    self.is_activated = True


class Dropdown(Element):
  """Generic dropdown."""


class DropdownStatic(Element):
  """Dropdown with predefined static elements."""

  def __init__(self, driver, dropdown_locator, elements_locator):
    """
    Args: driver (CustomDriver)
    """
    super(DropdownStatic, self).__init__(driver, dropdown_locator)
    self._locator_dropdown_elements = elements_locator
    self.elements_dropdown = self._driver.find_elements(
        *self._locator_dropdown_elements)

  def click(self):
    self.element.click()

  def select(self, member_name):
    """Selects dropdown element based on dropdown element name."""
    for element in self.elements_dropdown:
      if element.get_attribute("value") == member_name:
        element.click()
        break
    else:
      exception.ElementNotFound(member_name)


class Component(InstanceRepresentation):
  """Component class is container for elements."""

  def __init__(self, driver):
    """
    Args: driver (CustomDriver)
    """
    self._driver = driver
    if driver.title:  # only Login page doesn't have title and jQuery
      selenium_utils.wait_for_js_to_load(driver)


class AnimatedComponent(Component):
  """Class for components where animation must first complete before
 elements are visible."""

  def __init__(self, driver, locators_to_check, wait_until_visible):
    """
    Args:
    driver (CustomDriver)
    locators_to_check (list of tuples): locators to wait for to become
    (in)visible
    wait_until_visible (bool): for all elements to be visible do we
    have to wait for certain elements to be invisible or visible?
    """
    super(AnimatedComponent, self).__init__(driver)
    self._locators = locators_to_check
    if wait_until_visible:
      self._wait_until_visible()
    else:
      self._wait_until_invisible()

  def _wait_until_visible(self):
    for item_locator in self._locators:
      selenium_utils.get_when_visible(self._driver, item_locator)

  def _wait_until_invisible(self):
    for item_locator in self._locators:
      selenium_utils.get_when_invisible(self._driver, item_locator)


class Modal(Component):
  """Generic modal element."""


class FilterCommon(Component):
  """Common filter elements for LHN and Tree View."""

  def __init__(self, driver, text_box_locator, bt_submit_locator,
               bt_clear_locator):
    super(FilterCommon, self).__init__(driver)
    self.text_box = TextInputField(driver, text_box_locator)
    self.button_submit = Button(driver, bt_submit_locator)
    # for LHN the clear button is only visible after a query is entered
    self.button_clear = driver.find_element(*bt_clear_locator)

  def enter_query(self, query):
    """Enter query to field."""
    self.text_box.enter_text(query)

  def submit_query(self):
    """Submit query that was entered to field."""
    self.button_submit.click()
    selenium_utils.wait_for_js_to_load(self._driver)

  def clear_query(self):
    """Clear query that was entered to field."""
    self.button_clear.click()
    selenium_utils.wait_for_js_to_load(self._driver)

  def perform_query(self, query):
    """Clear filtering field, enter query and click submit."""
    self.enter_query(query)
    self.submit_query()


class AbstractPage(Component):
  """Represent page that can be navigate to, but we don't necessarily know
 it's url in advance."""

  def __init__(self, driver):
    """
    Args: driver (CustomDriver)
    """
    super(AbstractPage, self).__init__(driver)
    self.url = driver.current_url

  def navigate_to(self, custom_url=None):
    """Navigate to url."""
    url_to_use = self.url if custom_url is None else custom_url
    selenium_utils.open_url(self._driver, url_to_use)
    return self


class Page(AbstractPage):
  """Page class represents components with special properties i.e. they
 have *static* URL-s, can be navigated to etc."""
  URL = None

  def __init__(self, driver):
    """
    Args: driver (CustomDriver)
    """
    super(Page, self).__init__(driver)
    self.navigate_to(self.URL)


class DropdownDynamic(AnimatedComponent):
  """Dropdown that doesn't load all contents at once."""

  def __init__(self, driver, locators_to_check, wait_until_visible):
    """
    Args:
    driver (CustomDriver)
    locators_to_check (list of tuples): locators to wait for to become
    (in)visible
    wait_until_visible (bool): for all elements to be visible do we
    have to wait for certain elements to be invisible or visible?
    """
    super(DropdownDynamic, self).__init__(driver, locators_to_check,
                                          wait_until_visible)
    self.members_visible = None
    self.members_loaded = None

  def _update_loaded_members(self):
    """New members that are loaded are added to members_loaded container."""
    raise NotImplementedError

  def _set_visible_members(self):
    """When moving in dropdown it can happen we don't always see all
    the members. Here we set members, that are visible to user."""
    raise NotImplementedError

  def scroll_down(self):
    raise NotImplementedError

  def scroll_up(self):
    raise NotImplementedError


class Selectable(Element):
  """Representing list of elements that are selectable."""


class Widget(AbstractPage):
  """Page like class for which we don't know initial url."""

  def __init__(self, driver):
    """
    Args: driver (CustomDriver)
    """
    super(Widget, self).__init__(driver)
    matched_url_parts = re.search(
        constants.regex.URL_WIDGET_INFO, self.url + "/").groups()
    (source_obj_plural, source_obj_id, widget_name,
     mapped_obj_singular, mapped_obj_id) = matched_url_parts
    self.source_obj_from_url = source_obj_plural

    self.source_obj_id_from_url = source_obj_id
    self.widget_name_from_url = (widget_name.split("_")[0] or
                                 constants.element.WidgetBar.INFO)
    self.mapped_obj_from_url = mapped_obj_singular
    self.mapped_obj_id_from_url = mapped_obj_id


class TreeView(Component):
  """Common class for representing Tree View list with several objects."""
  # pylint: disable=too-many-instance-attributes
  _locators = constants.locator.TreeView

  def __init__(self, driver, obj_name=None):
    super(TreeView, self).__init__(driver)
    self._tree_view_header_elements = []
    self._tree_view_items_elements = []
    self._tree_view_items = []
    self.locator_set_visible_fields = None
    self.locator_no_results_message = self._locators.NO_RESULTS_MESSAGE
    self.obj_name = obj_name
    if self.obj_name is not None:
      self.widget_name = url.get_widget_name_of_mapped_objs(obj_name)
      from lib import factory
      self.fields_to_set = factory.get_fields_to_set(object_name=self.obj_name)

  def wait_loading_after_actions(self):
    """Wait loading elements of Tree View after made some action with
    object(s) under Tree View.
    """
    selenium_utils.wait_until_not_present(
        self._driver, self._locators.ITEM_LOADING)
    selenium_utils.get_when_invisible(self._driver, self._locators.SPINNER)
    selenium_utils.wait_for_js_to_load(self._driver)

  def get_tree_view_header_elements(self):
    """Get Tree View header as list of elements from current widget."""
    _locator_header = (By.CSS_SELECTOR, self._locators.HEADER)
    self._tree_view_header_elements = selenium_utils.get_when_all_visible(
        self._driver, _locator_header)

  def get_tree_view_items_elements(self):
    """Get Tree View items as list of elements from current widget.
    If no items in tree view return empty list.
    """
    _locator_items = (
        By.CSS_SELECTOR, self._locators.ITEMS)
    self.wait_loading_after_actions()
    has_no_record_found = selenium_utils.is_element_exist(
        self._driver, self.locator_no_results_message)
    self._tree_view_items_elements = (
        [] if has_no_record_found else
        selenium_utils.get_when_all_visible(self._driver, _locator_items))
    return self._tree_view_items_elements

  def set_tree_view_items(self):
    """Set Tree View items as list of Tree View item objects from current
    widget.
    """
    self.get_tree_view_items_elements()
    self._tree_view_items = [
        TreeViewItem(
            driver=self._driver, text=el.text,
            item_btn=el.find_element(
                By.CSS_SELECTOR, self._locators.ITEM_EXPAND_BUTTON)) for el in
        self._tree_view_items_elements]

  def tree_view_header_elements(self):
    """Return Tree View header as list of elements from current widget."""
    if not self._tree_view_header_elements:
      self.get_tree_view_header_elements()
    return self._tree_view_header_elements

  def tree_view_items_elements(self):
    """Return Tree View items as list of elements from current widget."""
    if not self._tree_view_items_elements:
      self.get_tree_view_items_elements()
    return self._tree_view_items_elements

  def tree_view_items(self):
    """Return Tree View items as list of Tree View item objects from
    current widget.
    """
    if not self._tree_view_items:
      self.set_tree_view_items()
    return self._tree_view_items

  def open_set_visible_fields(self):
    """Click to Set Visible Fields button on Tree View to open
    Set Visible Fields modal.
    Return: lib.page.modal.set_fields.SetVisibleFieldsModal
    """
    _locator_set_visible_fields = self.locator_set_visible_fields
    Button(self._driver, _locator_set_visible_fields).click()
    return SetVisibleFieldsModal(self._driver, self.fields_to_set)

  def get_list_members_as_list_scopes(self):
    """Get list of scopes (dicts) from members (text scopes) which displayed on
    Tree View according to current set of visible fields.
    """
    if self.get_tree_view_items_elements():
      list_headers = [_item.text.splitlines()[:len(self.fields_to_set)] for
                      _item in self.tree_view_header_elements()]
      list_lists_items = [_item.text.splitlines()[:len(self.fields_to_set)] for
                          _item in self.tree_view_items_elements()]
      return [dict(zip(list_headers[0], item)) for item in list_lists_items]
    return self._tree_view_items_elements


class UnifiedMapperTreeView(TreeView):
  """Tree-View class for Unified Mapper"""
  _locators = constants.locator.UnifiedMapperTreeView

  def __init__(self, driver, obj_name):
    super(UnifiedMapperTreeView, self).__init__(driver, obj_name=obj_name)
    self.locator_set_visible_fields = (By.CSS_SELECTOR,
                                       self._locators.BUTTON_SHOW_FIELDS)
    self.locator_no_results_message = (By.CSS_SELECTOR,
                                       self._locators.NO_RESULTS_MESSAGE)

  def open_set_visible_fields(self):
    """Click to Set Visible Fields button on Tree View to open
    Set Visible Fields modal.
    Return: lib.page.modal.set_fields.SetVisibleFieldsModal
    """
    _locator_set_visible_fields = self.locator_set_visible_fields
    Button(self._driver, _locator_set_visible_fields).click()
    return MapperSetVisibleFieldsModal(self._driver, self.fields_to_set)


class AdminTreeView(TreeView):
  """Class for representing Tree View list in Admin dashboard."""
  _locators = constants.locator.AdminTreeView

  def __init__(self, driver, widget_name):
    super(AdminTreeView, self).__init__(driver)
    self.widget_name = widget_name


class SetVisibleFieldsModal(Modal):
  """Modal to select and set visible fields for objects to represent them on
  Tree View."""
  _locators = constants.locator.ModalSetVisibleFields

  def __init__(self, driver, fields_to_set):
    super(SetVisibleFieldsModal, self).__init__(driver)
    self.fields_to_set = fields_to_set
    self.visible_fields_elements = None

  def select_visible_fields(self):
    """Select visible fields checkboxes on Select Visible Fields modal
    according to titles of fields to set."""
    # pylint: disable=attribute-defined-outside-init
    _locator_modal_fields = (By.CSS_SELECTOR,
                             self._locators.MODAL)
    _locator_fields_titles = (
        By.CSS_SELECTOR,
        self._locators.FIELDS_TITLES)
    _locator_fields_checkboxes = (
        By.CSS_SELECTOR,
        self._locators.FIELDS_CHECKBOXES)
    selenium_utils.get_when_visible(self._driver, _locator_modal_fields)
    self.visible_fields_elements = ListCheckboxes(
        self._driver, titles_locator=_locator_fields_titles,
        checkboxes_locator=_locator_fields_checkboxes)
    self.visible_fields_elements.select_by_titles(self.fields_to_set)

  def confirm_set_visible_fields(self):
    """Confirm set visible fields."""
    _locator_set_fields = (
        By.CSS_SELECTOR,
        self._locators.BUTTON_SET_FIELDS)
    Button(self._driver, _locator_set_fields).click_via_js()  # issue GGRC-1854
    selenium_utils.get_when_invisible(self._driver, _locator_set_fields)

  def select_and_set_visible_fields(self):
    """Select checkboxes to set objects visible fields and confirm set."""
    self.select_visible_fields()
    self.confirm_set_visible_fields()


class MapperSetVisibleFieldsModal(SetVisibleFieldsModal):
  """Modal to select and set visible fields for objects to represent them on
  Tree View."""
  _locators = constants.locator.ModalSetVisibleFieldsMapper


class TreeViewItem(Component):
  """Class for describing single item on Tree View."""
  def __init__(self, driver, text=None, item_btn=None):
    super(TreeViewItem, self).__init__(driver)
    self.text = text
    self.item_btn = item_btn

  def expand(self):
    """Expand Tree View item if it is not expanded already."""
    from lib.page.widget.widget_base import CustomAttributesItemContent
    if not self.is_expanded:
      self.item_btn.click()
      selenium_utils.wait_until_stops_moving(self.item_btn)
    return CustomAttributesItemContent(self._driver, self.text)

  def collapse(self):
    """Collapse Tree View item if it is expanded."""
    if self.is_expanded:
      self.item_btn.click()
      selenium_utils.wait_until_stops_moving(self.item_btn)

  @property
  def is_expanded(self):
    return selenium_utils.is_value_in_attr(self.item_btn)


class ListCheckboxes(Component):
  """Generic list of checkboxes elements."""

  def __init__(self, driver, titles_locator, checkboxes_locator):
    super(ListCheckboxes, self).__init__(driver)
    self.locator_titles = titles_locator
    self.locator_checkboxes = checkboxes_locator

  @staticmethod
  def _unselect_unnecessary(objs, list_titles):
    """Unselect unnecessary elements according objs (titles and checkboxes
    elements) and list of titles."""
    unselect = [obj[1].click() for obj in objs
                if obj[0].text not in list_titles if obj[1].is_selected()]
    return unselect

  @staticmethod
  def _select_necessary(objs, list_titles):
    """Select necessary elements according objs (titles and checkboxes
    elements) and list of titles."""
    select = [obj[1].click() for obj in objs
              if obj[0].text in list_titles if not obj[1].is_selected()]
    return select

  def select_by_titles(self, list_titles):
    """Select checkboxes according titles."""
    selenium_utils.wait_for_js_to_load(self._driver)
    selenium_utils.get_when_all_visible(self._driver, self.locator_titles)
    objs_titles = self._driver.find_elements(*self.locator_titles)
    objs_checkboxes = self._driver.find_elements(*self.locator_checkboxes)
    objs = zip(objs_titles, objs_checkboxes)
    self._unselect_unnecessary(objs, list_titles)
    self._select_necessary(objs, list_titles)

  def get_mapping_statuses(self):
    """Get list of mapping statuses by given titles"""
    selenium_utils.get_when_all_visible(self._driver, self.locator_titles)
    objs_titles = self._driver.find_elements(*self.locator_titles)
    objs_checkboxes = self._driver.find_elements(*self.locator_checkboxes)
    objs = [
        MappingStatusAttrs(obj[0], obj[1][0], obj[1][1]) for obj in zip(
            [obj.text for obj in objs_titles],
            [[string_utils.get_bool_from_string(obj.get_attribute("checked")),
              string_utils.get_bool_from_string(obj.get_attribute("disabled"))]
                for obj in objs_checkboxes])]
    return objs


class DropdownMenu(Component):
  """Class for common DropdownMenu Element"""
  _locators = constants.locator.CommonDropdownMenu

  def __init__(self, driver, element_or_locator):
    super(DropdownMenu, self).__init__(driver)
    self._driver = driver
    self.dropdown_element = self._get_dropdown_element(element_or_locator)
    self._dropdown_items = []

  def _get_dropdown_element(self, el_or_loc):
    """Return  DropdownMenu element if element not defined find it by
    locator"""
    element = (el_or_loc if isinstance(
               el_or_loc, webdriver.remote.webelement.WebElement)
               else selenium_utils.get_when_visible(self._driver, el_or_loc))
    return (element if element.tag_name == self._locators.DROPDOWN_MAIN_CSS[1]
            else element.find_element(*self._locators.DROPDOWN_MAIN_CSS))

  def dropdown_items(self):
    """Return list of DropdownMenu Items defined  by "li" tag"""
    if not self._dropdown_items:
      elements_on_dropdown = self.dropdown_element.find_elements(
          *self._locators.DROPDOWN_ITEMS_CSS)
      self._dropdown_items = [DropdownMenuItem(self._driver, el) for el in
                              elements_on_dropdown]
    return self._dropdown_items

  def get_dropdown_item(self, out_item_type):
    """Return DropdownItem element according to type"""
    return next(elem_val for elem_val in self.dropdown_items()
                if out_item_type in elem_val.item_type)

  def is_item_exists(self, out_item_type):
    """Check if element enable on dropdown and return Bool, by comparing
    icon type.
    Return bool
    """
    return any(elem_val.item_type for elem_val in self.dropdown_items()
               if out_item_type in elem_val.item_type)

  def is_item_enabled(self, out_item_type):
    """Check if element enable on dropdown.
    Return bool if element found
    If element not found raise exception
    """
    return self.get_dropdown_item(out_item_type).enabled


class DropdownMenuItem(Element):
  """Class for dropdown item"""
  _locators = constants.locator.CommonDropdownMenu
  _elements = constants.element.DropdownMenuItemTypes

  def __init__(self, driver, locator):
    super(DropdownMenuItem, self).__init__(driver, locator)
    self._enabled = None
    self._item_type = ""

  @property
  def item_type(self):
    """Item type defined by class of icon"""
    if not self._item_type:
      icon = selenium_utils.get_element_by_element_safe(
          self.element, self._locators.DROPDOWN_ITEM_ICON_CSS)
      if icon:
        icon_type = icon.get_attribute("class")
        self._item_type = next(
            (v for k, v in self._elements.__dict__.iteritems()
             if not k.startswith("_") and v in icon_type),
            icon_type)
    return self._item_type

  @property
  def enabled(self):
    """Return True if DropdownMenu Item enabled"""
    if not self._enabled:
      self._enabled = selenium_utils.is_element_enabled(self.element)
    return self._enabled
