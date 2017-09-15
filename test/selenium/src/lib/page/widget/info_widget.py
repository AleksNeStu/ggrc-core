# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Info widgets."""
# pylint: disable=useless-super-delegation

from lib import base
from lib.constants import locator, objects, element, roles
from lib.constants.locator import WidgetInfoAssessment
from lib.element import widget_info, tab_containers
from lib.page.modal import update_object
from lib.utils import selenium_utils


class CommonInfo(base.Widget):
  """Abstract class of common info for Info pages and Info panels."""
  _locators = locator.CommonWidgetInfo
  dropdown_settings_cls = widget_info.CommonInfoDropdownSettings
  locator_headers_and_values = None
  all_headers_and_values = []
  cas_headers_and_values = []
  list_all_headers_text = []
  list_all_values_text = []

  def __init__(self, driver):
    super(CommonInfo, self).__init__(driver)
    self.locator_headers_and_values = self._locators.HEADERS_AND_VALUES

  def title(self):
    return base.Label(self._driver, self._locators.TITLE)

  def title_entered(self):
    return base.Label(self._driver, self._locators.TITLE_ENTERED)

  def state(self):
    return base.Label(self._driver, self._locators.STATE)

  def open_info_3bbs(self):
    """Click to 3BBS button on Info page or Info panel to open info 3BBS modal.
    Return: lib.element.widget_info."obj_name"DropdownSettings
    """
    base.Button(self._driver, self._locators.BUTTON_3BBS).click()
    return self.dropdown_settings_cls(self._driver)

  def get_header_and_value_text_from_custom_scopes(self, header_text,
                                                   custom_scopes_locator=None):
    """Get one header and one value elements text from custom scopes elements
    according to scopes locator and header text.
    Example:
    If header_text is 'header' :return ['header', 'value']
    """
    # pylint: disable=not-an-iterable
    # pylint: disable=invalid-name
    selenium_utils.wait_for_js_to_load(self._driver)
    if custom_scopes_locator:
      self.all_headers_and_values = self._driver.find_elements(
          *custom_scopes_locator)
    if not custom_scopes_locator and self.locator_headers_and_values:
      self.all_headers_and_values = self._driver.find_elements(
          *self.locator_headers_and_values)
    header_and_value = (
        next((scope.text.splitlines() + [None]
              if len(scope.text.splitlines()) == 1
              else scope.text.splitlines()[:2]
              for scope in self.all_headers_and_values
              if header_text in scope.text), [None, None]))
    return header_and_value

  def get_headers_and_values_dict_from_cas_scopes(self, is_gcas_not_lcas=True):  # noqa: ignore=C901
    """Get text of all CAs headers and values elements scopes and convert it to
    dictionary. If 'is_gcas_not_lcas' then get GCAs, if not 'is_gcas_not_lcas'
    then get LCAs.
    Example:
    :return {'ca_header1': 'ca_value1', 'ca_header2': 'ca_value2', ...}
    """
    # pylint: disable=invalid-name
    # pylint: disable=too-many-branches
    # if not self.cas_headers_and_values and not is_gcas_not_lcas:
    selenium_utils.wait_for_js_to_load(self._driver)
    cas_locator = (self._locators.CAS_HEADERS_AND_VALUES if is_gcas_not_lcas
                   else self._locators.LCAS_HEADERS_AND_VALUES)
    self.cas_headers_and_values = self._driver.find_elements(*cas_locator)

    dict_cas_scopes = {None: None}
    if len(self.cas_headers_and_values) >= 1:
      list_text_cas_scopes = []
      for scope in self.cas_headers_and_values:
        ca_header_text = scope.text.splitlines()[0]
        if len(scope.text.splitlines()) >= 2:
          if scope.text.splitlines()[1].strip():
            list_text_cas_scopes.append(
                [ca_header_text, scope.text.splitlines()[1]])
          else:
            list_text_cas_scopes.append([ca_header_text, None])
        if len(scope.text.splitlines()) == 1:
          if (element.AdminWidgetCustomAttributes.CHECKBOX.upper() in
                  ca_header_text):
            list_text_cas_scopes.append(
                [ca_header_text,
                 unicode(int(base.Checkbox(self._driver, scope.find_element(
                     *self._locators.CAS_CHECKBOXES)).is_checked_via_js()))
                 ])
          else:
            list_text_cas_scopes.append([ca_header_text, None])
      cas_headers, _cas_values = [list(text_cas_scope) for text_cas_scope
                                  in zip(*list_text_cas_scopes)]
      # conversion
      cas_values = []
      for ca_val in _cas_values:
        if ca_val is None:
          cas_values.append(None)
        elif ca_val == roles.DEFAULT_USER:
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
      dict_cas_scopes = dict(zip(cas_headers, cas_values))
    return dict_cas_scopes

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

  def button_maximize_minimize(self):
    """Button (toggle) maximize and minimize for Info Panels."""
    return base.Toggle(self._driver, self._locators.BUTTON_MAXIMIZE_MINIMIZE,
                       locator.Common.NORMAL)

  def button_close(self):
    """Button close for Info Panels."""
    return self._driver.find_element(*self._locators.BUTTON_CLOSE)


class SnapshotableInfoPanel(InfoPanel):
  """Class for Info Panels of snapshotable objects."""
  # pylint: disable=too-few-public-methods
  _locators = locator.WidgetSnapshotsInfoPanel
  dropdown_settings_cls = widget_info.Snapshots
  locator_link_get_latest_ver = _locators.LINK_GET_LAST_VER

  def __init__(self, driver):
    super(SnapshotableInfoPanel, self).__init__(driver)

  def snapshot_obj_version(self):
    """Label of snapshot version"""
    return base.Label(self._driver, self._locators.SNAPSHOT_OBJ_VER)

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
    self.ref_url = base.MultiInputField(
        self._driver, self._locators.REF_URL_CSS)
    self.code = base.Label(self._driver, self._locators.CODE)
    self.code_entered = base.Label(self._driver, self._locators.CODE_ENTERED)
    self.effective_date = base.Label(
        self._driver, self._locators.EFFECTIVE_DATE)
    self.effective_date_entered = base.Label(
        self._driver, self._locators.EFFECTIVE_DATE_ENTERED)


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
        self.get_header_and_value_text_from_custom_scopes(
            self._elements.AUDIT_LEAD.upper()))
    self.code_text, self.code_entered_text = (
        self.get_header_and_value_text_from_custom_scopes(
            self._elements.CODE.upper()))
    self.cas_text = self.get_headers_and_values_dict_from_cas_scopes()
    # all obj scopes
    self.list_all_headers_text = [
        self._elements.CAS.upper(), self.title().text,
        self._elements.STATUS.upper(), self.audit_lead_text,
        self.code_text]
    self.list_all_values_text = [
        self.cas_text, self.title_entered().text,
        objects.get_normal_form(self.state().text),
        self.audit_lead_entered_text, self.code_entered_text]


class Assessments(InfoPanel):
  """Model for Assessment object Info pages and Info panels."""
  # pylint: disable=invalid-name
  # pylint: disable=too-many-instance-attributes
  _locators = locator.WidgetInfoAssessment
  _elements = element.AssessmentInfoWidget
  dropdown_settings_cls = widget_info.Assessments

  def __init__(self, driver):
    super(Assessments, self).__init__(driver)
    self.verified = selenium_utils.is_element_exist(
        self._driver, self._locators.ICON_VERIFIED)
    self.workflow_container = tab_containers.AssessmentTabContainer(
        self._driver,
        self._driver.find_element(*self._locators.ASMT_TAB_CONTAINER_CSS))
    self.workflow_container.switch_to_tab(
        element.AssessmentTabContainer.ASMT_TAB)
    self.mapped_objects_titles_text = self._get_mapped_objs_titles()
    self.lcas_text = self.get_headers_and_values_dict_from_cas_scopes(
        is_gcas_not_lcas=False)
    self.creators_text, self.creators_entered_text = (
        self.get_header_and_value_text_from_custom_scopes(
            self._elements.CREATORS_.upper(),
            self._locators.PEOPLE_HEADERS_AND_VALUES))
    self.assignees_text, self.assignees_entered_text = (
        self.get_header_and_value_text_from_custom_scopes(
            self._elements.ASSIGNEES_.upper(),
            self._locators.PEOPLE_HEADERS_AND_VALUES))
    self.verifiers_text, self.verifiers_entered_text = (
        self.get_header_and_value_text_from_custom_scopes(
            self._elements.VERIFIERS_.upper(),
            self._locators.PEOPLE_HEADERS_AND_VALUES))
    self.comments = base.CommentsPanel(
        self._driver, self._locators.COMMENTS_CSS)
    self.comments_scopes = self.comments.scopes

  def _get_mapped_objs_titles(self):
    """Return lists of str for mapped snapshots titles from current tab."""
    mapped_items = self._driver.find_elements(
        *self._locators.MAPPED_SNAPSHOTS_CSS)
    return [mapped_el.find_element(
            *self._locators.MAPPED_SNAPSHOT_TITLE_CSS).text
            for mapped_el in mapped_items]

  def get_info_widget_obj_scope(self):
    """Get an Assessment object's text scope (headers' (real and synthetic)
    and values' txt) from Info Widget navigating through the Assessment's tabs.
    """
    self.workflow_container.switch_to_tab(
        element.AssessmentTabContainer.OTHER_ATTRS_TAB)
    self.mapped_objects_titles_text += self._get_mapped_objs_titles()
    cas_text = self.get_headers_and_values_dict_from_cas_scopes()
    code_section = base.Label(self._driver, self._locators.CODE_CSS)
    code_text = code_section.element.find_element(
        *self._locators.CODE_HEADER_CSS).text
    code_entered_text = code_section.element.find_element(
        *self._locators.CODE_VALUE_CSS).text
    # todo: implement separate entities' model for asmts' lcas and gcas
    cas_text.update(self.lcas_text)
    self.list_all_headers_text = [
        self._elements.CAS.upper(), self._elements.TITLE,
        self._elements.STATE.upper(),
        self._elements.VERIFIED.upper(),
        self.creators_text, self.assignees_text,
        self.verifiers_text, self._elements.MAPPED_OBJECTS.upper(),
        code_text, self.comments.header_lbl.text]
    self.list_all_values_text = [
        cas_text, self.title_entered().text,
        objects.get_normal_form(self.state().text),
        self.verified,
        self.creators_entered_text, self.assignees_entered_text,
        self.verifiers_entered_text, self.mapped_objects_titles_text,
        code_entered_text, self.comments_scopes]
    return dict(zip(self.list_all_headers_text, self.list_all_values_text))

  def click_complete(self):
    base.Button(self._driver, WidgetInfoAssessment.BUTTON_COMPLETE).click()

  def click_verify(self):
    base.Button(self._driver, WidgetInfoAssessment.BUTTON_VERIFY).click()

  def click_needs_rework(self):
    base.Button(self._driver, WidgetInfoAssessment.BUTTON_NEEDS_REWORK).click()


class AssessmentTemplates(InfoPanel):
  """Model for Assessment Template object Info pages and Info panels."""
  _locators = locator.WidgetInfoAssessmentTemplate

  def __init__(self, driver):
    super(AssessmentTemplates, self).__init__(driver)


class Issues(InfoPanel):
  """Model for Issue object Info pages and Info panels."""
  _locators = locator.WidgetInfoIssue
  _elements = element.IssueInfoWidget

  def __init__(self, driver):
    super(Issues, self).__init__(driver)
    self.code_text, self.code_entered_text = (
        self.get_header_and_value_text_from_custom_scopes(
            self._elements.CODE.upper()))
    # all obj scopes
    self.list_all_headers_text = [
        self.title().text,
        self._elements.STATE.upper(),
        self.code_text]
    self.list_all_values_text = [
        self.title_entered().text,
        objects.get_normal_form(self.state().text),
        self.code_entered_text]


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
    self.code_text, self.code_entered_text = (
        self.get_header_and_value_text_from_custom_scopes(
            self._elements.CODE.upper()))
    self.admin_text, self.admin_entered_text = (
        self.get_header_and_value_text_from_custom_scopes(
            self._elements.ADMIN.upper(),
            self._locators.PEOPLE_HEADERS_AND_VALUES))
    self.primary_contact_text, self.primary_contact_entered_text = (
        self.get_header_and_value_text_from_custom_scopes(
            self._elements.PRIMARY_CONTACT.upper(),
            self._locators.PEOPLE_HEADERS_AND_VALUES))
    self.cas_text = self.get_headers_and_values_dict_from_cas_scopes()
    # scope
    self.list_all_headers_text = [
        self._elements.CAS.upper(), self.title().text,
        self._elements.STATE.upper(), self.admin_text,
        self.primary_contact_text, self.code_text]
    self.list_all_values_text = [
        self.cas_text, self.title_entered().text,
        objects.get_normal_form(self.state().text), self.admin_entered_text,
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
