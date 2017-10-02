# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Objectives tests."""
# pylint: disable=no-self-use
# pylint: disable=invalid-name
# pylint: disable=too-few-public-methods

import pytest

from lib import base

from lib.service import rest_service
from lib.service import webui_service
from lib.service.rest.client import RestClient
from lib.utils import help_utils


class TestObjectivePage(base.Test):
  """Tests of objectives."""

  @pytest.mark.smoke_tests
  @pytest.mark.parametrize(
      "dynamic_objects, dynamic_relationships, is_map_again",
      [("new_objective_rest",
        "map_new_control_rest_to_new_objective_rest", False),
       ("new_objectives_rest",
        "map_new_control_rest_to_new_objectives_rest", False),
       ("new_objective_rest",
        "map_new_control_rest_to_new_objective_rest", True),
       ],
      ids=["Check if Objective can be mapped to Control via REST",
           "Check if Multiple Objectives can be mapped to Control via REST",
           "Check if Objective can't be mapped to Control twice via REST"],
      indirect=["dynamic_objects", "dynamic_relationships"])
  def test_mapping_objectives_to_control_via_rest(
      self, new_control_rest, dynamic_objects, dynamic_relationships,
      is_map_again, selenium
  ):
    """Check if Objectives can be mapped to Control via REST."""
    # pylint: disable=too-many-arguments
    expected_status_code = RestClient.STATUS_CODES["OK"]
    dynamic_relationships = help_utils.convert_to_list(dynamic_relationships)
    assert all(expected_status_code == relationship.status_code
               for relationship in dynamic_relationships)
    assert (
        (rest_service.RelationshipsService().map_objs(
            src_obj=new_control_rest,
            dest_objs=dynamic_objects))[0].status_code ==
        expected_status_code) if is_map_again else True
    actual_objectives_tab_count = (
        webui_service.ObjectivesService(selenium).get_count_objs_from_tab(
            src_obj=new_control_rest))
    assert (len(help_utils.convert_to_list(dynamic_objects)) ==
            actual_objectives_tab_count)
