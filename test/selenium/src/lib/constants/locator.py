# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Locators for all elements."""
# pylint: disable=too-few-public-methods
# pylint: disable=too-many-lines

from selenium.webdriver.common.by import By

from lib.constants import objects


class Common(object):
  """Common locators."""
  TITLE = " .title"
  DESCRIPTION = " .description"
  SPINNER = ".spinner"
  SPINNER_CSS = (By.CSS_SELECTOR, SPINNER)
  # modal
  MODAL_CREATE = ".modal-wide"
  MODAL_CONFIRM = ".modal.hide"
  MODAL_MAPPER = ".modal-selector"
  MODAL_FOOTER = " .modal-footer"
  MODAL_BODY = " .modal-body"
  MODAL_FILTER = " .modal-filter"
  MODAL_HEADER = " .modal-header"
  # info page (panel)
  _INFO = "info"
  INFO = "." + _INFO
  _INFO_WIDGET = "info_widget"
  INFO_WIDGET_ID = "#" + _INFO_WIDGET
  # dropdown
  DROPDOWN_MENU = ".dropdown-menu"
  # tree
  TREE_LIST = " .tree-action"
  TREE_HEADER = ".tree-header"
  TREE_ITEM = " .object-list__item"
  TREE_SPINER = " .tree-spinner"
  # base
  BUTTON = "BUTTON_"
  BUTTON_CREATE_NEW = "BUTTON_CREATE_NEW_"
  COUNT = "COUNT_"
  SPINNY = "SPINNY_"
  ACCORDION_MEMBERS = "ACCORDION_MEMBERS_"
  TOGGLE = "TOGGLE_"
  # attrs values
  DISABLED_VALUE = "disabled-original"
  MAX = "max"
  NORMAL = "normal"
  DOWN = "down"
  # list item delimiter
  HTML_LIST_CSS = (By.CSS_SELECTOR, 'ul')
  # xpath helper
  XPATH_NOT_HIDDEN = "[not(ancestor::section[contains(@class, 'hidden')])]"
  INFO_WIDGET_XPATH = (
      "//section[contains(@class,'{}')]".format(_INFO) + XPATH_NOT_HIDDEN)
  INFO_PAGE_XPATH = (
      "//section[contains(@class,'{}')]".format(_INFO_WIDGET) +
      XPATH_NOT_HIDDEN)
  # import / export pages
  CONTENT = ".content"
  OPTION = "option"
  # panel locator
  PANEL_CSS = (By.CSS_SELECTOR, ".pin-content.cms_controllers_info_pin")
  OBJECT_AREA_CSS = (By.CSS_SELECTOR, ".object-area")
  # widgets
  WDG_NOT_HIDDEN = ".widget:not(.hidden) "


class CommonAssessment(object):
  """Common Assessment locators for Modal and Info."""
  MAP_OBJS_BTN = " map-button-using-assessment-type"
  MAP_OBJS_BTN_CSS = (By.CSS_SELECTOR, MAP_OBJS_BTN)
  MAPPED_SNAPSHOTS = " .mapped-objects__item.mapped-snapshot-item"
  MAPPED_SNAPSHOTS_CSS = (By.CSS_SELECTOR, MAPPED_SNAPSHOTS)
  MAPPED_SNAPSHOT_TITLE_CSS = (
      By.CSS_SELECTOR, MAPPED_SNAPSHOTS + Common.TITLE)
  MAPPED_SNAPSHOT_DESCRIPTION_CSS = (
      By.CSS_SELECTOR, MAPPED_SNAPSHOTS + Common.DESCRIPTION)


class Login(object):
  """Locators for Login page."""
  BUTTON_LOGIN = (By.CSS_SELECTOR, "a.btn.btn-large.btn-lightBlue")


class PageHeader(object):
  """Locators for Dashboard header."""
  _CONTENT = ".header-content"
  SRC_OBJ_TITLE = (By.CSS_SELECTOR, _CONTENT + " .entity-name")
  TOGGLE_LHN = (By.CSS_SELECTOR, ".lhn-trigger")
  BUTTON_DASHBOARD = (
      By.CSS_SELECTOR, _CONTENT + ' .to-my-work[href="/dashboard"]')
  BUTTON_SEARCH = (
      By.CSS_SELECTOR, _CONTENT + ' [data-toggle="unified-search"]')
  BUTTON_MY_TASKS = (
      By.CSS_SELECTOR, _CONTENT + ' [href="/dashboard#!task_widget"]')
  BUTTON_ALL_OBJECTS = (
      By.CSS_SELECTOR, _CONTENT + ' [href^="/objectBrowser"]')
  TOGGLE_USER_DROPDOWN = (By.CSS_SELECTOR, _CONTENT + " .dropdown-toggle")
  GENERIC_SUCCESS_ALERT = (By.CSS_SELECTOR, ".alert-success")
  BUTTON_DATA_IMPORT = (
      By.CSS_SELECTOR, _CONTENT + ' [href="/import"]')
  BUTTON_DATA_EXPORT = (
      By.CSS_SELECTOR, _CONTENT + ' [href="/export"]')
  # dropdown toggle
  USER_MENU = ".menu " + Common.DROPDOWN_MENU
  BUTTON_HELP = (By.CSS_SELECTOR, Common.DROPDOWN_MENU + ' #page-help')
  BUTTON_LOGOUT = (By.CSS_SELECTOR, Common.DROPDOWN_MENU + ' [href="/logout"]')
  NOTIFICATIONS = (By.CSS_SELECTOR, USER_MENU + ' .notify-wrap')
  BUTTON_ADMIN_DASHBOARD = (
      By.CSS_SELECTOR,
      Common.DROPDOWN_MENU + ' [href="/admin#!people_list_widget"]')
  CHECKBOX_DAILY_DIGEST = (By.CSS_SELECTOR, USER_MENU + ' input')
  CHECKBOX_DISABLED = (By.CSS_SELECTOR, USER_MENU + ' input.disabled')


class Dashboard(object):
  """Locators for Dashboard page."""
  _GET_LIST = ".get-started__list"
  # get started (user input elements)
  START_NEW_PROGRAM_BTN_CSS = (
      By.CSS_SELECTOR, _GET_LIST + ' [data-object-singular="Program"]')
  START_NEW_AUDIT_BTN_CSS = (
      By.CSS_SELECTOR, _GET_LIST + ' [data-object-singular="Audit"]')
  START_NEW_WORKFLOW_BTN_CSS = (
      By.CSS_SELECTOR, _GET_LIST + ' [data-object-singular="Workflow"]')
  CREATE_TASK_BTN_CSS = (
      By.CSS_SELECTOR, _GET_LIST +
      ' [data-object-singular="CycleTaskGroupObjectTask"]')
  CREATE_OBJECT_BTN_CSS = (By.CSS_SELECTOR, _GET_LIST + ' [href="#"]')
  ALL_OBJECTS_BTN_CSS = (
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


class ExportPage(object):
  """Locators for Export Page and Export Panels."""
  _CONTENT = Common.CONTENT
  _EXPORT_PAGE = _CONTENT + " #csv_export"
  _EXPORT_PANEL = ".new-relevant-block"
  # general
  EXPORT_PAGE_CSS = (By.CSS_SELECTOR, _EXPORT_PAGE)
  EXPORT_PANEL_CSS = (By.CSS_SELECTOR, ".choose-object-wrap " + _EXPORT_PANEL)
  EXPORT_ACTIONS_PANEL_CSS = (By.CSS_SELECTOR, ".export-group__actions-wrap")
  # labels
  TITLE_LBL_CSS = (By.CSS_SELECTOR, Common.TITLE)
  # user input elements
  EXPORT_FORMAT_DD_CSS = (
      By.CSS_SELECTOR, ".export-format")
  ADD_OBJECT_TYPE_BTN_CSS = (
      By.CSS_SELECTOR, "#addAnotherObjectType")
  EXPORT_OBJECTS_BTN_CSS = (By.CSS_SELECTOR, "#export-csv-button")


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
  # pylint: disable=invalid-name
  MODAL = Common.MODAL_MAPPER
  MODAL_CSS = (By.CSS_SELECTOR, MODAL)
  MODAL_FILTER = Common.MODAL_FILTER
  FILTER_TOGGLE_CSS = (By.CSS_SELECTOR,
                       MODAL_FILTER + " collapse-panel-click-area")
  FILTER_ADD_ATTRIBUTE_BTN = (By.XPATH, "//button[text()='Add Attribute']")
  FILTER_ROW_CSS = (By.CSS_SELECTOR, ".filter-container__attribute")
  FILTER_OPERATOR = (By.CSS_SELECTOR, ".filter-operator__content select")
  FILTER_ATTRIBUTE_NAME = (By.CSS_SELECTOR, ".filter-attribute__name select")
  FILTER_ATTRIBUTE_COMPARE = (
      By.CSS_SELECTOR, ".filter-attribute__operator select")
  FILTER_ATTRIBUTE_VALUE = (By.CSS_SELECTOR, ".filter-attribute__value input")
  MODAL_TITLE = (By.CSS_SELECTOR, MODAL + " h2")
  OBJ_TYPE = (By.CSS_SELECTOR, MODAL + " .object-controls__type h6")
  # user input elements
  OBJ_TYPE_DROPDOWN = (By.CSS_SELECTOR, MODAL + " .input-block-level")
  BUTTON_SEARCH = (By.CSS_SELECTOR, MODAL + " button[type='submit']")
  FOUND_OBJECTS_TITLES = (By.CSS_SELECTOR, MODAL + " .flex-box .title-attr")
  FOUND_OBJECTS_CHECKBOXES = (By.CSS_SELECTOR,
                              MODAL + ' .flex-box [type="checkbox"]')
  BUTTON_MAP_SELECTED = (By.CSS_SELECTOR, MODAL + Common.MODAL_FOOTER +
                         " .btn-map")
  RESULT_TOGGLE_CSS = (By.CSS_SELECTOR, MODAL + Common.MODAL_FOOTER +
                       " collapse-panel-click-area")
  CLOSE_BTN_CSS = (By.CSS_SELECTOR,
                   MODAL + Common.MODAL_HEADER + " a.modal-dismiss")


class ModalMapObjects(CommonModalUnifiedMapper):
  """Locators for map objects modals."""
  MODAL = Common.MODAL_MAPPER
  # user input elements
  BUTTON_CREATE_OBJ = (By.CSS_SELECTOR, MODAL + " .create-control")


class ModalSearchObjects(CommonModalUnifiedMapper):
  """Locators for search objects modals."""
  MODAL = Common.MODAL_MAPPER


class ModalGenerateAssessments(CommonModalUnifiedMapper):
  """Locators for generate Assessments modal."""
  MODAL = Common.MODAL_MAPPER


class BaseModalCreateNew(object):
  """Locators for Create new object modals."""
  MODAL = Common.MODAL_CREATE
  MODAL_CSS = (By.CSS_SELECTOR, MODAL)
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
  REF_URL_CSS = (By.CSS_SELECTOR, '[data-id="reference_url_hidden"]')
  UI_EFFECTIVE_DATE = (By.CSS_SELECTOR,
                       '[test-id="new_program_field_effective_date_f2783a28"] '
                       '[data-id="effective_date_hidden"] .datepicker__input')
  EFFECTIVE_DATE_DATEPICKER = (
      By.CSS_SELECTOR,
      '[test-id="new_program_field_effective_date_f2783a28"] '
      '[data-id="effective_date_hidden"] [data-handler="selectDay"]')
  TITLE = (By.CSS_SELECTOR, '[data-test-id="label_title_2c925d94"]')
  DESCRIPTION = (
      By.CSS_SELECTOR, '[data-test-id="label_description_2c925d94"]')
  PRIVACY = (By.CSS_SELECTOR, '[data-test-id="label_privacy_2c925d94"]')


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
    def get_assignee_row(first_id, second_id):
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
  ADMIN = (
      By.CSS_SELECTOR, '[data-test-id="control_owner_587d12d6"] label')
  BUTTON_ADD_OWNER = (By.CSS_SELECTOR, 'isolate-form .btn')
  REF_URL_CSS = (By.CSS_SELECTOR, '[data-id="reference_url_hidden"]')
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
  BUTTON_HIDE_ALL_OPTIONAL_FIELDS = (By.CSS_SELECTOR, '#formHide')


class ModalCreateNewObjective(BaseModalCreateNew):
  """Locators for Create new Objective modals."""


class ModalCreateNewIssue(BaseModalCreateNew):
  """Locators for Create new Issue modals."""


class ModalCreateNewAsmt(BaseModalCreateNew, CommonAssessment):
  """Locators for Create new Assessment modals."""
  MAPPED_SNAPSHOTS_CSS = (By.CSS_SELECTOR, BaseModalCreateNew.MODAL +
                          CommonAssessment.MAPPED_SNAPSHOTS)
  MAP_OBJS_BTN_CSS = (By.CSS_SELECTOR,
                      BaseModalCreateNew.MODAL + CommonAssessment.MAP_OBJS_BTN)


class ModalCreateNewAsmtTmpl(BaseModalCreateNew):
  """Locators for Create new Assessment Template modals."""
  ASSIGNEE_DROPDOWN = (
      By.CSS_SELECTOR, 'select[can-value="instance.default_people.assignees"]')


class ModalEditObject(BaseModalCreateNew):
  """Locators for Edit object modals."""
  BUTTON_DELETE = (
      By.CSS_SELECTOR, '.deny-buttons [data-toggle="modal-ajax-deleteform"]')


class ModalCustomAttribute(object):
  """Locators for generic custom attributes modal in Admin Dashboard."""
  MODAL_CSS = (By.CSS_SELECTOR, Common.MODAL_CONFIRM)
  MODAL_TITLE_LBL_CSS = (By.CSS_SELECTOR, Common.MODAL_HEADER + " h2")
  ATTR_TITLE_UI_CSS = (By.CSS_SELECTOR, Common.MODAL_BODY + ' [name="title"]')
  SAVE_AND_CLOSE_BTN_CSS = (
      By.CSS_SELECTOR,
      Common.MODAL_FOOTER + ' .confirm-buttons [data-toggle="modal-submit"]')
  ATTR_TITLE_LBL_CSS = (
      By.CSS_SELECTOR, Common.MODAL_BODY + " div:nth-child(1)>label")
  ATTR_TYPE_CSS = (By.CSS_SELECTOR, Common.MODAL_HEADER + " h2")
  ATTR_TYPE_SELECTOR_DD_CSS = (
      By.CSS_SELECTOR, Common.MODAL_BODY + " dropdown select")
  MANDATORY_LBL_CSS = (By.CSS_SELECTOR, Common.MODAL_BODY + " .span2 label")
  MANDATORY_CB_CSS = (
      By.CSS_SELECTOR, Common.MODAL_BODY + ' [type="checkbox"]')
  INLINE_HELP_LBL_CSS = (
      By.CSS_SELECTOR, Common.MODAL_BODY + " div:nth-child(2)>label")
  INLINE_HELP_UI_CSS = (
      By.CSS_SELECTOR, Common.MODAL_BODY + ' [name="helptext"]')
  PLACEHOLDER_LBL_CSS = (By.CSS_SELECTOR, Common.MODAL_BODY + " .span6 label")
  PLACEHOLDER_UI_CSS = (
      By.CSS_SELECTOR, Common.MODAL_BODY + ' [name="placeholder"]')
  POSSIBLE_VALUES_UI_CSS = (
      By.CSS_SELECTOR, Common.MODAL_BODY + ' [name="multi_choice_options"]')
  ADD_ANOTHER_BTN_CSS = (
      By.CSS_SELECTOR,
      Common.MODAL_FOOTER +
      ' .confirm-buttons [data-toggle="modal-submit-addmore"]')


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
  MODAL = ".modal"
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
      return (By.CSS_SELECTOR,
              '.object-nav [href$="#!{}_widget"]'.format(object_name))

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
  ADMIN_CUSTOM_ROLES = _Locator.get_widget("custom_roles")
  INFO = _Locator.get_widget("info")
  CUSTOM_ATTRIBUTES = _Locator.get_widget("custom_attribute")
  EVENTS = _Locator.get_widget("events_list")
  ROLES = _Locator.get_widget("roles_list")
  RISK_ASSESSMENTS = _Locator.get_widget("risk_assessment")
  TASKS = _Locator.get_widget("task")
  DASHBOARD_TAB = _Locator.get_widget("dashboard")


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
  ALL_MAPPABLE_WIDGETS_OBJS = (
      By.CSS_SELECTOR, ".inner-nav-item a[data-toggle='unified-mapper']")


class ObjectWidget(object):
  """Locators for Generic objects widget."""
  _HEADER = '.header [class^="span"]'
  _STATE = 'div.state-value'
  HEADER_TITLE = (By.CSS_SELECTOR, _HEADER + ' [data-field="title"]')
  HEADER_OWNER = (
      By.CSS_SELECTOR, _HEADER + ' [data-field="owners"]')
  HEADER_STATE = (By.CSS_SELECTOR, _STATE)
  HEADER_STATE_IN_PROGRESS = (By.CSS_SELECTOR, _STATE + '.state-inprogress')
  HEADER_STATE_COMPLETED = (By.CSS_SELECTOR, _STATE + '.state-completed')
  HEADER_STATE_READY_FOR_REVIEW = (
      By.CSS_SELECTOR, _STATE + '.state-readyforreview')
  HEADER_STATE_VERIFIED = (By.CSS_SELECTOR, _STATE + '.state-verified')

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


class ModalCloneAudit(ModalCommonConfirmAction):
  """Locators for Clone object modals."""
  MODAL = Common.MODAL_CONFIRM
  CHECKBOX_CLONE_ASMT_TMPLS = (
      By.CSS_SELECTOR,
      '{} [can-value="instance.includeObjects.AssessmentTemplate"]'
        .format(MODAL))


class CommonWidgetInfo(object):
  """Common locators for Info widgets and Info panels."""
  _NOT_HIDDEN = Common.XPATH_NOT_HIDDEN
  _INFO_WIDGET_XPATH = Common.INFO_WIDGET_XPATH
  _MAIN_HEADER_XPATH = "//div[contains(@class,'pane-header')]" + _NOT_HIDDEN
  _HEADERS_AND_VALUES = (_INFO_WIDGET_XPATH +
                         '//div[starts-with(./@class, "span")]//h6/..')
  WIDGET = Common.INFO
  _FOOTER = Common.INFO_WIDGET_ID + " .info-widget-footer em"
  INFO_PANEL_ELEM = (By.XPATH, Common.INFO_WIDGET_XPATH)
  INFO_PAGE_ELEM = (By.XPATH, Common.INFO_PAGE_XPATH)
  HEADERS_AND_VALUES = (By.XPATH, _HEADERS_AND_VALUES)
  LCAS_HEADERS_AND_VALUES = None  # due to exist only for WidgetInfoAssessment
  CAS_HEADERS_AND_VALUES = (By.XPATH,
                            _INFO_WIDGET_XPATH + "//inline-edit-control/div")
  CAS_CHECKBOXES = (By.XPATH, _INFO_WIDGET_XPATH +
                    "//inline-edit-control//input[""@type='checkbox']")
  # labels
  TITLE = (By.XPATH, _MAIN_HEADER_XPATH + "//h6")
  TITLE_ENTERED = (By.XPATH, _MAIN_HEADER_XPATH + "//h3")
  STATE = (By.XPATH, _MAIN_HEADER_XPATH +
           "//*[contains(normalize-space(./@class), 'state-value state')]")
  TXT_FOOTER_CSS = (By.CSS_SELECTOR, _FOOTER)
  TXT_MODIFIED_BY_CSS = (By.CSS_SELECTOR,
                         _FOOTER + ' [data-test-id="text_manager_7a906d2e"]')
  TXT_OBJECT_REVIEW = (
      By.CSS_SELECTOR,
      '{} [data-test-id="title_review_0ad9fbaf"] h6'.format(WIDGET))
  TXT_OBJECT_REVIEWED = (
      By.CSS_SELECTOR, "{} .object-approved".format(WIDGET))
  LINK_SUBMIT_FOR_REVIEW = (By.CSS_SELECTOR,
                            "{} .non-transparent".format(WIDGET))
  # people section
  _PEOPLE_ITEM = ".editable-people-group"
  PEOPLE_HEADERS_AND_VALUES_CSS = (By.CSS_SELECTOR, _PEOPLE_ITEM)
  PEOPLE_HEADER_CSS = (
      By.CSS_SELECTOR, _PEOPLE_ITEM + " editable-people-group-header")
  PEOPLE_VALUE_CSS = (By.CSS_SELECTOR, _PEOPLE_ITEM + " object-list")
  # user input elements
  BUTTON_3BBS = (By.XPATH, _INFO_WIDGET_XPATH + "//*[@data-toggle='dropdown']")
  # controllers
  TAB_CONTAINER_CSS = (By.CSS_SELECTOR, "tab-container")


class WidgetInfoPanel(CommonWidgetInfo):
  """Locators specific for Info panels."""
  _PIN_ACTION = ' .pin-action'
  # user input elements
  BUTTON_MAXIMIZE_MINIMIZE = (By.CSS_SELECTOR,
                              _PIN_ACTION + ' [can-click="toggleSize"]')
  BUTTON_CLOSE = (By.CSS_SELECTOR,
                  _PIN_ACTION + ' [can-click="close"]')
  # People section
  PEOPLE_HEADERS_AND_VALUES = (By.CSS_SELECTOR, ".editable-people-group")


class WidgetSnapshotsInfoPanel(WidgetInfoPanel):
  """Locators specific for Info panels of snapshotable objects."""
  LINK_GET_LAST_VER = (By.CSS_SELECTOR, ".snapshot [can-click='compareIt']")
  SNAPSHOT_OBJ_VER = (By.CSS_SELECTOR, "span.snapshot")


class WidgetInfoProgram(WidgetInfoPanel):
  """Locators for Program Info widgets."""
  # pylint: disable=too-many-format-args
  WIDGET = Common.INFO
  TOGGLE_SHOW_ADVANCED = (
      By.CSS_SELECTOR, "{} .show-hidden-fields".format(WIDGET))
  TOGGLE_SHOW_ADVANCED_ACTIVATED = (
      By.CSS_SELECTOR, "{} .show-hidden-fields.active".format(WIDGET))
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
  REF_URL_CSS = (
      By.CSS_SELECTOR,
      '{} [data-test-id="title_reference_url_aa7d1a65"]'.format(WIDGET))
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
  PRIVATE_PROGRAM = (By.CSS_SELECTOR,
                     '[data-test-id="title_private_ec758af9"] h6')
  ICON_LOCK = (By.CSS_SELECTOR, '[data-test-id="icon_private_ec758af9"]')
  ALERT_LINK_COPIED = (By.CSS_SELECTOR, ".alert.alert-success")
  MODAL_DELETE = (By.ID, '[id="ajax-lhn_modal-javascript:--"]')
  MODAL_DELETE_CLOSE = (By.CSS_SELECTOR, ".lhn_modal .grcicon-x-grey")


class WidgetInfoRisk(WidgetSnapshotsInfoPanel):
  """Locators for Risk Info widgets."""


class WidgetInfoOrgGroup(WidgetSnapshotsInfoPanel):
  """Locators for Org Group Info widgets."""


class WidgetInfoIssue(WidgetInfoPanel):
  """Locators for Issue Info widgets."""


class WidgetInfoRegulations(WidgetSnapshotsInfoPanel):
  """Locators for Regulation Info widgets."""


class WidgetInfoWorkflow(WidgetInfoPanel):
  """Locators for Workflow Info widgets."""


class WidgetInfoAudit(WidgetInfoPanel):
  """Locators for Audit Info widgets."""


class WidgetInfoAssessment(WidgetInfoPanel, CommonAssessment):
  """Locators for Assessment Info widgets."""
  # pylint: disable=invalid-name
  WIDGET = Common.INFO
  TOGGLE = ' [class*="fa-caret"]'
  # Base
  LCAS_HEADERS_AND_VALUES = (
      By.CSS_SELECTOR,
      WIDGET + " .field-wrapper.flex-size-1")
  CAS_HEADERS_AND_VALUES = (
      By.CSS_SELECTOR,
      WIDGET + " assessment-custom-attributes inline-edit-control")
  CAS_CHECKBOXES = (By.CSS_SELECTOR, '[class*="wrapper"] [type="checkbox"]')
  # Assessment Attributes tab
  # Code section
  _CODE = "assessment-inline-item[prop-name='slug'] "
  CODE_CSS = (By.CSS_SELECTOR, _CODE)
  CODE_HEADER_CSS = (By.CSS_SELECTOR, _CODE + ".ggrc-form__title")
  CODE_VALUE_CSS = (By.CSS_SELECTOR, _CODE + ".read-more__body")
  # comments section
  COMMENTS_CSS = (By.CSS_SELECTOR, ".assessment-comments")
  # asmt tab container
  ASMT_CONTROLLER_SECTION_CSS = (By.CSS_SELECTOR, "assessment-controls")
  _ASMT_PANEL = ".tab-pane"
  ASMT_LOG_PANEL_CSS = (By.CSS_SELECTOR,
                        " ".join([_ASMT_PANEL, "ul.entry-list"]))
  RELATED_ASMTS_CSS = (By.CSS_SELECTOR, " ".join(
      [_ASMT_PANEL, "related-objects[related-items-type='Assessment']"]))
  RELATED_ISSUES_CSS = (By.CSS_SELECTOR, " ".join(
      [_ASMT_PANEL, "related-objects[related-items-type='Issue']"]))
  # state section
  _PNL_STATE = ".pane-header__toolbar"
  BUTTON_COMPLETE = (By.CSS_SELECTOR, _PNL_STATE + " button.btn-darkBlue")
  BUTTON_VERIFY = (By.CSS_SELECTOR, _PNL_STATE + " button.btn-green")
  BUTTON_NEEDS_REWORK = (By.CSS_SELECTOR, _PNL_STATE + " button.btn-red")
  ICON_VERIFIED = (By.CSS_SELECTOR, "i.verified-icon")


class TabContainer(object):
  TAB_CONTROLLER_CSS = (By.CSS_SELECTOR, "ul.nav.nav-tabs")
  TAB_CONTENT_CSS = (By.CSS_SELECTOR, '.tab-pane.active')


class WidgetInfoAssessmentTemplate(WidgetInfoPanel):
  """Locators for assessment template info widget."""


class WidgetInfoPolicy(WidgetSnapshotsInfoPanel):
  """Locators for Policy Info widgets."""


class WidgetInfoStandard(WidgetSnapshotsInfoPanel):
  """Locators for Standard Info widgets."""


class WidgetInfoContract(WidgetSnapshotsInfoPanel):
  """Locators for Contract Info widgets."""


class WidgetInfoClause(WidgetSnapshotsInfoPanel):
  """Locators for Clause Info widgets."""


class WidgetInfoSection(WidgetSnapshotsInfoPanel):
  """Locators for Section Info widgets."""


class WidgetInfoControl(WidgetSnapshotsInfoPanel):
  """Locators for Control Info widgets."""


class WidgetInfoObjective(WidgetSnapshotsInfoPanel):
  """Locators for Objective Info widgets."""


class WidgetInfoPeople(CommonWidgetInfo):
  """Locators for People Info widgets."""


class WidgetInfoVendor(WidgetSnapshotsInfoPanel):
  """Locators for Vendor Info widgets."""


class WidgetInfoAccessGroup(WidgetSnapshotsInfoPanel):
  """Locators for Access Group Info widgets."""


class WidgetInfoSystem(WidgetSnapshotsInfoPanel):
  """Locators for System Info widgets."""


class WidgetInfoProcess(WidgetSnapshotsInfoPanel):
  """Locators for Process Info widgets."""


class WidgetInfoProduct(WidgetSnapshotsInfoPanel):
  """Locators for Product Info widgets."""


class WidgetInfoFacility(WidgetSnapshotsInfoPanel):
  """Locators for Facility Info widgets."""


class WidgetInfoProject(WidgetSnapshotsInfoPanel):
  """Locators for Project Info widgets."""


class WidgetInfoMarket(WidgetSnapshotsInfoPanel):
  """Locators for Market Info widgets."""


class WidgetInfoDataAsset(WidgetSnapshotsInfoPanel):
  """Locators for Data Asset Info widgets."""


class WidgetInfoThreat(WidgetSnapshotsInfoPanel):
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


class CommonDropdownMenu(object):
  """Locators for common drop down elements."""
  _DROPDOWN_MAIN = 'ul'
  _DROPDOWN_ITEMS = 'li'
  _DROPDOWN_ITEM_ICON = 'i'
  DROPDOWN_MAIN_CSS = (By.CSS_SELECTOR, _DROPDOWN_MAIN)
  DROPDOWN_ITEMS_CSS = (By.CSS_SELECTOR, _DROPDOWN_ITEMS)
  DROPDOWN_ITEM_ICON_CSS = (By.CSS_SELECTOR, _DROPDOWN_ITEM_ICON)
  DROPDOWN_OPTIONS = (By.CSS_SELECTOR, Common.OPTION)


class CommonDropdown3bbsInfoWidget(CommonDropdownMenu):
  """Locators for common settings 3BBS dropdown on Info widget and Info page.
 """
  _INFO_3BBS_DROPDOWN_BUTTON_XPATH = (
      Common.INFO_WIDGET_XPATH + "//*[contains(@class,'dropdown-menu')]")
  _INFO_3BBS_DROPDOWN_XPATH = (
      Common.INFO_WIDGET_XPATH +
      "//ul[contains(@class,'dropdown-menu three-dots-list')]")
  INFO_WDG_3BBS_DD_BTN_XPATH = (By.XPATH, _INFO_3BBS_DROPDOWN_BUTTON_XPATH)
  INFO_WDG_3BBS_DD_XPTAH = (By.XPATH, _INFO_3BBS_DROPDOWN_XPATH)


class AuditsDropdown3bbsInfoWidget(CommonDropdown3bbsInfoWidget):
  """Locators for Audit settings 3BBS dropdown on Info page and Info panel.
  """


class CommonDropdown3bbsTreeView(CommonDropdownMenu):
  """Locators for common settings 3BBS dropdown on Tree View."""
  TREE_VIEW_3BBS_DD = (
      Common.WDG_NOT_HIDDEN + Common.TREE_LIST + " .tree-action-list-items")
  # user input elements
  TREE_VIEW_3BBS_DD_CSS = (By.CSS_SELECTOR, TREE_VIEW_3BBS_DD)
  BTN_3BBS_IMPORT_CSS = (By.CSS_SELECTOR,
                         TREE_VIEW_3BBS_DD + " .fa-cloud-upload")
  BTN_3BBS_EXPORT_CSS = (By.CSS_SELECTOR, TREE_VIEW_3BBS_DD + " .fa-download")
  BTN_3BBS_SELECT_CHILD_TREE_CSS = (By.CSS_SELECTOR,
                                    TREE_VIEW_3BBS_DD + " .fa-share-alt")


class AssessmentsDropdown3bbsTreeView(CommonDropdown3bbsTreeView):
  """Locators for Assessments settings 3BBS dropdown on Tree View."""
  BTN_3BBS_GENERATE_CSS = (
      By.CSS_SELECTOR,
      CommonDropdown3bbsTreeView.TREE_VIEW_3BBS_DD + " .fa-magic")


class TreeView(object):
  """Locators for Tree View components."""
  # common
  TREE_VIEW_CONTAINER_CSS = (
      By.CSS_SELECTOR, Common.WDG_NOT_HIDDEN + " tree-widget-container>div")
  ITEMS = Common.WDG_NOT_HIDDEN + " .tree-item-element"
  HEADER = Common.WDG_NOT_HIDDEN + Common.TREE_HEADER
  ITEM_LOADING_CSS = (By.CSS_SELECTOR, " .tree-item-placeholder")
  ITEM_EXPAND_BTN = " tree-item-actions"
  ITEM_DD_MENU_CSS = Common.HTML_LIST_CSS
  TREE_SPINNER_CSS = (By.CSS_SELECTOR, Common.TREE_SPINER)
  NO_RESULTS_MSG_CSS = (
      By.CSS_SELECTOR, Common.WDG_NOT_HIDDEN + " .tree-no-results-message")
  SHOW_FIELDS_BTN_CSS = (
      By.CSS_SELECTOR,
      Common.WDG_NOT_HIDDEN + Common.TREE_HEADER + " .fa-bars")
  # user input elements
  BTN_3BBS_CSS = (By.CSS_SELECTOR,
                  Common.WDG_NOT_HIDDEN + Common.TREE_LIST + " .details-wrap")
  CREATE_BTN_CSS = (
      By.CSS_SELECTOR,
      Common.WDG_NOT_HIDDEN + Common.TREE_LIST + " .create-button")
  MAP_BTN_CSS = (By.CSS_SELECTOR,
                 Common.WDG_NOT_HIDDEN + Common.TREE_LIST + " .map-button")
  ITEM_DD_BTN_CSS = (
      By.CSS_SELECTOR, Common.WDG_NOT_HIDDEN + ITEM_EXPAND_BTN)


class TreeViewItem(object):
  """Locators for Tree View Item element"""
  CELL = (By.CSS_SELECTOR,
          "div[class*='attr']:not(.attr-content):not(.selectable-attrs)")


class AdminTreeView(object):
  """Locators for Tree View components in Admin dashboard."""
  # common
  ITEMS = "li.tree-item .item-main"
  ITEM_LOADING_CSS = (By.CSS_SELECTOR, " .tree-item-placeholder")
  ITEM_EXPAND_BTN = " .openclose"
  TREE_SPINNER_CSS = (By.CSS_SELECTOR, Common.TREE_SPINER)
  NO_RESULTS_MSG_CSS = (By.CSS_SELECTOR, ".tree-no-results-message")
  SHOW_FIELDS_BTN_CSS = (
      By.CSS_SELECTOR,
      Common.WDG_NOT_HIDDEN + Common.TREE_HEADER + " .fa-bars")
  # user input elements
  BTN_3BBS_CSS = (By.CSS_SELECTOR,
                  Common.WDG_NOT_HIDDEN + Common.TREE_LIST + " .btn-draft")
  CREATE_BTN_CSS = (
      By.CSS_SELECTOR,
      Common.WDG_NOT_HIDDEN + Common.TREE_LIST + " .create-button")
  MAP_BTN_CSS = (By.CSS_SELECTOR,
                 Common.WDG_NOT_HIDDEN + Common.TREE_LIST + " .map-button")


class UnifiedMapperTreeView(TreeView):
  """Common locators for UnifiedMapper from Tree View"""
  MODAL = ".object-modal"
  HEADER = MODAL + " .list-header"
  ITEMS = MODAL + Common.TREE_ITEM
  SHOW_FIELDS_BTN_CSS = (By.CSS_SELECTOR, HEADER + " .fa-bars")
  NO_RESULTS_MSG_CSS = (By.CSS_SELECTOR, ".well-small:not(.hidden)")


class BaseWidgetGeneric(object):
  """Locators for non Info and Admin widgets."""
  # pylint: disable=invalid-name
  _FILTER_BTN = (
      Common.WDG_NOT_HIDDEN + "tree-filter-input .tree-filter__actions")
  _FILTER_DD = Common.WDG_NOT_HIDDEN + "tree-status-filter"
  _FILTER_DD_ELEMENTS = (_FILTER_DD + " .multiselect-dropdown__element")
  TXTFIELD_TO_FILTER_CSS = (By.CSS_SELECTOR,
                            Common.WDG_NOT_HIDDEN + ".tree-filter__input")
  FILTER_BTN_CSS = (By.CSS_SELECTOR, _FILTER_BTN + ' [type="submit"]')
  HELP_BTN_CSS = (By.CSS_SELECTOR, _FILTER_BTN + " #page-help")
  DD_CSS = (By.CSS_SELECTOR,
            _FILTER_DD + " .multiselect-dropdown__input-container")
  DD_STATES_CSS = (By.CSS_SELECTOR, _FILTER_DD_ELEMENTS)
  PAGINATION_CONTROLLERS_CSS = (
      By.CSS_SELECTOR, Common.WDG_NOT_HIDDEN + ".tree-pagination.flex-box")


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
  _TREE_ITEM = ".tree-item.cms_controllers_tree_view_node"
  TREE_ITEM_EL_OPENED_CSS = (By.CSS_SELECTOR, _TREE_ITEM + ".item-open")
  CONTENT_OPEN = ".content-open .tier-2-info-content"
  TREE_STRUCTURE = (
      CONTENT_OPEN + " .tree-structure .cms_controllers_tree_view_node")
  TITLES_ROW_CSS = (By.CSS_SELECTOR, CONTENT_OPEN + " thead tr")
  ROW_CSS = (By.CSS_SELECTOR, TREE_STRUCTURE)
  CELL_IN_ROW_CSS = (By.CSS_SELECTOR, "td")
  EDIT_BTN_CSS = (By.CSS_SELECTOR, CONTENT_OPEN + Common.TREE_LIST)
  ADD_BTN_CSS = (By.CSS_SELECTOR, CONTENT_OPEN + " .add-item .btn")
  TREE_SPINNER_CSS = (By.CSS_SELECTOR, Common.TREE_SPINER)


class MultiInputField(object):
  """Locators for multi input field."""
  _form = ".create-form__layout"
  ADD_BTN_CSS = (By.CSS_SELECTOR, ".btn")
  TXT_CSS = (By.CSS_SELECTOR, _form + " input")
  APPLY_BTN_CSS = (By.CSS_SELECTOR, _form + " [type='submit']")
  CANCEL_BTN_CSS = (By.CSS_SELECTOR, _form + " [type='button']")
  ITEMS = (By.CSS_SELECTOR, ".document-object-item")


class MultiInputItem(object):
  """Locators for single item in multi input field."""
  LINK_CSS = (By.CSS_SELECTOR, "a")
  DATE = (By.CSS_SELECTOR, "data")


class CommentsPanel(object):
  """Locators for comments' panel."""
  HEADER_LBL_CSS = (By.CSS_SELECTOR, ".info-pane__section-title")
  INPUT_TXT_CSS = (By.CSS_SELECTOR, ".ql-editor")
  CB_SEND_CSS = (By.CSS_SELECTOR, ".comment-add-form__toolbar-item")
  ADD_BTN_CSS = (By.CSS_SELECTOR, "comment-add-button")
  ITEMS_CSS = (By.CSS_SELECTOR, "comment-list-item")


class CommentItem(object):
  """Locators for single item in comments' panel."""
  AUTHOR_CSS = (By.CSS_SELECTOR, ".person-holder")
  DATETIME_CSS = (By.CSS_SELECTOR, ".comment-object-item__header-author-info")
  CONTENT_CSS = (By.CSS_SELECTOR, ".comment-object-item__text")


class AssessmentLogTab(object):
  """Locators for Log Tab elements on Assessment InfoWidget."""
  CELLS_CSS = (By.CSS_SELECTOR, '.third-col')
  COMMENT_PERSON_CSS = (By.CSS_SELECTOR, '.person-tooltip-trigger')
  PERSON_LABEL = (By.CSS_SELECTOR, '.person-label')
  LOG_LIST_CSS = (By.CSS_SELECTOR, ' .w-status')


class AssessmentRelatedTable(object):
  """Locators for RelatedAssessments Tab elements on Assessment InfoWidget."""
  HEADERS = (By.CSS_SELECTOR, ".grid-data-header")
  ROWS = (By.CSS_SELECTOR, ".grid-data-row")
  CELLS = (By.CSS_SELECTOR, "div")
  TAB_BUTTON = (By.CSS_SELECTOR, ".btn.btn-small")


class DashboardWidget(object):
  """Locators for DashboardWidget."""
  _TAB_CONTAINER = ".dashboard-widget.info"
  TAB_CONTAINER_CSS = (By.CSS_SELECTOR, _TAB_CONTAINER)
  TAB_CONTROLLER_CSS = (By.CSS_SELECTOR, ".dashboard-list")
  TAB_CONTENT_CSS = (By.CSS_SELECTOR, _TAB_CONTAINER + " iframe")
