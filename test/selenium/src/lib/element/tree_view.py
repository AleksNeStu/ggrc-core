# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Tree View dropdown elements."""
# pylint: disable=too-few-public-methods

from selenium.webdriver.common.by import By

from lib import base
from lib.constants import locator, url
from lib.page.modal import unified_mapper


class CommonDropdownSettings(base.DropdownMenu):
  """Common for 3BBS button/dropdown settings on Tree View."""
  _locators = locator.CommonDropdown3bbsTreeView

  def __init__(self, driver, obj_name):
    self.widget_name = url.get_widget_name_of_mapped_objs(obj_name)
    self.obj_name = obj_name
    # elements
    _dropdown_element = (
        By.CSS_SELECTOR,
        self._locators.TREE_VIEW_3BBS_DROPDOWN.format(self.widget_name))
    super(CommonDropdownSettings, self).__init__(driver, _dropdown_element)
    self.select_child_tree_locator = (
        self._locators.BUTTON_3BBS_SELECT_CHILD_TREE.format(self.widget_name))
    self.import_locator = (
        self._locators.BUTTON_3BBS_IMPORT.format(self.widget_name))
    self.export_locator = (
        self._locators.BUTTON_3BBS_EXPORT.format(self.widget_name))


class Assessments(CommonDropdownSettings):
  """Assessments 3BBS button/dropdown settings on Tree View."""
  _locators = locator.AssessmentsDropdown3bbsTreeView

  def select_generate(self):
    """Select generate Assessments in 3BBS dropdown modal to
    open unified mapper modal.
    Return: lib.page.modal.unified_mapper.GenerateAssessmentsModal
    """
    _locator_generate = (
        By.CSS_SELECTOR,
        self._locators.BUTTON_3BBS_GENERATE.format(self.widget_name))
    base.Button(self._driver, _locator_generate).click()
    return unified_mapper.GenerateAssessmentsModal(self._driver, self.obj_name)


class AssessmentTemplates(CommonDropdownSettings):
  """Assessment Templates 3BBS button/dropdown settings on Tree View."""


class Audits(CommonDropdownSettings):
  """Audits 3BBS button/dropdown settings on Tree View."""


class Programs(CommonDropdownSettings):
  """Programs 3BBS button/dropdown settings on Tree View."""


class Controls(CommonDropdownSettings):
  """Controls 3BBS button/dropdown settings on Tree View."""


class Processes(CommonDropdownSettings):
  """Processes 3BBS button/dropdown settings on Tree View."""


class DataAssets(CommonDropdownSettings):
  """DataAssets 3BBS button/dropdown settings on Tree View."""


class Systems(CommonDropdownSettings):
  """Systems 3BBS button/dropdown settings on Tree View."""


class Products(CommonDropdownSettings):
  """Products 3BBS button/dropdown settings on Tree View."""


class Projects(CommonDropdownSettings):
  """Projects 3BBS button/dropdown settings on Tree View."""


class OrgGroups(CommonDropdownSettings):
  """OrgGroups 3BBS button/dropdown settings on Tree View."""


class Issues(CommonDropdownSettings):
  """Issues 3BBS button/dropdown settings on Tree View."""
