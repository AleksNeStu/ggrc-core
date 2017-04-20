# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""List dashboard."""

from selenium.common import exceptions

from lib import base, environment, decorator
from lib.constants import url, locator
from lib.page import widget_bar, lhn


class UserList(base.Component):
  """User list dashboard."""
  locators = locator.PageHeader

  def __init__(self, driver):
    super(UserList, self).__init__(driver)
    self.button_logout = base.Button(
        self._driver, self.locators.BUTTON_LOGOUT)
    self.notifications = base.Label(
        self._driver, self.locators.NOTIFICATIONS)
    self.checkbox_daily_digest = base.Checkbox(
        self._driver, self.locators.CHECKBOX_DAILY_DIGEST)
    self.button_admin_dashboard = base.Button(
        self._driver, self.locators.BUTTON_ADMIN_DASHBOARD)
    self.button_help = base.Button(
        self._driver, self.locators.BUTTON_HELP)
    self.button_data_export = base.Button(
        self._driver, self.locators.BUTTON_DATA_EXPORT)

  @decorator.wait_for_redirect
  def select_logout(self):
    raise NotImplementedError

  def check_daily_email_digest(self):
    """Checks daily checkbox."""
    self.checkbox_daily_digest.check()

  def uncheck_daily_email_digest(self):
    """Unchecks daily checkbox."""
    self.checkbox_daily_digest.uncheck()

  def select_admin_dashboard(self):
    """
    Return: widget.AdminDashboard
    """
    self.button_admin_dashboard.click()
    return AdminDashboard(self._driver)


class GenericHeader(base.Component):
  """Header of page dashboard without navigation to admin panel."""
  # pylint: disable=too-many-instance-attributes
  locators = locator.PageHeader

  def __init__(self, driver):
    super(GenericHeader, self).__init__(driver)
    self.toggle_lhn_menu = None
    self.button_dashboard = None
    self.button_search = None
    self.button_my_tasks = None
    self.button_all_objects = None
    self.toggle_user_dropdown = None
    self.button_data_import = None
    self.button_data_export = None
    self._refresh_elements()

  def _refresh_elements(self):
    """Refresh dashboard elements."""
    self.button_dashboard = base.Button(
        self._driver, self.locators.BUTTON_DASHBOARD)
    self.button_search = base.Button(
        self._driver, self.locators.BUTTON_SEARCH)
    self.button_my_tasks = base.Button(
        self._driver, self.locators.BUTTON_MY_TASKS)
    self.button_all_objects = base.Button(
        self._driver, self.locators.BUTTON_ALL_OBJECTS)
    self.toggle_user_dropdown = base.Toggle(
        self._driver, self.locators.TOGGLE_USER_DROPDOWN)
    self.toggle_lhn_menu = base.Toggle(
        self._driver, self.locators.TOGGLE_LHN)
    self.button_data_import = base.Button(
        self._driver, self.locators.BUTTON_DATA_IMPORT)

  def open_lhn_menu(self):
    """Opens LHN on Dashboard.
    For some reason, after creating 2 objects via LHN (and clicking 2x on
    LHN button), third time toggle_lhn_menu signals it's not part of
    the DOM anymore. For this reason we're refreshing elements.
    Return: LHN Menu
    """
    try:
      self.toggle_lhn_menu.toggle()
      return lhn.Menu(self._driver)
    except exceptions.StaleElementReferenceException:
      self._refresh_elements()
      return self.open_lhn_menu()

  def close_lhn_menu(self):
    """Closes LHN on Dashboard.
    Return: LhnMenu
    """
    try:
      self.toggle_lhn_menu.toggle(on_el=False)
    except exceptions.WebDriverException:
      self._refresh_elements()
      self.close_lhn_menu()

  def open_user_list(self):
    """
    Return: UserList
    """
    self.toggle_user_dropdown.click()
    return UserList(self._driver)

  def select_my_work(self):
    """
    Return: widget.Dashboard
    """
    self.button_dashboard.click()
    return Dashboard(self._driver)


class Header(GenericHeader):
  """Header of page dashboard with navigation to admin panel."""

  def __init__(self, driver):
    super(Header, self).__init__(driver)
    self._refresh_elements()


class Dashboard(widget_bar.Dashboard, Header):
  """Main dashboard page."""
  # pylint: disable=abstract-method
  URL = environment.APP_URL + url.DASHBOARD

  def __init__(self, driver):
    super(Dashboard, self).__init__(driver)


class AdminDashboard(widget_bar.AdminDashboard, GenericHeader):
  """Admin Dashboard page model."""
  # pylint: disable=abstract-method
  URL = environment.APP_URL + url.ADMIN_DASHBOARD

  def __init__(self, driver):
    super(AdminDashboard, self).__init__(driver)
