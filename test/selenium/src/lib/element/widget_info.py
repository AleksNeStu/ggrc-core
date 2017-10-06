# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Info Page and Info Panel dropdown elements."""

from lib import base
from lib.constants import locator, element
from lib.element import elements_list
from lib.page.modal import (delete_object, edit_object, update_object,
                            clone_object)


class CommonInfoDropdownSettings(elements_list.DropdownMenu):
  """Common for 3BBS button/dropdown settings on Info pages and Info panels.
  """
  _locators = locator.CommonDropdown3bbsInfoWidget
  _elements = element.DropdownMenuItemTypes

  def __init__(self, driver):
    super(CommonInfoDropdownSettings, self).__init__(
        driver, self._locators.INFO_WDG_3BBS_DD_XPTAH)
    self.dropdown_button = base.Button(
        self._driver, self._locators.INFO_WDG_3BBS_DD_BTN_XPATH)

  def select_open(self):
    """Select open button in 3BBS dropdown modal."""
    self.get_dropdown_item(self._elements.OPEN).click()

  def select_edit(self):
    """Select edit button in 3BBS dropdown modal.
    Return: lib.page.modal.edit_object.EditModal
    """
    self.get_dropdown_item(self._elements.EDIT).click()
    return getattr(edit_object, self.__class__.__name__)(self._driver)

  def select_get_permalink(self):
    """Select get permalink in 3BBS dropdown modal."""
    self.get_dropdown_item(self._elements.GET_PERMALINK).click()

  def select_delete(self):
    """Select delete in 3BBS dropdown modal.
    Return: modal.delete_object.DeleteObjectModal
    """
    self.get_dropdown_item(self._elements.DELETE).click()
    return delete_object.DeleteObjectModal(self._driver)

  def select_unmap(self):
    """Select unmap in 3BBS dropdown modal."""
    self.get_dropdown_item(self._elements.UNMAP).click()


class Snapshots(CommonInfoDropdownSettings):
  """Snapshots 3BBS button/dropdown settings on Info panels."""


class Audits(CommonInfoDropdownSettings):
  """Audits 3BBS button/dropdown settings on Info pages and Info panels."""
  _locators = locator.AuditsDropdown3bbsInfoWidget

  def select_update_objs(self):
    """Select update objects to latest version in 3BBS dropdown modal.
    Return: modal.update_object.CompareUpdateObjectModal
    """
    self.get_dropdown_item(self._elements.UPDATE).click()
    return update_object.CompareUpdateObjectModal(self._driver)

  def select_clone(self):
    """Select clone Audit in 3BBS dropdown modal.
    Return: modal.clone_object.CloneAuditModal
    """
    self.get_dropdown_item(self._elements.CLONE).click()
    return clone_object.CloneAuditModal(self._driver)


class Programs(CommonInfoDropdownSettings):
  """Programs 3BBS button/dropdown settings on Info pages and Info panels."""


class Controls(Snapshots):
  """Controls 3BBS button/dropdown settings on Info pages and Info panels."""


class Processes(CommonInfoDropdownSettings):
  """Processes 3BBS button/dropdown settings on Info pages and Info panels."""


class DataAssets(CommonInfoDropdownSettings):
  """DataAssets 3BBS button/dropdown settings on Info pages and Info panels."""


class Systems(CommonInfoDropdownSettings):
  """Systems 3BBS button/dropdown settings on Info pages and Info panels."""


class Products(CommonInfoDropdownSettings):
  """Products 3BBS button/dropdown settings on Info pages and Info panels."""


class Projects(CommonInfoDropdownSettings):
  """Projects 3BBS button/dropdown settings on Info pages and Info panels."""


class OrgGroups(CommonInfoDropdownSettings):
  """OrgGroups 3BBS button/dropdown settings on Info pages and Info panels."""


class Assessments(CommonInfoDropdownSettings):
  """Assessments 3BBS button/dropdown settings on Info pages and Info panels.
  """
