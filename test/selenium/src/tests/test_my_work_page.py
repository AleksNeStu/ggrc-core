# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""My Work page smoke tests."""
# pylint: disable=no-self-use
# pylint: disable=invalid-name
# pylint: disable=too-few-public-methods
# pylint: disable=unused-argument

import pytest  # pylint: disable=import-error

from lib import base
from lib.constants import objects, url
from lib.page import dashboard, lhn
from lib.page.widget import generic_widget
from lib.utils import selenium_utils


class TestMyWorkPage(base.Test):
  """Tests My Work page, part of smoke tests, section 2."""

  @pytest.mark.smoke_tests
  def test_horizontal_nav_bar_tabs(self, new_controls_rest, my_work_dashboard,
                                   selenium):
    """Tests that several objects in widget can be deleted sequentially.
    Preconditions:
    - Controls created via REST API.
    """
    controls_tab = my_work_dashboard.select_controls()
    for _ in xrange(controls_tab.member_count):
      counter = controls_tab.get_items_count()
      (controls_tab.select_member_by_num(0).
       open_info_3bbs().select_delete().confirm_delete())
      controls_tab.wait_member_deleted(counter)
    controls_generic_widget = generic_widget.Controls(
        selenium, objects.Names.CONTROLS)
    expected_widget_members = []
    actual_widget_members = controls_generic_widget.members_listed
    assert expected_widget_members == actual_widget_members

  @pytest.mark.smoke_tests
  def test_redirect(self, header_dashboard, selenium):
    """Tests if user is redirected to My Work page after clicking on
    the my work button in user dropdown."""
    header_dashboard.select_my_work()
    expected_url = dashboard.Dashboard.URL + url.Widget.INFO
    actual_url = selenium.current_url
    assert expected_url == actual_url

  @pytest.mark.smoke_tests
  def test_lhn_stays_expanded(self, header_dashboard, selenium):
    """Tests if, after opening LHN, it slides out and stays expanded."""
    lhn_menu = header_dashboard.open_lhn_menu()
    initial_position = lhn_menu.my_objects.element.location
    selenium_utils.wait_until_stops_moving(lhn_menu.my_objects.element)
    selenium_utils.hover_over_element(
        selenium, dashboard.Header(selenium).button_my_tasks.element)
    expected_el_position = initial_position
    actual_el_position = lhn.Menu(selenium).my_objects.element.location
    assert expected_el_position == actual_el_position

  @pytest.mark.smoke_tests
  def test_lhn_remembers_tab_state(self, header_dashboard, selenium):
    """Tests if LHN remembers which tab is selected (my or all objects) after
    closing it."""
    lhn_menu = header_dashboard.open_lhn_menu()
    # check if my objects tab saves state
    lhn_menu.select_my_objects()
    header_dashboard.close_lhn_menu()
    header_dashboard.open_user_list()
    selenium.get(dashboard.Dashboard.URL)
    new_lhn_menu = dashboard.Header(selenium).open_lhn_menu()
    assert selenium_utils.is_value_in_attr(
        new_lhn_menu.my_objects.element) is True
    # check if all objects tab saves state
    lhn_menu = header_dashboard.open_lhn_menu()
    lhn_menu.select_all_objects()
    header_dashboard.close_lhn_menu()
    header_dashboard.open_user_list()
    assert selenium_utils.is_value_in_attr(
        new_lhn_menu.all_objects.element) is True

  @pytest.mark.smoke_tests
  def test_lhn_pin(self, header_dashboard):
    """Tests if pin is present and if it's default state is off."""
    lhn_menu = header_dashboard.open_lhn_menu()
    assert lhn_menu.pin.is_activated is False

  @pytest.mark.smoke_tests
  def test_user_menu_checkbox(self, header_dashboard):
    """Tests user menu checkbox. With that also user menu itself is
    tested since model initializes all elements (and throws and
    exception if they're not present."""
    user_list = header_dashboard.open_user_list()
    user_list.checkbox_daily_digest.click()
    user_list.checkbox_daily_digest.element.get_attribute("disabled")
    # restore previous state
    user_list.checkbox_daily_digest.click()
