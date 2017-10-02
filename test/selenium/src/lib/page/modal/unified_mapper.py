# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Modals for map objects."""

from lib import base, decorator
from lib.constants import element, locator, value_aliases as alias
from lib.utils import selenium_utils


class CommonUnifiedMapperModal(base.Modal):
  """Common unified mapper modal."""
  _locators = locator.ModalMapObjects
  _elements = element.UnifiedMapperModal

  def __init__(self, driver, obj_name):
    super(CommonUnifiedMapperModal, self).__init__(driver)
    # labels
    self.filter_toggle = base.Toggle(
        self._driver, self._locators.FILTER_TOGGLE_CSS)
    self.filter_toggle.is_activated = True
    self.title_modal = base.Label(self._driver, self._locators.MODAL_TITLE)
    self.obj_type = base.Label(self._driver, self._locators.OBJ_TYPE)
    # user input elements
    self.tree_view = base.UnifiedMapperTreeView(
        self._driver, obj_name=obj_name)
    self._add_attr_btn = None
    self.search_result_toggle = base.Toggle(
        self._driver, self._locators.RESULT_TOGGLE_CSS)
    self.close_btn = base.Button(self._driver, self._locators.CLOSE_BTN_CSS)

  def get_available_to_map_obj_aliases(self):
    """Return texts of all objects available to map via UnifiedMapper."""
    # pylint: disable=invalid-name
    return [opt.get_attribute("label")
            for opt in self.obj_type_dropdown.find_options()]

  @decorator.lazy_property
  def obj_type_dropdown(self):
    return base.DropdownStatic(self._driver, self._locators.OBJ_TYPE_DROPDOWN)

  def _select_dest_obj_type(self, obj_name, is_asmts_generation=False):
    """Open dropdown and select element according to destination object name.
    If is_asmts_generation then TextFilterDropdown, else DropdownStatic.
    """
    if obj_name:
      obj_type_dropdown = base.DropdownStatic(
          self._driver, self._locators.OBJ_TYPE_DROPDOWN)
      obj_type_dropdown.select(obj_name)
      if is_asmts_generation:
        asmt_tmpl_dropdown = base.DropdownStatic(
            self._driver, self._locators.OBJ_TYPE_DROPDOWN,)
        asmt_tmpl_dropdown.select_by_label(obj_name)

  def add_filter_attr(self, attr_name, value,
                      operator=None, compare_op=alias.EQUAL_OP):
    """Add filter attribute according to passed parameters. """
    if not self._add_attr_btn:
      self._add_attr_btn = selenium_utils.get_when_visible(
          self._driver, self._locators.FILTER_ADD_ATTRIBUTE_BTN)
    self._add_attr_btn.click()
    last_filter_param = self._get_latest_filter_elements()
    last_filter_param['name'].select(attr_name)
    last_filter_param['value'].enter_text(value)
    last_filter_param["compare_op"].select(compare_op)
    if last_filter_param["operator"] and operator:
      last_filter_param["operator"].select(operator)

  def _get_latest_filter_elements(self):
    """Return elements of last filter parameter"""
    latest_filter_elem = self._driver.find_elements(
        *self._locators.FILTER_ROW_CSS)
    latest_filter = {
        "name": base.DropdownStatic(
            latest_filter_elem[-1], self._locators.FILTER_ATTRIBUTE_NAME),
        "compare_op": base.DropdownStatic(
            latest_filter_elem[-1], self._locators.FILTER_ATTRIBUTE_COMPARE),
        "value": base.TextInputField(
            latest_filter_elem[-1], self._locators.FILTER_ATTRIBUTE_VALUE),
        "operator": None}
    if len(latest_filter_elem) > 1:
      latest_filter["operator"] = base.DropdownStatic(
          self._driver, selenium_utils.get_when_all_visible(
              self._driver, self._locators.FILTER_OPERATOR)[-1])
    return latest_filter

  def _select_search_dest_objs(self):
    """Click Search button to search objects according set filters."""
    base.Button(self._driver, self._locators.BUTTON_SEARCH).click()
    selenium_utils.wait_for_js_to_load(self._driver)

  def _select_dest_objs_to_map(self, objs_titles):
    """Select checkboxes regarding to titles from list of checkboxes
    according to destinations objects titles.
    """
    dest_objs = base.ListCheckboxes(
        self._driver, self._locators.FOUND_OBJECTS_TITLES,
        self._locators.FOUND_OBJECTS_CHECKBOXES)
    dest_objs.select_by_titles(objs_titles)

  def get_mapping_statuses(self):
    """Get mapping status from checkboxes on Unified Mapper
       (selected and disabled or not).
    """
    dest_objs = base.ListCheckboxes(
        self._driver, self._locators.FOUND_OBJECTS_TITLES,
        self._locators.FOUND_OBJECTS_CHECKBOXES)
    return (
        dest_objs.get_mapping_statuses() if
        self.tree_view.tree_view_items() else [])

  def _confirm_map_selected(self):
    """Select Map Selected button to confirm map selected objects to
    source object.
    """
    base.Button(self._driver, self._locators.BUTTON_MAP_SELECTED).click()
    selenium_utils.get_when_invisible(
        self._driver, self._locators.BUTTON_MAP_SELECTED)

  def _confirm_items_added(self):
    """Wait until items shown on Tree View"""
    selenium_utils.get_when_invisible(
        self._driver, locator.TreeView.NO_RESULTS_MESSAGE)

  def search_dest_objs(self, dest_objs_type, dest_objs_titles,
                       is_asmts_generation=False):
    """Filter and search destination objects according to them type and titles.
    If is_asmts_generation then TextFilterDropdown is using.
    """
    if not self.filter_toggle.is_activated:
      self.filter_toggle.toggle()
    self._select_dest_obj_type(obj_name=dest_objs_type,
                               is_asmts_generation=is_asmts_generation)
    for enum, title in enumerate(dest_objs_titles):
      if enum == 0:
        operator = None
      else:
        operator = alias.OR_OP
      self.add_filter_attr(self._elements.ATTRIBUTE_TITLE, title,
                           operator=operator)
    self._select_search_dest_objs()
    return self.tree_view.get_list_members_as_list_scopes()

  def map_dest_objs(self, dest_objs_type, dest_objs_titles,
                    is_asmts_generation=False):
    """Filter, search destination objects according to them type and titles.
    Map found destination objects to source object.
    If is_asmts_generation then TextFilterDropdown is using.
    """
    selenium_utils.wait_for_js_to_load(self._driver)
    self.search_dest_objs(dest_objs_type, dest_objs_titles,
                          is_asmts_generation=is_asmts_generation)
    self._select_dest_objs_to_map(objs_titles=dest_objs_titles)
    self._confirm_map_selected()

  def close_modal(self):
    """Close Unified Mapper's modal window."""
    self.close_btn.click()


class MapObjectsModal(CommonUnifiedMapperModal):
  """Modal for map objects."""


class SearchObjectsModal(CommonUnifiedMapperModal):
  """Modal for search objects."""


class GenerateAssessmentsModal(CommonUnifiedMapperModal):
  """Modal for map objects."""
  _locators = locator.ModalGenerateAssessments

  def generate_asmts(self, objs_under_asmt_titles, asmt_tmpl_title=None):
    """Filter, search objects under Assessment according to them titles:
    objects under assessments titles, if 'asmt_tmpl_title'
    then Assessment Template title.
    Generate Assessments based on found objects under Assessment.
    """
    # pylint: disable=invalid-name
    self.map_dest_objs(
        dest_objs_type=asmt_tmpl_title,
        dest_objs_titles=objs_under_asmt_titles, is_asmts_generation=True)


class AssessmentCreationMapperModal(CommonUnifiedMapperModal):
  """Class for UnifiedMapper modal on Assessment Edit/Create Modal."""
  def _confirm_items_added(self):
    """Wait until items shown on Edit/Create Assessment Modal."""
    selenium_utils.get_when_invisible(
        self._driver, locator.TreeView.NO_RESULTS_MESSAGE)
