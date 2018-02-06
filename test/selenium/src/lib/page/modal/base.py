# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Modal base classes."""
# pylint: disable=too-few-public-methods

from lib import base
from lib.constants import locator, objects
from lib.page.modal import unified_mapper
from lib.utils import selenium_utils


class BaseModal(base.Modal):
  """Base class for creation and edition modals."""
  _locators = locator.BaseModalCreateNew
  _locator_ui_title = locator.ModalCreateNewObject.UI_TITLE
  _locator_ui_code = locator.ModalCreateNewObject.UI_CODE
  _locator_button_save = locator.ModalCreateNewObject.BUTTON_SAVE_AND_CLOSE

  def __init__(self, driver):
    super(BaseModal, self).__init__(driver)
    self.modal_elem = selenium_utils.get_when_visible(
        self._driver, self._locators.MODAL_CSS)
    self.button_save_and_close = base.Button(
        self.modal_elem, self._locator_button_save)
    self.ui_title = base.TextInputField(
        self.modal_elem, self._locator_ui_title)
    self.ui_code = base.TextInputField(
        self.modal_elem, self._locator_ui_code)

  def enter_title(self, text):
    """Enter title to modal."""
    self.ui_title.enter_text(text)

  def enter_code(self, code):
    """Enter code to modal."""
    self.ui_code.enter_text(code)

  def fill_minimal_data(self, title, code):
    """Enter common minimal data to modal."""
    self.enter_title(title)
    self.enter_code(code)
    return self.__class__(self._driver)

  def edit_minimal_data(self, title):
    """Edit title of current modal."""
    self.enter_title(title)
    return self.__class__(self._driver)


class ProgramsModal(BaseModal):
  """Modal base for Program objects."""
  # pylint: disable=too-many-instance-attributes
  _locators = locator.ModalCreateNewProgram

  def __init__(self, driver):
    super(ProgramsModal, self).__init__(driver)
    # user input elements
    self.ui_description = base.Iframe(
        self.modal_elem.parent, self._locators.UI_DESCRIPTION)
    self.ui_notes = base.Iframe(
        self.modal_elem.parent, self._locators.UI_NOTES)
    self.ui_code = base.TextInputField(
        self.modal_elem, self._locators.UI_CODE)
    self.ui_state = base.Dropdown(
        self.modal_elem, self._locators.UI_STATE)
    self.ui_show_optional_fields = base.Toggle(
        self.modal_elem, self._locators.BUTTON_SHOW_ALL_OPTIONAL_FIELDS)
    self.ref_url = base.MultiInputField(
        self.modal_elem.parent, self._locators.REF_URL_CSS)
    self.ui_effective_date = base.DatePicker(
        self.modal_elem, self._locators.EFFECTIVE_DATE_DATEPICKER,
        self._locators.UI_EFFECTIVE_DATE)
    # static elements
    self.title = base.Label(self.modal_elem, self._locators.TITLE)
    self.description = base.Label(
        self.modal_elem, self._locators.DESCRIPTION)

  def enter_description(self, description):
    """Enter text into description element.
    Args: description (basestring)
    """
    self.ui_description.find_iframe_and_enter_data(description)

  def enter_notes(self, notes):
    """Enter text into notes element.
    Args: notes basestring)
    """
    self.ui_notes.find_iframe_and_enter_data(notes)

  def enter_code(self, code):
    """Enter text into code element.
    Args: code (basestring)
    """
    self.ui_code.enter_text(code)

  def select_state(self, state):
    """Selects state from dropdown."""
    raise NotImplementedError

  def toggle_optional_fields(self):
    """Show or hide optional fields."""
    raise NotImplementedError

  def enter_program_ref_url(self, url):
    """Enter program reference urls for this program object.
    Args: url (str) or (iterable)
    """
    self.ref_url.add_values(url)

  def enter_effective_date_start_month(self, day):
    """Select from datepicker start date.
    Args: day (int): # base.DatePicker.select_day_in_current_month
    """
    # pylint: disable=invalid-name
    self.ui_effective_date.select_day_in_current_month(day)


class ControlsModal(BaseModal):
  """Modal base for Control objects."""
  # pylint: disable=too-many-instance-attributes
  _locators = locator.ModalCreateNewControl

  def __init__(self, driver):
    super(ControlsModal, self).__init__(driver)
    # labels
    self.modal_title = base.Label(
        self.modal_elem, self._locators.MODAL_TITLE)
    self.title = base.Label(
        self.modal_elem, self._locators.TITLE)
    self.description = base.Label(
        self.modal_elem, self._locators.DESCRIPTION)
    self.test_plan = base.Label(
        self.modal_elem, self._locators.TEST_PLAN)
    self.notes = base.Label(self.modal_elem, self._locators.NOTES)
    self.code = base.Label(self.modal_elem, self._locators.CODE)
    self.kind_or_nature = base.Label(
        self.modal_elem, self._locators.KIND_OR_NATURE)
    self.fraud_related = base.Label(
        self.modal_elem, self._locators.FRAUD_RELATED)
    self.frequency = base.Label(
        self.modal_elem, self._locators.FREQUENCY)
    self.assertions = base.Label(
        self.modal_elem, self._locators.ASSERTIONS)
    self.admin = base.Label(self.modal_elem, self._locators.ADMIN)
    self.significance = base.Label(
        self.modal_elem, self._locators.SIGNIFICANCE)
    self.type_or_means = base.Label(
        self.modal_elem, self._locators.TYPE_OR_MEANS)
    self.categories = base.Label(
        self.modal_elem, self._locators.CATEGORIES)
    self.state = base.Label(self.modal_elem, self._locators.STATE)
    self.ui_description = base.Iframe(
        self.modal_elem.parent, self._locators.UI_DESCRIPTION)
    self.ui_test_plan = base.Iframe(
        self.modal_elem.parent, self._locators.UI_TEST_PLAN)
    self.ui_notes = base.Iframe(
        self.modal_elem.parent, self._locators.UI_NOTES)
    self.ui_code = base.TextInputField(
        self.modal_elem, self._locators.UI_CODE)
    # multi input fields
    self.ref_url = base.MultiInputField(
        self.modal_elem.parent, self._locators.REF_URL_CSS)
    # datepickers
    self.ui_effective_date = base.DatePicker(
        self.modal_elem, self._locators.EFFECTIVE_DATE,
        self._locators.DATEPICKER_EFFECTIVE_DATE)
    # dropdowns
    self.ui_kind_or_nature = base.Dropdown(
        self.modal_elem, self._locators.DROPDOWN_KIND_OR_NATURE)
    self.ui_fraud_related = base.Dropdown(
        self.modal_elem, self._locators.DROPDOWN_FRAUD_RELATED)
    self.ui_type_or_means = base.Dropdown(
        self.modal_elem, self._locators.DROPDOWN_TYPE_OR_MEANS)
    self.ui_frequency = base.Dropdown(
        self.modal_elem, self._locators.DROPDOWN_FREQUENCY)
    # selectable lists
    self.selectable_assertions = base.Selectable(
        self.modal_elem, self._locators.SELECTABLE_ASSERTIONS)
    self.selectable_categories = base.Selectable(
        self.modal_elem, self._locators.SELECTABLE_CATEGORIES)
    # buttons
    self.button_add_owner = base.Button(
        self.modal_elem, self._locators.BUTTON_ADD_OWNER)
    self.button_hide_all_optional_fields = base.Button(
        self.modal_elem, self._locators.BUTTON_HIDE_ALL_OPTIONAL_FIELDS)

  def enter_description(self, text):
    """
    Args: text (basestringe)
    """
    self.ui_description.find_iframe_and_enter_data(text)

  def enter_test_plan(self, text):
    """
    Args: text (basestring)
    """
    self.ui_test_plan.find_iframe_and_enter_data(text)

  def enter_notes(self, text):
    """
    Args: text (basestring)
    """
    self.ui_notes.find_iframe_and_enter_data(text)

  def enter_code(self, code):
    """
    Args: text (basestring)
    """
    self.ui_code.enter_text(code)


class ObjectivesModal(BaseModal):
  """Modal base for Objective objects."""
  _locator_ui_title = locator.ModalCreateNewObjective.UI_TITLE


class RisksModal(BaseModal):
  """Modal base for Risk objects."""
  _locators = locator.ModalCreateNewRisk
  _locator_ui_title = locator.ModalCreateNewRisk.UI_TITLE

  def __init__(self, driver):
    super(RisksModal, self).__init__(driver)
    self.ui_description = base.Iframe(
        self.modal_elem.parent, self._locators.UI_DESCRIPTION)

  def enter_description(self, text):
    self.ui_description.find_iframe_and_enter_data(text)


class OrgGroupsModal(BaseModal):
  """Modal base for Org Group objects."""
  _locator_ui_title = locator.ModalCreateNewOrgGroup.UI_TITLE


class IssuesModal(BaseModal):
  """Modal base for Issue objects."""
  _locator_ui_title = locator.ModalCreateNewIssue.UI_TITLE


class ProcessesModal(BaseModal):
  """Modal base for Process objects."""
  _locator_ui_title = locator.ModalCreateNewProcess.UI_TITLE


class DataAssetsModal(BaseModal):
  """Modal base for DataAsset objects."""
  _locator_ui_title = locator.ModalCreateNewDataAsset.UI_TITLE


class SystemsModal(BaseModal):
  """Modal base for System objects."""
  _locator_ui_title = locator.ModalCreateNewSystem.UI_TITLE


class ProductsModal(BaseModal):
  """Modal base for Product objects."""
  _locator_ui_title = locator.ModalCreateNewProduct.UI_TITLE


class ProjectsModal(BaseModal):
  """Modal base for Project objects."""
  _locator_ui_title = locator.ModalCreateNewProject.UI_TITLE


class AsmtTmplModal(BaseModal):
  """Modal base for Assessment Template objects."""
  _locators = locator.ModalCreateNewAsmtTmpl

  def __init__(self, driver):
    super(AsmtTmplModal, self).__init__(driver)
    self.assignees_dd = base.DropdownStatic(
        self.modal_elem, self._locators.ASSIGNEE_DROPDOWN)

  def select_assignee(self, assignee):
    """Select 'Default Assignee' from drop down list."""
    self.assignees_dd.select(assignee)
    return self.__class__(self._driver)


class AsmtsModal(BaseModal):
  """Modal base for Assessment objects."""
  _locators = locator.ModalCreateNewAsmt

  def map_controls(self, objs):
    """Open Unified Mapper on modal and map objs.
    Return: self
    """
    base.Button(
        self.modal_elem, self._locators.MAP_OBJS_BTN_CSS).click()
    mapper = unified_mapper.AssessmentCreationMapperModal(
        self._driver, objects.ASSESSMENTS)
    mapper.map_dest_objs(
        dest_objs_type=objs[0]["type"],
        dest_objs_titles=[obj["title"] for obj in objs])
    return self

  def get_mapped_snapshots_titles(self):
    """Return titles of mapped snapshots on Assessment Modal.
    Return: list of str
    """
    return [base.Label(self._driver, el.find_element(
            *self._locators.MAPPED_SNAPSHOT_TITLE_CSS)).text
            for el in selenium_utils.get_when_all_visible(
            self.modal_elem, self._locators.MAPPED_SNAPSHOTS_CSS)]
