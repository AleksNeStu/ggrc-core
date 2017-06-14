# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Program page smoke tests."""
# pylint: disable=no-self-use
# pylint: disable=invalid-name
# pylint: disable=too-few-public-methods
# pylint: disable=unused-argument

import pytest    # pylint: disable=import-error

from lib import base
from lib.constants import element, locator, url
from lib.page import dashboard, widget_bar
from lib.page.widget import info_widget
from lib.utils import test_utils, selenium_utils


class TestProgramPage(base.Test):
  """A part of smoke tests, section 4."""

  @pytest.mark.smoke_tests
  def test_object_count_updates(self, selenium, new_program_ui):
    """Checks if count updates in LHN after creating new program
    object."""
    _, program_info_page = new_program_ui
    lhn_menu = dashboard.Header(selenium).open_lhn_menu().select_my_objects()
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
    assert (url.PROGRAMS + "/" + program_info_page.source_obj_id_from_url in
            program_info_page.url)

  @pytest.mark.smoke_tests
  def test_info_tab_is_active_by_default(self, selenium, new_program_ui):
    """Tests if after lhn_modal is saved we're redirected and info
    tab is activated.
    Because app uses url arguments to remember state of page
    (which widget is active), we can simply use url of created
    object.
    """
    _, program_info_page = new_program_ui
    program_info_page.navigate_to()
    horizontal_bar = widget_bar.Dashboard(selenium)
    assert (horizontal_bar.get_active_widget_name() ==
            element.ProgramInfoWidget().WIDGET_HEADER)

  @pytest.mark.smoke_tests
  def test_info_tab_contains_entered_data(self, new_program_ui):
    """Verify that created object contains data we've entered
    into modal."""
    modal, program_info_page = new_program_ui
    assert (test_utils.HtmlParser.parse_text(modal.ui_title.text) ==
            program_info_page.title_entered().text)
    assert (modal.ui_description.text ==
            program_info_page.description_entered.text)
    assert modal.ui_notes.text == program_info_page.notes_entered.text
    assert modal.ui_code.text == program_info_page.code_entered.text
    assert (modal.ui_program_url.text ==
            program_info_page.program_url_entered.text)
    assert (modal.ui_reference_url.text ==
            program_info_page.reference_url_entered.text)
    assert (modal.ui_effective_date.text ==
            program_info_page.effective_date_entered.text)
    assert modal.ui_stop_date.text == program_info_page.stop_date_entered.text

  @pytest.mark.smoke_tests
  def test_permalink(self, selenium, new_program_ui):
    """Verify url is copied to clipboard."""
    _, program_info_page = new_program_ui
    selenium_utils.open_url(selenium, program_info_page.url)
    program_info_page = info_widget.Programs(selenium)
    program_info_page.open_info_3bbs().select_get_permalink()
    # test notification alert
    base.AnimatedComponent(
        selenium, [locator.WidgetInfoProgram.ALERT_LINK_COPIED],
        wait_until_visible=True)
    # test generated link
    modal = program_info_page.open_info_3bbs().select_edit()
    modal.ui_title.paste_from_clipboard(modal.ui_description)
    assert modal.ui_title.text == program_info_page.url

  @pytest.mark.smoke_tests
  def test_edit_modal(self, selenium, new_program_ui):
    """Tests if data is saved after editing program info page edit modal.
    """
    _, program_info_page = new_program_ui
    selenium_utils.open_url(selenium, program_info_page.url)
    program_info_page = info_widget.Programs(selenium)
    modal = program_info_page.open_info_3bbs().select_edit()
    test_utils.ModalNewPrograms.enter_test_data(modal)
    test_utils.ModalNewPrograms.set_start_end_dates(modal, 1, -2)
    modal.save_and_close()
    selenium_utils.open_url(selenium, program_info_page.url)
    updated_program_info_page = info_widget.Programs(selenium)
    assert (test_utils.HtmlParser.parse_text(modal.ui_title.text) ==
            updated_program_info_page.title_entered().text)
    assert (modal.ui_description.text ==
            updated_program_info_page.description_entered.text)
    assert modal.ui_notes.text == updated_program_info_page.notes_entered.text
    assert (modal.ui_program_url.text ==
            updated_program_info_page.program_url_entered.text)
    assert (modal.ui_reference_url.text ==
            updated_program_info_page.reference_url_entered.text)
