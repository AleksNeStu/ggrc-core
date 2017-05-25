# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Info widgets."""

from lib import base
from lib.constants import locator, objects, element, roles
from lib.element import widget_info
from lib.page.modal import update_object
from lib.utils import selenium_utils


import logging
import sys

root = logging.getLogger()
root.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)

class CommonInfo(base.Widget):
  """Abstract class of common info for Info pages and Info panels."""
  _locators = locator.CommonWidgetInfo
  dropdown_settings_cls = widget_info.CommonDropdownSettings
  locator_headers_and_values = None
  all_headers_and_values = []
  cas_headers_and_values = []
  list_all_headers_text = []
  list_all_values_text = []

  def __init__(self, driver):
    super(CommonInfo, self).__init__(driver)
    if self.is_under_audit:
      self.title = base.Label(driver, self._locators.TITLE_UNDER_AUDIT)
      self.title_entered = base.Label(
          driver, self._locators.TITLE_ENTERED_UNDER_AUDIT)
      self.state = base.Label(driver, self._locators.STATE_UNDER_AUDIT)
      self.locator_3bbs = self._locators.BUTTON_3BBS_UNDER_AUDIT
    else:
      self.title = base.Label(driver, self._locators.TITLE)
      self.title_entered = base.Label(driver, self._locators.TITLE_ENTERED)
      self.state = base.Label(driver, self._locators.STATE)
      self.locator_3bbs = self._locators.BUTTON_3BBS

  def open_info_3bbs(self):
    """Click to 3BBS button on Info page or Info panel to open info 3BBS modal.
    Return: lib.element.widget_info."obj_name"DropdownSettings
    """
    base.Button(self._driver, self.locator_3bbs).click()
    return self.dropdown_settings_cls(self._driver, self.is_under_audit)

  def get_header_and_value_text_from_all_scopes(self, header_text):
    """Get one header and one value elements text from all scopes elements
    according to header text.
    Example:
    If header_text is 'header' :return ['header', 'value']
    """
    # pylint: disable=not-an-iterable
    # pylint: disable=invalid-name
    if not self.all_headers_and_values and self.locator_headers_and_values:
      selenium_utils.wait_for_js_to_load(self._driver)
      self.all_headers_and_values = self._driver.find_elements(
          *self.locator_headers_and_values)
    header_and_value = (
        [scope.text.splitlines()[:2] for scope in self.all_headers_and_values
         if header_text in scope.text][0]
        if self.all_headers_and_values else [None, None])
    return header_and_value

  def get_and_convert_headers_and_values_text_from_cas_scopes(self):
    """Get and convert to entities form all headers and values elements text
    from CAs scopes elements.
    Example:
    :return [['ca_header1', 'ca_header2'], ['ca_value1', 'ca_value2']]
    """
    # pylint: disable=invalid-name
    try:
      if not self.cas_headers_and_values:
        selenium_utils.wait_for_js_to_load(self._driver)
        self.cas_headers_and_values = self._driver.find_elements(
            *self._locators.CAS_HEADERS_AND_VALUES)
      if self.cas_headers_and_values:
        list_text_cas_scopes = [
            scope.text.splitlines() if len(scope.text.splitlines()) == 2 else
            [scope.text.splitlines()[0],
             unicode(int(base.Checkbox(self._driver, scope.find_element(
                 *self._locators.CAS_CHECKBOXES)).is_element_checked()))
             ] for scope in self.cas_headers_and_values]
        cas_headers, _cas_values = zip(*list_text_cas_scopes)
        cas_values = []
        for ca_val in _cas_values:
          if ca_val == roles.DEFAULT_USER:
            # Example User
            cas_values.append(
                unicode(objects.get_singular(objects.PEOPLE).title()))
          elif "/" in ca_val and len(ca_val) == 10:
            # Date
            _date = ca_val.split("/")
            cas_values.append(unicode("{y}-{m}-{d}".format(
                y=_date[2], m=_date[0], d=_date[1])))
          else:
            # Other
            cas_values.append(ca_val)
        return cas_headers, cas_values
      else:
        return [None, None]
    except:
      root.exception("Debug")

  def get_info_widget_obj_scope(self):
    """Get dict from object (text scope) which displayed on info page or
    info panel according to list of headers text and list of values text.
    """
    return dict(zip(self.list_all_headers_text, self.list_all_values_text))


class InfoPanel(CommonInfo):
  """Class for Info Panels."""
  _locators = locator.WidgetInfoPanel

  def __init__(self, driver):
    super(InfoPanel, self).__init__(driver)
    self.locator_headers_and_values = (
        self._locators.PANEL_HEADERS_AND_VALUES if self.is_info_panel or
        not self.is_info_panel and not self.is_info_page
        else self._locators.PAGE_HEADERS_AND_VALUES)
    if self.is_info_panel:
      self.button_maximize_minimize = self._driver.find_element(
          *self._locators.BUTTON_MAXIMIZE_MINIMIZE)
      self.button_close = self._driver.find_element(
          *self._locators.BUTTON_CLOSE)

  def maximize(self):
    """Maximize Info Panel if it is not maximized yet."""
    if not self.is_maximized:
      self.button_maximize_minimize.click()
      selenium_utils.get_when_all_visible(
          self._driver, self._locators.BUTTON_MAXIMIZE_MINIMIZE)
    return self.__class__(self._driver)

  def minimize(self):
    """Minimize Info Panel if it is maximized."""
    if self.is_maximized:
      self.button_maximize_minimize.click()
    selenium_utils.get_when_all_visible(
        self._driver, self._locators.BUTTON_MAXIMIZE_MINIMIZE)
    return self.__class__(self._driver)

  def close(self):
    """Close Info Panel."""
    self.button_close.click()
    selenium_utils.get_when_invisible(self._driver, self.button_close)

  @property
  def is_maximized(self):
    """Is Info Panel maximized."""
    return selenium_utils.is_value_in_attr(
        element=self.button_maximize_minimize, value=locator.Common.NORMAL)


class SnapshotableInfoPanel(InfoPanel):
  """Class for Info Panels of snapshotable objects."""
  # pylint: disable=too-few-public-methods
  _locators = locator.WidgetSnapshotsInfoPanel
  locator_link_get_latest_ver = _locators.LINK_GET_LAST_VER

  def __init__(self, driver):
    super(SnapshotableInfoPanel, self).__init__(driver)
    if self.is_under_audit and self.is_info_panel:
      self.snapshot_obj_version = base.Label(
          driver, self._locators.SNAPSHOT_OBJ_VER)

  def open_link_get_latest_ver(self):
    """Click on link get latest version under Info panel."""
    base.Button(self._driver, self.locator_link_get_latest_ver).click()
    return update_object.CompareUpdateObjectModal(self._driver)

  def is_link_get_latest_ver_exist(self):
    """Find link get latest version under Info panel.
    Return: True if link get latest version is exist,
            False if link get latest version is not exist.
    """
    return selenium_utils.is_element_exist(
        self._driver, self.locator_link_get_latest_ver)


class Programs(InfoPanel):
  """Model for program object Info pages and Info panels."""
  # pylint: disable=too-many-instance-attributes
  _locators = locator.WidgetInfoProgram
  dropdown_settings_cls = widget_info.Programs

  def __init__(self, driver):
    super(Programs, self).__init__(driver)
    # same for info_page or info_panel or is_under_audit
    self.show_advanced = base.Toggle(
        self._driver, self._locators.TOGGLE_SHOW_ADVANCED)
    self.show_advanced.toggle()
    self.object_review = base.Label(self._driver, self._locators.OBJECT_REVIEW)
    self.submit_for_review = base.Label(
        self._driver, self._locators.SUBMIT_FOR_REVIEW)
    self.description = base.Label(self._driver, self._locators.DESCRIPTION)
    self.description_entered = base.Label(
        self._driver, self._locators.DESCRIPTION_ENTERED)
    self.notes = base.Label(self._driver, self._locators.NOTES)
    self.notes_entered = base.Label(self._driver, self._locators.NOTES_ENTERED)
    self.manager = base.Label(self._driver, self._locators.MANAGER)
    self.manager_entered = base.Label(
        self._driver, self._locators.MANAGER_ENTERED)
    self.program_url = base.Label(self._driver, self._locators.PROGRAM_URL)
    self.program_url_entered = base.Label(
        self._driver, self._locators.PROGRAM_URL_ENTERED)
    self.reference_url = base.Label(self._driver, self._locators.REFERENCE_URL)
    self.reference_url_entered = base.Label(
        self._driver, self._locators.REFERENCE_URL_ENTERED)
    self.code = base.Label(self._driver, self._locators.CODE)
    self.code_entered = base.Label(self._driver, self._locators.CODE_ENTERED)
    self.effective_date = base.Label(
        self._driver, self._locators.EFFECTIVE_DATE)
    self.effective_date_entered = base.Label(
        self._driver, self._locators.EFFECTIVE_DATE_ENTERED)
    self.stop_date = base.Label(self._driver, self._locators.STOP_DATE)
    self.stop_date_entered = base.Label(
        self._driver, self._locators.STOP_DATE_ENTERED)


class Workflows(InfoPanel):
  """Model for Workflow object Info pages and Info panels."""
  _locators = locator.WidgetInfoWorkflow

  def __init__(self, driver):
    super(Workflows, self).__init__(driver)


class Audits(InfoPanel):
  """Model for Audit object Info pages and Info panels."""
  # pylint: disable=too-many-instance-attributes
  _locators = locator.WidgetInfoAudit
  _elements = element.AuditInfoWidget
  dropdown_settings_cls = widget_info.Audits

  def __init__(self, driver):
    super(Audits, self).__init__(driver)
    self.audit_lead_text, self.audit_lead_entered_text = (
        self.get_header_and_value_text_from_all_scopes(
            self._elements.AUDIT_LEAD.upper()))
    self.code_text, self.code_entered_text = (
        self.get_header_and_value_text_from_all_scopes(
            self._elements.CODE.upper()))
    self.cas_headers_text, self.cas_values_text = (
        self.get_and_convert_headers_and_values_text_from_cas_scopes())
    # all obj scopes
    self.list_all_headers_text = [
        self._elements.CAS_HEADERS.upper(), self._elements.CAS_VALUES.upper(),
        self.title.text, self._elements.STATUS.upper(), self.audit_lead_text,
        self.code_text]
    self.list_all_values_text = [
        self.cas_headers_text, self.cas_values_text, self.title_entered.text,
        objects.get_normal_form(self.state.text), self.audit_lead_entered_text,
        self.code_entered_text]


class Assessments(InfoPanel):
  """Model for Assessment object Info pages and Info panels."""
  _locators = locator.WidgetInfoAssessment

  def __init__(self, driver):
    super(Assessments, self).__init__(driver)


class AssessmentTemplates(InfoPanel):
  """Model for Assessment Template object Info pages and Info panels."""
  _locators = locator.WidgetInfoAssessmentTemplate

  def __init__(self, driver):
    super(AssessmentTemplates, self).__init__(driver)


class Issues(InfoPanel):
  """Model for Issue object Info pages and Info panels."""
  _locators = locator.WidgetInfoIssue

  def __init__(self, driver):
    super(Issues, self).__init__(driver)


class Regulations(SnapshotableInfoPanel):
  """Model for Assessment object Info pages and Info panels."""
  _locators = locator.WidgetInfoRegulations

  def __init__(self, driver):
    super(Regulations, self).__init__(driver)


class Policies(SnapshotableInfoPanel):
  """Model for Policy object Info pages and Info panels."""
  _locators = locator.WidgetInfoPolicy

  def __init__(self, driver):
    super(Policies, self).__init__(driver)


class Standards(SnapshotableInfoPanel):
  """Model for Standard object Info pages and Info panels."""
  _locators = locator.WidgetInfoStandard

  def __init__(self, driver):
    super(Standards, self).__init__(driver)


class Contracts(SnapshotableInfoPanel):
  """Model for Contract object Info pages and Info panels."""
  _locators = locator.WidgetInfoContract

  def __init__(self, driver):
    super(Contracts, self).__init__(driver)


class Clauses(SnapshotableInfoPanel):
  """Model for Clause object Info pages and Info panels."""
  _locators = locator.WidgetInfoClause

  def __init__(self, driver):
    super(Clauses, self).__init__(driver)


class Sections(SnapshotableInfoPanel):
  """Model for Section object Info pages and Info panels."""
  _locators = locator.WidgetInfoSection

  def __init__(self, driver):
    super(Sections, self).__init__(driver)


class Controls(SnapshotableInfoPanel):
  """Model for Control object Info pages and Info panels."""
  # pylint: disable=too-many-instance-attributes
  _locators = locator.WidgetInfoControl
  _elements = element.ControlInfoWidget
  dropdown_settings_cls = widget_info.Controls

  def __init__(self, driver):
    super(Controls, self).__init__(driver)
    self.admin_text, self.admin_entered_text = (
        self.get_header_and_value_text_from_all_scopes(
            self._elements.ADMIN.upper()))
    self.primary_contact_text, self.primary_contact_entered_text = (
        self.get_header_and_value_text_from_all_scopes(
            self._elements.PRIMARY_CONTACT.upper()))
    self.code_text, self.code_entered_text = (
        self.get_header_and_value_text_from_all_scopes(
            self._elements.CODE.upper()))
    self.cas_headers_text, self.cas_values_text = (
        self.get_and_convert_headers_and_values_text_from_cas_scopes())
    # scope
    self.list_all_headers_text = [
        self._elements.CAS_HEADERS.upper(), self._elements.CAS_VALUES.upper(),
        self.title.text, self._elements.STATE.upper(), self.admin_text,
        self.primary_contact_text, self.code_text]
    self.list_all_values_text = [
        self.cas_headers_text, self.cas_values_text, self.title_entered.text,
        objects.get_normal_form(self.state.text), self.admin_entered_text,
        self.primary_contact_entered_text, self.code_entered_text]


class Objectives(SnapshotableInfoPanel):
  """Model for Objective object Info pages and Info panels."""
  _locators = locator.WidgetInfoObjective

  def __init__(self, driver):
    super(Objectives, self).__init__(driver)


class People(base.Widget):
  """Model for People object Info pages and Info panels."""
  # pylint: disable=too-few-public-methods
  _locators = locator.WidgetInfoPeople


class OrgGroups(SnapshotableInfoPanel):
  """Model for Org Group object Info pages and Info panels."""
  _locators = locator.WidgetInfoOrgGroup
  dropdown_settings_cls = widget_info.OrgGroups

  def __init__(self, driver):
    super(OrgGroups, self).__init__(driver)


class Vendors(SnapshotableInfoPanel):
  """Model for Vendor object Info pages and Info panels."""
  _locators = locator.WidgetInfoVendor

  def __init__(self, driver):
    super(Vendors, self).__init__(driver)


class AccessGroup(SnapshotableInfoPanel):
  """Model for Access Group object Info pages and Info panels."""
  _locators = locator.WidgetInfoAccessGroup

  def __init__(self, driver):
    super(AccessGroup, self).__init__(driver)


class Systems(SnapshotableInfoPanel):
  """Model for System object Info pages and Info panels."""
  _locators = locator.WidgetInfoSystem
  dropdown_settings_cls = widget_info.Systems

  def __init__(self, driver):
    super(Systems, self).__init__(driver)


class Processes(SnapshotableInfoPanel):
  """Model for Process object Info pages and Info panels."""
  _locators = locator.WidgetInfoProcess
  dropdown_settings_cls = widget_info.Processes

  def __init__(self, driver):
    super(Processes, self).__init__(driver)


class DataAssets(SnapshotableInfoPanel):
  """Model for Data Asset object Info pages and Info panels."""
  _locators = locator.WidgetInfoDataAsset
  dropdown_settings_cls = widget_info.DataAssets

  def __init__(self, driver):
    super(DataAssets, self).__init__(driver)


class Products(SnapshotableInfoPanel):
  """Model for Product object Info pages and Info panels."""
  _locators = locator.WidgetInfoProduct
  dropdown_settings_cls = widget_info.Products

  def __init__(self, driver):
    super(Products, self).__init__(driver)


class Projects(SnapshotableInfoPanel):
  """Model for Project object Info pages and Info panels."""
  _locators = locator.WidgetInfoProject
  dropdown_settings_cls = widget_info.Projects

  def __init__(self, driver):
    super(Projects, self).__init__(driver)


class Facilities(SnapshotableInfoPanel):
  """Model for Facility object Info pages and Info panels."""
  _locators = locator.WidgetInfoFacility

  def __init__(self, driver):
    super(Facilities, self).__init__(driver)


class Markets(SnapshotableInfoPanel):
  """Model for Market object Info pages and Info panels."""
  _locators = locator.WidgetInfoMarket

  def __init__(self, driver):
    super(Markets, self).__init__(driver)


class Risks(SnapshotableInfoPanel):
  """Model for Risk object Info pages and Info panels."""
  _locators = locator.WidgetInfoRisk

  def __init__(self, driver):
    super(Risks, self).__init__(driver)


class Threats(SnapshotableInfoPanel):
  """Model for Threat object Info pages and Info panels."""
  _locators = locator.WidgetInfoThreat

  def __init__(self, driver):
    super(Threats, self).__init__(driver)


class Dashboard(CommonInfo):
  """Model for Dashboard object Info pages and Info panels."""
  _locators = locator.Dashboard

  def __init__(self, driver):
    super(Dashboard, self).__init__(driver)
    self.button_start_new_program = base.Button(
        self._driver, self._locators.BUTTON_START_NEW_PROGRAM)
    self.button_start_new_audit = base.Button(
        self._driver, self._locators.BUTTON_START_NEW_AUDIT)
    self.button_start_new_workflow = base.Button(
        self._driver, self._locators.BUTTON_START_NEW_WORKFLOW)
    self.button_create_new_object = base.Button(
        self._driver, self._locators.BUTTON_CREATE_NEW_OBJECT)
    self.button_all_objects = base.Button(
        self._driver, self._locators.BUTTON_ALL_OBJECTS)
