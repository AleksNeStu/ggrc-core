# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Program page smoke tests."""
# pylint: disable=no-self-use
# pylint: disable=invalid-name
# pylint: disable=too-few-public-methods
# pylint: disable=unused-argument

import pytest  # pylint: disable=import-error

from lib import base
from lib.constants import element, locator, url
from lib.page.widget import info_widget
from lib.utils import test_utils, selenium_utils


class TestProgramPage(base.Test):
  """A part of smoke tests, section 4."""

  @pytest.mark.smoke_tests
  def test_object_count_updates(self, new_program_ui, header_dashboard):
    """Checks if count updates in LHN after creating new program
    object."""
    _, program_info_page = new_program_ui
    lhn_menu = header_dashboard.open_lhn_menu().select_my_objects()
    assert (lhn_menu.toggle_programs.members_count >=
            int(program_info_page.source_obj_id_from_url))

  @pytest.mark.smoke_tests
  def test_modal_redirects(self, new_program_ui):
    """Tests if after saving and closing lhn_modal app redirects to
    the object page.
    Generally we start at random url. Here we verify that after saving
    and closing lhn_modal we're redirected to an url that contains an
    object id.
    """
    _, program_info_page = new_program_ui
    expected_url = (
      url.All.PROGRAMS + "/" + program_info_page.source_obj_id_from_url)
    actual_url = program_info_page.url
    assert expected_url in actual_url

  @pytest.mark.smoke_tests
  def test_info_tab_is_active_by_default(self, new_program_ui,
                                         my_work_dashboard):
    """Tests if after lhn_modal is saved we're redirected and info
    tab is activated.
    Because app uses url arguments to remember state of page
    (which widget is active), we can simply use url of created
    object.
    """
    _, program_info_page = new_program_ui
    program_info_page.navigate_to()
    expected_widget_name = element.ProgramInfoWidget().WIDGET_HEADER
    actual_widget_name = my_work_dashboard.get_active_widget_name()
    assert expected_widget_name == actual_widget_name

  @pytest.mark.smoke_tests
  def test_info_tab_contains_entered_data(self, new_program_ui):
    """Verify that created object contains data we've entered
    into modal."""
    modal, program_info_page = new_program_ui
    expected_list_texts = [
        test_utils.HtmlParser.parse_text(modal.ui_title.text),
        modal.ui_description.text, modal.ui_notes.text, modal.ui_code.text,
        modal.ref_url.values,
        modal.ui_effective_date.text
    ]
    actual_list_texts = [
        program_info_page.title.text,
        program_info_page.description_entered.text,
        program_info_page.notes_entered.text,
        program_info_page.code_entered.text,
        program_info_page.ref_url.values,
        program_info_page.effective_date_entered.text,
    ]
    assert expected_list_texts == actual_list_texts

  @pytest.mark.smoke_tests
  def test_permalink(self, selenium, new_program_ui):
    """Verify url is copied to clipboard."""
    _, program_info_page = new_program_ui
    selenium_utils.open_url(selenium, program_info_page.url)
    program_info_page = info_widget.Programs(selenium)
    expected_url = url.Utils.get_src_obj_url(program_info_page.url)
    program_info_page.open_info_3bbs().select_get_permalink()
    # test notification alert
    base.AnimatedComponent(
        selenium, [locator.WidgetInfoProgram.ALERT_LINK_COPIED],
        wait_until_visible=True)
    # test generated link
    modal = program_info_page.open_info_3bbs().select_edit()
    modal.ui_title.paste_from_clipboard(modal.ui_description)
    actual_url = modal.ui_title.text
    assert expected_url in actual_url

  @pytest.mark.smoke_tests
  def test_edit_modal(self, selenium, new_program_ui):
    """Tests if data is saved after editing program info page edit modal.
    """
    _, program_info_page = new_program_ui
    selenium_utils.open_url(selenium, program_info_page.url)
    program_info_page = info_widget.Programs(selenium)
    modal = program_info_page.open_info_3bbs().select_edit()
    test_utils.ModalNewPrograms.enter_test_data(modal)
    test_utils.ModalNewPrograms.set_start_date(modal, 1)
    modal.save_and_close()
    selenium_utils.open_url(selenium, program_info_page.url)
    updated_program_info_page = info_widget.Programs(selenium)
    expected_list_texts = [
        test_utils.HtmlParser.parse_text(modal.ui_title.text),
        modal.ui_description.text, modal.ui_notes.text,
        modal.ref_url.values]
    actual_list_texts = [
        updated_program_info_page.title.text,
        updated_program_info_page.description_entered.text,
        updated_program_info_page.notes_entered.text,
        updated_program_info_page.ref_url.values]
    assert expected_list_texts == actual_list_texts
