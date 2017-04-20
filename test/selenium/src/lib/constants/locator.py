# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Locators for all elements."""
# pylint: disable=too-few-public-methods
# pylint: disable=too-many-lines

from selenium.webdriver.common.by import By

from lib.constants import objects, url, element


class Common(object):
  """Common locators."""
  # modal
  MODAL_GENEATE = ".modal-selector"
  MODAL_CREATE = ".modal-wide"
  MODAL_CONFIRM = ".modal.hide"
  MODAL_MAP = ".modal-selector"
  # info page (panel)
  PIN_CONTENT = ".pin-content "
  INFO_WIDGET = ".info"
  INFO_HEADER = INFO_WIDGET + " .pane-header"
  INFO_UTILITY = INFO_WIDGET + " .info-pane-utility"
  INFO_TOGGLE = INFO_UTILITY + " .dropdown-toggle"
  # dropdown
  DROPDOWN_MENU = ".dropdown-menu"
  # tree
  TREE_LIST = ".tree-action"
  TREE_HEADER = ".tree-header"
  # base
  BUTTON = "BUTTON_"
  BUTTON_CREATE_NEW = "BUTTON_CREATE_NEW_"
  COUNT = "COUNT_"
  SPINNY = "SPINNY_"
  ACCORDION_MEMBERS = "ACCORDION_MEMBERS_"
  TOGGLE = "TOGGLE_"
  # attrs values
  DISABLED_VALUE = "disabled-original disabled"


class Login(object):
  """Locators for Login page."""
  BUTTON_LOGIN = (By.CSS_SELECTOR, "a.btn.btn-large.btn-info")


class PageHeader(object):
  """Locators for Dashboard header."""
  _CONTENT = ".header-content"
  TOGGLE_LHN = (By.CSS_SELECTOR, ".lhn-trigger")
  BUTTON_DASHBOARD = (
      By.CSS_SELECTOR, _CONTENT + ' .to-my-work[href="/dashboard"]')
  BUTTON_SEARCH = (
      By.CSS_SELECTOR, _CONTENT + ' [data-toggle="unified-search"]')
  BUTTON_MY_TASKS = (
      By.CSS_SELECTOR, _CONTENT + ' [href="/dashboard#task_widget"]')
  BUTTON_ALL_OBJECTS = (
      By.CSS_SELECTOR, _CONTENT + ' [href^="/objectBrowser"]')
  TOGGLE_USER_DROPDOWN = (By.CSS_SELECTOR, _CONTENT + " .dropdown-toggle")
  GENERIC_SUCCESS_ALERT = (By.CSS_SELECTOR, ".alert-success")
  BUTTON_ADMIN_DASHBOARD = (
      By.CSS_SELECTOR, _CONTENT + ' [href="/admin#people_list_widget"]')
  BUTTON_DATA_IMPORT = (
      By.CSS_SELECTOR, _CONTENT + ' [href="/import"]')
  BUTTON_DATA_EXPORT = (
      By.CSS_SELECTOR, _CONTENT + ' [href="/export"]')
  # dropdown toggle
  USER_MENU = ".menu " + Common.DROPDOWN_MENU
  BUTTON_HELP = (By.CSS_SELECTOR, Common.DROPDOWN_MENU + ' #page-help')
  BUTTON_LOGOUT = (By.CSS_SELECTOR, Common.DROPDOWN_MENU + ' [href="/logout"]')
  NOTIFICATIONS = (By.CSS_SELECTOR, USER_MENU + ' .notify-wrap')
  CHECKBOX_DAILY_DIGEST = (By.CSS_SELECTOR, USER_MENU + ' input')
  CHECKBOX_DISABLED = (By.CSS_SELECTOR, USER_MENU + ' input.disabled')


class Dashboard(object):
  """Locators for Dashboard page."""
  _GET_LIST = ".get-started__list"
  # get started (user input elements)
  BUTTON_START_NEW_PROGRAM = (
      By.CSS_SELECTOR, _GET_LIST + ' [data-object-singular="Program"]')
  BUTTON_START_NEW_AUDIT = (
      By.CSS_SELECTOR, _GET_LIST + ' [data-object-singular="Audit"]')
  BUTTON_START_NEW_WORKFLOW = (
      By.CSS_SELECTOR, _GET_LIST + ' [data-object-singular="Workflow"]')
  BUTTON_CREATE_NEW_OBJECT = (By.CSS_SELECTOR, _GET_LIST + ' [href="#"]')
  BUTTON_ALL_OBJECTS = (
      By.CSS_SELECTOR, _GET_LIST + ' [href="/objectBrowser"]')


class LhnMenu(object):
  """Locators for Menu in header"""
  class _Locator(object):
    """Locators for LHN menu."""

    @staticmethod
    def get_accordion_button(label):
      return (By.CSS_SELECTOR, '[data-model-name="{}"]>a'.format(label))

    @staticmethod
    def get_create_new_button(label):
      return (
          By.CSS_SELECTOR,
          '[data-model-name="{}"] [data-test-id='
          '"button_lhn_create_new_program_522c563f"]'.format(label))

    @staticmethod
    def get_accordion_count(label):
      return (
          By.CSS_SELECTOR, '[data-model-name="{}"] .item-count'.format(label))

    @staticmethod
    def get_accordion_members(object_name):
      return (
          By.CSS_SELECTOR,
          '[data-model-name="{}"]>.content>.sub-level>li'.format(object_name))

    @staticmethod
    def get_spinny(object_name):
      return (
          By.CSS_SELECTOR,
          '[data-model-name="{}"] .spinny'.format(object_name))

  class __metaclass__(type):
    def __init__(cls, *args):
      for object_singular, object_plural in (zip(objects.ALL_SINGULAR,
                                                 objects.ALL_PLURAL)):
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
  # user input elements
  LHN_MENU = (By.ID, "lhn")
  MODAL = (By.CSS_SELECTOR, '[id="ajax-lhn_modal-javascript:--"]')
  EXTENDED_INFO = (By.CSS_SELECTOR, ".extended-info.in .info .fa")
  FILTER = (By.CSS_SELECTOR, ".lhs-search")
  FILTER_TEXT_BOX = (By.CSS_SELECTOR, ".lhs-search>.widgetsearch")
  FILTER_SUBMIT_BUTTON = (By.CSS_SELECTOR, ".lhs-search>.widgetsearch-submit")
  FILTER_CLEAR_BUTTON = (
      By.CSS_SELECTOR, '.lhs-search [data-title="Clear filters"]')
  LHS_ITEM = (By.CSS_SELECTOR, '[test-data-id="lhs-item_3ad27b8b"]')
  ALL_OBJECTS = (By.CSS_SELECTOR, '[data-test-id="all_objects_e0345ec4"]')
  MY_OBJECTS = (By.CSS_SELECTOR, '[data-test-id="my_objects_6fa95ae1"]')
  PIN = (By.CSS_SELECTOR, ".lhn-pin")
  # LHN items
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
  """Locators for Extended info tooltip in LHN after hovering over
 member object."""
  # labels
  TITLE = (By.CSS_SELECTOR, "#extended-info .main-title")
  # user input elements
  BUTTON_MAP_TO = (
      By.CSS_SELECTOR, '[data-test-id="extended_info_button_map"]')
  ALREADY_MAPPED = (
      By.CSS_SELECTOR, '[data-test-id="extended_info_object_already_mapped"]')


class CommonModalUnifiedMapper(object):
  """Common locators for unified mapper modals."""
  MODAL = Common.MODAL_MAP
  # labels
  MODAL_TITLE = (By.CSS_SELECTOR, MODAL + " h2")
  OBJ_TYPE = (By.CSS_SELECTOR, MODAL + " .col:nth-child(1) h6")
  FILTER_BY_EXPRESSION = (By.CSS_SELECTOR, MODAL + " .col.filter h6")
  # user input elements
  OBJ_TYPE_DROPDOWN = (By.CSS_SELECTOR, MODAL + " .input-block-level")
  OBJ_TYPE_DROPDOWN_OPTIONS = (By.CSS_SELECTOR,
                               MODAL + " .input-block-level option")
  FILTER_VIA_EXPRESSION_TEXT_BOX = (By.CSS_SELECTOR, MODAL + " #mapper-filter")
  FILTER_BY_STATE_DROPDOWN = (By.CSS_SELECTOR,
                              MODAL + " .multiselect-dropdown__input")
  FILTER_BY_STATE_DROPDOWN_OPTIONS = (By.CSS_SELECTOR,
                                      MODAL + " .multiselect-dropdown__label")
  BUTTON_SEARCH = (By.CSS_SELECTOR, MODAL + " .filter-buttons .btn-small")
  FOUND_OBJECTS_TITLES = (By.CSS_SELECTOR, MODAL + " .flex-box .title-attr")
  FOUND_OBJECTS_CHECKBOXES = (By.CSS_SELECTOR,
                              MODAL + ' .flex-box [type="checkbox"]')
  BUTTON_MAP_SELECTED = (By.CSS_SELECTOR, MODAL + " .modal-footer .btn-map")


class ModalMapObjects(CommonModalUnifiedMapper):
  """Locators for map objects modals."""
  MODAL = Common.MODAL_MAP
  # user input elements
  BUTTON_CREATE_OBJ = (By.CSS_SELECTOR, MODAL + " .create-control")


class ModalSearchObjects(CommonModalUnifiedMapper):
  """Locators for search objects modals."""
  MODAL = Common.MODAL_MAP


class ModalGenerateAssessments(CommonModalUnifiedMapper):
  """Locators for generate Assessments modal."""
  MODAL = Common.MODAL_GENEATE


class BaseModalCreateNew(object):
  """Locators for Create new object modals."""
  MODAL = Common.MODAL_CREATE
  # labels
  MODAL_TITLE = (By.CSS_SELECTOR, MODAL + " .ui-draggable-handle>h2")
  TITLE = (By.CSS_SELECTOR,
           MODAL + " .modal-body form>div:nth-child(2) .span6>label")
  # user input elements
  UI_TITLE = (By.CSS_SELECTOR,
              MODAL + " .modal-body form>div:nth-child(2) .span6>input")


class ModalCreateNewObject(BaseModalCreateNew):
  """Locators for Create new object modals."""
  MODAL = Common.MODAL_CREATE
  # user input elements
  UI_TITLE = (By.CSS_SELECTOR, MODAL + ' [placeholder="Enter Title"]')
  UI_CODE = (By.CSS_SELECTOR, MODAL + ' [name="slug"]')
  BUTTON_SAVE_AND_CLOSE = (By.CSS_SELECTOR,
                           MODAL + ' [data-toggle="modal-submit"]')
  BUTTON_SAVE_AND_ADD_ANOTHER = (
      By.CSS_SELECTOR, '{} [data-toggle="modal-submit-addmore"]'.format(MODAL))


class ModalCreateNewProgram(BaseModalCreateNew):
  """Locators for Create new Program modals."""
  # user input elements
  UI_DESCRIPTION = (By.CSS_SELECTOR,
                    '[data-test-id="new_program_field_description_1fb8bc06"] '
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
  UI_PRIMARY_CONTACT = (
      By.CSS_SELECTOR,
      '[data-test-id="new_program_field_primary_contact_86160053"]')
  DROPDOWN_CONTACT = (By.CSS_SELECTOR, '.ui-menu-item')
  UI_SECONDARY_CONTACT = (
      By.CSS_SELECTOR,
      '[data-test-id="new_program_field_secondary_contact_86160053"]')
  UI_PROGRAM_URL = (
      By.CSS_SELECTOR,
      '[data-test-id="new_program_field_program_url_86160053"]')
  UI_REFERENCE_URL = (
      By.CSS_SELECTOR,
      '[data-test-id="new_program_field_reference_url_86160053"]')
  UI_EFFECTIVE_DATE = (By.CSS_SELECTOR,
                       '[test-id="new_program_field_effective_date_f2783a28"] '
                       '[data-id="effective_date_hidden"] .datepicker__input')
  EFFECTIVE_DATE_DATEPICKER = (
      By.CSS_SELECTOR,
      '[test-id="new_program_field_effective_date_f2783a28"] '
      '[data-id="effective_date_hidden"] [data-handler="selectDay"]')
  UI_STOP_DATE = (
      By.CSS_SELECTOR,
      '[test-id="new_program_field_effective_date_f2783a28"] '
      '[data-id="stop_date_hidden"] .datepicker__input')
  STOP_DATE_DATEPICKER = (
      By.CSS_SELECTOR,
      '[test-id="new_program_field_effective_date_f2783a28"] '
      '[data-id="stop_date_hidden"] [data-handler="selectDay"]')
  TITLE = (By.CSS_SELECTOR, '[data-test-id="label_title_2c925d94"]')
  DESCRIPTION = (
      By.CSS_SELECTOR, '[data-test-id="label_description_2c925d94"]')
  PRIVACY = (By.CSS_SELECTOR, '[data-test-id="label_privacy_2c925d94"]')
  PROGRAM_URL = (
      By.CSS_SELECTOR, '[data-test-id="label_program_url_2c925d94"]')


class ModalCreateNewOrgGroup(BaseModalCreateNew):
  """Locators for Create new Org Group modals."""


class ModalCreateNewRisk(BaseModalCreateNew):
  """Locators for Create new Risk modals."""
  UI_DESCRIPTION = (
      By.CSS_SELECTOR, '.modal-body form>div:nth-child(3) iframe')


class ModalCreateNewDataAsset(BaseModalCreateNew):
  """Locators for Create new Data Asset modals."""


class ModalCreateNewProcess(BaseModalCreateNew):
  """Locators for Create new Process modals."""


class ModalCreateNewProject(BaseModalCreateNew):
  """Locators for Create new Project modals."""


class ModalCreateNewSystem(BaseModalCreateNew):
  """Locators for Create new System modals."""


class ModalCreateNewProduct(BaseModalCreateNew):
  """Locators for Create new Product modals."""


class ModalCreateNewControl(BaseModalCreateNew):
  """Locators for Create new Control modals."""
  class _Locator(object):
    """Locators for Create new Control modals visible when creating from LHN.
    """
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
      By.CSS_SELECTOR, '[data-test-id="control_description-label_9cc51ca3"]')
  UI_DESCRIPTION = (
      By.CSS_SELECTOR,
      '[data-test-id="control_description-text_9cc51ca3"] iframe')
  TEST_PLAN = (
      By.CSS_SELECTOR, '[data-test-id="control_test_plan_d8b5a2f4"] label')
  UI_TEST_PLAN = (
      By.CSS_SELECTOR, '[data-test-id="control_test_plan_d8b5a2f4"] iframe')
  NOTES = (By.CSS_SELECTOR, '[data-id="note_hidden"] label')
  CODE = (By.CSS_SELECTOR, '[data-test-id="control_code_f8abbcc9"] label')
  UI_CODE = (
      By.CSS_SELECTOR, '[data-test-id="control_code_f8abbcc9"] input')
  KIND_OR_NATURE = (
      By.CSS_SELECTOR, '[data-test-id="control_kind_nature_dadc232f"] label')
  DROPDOWN_KIND_OR_NATURE = (
      By.CSS_SELECTOR, '[data-test-id="control_kind_nature_dadc232f"] select')
  FRAUD_RELATED = (
      By.CSS_SELECTOR, '[data-test-id="control_fraud_9cc51ca3"] label')
  DROPDOWN_FRAUD_RELATED = (
      By.CSS_SELECTOR, '[data-test-id="control_fraud_9cc51ca3"] select')
  FREQUENCY = (
      By.CSS_SELECTOR, '[data-test-id="control_frequency_fb20318a"] label')
  DROPDOWN_FREQUENCY = (
      By.CSS_SELECTOR, '[data-test-id="control_frequency_fb20318a"] select')
  ASSERTIONS = (
      By.CSS_SELECTOR, '[data-test-id="control_assertions_5d8b7f7a"] label')
  SELECTABLE_ASSERTIONS = (
      By.CSS_SELECTOR, '[data-test-id="control_assertions_5d8b7f7a"] select')
  PRINCIPAL_ASSESSOR = (
      By.CSS_SELECTOR,
      '[data-test-id="control_primary_assessor_f7379330"] label')
  SECONDARY_ASSESSOR = (
      By.CSS_SELECTOR,
      '[data-test-id="control_secondary_assessor_b9439af6"] label')
  ADMIN = (
      By.CSS_SELECTOR, '[data-test-id="control_owner_587d12d6"] label')
  BUTTON_ADD_OWNER = (By.CSS_SELECTOR, 'isolate-form .btn')
  PRIMARY_CONTACT = (
      By.CSS_SELECTOR, '[data-test-id="control_contacts_8bd3d8c7"] '
                       '.row-fluid:nth-child(1) label')
  UI_PRIMARY_CONTACT = (
      By.CSS_SELECTOR, '[data-test-id='
                       '"new_program_field_primary_contact_86160053"]')
  SECONDARY_CONTACT = (
      By.CSS_SELECTOR, '[data-test-id="control_contacts_8bd3d8c7"] '
                       '.row-fluid:nth-child(2) label')
  UI_SECONDARY_CONTACT = (
      By.CSS_SELECTOR,
      '[data-test-id="new_program_field_secondary_contact_86160053"]')
  CONTROL_URL = (
      By.CSS_SELECTOR, '[data-test-id="control_control_url-label_c4038873"]')
  UI_CONTROL_URL = (
      By.CSS_SELECTOR, '[data-test-id="control_control_url-input_c4038873"]')
  REFERENCE_URL = (
      By.CSS_SELECTOR, '[data-test-id="control_reference_url-label_8931063d"]')
  UI_REFERENCE_URL = (
      By.CSS_SELECTOR, '[data-test-id="control_reference_url-input_8931063d"]')
  SIGNIFICANCE = (
      By.CSS_SELECTOR, '[data-test-id="control_significance_18f15545"] label')
  DROPDOWN_SIGNIFICANCE = (
      By.CSS_SELECTOR, '[data-test-id="control_significance_18f15545"] select')
  TYPE_OR_MEANS = (
      By.CSS_SELECTOR, '[data-test-id="control_type_means_2ffa1b64"] label')
  DROPDOWN_TYPE_OR_MEANS = (
      By.CSS_SELECTOR, '[data-test-id="control_type_means_2ffa1b64"] select')
  CATEGORIES = (
      By.CSS_SELECTOR, '[data-test-id="control_categories_1eb33246"] label')
  SELECTABLE_CATEGORIES = (
      By.CSS_SELECTOR, '[data-test-id="control_categories_1eb33246"] select')
  STATE = (
      By.CSS_SELECTOR, '[data-test-id="control_state_5d184456"] label')
  DROPDOWN_STATE = (
      By.CSS_SELECTOR, '[data-test-id="control_state_5d184456"] select')
  UI_NOTES = (By.CSS_SELECTOR, '[data-id="note_hidden"] iframe')
  EFFECTIVE_DATE = (
      By.CSS_SELECTOR,
      '[test-id="control_effective_dates_0376cf90"] '
      '[data-id="effective_date_hidden"] .datepicker__input')
  DATEPICKER_EFFECTIVE_DATE = (
      By.CSS_SELECTOR,
      '[test-id="control_effective_dates_0376cf90"] '
      '[data-id="effective_date_hidden"] [data-handler="selectDay"]')
  STOP_DATE = (
      By.CSS_SELECTOR,
      '[test-id="control_effective_dates_0376cf90"] '
      '[data-id="stop_date_hidden"] .datepicker__input')
  DATEPICKER_STOP_DATE = (
      By.CSS_SELECTOR,
      '[test-id="control_effective_dates_0376cf90"] '
      '[data-id="stop_date_hidden"] [data-handler="selectDay"]')
  BUTTON_HIDE_ALL_OPTIONAL_FIELDS = (By.CSS_SELECTOR, '#formHide')


class ModalCreateNewIssue(BaseModalCreateNew):
  """Locators for Create new Issue modals."""


class ModalCreateNewAsmt(BaseModalCreateNew):
  """Locators for Create new Assessment modals."""


class ModalCreateNewAsmtTmpl(BaseModalCreateNew):
  """Locators for Create new Assessment Template modals."""


class ModalEditObject(BaseModalCreateNew):
  """Locators for Edit object modals."""
  BUTTON_DELETE = (
      By.CSS_SELECTOR, '.deny-buttons [data-toggle="modal-ajax-deleteform"]')


class ModalCustomAttribute(object):
  """Locators for generic custom attributes modal in Admin Dashboard."""
  MODAL_TITLE = (By.CSS_SELECTOR, '.modal-header h2')
  ATTRIBUTE_TITLE = (By.CSS_SELECTOR, '.modal-body div:nth-child(1)>label')
  INLINE_HELP = (By.CSS_SELECTOR, '.modal-body div:nth-child(2)>label')
  ATTRIBUTE_TYPE = (By.CSS_SELECTOR, '.modal-header h2')
  PLACEHOLDER = (By.CSS_SELECTOR, '.modal-header h2')
  MANDATORY = (By.CSS_SELECTOR, '.modal-header h2')
  UI_ATTRIBUTE_TITLE = (By.CSS_SELECTOR, '.modal-body [name="title"]')
  UI_INLINE_HELP = (By.CSS_SELECTOR, '.modal-body [name="helptext"]')
  UI_PLACEHOLDER = (By.CSS_SELECTOR, '.modal-body [name="placeholder"]')
  UI_POSSIBLE_VALUES = (
      By.CSS_SELECTOR, '.modal-body [name="multi_choice_options"]')
  CHECKBOX_MANDATORY = (By.CSS_SELECTOR, '.modal-body [type="checkbox"]')
  BUTTON_ADD_ANOTHER = (
      By.CSS_SELECTOR, '.confirm-buttons [data-toggle="modal-submit-addmore"]')
  BUTTON_SAVE_AND_CLOSE = (
      By.CSS_SELECTOR,
      '.modal-footer .confirm-buttons [data-toggle="modal-submit"]')
  ATTRIBUTE_TYPE_SELECTOR = (By.CSS_SELECTOR, "dropdown select")
  ATTRIBUTE_TYPE_OPTIONS = (By.CSS_SELECTOR, "dropdown select option")


class ModalSetVisibleFields(object):
  """Locators for Set visible fields modals."""
  MODAL = ".open .visible-columns-list"
  # labels
  MODAL_TITLE = MODAL + " h5"
  ATTR_LIST = " .attr-list"
  FIELDS_TITLES = MODAL + ATTR_LIST + " .checkbox-inline"
  # user input elements
  FIELDS_CHECKBOXES = MODAL + ATTR_LIST + " .attr-checkbox"
  BUTTON_SET_FIELDS = MODAL + " .set-tree-attrs"


class ModalSetVisibleFieldsMapper(ModalSetVisibleFields):
  """Locators for Set visible fields modals."""
  MODAL = ".modal-body"
  # labels
  MODAL_TITLE = MODAL + " h5"
  ATTR_LIST = ModalSetVisibleFields.ATTR_LIST
  FIELDS_TITLES = MODAL + ATTR_LIST + " .checkbox-inline"
  # user input elements
  FIELDS_CHECKBOXES = MODAL + ATTR_LIST + " .attr-checkbox"
  BUTTON_SET_FIELDS = MODAL + " .set-tree-attrs"


class WidgetBar(object):
  """Locators for bar containing widgets/tabs."""

  class _Locator(object):
    """Locators for Menu in header."""
    @staticmethod
    def get_widget(object_name):
      return (
          By.CSS_SELECTOR,
          '.object-nav [href$="#{}_widget"]'.format(object_name))

  class __metaclass__(type):
    def __init__(cls, *args):
      for object_singular, object_plural in (zip(objects.ALL_SINGULAR,
                                                 objects.ALL_PLURAL)):
        name = object_singular.lower()
        setattr(cls, object_plural, cls._Locator.get_widget(name))
  BUTTON_ADD = (
      By.CSS_SELECTOR, '[data-test-id="button_widget_add_2c925d94"]')
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
  """Locators for button/dropdown "Add widget" in Widget bar."""
  class _Locator(object):
    """Toggle locators for Widget custom attributes in Admin Dashboard."""
    @staticmethod
    def get_dropdown_item(object_name):
      return (
          By.CSS_SELECTOR,
          '[data-test-id="button_widget_add_2c925d94"] '
          '.object-nav [href$="#{}_widget"]'.format(object_name))

  class __metaclass__(type):
    def __init__(cls, *args):
      for object_ in objects.ALL_PLURAL:
        name = object_.lower()
        setattr(cls, object_, cls._Locator.get_dropdown_item(name))
  THREAD_ACTORS = _Locator.get_dropdown_item("threat_actor")
  WORKFLOW_TASKS = _Locator.get_dropdown_item("workflow_task")


class ObjectWidget(object):
  """Locators for Generic objects widget."""
  _HEADER = '.header [class^="span"]'
  HEADER_TITLE = (By.CSS_SELECTOR, _HEADER + ' [data-field="title"]')
  HEADER_OWNER = (
      By.CSS_SELECTOR, _HEADER + ' [data-field="owners"]')
  HEADER_STATE = (By.CSS_SELECTOR, _HEADER + ' [data-field="status"]')
  HEADER_LAST_ASSESSMENT_DATE = (
      By.CSS_SELECTOR, _HEADER + ' [data-field="last_assessment_date"]')
  MEMBERS_TITLE_LIST = (
      By.CSS_SELECTOR,
      '.object-area .tree-item-element .selectable-attrs '
      '.attr-cell:first-child .attr-content')
  INFO_PANE = (By.CSS_SELECTOR, '.sticky-info-panel')
  LOADING = (By.CSS_SELECTOR, '.new-tree_loading')


class ModalCommonConfirmAction(object):
  """Locators for Confirm actions with objects modals."""
  MODAL = Common.MODAL_CONFIRM
  # labels
  MODAL_TITLE = (By.CSS_SELECTOR, "{} .modal-header h2".format(MODAL))
  CONFIRMATION_TEXT = (By.CSS_SELECTOR, "{} .modal-body p".format(MODAL))
  # user input elements
  BUTTON_CONFIRM = (By.CSS_SELECTOR,
                    "{} .modal-footer .btn-small".format(MODAL))


class ModalDeleteObject(ModalCommonConfirmAction):
  """Locators for Delete object modals."""
  MODAL = Common.MODAL_CONFIRM
  OBJECT_TITLE = (By.CSS_SELECTOR, "{} .modal-body span".format(MODAL))
  BUTTON_DELETE = ModalCommonConfirmAction.BUTTON_CONFIRM


class ModalUpdateObject(ModalCommonConfirmAction):
  """Locators for Update object modals."""
  PERMALINK_ALERT = (By.CSS_SELECTOR, '.content>.flash>.alert-success')


class ModalCloneAudit(ModalCommonConfirmAction):
  """Locators for Clone object modals."""
  MODAL = Common.MODAL_CONFIRM
  CHECKBOX_CLONE_ASMT_TMPLS = (
      By.CSS_SELECTOR,
      '{} [can-value="instance.includeObjects.AssessmentTemplate"]'
        .format(MODAL))


class CommonWidgetInfo(object):
  """Common locators for Info widgets and Info panels."""
  PIN_CONTENT = Common.PIN_CONTENT
  INFO_HEADER = Common.INFO_HEADER
  INFO_TOGGLE = Common.INFO_TOGGLE
  HEADERS_VALUES = (
      '//*[contains(@class, "object-area")]//*[contains(@class, "info")]'
      '//div[starts-with(./@class, "span")]')
  HEADER = HEADERS_VALUES + '//*[contains(text(),"{header}")]'
  # labels
  HEADERS_AND_VALUES = (By.XPATH, HEADERS_VALUES)
  TITLE = (By.CSS_SELECTOR, INFO_HEADER + " h6")
  TITLE_ENTERED = (By.CSS_SELECTOR, INFO_HEADER + " .span9 h3")
  STATE = (By.CSS_SELECTOR, INFO_HEADER + " .state-value")
  # user input elements
  BUTTON_3BBS = (By.CSS_SELECTOR, INFO_TOGGLE)
  BUTTON_3BBS_UNDER_AUDIT = (By.CSS_SELECTOR, PIN_CONTENT + INFO_TOGGLE)


class CommonWidgetInfoSnapshots(object):
  """Common locators for Info widgets and Info panels of snapshotable objects.
 """
  WIDGET = Common.INFO_WIDGET
  LINK_GET_LAST_VER = (
      By.CSS_SELECTOR, WIDGET + ' .snapshot [can-click="compareIt"]')


class WidgetInfoProgram(CommonWidgetInfo):
  """Locators for Program Info widgets."""
  # pylint: disable=too-many-format-args
  WIDGET = Common.INFO_WIDGET
  TOGGLE_SHOW_ADVANCED = (
      By.CSS_SELECTOR, "{} .show-hidden-fields".format(WIDGET))
  TOGGLE_SHOW_ADVANCED_ACTIVATED = (
      By.CSS_SELECTOR, "{} .show-hidden-fields.active".format(WIDGET))
  OBJECT_REVIEW = (
      By.CSS_SELECTOR,
      '{} [data-test-id="title_review_0ad9fbaf"] h6'.format(WIDGET))
  SUBMIT_FOR_REVIEW = (By.CSS_SELECTOR, "{} .non-transparent".format(WIDGET))
  DESCRIPTION = (
      By.CSS_SELECTOR,
      '{} [data-test-id="title_description_7a906d2e"] h6'.format(WIDGET))
  DESCRIPTION_ENTERED = (
      By.CSS_SELECTOR,
      '{} [data-test-id="title_description_content_7a906d2e"]'.format(WIDGET))
  NOTES = (By.CSS_SELECTOR,
           '{} [data-test-id="title_notes_ef5bc3a71e88"] h6'.format(WIDGET))
  NOTES_ENTERED = (
      By.CSS_SELECTOR,
      '{} [data-test-id="title_notes_content_ef5bc3a71e88"]'.format(WIDGET))
  MANAGER = (By.CSS_SELECTOR,
             '{} [data-test-id="title_manager_7a906d2e"] h6'.format(WIDGET))
  MANAGER_ENTERED = (By.CSS_SELECTOR,
                     '{} [data-test-id="title_manager_7a906d2e"] '
                     '[data-test-id="text_manager_7a906d2e"]'.format(WIDGET))
  PRIMARY_CONTACT = (By.CSS_SELECTOR,
                     '{} [data-test-id="title_primary_contact_696de7244b84"] '
                     'h6'.format(WIDGET))
  PRIMARY_CONTACT_ENTERED = (
      By.CSS_SELECTOR,
      '{} [data-test-id="text_primary_contact_696de7244b84"] '
      '[data-test-id="text_manager_7a906d2e"]'.format(WIDGET))
  SECONDARY_CONTACT = (
      By.CSS_SELECTOR,
      '{} [data-test-id="title_contacts_696de7244b84"] '
      'h6:nth-child(2)'.format(WIDGET))
  SECONDARY_CONTACT_ENTERED = (
      By.CSS_SELECTOR,
      '{} [data-test-id="text_secondary_contact_696de7244b84"] '
      '[data-test-id="text_manager_7a906d2e"]'.format(WIDGET))
  PROGRAM_URL = (
      By.CSS_SELECTOR,
      '{} [data-test-id="title_program_url_aa7d1a65"] h6'.format(WIDGET))
  PROGRAM_URL_ENTERED = (
      By.CSS_SELECTOR,
      '{} [data-test-id="text_program_url_aa7d1a65"]'.format(WIDGET))
  REFERENCE_URL = (
      By.CSS_SELECTOR,
      '{} [data-test-id="title_reference_url_aa7d1a65"]'.format(WIDGET))
  REFERENCE_URL_ENTERED = (
      By.CSS_SELECTOR,
      '[data-test-id="text_reference_url_aa7d1a65"]'.format(WIDGET))
  CODE = (By.CSS_SELECTOR,
          '{} [data-test-id="title_code_cf47bc01"] h6'.format(WIDGET))
  CODE_ENTERED = (By.CSS_SELECTOR,
                  '{} [data-test-id="title_code_cf47bc01"] p'.format(WIDGET))
  EFFECTIVE_DATE = (
      By.CSS_SELECTOR,
      '{} [data-test-id="title_effective_date_cf47bc01"] h6'.format(WIDGET))
  EFFECTIVE_DATE_ENTERED = (
      By.CSS_SELECTOR,
      '[data-test-id="title_effective_date_cf47bc01"] p'.format(WIDGET))
  STOP_DATE = (
      By.CSS_SELECTOR,
      '{} [data-test-id="title_stop_date_cf47bc01"] h6'.format(WIDGET))
  STOP_DATE_ENTERED = (
      By.CSS_SELECTOR,
      '[data-test-id="title_stop_date_cf47bc01"] p'.format(WIDGET))
  PRIVATE_PROGRAM = (By.CSS_SELECTOR,
                     '[data-test-id="title_private_ec758af9"] h6')
  ICON_LOCK = (By.CSS_SELECTOR, '[data-test-id="icon_private_ec758af9"]')
  PERMALINK_ALERT = (By.CSS_SELECTOR, ".content>.flash>.alert-success")
  ALERT_LINK_COPIED = (By.CSS_SELECTOR, ".alert.alert-success")
  MODAL_DELETE = (By.ID, '[id="ajax-lhn_modal-javascript:--"]')
  MODAL_DELETE_CLOSE = (By.CSS_SELECTOR, ".lhn_modal .grcicon-x-grey")


class WidgetInfoRisk(CommonWidgetInfo):
  """Locators for Risk Info widgets."""


class WidgetInfoOrgGroup(CommonWidgetInfo):
  """Locators for Org Group Info widgets."""


class WidgetInfoIssue(CommonWidgetInfo):
  """Locators for Issue Info widgets."""


class WidgetInfoRegulations(CommonWidgetInfo):
  """Locators for Regulation Info widgets."""


class WidgetInfoWorkflow(CommonWidgetInfo):
  """Locators for Workflow Info widgets."""


class WidgetInfoAudit(CommonWidgetInfo):
  """Locators for Audit Info widgets."""
  HEADER = CommonWidgetInfo.HEADER
  elements = element.AuditInfoWidget
  # labels
  AUDIT_LEAD = (By.XPATH, HEADER.format(header=elements.AUDIT_LEAD))
  CODE = (By.XPATH, HEADER.format(header=elements.CODE))


class WidgetInfoAssessment(CommonWidgetInfo):
  """Locators for Assessment Info widgets."""


class WidgetInfoAssessmentTemplate(CommonWidgetInfo):
  """Locators for assessment template info widget."""


class WidgetInfoPolicy(CommonWidgetInfo):
  """Locators for Policy Info widgets."""


class WidgetInfoStandard(CommonWidgetInfo):
  """Locators for Standard Info widgets."""


class WidgetInfoContract(CommonWidgetInfo):
  """Locators for Contract Info widgets."""


class WidgetInfoClause(CommonWidgetInfo):
  """Locators for Clause Info widgets."""


class WidgetInfoSection(CommonWidgetInfo):
  """Locators for Section Info widgets."""


class WidgetInfoControl(CommonWidgetInfo, CommonWidgetInfoSnapshots):
  """Locators for Control Info widgets."""


class WidgetInfoObjective(CommonWidgetInfo):
  """Locators for Objective Info widgets."""


class WidgetInfoPeople(CommonWidgetInfo):
  """Locators for People Info widgets."""


class WidgetInfoVendor(CommonWidgetInfo):
  """Locators for Vendor Info widgets."""


class WidgetInfoAccessGroup(CommonWidgetInfo):
  """Locators for Access Group Info widgets."""


class WidgetInfoSystem(CommonWidgetInfo):
  """Locators for System Info widgets."""


class WidgetInfoProcess(CommonWidgetInfo):
  """Locators for Process Info widgets."""


class WidgetInfoProduct(CommonWidgetInfo):
  """Locators for Product Info widgets."""


class WidgetInfoFacility(CommonWidgetInfo):
  """Locators for Facility Info widgets."""


class WidgetInfoProject(CommonWidgetInfo):
  """Locators for Project Info widgets."""


class WidgetInfoMarket(CommonWidgetInfo):
  """Locators for Market Info widgets."""


class WidgetInfoDataAsset(CommonWidgetInfo):
  """Locators for Data Asset Info widgets."""


class WidgetInfoThreat(CommonWidgetInfo):
  """Locators for Threat Info widgets."""


class WidgetAdminRoles(object):
  """Locators for Roles widget on Admin Dashboard."""


class WidgetAdminEvents(object):
  """Locators for Events widget on Admin Dashboard."""
  _BASE_CSS_SELECTOR = 'section#events_list_widget:not([class~="hidden"])'
  _TREE_ITEMS_SELECTOR = ".tree-item[data-model]"
  TREE_VIEW_ITEMS = (
      By.CSS_SELECTOR,
      "{0} {1}".format(_BASE_CSS_SELECTOR, _TREE_ITEMS_SELECTOR))
  TREE_VIEW_HEADER = (
      By.CSS_SELECTOR, "{} header".format(_BASE_CSS_SELECTOR))
  FIRST_TREE_VIEW_ITEM = (
      By.CSS_SELECTOR,
      "{0} {1}:first-child".format(_BASE_CSS_SELECTOR, _TREE_ITEMS_SELECTOR))


class CommonDropdown3bbsInfoWidget(object):
  """Locators for common settings 3BBS dropdown on Info widget and Info page.
 """
  INFO_3BBS_DROPDOWN = Common.INFO_WIDGET + " .dropdown-menu"
  PIN_CONTENT = CommonWidgetInfo.PIN_CONTENT
  EDIT = INFO_3BBS_DROPDOWN + " .fa-pencil-square-o"
  GET_PERMALINK = (INFO_3BBS_DROPDOWN + " .fa-link")
  OPEN = (INFO_3BBS_DROPDOWN + " .fa-long-arrow-right")
  DELETE = (INFO_3BBS_DROPDOWN + " .fa-trash")
  # user input elements
  BUTTON_3BBS_EDIT = (By.CSS_SELECTOR, EDIT)
  BUTTON_3BBS_GET_PERMALINK = (By.CSS_SELECTOR, GET_PERMALINK)
  BUTTON_3BBS_OPEN = (By.CSS_SELECTOR, OPEN)
  BUTTON_3BBS_DELETE = (By.CSS_SELECTOR, DELETE)
  # user input elements under audit
  BUTTON_3BBS_EDIT_UNDER_AUDIT = (By.CSS_SELECTOR, PIN_CONTENT + EDIT)
  BUTTON_3BBS_GET_PERMALINK_UNDER_AUDIT = (By.CSS_SELECTOR,
                                           PIN_CONTENT + GET_PERMALINK)
  BUTTON_3BBS_OPEN_UNDER_AUDIT = (By.CSS_SELECTOR, PIN_CONTENT + OPEN)
  BUTTON_3BBS_DELETE_UNDER_AUDIT = (By.CSS_SELECTOR, PIN_CONTENT + DELETE)


class AuditsDropdown3bbsInfoWidget(CommonDropdown3bbsInfoWidget):
  """Locators for Audit settings 3BBS dropdown on Info page and Info panel.
  """
  INFO_3BBS_DROPDOWN = CommonDropdown3bbsInfoWidget.INFO_3BBS_DROPDOWN
  BUTTON_3BBS_UPDATE = (
      By.CSS_SELECTOR, INFO_3BBS_DROPDOWN + " snapshot-scope-update")
  BUTTON_3BBS_CLONE = (By.CSS_SELECTOR, INFO_3BBS_DROPDOWN + " object-cloner")


class CommonDropdown3bbsTreeView(object):
  """Locators for common settings 3BBS dropdown on Tree View."""
  TREE_VIEW_3BBS_DROPDOWN = (
      "{} " + Common.TREE_LIST + " .tree-action-list-items")
  # user input elements
  BUTTON_3BBS_IMPORT = TREE_VIEW_3BBS_DROPDOWN + " .fa-cloud-upload"
  BUTTON_3BBS_EXPORT = TREE_VIEW_3BBS_DROPDOWN + " .fa-download"
  BUTTON_3BBS_SELECT_CHILD_TREE = TREE_VIEW_3BBS_DROPDOWN + " .fa-share-alt"


class AssessmentsDropdown3bbsTreeView(CommonDropdown3bbsTreeView):
  """Locators for Assessments settings 3BBS dropdown on Tree View."""
  TREE_VIEW_3BBS_DROPDOWN = CommonDropdown3bbsTreeView.TREE_VIEW_3BBS_DROPDOWN
  BUTTON_3BBS_GENERATE = TREE_VIEW_3BBS_DROPDOWN + " .fa-magic"


class TreeView(object):
  """Locators for Tree View components."""
  # common
  ITEMS = ".tree-item-element"
  HEADER = Common.TREE_HEADER
  ITEM_LOADING = (By.CSS_SELECTOR, " .tree-item-placeholder")
  ITEM_EXPAND_BUTTON = "tree-item-actions"
  SPINNER = (By.CSS_SELECTOR, " .tree-spinner")
  NO_RESULTS_MESSAGE = (
      By.CSS_SELECTOR, ".widget:not(.hidden) .tree-no-results-message")
  BUTTON_SHOW_FIELDS = "{} " + Common.TREE_HEADER + " .fa-bars"
  # user input elements
  BUTTON_3BBS = "{} " + Common.TREE_LIST + " .details-wrap"
  BUTTON_CREATE = "{} " + Common.TREE_LIST + " .create-button"
  BUTTON_MAP = "{} " + Common.TREE_LIST + " .map-button"


class AdminTreeView(object):
  """Locators for Tree View components in Admin dashboard."""
  # common
  ITEMS = "li.tree-item .item-main"
  HEADER = Common.TREE_HEADER
  ITEM_LOADING = (By.CSS_SELECTOR, " .tree-item-placeholder")
  ITEM_EXPAND_BUTTON = " .openclose"
  SPINNER = (By.CSS_SELECTOR, " .tree-spinner")
  NO_RESULTS_MESSAGE = (By.CSS_SELECTOR, ".tree-no-results-message")
  BUTTON_SHOW_FIELDS = "{} " + Common.TREE_HEADER + " .fa-bars"
  # user input elements
  BUTTON_3BBS = "{} " + Common.TREE_LIST + " .btn-draft"
  BUTTON_CREATE = "{} " + Common.TREE_LIST + " .create-button"
  BUTTON_MAP = "{} " + Common.TREE_LIST + " .map-button"


class UnifiedMapperTreeView(TreeView):
  MODAL = ".ggrc_controllers_mapper_modal"
  HEADER = MODAL + " .list-header"
  ITEMS = MODAL + " .object-list-item"
  BUTTON_SHOW_FIELDS = HEADER + " .fa-bars"
  NO_RESULTS_MESSAGE = ".well-small:not(.hidden)"


class BaseWidgetGeneric(object):
  """Locators for non Info and Admin widgets."""
  _object_name = None
  widget_info = url.Widget.INFO

  class __metaclass__(type):
    """For sharing parametrized class attributes we simply define how
    class should look like. Note that same functionality can be
    implemented using properties though with more code."""
    def __init__(cls, *args):
      _WIDJET = "#{}_widget"
      _FILTER_BUTTON = _WIDJET + " tree-filter-input .tree-filter__actions"
      _FILTER_DROPDOWN = _WIDJET + " tree-status-filter"
      _FILTER_DROPDOWN_ELEMENTS = (
          _FILTER_DROPDOWN + " .multiselect-dropdown__element")
      cls.TEXTFIELD_TO_FILTER = (
          By.CSS_SELECTOR, str(_WIDJET + " .tree-filter__input")
            .format(cls._object_name))
      cls.BUTTON_FILTER = (
          By.CSS_SELECTOR,
          str(_FILTER_BUTTON + ' [type="submit"]').format(cls._object_name))
      cls.BUTTON_RESET = (
          By.CSS_SELECTOR,
          str(_FILTER_BUTTON + ' [type="reset"]').format(cls._object_name))
      cls.BUTTON_HELP = (
          By.CSS_SELECTOR,
          str(_FILTER_BUTTON + " #page-help").format(cls._object_name))
      cls.DROPDOWN = (
          By.CSS_SELECTOR,
          str(_FILTER_DROPDOWN + " .multiselect-dropdown__input-container")
            .format(cls._object_name))
      cls.DROPDOWN_STATES = (
          By.CSS_SELECTOR,
          str(_FILTER_DROPDOWN_ELEMENTS).format(cls._object_name))
  FILTER_PANE_COUNTER = (
      By.CSS_SELECTOR,
      "section.widget:not(.hidden) .tree-view-pagination__count__title")


class WidgetAudits(BaseWidgetGeneric):
  """Locators for Audits generic widgets."""
  _object_name = objects.get_singular(objects.AUDITS)


class WidgetAssessments(BaseWidgetGeneric):
  """Locators for Assessments generic widgets."""
  _object_name = objects.get_singular(objects.ASSESSMENTS)


class WidgetControls(BaseWidgetGeneric):
  """Locators for Controls generic widgets."""
  _object_name = objects.get_singular(objects.CONTROLS)


class WidgetProducts(BaseWidgetGeneric):
  """Locators for Products generic widgets."""
  _object_name = objects.get_singular(objects.PRODUCTS)


class WidgetProjects(BaseWidgetGeneric):
  """Locators for Projects generic widgets."""
  _object_name = objects.get_singular(objects.PROJECTS)


class WidgetSystems(BaseWidgetGeneric):
  """Locators for Systems generic widgets."""
  _object_name = objects.get_singular(objects.SYSTEMS)


class WidgetDataAssets(BaseWidgetGeneric):
  """Locators for DataAssets generic widgets."""
  _object_name = objects.get_singular(objects.PROJECTS)


class WidgetProcesses(BaseWidgetGeneric):
  """Locators for Processes generic widgets."""
  _object_name = objects.get_singular(objects.PROCESSES)


class WidgetIssues(BaseWidgetGeneric):
  """Locators for Issues generic widgets"""
  _object_name = objects.get_singular(objects.ISSUES)


class WidgetPrograms(BaseWidgetGeneric):
  """Locators for Programs generic widgets"""
  _object_name = objects.get_singular(objects.PROGRAMS)


class WidgetAssessmentTemplates(BaseWidgetGeneric):
  """Locators for Assessment Templates generic widgets."""
  _object_name = objects.get_singular(objects.ASSESSMENT_TEMPLATES)


class AdminCustomAttributes(object):
  """Locators for Widget custom attributes on Admin Dashboard."""

  class _Locator(object):
    """Locators for Widget custom attributes on Admin Dashboard."""
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
      By.CSS_SELECTOR, '.tree-structure li:nth-child(5) div tbody>tr')
  BUTTON_LISTED_MEMBERS_EDIT = (
      By.CSS_SELECTOR,
      '.tree-structure li:nth-child(5) div tbody>tr>td>ul .fa-pencil-square-o')
  CA_ADDED_SUCCESS_ALERT = PageHeader.GENERIC_SUCCESS_ALERT


class CustomAttributesItemContent(AdminCustomAttributes):
  """Locators for expanded view of custom attribute group
  in admin dashboard."""
  CONTENT_OPEN = ".content-open .tier-2-info-content"
  TREE_STRUCTURE = (
      CONTENT_OPEN + " .tree-structure .cms_controllers_tree_view_node")
  TITLES_ROW = (By.CSS_SELECTOR, CONTENT_OPEN + " thead tr")
  ROW = (By.CSS_SELECTOR, TREE_STRUCTURE)
  CELL_IN_ROW = (By.CSS_SELECTOR, "td")
  EDIT_BTN = (By.CSS_SELECTOR, CONTENT_OPEN + " " + Common.TREE_LIST)
  ADD_BTN = (By.CSS_SELECTOR, CONTENT_OPEN + " .add-item .btn")
  TREE_SPINNER = (By.CSS_SELECTOR, ".tree-spinner")
