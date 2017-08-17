# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Unified mapper tests."""
# pylint: disable=no-self-use
# pylint: disable=invalid-name
# pylint: disable=too-few-public-methods

import pytest

from lib import base
from lib.service import webui_service


class TestProgramPage(base.Test):
  """Tests of unified mapper."""

  @pytest.mark.smoke_tests
  def test_mapping_controls_to_program_via_unified_mapper(
      self, new_program_rest, new_controls_rest, selenium
  ):
    """Check if Controls can be mapped to Program from Controls widget under
    Program page via unified mapper.
    Preconditions:
    - Program, Controls created via REST API.
    """
    # pylint: disable=no-self-use
    # due to 'actual_control.custom_attributes = {None: None}'
    expected_controls = [
        expected_control.repr_ui().update_attrs(custom_attributes={None: None})
        for expected_control in new_controls_rest]
    (webui_service.ControlsService(selenium).map_objs_via_tree_view(
        src_obj=new_program_rest, dest_objs=expected_controls))
    actual_controls_tab_count = (
        webui_service.ControlsService(selenium).get_count_objs_from_tab(
            src_obj=new_program_rest))
    assert len(expected_controls) == actual_controls_tab_count
    actual_controls = (webui_service.ControlsService(selenium).
                       get_list_objs_from_tree_view(src_obj=new_program_rest))
    self.extended_assert_w_excluded_attrs(
        sorted(expected_controls), sorted(actual_controls))
