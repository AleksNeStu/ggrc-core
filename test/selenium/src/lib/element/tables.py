# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Module of classes inherited from AbstractTable control."""
import itertools

from lib import base
from lib.constants import locator, element
from lib.page.modal import create_new_object
from lib.utils import selenium_utils


class CommonTable(base.AbstractTable):
  """Common table class for Table."""
  def __init__(self, driver, table_element):
    super(CommonTable, self).__init__(driver)
    self.table_element = table_element
    self._locators = self._get_locators()
    self._headers, self._rows, self._items = (None, None, None)

  def get_headers(self):
    """Get WebElement of headers in "table_element" scope then split it by
    "get_cells" method.
    Return list of headers: [str, str ..]
    """
    if not self._headers:
      headers_row = self.table_element.find_element(*self._locators.HEADERS)
      self._headers = [el.text for el in self.get_cells(headers_row)]
    return self._headers

  def get_rows(self):
    """Get WebElements of rows in "table_element" scope
    Return list of WebElement: [WebElement, WebElement ...]
    """
    if not self._rows:
      self._rows = selenium_utils.get_when_all_visible(
          self.table_element, self._locators.ROWS)
    return self._rows

  def get_cells(self, row):
    """Split any row by getting first-level child WebElement.
    Return list of WebElement: [WebElement, WebElement ...]
    """
    return selenium_utils.get_nested_elements(row)

  def get_items(self, as_element=False):
    """Map all cells of all rows to headers. Value is text of WebElement by
    default. If "as_element" attr is passed, value will be WebElement.
    Return list of dicts: [{header: value, header: value} ...]
    """
    if not self._items or as_element:
      self._items = [
          dict(itertools.izip(self.get_headers(), itertools.cycle(
              cells if as_element else [c.text for c in cells])))
          for cells in [self.get_cells(row) for row in self.get_rows()]]
    return self._items

  def _get_locators(self):
    """Should implement locators getter."""
    raise NotImplementedError


class AssessmentRelatedIssuesTable(CommonTable):
  """Table class for AssessmentRelated Issues."""
  def __init__(self, driver, table_element):
    super(AssessmentRelatedIssuesTable, self).__init__(driver, table_element)
    self._elements = element.RelatedIssuesTab

  def _get_locators(self):
    return locator.AssessmentRelatedTable

  def raise_issue(self, issue_entity):
    """Click on "raise issue" button then fill IssueCreate modal and save
    the Issue.
    """
    raise_btn = base.Button(self._driver, self.table_element.find_element(
        *self._locators.TAB_BUTTON))
    raise_btn.click()
    create_new_object.IssuesCreate(self._driver).fill_minimal_data(
        issue_entity.title, issue_entity.slug).save_and_close()
    selenium_utils.wait_for_js_to_load(self._driver)


class AssessmentRelatedAsmtsTable(CommonTable):
  """Table class for AssessmentRelated Assessments."""
  def __init__(self, driver, table_element):
    super(AssessmentRelatedAsmtsTable, self).__init__(driver, table_element)
    self._elements = element.RelatedAsmtsTab

  def _get_locators(self):
    return locator.AssessmentRelatedTable

  def reuse_asmt(self):
    raise NotImplementedError

  def get_related_titles(self):
    """Get titles of Related Assessments and their related Audit and
    Controls titles.
    Return list of tuples, tuples with 3 strings:
      [(str, str, str ), (str, str, str) ...]
    """
    return [
        (r_asmt[self._elements.ASSESSMENT_TITLE.upper()],
         r_asmt[self._elements.RELATED_CONTROLS.upper()],
         r_asmt[self._elements.AUDIT_TITLE.upper()])
        for r_asmt in self.get_items()]
