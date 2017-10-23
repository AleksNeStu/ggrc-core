# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Base widget models."""
# pylint: disable=not-callable
# pylint: disable=not-an-iterable
# pylint: disable=too-few-public-methods

from lib import base, decorator, environment
from lib.constants import locator, url, objects
from lib.entities.entity import CustomAttributeEntity
from lib.utils import selenium_utils
from lib.utils.string_utils import get_bool_value_from_arg


class _Modal(base.Modal):
  """Base model for Edit modal."""
  _locators = locator.ModalCustomAttribute

  def __init__(self, driver):
    super(_Modal, self).__init__(driver)
    self.ui_attribute_title = base.TextInputField(
        self._driver, self._locators.UI_ATTRIBUTE_TITLE)
    self.button_submit = base.Button(
        self._driver, self._locators.BUTTON_SAVE_AND_CLOSE)

  def enter_title(self, title):
    self.ui_attribute_title.enter_text(title)

  @decorator.handle_alert
  def save_and_close(self):
    """
    Return: WidgetAdminCustomAttributes
    """
    self.button_submit.click()


class CustomAttributesItemContent(base.Component):
  """Model for 2-tier of custom attributes Tree View item."""
  _locators = locator.CustomAttributesItemContent

  def __init__(self, driver, item_text):
    super(CustomAttributesItemContent, self).__init__(driver)
    self.button_add = base.Button(driver, self._locators.ADD_BTN)
    self.custom_attributes_list = []
    self._item_name = item_text

  def add_new_custom_attribute(self, ca_obj):
    """Create Custom Attribute entry based on given Custom Attribute object."""
    ca_modal = self.open_add_new_ca_modal()
    ca_modal.select_type(ca_obj.attribute_type)
    ca_modal.enter_title(ca_obj.title)
    if ca_obj.mandatory:
      ca_modal.set_mandatory()
    if ca_obj.placeholder:
      ca_modal.enter_placeholder(ca_obj.placeholder)
    if ca_obj.helptext:
      ca_modal.enter_inline_help(ca_obj.helptext)
    if ca_obj.multi_choice_options:
      ca_modal.enter_possible_values(ca_obj.multi_choice_options)
    ca_modal.save_and_close()

  def _set_custom_attributes_list(self):
    """Set custom attributes list with Custom Attribute objects from
    current opened content item.
    """
    for row in selenium_utils.get_when_all_visible(self._driver,
                                                   self._locators.ROW):
      attrs = [i.text for i in row.find_elements(*self._locators.CELL_IN_ROW)]
      self.custom_attributes_list.append(
          CustomAttributeEntity(
              title=attrs[0],
              type=objects.get_singular(objects.CUSTOM_ATTRIBUTES),
              attribute_type=attrs[1],
              mandatory=get_bool_value_from_arg(attrs[2]),
              definition_type=self._item_name))

  def get_ca_list_from_group(self):
    """Return list of Custom Attribute objects."""
    self._set_custom_attributes_list()
    return self.custom_attributes_list

  def open_add_new_ca_modal(self):
    """Open Add Attribute modal and return Custom Attribute Modal."""
    selenium_utils.wait_until_stops_moving(self.button_add.element)
    selenium_utils.scroll_into_view(self._driver, self.button_add.element)
    selenium_utils.get_when_clickable(self._driver, self._locators.ADD_BTN)
    selenium_utils.get_when_invisible(
        self._driver, self._locators.TREE_SPINNER_CSS)
    self.button_add.click()
    return CustomAttributeModal(self._driver)

  def select_ca_member_by_num(self, num):
    """Select Custom Attribute member from list of members by number
    (start from 0).
    Args: num (int)
    Return: lib.page.widget.widget_base.CustomAttributeModal
    """
    # check that the buttons are loaded
    selenium_utils.get_when_clickable(self._driver, self._locators.EDIT_BTN)
    elements = self._driver.find_elements(self._locators.EDIT_BTN)
    selenium_utils.scroll_into_view(self._driver, elements[num]).click()
    return CustomAttributeModal(self._driver)


class CustomAttributeModal(_Modal):
  """Custom attribute modal."""
  # pylint: disable=too-many-instance-attributes
  def __init__(self, driver):
    super(CustomAttributeModal, self).__init__(driver)
    self.attribute_title = base.Label(
        self._driver, self._locators.ATTRIBUTE_TITLE)
    self.inline_help = base.Label(self._driver, self._locators.INLINE_HELP)
    self.attribute_type = base.Label(
        self._driver, self._locators.ATTRIBUTE_TYPE)
    self.placeholder = base.Label(self._driver, self._locators.PLACEHOLDER)
    self.mandatory = base.Label(self._driver, self._locators.MANDATORY)
    self.ui_inline_help = None
    self.ui_placeholder = None
    self.checkbox_mandatory = base.Checkbox(
        self._driver, self._locators.CHECKBOX_MANDATORY)
    self.attribute_type_selector = base.DropdownStatic(
        self._driver, self._locators.ATTRIBUTE_TYPE_SELECTOR)
    self.ui_possible_values = None

  def enter_inline_help(self, inline_help):
    """Fill 'Inline help' field."""
    self.ui_inline_help = base.TextInputField(
        self._driver, self._locators.UI_INLINE_HELP)
    self.ui_inline_help.enter_text(inline_help)

  def enter_placeholder(self, placeholder):
    """Fill 'Placeholder' field."""
    self.ui_placeholder = base.TextInputField(
        self._driver, self._locators.UI_PLACEHOLDER)
    self.ui_placeholder.enter_text(placeholder)

  def set_mandatory(self):
    """Check 'Mandatory' checkbox."""
    self.checkbox_mandatory.click()

  def select_type(self, ca_type):
    """Select CustomAttribute type from 'Attribute type' dropdown."""
    self.attribute_type_selector.select(ca_type)

  def enter_possible_values(self, values_string):
    """Fill 'Possible values' field for 'Dropdown' type of CustomAttribute."""
    self.ui_possible_values = base.TextInputField(
        self._driver, self._locators.UI_POSSIBLE_VALUES)
    self.ui_possible_values.enter_text(values_string)


class DynamicTreeToggle(base.Toggle):
  """Tree item in Admin custom attribute widget."""
  def __init__(self, driver, el_locator):
    super(DynamicTreeToggle, self).__init__(driver, el_locator)
    self.element = driver.find_element(*el_locator)
    self.is_activated = selenium_utils.is_value_in_attr(self.element)


class WidgetAdminCustomAttributes(base.Widget):
  """Base model for custom attributes on Admin Dashboard page."""
  _locators = locator.AdminCustomAttributes
  URL = (environment.APP_URL + url.ADMIN_DASHBOARD +
         url.Widget.CUSTOM_ATTRIBUTES)
