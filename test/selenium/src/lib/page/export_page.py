# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Export page with Export Panels."""

from lib import base
from lib.constants import locator, element
from lib.utils import selenium_utils


class ExportPanel(base.Component):
  """Export Panel on Export Page."""

  def __init__(self, driver, export_panel):
    super(ExportPanel, self).__init__(driver)


class ExportPage(base.Page):
  """Export Page."""
  _locators = locator.ExportPage
  _elements = element.ExportPage

  def __init__(self, driver):
    super(ExportPage, self).__init__(driver)
    self.export_page = self._driver.find_element(
        *self._locators.EXPORT_PAGE_CSS)
    self.export_panels = self.get_list_export_panels()
    self.export_format_dd = base.DropdownStatic(
        self.export_page, self._locators.EXPORT_FORMAT_DD_CSS)
    self.add_obj_type_btn = base.Button(
        self.export_page, self._locators.ADD_OBJECT_TYPE_BTN_CSS)
    self.export_objs_btn = base.Button(
        self.export_page, self._locators.EXPORT_OBJECTS_BTN_CSS)

  def get_list_export_panels(self):
    """Get list of all Export Panels witch are presented on Export Page at the
    moment of getting.
    """
    return [ExportPanel(self._driver, exp_panel_el) for exp_panel_el in
            self.export_page.find_elements(*self._locators.EXPORT_PANEL_CSS)]

  def click_export_objs(self):
    """Click to 'Export Objects' button to confirm export objects according to
    selected before export format (Google Sheet or CSV).
    """
    self.export_objs_btn.click()
    selenium_utils.get_when_invisible(
        self.export_page, locator.Common.SPINNER_CSS)
    selenium_utils.wait_for_js_to_load(self._driver)

  def export_objs_to_csv(self):
    """Export objects choosing CSV as exporting format."""
    self.export_format_dd.select_by_label(self._elements.CSV)
    self.click_export_objs()
