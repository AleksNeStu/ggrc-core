# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Base widget models."""
# pylint: disable=not-callable
# pylint: disable=not-an-iterable
# pylint: disable=too-few-public-methods

from lib import base, decorator, environment
from lib.constants import locator, url
from lib.entities.entities_factory import CustomAttributeDefinitionsFactory
from lib.utils import selenium_utils
from lib.utils.string_utils import StringMethods


class _Modal(base.Modal):
  """Base model for Edit modal."""
  _locators = locator.ModalCustomAttribute

  def __init__(self, driver):
    super(_Modal, self).__init__(driver)
    self.modal_window = selenium_utils.get_when_visible(
        self._driver, self._locators.MODAL_CSS)
    self.attr_title_ui = base.TextInputField(
        self.modal_window, self._locators.ATTR_TITLE_UI_CSS)
    self.submit_btn = base.Button(
        self.modal_window, self._locators.SAVE_AND_CLOSE_BTN_CSS)

  def enter_title(self, title):
    self.attr_title_ui.enter_text(title)

  @decorator.handle_alert
  def save_and_close(self):
    """
    Return: WidgetAdminCustomAttributes
    """
    self.submit_btn.click()
    selenium_utils.wait_until_not_present(
        self._driver, self._locators.SAVE_AND_CLOSE_BTN_CSS)
    selenium_utils.wait_until_not_present(
        self._driver, self._locators.MODAL_CSS)


class CustomAttributesItemContent(base.Component):
  """Model for 2-tier of custom attributes Tree View item."""
  _locators = locator.CustomAttributesItemContent

  def __init__(self, driver, item_text):
    super(CustomAttributesItemContent, self).__init__(driver)
    self.item_el = selenium_utils.get_when_visible(
        self._driver, self._locators.TREE_ITEM_EL_OPENED_CSS)
    self.add_btn = base.Button(self.item_el, self._locators.ADD_BTN_CSS)
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
                                                   self._locators.ROW_CSS):
      attrs = [i.text for i in row.find_elements(
          *self._locators.CELL_IN_ROW_CSS)]
      # todo: add PO and getting 'multi_choice_options' via 'Edit' btn
      self.custom_attributes_list.append(
          CustomAttributeDefinitionsFactory().create(
              title=attrs[0], attribute_type=attrs[1],
              mandatory=StringMethods.get_bool_value_from_arg(attrs[2]),
              definition_type=self._item_name, multi_choice_options=None))

  def get_ca_list_from_group(self):
    """Return list of Custom Attribute objects."""
    self._set_custom_attributes_list()
    return self.custom_attributes_list

  def open_add_new_ca_modal(self):
    """Open Add Attribute modal and return Custom Attribute Modal."""
    selenium_utils.wait_until_stops_moving(self.add_btn.element)
    selenium_utils.scroll_into_view(self._driver, self.item_el)
    selenium_utils.get_when_clickable(self._driver, self._locators.ADD_BTN_CSS)
    selenium_utils.wait_until_not_present(
        self._driver, self._locators.TREE_SPINNER_CSS)
    self.add_btn.click()
    return CustomAttributeModal(self._driver)

  def select_ca_member_by_num(self, num):
    """Select Custom Attribute member from list of members by number
    (start from 0).
    Args: num (int)
    Return: lib.page.widget.widget_base.CustomAttributeModal
    """
    # check that the buttons are loaded
    selenium_utils.get_when_clickable(
        self._driver, self._locators.EDIT_BTN_CSS)
    elements = self._driver.find_elements(self._locators.EDIT_BTN_CSS)
    selenium_utils.scroll_into_view(self._driver, elements[num]).click()
    return CustomAttributeModal(self._driver)


class CustomAttributeModal(_Modal):
  """Custom attribute modal."""
  # pylint: disable=too-many-instance-attributes
  def __init__(self, driver):
    super(CustomAttributeModal, self).__init__(driver)
    self.attr_title_lbl = base.Label(
        self.modal_window, self._locators.ATTR_TITLE_LBL_CSS)
    self.attr_type_lbl = base.Label(
        self.modal_window, self._locators.ATTR_TYPE_CSS)
    self.attr_type_selector_dd = base.DropdownStatic(
        self.modal_window, self._locators.ATTR_TYPE_SELECTOR_DD_CSS)
    self.mandatory_lbl = base.Label(
        self.modal_window, self._locators.MANDATORY_LBL_CSS)
    self.mandatory_cb = base.Checkbox(
        self.modal_window, self._locators.MANDATORY_CB_CSS)
    self.inline_help_lbl = base.Label(
        self.modal_window, self._locators.INLINE_HELP_LBL_CSS)
    self.inline_help_ui = None
    self.placeholder_lbl = base.Label(
        self.modal_window, self._locators.PLACEHOLDER_LBL_CSS)
    self.placeholder_ui = None
    self.possible_values_ui = None

  def enter_inline_help(self, inline_help):
    """Fill 'Inline help' field."""
    self.inline_help_ui = base.TextInputField(
        self.modal_window, self._locators.INLINE_HELP_UI_CSS)
    self.inline_help_ui.enter_text(inline_help)

  def enter_placeholder(self, placeholder):
    """Fill 'Placeholder' field."""
    self.placeholder_ui = base.TextInputField(
        self.modal_window, self._locators.PLACEHOLDER_UI_CSS)
    self.placeholder_ui.enter_text(placeholder)

  def set_mandatory(self):
    """Check 'Mandatory' checkbox."""
    self.mandatory_cb.click()

  def select_type(self, ca_type):
    """Select CustomAttribute type from 'Attribute type' dropdown."""
    self.attr_type_selector_dd.select(ca_type)

  def enter_possible_values(self, values_string):
    """Fill 'Possible values' field for 'Dropdown' type of CustomAttribute."""
    self.possible_values_ui = base.TextInputField(
        self.modal_window, self._locators.POSSIBLE_VALUES_UI_CSS)
    self.possible_values_ui.enter_text(values_string)


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
