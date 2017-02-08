# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Locators for all the elements."""
# pylint: disable=too-few-public-methods
# pylint: disable=too-many-lines

from selenium.webdriver.common.by import By

from lib.constants import objects, url


class Common(object):
  """Common locators."""

  # modal
  MODAL_GENEATE = ".modal-selector"
  MODAL_CREATE = ".modal-wide"
  # attribute names used amongst classes
  BUTTON = "BUTTON_"
  BUTTON_CREATE_NEW = "BUTTON_CREATE_NEW_"
  COUNT = "COUNT_"
  SPINNY = "SPINNY_"
  ACCORDION_MEMBERS = "ACCORDION_MEMBERS_"
  TOGGLE = "TOGGLE_"


class Login(object):
  """All locators for the login page"""

  BUTTON_LOGIN = (By.CSS_SELECTOR, "a.btn.btn-large.btn-info")


class PageHeader(object):
  """All locators for the dashboard header (has the same name as the element"""

  TOGGLE_LHN = (By.CSS_SELECTOR, ".lhn-trigger")
  BUTTON_DASHBOARD = (By.CSS_SELECTOR, '.header-content .to-my-work['
                                       'href="/dashboard"]')
  BUTTON_SEARCH = (By.CSS_SELECTOR, '.header-content ['
                                    'data-toggle="unified-search"]')
  BUTTON_MY_TASKS = (By.CSS_SELECTOR, '.header-content ['
                                      'href="/dashboard#task_widget"]')
  BUTTON_ALL_OBJECTS = (By.CSS_SELECTOR, '.header-content ['
                                         'href="/objectBrowser"]')
  TOGGLE_USER_DROPDOWN = (
      By.CSS_SELECTOR, '.header-content .dropdown-toggle')
  BUTTON_HELP = (By.CSS_SELECTOR, '.header-content [id="#page-help"]')

  GENERIC_SUCCESS_ALERT = (By.CSS_SELECTOR, ".alert-success")

  # dropdown toggle
  BUTTON_ADMIN_DASHBOARD = (
      By.CSS_SELECTOR, '.dropdown-menu [href="/admin#people_list_widget"]')
  BUTTON_MY_WORK = (By.CSS_SELECTOR, '.dropdown-menu [href="/dashboard"]')
  BUTTON_DATA_IMPORT = (By.CSS_SELECTOR, '.dropdown-menu [href="/import"]')
  BUTTON_DATA_EXPORT = (By.CSS_SELECTOR, '.dropdown-menu [href="/export"]')
  BUTTON_LOGOUT = (By.CSS_SELECTOR, '.dropdown-menu [href="/logout"]')
  NOTIFICATIONS = (By.CSS_SELECTOR, '.menu .user-dropdown .notify-wrap')
  CHECKBOX_DAILY_DIGEST = (By.CSS_SELECTOR, '.menu .user-dropdown input')
  CHECKBOX_DISABLED = (By.CSS_SELECTOR, '.menu .user-dropdown input.disabled')


class Dashboard(object):
  """Locators for the dashbord page"""

  BUTTON_START_NEW_PROGRAM = (
      By.CSS_SELECTOR, '.get-started__list [data-object-singular="Program"]')
  BUTTON_START_NEW_AUDIT = (
      By.CSS_SELECTOR, '.get-started__list [data-object-singular="Audit"]')
  BUTTON_START_NEW_WORKFLOW = (
      By.CSS_SELECTOR, '.get-started__list [data-object-singular="Workflow"]')
  BUTTON_CREATE_NEW_OBJECT = (
      By.CSS_SELECTOR, '.get-started__list [href="#"]')
  BUTTON_ALL_OBJECTS = (By.CSS_SELECTOR, '.get-started__list '
                                         '[href="/objectBrowser"]')


class LhnMenu(object):
  """Locators for the menu in header"""
  class _Locator(object):
    """Locators for Lhn Menu"""
    @staticmethod
    def get_accordion_button(label):
      return (By.CSS_SELECTOR, '[data-model-name="{}"]>a'.format(label))

    @staticmethod
    def get_create_new_button(label):
      return (
          By.CSS_SELECTOR,
          '[data-model-name="{}"] [data-test-id="button_lhn_create_new_program'
          '_522c563f"]'.format(label))

    @staticmethod
    def get_accordion_count(label):
      return (By.CSS_SELECTOR, '[data-model-name="{}"] .item-count'.format(
          label))

    @staticmethod
    def get_accordion_members(object_name):
      return (
          By.CSS_SELECTOR,
          '[data-model-name="{}"]>.content>.sub-level>li'.format(object_name))

    @staticmethod
    def get_spinny(object_name):
      return (By.CSS_SELECTOR, '[data-model-name="{}"] .spinny'.format(
          object_name))

  class __metaclass__(type):
    def __init__(cls, *args):
      for object_singular, object_plural in zip(objects.ALL_SINGULAR,
                                                objects.ALL_PLURAL):
        capitalized_name = object_singular.title()

        # handle underscore in object names
        if "_" in capitalized_name:
          capitalized_name = capitalized_name.title().replace("_", "")

        # set lhn items
        setattr(cls, Common.TOGGLE + object_plural,
                cls._Locator.get_accordion_button(capitalized_name))
        setattr(cls, Common.BUTTON_CREATE_NEW + object_plural,
                cls._Locator.get_create_new_button(capitalized_name))
        setattr(cls, Common.COUNT + object_plural,
                cls._Locator.get_accordion_count(capitalized_name))
        setattr(cls, Common.SPINNY + object_plural,
                cls._Locator.get_spinny(capitalized_name))
        setattr(cls, Common.ACCORDION_MEMBERS + object_plural,
                cls._Locator.get_accordion_members(capitalized_name))

  LHN_MENU = (By.ID, "lhn")
  MODAL = (By.CSS_SELECTOR, '[id="ajax-lhn_modal-javascript:--"]')
  EXTENDED_INFO = (By.CSS_SELECTOR, '.extended-info.in .info .fa')

  FILTER = (By.CSS_SELECTOR, '.lhs-search')
  FILTER_TEXT_BOX = (By.CSS_SELECTOR, '.lhs-search>.widgetsearch')
  FILTER_SUBMIT_BUTTON = (
      By.CSS_SELECTOR, '.lhs-search>.widgetsearch-submit')
  FILTER_CLEAR_BUTTON = (
      By.CSS_SELECTOR, '.lhs-search [data-title="Clear filters"]')

  LHS_ITEM = (By.CSS_SELECTOR, '[test-data-id="lhs-item_3ad27b8b"]')
  ALL_OBJECTS = (By.CSS_SELECTOR, '[data-test-id="all_objects_e0345ec4"]')
  MY_OBJECTS = (By.CSS_SELECTOR, '[data-test-id="my_objects_6fa95ae1"]')
  PIN = (By.CSS_SELECTOR, '.lhn-pin')

  # lhn items
  DIRECTIVES = (By.CSS_SELECTOR, '[data-test-id="directives_66116337"]')
  TOGGLE_CONTROLS_OR_OBJECTIVES = (
      By.CSS_SELECTOR, '[data-test-id="controls/objectives_66116337"]')
  TOGGLE_PEOPLE_OR_GROUPS = (
      By.CSS_SELECTOR, '[data-test-id="people/groups_66116337"]')
  TOGGLE_ASSETS_OR_BUSINESS = (
      By.CSS_SELECTOR, '[data-test-id="assets/business_66116337"]')
  TOGGLE_RISK_OR_THREATS = (
      By.CSS_SELECTOR, '[data-test-id="risk/threats_66116337"]')

  # workflows labels
  BUTTON_WORKFLOWS_ACTIVE = (
      By.CSS_SELECTOR, '[data-for="Workflow"]>[data-value="Active"]')
  BUTTON_WORKFLOWS_DRAFT = (
      By.CSS_SELECTOR, '[data-for="Workflow"]>[data-value="Draft"]')
  BUTTON_WORKFLOWS_INACTIVE = (
      By.CSS_SELECTOR, '[data-for="Workflow"]>[data-value="Inactive"]')


class ExtendedInfo(object):
  """Locators for the extended info tooltip in LHN after hovering over a
  member object"""

  BUTTON_MAP_TO = (
      By.CSS_SELECTOR, '[data-test-id="extended_info_button_map"]')
  ALREADY_MAPPED = (
      By.CSS_SELECTOR, '[data-test-id="extended_info_object_already_mapped"]')
  TITLE = (By.CSS_SELECTOR, '#extended-info .main-title')


class BaseModalCreateNew(object):
  """Locators shared with create new object modals."""
  MODAL = Common.MODAL_CREATE
  # labels
  MODAL_TITLE = (By.CSS_SELECTOR, "{} .ui-draggable-handle>h2".format(MODAL))
  TITLE = (By.CSS_SELECTOR,
           "{} .modal-body form>div:nth-child(2) .span6>label".format(MODAL))
  # user input elements
  UI_TITLE = (By.CSS_SELECTOR,
              "{} .modal-body form>div:nth-child(2) .span6>input".
              format(MODAL))


class BaseModalGenerateNew(object):
  """Locators shared with generate new object modals."""
  MODAL = Common.MODAL_GENEATE
  # labels
  MODAL_TITLE = (By.CSS_SELECTOR, "{} .modal-header>h2".format(MODAL))


class ModalSetVisibleFields(object):
  """Locators for a generic edit object modal."""
  FIELDS_MODAL = "{} .open .dropdown-menu-form"
  FIELDS_TITLES = "{} .tree-header .checkbox-inline"
  FIELDS_CHECKBOXES = "{} .tree-header .attr-checkbox"
  BUTTON_SAVE_SET_FIELDS = "{} .tree-action-list .set-tree-attrs"


class ModalCreateNewObject(BaseModalCreateNew):
  """Locators for a generic new object modal."""
  UI_TITLE = (By.CSS_SELECTOR,
              '{} [data-id="title_txtbx"]'.format(BaseModalCreateNew.MODAL))
  BUTTON_SAVE_AND_CLOSE = (By.CSS_SELECTOR,
                           '{} [data-toggle="modal-submit"]'.
                           format(BaseModalCreateNew.MODAL))
  BUTTON_SAVE_AND_ADD_ANOTHER = (By.CSS_SELECTOR,
                                 '{} [data-toggle="modal-submit-addmore"]'.
                                 format(BaseModalCreateNew.MODAL))


class ModalCreateNewProgram(BaseModalCreateNew):
  """Locators for the program modal visible when creating a new modal from
  LHN"""
  UI_TITLE = (By.CSS_SELECTOR,
              '[data-test-id="new_program_field_title_a63ed79d"]')
  UI_DESCRIPTION = (By.CSS_SELECTOR,
                    '[data-test-id="new_program_field_description_1fb8bc06"]'
                    '>iframe.wysihtml5-sandbox')
  UI_NOTES = (By.CSS_SELECTOR,
              '[data-test-id="new_program_field_notes_75b8bc05"]'
              '>iframe.wysihtml5-sandbox')
  UI_CODE = (By.CSS_SELECTOR,
             '[data-test-id="new_program_field_code_334276e2"]')
  UI_STATE = (By.CSS_SELECTOR,
              '[data-test-id="new_program_dropdown_state_036a1fa6"]')
  BUTTON_HIDE_OPTIONAL_FIELDS = (By.ID, "formHide")
  BUTTON_SHOW_ALL_OPTIONAL_FIELDS = (By.ID, "formHide")
  UI_PRIMARY_CONTACT = (By.CSS_SELECTOR, '[data-test-id='
                                         '"new_program_field_primary_contact_'
                                         '86160053"]')
  DROPDOWN_CONTACT = (By.CSS_SELECTOR, '.ui-menu-item')
  UI_SECONDARY_CONTACT = (By.CSS_SELECTOR, '[data-test-id='
                                           '"new_program_field_secondary_'
                                           'contact_'
                                           '86160053"]')

  UI_PROGRAM_URL = (By.CSS_SELECTOR, '[data-test-id='
                                     '"new_program_field_program_url_'
                                     '86160053"]')
  UI_REFERENCE_URL = (By.CSS_SELECTOR, '[data-test-id='
                                       '"new_program_field_reference_url_'
                                       '86160053"]')

  UI_EFFECTIVE_DATE = (
      By.CSS_SELECTOR,
      '[test-id="new_program_field_effective_date_f2783a28"] '
      '[data-id="effective_date_hidden"] '
      '.datepicker__input')
  EFFECTIVE_DATE_DATEPICKER = (
      By.CSS_SELECTOR,
      '[test-id="new_program_field_effective_date_f2783a28"] '
      '[data-id="effective_date_hidden"] '
      '[data-handler="selectDay"]')

  UI_STOP_DATE = (
      By.CSS_SELECTOR,
      '[test-id="new_program_field_effective_date_f2783a28"] '
      '[data-id="stop_date_hidden"] '
      '.datepicker__input')
  STOP_DATE_DATEPICKER = (
      By.CSS_SELECTOR,
      '[test-id="new_program_field_effective_date_f2783a28"] '
      '[data-id="stop_date_hidden"] '
      '[data-handler="selectDay"]')

  TITLE = (By.CSS_SELECTOR, '[data-test-id="label_title_2c925d94"]')
  DESCRIPTION = (By.CSS_SELECTOR,
                 '[data-test-id="label_description_2c925d94"]')

  PRIVACY = (By.CSS_SELECTOR, '[data-test-id="label_privacy_2c925d94"]')
  PROGRAM_URL = (By.CSS_SELECTOR,
                 '[data-test-id="label_program_url_2c925d94"]')


class ModalCreateNewOrgGroup(BaseModalCreateNew):
  """Locators for the control modal visible when creating a new modal from
  LHN"""


class ModalCreateNewRisk(BaseModalCreateNew):
  """Locators for the control modal visible when creating a new modal from
  LHN"""
  UI_DESCRIPTION = (
      By.CSS_SELECTOR, '.modal-body form>div:nth-child(3) iframe')


class ModalCreateNewDataAsset(BaseModalCreateNew):
  """Locators for the control modal visible when creating a new modal from
  LHN"""


class ModalCreateNewProcess(BaseModalCreateNew):
  """Locators for the control modal visible when creating a new modal from
  LHN"""


class ModalCreateNewProject(BaseModalCreateNew):
  """Locators for the control modal visible when creating a new modal from
  LHN"""


class ModalCreateNewSystem(BaseModalCreateNew):
  """Locators for the control modal visible when creating a new modal from
  LHN"""


class ModalCreateNewProduct(BaseModalCreateNew):
  """Locators for the control modal visible when creating a new modal from
  LHN"""


class ModalCreateNewControl(BaseModalCreateNew):
  """Locators for the control modal visible when creating a new modal from
  LHN"""
  class _Locator(object):
    """Locators for the control modal visible when creating a modal from LHN"""
    @staticmethod
    def get_assessor_row(first_id, second_id):
      return (
          By.CSS_SELECTOR,
          '.modal-body div>form>div>div:nth-child({})>div:nth-child({}) '
          'label'.format(first_id, second_id))

    @staticmethod
    def get_dropdown_item(first_id, second_id):
      return (
          By.CSS_SELECTOR,
          '.modal-body div>form>div>div:nth-child({})>div:nth-child({}) '
          'select'.format(first_id, second_id))

  DESCRIPTION = (
      By.CSS_SELECTOR,
      '[data-test-id="control_description-label_9cc51ca3"]')
  UI_DESCRIPTION = (
      By.CSS_SELECTOR,
      '[data-test-id="control_description-text_9cc51ca3"] iframe')

  TEST_PLAN = (
      By.CSS_SELECTOR,
      '[data-test-id="control_test_plan_d8b5a2f4"] label')
  UI_TEST_PLAN = (
      By.CSS_SELECTOR,
      '[data-test-id="control_test_plan_d8b5a2f4"] iframe')

  NOTES = (By.CSS_SELECTOR, '[data-id="note_hidden"] label')

  CODE = (
      By.CSS_SELECTOR,
      '[data-test-id="control_code_f8abbcc9"] label')
  UI_CODE = (
      By.CSS_SELECTOR,
      '[data-test-id="control_code_f8abbcc9"] input')

  KIND_OR_NATURE = (
      By.CSS_SELECTOR,
      '[data-test-id="control_kind_nature_dadc232f"] label')
  DROPDOWN_KIND_OR_NATURE = (
      By.CSS_SELECTOR,
      '[data-test-id="control_kind_nature_dadc232f"] select')

  FRAUD_RELATED = (
      By.CSS_SELECTOR,
      '[data-test-id="control_fraud_9cc51ca3"] label')
  DROPDOWN_FRAUD_RELATED = (
      By.CSS_SELECTOR,
      '[data-test-id="control_fraud_9cc51ca3"] select')

  FREQUENCY = (
      By.CSS_SELECTOR,
      '[data-test-id="control_frequency_fb20318a"] label')
  DROPDOWN_FREQUENCY = (
      By.CSS_SELECTOR,
      '[data-test-id="control_frequency_fb20318a"] select')

  ASSERTIONS = (
      By.CSS_SELECTOR,
      '[data-test-id="control_assertions_5d8b7f7a"] label')
  SELECTABLE_ASSERTIONS = (
      By.CSS_SELECTOR,
      '[data-test-id="control_assertions_5d8b7f7a"] select')

  PRINCIPAL_ASSESSOR = (
      By.CSS_SELECTOR,
      '[data-test-id="control_primary_assessor_f7379330"] label')
  SECONDARY_ASSESSOR = (
      By.CSS_SELECTOR,
      '[data-test-id="control_secondary_assessor_b9439af6"] label')

  OWNER = (
      By.CSS_SELECTOR,
      '[data-test-id="control_owner_587d12d6"] label')
  BUTTON_ADD_OWNER = (By.CSS_SELECTOR, 'isolate-form .btn')

  PRIMARY_CONTACT = (
      By.CSS_SELECTOR,
      '[data-test-id="control_contacts_8bd3d8c7"] '
      '.row-fluid:nth-child(1) label')
  UI_PRIMARY_CONTACT = (
      By.CSS_SELECTOR,
      '[data-test-id="new_program_field_primary_contact_86160053"]')

  SECONDARY_CONTACT = (
      By.CSS_SELECTOR,
      '[data-test-id="control_contacts_8bd3d8c7"] '
      '.row-fluid:nth-child(2) label')
  UI_SECONDARY_CONTACT = (
      By.CSS_SELECTOR,
      '[data-test-id="new_program_field_secondary_contact_86160053"]')

  CONTROL_URL = (
      By.CSS_SELECTOR,
      '[data-test-id="control_control_url-label_c4038873"]')
  UI_CONTROL_URL = (
      By.CSS_SELECTOR,
      '[data-test-id="control_control_url-input_c4038873"]')

  REFERENCE_URL = (
      By.CSS_SELECTOR,
      '[data-test-id="control_reference_url-label_8931063d"]')
  UI_REFERENCE_URL = (
      By.CSS_SELECTOR,
      '[data-test-id="control_reference_url-input_8931063d"]')

  SIGNIFICANCE = (
      By.CSS_SELECTOR,
      '[data-test-id="control_significance_18f15545"] label')
  DROPDOWN_SIGNIFICANCE = (
      By.CSS_SELECTOR,
      '[data-test-id="control_significance_18f15545"] select')

  TYPE_OR_MEANS = (
      By.CSS_SELECTOR,
      '[data-test-id="control_type_means_2ffa1b64"] label')
  DROPDOWN_TYPE_OR_MEANS = (
      By.CSS_SELECTOR,
      '[data-test-id="control_type_means_2ffa1b64"] select')

  CATEGORIES = (
      By.CSS_SELECTOR,
      '[data-test-id="control_categories_1eb33246"] label')
  SELECTABLE_CATEGORIES = (
      By.CSS_SELECTOR,
      '[data-test-id="control_categories_1eb33246"] select')

  STATE = (
      By.CSS_SELECTOR,
      '[data-test-id="control_state_5d184456"] label')
  DROPDOWN_STATE = (
      By.CSS_SELECTOR,
      '[data-test-id="control_state_5d184456"] select')

  UI_NOTES = (By.CSS_SELECTOR, '[data-id="note_hidden"] iframe')

  EFFECTIVE_DATE = (
      By.CSS_SELECTOR,
      '[test-id="control_effective_dates_0376cf90"] '
      '[data-id="effective_date_hidden"] '
      '.datepicker__input')
  DATEPICKER_EFFECTIVE_DATE = (
      By.CSS_SELECTOR,
      '[test-id="control_effective_dates_0376cf90"] '
      '[data-id="effective_date_hidden"] '
      '[data-handler="selectDay"]')

  STOP_DATE = (
      By.CSS_SELECTOR,
      '[test-id="control_effective_dates_0376cf90"] '
      '[data-id="stop_date_hidden"] '
      '.datepicker__input')
  DATEPICKER_STOP_DATE = (
      By.CSS_SELECTOR,
      '[test-id="control_effective_dates_0376cf90"] '
      '[data-id="stop_date_hidden"] '
      '[data-handler="selectDay"]')

  # buttons
  BUTTON_HIDE_ALL_OPTIONAL_FIELDS = (By.CSS_SELECTOR, '#formHide')


class ModalCreateNewIssue(BaseModalCreateNew):
  """Locators for the issue modal visible when creating a new modal from
  LHN"""


class ModalCreateNewAsmt(BaseModalCreateNew):
  """Locators for a assessments creation modal."""


class ModalCreateNewAsmtTmpl(BaseModalCreateNew):
  """Locators for a assessment templates creation modal."""


class ModalGenerateNewObject(BaseModalGenerateNew):
  """Locators for a generate new object modal."""
  BUTTON_GENERATE = (By.CSS_SELECTOR,
                     "{} .btn-map".format(BaseModalGenerateNew.MODAL))


class ModalGenerateNewAsmt(ModalGenerateNewObject):
  """Locators for a assessments generation modal."""
  MODAL = ModalGenerateNewObject.MODAL
  SELECT_ASMT_TMPL_DROPDOWN = (By.CSS_SELECTOR,
                               '{} dropdown[name="assessmentTemplate"] '
                               '.input-block-level'.format(MODAL))
  SELECT_ASMT_TMPL_OPTIONS = (By.CSS_SELECTOR,
                              '{} dropdown[name="assessmentTemplate"] '
                              '.input-block-level option'.format(MODAL))
  BUTTON_SEARCH = (By.CSS_SELECTOR, "{} .btn-info".format(MODAL))
  FOUNDED_OBJECTS_TITLES = (By.CSS_SELECTOR,
                            "{} .snapshot-list .title".
                            format(MODAL))
  FOUNDED_OBJECTS_CHECKBOXES = (By.CSS_SELECTOR,
                                '{} .snapshot-list [type="checkbox"]'.
                                format(MODAL))


class ModalEditObject(BaseModalCreateNew):
  """Locators for a generic edit object modal"""
  BUTTON_DELETE = (
      By.CSS_SELECTOR, '.deny-buttons [data-toggle="modal-ajax-deleteform"]')


class ModalCustomAttribute(object):
  """Locators for a generic custom attributes modal in admin dashboard"""

  MODAL_TITLE = (By.CSS_SELECTOR, '.modal-header h2')
  ATTRIBUTE_TITLE = (By.CSS_SELECTOR, '.modal-body div:nth-child(1)>label')
  INLINE_HELP = (By.CSS_SELECTOR, '.modal-body div:nth-child(2)>label')
  ATTRIBUTE_TYPE = (By.CSS_SELECTOR, '.modal-header h2')
  PLACEHOLDER = (By.CSS_SELECTOR, '.modal-header h2')
  MANDATORY = (By.CSS_SELECTOR, '.modal-header h2')
  UI_ATTRIBUTE_TITLE = (By.CSS_SELECTOR, '.modal-body [name="title"]')
  UI_INLINE_HELP = (By.CSS_SELECTOR, '.modal-body [name="helptext"]')
  UI_PLACEHOLDER = (By.CSS_SELECTOR, '.modal-body [name="placeholder"]')
  UI_POSSIBLE_VALUES = (By.CSS_SELECTOR, '.modal-body '
                                         '[name="multi_choice_options"]')
  CHECKBOX_MANDATORY = (By.CSS_SELECTOR, '.modal-body [type="checkbox"]')
  BUTTON_ADD_ANOTHER = (
      By.CSS_SELECTOR,
      '.confirm-buttons [data-toggle="modal-submit-addmore"]')
  BUTTON_SAVE_AND_CLOSE = (
      By.CSS_SELECTOR,
      '.modal-footer .confirm-buttons [data-toggle="modal-submit"]')
  ATTRIBUTE_TYPE_SELECTOR = (By.CSS_SELECTOR, "dropdown select")
  ATTRIBUTE_TYPE_OPTIONS = (By.CSS_SELECTOR, "dropdown select option")


class WidgetBar(object):
  """Locators for the bar containing the widgets/tabs"""

  class _Locator(object):
    """Locators for the menu in header."""
    @staticmethod
    def get_widget(object_name):
      return (
          By.CSS_SELECTOR,
          '.object-nav [href$="#{}_widget"]'.format(object_name)
      )

  class __metaclass__(type):
    def __init__(cls, *args):
      for object_singular, object_plural in zip(objects.ALL_SINGULAR,
                                                objects.ALL_PLURAL):
        name = object_singular.lower()
        setattr(cls, object_plural, cls._Locator.get_widget(name))

  BUTTON_ADD = (By.CSS_SELECTOR,
                '[data-test-id="button_widget_add_2c925d94"]')
  TAB_WIDGET = (By.CSS_SELECTOR, ".object-nav .active")
  ADMIN_PEOPLE = _Locator.get_widget("people_list")
  ADMIN_ROLES = _Locator.get_widget("roles_list")
  ADMIN_EVENTS = _Locator.get_widget("events_list")
  ADMIN_CUSTOM_ATTRIBUTE = _Locator.get_widget("custom_attribute")

  INFO = _Locator.get_widget("info")
  CUSTOM_ATTRIBUTES = _Locator.get_widget("custom_attribute")
  EVENTS = _Locator.get_widget("events_list")
  ROLES = _Locator.get_widget("roles_list")
  RISK_ASSESSMENTS = _Locator.get_widget("risk_assessment")
  TASKS = _Locator.get_widget("task")


class WidgetBarButtonAddDropdown(object):
  """Locators for the button/dropdown "add widget" in widget bar"""
  class _Locator(object):
    """Toggle locators for the widget custom attributes in admin dashboard."""
    @staticmethod
    def get_dropdown_item(object_name):
      return (
          By.CSS_SELECTOR,
          '[data-test-id="button_widget_add_2c925d94"] '
          '.object-nav [href$="#{}_widget"]'.format(object_name)
      )

  class __metaclass__(type):
    def __init__(cls, *args):
      for object_ in objects.ALL_PLURAL:
        name = object_.lower()
        setattr(cls, object_, cls._Locator.get_dropdown_item(name))

  THREAD_ACTORS = _Locator.get_dropdown_item("threat_actor")
  WORKFLOW_TASKS = _Locator.get_dropdown_item("workflow_task")


class ObjectWidget(object):
  """Locators for a generic widget"""

  CONTROL_COLUMN_TITLE = (
      By.CSS_SELECTOR, '.header .span4 .title-heading .widget-col-title')
  CONTROL_OWNER = (
      By.CSS_SELECTOR, '.header .span4 [data-field="contact.name|email"]')
  COTNROL_STATE = (
      By.CSS_SELECTOR, '.header .span4 [data-field="status"]')
  MEMBERS_TITLE_LIST = (
      By.CSS_SELECTOR,
      '.object-area .tree-structure .select .span4:nth-child(1) .title')
  INFO_PANE = (By.CSS_SELECTOR, '.sticky-info-panel')
  LOADING = (By.CSS_SELECTOR, '.new-tree_loading')


class ModalDeleteObject(object):
  MODAL_TITLE = (By.CSS_SELECTOR, '.modal-header>h2')
  CONFIRMATION_TEXT = (By.CSS_SELECTOR, '.modal-body>div>p')
  OBJECT_TITLE = (By.CSS_SELECTOR, '.modal-body>div>p>span')
  BUTTON_DELETE = (
      By.CSS_SELECTOR, '.modal-footer .confirm-buttons>[data-toggle="delete"]')


class BaseInfoWidget(object):
  """Locators that are common to all info widgets"""
  BUTTON_SETTINGS = (By.CSS_SELECTOR, '.info-pane-utility')
  TITLE = (By.CSS_SELECTOR, '[data-test-id="title_0ad9fbaf"] h6')
  TITLE_ENTERED = (By.CSS_SELECTOR, '[data-test-id="title_0ad9fbaf"] h3')


class WidgetInfoProgram(BaseInfoWidget):
  """Locators for the info program widget"""

  PERMALINK_ALERT = (By.CSS_SELECTOR, '.content>.flash>.alert-success')

  ALERT_LINK_COPIED = (By.CSS_SELECTOR, '.alert.alert-success')
  MODAL_DELETE = (By.ID, '[id="ajax-lhn_modal-javascript:--"]')
  MODAL_DELETE_CLOSE = (By.CSS_SELECTOR, '.lhn_modal .grcicon-x-grey')

  OBJECT_REVIEW = (By.CSS_SELECTOR,
                   '[data-test-id="title_review_0ad9fbaf"] h6')
  SUBMIT_FOR_REVIEW = (By.CSS_SELECTOR,
                       '[data-test-id="title_review_0ad9fbaf"] '
                       '[href="javascript://"]')
  DESCRIPTION = (By.CSS_SELECTOR,
                 '[data-test-id="title_description_7a906d2e"] h6')
  DESCRIPTION_ENTERED = (By.CSS_SELECTOR,
                         '[data-test-id="title_description_'
                         'content_7a906d2e"]')
  NOTES = (By.CSS_SELECTOR, '[data-test-id="title_notes_ef5bc3a71e88"] '
                            'h6')
  NOTES_ENTERED = (By.CSS_SELECTOR,
                   '[data-test-id="title_notes_ef5bc3a71e88"]>div')
  MANAGER = (By.CSS_SELECTOR, '[data-test-id="title_manager_7a906d2e"] '
                              'h6')
  MANAGER_ENTERED = (By.CSS_SELECTOR,
                     '[data-test-id="title_manager_7a906d2e"] '
                     '[data-test-id="text_manager_7a906d2e"]')
  PROGRAM_URL = (By.CSS_SELECTOR,
                 '[data-test-id="title_program_url_aa7d1a65"] h6')
  PROGRAM_URL_ENTERED = (By.CSS_SELECTOR,
                         '[data-test-id="text_program_url_aa7d1a65"]')
  REFERENCE_URL = (By.CSS_SELECTOR,
                   '[data-test-id="title_reference_url_aa7d1a65"]')
  REFERENCE_URL_ENTERED = (By.CSS_SELECTOR,
                           '[data-test-id="text_reference_url_aa7d1a65"]')
  TOGGLE_SHOW_ADVANCED = (By.CSS_SELECTOR,
                          '[data-test-id="button_advanced_cf47bc01"]')
  TOGGLE_SHOW_ADVANCED_ACTIVATED = (
      By.CSS_SELECTOR, '[data-test-id="button_advanced_cf47bc01"].active')
  CODE = (By.CSS_SELECTOR, '[data-test-id="title_code_cf47bc01"] h6')
  CODE_ENTERED = (By.CSS_SELECTOR,
                  '[data-test-id="title_code_cf47bc01"] p')
  EFFECTIVE_DATE = (By.CSS_SELECTOR,
                    '[data-test-id="title_effective_date_cf47bc01"] h6')
  EFFECTIVE_DATE_ENTERED = (By.CSS_SELECTOR,
                            '[data-test-id="title_effective_date_'
                            'cf47bc01"] p')
  STOP_DATE = (By.CSS_SELECTOR,
               '[data-test-id="title_stop_date_cf47bc01"] h6')
  STOP_DATE_ENTERED = (By.CSS_SELECTOR,
                       '[data-test-id="title_stop_date_cf47bc01"] p')
  STATE = (By.CSS_SELECTOR,
           '[dadata-test-id="new_program_button_save_and_new_86160053"'
           ' ta-test-id="title_state_0ad9fbaf"] h6')
  STATE_ENTERED = (By.CSS_SELECTOR,
                   '[data-test-id="title_state_value_0ad9fbaf"]')
  PRIMARY_CONTACT = (By.CSS_SELECTOR, '[data-test-id="title_primary_'
                                      'contact_696de7244b84"] h6')
  PRIMARY_CONTACT_ENTERED = (
      By.CSS_SELECTOR, '[data-test-id="text_primary_contact_'
                       '696de7244b84"] [data-test-id="text_'
                       'manager_7a906d2e"]')
  SECONDARY_CONTACT = (
      By.CSS_SELECTOR, '[data-test-id="title_contacts_696de7244b84"] '
                       'h6:nth-child(2)')
  SECONDARY_CONTACT_ENTERED = (
      By.CSS_SELECTOR, '[data-test-id="text_secondary_contact_'
                       '696de7244b84"] [data-test-id="text_manager_'
                       '7a906d2e"]')
  PRIVATE_PROGRAM = (By.CSS_SELECTOR,
                     '[data-test-id="title_private_ec758af9"] h6')
  ICON_LOCK = (By.CSS_SELECTOR, '[data-test-id="icon_private_ec758af9"]')


class WidgetInfoRisk(BaseInfoWidget):
  """Locators for the risk info widget"""


class WidgetInfoOrgGroup(BaseInfoWidget):
  """Locators for the org group info widget"""


class WidgetInfoIssue(BaseInfoWidget):
  """Locators for the org group info widget"""


class WidgetInfoRegulations(BaseInfoWidget):
  """Locators for the regulation info widget"""


class WidgetInfoWorkflow(BaseInfoWidget):
  """Locators for the workflow info widget"""


class WidgetInfoAudit(BaseInfoWidget):
  """Locators for the audit info widget"""


class WidgetInfoAssessment(BaseInfoWidget):
  """Locators for the assessment info widget"""


class WidgetInfoAssessmentTemplate(BaseInfoWidget):
  """Locators for the assessment template info widget."""


class WidgetInfoPolicy(BaseInfoWidget):
  """Locators for the regulation info widget"""


class WidgetInfoStandard(BaseInfoWidget):
  """Locators for the standard info widget"""


class WidgetInfoContract(BaseInfoWidget):
  """Locators for the contract info widget"""


class WidgetInfoClause(BaseInfoWidget):
  """Locators for the clause info widget"""


class WidgetInfoSection(BaseInfoWidget):
  """Locators for the section info widget"""


class WidgetInfoControl(BaseInfoWidget):
  """Locators for the control info widget"""


class WidgetInfoObjective(BaseInfoWidget):
  """Locators for the objective info widget"""


class WidgetInfoPeople(BaseInfoWidget):
  """Locators for the people info widget"""


class WidgetInfoVendor(BaseInfoWidget):
  """Locators for the vendor info widget"""


class WidgetInfoAccessGroup(BaseInfoWidget):
  """Locators for the access group info widget"""


class WidgetInfoSystem(BaseInfoWidget):
  """Locators for the system info widget"""


class WidgetInfoProcess(BaseInfoWidget):
  """Locators for the process info widget"""


class WidgetInfoProduct(BaseInfoWidget):
  """Locators for the product info widget"""


class WidgetInfoFacility(BaseInfoWidget):
  """Locators for the facility info widget"""


class WidgetInfoProject(BaseInfoWidget):
  """Locators for the project info widget"""


class WidgetInfoMarket(BaseInfoWidget):
  """Locators for the market info widget"""


class WidgetInfoDataAsset(BaseInfoWidget):
  """Locators for the data asset info widget"""


class WidgetInfoThreat(BaseInfoWidget):
  """Locators for the data asset info widget"""


class WidgetAdminRoles(object):
  """Locators for the roles widget on the admin dashboard."""
  widget_name = url.Widget.ROLES


class WidgetAdminEvents(object):
  """Locators for event widget at admin dashboard"""
  _BASE_CSS_SELECTOR = 'section#events_list_widget:not([class~="hidden"])'
  _TREE_ITEMS_SELECTOR = ".tree-item[data-model]"

  TREE_VIEW_ITEMS = (By.CSS_SELECTOR,
                     "{0} {1}".
                     format(_BASE_CSS_SELECTOR, _TREE_ITEMS_SELECTOR))
  TREE_VIEW_HEADER = (By.CSS_SELECTOR,
                      "{} header".format(_BASE_CSS_SELECTOR))
  FIRST_TREE_VIEW_ITEM = (By.CSS_SELECTOR,
                          "{0} {1}:first-child".
                          format(_BASE_CSS_SELECTOR, _TREE_ITEMS_SELECTOR))


class WidgetInfoSettingsButton(object):
  """Locators for the control info widget"""
  TITLE_ENTERED = (By.CSS_SELECTOR, '[data-test-id="title_0ad9fbaf"]>h3')

  DROPDOWN_SETTINGS_EDIT = (
      By.CSS_SELECTOR,
      '[data-test-id="dropdown_settings_edit_f4b27aec"]')
  DROPDOWN_SETTINGS_PERMALINK = (
      By.CSS_SELECTOR,
      '[data-test-id="dropdown_settings_get_permalink_75e3bf91"]')
  DROPDOWN_SETTINGS_DELETE = (
      By.CSS_SELECTOR, '[data-test-id="dropdown_settings_delete_6a62eaaf"]')


class BaseWidgetGeneric(object):
  """Locators shared amongst non info&admin widgets"""
  _object_name = None

  class __metaclass__(type):
    """For sharing parametrized class attributes we simply define how a
    class should look like. Note that the same functionality can be
    implemented using properties though with more code."""
    def __init__(cls, *args):
      cls.TEXTFIELD_TO_FILTER = (
          By.CSS_SELECTOR,
          '#{}_widget .sticky-filter .tree-filter__expression-holder'
            .format(cls._object_name))
      cls.BUTTON_FILTER = (
          By.CSS_SELECTOR,
          '#{}_widget .sticky-filter .tree-filter__button [type="submit"]'
            .format(cls._object_name))
      cls.BUTTON_RESET = (
          By.CSS_SELECTOR,
          '#{}_widget .sticky-filter .tree-filter__button [type="reset"]'
            .format(cls._object_name))
      cls.BUTTON_HELP = (
          By.CSS_SELECTOR,
          '#{}_widget .sticky-filter .tree-filter__button  #page-help'
            .format(cls._object_name))
      cls.ACTIVE_CHECKBOX = (
          By.CSS_SELECTOR,
          '#{}_widget .sticky-filter .tree-filter__status-wrap '
          '[name="active"]'.format(cls._object_name))
      cls.DRAFT_CHECKBOX = (
          By.CSS_SELECTOR,
          '#{}_widget .sticky-filter .tree-filter__status-wrap '
          '[name="draft"]'.format(cls._object_name))
      cls.CHECKBOX_DEPRECATED = (
          By.CSS_SELECTOR,
          '#{}_widget .sticky-filter .tree-filter__status-wrap '
          '[name="deprecated"]'.format(cls._object_name))

  FILTER_PANE_COUNTER = (
      By.CSS_SELECTOR, ".tree-pagination__count "
                       ".tree-view-pagination__count__title")


class WidgetAssessments(BaseWidgetGeneric):
  """Locators for assessment widget"""
  _object_name = objects.get_singular(objects.ASSESSMENTS)
  widget_name = url.Widget.ASSESSMENTS


class WidgetControls(BaseWidgetGeneric):
  """Locators for control widget"""
  _object_name = "control"


class WidgetProducts(BaseWidgetGeneric):
  """Locators for product widget"""
  _object_name = "product"


class WidgetProjects(BaseWidgetGeneric):
  """Locators for project widget"""
  _object_name = "project"


class WidgetSystems(BaseWidgetGeneric):
  """Locators for system widget"""
  _object_name = "system"


class WidgetDataAssets(BaseWidgetGeneric):
  """Locators for system widget"""
  _object_name = "data_asset"


class WidgetProcesses(BaseWidgetGeneric):
  """Locators for system widget"""
  _object_name = "process"


class WidgetIssues(BaseWidgetGeneric):
  """Locators for system widget"""
  _object_name = "issue"


class WidgetAssessmentTemplates(BaseWidgetGeneric):
  """Locators for assessment widget."""
  _object_name = objects.get_singular(objects.ASSESSMENT_TEMPLATES)
  widget_name = url.Widget.ASSESSMENT_TEMPLATES


class TreeView(object):
  """Locators for tree-view components."""
  # common
  ITEMS = "{} li.tree-item .item-main"
  HEADER = "{} .tree-header"
  ITEM_LOADING = (By.CSS_SELECTOR, " .tree-item-placeholder")
  ITEM_EXPAND_BUTTON = " .openclose"
  SPINNER = (By.CSS_SELECTOR, " .tree-spinner")
  # tree view tool bar of widgets
  _TREE = " .tree-action-list"
  BUTTON_3BBS = "{}" + _TREE + " .btn-draft"
  BUTTON_CREATE = "{}" + _TREE + " .create-button"
  BUTTON_GENERATE = "{}" + _TREE + " .tree-action-list-items .fa-magic"
  BUTTON_SET_FIELDS = "{}" + _TREE + " .tree-action-list-items .fa-cog"


class AdminCustomAttributes(object):
  """Locators for the widget custom attributes in admin dashboard."""
  widget_name = url.Widget.CUSTOM_ATTRIBUTES

  class _Locator(object):
    """Locators for the widget custom attributes in admin dashboard."""
    @staticmethod
    def get_toggle(child_id):
      return (By.CSS_SELECTOR, '#custom_attribute_widget li:nth-child({}) '
              '.openclose'.format(child_id))

    @staticmethod
    def get_programs_label(child_id):
      return (
          By.CSS_SELECTOR,
          '.tree-structure li:nth-child(5) div thead>tr>th:nth-child({})'
            .format(child_id))

  class __metaclass__(type):
    def __init__(cls, *args):
      items = (
          objects.WORKFLOWS, objects.RISK_ASSESSMENTS, objects.THREATS,
          objects.RISKS, objects.PROGRAMS, objects.AUDITS,
          objects.OBJECTIVES, objects.SECTIONS, objects.CONTROLS,
          objects.ISSUES, objects.ASSESSMENTS, objects.STANDARDS,
          objects.REGULATIONS, objects.POLICIES, objects.CONTRACTS,
          objects.CLAUSES, objects.VENDORS, objects.PEOPLE,
          objects.ACCESS_GROUPS, objects.ORG_GROUPS, objects.PRODUCTS,
          objects.MARKETS, objects.PROCESSES, objects.FACILITIES,
          objects.PROJECTS, objects.DATA_ASSETS, objects.SYSTEMS)

      for id_, name in enumerate(items, start=1):
        setattr(cls,
                Common.TOGGLE + name.upper(),
                cls._Locator.get_toggle(id_))

  FILTER_INPUT_FIELD = (By.CLASS_NAME, 'tree-filter__expression-holder')
  FILTER_BUTTON_SUBMIT = (By.CSS_SELECTOR,
                          '.tree-filter__button>[type="submit"]')
  FILTER_BUTTON_RESET = (By.CSS_SELECTOR,
                         '.tree-filter__button>[type="reset"]')

  # programs dropdown
  BUTTON_ADD_CUSTOM_PROGRAM_ATTR = (
      By.CSS_SELECTOR,
      '.tree-item:nth-child(5) [data-test-id="button_add-86eaf948"]')
  PROGRAMS_LABEL_ATTRIBUTE_NAME = _Locator.get_programs_label(1)
  PROGRAMS_LABEL_ATTRIBUTE_TYPE = _Locator.get_programs_label(2)
  PROGRAMS_LABEL_MANDATORY = _Locator.get_programs_label(3)
  PROGRAMS_LABEL_EDIT = _Locator.get_programs_label(4)
  LISTED_MEMBERS = (
      By.CSS_SELECTOR,
      '.tree-structure li:nth-child(5) div tbody>tr')
  BUTTON_LISTED_MEMBERS_EDIT = (
      By.CSS_SELECTOR,
      '.tree-structure li:nth-child(5) div tbody>tr>td>ul .fa-pencil-square-o')
  CA_ADDED_SUCCESS_ALERT = PageHeader.GENERIC_SUCCESS_ALERT


class CustomAttributesItemContent(AdminCustomAttributes):
  """Locators for the expanded view of custom attribute group
   in admin dashboard."""
  _base_locator = ".content-open .tier-2-info-content"
  _row_locator = "{} .tree-structure .cms_controllers_tree_view_node"\
      .format(_base_locator)
  TITLES_ROW = (By.CSS_SELECTOR, "{} thead tr".format(_base_locator))
  ROW = (By.CSS_SELECTOR, _row_locator)
  CELL_IN_ROW = (By.CSS_SELECTOR, "td")
  EDIT_BTN = (By.CSS_SELECTOR, "{} .tree-action-list a".format(_row_locator))
  ADD_BTN = (By.CSS_SELECTOR, "{} .add-item .btn".format(_base_locator))
  TREE_SPINNER = (By.CSS_SELECTOR, ".tree-spinner")
