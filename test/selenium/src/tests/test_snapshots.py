# Copyright (C) 2017 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Snapshot smoke tests."""
# pylint: disable=no-self-use
# pylint: disable=invalid-name
# pylint: disable=unused-argument
# pylint: disable=too-many-arguments
# pylint: disable=too-many-locals

import pytest

from lib import base
from lib.constants import messages, objects, element
from lib.constants.element import AssessmentStates, ObjectStates
from lib.constants.element import Lhn, MappingStatusAttrs
from lib.entities import entities_factory, entity
from lib.entities.entity import Representation
from lib.factory import get_cls_webui_service, get_cls_rest_service
from lib.page import dashboard
from lib.service import webui_service
from lib.utils import selenium_utils
from lib.utils.filter_utils import FilterUtils


class TestSnapshots(base.Test):
  """Tests for snapshot functionality."""

  @classmethod
  def check_ggrc_1773(cls, is_updateable_condition,
                      is_control_updateable_actual):
    """Particular check if issue in app exist or not according to GGRC-1773."""
    cls.check_xfail_or_fail(
        is_condition=is_updateable_condition,
        issue_msg="Issue in app GGRC-1773",
        assert_msg=("\nis_control_updateable:\n" +
                    messages.AssertionMessages.format_err_msg_equal(
                        True, is_control_updateable_actual)))

  @pytest.fixture(scope="function")
  def lhn_menu(self, selenium):
    """Open LHN menu and return LHN page objects model."""
    selenium_utils.open_url(selenium, dashboard.Dashboard.URL)
    return dashboard.Dashboard(selenium).open_lhn_menu()

  @pytest.fixture(scope="function")
  def create_audit_and_update_first_of_two_original_controls(
      self, create_audit_with_control_and_update_control,
      new_control_rest, map_new_program_rest_to_new_control_rest
  ):
    """Create Audit with snapshotable Control and update original Control under
    Program via REST API. After that create second Control and map it to
    Program via REST API.
    Preconditions:
    - Execution and return of fixture
      'create_audit_with_control_and_update_control'.
    - Second Control created via REST API.
    - Second Control mapped to Program via REST API.
    """
    audit_with_one_control = create_audit_with_control_and_update_control
    return {
        "audit": audit_with_one_control["new_audit_rest"][0],
        "program": audit_with_one_control["new_program_rest"][0],
        "control": audit_with_one_control["new_control_rest"][0],
        "updated_control": audit_with_one_control["update_control_rest"][0],
        "second_control": new_control_rest
    }

  @pytest.mark.smoke_tests
  def test_audit_contains_readonly_ver_of_control(
      self, create_audit_with_control, selenium
  ):
    """Check via UI that Audit contains read-only snapshotable Control.
    Preconditions:
    - Program, Control created via REST API.
    - Control mapped to Program via REST API.
    - Audit created under Program via REST API.
    """
    audit_with_one_control = create_audit_with_control
    audit = audit_with_one_control["new_audit_rest"][0]
    control = audit_with_one_control["new_control_rest"][0]
    controls_ui_service = webui_service.ControlsService(selenium)
    actual_controls_tab_count = controls_ui_service.get_count_objs_from_tab(
        src_obj=audit)
    assert len([control]) == actual_controls_tab_count
    is_control_editable = controls_ui_service.is_obj_editable_via_info_panel(
        src_obj=audit, obj=control)
    assert is_control_editable is False

  @pytest.mark.smoke_tests
  @pytest.mark.parametrize(
      ("dynamic_create_audit_with_control", "expected_control",
       "is_openable", "is_ggrc_1773"),
      [("create_audit_with_control_and_update_control",
        "new_control_rest", True, False),
       ("create_audit_with_control_and_delete_control",
        "new_control_rest", False, False),
       ("create_audit_with_control_with_cas_and_update_control_with_cas",
        "new_control_with_cas_rest", True, False),
       ("create_audit_with_control_with_cas_and_delete_cas_for_controls",
        "new_control_with_cas_rest", True, True)],
      ids=["Audit contains snapshotable Control after updating Control",
           "Audit contains snapshotable Control after deleting Control",
           "Audit contains snapshotable Control "
           "after updating Control with CAs",
           "Audit contains snapshotable Control "
           "after deleting CAs for Controls"],
      indirect=["dynamic_create_audit_with_control"])
  def test_audit_contains_snapshotable_control(
      self, new_cas_for_controls_rest, dynamic_create_audit_with_control,
      expected_control, is_openable, is_ggrc_1773, selenium
  ):
    """Test snapshotable Control and check via UI that:
    - Audit contains snapshotable Control after updating Control.
    - Audit contains snapshotable Control after deleting Control.
    - Audit contains snapshotable Control after updating Control with CAs.
    - "Audit contains snapshotable Control after deleting CAs of Control.
    Preconditions:
      Execution and return of dynamic fixtures used REST API:
    - 'new_cas_for_controls_rest' *(due to Issue in app GGRC-2344)
    - 'create_audit_with_control_and_update_control'.
    - 'create_audit_with_control_and_delete_control'.
    - 'create_audit_with_control_with_cas_and_update_control_with_cas'.
    - 'create_audit_with_control_with_cas_and_delete_cas_for_controls'.
    """
    audit_with_one_control = dynamic_create_audit_with_control
    audit = audit_with_one_control["new_audit_rest"][0]
    expected_control = audit_with_one_control[expected_control][0].repr_ui()
    controls_ui_service = webui_service.ControlsService(selenium)
    actual_controls_tab_count = controls_ui_service.get_count_objs_from_tab(
        src_obj=audit)
    assert len([expected_control]) == actual_controls_tab_count
    is_control_openable = controls_ui_service.is_obj_page_exist_via_info_panel(
        src_obj=audit, obj=expected_control)
    is_control_updateable = (
        controls_ui_service.is_obj_updateble_via_info_panel(
            src_obj=audit, obj=expected_control))
    actual_control = controls_ui_service.get_list_objs_from_info_panels(
        src_obj=audit, objs=expected_control)
    assert is_control_openable is is_openable
    is_updateable_condition = is_control_updateable is True
    if is_ggrc_1773:
      self.check_ggrc_1773(is_updateable_condition, is_control_updateable)
    else:
      assert is_updateable_condition
    # 'actual_control': created_at, updated_at, modified_by (None)
    self.general_equal_assert(
        expected_control, actual_control,
        "created_at", "updated_at", "modified_by", "custom_attributes")
    self.xfail_equal_assert(
        expected_control, actual_control,
        "Issue in app GGRC-2344", "custom_attributes")

  @pytest.mark.smoke_tests
  @pytest.mark.parametrize(
      ("dynamic_create_audit_with_control", "control", "expected_control",
       "is_openable", "is_ggrc_1773"),
      [("create_audit_with_control_and_update_control",
        "new_control_rest", "update_control_rest", True, False),
       ("create_audit_with_control_and_delete_control",
        "new_control_rest", "new_control_rest", False, False),
       ("create_audit_with_control_with_cas_and_update_control_with_cas",
        "new_control_with_cas_rest", "update_control_with_cas_rest",
        True, False),
       ("create_audit_with_control_with_cas_and_delete_cas_for_controls",
        "new_control_with_cas_rest", "new_control_with_cas_rest",
        False, True)],
      ids=["Update snapshotable Control to latest ver after updating Control",
           "Update snapshotable Control to latest ver after deleting Control",
           "Update snapshotable Control to latest ver "
           "after updating Control with CAs",
           "Update snapshotable Control to latest ver "
           "after deleting CAs for Controls"],
      indirect=["dynamic_create_audit_with_control"])
  def test_update_snapshotable_control_to_latest_ver(
      self, new_cas_for_controls_rest, dynamic_create_audit_with_control,
      control, expected_control, is_openable, is_ggrc_1773, selenium
  ):
    """Test snapshotable Control and check via UI that:
    - Update snapshotable Control to latest ver after updating Control.
    - Update snapshotable Control to latest ver after deleting Control.
    - Update snapshotable Control to latest ver
    after updating Control with CAs.
    - Update snapshotable Control to latest ver
    after deleting CAs of Control.
    Preconditions:
      Execution and return of dynamic fixtures used REST API:
    - 'new_cas_for_controls_rest' *(due to Issue in app GGRC-2344)
    - 'create_audit_with_control_and_update_control'.
    - 'create_audit_with_control_and_delete_control'.
    - 'create_audit_with_control_with_cas_and_update_control_with_cas'.
    - 'create_audit_with_control_with_cas_and_delete_cas_for_controls'.
    """
    audit_with_one_control = dynamic_create_audit_with_control
    audit = audit_with_one_control["new_audit_rest"][0]
    control = audit_with_one_control[control][0]
    expected_control = audit_with_one_control[expected_control][0].repr_ui()
    controls_ui_service = webui_service.ControlsService(selenium)
    actual_controls_tab_count = controls_ui_service.get_count_objs_from_tab(
        src_obj=audit)
    assert len([expected_control]) == actual_controls_tab_count
    is_updateable_condition = (
        controls_ui_service.is_obj_updateble_via_info_panel(
            src_obj=audit, obj=control))
    if is_ggrc_1773:
      self.check_ggrc_1773(is_updateable_condition, is_updateable_condition)
    controls_ui_service.update_obj_ver_via_info_panel(
        src_obj=audit, obj=control)
    is_control_openable = controls_ui_service.is_obj_page_exist_via_info_panel(
        src_obj=audit, obj=expected_control)
    is_control_updateable = (
        controls_ui_service.is_obj_updateble_via_info_panel(
            src_obj=audit, obj=expected_control))
    actual_control = controls_ui_service.get_list_objs_from_info_panels(
        src_obj=audit, objs=expected_control)
    assert is_control_openable is is_openable
    assert is_control_updateable is False
    # 'actual_control': created_at, updated_at, modified_by (None)
    self.general_equal_assert(
        expected_control, actual_control,
        "created_at", "updated_at", "modified_by", "custom_attributes")
    self.xfail_equal_assert(
        expected_control, actual_control,
        "Issue in app GGRC-2344", "custom_attributes")

  @pytest.mark.smoke_tests
  def test_mapped_to_program_controls_does_not_added_to_existing_audit(
      self, create_audit_and_update_first_of_two_original_controls, selenium
  ):
    """Check via UI that Audit contains snapshotable Control that equal to
    original Control does not contain Control that was mapped to
    Program after Audit creation.
    Preconditions:
    - Execution and return of fixture
      'create_audit_and_update_first_of_two_original_controls'.
    """
    audit_with_two_controls = (
        create_audit_and_update_first_of_two_original_controls)
    audit = audit_with_two_controls["audit"]
    expected_control = audit_with_two_controls["control"].repr_ui()
    controls_ui_service = webui_service.ControlsService(selenium)
    actual_controls_tab_count = controls_ui_service.get_count_objs_from_tab(
        src_obj=audit)
    assert len([expected_control]) == actual_controls_tab_count
    actual_controls = controls_ui_service.get_list_objs_from_tree_view(
        src_obj=audit)
    # 'actual_controls': created_at, updated_at, custom_attributes (None)
    self.general_equal_assert(
        [expected_control], actual_controls,
        *Representation.tree_view_attrs_to_exclude)

  @pytest.mark.smoke_tests
  def test_bulk_update_audit_objects_to_latest_ver(
      self, create_audit_and_update_first_of_two_original_controls, selenium
  ):
    """Check via UI that Audit contains snapshotable Controls that up-to-date
    with their actual states after bulk updated audit objects
    to latest version.
    Preconditions:
    - Execution and return of fixture
      'create_audit_and_update_first_of_two_original_controls'.
    """
    audit_with_two_controls = (
        create_audit_and_update_first_of_two_original_controls)
    audit = audit_with_two_controls["audit"]
    expected_controls = [expected_control.repr_ui() for expected_control
                         in [audit_with_two_controls["updated_control"],
                             audit_with_two_controls["second_control"]]]
    (webui_service.AuditsService(selenium).
     bulk_update_via_info_page(audit_obj=audit))
    controls_ui_service = webui_service.ControlsService(selenium)
    actual_controls_tab_count = controls_ui_service.get_count_objs_from_tab(
        src_obj=audit)
    assert len(expected_controls) == actual_controls_tab_count
    actual_controls = controls_ui_service.get_list_objs_from_tree_view(
        src_obj=audit)
    # 'actual_controls': created_at, updated_at, custom_attributes (None)
    self.general_equal_assert(
        expected_controls, actual_controls,
        *Representation.tree_view_attrs_to_exclude)

  @pytest.mark.smoke_tests
  @pytest.mark.parametrize("tab_name", [Lhn.ALL_OBJS, Lhn.MY_OBJS])
  @pytest.mark.parametrize(
      "version_of_ctrl, is_found",
      [("new_control_rest", False), ("update_control_rest", True)],
      ids=["Snapshoted version is not found",
           "Actual snapshotable control is presented"])
  def test_search_snapshots_in_lhn(
      self, create_audit_with_control_and_update_control, version_of_ctrl,
      is_found, tab_name, lhn_menu
  ):
    """Check via UI that LHN search not looking for snapshots."""
    audit_with_one_control = create_audit_with_control_and_update_control
    lhn_menu.select_tab(tab_name)
    expected_control_title = audit_with_one_control[version_of_ctrl][0].title
    lhn_menu.filter_query(expected_control_title)
    actual_controls = (lhn_menu.select_controls_or_objectives().
                       select_controls().members_visible)
    actual_controls_titles = [act_ctrl.text for act_ctrl in actual_controls]
    assert is_found is (expected_control_title in actual_controls_titles), (
        messages.AssertionMessages.format_err_msg_contains(
            expected_control_title, actual_controls_titles))

  @pytest.mark.smoke_tests
  @pytest.mark.parametrize(
      "version_of_ctrl, is_found",
      [("new_control_rest", True), ("update_control_rest", False)],
      ids=["Snapshoted version is filtered",
           "Actual snapshotable Control is not filtered"])
  def test_filter_of_snapshotable_control(
      self, create_audit_with_control_and_update_control, version_of_ctrl,
      is_found, selenium
  ):
    """Check via UI that filtering work for snapshoted version of Control only,
    filtering by actual values returns no items in scope of Audit page.
    """
    audit_with_one_control = create_audit_with_control_and_update_control
    audit = audit_with_one_control["new_audit_rest"][0]
    expected_control = audit_with_one_control[version_of_ctrl][0].repr_ui()
    filter_exp = FilterUtils.get_filter_exp_by_title(expected_control.title)
    actual_controls = (webui_service.ControlsService(selenium).
                       filter_and_get_list_objs_from_tree_view(
                           src_obj=audit, filter_exp=filter_exp))
    # 'actual_controls': created_at, updated_at, custom_attributes (None)
    expected_controls, actual_controls = entity.Entity.extract_objs(
        [expected_control], actual_controls,
        *Representation.tree_view_attrs_to_exclude)
    expected_control = expected_controls[0]
    assert is_found is (expected_control in actual_controls), (
        messages.AssertionMessages.format_err_msg_contains(
            expected_control, actual_controls))

  @pytest.mark.smoke_tests
  @pytest.mark.parametrize(
      "control_for_mapper, control_for_tree_view, dynamic_objects, "
      "dynamic_relationships, expected_map_statuses, expected_is_found",
      [("new_control_rest", "update_control_rest", "new_audit_rest",
        None, (True, True), False),
       ("update_control_rest", "update_control_rest", "new_audit_rest",
        None, (True, True), True),
       ("new_control_rest", None, "new_assessment_rest",
        None, (False, False), True),
       ("update_control_rest", None, "new_assessment_rest",
        None, (False, False), False),
       ("new_control_rest", None, "new_issue_rest",
        "map_new_audit_rest_to_new_issue_rest", (False, False), False),
       ("update_control_rest", None, "new_issue_rest",
        "map_new_audit_rest_to_new_issue_rest", (False, False), True)],
      ids=["Mapper: snapshoted version is not found for new Audit "
           "which based on Program w' updated Control; "
           "Tree View: snapshotable Control is mapped to new Audit.",
           "Mapper: Actual snapshotable Control is found and mapped to new "
           "Audit which based on Program w' updated Control; "
           "Tree View: snapshotable Control is mapped to new Audit.",
           "Mapper: Snapshoted version is found for Assessment "
           "which created in Audit scope; "
           "Tree View: Assessment doesn't contain Controls.",
           "Mapper: Actual snapshotable Control is not found for Assessment "
           "which created in Audit scope; "
           "Tree View: Assessment doesn't contain Controls.",
           "Mapper: Snapshoted version is not found for standalone Issue "
           "which mapped to Audit; "
           "Tree View: Issue doesn't contain Controls.",
           "Mapper: Actual version of Control found for standalone Issue "
           "which mapped to Audit; "
           "Tree View: Issue doesn't contain Controls."],
      indirect=["dynamic_objects", "dynamic_relationships"])
  def test_search_unified_mapper_and_check_mapping(
      self, create_audit_with_control_and_update_control, control_for_mapper,
      control_for_tree_view, dynamic_objects, dynamic_relationships,
      expected_map_statuses, expected_is_found, selenium
  ):
    """Check searching of shapshotable and snapshoted objects via Unified
    Mapper modal and check their correct mapping.
    """
    audit_with_one_control = create_audit_with_control_and_update_control
    source_obj = dynamic_objects
    expected_control_from_mapper = (
        audit_with_one_control[control_for_mapper][0].repr_ui())
    expected_control_from_tree_view = (
        (expected_control_from_mapper
         if control_for_mapper == control_for_tree_view else
         audit_with_one_control[control_for_tree_view][0].repr_ui())
        if control_for_tree_view else None)
    expected_map_status = MappingStatusAttrs(
        expected_control_from_mapper.title, *expected_map_statuses)
    controls_ui_service = webui_service.ControlsService(driver=selenium)
    actual_controls_from_mapper, actual_map_status = (
        controls_ui_service.get_list_objs_from_mapper(
            src_obj=source_obj, dest_objs=[expected_control_from_mapper]))
    actual_controls_from_tree_view = (
        controls_ui_service.get_list_objs_from_tree_view(src_obj=source_obj))
    # 'actual_controls': created_at, updated_at, custom_attributes (None)
    expected_controls_from_mapper, actual_controls_from_mapper = (
        entity.Entity.extract_objs(
            [expected_control_from_mapper], actual_controls_from_mapper,
            *Representation.tree_view_attrs_to_exclude))
    expected_controls_from_tree_view = []
    if expected_control_from_tree_view:
      expected_controls_from_tree_view, actual_controls_from_tree_view = (
          entity.Entity.extract_objs(
              [expected_control_from_tree_view],
              actual_controls_from_tree_view,
              *Representation.tree_view_attrs_to_exclude))
    assert (
        expected_is_found
        is (expected_controls_from_mapper[0] in actual_controls_from_mapper)
        is (expected_map_status in actual_map_status)) == (
        (expected_controls_from_tree_view[0] in actual_controls_from_tree_view)
        if expected_control_from_tree_view else
        expected_controls_from_tree_view ==
        actual_controls_from_tree_view), (
        messages.AssertionMessages.format_err_msg_equal(
            messages.AssertionMessages.format_err_msg_contains(
                expected_controls_from_mapper[0], actual_controls_from_mapper),
            messages.AssertionMessages.format_err_msg_contains(
                expected_controls_from_tree_view[0],
                actual_controls_from_tree_view)
            if expected_control_from_tree_view else
            messages.AssertionMessages.format_err_msg_equal(
                expected_controls_from_tree_view,
                actual_controls_from_tree_view)))

  @pytest.mark.smoke_tests
  def test_mapping_control_to_existing_audit(
      self, new_program_rest, new_audit_rest, new_control_rest, selenium
  ):
    """Check if Control can be mapped to existing Audit and mapping
    between Control and Program of this Audit automatically created.
    Preconditions:
    - Audit and program, and different control created via REST API
    """
    # 'actual_controls': created_at, updated_at, custom_attributes (None)
    expected_control = entity.Entity.extract_objs_wo_excluded_attrs(
        [new_control_rest.repr_ui()],
        *Representation.tree_view_attrs_to_exclude)[0]
    controls_ui_service = webui_service.ControlsService(selenium)
    controls_ui_service.map_objs_via_tree_view(
        src_obj=new_audit_rest, dest_objs=[new_control_rest])
    actual_controls_count_in_tab_audit = (
        controls_ui_service.get_count_objs_from_tab(src_obj=new_audit_rest))
    actual_controls_in_audit = (
        controls_ui_service.get_list_objs_from_tree_view(
            src_obj=new_audit_rest))
    actual_controls_count_in_tab_program = (
        controls_ui_service.get_count_objs_from_tab(src_obj=new_program_rest))
    actual_controls_in_program = (
        controls_ui_service.get_list_objs_from_tree_view(
            src_obj=new_program_rest))
    assert (len([expected_control]) == actual_controls_count_in_tab_audit ==
            actual_controls_count_in_tab_program)
    assert ([expected_control] == actual_controls_in_audit ==
            actual_controls_in_program), (
        messages.AssertionMessages.format_err_msg_equal(
            messages.AssertionMessages.format_err_msg_equal(
                [expected_control], actual_controls_in_audit),
            messages.AssertionMessages.format_err_msg_equal(
                [expected_control], actual_controls_in_program)))

  @pytest.mark.smoke_tests
  def test_snapshot_cannot_be_unmapped_from_audit(
      self, create_audit_with_control, selenium
  ):
    """Check Snapshot cannot be unmapped from audit using "Unmap" button on
    info panel.
    Check that snapshot cannot be mapped from tree-view using "Map to this
    object" button.
    Preconditions:
    - Audit with mapped Control Snapshot created via REST API
    """
    audit_with_one_control = create_audit_with_control
    audit = audit_with_one_control["new_audit_rest"][0]
    control = audit_with_one_control["new_control_rest"][0]
    controls_ui_service = webui_service.ControlsService(selenium)
    is_mappable_on_tree_view_item = (
        controls_ui_service.is_obj_mappable_via_tree_view(audit, control))
    is_unmappable_on_info_panel = (
        controls_ui_service.
        is_obj_unmappable_via_info_panel(src_obj=audit, obj=control))
    assert (False
            is is_mappable_on_tree_view_item is is_unmappable_on_info_panel)

  @pytest.mark.smoke_tests
  @pytest.mark.parametrize(
      "control_for_mapper, dynamic_objects, dynamic_relationships",
      [pytest.mark.skip(
          reason="todo: Redesign test according to business requirements")(
          ("update_control_rest", "new_audit_rest", None)),
       ("new_control_rest", "new_assessment_rest", None),
       pytest.mark.skip(
           reason="todo: Redesign test according to business requirements")(
           ("new_control_rest", ["new_assessment_rest", "new_issue_rest"],
            "map_new_assessment_rest_to_new_control_rest_snapshot"))],
      indirect=["dynamic_objects", "dynamic_relationships"])
  def test_mapping_of_objects_to_snapshots_via_map_btn(
      self, create_audit_with_control_and_update_control, control_for_mapper,
      dynamic_objects, dynamic_relationships, selenium
  ):
    """Check mapping of objects to Control's snapshots via UI using Unified
    Mapper functionality (map button):
    - Audits: using auto-mapping in Program's scope;
    - Assessments: using Audit's scope;
    - Issues: using auto-mapping in Assessment's with mapped snapshoted object
              scope.
    """
    audit_with_one_control = create_audit_with_control_and_update_control
    source_obj = dynamic_objects
    expected_control = audit_with_one_control[control_for_mapper][0].repr_ui()
    controls_ui_service = webui_service.ControlsService(selenium)
    controls_ui_service.map_objs_via_tree_view(
        src_obj=source_obj, dest_objs=[expected_control])
    actual_controls_count_in_tab = (
        controls_ui_service.get_count_objs_from_tab(src_obj=source_obj))
    actual_controls = (
        controls_ui_service.get_list_objs_from_tree_view(source_obj))
    assert len([expected_control]) == actual_controls_count_in_tab
    # 'actual_controls': created_at, updated_at, custom_attributes (None)
    self.general_equal_assert(
        [expected_control], actual_controls,
        *Representation.tree_view_attrs_to_exclude)

  @pytest.mark.smoke_tests
  @pytest.mark.parametrize(
      "control_for_mapper, dynamic_objects, dynamic_relationships",
      [pytest.mark.skip(
          reason="todo: Redesign test according to business requirements")(
          ("update_control_rest", "new_audit_rest", None)),
       ("new_control_rest", "new_assessment_rest", None),
       pytest.mark.skip(
           reason="todo: Redesign test according to business requirements")(
           ("new_control_rest", ["new_assessment_rest", "new_issue_rest"],
            "map_new_assessment_rest_to_new_control_rest_snapshot"))],
      indirect=["dynamic_objects", "dynamic_relationships"])
  def test_mapping_of_objects_to_snapshots_via_tree_view(
      self, create_audit_with_control_and_update_control, control_for_mapper,
      dynamic_objects, dynamic_relationships, selenium
  ):
    """Check mapping of objects to Control's snapshots via UI using Unified
    Mapper functionality (Tree View element's dropdown):
    - Audits: using auto-mapping in Program's scope;
    - Assessments: using Audit's scope;
    - Issues: using auto-mapping in Assessment's with mapped snapshoted object
              scope.
    """
    audit_with_one_control = create_audit_with_control_and_update_control
    expected_control = audit_with_one_control[control_for_mapper][0].repr_ui()
    audit = audit_with_one_control["new_audit_rest"][0]
    existing_obj = dynamic_objects
    (get_cls_webui_service(objects.get_plural(existing_obj.type))(selenium).
        map_objs_via_tree_view_item(
        src_obj=audit, dest_objs=[expected_control]))
    controls_ui_service = get_cls_webui_service(
        objects.get_plural(expected_control.type))(selenium)
    actual_controls_count = controls_ui_service.get_count_objs_from_tab(
        src_obj=existing_obj)
    actual_controls = (controls_ui_service.get_list_objs_from_tree_view(
        src_obj=existing_obj))
    assert len([expected_control]) == actual_controls_count
    # 'actual_controls': created_at, updated_at, custom_attributes (None)
    self.general_equal_assert(
        [expected_control], actual_controls,
        *Representation.tree_view_attrs_to_exclude)

  @pytest.mark.smoke_tests
  @pytest.mark.parametrize(
      "dynamic_objects, dynamic_relationships",
      [(None, None),
       (["new_assessment_rest", "new_issue_rest"],
        ["map_new_assessment_rest_to_new_control_rest_snapshot",
         "map_new_assessment_rest_to_new_issue_rest"]),
       pytest.mark.xfail(reason="Issue GGRC-1909", strict=True)(
           ("new_assessment_rest",
            "map_new_assessment_rest_to_new_control_rest_snapshot"))],
      ids=["Export of snapshoted Control from Audit's Info Page "
           "via mapped Controls' Tree View",
           "Export of snapshoted Control from Issue's Info Page "
           "via mapped Controls' Tree View",
           "Export of snapshoted Control from Assessment's Info Page "
           "via mapped Controls' Tree View"],
      indirect=True)
  def test_export_of_snapshoted_control_from_src_objs_pages_via_tree_view(
      self, create_tmp_dir, create_audit_with_control_and_update_control,
      dynamic_objects, dynamic_relationships, selenium
  ):
    """Check if snapshoted Control can be exported from (Audit's, Issue's,
    Assessment's) Info Page via mapped Controls's Tree View.
    Preconditions:
    - Execution and return of fixtures:
      - 'create_tmp_dir';
      - 'create_audit_and_update_first_of_two_original_controls'.
    Test parameters:
    - 'dynamic_objects';
    - 'dynamic_relationships'.
    """
    audit_with_one_control = create_audit_with_control_and_update_control
    is_issue_flow = (isinstance(dynamic_objects, dict) and
                     dynamic_objects.get("new_issue_rest") is not None)
    dynamic_objects = (
        (dynamic_objects["new_issue_rest"] if is_issue_flow else
         dynamic_objects) if dynamic_objects else
        audit_with_one_control["new_audit_rest"][0])
    expected_control = audit_with_one_control["new_control_rest"][0].repr_ui()
    export_ui_service = webui_service.BaseWebUiService(
        driver=selenium, obj_name=objects.get_plural(expected_control.type),
        is_versions_widget=is_issue_flow)
    export_ui_service.export_objs_via_tree_view(src_obj=dynamic_objects)
    actual_controls = export_ui_service.get_list_objs_from_csv(
        path_to_export_dir=create_tmp_dir)
    # 'actual_controls': created_at, updated_at,
    #                    custom_attributes (GGRC-2344) (None)
    self.general_equal_assert(
        [expected_control], actual_controls,
        *Representation.tree_view_attrs_to_exclude)

  @pytest.mark.smoke_tests
  @pytest.mark.parametrize(
      "dynamic_objects, expected_state",
      [("new_assessment_rest", element.BaseStates.IN_PROGRESS),
       pytest.mark.xfail(reason="Issue GGRC-1407", strict=True)(
          ("new_issue_rest", element.IssueStates.DRAFT))],
      indirect=["dynamic_objects"])
  def test_asmt_and_issue_mapped_to_origin_control(
      self, create_audit_with_control_and_update_control,
      dynamic_objects, expected_state, selenium
  ):
    """
    Check Assessment or Issue was mapped to origin control after mapping
    snapshot of control to Assessment or Issue.
    Test parameters:
      - check Assessment
      - check Issue
    """
    origin_control = create_audit_with_control_and_update_control[
        "update_control_rest"][0]
    snapshoted_control = create_audit_with_control_and_update_control[
        "new_control_rest"][0]
    expected_obj = (
        dynamic_objects.repr_ui().update_attrs(status=expected_state))
    (webui_service.ControlsService(selenium).map_objs_via_tree_view(
        src_obj=expected_obj, dest_objs=[snapshoted_control]))
    actual_objs = (get_cls_webui_service(
        objects.get_plural(expected_obj.type))(selenium).
        get_list_objs_from_tree_view(src_obj=origin_control))
    # 'actual_controls': created_at, updated_at, custom_attributes (None)
    exclude_attrs = Representation.tree_view_attrs_to_exclude
    if dynamic_objects.type == entities_factory.EntitiesFactory.obj_issue:
      exclude_attrs = exclude_attrs + ("objects_under_assessment", )
    self.general_equal_assert([expected_obj], actual_objs, *exclude_attrs)

  @pytest.mark.smoke_tests
  @pytest.mark.parametrize(
      "dynamic_objects, dynamic_object_state",
      [("new_assessment_rest", AssessmentStates.NOT_STARTED),
       ("new_assessment_rest", AssessmentStates.IN_PROGRESS),
       ("new_assessment_rest", AssessmentStates.READY_FOR_REVIEW),
       ("new_assessment_rest", AssessmentStates.COMPLETED),
       pytest.mark.xfail(reason="Issue GGRC-2817", strict=True)
          (("new_issue_rest", ObjectStates.DRAFT))],
      indirect=["dynamic_objects"])
  def test_snapshot_can_be_unmapped_from_assessment_or_issue(
      self, create_audit_with_control_and_update_control, dynamic_objects,
      selenium, dynamic_object_state
  ):
    """Check Snapshot can be unmapped from assessment using "Unmap" button on
    info panel.
    Test parameters:
      "Checking assessment"
      "Checking issue"
    Steps:
      - Create assessment
      - Map snapshoted control with assessment
      - Unmap snapshot from assessment
      - Make sure that assessment has no any mapped snapshots
    """
    # pylint: disable=misplaced-comparison-constant
    audit_with_one_control = create_audit_with_control_and_update_control
    control = audit_with_one_control["new_control_rest"][0].repr_ui()
    audit = audit_with_one_control["new_audit_rest"][0]
    existing_obj = dynamic_objects
    existing_obj_name = objects.get_plural(existing_obj.type)
    (get_cls_webui_service(existing_obj_name)(selenium).
        map_objs_via_tree_view_item(src_obj=audit, dest_objs=[control]))
    controls_ui_service = (
        get_cls_webui_service(objects.get_plural(control.type))(selenium))
    (get_cls_rest_service(existing_obj_name)().
        update_obj(obj=existing_obj, status=dynamic_object_state))
    controls_ui_service.unmap_via_info_panel(existing_obj, control)
    actual_controls_count = controls_ui_service.get_count_objs_from_tab(
        src_obj=existing_obj)
    actual_controls = (controls_ui_service.get_list_objs_from_tree_view(
        src_obj=existing_obj))
    assert 0 == actual_controls_count
    assert [] == actual_controls

  @pytest.mark.skip(
      reason="todo: Redesign tests according to business requirements")
  @pytest.mark.smoke_tests
  @pytest.mark.parametrize(
      "dynamic_objects",
      ["new_audit_rest", "new_assessment_rest", "new_issue_rest"],
      indirect=True)
  def test_availability_mapping_of_objects_to_snapshotable_objs(
      self, create_audit_with_control_and_update_control, dynamic_objects,
      selenium
  ):
    """Check availability mapping of objects to Control's snapshots via UI
    using Unified Mapper functionality and AddWidget button on Horizontal
    Nav Bar.
    Steps:
      - Get list of available objects from HNB
      - Get list of available objects from Unified Mapper
      - Compare their with constant of snapshotable objects
    """
    mapped_audit = create_audit_with_control_and_update_control[
        'new_audit_rest'][0]
    obj_ui_service = get_cls_webui_service(
        objects.get_plural(dynamic_objects.type))(selenium)
    objs_types_from_mapper = (
        obj_ui_service.get_objs_available_to_map_via_mapper(
            src_obj=mapped_audit))
    objs_types_from_add_widget = (
        obj_ui_service.get_objs_available_to_map_via_add_widget(
            src_obj=dynamic_objects))
    expected_objs_types = sorted(
        objects.get_normal_form(snap_obj)
        for snap_obj in objects.ALL_SNAPSHOTABLE_OBJS)
    assert (expected_objs_types == objs_types_from_mapper ==
            objs_types_from_add_widget)
