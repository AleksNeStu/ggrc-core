# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""All smoke tests relevant to program page"""
# pylint: disable=no-self-use
# pylint: disable=invalid-name
# pylint: disable=too-few-public-methods
# pylint: disable=unused-argument

import pytest    # pylint: disable=import-error

from lib import base
from lib.utils import test_utils
from lib.constants import element
from lib.constants import url
from lib.constants import locator
from lib.page import dashboard
from lib.page import widget_bar
from lib.page.widget import info_widget


class TestProgramPage(base.Test):
  """A part of smoke tests, section 4."""

  @pytest.mark.smoke_tests
  def test_object_count_updates(self, selenium, new_program):
    """Checks if the count updates in LHN after creating a new program
    object."""
    _, program_info_page = new_program
    lhn_menu = dashboard.Header(selenium) \
        .open_lhn_menu() \
        .select_my_objects()

    assert lhn_menu.toggle_programs.members_count \
        >= int(program_info_page.object_id)

  @pytest.mark.smoke_tests
  def test_modal_redirects(self, new_program):
    """Tests if after saving and closing the lhn_modal the app redirects to
    the object page.

    Generally we start at a random url. Here we verify that after saving
    and closing the lhn_modal we're redirected to an url that contains an
    object id.
    """
    _, program_info_page = new_program
    assert url.PROGRAMS + "/" + program_info_page.object_id in \
        program_info_page.url

  @pytest.mark.smoke_tests
  def test_info_tab_is_active_by_default(self, selenium, new_program):
    """Tests if after the lhn_modal is saved we're redirected and the info
    tab is activated.

    Because the app uses url arguments to remember the state of the page
    (which widget is active), we can simply use the url of the created
    object.
    """
    _, program_info_page = new_program
    program_info_page.navigate_to()
    horizontal_bar = widget_bar.Dashboard(selenium)

    assert horizontal_bar.get_active_widget_name() == \
        element.ProgramWidgetInfo.TREE_VIEW_HEADER

  @pytest.mark.smoke_tests
  def test_info_tab_contains_entered_data(self, new_program):
    """Verify that the created object contains the data we've entered
    into the modal."""
    modal, program_info_page = new_program

    assert test_utils.HtmlParser.parse_text(modal.ui_title.text) == \
        program_info_page.title_entered.text
    assert modal.ui_description.text == \
        program_info_page.description_entered.text
    assert modal.ui_notes.text == program_info_page.notes_entered.text
    assert modal.ui_code.text == program_info_page.code_entered.text
    assert program_info_page.primary_contact_entered.text in \
        modal.ui_primary_contact.text
    assert program_info_page.secondary_contact_entered.text in \
        modal.ui_secondary_contact.text
    assert modal.ui_program_url.text == \
        program_info_page.program_url_entered.text
    assert modal.ui_reference_url.text == \
        program_info_page.reference_url_entered.text
    assert modal.ui_effective_date.text == \
        program_info_page.effective_date_entered.text
    assert modal.ui_stop_date.text == program_info_page.stop_date_entered.text

  @pytest.mark.smoke_tests
  def test_permalink(self, selenium, new_program):
    """Verify the url is copied to clipboard"""
    _, program_info = new_program
    selenium.get(program_info.url)

    program_info_page = info_widget.Programs(selenium)
    program_info_page \
        .press_object_settings() \
        .select_get_permalink()

    # test notification alert
    base.AnimatedComponent(
        selenium,
        [locator.WidgetInfoProgram.ALERT_LINK_COPIED],
        wait_until_visible=True
    )

    # test generated link
    modal = program_info_page \
        .press_object_settings() \
        .select_edit()
    modal.ui_title.paste_from_clipboard(modal.ui_description)

    assert modal.ui_title.text == program_info_page.url

  @pytest.mark.smoke_tests
  def test_edit_modal(self, selenium, new_program):
    """Tests if data is saved after editing the program info page edit modal"""
    _, program_info = new_program
    selenium.get(program_info.url)

    program_info_page = info_widget.Programs(selenium)
    modal = program_info_page \
        .press_object_settings() \
        .select_edit()
    test_utils.ModalNewPrograms.enter_test_data(modal)
    test_utils.ModalNewPrograms.set_start_end_dates(modal, 1, -2)
    modal.save_and_close()

    updated_program_info_page = info_widget.Programs(selenium)
    assert test_utils.HtmlParser.parse_text(modal.ui_title.text) == \
        updated_program_info_page.title_entered.text
    assert modal.ui_description.text == \
        updated_program_info_page.description_entered.text
    assert modal.ui_notes.text == updated_program_info_page.notes_entered.text
    assert updated_program_info_page.primary_contact_entered.text in \
        modal.ui_primary_contact.text
    assert updated_program_info_page.secondary_contact_entered.text in \
        modal.ui_secondary_contact.text
    assert modal.ui_program_url.text == \
        updated_program_info_page.program_url_entered.text
    assert modal.ui_reference_url.text == \
        updated_program_info_page.reference_url_entered.text

  @pytest.mark.smoke_tests
  def test_mapping_controls_via_lhn(self, selenium, new_control, new_program):
    """Tests if widget number increases when mapping via LHN"""

    # check that the widget isn't opened yet since it doesn't have any members
    assert selenium.find_element(
        *locator.WidgetBar.CONTROLS).is_displayed() is False

    # map to obj
    dashboard.Header(selenium)\
        .open_lhn_menu()\
        .select_my_objects()\
        .select_controls_or_objectives()\
        .select_controls()\
        .hover_over_visible_member(new_control.title_entered.text)\
        .map_to_object()
    control_widget_count = widget_bar.Programs(selenium)\
        .select_controls()\
        .member_count
    assert control_widget_count == 1
