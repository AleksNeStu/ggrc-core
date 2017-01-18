# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Admin dashboard page smoke tests"""
# pylint: disable=no-self-use
# pylint: disable=invalid-name
# pylint: disable=too-few-public-methods
# pylint: disable=protected-access

import random

import pytest
import re

from lib import base, constants
from lib.constants import objects
from lib.constants.element import AdminWidgetCustomAttrs
from lib.entities.entities_factory import CAFactory
from lib.page import dashboard


class TestAdminDashboardPage(base.Test):
  """Tests for the admin dashboard page."""
  _role_el = constants.element.AdminWidgetRoles
  _event_el = constants.element.AdminWidgetEvents
  err_msg_format = constants.messages.ERR_MSG_FORMAT

  @pytest.fixture(scope="function")
  def admin_dashboard(self, selenium):
    selenium.get(dashboard.AdminDashboard.URL)
    return dashboard.AdminDashboard(selenium)

  @pytest.mark.smoke_tests
  def test_roles_widget(self, admin_dashboard):
    """Check count and content of role scopes"""
    admin_roles_widget = admin_dashboard.select_roles()
    expected_dict = self._role_el.ROLE_SCOPES_DICT
    actual_dict = admin_roles_widget.get_role_scopes_text_as_dict()
    assert admin_dashboard.tab_roles.member_count == len(expected_dict)
    assert expected_dict == actual_dict, self.err_msg_format.format(
        expected_dict, actual_dict)

  @pytest.mark.smoke_tests
  def test_events_widget_tree_view_has_data(self, admin_dashboard):
    """Confirms tree view has at least one data row in valid format"""
    admin_events_tab = admin_dashboard.select_events()
    list_of_items = admin_events_tab.get_events()
    assert len(list_of_items) > 0
    items_with_incorrect_format = \
        [getattr(item, 'text') for item in list_of_items if
            not(re.compile(self._event_el.TREE_VIEW_ROW_REGEXP).match(
                getattr(item, 'text')))]
    assert items_with_incorrect_format == []
    assert admin_events_tab.widget_header.text == \
        self._event_el.TREE_VIEW_HEADER

  @pytest.mark.smoke_tests
  def test_check_ca_groups(self, admin_dashboard):
    """Check that full list of Custom Attributes groups is displayed
    on Admin Dashboard panel.
    """
    ca_widget = admin_dashboard.select_custom_attributes()
    act_ca_groups_set = set([item.text for item in ca_widget.get_items_list()])
    exp_ca_groups_set = set([objects.get_normal_form(item) for item in
                             objects.ALL_CA_OBJECTS])
    assert exp_ca_groups_set == act_ca_groups_set, self.err_msg_format.format(
        exp_ca_groups_set, act_ca_groups_set)

  @pytest.mark.smoke_tests
  @pytest.mark.parametrize("ca_type, def_type",
                           [(ca_type_item, random.choice(objects.ALL_CA_OBJECTS))
                            for ca_type_item in
                            AdminWidgetCustomAttrs.ALL_ATTRS_TYPES])
  def test_add_global_ca(self, admin_dashboard, ca_type, def_type):
    """Create different types of Custom Attribute on Admin Dashboard."""
    exp_custom_attribute = CAFactory().create(
        ca_type=ca_type,
        definition_type=def_type)
    ca_widget = admin_dashboard.select_custom_attributes()
    ca_widget.add_custom_attribute(exp_custom_attribute)
    act_ca_list = ca_widget.get_custom_attributes_list(
        exp_custom_attribute.definition_type
    )
    assert exp_custom_attribute in act_ca_list
