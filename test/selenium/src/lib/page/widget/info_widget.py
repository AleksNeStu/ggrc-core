# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Info widgets."""
# pylint: disable=useless-super-delegation
# pylint: disable=attribute-defined-outside-init

import re

from lib import base
from lib.constants import locator, objects, element, roles
from lib.constants.locator import WidgetInfoAssessment
from lib.element import widget_info, tab_containers
from lib.page.modal import update_object
from lib.utils import selenium_utils, string_utils, help_utils


class InfoWidget(base.Widget):
  """Abstract class of common info for Info pages and Info panels.
  For labels (headers) Will be used actual unicode elements from UI or pseudo
  string elements from 'lib.element' module in upper case.
  """
  # pylint: disable=too-many-instance-attributes
  _locators = locator.CommonWidgetInfo
  _elements = element.Common
  dropdown_settings_cls = widget_info.CommonInfoDropdownSettings
  locator_headers_and_values = None

  def __init__(self, driver):
    super(InfoWidget, self).__init__(driver)
    self.child_cls_name = self.__class__.__name__.lower()
    self.list_all_headers_txt = []
    self.list_all_values_txt = []
    self.info_widget_locator = (
        self._locators.INFO_PAGE_ELEM if self.is_info_page else
        self._locators.INFO_PANEL_ELEM)
    self.info_widget_elem = selenium_utils.get_when_visible(
        self._driver, self.info_widget_locator)
    # common for all objects
    self.title_lbl_txt = self.get_title_lbl_txt()
    self.title = base.Element(
        self.info_widget_elem, self._locators.TITLE_ENTERED)
    self.state_lbl_txt = self._elements.STATE.upper()
    self.state_txt = self.get_state_txt()
    self._extend_list_all_scopes(
        [self.title_lbl_txt, self.state_lbl_txt],
        [self.title.text, self.state_txt])
    self.info_3bbs_btn = selenium_utils.get_when_visible(
        self.info_widget_elem, self._locators.BUTTON_3BBS)
    # for Info Page
    if self.is_info_page:
      self.info_page_footer = base.Label(
          self.info_widget_elem, self._locators.TXT_FOOTER_CSS)
      self.modified_by = selenium_utils.get_when_visible(
          self.info_widget_elem, self._locators.TXT_MODIFIED_BY_CSS)
      _created_at_txt, _updated_at_txt = (
          self.info_page_footer.text.split(string_utils.WHITESPACE * 6))
      self.created_at_txt = (
          re.sub("Created at", string_utils.BLANK, _created_at_txt))
      self.updated_at_txt = (
          _updated_at_txt.splitlines()[1].replace("on ", string_utils.BLANK))
      self._extend_list_all_scopes(
          [self._elements.CREATED_AT.upper(),
           self._elements.MODIFIED_BY.upper(),
           self._elements.UPDATED_AT.upper()],
          [self.created_at_txt, self.modified_by.text, self.updated_at_txt])
    # for Info Panel
    else:
      self.panel = (
          SnapshotableInfoPanel(self._driver, self.info_widget_elem)
          if self.child_cls_name in objects.ALL_SNAPSHOTABLE_OBJS else
          InfoPanel(self._driver, self.info_widget_elem))

  def get_title_lbl_txt(self):
    """Get title's label text from Info Widget."""
    return base.Label(self.info_widget_elem, self._locators.TITLE).text

  def get_state_txt(self):
    """Get object's state text from Info Widget."""
    return objects.get_normal_form(
        base.Label(self.info_widget_elem, self._locators.STATE).text)

  def get_review_state_txt(self):
    """Get object's review state text from Info Widget checking if exact UI
    elements are existed.
    """
    return (element.ReviewStates.REVIEWED if selenium_utils.is_element_exist(
        self.info_widget_elem, self._locators.TXT_OBJECT_REVIEWED) else
        element.ReviewStates.UNREVIEWED)

  def open_info_3bbs(self):
    """Click to 3BBS button on Info page or Info panel to open info 3BBS modal.
    Return: lib.element.widget_info."obj_name"DropdownSettings
    """
    self.info_3bbs_btn.click()
    return self.dropdown_settings_cls(self._driver)

  def get_header_and_value_txt_from_custom_scopes(self, header_text,
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
      self.all_headers_and_values = self.info_widget_elem.find_elements(
          *custom_scopes_locator)
    if not custom_scopes_locator and self._locators.HEADERS_AND_VALUES:
      self.all_headers_and_values = self.info_widget_elem.find_elements(
          *self._locators.HEADERS_AND_VALUES)
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
    self.cas_headers_and_values = (
        self.info_widget_elem.find_elements(*cas_locator))
    dict_cas_scopes = {}
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
    return dict(zip(self.list_all_headers_txt, self.list_all_values_txt))

  def _extend_list_all_scopes(self, headers, values):
    """Extend 'list all scopes' by headers' text and values' text."""
    self.list_all_headers_txt.extend(help_utils.convert_to_list(headers))
    self.list_all_values_txt.extend(help_utils.convert_to_list(values))

  def extend_list_all_scopes_by_code(self):
    """Set attributes related to 'code' and extend 'list all scopes'
    accordingly.
    """
    self.code_lbl_txt, self.code_txt = (
        self.get_header_and_value_txt_from_custom_scopes(
            self._elements.CODE.upper()))
    self._extend_list_all_scopes(self.code_lbl_txt, self.code_txt)

  def extend_list_all_scopes_by_cas(self):
    """Set attributes related to 'global custom attributes' and extend
    'list all scopes' accordingly.
    """
    self.cas_lbl_txt = self._elements.CAS.upper()
    self.cas_scope_txt = self.get_headers_and_values_dict_from_cas_scopes()
    self._extend_list_all_scopes(self.cas_lbl_txt, self.cas_scope_txt)

  def extend_list_all_scopes_by_review_state(self):
    """Set attributes related to 'review state' and extend
    'list all scopes' accordingly.
    """
    # pylint: disable=invalid-name
    self.review_state_lbl = base.Label(
        self.info_widget_elem, self._locators.TXT_OBJECT_REVIEW)
    self.review_state_txt = self.get_review_state_txt()
    self._extend_list_all_scopes(
        self.review_state_lbl.text, self.review_state_txt)


class InfoPanel(object):
  """Class for Info Panels."""
  _locators = locator.WidgetInfoPanel

  def __init__(self, driver, info_widget_elem):
    self._driver = driver
    self.info_widget_elem = info_widget_elem

  def button_maximize_minimize(self):
    """Button (toggle) maximize and minimize for Info Panels."""
    return base.Toggle(
        self.info_widget_elem, self._locators.BUTTON_MAXIMIZE_MINIMIZE,
        locator.Common.NORMAL)

  def button_close(self):
    """Button close for Info Panels."""
    return self.info_widget_elem.find_element(*self._locators.BUTTON_CLOSE)


class SnapshotableInfoPanel(InfoPanel):
  """Class for Info Panels of snapshotable objects."""
  # pylint: disable=too-few-public-methods
  _locators = locator.WidgetSnapshotsInfoPanel
  dropdown_settings_cls = widget_info.Snapshots
  locator_link_get_latest_ver = _locators.LINK_GET_LAST_VER

  def snapshot_obj_version(self):
    """Label of snapshot version"""
    return base.Label(self.info_widget_elem, self._locators.SNAPSHOT_OBJ_VER)

  def open_link_get_latest_ver(self):
    """Click on link get latest version under Info panel."""
    base.Button(self.info_widget_elem,
                self.locator_link_get_latest_ver).click()
    return update_object.CompareUpdateObjectModal(self._driver)

  def is_link_get_latest_ver_exist(self):
    """Find link get latest version under Info panel.
    Return: True if link get latest version is exist,
            False if link get latest version is not exist.
    """
    return selenium_utils.is_element_exist(
        self.info_widget_elem, self.locator_link_get_latest_ver)


class Programs(InfoWidget):
  """Model for program object Info pages and Info panels."""
  # pylint: disable=too-many-instance-attributes
  _locators = locator.WidgetInfoProgram
  dropdown_settings_cls = widget_info.Programs

  def __init__(self, driver):
    super(Programs, self).__init__(driver)
    # todo redesign 'Programs' cls init and related methods and tests
    self.show_advanced = base.Toggle(
        self.info_widget_elem, self._locators.TOGGLE_SHOW_ADVANCED)
    self.show_advanced.toggle()
    self.object_review = base.Label(
        self.info_widget_elem, self._locators.TXT_OBJECT_REVIEW)
    self.submit_for_review = base.Label(
        self.info_widget_elem, self._locators.LINK_SUBMIT_FOR_REVIEW)
    self.description = base.Label(
        self.info_widget_elem, self._locators.DESCRIPTION)
    self.description_entered = base.Label(
        self.info_widget_elem, self._locators.DESCRIPTION_ENTERED)
    self.notes = base.Label(self.info_widget_elem, self._locators.NOTES)
    self.notes_entered = base.Label(
        self.info_widget_elem, self._locators.NOTES_ENTERED)
    self.manager = base.Label(self.info_widget_elem, self._locators.MANAGER)
    self.manager_entered = base.Label(
        self.info_widget_elem, self._locators.MANAGER_ENTERED)
    self.ref_url = base.MultiInputField(
        self.info_widget_elem, self._locators.REF_URL_CSS)
    self.code = base.Label(self.info_widget_elem, self._locators.CODE)
    self.code_entered = base.Label(
        self.info_widget_elem, self._locators.CODE_ENTERED)
    self.effective_date = base.Label(
        self.info_widget_elem, self._locators.EFFECTIVE_DATE)
    self.effective_date_entered = base.Label(
        self.info_widget_elem, self._locators.EFFECTIVE_DATE_ENTERED)


class Workflows(InfoWidget):
  """Model for Workflow object Info pages and Info panels."""
  _locators = locator.WidgetInfoWorkflow

  def __init__(self, driver):
    super(Workflows, self).__init__(driver)
    self.extend_list_all_scopes_by_code()
    self.extend_list_all_scopes_by_cas()


class Audits(InfoWidget):
  """Model for Audit object Info pages and Info panels."""
  # pylint: disable=too-many-instance-attributes
  _locators = locator.WidgetInfoAudit
  _elements = element.AuditInfoWidget
  dropdown_settings_cls = widget_info.Audits

  def __init__(self, driver):
    super(Audits, self).__init__(driver)
    self.extend_list_all_scopes_by_code()
    self.extend_list_all_scopes_by_cas()
    self.audit_captain_lbl_txt, self.audit_captain_txt = (
        self.get_header_and_value_txt_from_custom_scopes(
            self._elements.AUDIT_CAPTAIN.upper()))
    self._extend_list_all_scopes(
        self.audit_captain_lbl_txt, self.audit_captain_txt)


class Assessments(InfoWidget):
  """Model for Assessment object Info pages and Info panels."""
  # pylint: disable=invalid-name
  # pylint: disable=too-many-instance-attributes
  _locators = locator.WidgetInfoAssessment
  _elements = element.AssessmentInfoWidget
  dropdown_settings_cls = widget_info.Assessments

  def __init__(self, driver):
    super(Assessments, self).__init__(driver)
    self.title_lbl = self.get_title_lbl_txt()
    self.is_verified_lbl_txt = self._elements.VERIFIED.upper()
    self.is_verified = selenium_utils.is_element_exist(
        self.info_widget_elem, self._locators.ICON_VERIFIED)
    self.workflow_container = tab_containers.AssessmentTabContainer(
        self._driver,
        self.info_widget_elem.find_element(
            *self._locators.ASMT_TAB_CONTAINER_CSS))
    self.workflow_container.tab_controller.active_tab = (
        element.AssessmentTabContainer.ASMT_TAB)
    self.mapped_objects_lbl_txt = self._elements.MAPPED_OBJECTS.upper()
    self.mapped_objects_titles_txt = self._get_mapped_objs_titles_txt()
    self.lcas_scope_txt = self.get_headers_and_values_dict_from_cas_scopes(
        is_gcas_not_lcas=False)
    self.creators_lbl_txt, self.creators_txt = (
        self.get_header_and_value_txt_from_custom_scopes(
            self._elements.CREATORS_.upper(),
            self._locators.PEOPLE_HEADERS_AND_VALUES))
    self.assignees_lbl_txt, self.assignees_txt = (
        self.get_header_and_value_txt_from_custom_scopes(
            self._elements.ASSIGNEES_.upper(),
            self._locators.PEOPLE_HEADERS_AND_VALUES))
    self.verifiers_lbl_txt, self.verifiers_txt = (
        self.get_header_and_value_txt_from_custom_scopes(
            self._elements.VERIFIERS_.upper(),
            self._locators.PEOPLE_HEADERS_AND_VALUES))
    self.comments_panel = base.CommentsPanel(
        self.info_widget_elem, self._locators.COMMENTS_CSS)
    self.comments_lbl_txt = self.comments_panel.header_lbl.text
    self.comments_scopes_txt = self.comments_panel.scopes
    # todo: implement separate add lcas and gcas
    # todo: implement separate add mapped ctrls and mapped other objs
    self._extend_list_all_scopes(
        [self.is_verified_lbl_txt, self.creators_lbl_txt,
         self.assignees_lbl_txt, self.verifiers_lbl_txt,
         self.mapped_objects_lbl_txt, self.comments_lbl_txt],
        [self.is_verified, self.creators_txt, self.assignees_txt,
         self.verifiers_txt, self.mapped_objects_titles_txt,
         self.comments_scopes_txt])

  def get_title_lbl_txt(self):
    """Get title's label element from Assessment's Info Widget."""
    #  Issue in app GGRC-3451
    return (self._elements.TITLE.upper() if self.is_info_page else
            super(Assessments, self).get_title_lbl_txt())

  def _get_mapped_objs_titles_txt(self):
    """Return lists of str for mapped snapshots titles text from current tab.
    """
    mapped_items = self.info_widget_elem.find_elements(
        *self._locators.MAPPED_SNAPSHOTS_CSS)
    return [mapped_el.find_element(
            *self._locators.MAPPED_SNAPSHOT_TITLE_CSS).text
            for mapped_el in mapped_items]

  def get_info_widget_obj_scope(self):
    """Get an Assessment object's text scope (headers' (real and synthetic)
    and values' txt) from Info Widget navigating through the Assessment's tabs.
    """
    self.workflow_container.tab_controller.active_tab = (
        element.AssessmentTabContainer.OTHER_ATTRS_TAB)
    self.mapped_objects_titles_txt += self._get_mapped_objs_titles_txt()
    self.extend_list_all_scopes_by_code()
    self.extend_list_all_scopes_by_cas()
    return dict(zip(self.list_all_headers_txt, self.list_all_values_txt))

  def extend_list_all_scopes_by_code(self):
    """Set attributes related to 'code' and extend 'list all scopes'
    accordingly.
    """
    code_elem = base.Label(self.info_widget_elem, self._locators.CODE_CSS)
    self.code_lbl_txt = code_elem.element.find_element(
        *self._locators.CODE_HEADER_CSS).text
    self.code_txt = code_elem.element.find_element(
        *self._locators.CODE_VALUE_CSS).text
    self._extend_list_all_scopes(self.code_lbl_txt, self.code_txt)

  def extend_list_all_scopes_by_cas(self):
    """Set attributes related to 'local and global custom attributes' and
    extend 'list all scopes' accordingly.
    """
    # todo: implement separate entities' model for lcas and gcas
    self.cas_lbl_txt = self._elements.CAS.upper()
    self.cas_scope_txt = self.get_headers_and_values_dict_from_cas_scopes()
    self.cas_scope_txt.update(self.lcas_scope_txt)
    self._extend_list_all_scopes(self.cas_lbl_txt, self.cas_scope_txt)

  def click_complete(self):
    """Click on 'Complete' button."""
    base.Button(self.info_widget_elem,
                WidgetInfoAssessment.BUTTON_COMPLETE).click()

  def click_verify(self):
    """Click on 'Verify' button."""
    base.Button(self.info_widget_elem,
                WidgetInfoAssessment.BUTTON_VERIFY).click()

  def click_needs_rework(self):
    """Click on 'Needs Rework' button."""
    base.Button(self.info_widget_elem,
                WidgetInfoAssessment.BUTTON_NEEDS_REWORK).click()


class AssessmentTemplates(InfoWidget):
  """Model for Assessment Template object Info pages and Info panels."""
  _locators = locator.WidgetInfoAssessmentTemplate

  def __init__(self, driver):
    super(AssessmentTemplates, self).__init__(driver)
    self.extend_list_all_scopes_by_code()


class Issues(InfoWidget):
  """Model for Issue object Info pages and Info panels."""
  _locators = locator.WidgetInfoIssue
  _elements = element.IssueInfoWidget

  def __init__(self, driver):
    super(Issues, self).__init__(driver)
    self.extend_list_all_scopes_by_code()
    self.extend_list_all_scopes_by_cas()
    self.extend_list_all_scopes_by_review_state()


class Regulations(InfoWidget):
  """Model for Assessment object Info pages and Info panels."""
  _locators = locator.WidgetInfoRegulations

  def __init__(self, driver):
    super(Regulations, self).__init__(driver)
    self.extend_list_all_scopes_by_code()
    self.extend_list_all_scopes_by_cas()
    self.extend_list_all_scopes_by_review_state()


class Policies(InfoWidget):
  """Model for Policy object Info pages and Info panels."""
  _locators = locator.WidgetInfoPolicy

  def __init__(self, driver):
    super(Policies, self).__init__(driver)
    self.extend_list_all_scopes_by_code()
    self.extend_list_all_scopes_by_cas()
    self.extend_list_all_scopes_by_review_state()


class Standards(InfoWidget):
  """Model for Standard object Info pages and Info panels."""
  _locators = locator.WidgetInfoStandard

  def __init__(self, driver):
    super(Standards, self).__init__(driver)
    self.extend_list_all_scopes_by_code()
    self.extend_list_all_scopes_by_cas()
    self.extend_list_all_scopes_by_review_state()


class Contracts(InfoWidget):
  """Model for Contract object Info pages and Info panels."""
  _locators = locator.WidgetInfoContract

  def __init__(self, driver):
    super(Contracts, self).__init__(driver)
    self.extend_list_all_scopes_by_code()
    self.extend_list_all_scopes_by_cas()
    self.extend_list_all_scopes_by_review_state()


class Clauses(InfoWidget):
  """Model for Clause object Info pages and Info panels."""
  _locators = locator.WidgetInfoClause

  def __init__(self, driver):
    super(Clauses, self).__init__(driver)
    self.extend_list_all_scopes_by_code()
    self.extend_list_all_scopes_by_cas()
    self.extend_list_all_scopes_by_review_state()


class Sections(InfoWidget):
  """Model for Section object Info pages and Info panels."""
  _locators = locator.WidgetInfoSection

  def __init__(self, driver):
    super(Sections, self).__init__(driver)
    self.extend_list_all_scopes_by_code()
    self.extend_list_all_scopes_by_cas()
    self.extend_list_all_scopes_by_review_state()


class Controls(InfoWidget):
  """Model for Control object Info pages and Info panels."""
  # pylint: disable=too-many-instance-attributes
  _locators = locator.WidgetInfoControl
  _elements = element.ControlInfoWidget
  dropdown_settings_cls = widget_info.Controls

  def __init__(self, driver):
    super(Controls, self).__init__(driver)
    self.extend_list_all_scopes_by_code()
    self.extend_list_all_scopes_by_cas()
    self.extend_list_all_scopes_by_review_state()
    self.admin_text, self.admin_entered_text = (
        self.get_header_and_value_txt_from_custom_scopes(
            self._elements.ADMIN.upper(),
            self._locators.PEOPLE_HEADERS_AND_VALUES))
    self.primary_contact_text, self.primary_contact_entered_text = (
        self.get_header_and_value_txt_from_custom_scopes(
            self._elements.PRIMARY_CONTACTS.upper(),
            self._locators.PEOPLE_HEADERS_AND_VALUES))
    self._extend_list_all_scopes(
        [self.admin_text, self.primary_contact_text],
        [self.admin_entered_text, self.primary_contact_entered_text])


class Objectives(InfoWidget):
  """Model for Objective object Info pages and Info panels."""
  _locators = locator.WidgetInfoObjective

  def __init__(self, driver):
    super(Objectives, self).__init__(driver)
    self.extend_list_all_scopes_by_code()
    self.extend_list_all_scopes_by_cas()
    self.extend_list_all_scopes_by_review_state()


class OrgGroups(InfoWidget):
  """Model for Org Group object Info pages and Info panels."""
  _locators = locator.WidgetInfoOrgGroup
  dropdown_settings_cls = widget_info.OrgGroups

  def __init__(self, driver):
    super(OrgGroups, self).__init__(driver)
    self.extend_list_all_scopes_by_code()
    self.extend_list_all_scopes_by_cas()
    self.extend_list_all_scopes_by_review_state()


class Vendors(InfoWidget):
  """Model for Vendor object Info pages and Info panels."""
  _locators = locator.WidgetInfoVendor

  def __init__(self, driver):
    super(Vendors, self).__init__(driver)
    self.extend_list_all_scopes_by_code()
    self.extend_list_all_scopes_by_cas()
    self.extend_list_all_scopes_by_review_state()


class AccessGroup(InfoWidget):
  """Model for Access Group object Info pages and Info panels."""
  _locators = locator.WidgetInfoAccessGroup

  def __init__(self, driver):
    super(AccessGroup, self).__init__(driver)
    self.extend_list_all_scopes_by_code()
    self.extend_list_all_scopes_by_cas()
    self.extend_list_all_scopes_by_review_state()


class Systems(InfoWidget):
  """Model for System object Info pages and Info panels."""
  _locators = locator.WidgetInfoSystem
  dropdown_settings_cls = widget_info.Systems

  def __init__(self, driver):
    super(Systems, self).__init__(driver)
    self.extend_list_all_scopes_by_code()
    self.extend_list_all_scopes_by_cas()
    self.extend_list_all_scopes_by_review_state()


class Processes(InfoWidget):
  """Model for Process object Info pages and Info panels."""
  _locators = locator.WidgetInfoProcess
  dropdown_settings_cls = widget_info.Processes

  def __init__(self, driver):
    super(Processes, self).__init__(driver)
    self.extend_list_all_scopes_by_code()
    self.extend_list_all_scopes_by_cas()
    self.extend_list_all_scopes_by_review_state()


class DataAssets(InfoWidget):
  """Model for Data Asset object Info pages and Info panels."""
  _locators = locator.WidgetInfoDataAsset
  dropdown_settings_cls = widget_info.DataAssets

  def __init__(self, driver):
    super(DataAssets, self).__init__(driver)
    self.extend_list_all_scopes_by_code()
    self.extend_list_all_scopes_by_cas()
    self.extend_list_all_scopes_by_review_state()


class Products(InfoWidget):
  """Model for Product object Info pages and Info panels."""
  _locators = locator.WidgetInfoProduct
  dropdown_settings_cls = widget_info.Products

  def __init__(self, driver):
    super(Products, self).__init__(driver)
    self.extend_list_all_scopes_by_code()
    self.extend_list_all_scopes_by_cas()
    self.extend_list_all_scopes_by_review_state()


class Projects(InfoWidget):
  """Model for Project object Info pages and Info panels."""
  _locators = locator.WidgetInfoProject
  dropdown_settings_cls = widget_info.Projects

  def __init__(self, driver):
    super(Projects, self).__init__(driver)
    self.extend_list_all_scopes_by_code()
    self.extend_list_all_scopes_by_cas()
    self.extend_list_all_scopes_by_review_state()


class Facilities(InfoWidget):
  """Model for Facility object Info pages and Info panels."""
  _locators = locator.WidgetInfoFacility

  def __init__(self, driver):
    super(Facilities, self).__init__(driver)
    self.extend_list_all_scopes_by_code()
    self.extend_list_all_scopes_by_cas()
    self.extend_list_all_scopes_by_review_state()


class Markets(InfoWidget):
  """Model for Market object Info pages and Info panels."""
  _locators = locator.WidgetInfoMarket

  def __init__(self, driver):
    super(Markets, self).__init__(driver)
    self.extend_list_all_scopes_by_code()
    self.extend_list_all_scopes_by_cas()
    self.extend_list_all_scopes_by_review_state()


class Risks(InfoWidget):
  """Model for Risk object Info pages and Info panels."""
  _locators = locator.WidgetInfoRisk

  def __init__(self, driver):
    super(Risks, self).__init__(driver)
    self.extend_list_all_scopes_by_code()
    self.extend_list_all_scopes_by_cas()
    self.extend_list_all_scopes_by_review_state()


class Threats(InfoWidget):
  """Model for Threat object Info pages and Info panels."""
  _locators = locator.WidgetInfoThreat

  def __init__(self, driver):
    super(Threats, self).__init__(driver)
    self.extend_list_all_scopes_by_code()
    self.extend_list_all_scopes_by_cas()
    self.extend_list_all_scopes_by_review_state()


class People(base.Widget):
  """Model for People object Info pages and Info panels."""
  # pylint: disable=too-few-public-methods
  _locators = locator.WidgetInfoPeople


class Dashboard(base.Widget):
  """Model for Dashboard object Info pages and Info panels."""
  _locators = locator.Dashboard

  def __init__(self, driver):
    super(Dashboard, self).__init__(driver)
    self.start_new_program_btn = base.Button(
        self._driver, self._locators.START_NEW_PROGRAM_BTN_CSS)
    self.start_new_audit_btn = base.Button(
        self._driver, self._locators.START_NEW_AUDIT_BTN_CSS)
    self.start_new_workflow_btn = base.Button(
        self._driver, self._locators.START_NEW_WORKFLOW_BTN_CSS)
    self.create_task_btn = base.Button(
        self._driver, self._locators.CREATE_TASK_BTN_CSS)
    self.create_object_btn = base.Button(
        self._driver, self._locators.CREATE_OBJECT_BTN_CSS)
    self.all_objects_btn = base.Button(
        self._driver, self._locators.ALL_OBJECTS_BTN_CSS)
