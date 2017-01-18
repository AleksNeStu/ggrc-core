# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Module for modal base classes."""
# pylint: disable=too-few-public-methods

from selenium.webdriver.common.by import By

from lib import base
from lib.constants import locator
from lib.utils import selenium_utils


class BaseModal(base.Modal):
  """Base class for the edit modal."""
  _locator_ui_title = locator.ModalCreateNewObject.UI_TITLE
  locator_button_save = locator.ModalCreateNewObject.BUTTON_SAVE_AND_CLOSE

  def __init__(self, driver):
    super(BaseModal, self).__init__(driver)
    self.button_save_and_close = base.Button(driver, self.locator_button_save)
    self.ui_title = base.TextInputField(self._driver,
                                        self._locator_ui_title)

  def enter_title(self, text):
    """
    Args:
        text (basestring)
    """
    self.ui_title.enter_text(text)


class SetFieldsModal(base.Modal):
  """Class representing a base set visible fields modal."""
  _locators = locator.ModalSetVisibleFields
  button_save_set_fields = None
  fields_elements = None

  def __init__(self, driver, widget_name):
    """
    Args:
        driver (CustomDriver)
        widget_name (#widget_name according URL)
    """
    super(SetFieldsModal, self).__init__(driver)
    self.widget_name = widget_name

  def set_visible_fields(self, fields):
    """Set visible fields to display objects on the tree view."""
    _locator_modal_fields = (By.CSS_SELECTOR, self._locators.FIELDS_MODAL.
                             format(self.widget_name))
    _locator_fields_titles = (By.CSS_SELECTOR, locator.ModalSetVisibleFields.
                              FIELDS_TITLES.format(self.widget_name))
    _locator_fields_checkboxes = (By.CSS_SELECTOR,
                                  locator.ModalSetVisibleFields.
                                  FIELDS_CHECKBOXES.format(self.widget_name))
    selenium_utils.get_when_visible(self._driver, _locator_modal_fields)
    self.fields_elements = base.Checkboxes(
        self._driver, _locator_fields_titles, _locator_fields_checkboxes)
    self.fields_elements.select_by_titles(fields)

  def save_set_visible_fields(self):
    """Save visible fields to display objects on the tree view."""
    _locator_save_set_fields = (By.CSS_SELECTOR,
                                self._locators.BUTTON_SAVE_SET_FIELDS.
                                format(self.widget_name))
    self.button_save_set_fields = base.Button(self._driver,
                                              _locator_save_set_fields)
    self.button_save_set_fields.click()

  def set_and_save_visible_fields(self, fields):
    """Set and save visible fields to display objects on the tree view."""
    self.set_visible_fields(fields)
    self.save_set_visible_fields()


class ProgramsModal(BaseModal):
  """Class representing a modal base for the program object"""
  # pylint: disable=too-many-instance-attributes

  _locators = locator.ModalCreateNewProgram
  _locator_ui_title = locator.ModalCreateNewProgram.UI_TITLE

  def __init__(self, driver):
    super(ProgramsModal, self).__init__(driver)

    # user input elements
    self.ui_description = base.Iframe(
        self._driver, self._locators.UI_DESCRIPTION)
    self.ui_notes = base.Iframe(self._driver,
                                self._locators.UI_NOTES)
    self.ui_code = base.TextInputField(self._driver,
                                       self._locators.UI_CODE)
    self.ui_state = base.Dropdown(self._driver, self._locators.UI_STATE)
    self.ui_show_optional_fields = base.Toggle(
        self._driver,
        self._locators.BUTTON_SHOW_ALL_OPTIONAL_FIELDS)
    self.ui_primary_contact = base.TextFilterDropdown(
        self._driver,
        self._locators.UI_PRIMARY_CONTACT,
        self._locators.DROPDOWN_CONTACT)
    self.ui_secondary_contact = base.TextFilterDropdown(
        self._driver,
        self._locators.UI_SECONDARY_CONTACT,
        self._locators.DROPDOWN_CONTACT)
    self.ui_program_url = base.TextInputField(
        self._driver, self._locators.UI_PROGRAM_URL)
    self.ui_reference_url = base.TextInputField(
        self._driver, self._locators.UI_REFERENCE_URL)
    self.ui_effective_date = base.DatePicker(
        self._driver,
        self._locators.EFFECTIVE_DATE_DATEPICKER,
        self._locators.UI_EFFECTIVE_DATE)
    self.ui_stop_date = base.DatePicker(
        self._driver,
        self._locators.STOP_DATE_DATEPICKER,
        self._locators.UI_STOP_DATE)

    # static elements
    self.title = base.Label(self._driver, self._locators.TITLE)
    self.description = base.Label(self._driver, self._locators.DESCRIPTION)
    self.program_url = base.Label(self._driver, self._locators.PROGRAM_URL)

  def enter_description(self, description):
    """Enters the text into the description element

    Args:
        description (basestring)
    """
    self.ui_description.find_iframe_and_enter_data(description)

  def enter_notes(self, notes):
    """Enters the text into the notes element

    Args:
        notes basestring)
    """
    self.ui_notes.find_iframe_and_enter_data(notes)

  def enter_code(self, code):
    """Enters the text into the code element

    Args:
        code (basestring)
    """
    self.ui_code.enter_text(code)

  def select_state(self, state):
    """Selects a state from the dropdown"""
    raise NotImplementedError

  def toggle_optional_fields(self):
    """Shows or hides optional fields"""
    raise NotImplementedError

  def filter_and_select_primary_contact(self, text):
    """Enters the text into the primary contact element"""
    # pylint: disable=invalid-name
    self.ui_primary_contact.filter_and_select_first(text)

  def filter_and_select_secondary_contact(self, text):
    """Enters the text into the secondary contact element"""
    # pylint: disable=invalid-name
    self.ui_secondary_contact.filter_and_select_first(text)

  def enter_program_url(self, url):
    """Enters the program url for this program object

    Args:
        url (str)
    """
    self.ui_program_url.enter_text(url)

  def enter_reference_url(self, url):
    """Enters the reference url for this program object

    Args:
        url (str)
    """
    self.ui_reference_url.enter_text(url)

  def enter_effective_date_start_month(self, day):
    """Selects from datepicker the start date
    Args:
      day (int): for more info see base.DatePicker.select_day_in_current_month
    """
    # pylint: disable=invalid-name
    self.ui_effective_date.select_day_in_current_month(day)

  def enter_stop_date_end_month(self, day):
    """Selects from datepicker the end date
    Args:
      day (int): for more info see base.DatePicker.select_day_in_current_month
    """
    self.ui_stop_date.select_day_in_current_month(day)


class ControlsModal(BaseModal):
  """Class representing a modal base for the control object."""
  # pylint: disable=too-many-instance-attributes
  _locators = locator.ModalCreateNewControl

  def __init__(self, driver):
    super(ControlsModal, self).__init__(driver)

    # labels
    self.modal_title = base.Label(driver, self._locators.MODAL_TITLE)
    self.title = base.Label(driver, self._locators.TITLE)
    self.description = base.Label(driver, self._locators.DESCRIPTION)
    self.test_plan = base.Label(driver, self._locators.TEST_PLAN)
    self.notes = base.Label(driver, self._locators.NOTES)
    self.code = base.Label(driver, self._locators.CODE)
    self.kind_or_nature = base.Label(driver, self._locators.KIND_OR_NATURE)
    self.fraud_related = base.Label(driver, self._locators.FRAUD_RELATED)
    self.frequency = base.Label(driver, self._locators.FREQUENCY)
    self.assertions = base.Label(driver, self._locators.ASSERTIONS)
    self.principal_assessor = base.Label(driver,
                                         self._locators.PRINCIPAL_ASSESSOR)
    self.secondary_assessor = base.Label(driver,
                                         self._locators.SECONDARY_ASSESSOR)
    self.owner = base.Label(driver, self._locators.OWNER)
    self.primary_contact = base.Label(driver, self._locators.PRIMARY_CONTACT)
    self.secondary_contact = base.Label(driver,
                                        self._locators.SECONDARY_CONTACT)
    self.control_url = base.Label(driver, self._locators.CONTROL_URL)
    self.reference_url = base.Label(driver, self._locators.REFERENCE_URL)
    self.significance = base.Label(driver, self._locators.SIGNIFICANCE)
    self.type_or_means = base.Label(driver, self._locators.TYPE_OR_MEANS)
    self.categories = base.Label(driver, self._locators.CATEGORIES)
    self.state = base.Label(driver, self._locators.STATE)

    self.ui_description = base.Iframe(driver, self._locators.UI_DESCRIPTION)
    self.ui_test_plan = base.Iframe(driver, self._locators.UI_TEST_PLAN)
    self.ui_notes = base.Iframe(driver, self._locators.UI_NOTES)
    self.ui_code = base.TextInputField(driver, self._locators.UI_CODE)
    self.ui_primary_contact = base.TextInputField(
        driver, self._locators.UI_PRIMARY_CONTACT)
    self.ui_secondary_contact = base.TextInputField(
        driver, self._locators.UI_SECONDARY_CONTACT)
    self.ui_control_url = base.TextInputField(
        driver, self._locators.UI_CONTROL_URL)
    self.ui_reference_url = base.TextInputField(
        driver, self._locators.UI_REFERENCE_URL)

    # datepickers
    self.ui_effective_date = base.DatePicker(
        driver,
        self._locators.EFFECTIVE_DATE,
        self._locators.DATEPICKER_EFFECTIVE_DATE)
    self.ui_stop_date = base.DatePicker(
        driver,
        self._locators.STOP_DATE,
        self._locators.DATEPICKER_STOP_DATE)

    # dropdowns
    self.ui_kind_or_nature = base.Dropdown(
        driver,
        self._locators.DROPDOWN_KIND_OR_NATURE)
    self.ui_fraud_related = base.Dropdown(
        driver,
        self._locators.DROPDOWN_FRAUD_RELATED)
    self.ui_type_or_means = base.Dropdown(
        driver,
        self._locators.DROPDOWN_TYPE_OR_MEANS)
    self.ui_frequency = base.Dropdown(
        driver,
        self._locators.DROPDOWN_FREQUENCY)

    # selectable lists
    self.selectable_assertions = base.Selectable(
        driver,
        self._locators.SELECTABLE_ASSERTIONS)
    self.selectable_categories = base.Selectable(
        driver,
        self._locators.SELECTABLE_CATEGORIES)

    # buttons
    self.button_add_owner = base.Button(
        driver, self._locators.BUTTON_ADD_OWNER)
    self.button_hide_all_optional_fields = base.Button(
        driver, self._locators.BUTTON_HIDE_ALL_OPTIONAL_FIELDS)

  def enter_description(self, text):
    """
    Args:
        text (basestringe)
    """
    self.ui_description.find_iframe_and_enter_data(text)

  def enter_test_plan(self, text):
    """
    Args:
        text (basestring)
    """
    self.ui_test_plan.find_iframe_and_enter_data(text)

  def enter_notes(self, text):
    """
    Args:
        text (basestring)
    """
    self.ui_notes.find_iframe_and_enter_data(text)

  def enter_code(self, text):
    """
    Args:
        text (basestring)
    """
    self.ui_code.enter_text(text)


class RisksModal(BaseModal):
  """Class representing a new risk modal visible after creating a new
  control from LHN"""

  _locators = locator.ModalCreateNewRisk
  _locator_ui_title = locator.ModalCreateNewRisk.UI_TITLE

  def __init__(self, driver):
    super(RisksModal, self).__init__(driver)
    self.ui_description = base.Iframe(driver, self._locators.UI_DESCRIPTION)

  def enter_description(self, text):
    self.ui_description.find_iframe_and_enter_data(text)


class OrgGroupsModal(BaseModal):
  """Class representing a base org group modal visible after creating a new
  org group from LHN"""
  _locator_ui_title = locator.ModalCreateNewOrgGroup.UI_TITLE


class IssuesModal(BaseModal):
  """Class representing a base issue modal visible after creating a new
  issue from LHN"""
  _locator_ui_title = locator.ModalCreateNewIssue.UI_TITLE


class ProcessesModal(BaseModal):
  """Class representing a base process modal"""
  _locator_ui_title = locator.ModalCreateNewProcess.UI_TITLE


class DataAssetsModal(BaseModal):
  """Class representing a base data asset modal"""
  _locator_ui_title = locator.ModalCreateNewDataAsset.UI_TITLE


class SystemsModal(BaseModal):
  """Class representing a base system modal"""
  _locator_ui_title = locator.ModalCreateNewSystem.UI_TITLE


class ProductsModal(BaseModal):
  """Class representing a base product modal"""
  _locator_ui_title = locator.ModalCreateNewProduct.UI_TITLE


class ProjectsModal(BaseModal):
  """Class representing a base product modal"""
  _locator_ui_title = locator.ModalCreateNewProject.UI_TITLE


class AsmtTmplModal(BaseModal):
  """Class representing a base assessment creation modal."""
  _locators = locator.ModalCreateNewAsmtTmpl

  def __init__(self, driver):
    super(AsmtTmplModal, self).__init__(driver)

  def fill_minimal_data(self, title):
    """Enter minimal data to create assessment template."""
    self.enter_title(title)


class AsmtsModal(BaseModal):
  """Class representing a base assessment creation modal."""
  _locators = locator.ModalCreateNewAsmt

  def __init__(self, driver):
    super(AsmtsModal, self).__init__(driver)

  def fill_minimal_data(self, title):
    """Enter minimal data to create assessment."""
    self.enter_title(title)


class AsmtsModalGenerate(base.Modal):
  """Class representing a base assessment generation modal."""
  _locators = locator.ModalGenerateNewAsmt

  def __init__(self, driver):
    super(AsmtsModalGenerate, self).__init__(driver)
    self.button_search = None
    self.controls_elements = None
    self.asmt_tmpl_element = None

  def select_asmt_tmpl(self, asmt_tmpl_title):
    """Select assessment template via dropdown according to the text title."""
    self.asmt_tmpl_element = base.TextFilterDropdown(
        self._driver,
        self._locators.SELECT_ASMT_TMPL_OPTIONS,
        self._locators.SELECT_ASMT_TMPL_DROPDOWN)
    self.asmt_tmpl_element.find_and_select_first(asmt_tmpl_title)

  def search_objects(self):
    """Click to the button to search objects according set filters."""
    self.button_search = base.Button(self._driver,
                                     self._locators.BUTTON_SEARCH)
    self.button_search.click_when_visible()

  def select_objs_under(self, controls_titles):
    """Click checkboxes (Select objects) which was found after search
    was completed."""
    self.controls_elements = base.Checkboxes(
        self._driver,
        self._locators.FOUNDED_OBJECTS_TITLES,
        self._locators.FOUNDED_OBJECTS_CHECKBOXES)
    self.controls_elements.select_by_titles(controls_titles)

  def fill_minimal_data(self, asmt_tmpl, controls):
    """Enter minimal data to generate assessment(s)."""
    self.select_asmt_tmpl(asmt_tmpl)
    self.search_objects()
    self.select_objs_under(controls)
