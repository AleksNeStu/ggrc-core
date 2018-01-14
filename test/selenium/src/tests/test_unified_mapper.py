# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Unified mapper tests."""
# pylint: disable=no-self-use
# pylint: disable=invalid-name
# pylint: disable=too-few-public-methods

import pytest

from lib import base
from lib.entities.entity import Representation
from lib.service import webui_service
from lib.constants import objects

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
    expected_controls = [
        expected_control.repr_ui() for expected_control in new_controls_rest]
    controls_ui_service = webui_service.ControlsService(selenium)
    controls_ui_service.map_objs_via_tree_view(
        src_obj=new_program_rest, dest_objs=expected_controls)
    actual_controls_tab_count = controls_ui_service.get_count_objs_from_tab(
        src_obj=new_program_rest)
    assert len(expected_controls) == actual_controls_tab_count
    actual_controls = controls_ui_service.get_list_objs_from_tree_view(
        src_obj=new_program_rest)
    # 'actual_controls': created_at, updated_at, custom_attributes (None)
    self.general_equal_assert(
        sorted(expected_controls), sorted(actual_controls),
        *Representation.tree_view_attrs_to_exclude)

  @pytest.mark.smoke_tests
  def test_per_dfgdfg(
      self, new_program_rest, new_control_rest,
      map_new_program_rest_to_new_control_rest, new_audit_rest,
      new_assessment_rest
  ):
    assert 1
    print new_assessment_rest
    f = 2
    g =1


  @pytest.yield_fixture(scope="function")
  def dynamic_new_gcas_for_entities(self, request):
    import conftest
    yield conftest._common_fixtures(request.param) if request.param else None

  @pytest.mark.smoke_tests
  @pytest.mark.parametrize(
    "dynamic_new_gcas_for_entities",
    ["new_cas_for_{obj}_rest".format(obj=obj) for obj in objects.ALL_CA_OBJS],
    indirect=["dynamic_new_gcas_for_entities"])
  def test_add_6gcas_for_all_entities(self, dynamic_new_gcas_for_entities):
    # for gcas in dynamic_new_gcas_for_entities:
    #   print gcas
    #   print "\n"
   assert 1 == 1
