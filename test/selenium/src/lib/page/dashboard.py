# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

from selenium.common import exceptions

from lib import base
from lib.constants import url
from lib.constants import locator
from lib import environment
from lib import decorator
from lib.page import widget_bar
from lib.page import lhn


class UserList(base.Component):
  locators = locator.PageHeader

  def __init__(self, driver):
    super(UserList, self).__init__(driver)
    self.button_my_work = base.Button(self._driver,
                                      self.locators.BUTTON_MY_WORK)
    self.button_admin_dashboard = base.Button(
        self._driver, self.locators.BUTTON_ADMIN_DASHBOARD)
    self.button_data_import = base.Button(
        self._driver, self.locators.BUTTON_DATA_IMPORT)
    self.button_data_export = base.Button(
        self._driver, self.locators.BUTTON_DATA_EXPORT)
    self.button_logout = base.Button(
        self._driver, self.locators.BUTTON_LOGOUT)
    self.notifications = base.Label(
        self._driver, self.locators.NOTIFICATIONS)
    self.checkbox_daily_digest = base.Checkbox(
        self._driver, self.locators.CHECKBOX_DAILY_DIGEST)

  def select_my_work(self):
    """
    Returns:
        widget.DataAssets
    """
    self.button_my_work.click()
    return Dashboard(self._driver)

  def select_admin_dashboard(self):
    """
    Returns:
        admin_dashboard.AdminDashboard
    """
    self.button_my_work.click()
    return AdminDashboard(self._driver)

  def select_import_data(self):
    raise NotImplementedError

  def select_export_data(self):
    raise NotImplementedError

  @decorator.wait_for_redirect
  def select_logout(self):
    raise NotImplementedError

  def check_daily_email_digest(self):
    """Checks the daily checkbox"""
    self.checkbox_daily_digest.check()

  def uncheck_daily_email_digest(self):
    """Unchecks the daily checkbox"""
    self.checkbox_daily_digest.uncheck()


class Header(base.Component):
  """Header of the page"""
  locators = locator.PageHeader

  def __init__(self, driver):
    super(Header, self).__init__(driver)
    self.toggle_lhn_menu = None
    self.button_dashboard = None
    self.button_search = None
    self.button_my_tasks = None
    self.button_all_objects = None
    self.toggle_user_dropdown = None
    self._refresh_elements()

  def _refresh_elements(self):
    self.button_dashboard = base.Button(self._driver,
                                        self.locators.BUTTON_DASHBOARD)
    self.button_search = base.Button(self._driver,
                                     self.locators.BUTTON_SEARCH)
    self.button_my_tasks = base.Button(self._driver,
                                       self.locators.BUTTON_MY_TASKS)
    self.button_all_objects = base.Button(
        self._driver, self.locators.BUTTON_ALL_OBJECTS)
    self.toggle_user_dropdown = base.Toggle(
        self._driver, self.locators.TOGGLE_USER_DROPDOWN)
    self.toggle_lhn_menu = base.Toggle(self._driver,
                                       self.locators.TOGGLE_LHN)

  def open_lhn_menu(self):
    """Opens LHN on the Dashboard.
    For some reason, after creating 2 objects via LHN (and clicking 2x on the
    LHN button), the third time the toggle_lhn_menu signals it's not a part of
    the DOM anymore. For this reason we're refreshing the elements.

    Returns:
        LhnMenu
    """
    try:
      self.toggle_lhn_menu.toggle()
      return lhn.Menu(self._driver)
    except exceptions.StaleElementReferenceException:
      self._refresh_elements()
      return self.open_lhn_menu()

  def close_lhn_menu(self):
    """Closes LHN on the Dashboard

    Returns:
        LhnMenu
    """
    try:
      self.toggle_lhn_menu.toggle(on_el=False)
    except exceptions.WebDriverException:
      self._refresh_elements()
      self.close_lhn_menu()

  def click_on_logo(self):
    """
    Returns:
        widget.DataAssets
    """
    raise NotImplementedError

  def open_user_list(self):
    """
    Returns:
        UserList
    """
    self.toggle_user_dropdown.click()
    return UserList(self._driver)


class Dashboard(widget_bar.Dashboard, Header):
  """The main dashboard page"""
  URL = environment.APP_URL + url.DASHBOARD

  def __init__(self, driver):
    super(Dashboard, self).__init__(driver)
    self.button_help = base.Button(self._driver, self.locators.BUTTON_HELP)


class AdminDashboard(widget_bar.AdminDashboard, Header):
  """Admin dashboard page model"""
  URL = environment.APP_URL + url.ADMIN_DASHBOARD

  def __init__(self, driver):
    super(AdminDashboard, self).__init__(driver)
