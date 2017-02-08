# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Page object models for the info widget of the object"""


from lib import base
from lib.constants import locator
from lib.element import widget_info


class Widget(base.Widget):
  """Abstract class for all info widgets"""
  _locator = None
  _dropdown_settings_cls = None

  def __init__(self, driver):
    # wait that the elements load before calling super
    self.button_settings = base.Button(
        driver, locator.BaseInfoWidget.BUTTON_SETTINGS)
    self.title = base.Label(driver, self._locator.TITLE)
    self.title_entered = base.Label(
        driver, self._locator.TITLE_ENTERED)

    super(Widget, self).__init__(driver)
    self.object_id = self.url.split("/")[-1]

  def press_object_settings(self):
    """
    Returns:
        widget_info.DropdownSettings
    """
    self.button_settings.click()
    return self._dropdown_settings_cls(self._driver)


class DashboardInfo(Widget):
  """Model for the dashboard info widget"""
  _locator = locator.Dashboard

  def __init__(self, driver):
    super(DashboardInfo, self).__init__(driver)

    self.button_start_new_program = base.Button(
        self._driver, self._locator.BUTTON_START_NEW_PROGRAM)
    self.button_start_new_audit = base.Button(
        self._driver, self._locator.BUTTON_START_NEW_AUDIT)
    self.button_start_new_workflow = base.Button(
        self._driver, self._locator.BUTTON_START_NEW_WORKFLOW)
    self.button_create_new_object = base.Button(
        self._driver, self._locator.BUTTON_CREATE_NEW_OBJECT)
    self.button_all_objects = base.Button(
        self._driver, self._locator.BUTTON_ALL_OBJECTS)

  def start_new_program(self):
    raise NotImplementedError

  def start_new_audit(self):
    raise NotImplementedError

  def start_new_workflow(self):
    raise NotImplementedError

  def create_new_object(self):
    raise NotImplementedError

  def browse_all_objects(self):
    raise NotImplementedError


class Programs(Widget):
  """Model for program object info widget"""
  _locator = locator.WidgetInfoProgram
  _dropdown_settings_cls = widget_info.Programs

  def __init__(self, driver):
    """
    Args:
        driver (base.CustomDriver)
    """
    super(Programs, self).__init__(driver)

    self.object_review = base.Label(
        self._driver, self._locator.OBJECT_REVIEW)
    self.submit_for_review = base.Label(
        self._driver, self._locator.SUBMIT_FOR_REVIEW)
    self.description = base.Label(self._driver, self._locator.DESCRIPTION)
    self.description_entered = base.Label(
        self._driver, self._locator.DESCRIPTION_ENTERED)
    self.notes = base.Label(self._driver, self._locator.NOTES)
    self.notes_entered = base.Label(
        self._driver, self._locator.NOTES_ENTERED)
    self.manager = base.Label(self._driver, self._locator.MANAGER)
    self.manager_entered = base.Label(
        self._driver, self._locator.MANAGER_ENTERED)
    self.program_url = base.Label(self._driver, self._locator.PROGRAM_URL)
    self.program_url_entered = base.Label(
        self._driver, self._locator.PROGRAM_URL_ENTERED)
    self.code = base.Label(self._driver, self._locator.CODE)
    self.code_entered = base.Label(
        self._driver, self._locator.CODE_ENTERED)
    self.effective_date = base.Label(
        self._driver, self._locator.EFFECTIVE_DATE)
    self.effective_date_entered = base.Label(
        self._driver, self._locator.EFFECTIVE_DATE_ENTERED)
    self.stop_date = base.Label(self._driver, self._locator.STOP_DATE)
    self.stop_date_entered = base.Label(
        self._driver, self._locator.STOP_DATE_ENTERED)
    self.primary_contact = base.Label(
        self._driver, self._locator.PRIMARY_CONTACT)
    self.primary_contact_entered = base.Label(
        self._driver, self._locator.PRIMARY_CONTACT_ENTERED)
    self.secondary_contact = base.Label(
        self._driver, self._locator.SECONDARY_CONTACT)
    self.secondary_contact_entered = base.Label(
        self._driver, self._locator.SECONDARY_CONTACT_ENTERED)
    self.reference_url = base.Label(
        self._driver, self._locator.REFERENCE_URL)
    self.reference_url_entered = base.Label(
        self._driver, self._locator.REFERENCE_URL_ENTERED)


class Workflows(Widget):
  """Model for workflow object info widget"""
  _locator = locator.WidgetInfoWorkflow


class Audits(Widget):
  """Model for audit object info widget"""
  _locator = locator.WidgetInfoAudit


class Assessments(Widget):
  """Model for assessment object info widget"""
  _locator = locator.WidgetInfoAssessment


class Issues(Widget):
  """Model for issue object info widget"""
  _locator = locator.WidgetInfoIssue


class Regulations(Widget):
  """Model for regulation object info widget"""
  _locator = locator.WidgetInfoRegulations


class Policies(Widget):
  """Model for policies object info widget"""
  _locator = locator.WidgetInfoPolicy


class Standards(Widget):
  """Model for standard object info widget"""
  _locator = locator.WidgetInfoStandard


class Contracts(Widget):
  """Model for contract object info widget"""
  _locator = locator.WidgetInfoContract


class Clauses(Widget):
  """Model for clause object info widget"""
  _locator = locator.WidgetInfoClause


class Sections(Widget):
  """Model for selection object info widget"""
  _locator = locator.WidgetInfoSection


class Controls(Widget):
  """Model for control object info widget"""
  _locator = locator.WidgetInfoControl
  _dropdown_settings_cls = widget_info.Controls


class Objectives(Widget):
  """Model for objectives object info widget"""
  _locator = locator.WidgetInfoObjective


class People(base.Widget):
  """Model for people object info widget"""
  _locator = locator.WidgetInfoPeople


class OrgGroups(Widget):
  """Model for org groups object info widget"""
  _locator = locator.WidgetInfoOrgGroup
  _dropdown_settings_cls = widget_info.OrgGroups


class Vendors(Widget):
  """Model for vendors object info widget"""
  _locator = locator.WidgetInfoVendor


class AccessGroup(Widget):
  """Model for access group object info widget"""
  _locator = locator.WidgetInfoAccessGroup


class Systems(Widget):
  """Model for system object info widget"""
  _locator = locator.WidgetInfoSystem
  _dropdown_settings_cls = widget_info.Systems


class Processes(Widget):
  """Model for process object info widget"""
  _locator = locator.WidgetInfoProcess
  _dropdown_settings_cls = widget_info.Processes


class DataAssets(Widget):
  """Model for data asset object info widget"""
  _locator = locator.WidgetInfoDataAsset
  _dropdown_settings_cls = widget_info.DataAssets


class Products(Widget):
  """Model for product object info widget"""
  _locator = locator.WidgetInfoProduct
  _dropdown_settings_cls = widget_info.Products


class Projects(Widget):
  """Model for project object info widget"""
  _locator = locator.WidgetInfoProject
  _dropdown_settings_cls = widget_info.Projects


class Facilities(Widget):
  """Model for facility object info widget"""
  _locator = locator.WidgetInfoFacility


class Markets(Widget):
  """Model for market object info widget"""
  _locator = locator.WidgetInfoMarket


class Risks(Widget):
  """Model for risk object info widget"""
  _locator = locator.WidgetInfoRisk


class Threats(Widget):
  """Model for threat object info widget"""
  _locator = locator.WidgetInfoThreat
