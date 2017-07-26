# Copyright (C) 2017 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Snapshot smoke tests."""
# pylint: disable=no-self-use
# pylint: disable=invalid-name
# pylint: disable=unused-argument
# pylint: disable=too-many-arguments

import pytest

from lib import base
from lib.constants import messages, objects
from lib.constants.element import Lhn, MappingStatusAttrs
from lib.entities import entity
from lib.factory import get_ui_service
from lib.page import dashboard
from lib.service import webui_service
from lib.utils import selenium_utils
from lib.utils.filter_utils import FilterUtils


class TestSnapshots(base.Test):
  """Tests for snapshot functionality."""

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
    actual_controls_tab_count = (webui_service.ControlsService(selenium).
                                 get_count_objs_from_tab(src_obj=audit))
    assert len([control]) == actual_controls_tab_count
    is_control_editable = (
        webui_service.ControlsService(selenium).
        is_obj_editable_via_info_panel(src_obj=audit, obj=control))
    assert is_control_editable is False

  @pytest.mark.smoke_tests
  @pytest.mark.parametrize(
      ("dynamic_create_audit_with_control",
       "expected_control", "is_updateable", "is_openable"),
      [("create_audit_with_control_and_update_control",
        "new_control_rest", True, True),
       ("create_audit_with_control_and_delete_control",
        "new_control_rest", True, False),
       ("create_audit_with_control_with_cas_and_update_control_with_cas",
        "new_control_with_cas_rest", True, True),
       pytest.mark.xfail(strict=True)(
           ("create_audit_with_control_with_cas_and_delete_cas_for_controls",
            "new_control_with_cas_rest", True, True))],
      ids=["Audit contains snapshotable Control after updating Control",
           "Audit contains snapshotable Control after deleting Control",
           "Audit contains snapshotable Control "
           "after updating Control with CAs",
           "Audit contains snapshotable Control "
           "after deleting CAs for Controls"],
      indirect=["dynamic_create_audit_with_control"])
  def test_audit_contains_snapshotable_control(
      self, dynamic_create_audit_with_control, expected_control, is_updateable,
      is_openable, selenium
  ):
    """Test snapshotable Control and check via UI that:
    - Audit contains snapshotable Control after updating Control.
    - Audit contains snapshotable Control after deleting Control.
    - Audit contains snapshotable Control after updating Control with CAs.
    - "Audit contains snapshotable Control after deleting CAs of Control.
    Preconditions:
      Execution and return of dynamic fixtures used REST API:
    - 'create_audit_with_control_and_update_control'.
    - 'create_audit_with_control_and_delete_control'.
    - 'create_audit_with_control_with_cas_and_update_control_with_cas'.
    - 'create_audit_with_control_with_cas_and_delete_cas_for_controls'.
    """
    audit_with_one_control = dynamic_create_audit_with_control
    audit = audit_with_one_control["new_audit_rest"][0]
    # due to 'actual_control.os_state = None',
    #        'actual_control.updated_at = None'
    expected_control = (audit_with_one_control[expected_control][0].repr_ui().
                        update_attrs(os_state=None, updated_at=None))
    actual_controls_tab_count = (webui_service.ControlsService(selenium).
                                 get_count_objs_from_tab(src_obj=audit))
    assert len([expected_control]) == actual_controls_tab_count
    is_control_updateable = (
        webui_service.ControlsService(selenium).
        is_obj_updateble_via_info_panel(src_obj=audit, obj=expected_control))
    is_control_openable = (
        webui_service.ControlsService(selenium).
        is_obj_page_exist_via_info_panel(src_obj=audit, obj=expected_control))
    actual_control = (
        webui_service.ControlsService(selenium).
        get_list_objs_from_info_panels(src_obj=audit, objs=expected_control))
    assert is_control_openable is is_openable
    assert (True if is_control_updateable is is_updateable else
            pytest.xfail(reason="Issue in app GGRC-1773"))
    entity.Entity.issue_assert(
        expected_objs=expected_control, actual_objs=actual_control,
        issue_msg="Issue in app GGRC-2344", custom_attributes={None: None})

  @pytest.mark.smoke_tests
  @pytest.mark.parametrize(
      ("dynamic_create_audit_with_control",
       "control", "expected_control", "is_updateable", "is_openable"),
      [("create_audit_with_control_and_update_control",
        "new_control_rest", "update_control_rest", False, True),
       ("create_audit_with_control_and_delete_control",
        "new_control_rest", "new_control_rest", False, False),
       ("create_audit_with_control_with_cas_and_update_control_with_cas",
        "new_control_with_cas_rest", "update_control_with_cas_rest",
        False, True),
       pytest.mark.xfail(strict=True)(
           ("create_audit_with_control_with_cas_and_delete_cas_for_controls",
            "new_control_with_cas_rest", "new_control_with_cas_rest",
            False, False))],
      ids=["Update snapshotable Control to latest ver after updating Control",
           "Update snapshotable Control to latest ver after deleting Control",
           "Update snapshotable Control to latest ver "
           "after updating Control with CAs",
           "Update snapshotable Control to latest ver "
           "after deleting CAs for Controls"],
      indirect=["dynamic_create_audit_with_control"])
  def test_update_snapshotable_control_to_latest_ver(
      self, dynamic_create_audit_with_control, control, expected_control,
      is_updateable, is_openable, selenium
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
    - 'create_audit_with_control_and_update_control'.
    - 'create_audit_with_control_and_delete_control'.
    - 'create_audit_with_control_with_cas_and_update_control_with_cas'.
    - 'create_audit_with_control_with_cas_and_delete_cas_for_controls'.
    """
    audit_with_one_control = dynamic_create_audit_with_control
    audit = audit_with_one_control["new_audit_rest"][0]
    control = audit_with_one_control[control][0]
    # due to 'actual_control.os_state = None',
    #        'actual_control.updated_at = None'
    expected_control = (audit_with_one_control[expected_control][0].repr_ui().
                        update_attrs(os_state=None, updated_at=None))
    is_control_updateable = (
        webui_service.ControlsService(selenium).
        is_obj_updateble_via_info_panel(src_obj=audit, obj=control))
    assert (True if is_control_updateable is True else
            pytest.xfail(reason="Issue in app GGRC-1773"))
    (webui_service.ControlsService(selenium).
     update_obj_ver_via_info_panel(src_obj=audit, obj=control))
    actual_controls_tab_count = (webui_service.ControlsService(selenium).
                                 get_count_objs_from_tab(src_obj=audit))
    assert len([expected_control]) == actual_controls_tab_count
    is_control_updateable = (
        webui_service.ControlsService(selenium).
        is_obj_updateble_via_info_panel(src_obj=audit, obj=expected_control))
    is_control_openable = (
        webui_service.ControlsService(selenium).
        is_obj_page_exist_via_info_panel(src_obj=audit, obj=expected_control))
    actual_control = (
        webui_service.ControlsService(selenium).
        get_list_objs_from_info_panels(src_obj=audit, objs=expected_control))
    assert is_control_openable is is_openable
    assert is_control_updateable is is_updateable
    entity.Entity.issue_assert(
        expected_objs=expected_control, actual_objs=actual_control,
        issue_msg="Issue in app GGRC-2344", custom_attributes={None: None})

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
    # due to 'actual_control.custom_attributes = {None: None}'
    expected_control = (audit_with_two_controls["control"].repr_ui().
                        update_attrs(custom_attributes={None: None}))
    actual_controls_tab_count = (webui_service.ControlsService(selenium).
                                 get_count_objs_from_tab(src_obj=audit))
    assert len([expected_control]) == actual_controls_tab_count
    actual_controls = (webui_service.ControlsService(selenium).
                       get_list_objs_from_tree_view(src_obj=audit))
    assert [expected_control] == actual_controls, (
        messages.AssertionMessages.
        format_err_msg_equal([expected_control], actual_controls))

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
    # due to 'actual_control.custom_attributes = {None: None}'
    expected_controls = [
        expected_control.repr_ui().update_attrs(custom_attributes={None: None})
        for expected_control in [audit_with_two_controls["updated_control"],
                                 audit_with_two_controls["second_control"]]]
    (webui_service.AuditsService(selenium).
     bulk_update_via_info_page(audit_obj=audit))
    actual_controls_tab_count = (webui_service.ControlsService(selenium).
                                 get_count_objs_from_tab(src_obj=audit))
    assert len(expected_controls) == actual_controls_tab_count
    actual_controls = (webui_service.ControlsService(selenium).
                       get_list_objs_from_tree_view(src_obj=audit))
    assert expected_controls == actual_controls, (
        messages.AssertionMessages.
        format_err_msg_equal(expected_controls, actual_controls))

  @pytest.mark.smoke_tests
  @pytest.mark.parametrize("tab_name", [Lhn.ALL_OBJS, Lhn.MY_OBJS])
  @pytest.mark.parametrize(
      "version_of_ctrl, is_found",
      [("new_control_rest", False), ("update_control_rest", True)],
      ids=["Snapshoted version is not found",
           "Actual snapshotable control is presented"])
  def test_search_snapshots_in_lhn(
      self, create_audit_with_control_and_update_control, selenium,
      version_of_ctrl, is_found, tab_name
  ):
    """Check via UI that LHN search not looking for snapshots."""
    audit_with_one_control = create_audit_with_control_and_update_control
    selenium_utils.open_url(selenium, dashboard.Dashboard.URL)
    lhn_menu = dashboard.Dashboard(selenium).open_lhn_menu()
    lhn_menu.select_tab(tab_name)
    control_title = audit_with_one_control[version_of_ctrl][0].title
    lhn_menu.filter_query(control_title)
    controls = (lhn_menu.select_controls_or_objectives().
                select_controls().members_visible)
    assert (control_title in [el.text for el in controls]) == is_found, (
        messages.AssertionMessages.
        format_err_msg_contains(control_title, [el.text for el in controls]))

  @pytest.mark.smoke_tests
  @pytest.mark.parametrize(
      "version_of_ctrl, is_found",
      [("new_control_rest", True), ("update_control_rest", False)],
      ids=["Snapshoted version is filtered",
           "Actual snapshotable control is not filtered"])
  def test_filter_of_snapshotable_control(
      self, create_audit_with_control_and_update_control, selenium,
      version_of_ctrl, is_found
  ):
    """Check via UI that filtering work for snapshoted version of Control only,
    filtering by actual values returns no items in scope of Audit page.
    """
    audit_with_one_control = create_audit_with_control_and_update_control
    audit = audit_with_one_control["new_audit_rest"][0]
    # due to 'actual_control.custom_attributes = {None: None}'
    expected_control = (audit_with_one_control[version_of_ctrl][0].repr_ui().
                        update_attrs(custom_attributes={None: None}))
    filter_exp = FilterUtils.get_filter_exp_by_title(expected_control.title)
    actual_controls = (
        webui_service.ControlsService(selenium).
        filter_list_objs_from_tree_view(src_obj=audit, filter_exp=filter_exp))
    assert (expected_control in
            [ctrls for ctrls in actual_controls]
            ) == is_found, (
        messages.AssertionMessages.
        format_err_msg_contains(
            expected_control, [ctrls for ctrls in actual_controls]))

  @pytest.mark.smoke_tests
  @pytest.mark.parametrize(
      "dynamic_object, map_status, version_of_ctrl, is_found",
      [("new_audit_rest", (True, True), "new_control_rest", False),
       ("new_issue_rest", (False, False), "new_control_rest", True),
       ("new_assessment_rest", (False, False), "new_control_rest", True),
       ("new_audit_rest", (True, True), "update_control_rest", True),
       ("new_issue_rest", (False, False), "update_control_rest", False),
       ("new_assessment_rest", (False, False), "update_control_rest", False)],
      ids=["Snapshoted version is not found for audit",
           "Snapshoted version is found for issue",
           "Snapshoted version is found for assessment",
           "Actual snapshotable control is found and already mapped to audit",
           "Actual snapshotable control is not found for issue",
           "Actual snapshotable control is not found to asmt"],
      indirect=["dynamic_object"])
  @pytest.mark.smoke_tests
  def test_search_unified_mapper(
      self, create_audit_with_control_and_update_control, dynamic_object,
      selenium, version_of_ctrl, is_found, map_status
  ):
    """Check Unified Mapper modal that Unified Mapper search not
    looking for snapshots for audit and search for Issues/Assessments.
    For audit check of snapshotable control showing control that is
    already mapped to audit. For Issues/Assessments origin of snapshotable
    control is not presented.
    Test parameters:
    "Snapshoted version is not found for audit"
    "Snapshoted version is found for issue"
    "Snapshoted version is found for assessment"
    "Actual snapshotable control is found and already mapped to audit"
    "Actual snapshotable control is not found for issue"
    "Actual snapshotable control is not found for asmt"
    """
    audit_with_one_control = create_audit_with_control_and_update_control
    source_obj = dynamic_object
    # due to 'actual_control.custom_attributes = {None: None}'
    expected_control = (audit_with_one_control[version_of_ctrl][0].repr_ui().
                        update_attrs(custom_attributes={None: None}))
    expected_map_status = MappingStatusAttrs(
        expected_control.title, *map_status)
    controls_service = webui_service.ControlsService(selenium)
    actual_controls, actual_map_status = (
        controls_service.get_list_objs_from_mapper(
            src_obj=source_obj, dest_objs=[expected_control]))
    assert (is_found
            is (expected_control in actual_controls)
            is (expected_map_status in actual_map_status)), (
        messages.AssertionMessages.
        format_err_msg_contains(expected_control, actual_controls))

  @pytest.mark.smoke_tests
  def test_mapping_control_to_existing_audit(
      self, new_program_rest, new_audit_rest, new_control_rest, selenium
  ):
    """Check if Control can be mapped to existing Audit and mapping
    between Control and Program of this Audit automatically created.
    Preconditions:
    - Audit and program, and different control created via REST API
    """
    # due to 'actual_control_in_audit.custom_attributes = {None: None}',
    #        'actual_control_in_program.custom_attributes = {None: None}'
    expected_control = (new_control_rest.repr_ui().
                        update_attrs(custom_attributes={None: None}))
    (webui_service.ControlsService(selenium).map_objs_via_tree_view(
        src_obj=new_audit_rest, dest_objs=[new_control_rest]))
    actual_controls_count_in_tab_audit = (
        webui_service.ControlsService(selenium).
        get_count_objs_from_tab(src_obj=new_audit_rest))
    actual_control_in_audit = (
        webui_service.ControlsService(selenium).
        get_list_objs_from_tree_view(src_obj=new_audit_rest))
    actual_controls_count_in_tab_program = (
        webui_service.ControlsService(selenium).
        get_count_objs_from_tab(src_obj=new_program_rest))
    actual_control_in_program = (
        webui_service.ControlsService(selenium).
        get_list_objs_from_tree_view(src_obj=new_program_rest))
    assert (len([expected_control]) ==
            actual_controls_count_in_tab_audit ==
            actual_controls_count_in_tab_program)
    assert ([expected_control] ==
            actual_control_in_audit ==
            actual_control_in_program), (
        messages.AssertionMessages.
        format_err_msg_equal(
            messages.AssertionMessages.
            format_err_msg_equal([expected_control], actual_control_in_audit),
            messages.AssertionMessages.
            format_err_msg_equal([expected_control], actual_control_in_program)
        ))

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
    is_mappable_on_tree_view_item = (
        webui_service.ControlsService(selenium).
        is_obj_mappable_via_tree_view(audit, control))
    is_unmappable_on_info_panel = (
        webui_service.ControlsService(selenium).
        is_obj_unmappable_via_info_panel(src_obj=audit, obj=control))
    assert (
        False is is_mappable_on_tree_view_item is is_unmappable_on_info_panel)

  @pytest.mark.smoke_tests
  @pytest.mark.parametrize(
      "dynamic_object",
      ["new_assessment_rest",
       "new_issue_rest"],
      indirect=["dynamic_object"])
  def test_mapping_of_assessments_and_issues_to_snapshots(
      self, create_audit_with_control_and_update_control, dynamic_object,
      selenium
  ):
    """Check mapping of assessments or issues to snapshot of control via
    info widget.
    Test parameters:
    "Checking assessment"
    "Checking issue"
    """
    # due to 'actual_control.custom_attributes = {None: None}'
    expected_control = (
        create_audit_with_control_and_update_control["new_control_rest"][0].
        repr_ui().update_attrs(custom_attributes={None: None}))
    source_obj = dynamic_object
    control_service = webui_service.ControlsService(selenium)
    control_service.map_objs_via_tree_view(src_obj=source_obj,
                                           dest_objs=[expected_control])
    actual_controls_count_in_tab = control_service.get_count_objs_from_tab(
        src_obj=source_obj)
    actual_controls = control_service.get_list_objs_from_tree_view(source_obj)
    assert len([expected_control]) == actual_controls_count_in_tab
    assert [expected_control] == actual_controls, (
        messages.AssertionMessages.
        format_err_msg_equal([expected_control], actual_controls))

  @pytest.mark.smoke_tests
  @pytest.mark.parametrize(
      "dynamic_object",
      ["new_assessment_rest",
       "new_issue_rest"],
      indirect=["dynamic_object"])
  def test_mapping_of_assessments_and_issues_to_snapshots_via_tree_view(
      self, create_audit_with_control_and_update_control, dynamic_object,
      selenium
  ):
    """Check mapping of assessments or issues to snapshot of control via
    tree view.
    Test parameters:
    "Checking assessment"
    "Checking issue"
    """
    audit_with_one_control = create_audit_with_control_and_update_control
    # due to 'actual_control.custom_attributes = {None: None}'
    expected_control = (
        audit_with_one_control["new_control_rest"][0].
        repr_ui().update_attrs(custom_attributes={None: None}))
    audit = audit_with_one_control["new_audit_rest"][0]
    existing_obj = dynamic_object
    existing_obj_service = get_ui_service(existing_obj.type)(selenium)
    (existing_obj_service.map_objs_via_tree_view_item(
        src_obj=audit, dest_objs=[expected_control]))
    controls_service = get_ui_service(expected_control.type)(selenium)
    actual_controls_count = controls_service.get_count_objs_from_tab(
        src_obj=existing_obj)
    actual_controls = (controls_service.get_list_objs_from_tree_view(
        src_obj=existing_obj))
    assert len([expected_control]) == actual_controls_count
    assert [expected_control] == actual_controls, (
        messages.AssertionMessages.
        format_err_msg_equal([expected_control], actual_controls))

  @pytest.mark.xfail(strict=True)
  @pytest.mark.smoke_tests
  @pytest.mark.parametrize(
      "dynamic_object, dynamic_relationships",
      [(None, None),
       ("new_issue_rest",
        "map_new_issue_rest_to_new_control_rest_snapshot"),
       pytest.mark.xfail(reason="Issue GGRC-1909", strict=True)(
           ("new_assessment_rest",
            "map_new_assessment_rest_to_new_control_rest_snapshot"))],
      ids=["Export of snapshoted Control from Audit's Info Page "
           "via mapped Controls' Tree View",
           "Export of snapshoted Control from Issue's Info Page "
           "via mapped Controls' Tree View",
           "Export of snapshoted Control from Assessment's Info Page "
           "via mapped Controls' Tree View"],
      indirect=["dynamic_object", "dynamic_relationships"])
  @pytest.mark.smoke_tests
  def test_export_of_snapshoted_control_from_src_objs_pages_via_tree_view(
      self, create_tmp_dir, create_audit_with_control_and_update_control,
      dynamic_object, dynamic_relationships, selenium
  ):
    """Check if snapshoted Control can be exported from (Audit's, Issue's,
    Assessment's) Info Page via mapped Controls's Tree View.
    Preconditions:
    - Execution and return of fixtures:
      - 'create_tmp_dir';
      - 'create_audit_and_update_first_of_two_original_controls'.
    Test parameters:
    - 'dynamic_object';
    - 'dynamic_relationships'.
    """
    audit_with_one_control = create_audit_with_control_and_update_control
    dynamic_object = (dynamic_object if dynamic_object
                      else audit_with_one_control["new_audit_rest"][0])
    # due to 'actual_control.custom_attributes = {None: None}'
    expected_control = (audit_with_one_control["new_control_rest"][0].
                        repr_ui().update_attrs(custom_attributes={None: None}))
    export_service = webui_service.BaseWebUiService(
        selenium, objects.get_plural(expected_control.type))
    export_service.export_objs_via_tree_view(src_obj=dynamic_object)
    actual_controls = export_service.get_list_objs_from_csv(
        path_to_export_dir=create_tmp_dir)
    entity.Entity.issue_assert(
        expected_objs=[expected_control], actual_objs=actual_controls,
        issue_msg="Issue in app GGRC-2750", owners={None: None})

  @pytest.mark.smoke_tests
  @pytest.mark.parametrize(
      "dynamic_object",
      ["new_assessment_rest",
       pytest.mark.xfail(reason="Issue GGRC-1407", strict=True)
          ("new_issue_rest")],
      indirect=["dynamic_object"])
  def test_asmt_and_issue_mapped_to_origin_control(
      self, create_audit_with_control_and_update_control,
      dynamic_object, selenium
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
    # due to 'actual_control.custom_attributes = {None: None}'
    expected_obj = (dynamic_object.repr_ui().update_attrs(
        custom_attributes={None: None}))
    expected_obj_service = get_ui_service(expected_obj.type)(selenium)
    (webui_service.ControlsService(selenium).map_objs_via_tree_view(
        src_obj=expected_obj, dest_objs=[snapshoted_control]))
    actual_objs = expected_obj_service.get_list_objs_from_tree_view(
        src_obj=origin_control)
    assert [expected_obj] == actual_objs, (
        messages.AssertionMessages.
        format_err_msg_equal(expected_obj, actual_objs))

  @pytest.mark.parametrize(
      "dynamic_object",
      ["new_assessment_rest",
       pytest.mark.xfail(reason="Issue GGRC-2817", strict=True)
          ("new_issue_rest")],
      indirect=["dynamic_object"])
  @pytest.mark.smoke_tests
  def test_snapshot_can_be_unmapped_from_assessment_or_issue(
      self, create_audit_with_control_and_update_control, dynamic_object,
      selenium
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
    # due to 'actual_control.custom_attributes = {None: None}'
    control = (
        audit_with_one_control["new_control_rest"][0].
        repr_ui().update_attrs(custom_attributes={None: None}))
    audit = audit_with_one_control["new_audit_rest"][0]
    existing_obj = dynamic_object
    existing_obj_service = get_ui_service(existing_obj.type)(selenium)
    (existing_obj_service.map_objs_via_tree_view_item(
        src_obj=audit, dest_objs=[control]))
    controls_service = get_ui_service(control.type)(selenium)
    controls_service.unmap_via_info_panel(existing_obj, control)
    actual_controls_count = controls_service.get_count_objs_from_tab(
        src_obj=existing_obj)
    actual_controls = (controls_service.get_list_objs_from_tree_view(
        src_obj=existing_obj))
    assert 0 == actual_controls_count
    assert [] == actual_controls
