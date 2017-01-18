# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Models for LHN modals when creating new objects"""

from lib import base
from lib import decorator
from lib.constants import locator
from lib.page.modal import base as modal_base
from lib.utils import selenium_utils


class _CreateNewObjectModal(modal_base.BaseModal):
  """Base create modal model."""
  _locator_button_add_another = (
      locator.ModalCreateNewObject.BUTTON_SAVE_AND_ADD_ANOTHER)

  def __init__(self, driver):
    super(_CreateNewObjectModal, self).__init__(driver)
    self.button_save_and_add_another = None

  def save_and_add_other(self):
    """Save this objects and open a new modal."""
    self.button_save_and_add_another = base.Button(
        self._driver, self._locator_button_add_another)
    self.button_save_and_add_another.click()
    selenium_utils.get_when_invisible(self._driver,
                                      self._locator_button_add_another)
    return self.__class__(self._driver)

  @decorator.wait_for_redirect
  @decorator.handle_alert
  def save_and_close(self):
    """Save this objects and close modal."""
    self.button_save_and_close.click()
    selenium_utils.get_when_invisible(self._driver, self.locator_button_save)


class _GenerateNewObjectModal(base.Modal):
  """Base generate modal model."""
  _locator_button_generate = locator.ModalGenerateNewObject.BUTTON_GENERATE

  def __init__(self, driver):
    super(_GenerateNewObjectModal, self).__init__(driver)
    self.button_generate_and_close = None

  def generate_and_close(self):
    """Save this objects and close modal."""
    self.button_generate_and_close = base.Button(
        self._driver, self._locator_button_generate)
    self.button_generate_and_close.click()
    selenium_utils.get_when_invisible(self._driver,
                                      self._locator_button_generate)


class Programs(modal_base.ProgramsModal, _CreateNewObjectModal):
  """Class representing a program modal"""


class Controls(modal_base.ControlsModal, _CreateNewObjectModal):
  """Class representing a control modal"""


class OrgGroups(modal_base.OrgGroupsModal, _CreateNewObjectModal):
  """Class representing an org group modal"""


class Risks(modal_base.RisksModal, _CreateNewObjectModal):
  """Class representing a risk modal"""


class Issues(modal_base.IssuesModal, _CreateNewObjectModal):
  """Class representing an issue modal"""


class Processes(modal_base.ProcessesModal, _CreateNewObjectModal):
  """Class representing a process modal"""


class DataAssets(modal_base.DataAssetsModal, _CreateNewObjectModal):
  """Class representing a Data Assets modal"""


class Systems(modal_base.SystemsModal, _CreateNewObjectModal):
  """Class representing a system modal"""


class Products(modal_base.ProductsModal, _CreateNewObjectModal):
  """Class representing a product modal"""


class Projects(modal_base.ProjectsModal, _CreateNewObjectModal):
  """Class representing a process modal"""


class AssessmentTemplates(modal_base.AsmtTmplModal, _CreateNewObjectModal):
  """Class representing a assessment template creation modal."""


class Assessments(modal_base.AsmtsModal, _CreateNewObjectModal):
  """Class representing a assessment creation modal."""


class AssessmentsGenerate(modal_base.AsmtsModalGenerate,
                          _GenerateNewObjectModal):
  """Class representing a assessment generation modal."""
