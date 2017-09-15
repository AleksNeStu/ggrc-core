# Copyright (C) 2017 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Assessments Workflow smoke tests."""
# pylint: disable=no-self-use
# pylint: disable=invalid-name
# pylint: disable=unused-argument
# pylint: disable=too-few-public-methods
# pylint: disable=too-many-arguments

import pytest

from lib import base
from lib.constants import messages, roles, element, value_aliases as alias
from lib.constants.element import AssessmentStates
from lib.entities import entities_factory, entity
from lib.entities.entities_factory import CustomAttributeDefinitionsFactory
from lib.service import rest_service, webui_service
from lib.utils.filter_utils import FilterUtils


class TestAssessmentsWorkflow(base.Test):
  """Tests for Assessments Workflow functionality."""

  @pytest.mark.smoke_tests
  def test_add_comment_to_asmt_via_info_panel(
      self, new_program_rest, new_audit_rest, new_assessment_rest, selenium
  ):
    """Check via UI of possibility to correctly add comment to Assessment via
    Info Panel.
    Preconditions:
    - Program created via REST API.
    - Audit created under Program via REST API.
    - Assessment created under Audit via REST API.
    Test parameters: None
    """
    expected_asmt = new_assessment_rest
    expected_asmt_comments = [entities_factory.CommentsFactory().
                              create().repr_ui()]
    # due to 'actual_asmt.updated_at = None'
    (expected_asmt.
     update_attrs(comments=expected_asmt_comments, updated_at=None).repr_ui())
    assessments_service = webui_service.AssessmentsService(selenium)
    asmt_comments_panel = assessments_service.add_comments(
        src_obj=new_audit_rest, obj=expected_asmt,
        comment_objs=expected_asmt_comments)
    assert asmt_comments_panel.is_input_empty is True
    actual_asmt = (
        webui_service.AssessmentsService(selenium).
        get_list_objs_from_info_panels(
            src_obj=new_audit_rest, objs=expected_asmt).update_attrs(
            comments={"created_at": None}, is_replace_dicts_values=True))
    self.general_assert(expected_asmt, actual_asmt)

  @pytest.mark.smoke_tests
  def test_asmt_logs(
      self, new_program_rest, new_audit_rest, new_assessment_rest, selenium
  ):
    """Test for validation of Assessment log pane.
    Acceptance criteria:
      1) 3 log items at the log pane
      2) all items return 'True' for all attrs.
    """
    log_items_validation = webui_service.AssessmentsService(
        selenium).get_log_pane_validation_result(obj=new_assessment_rest)
    log_validation_results = [all(item_result.values()) for item_result in
                              log_items_validation]
    assert ([True] * 3) == log_validation_results, str(log_items_validation)

  @pytest.mark.smoke_tests
  def test_asmt_related_asmts(
      self, new_program_rest, new_control_rest,
      map_new_program_rest_to_new_control_rest, new_audit_rest,
      new_assessments_rest, selenium
  ):
    """Test for checking Related Assessments. Map two Assessments to one
    snapshot of control. And check second Assessment contains in "Related
    Assessments" Tab of first Assessment. 3 Titles will be compared:
    Assessment, Audit of Assessment, generic Control
    """
    expected_titles = [(new_assessments_rest[1].title,
                        new_control_rest.title,
                        new_audit_rest.title)]
    asmt_service = webui_service.AssessmentsService(selenium)
    asmt_service.map_objs_via_tree_view_item(
        src_obj=new_audit_rest, dest_objs=[new_control_rest])
    related_asmts_objs = (webui_service.AssessmentsService(
        selenium).get_related_asmts_titles(obj=new_assessments_rest[0]))
    assert expected_titles == related_asmts_objs

  @pytest.mark.smoke_tests
  def test_raise_issue(
      self, new_program_rest, new_audit_rest, new_assessment_rest, selenium
  ):
    """Test for checking raising Issues in Related Issues Tab. Open
    Related Issues tab on Assessments Info page. Raise Issue with pre-defined
    attributes via "raise issue" button. Compare expected Issue title and
    actual issue_titles.
    """
    expected_issue = (entities_factory.IssuesFactory().create().repr_ui())
    asmt_service = webui_service.AssessmentsService(selenium)
    asmt_service.raise_issue(new_assessment_rest, expected_issue)
    related_issues_titles = asmt_service.get_related_issues_titles(
        obj=new_assessment_rest)
    assert related_issues_titles == [expected_issue.title]

  @pytest.mark.smoke_tests
  @pytest.mark.parametrize(
      ("dynamic_object_w_factory_params", "action",
       "expected_initial_state", "expected_final_state", "expected_verified"),
      [(("new_assessment_rest", {"status":
                                 AssessmentStates.NOT_STARTED}),
        "edit_obj_via_edit_modal_from_info_page",
        None, AssessmentStates.IN_PROGRESS, False),
       (("new_assessment_rest", {"status": AssessmentStates.NOT_STARTED,
                                 "verifier": [roles.DEFAULT_USER]}),
        "edit_obj_via_edit_modal_from_info_page",
        None, AssessmentStates.IN_PROGRESS, False),
       (("new_assessment_rest", {"status": AssessmentStates.IN_PROGRESS}),
        "edit_obj_via_edit_modal_from_info_page",
        None, AssessmentStates.IN_PROGRESS, False),
       (("new_assessment_rest", {"status": AssessmentStates.IN_PROGRESS,
                                 "verifier": [roles.DEFAULT_USER]}),
        "edit_obj_via_edit_modal_from_info_page",
        None, AssessmentStates.IN_PROGRESS, False),
       (("new_assessment_rest", {"status": AssessmentStates.IN_PROGRESS}),
        "edit_obj_via_edit_modal_from_info_page",
        AssessmentStates.COMPLETED, AssessmentStates.IN_PROGRESS, False),
       (("new_assessment_rest", {"status": AssessmentStates.IN_PROGRESS,
                                 "verifier": [roles.DEFAULT_USER]}),
        "edit_obj_via_edit_modal_from_info_page",
        AssessmentStates.COMPLETED, AssessmentStates.IN_PROGRESS, False),
       (("new_assessment_rest", {"status": AssessmentStates.NOT_STARTED}),
        "complete_assessment", None, AssessmentStates.COMPLETED, False),
       (("new_assessment_rest", {"status": AssessmentStates.NOT_STARTED,
                                 "verifier": [roles.DEFAULT_USER]}),
        "complete_assessment", None, AssessmentStates.READY_FOR_REVIEW, False),
       (("new_assessment_rest", {"status": AssessmentStates.IN_PROGRESS}),
        "complete_assessment", None, AssessmentStates.COMPLETED, False),
       (("new_assessment_rest", {"status": AssessmentStates.IN_PROGRESS,
                                 "verifier": [roles.DEFAULT_USER]}),
        "complete_assessment", None, AssessmentStates.READY_FOR_REVIEW, False),
       (("new_assessment_rest", {"status": AssessmentStates.IN_PROGRESS,
                                 "verifier": [roles.DEFAULT_USER]}),
        "verify_assessment",
        AssessmentStates.READY_FOR_REVIEW, AssessmentStates.COMPLETED, True),
       (("new_assessment_rest", {"status": AssessmentStates.IN_PROGRESS,
                                 "verifier": [roles.DEFAULT_USER]}),
        "reject_assessment",
        AssessmentStates.READY_FOR_REVIEW, AssessmentStates.REWORK_NEEDED,
        False)],
      ids=["Edit asmt w'o verifier 'Not Started' - 'In Progress'",
           "Edit asmt w' verifier 'Not Started' - 'In Progress'",
           "Edit asmt w'o verifier 'In Progress' - 'In Progress'",
           "Edit asmt w' verifier 'In Progress' - 'In Progress'",
           "Edit asmt w'o verifier 'Completed' - 'In Progress'",
           "Edit asmt w' verifier 'Completed' - 'In Progress'",
           "Complete asmt w'o verifier 'Not Started' - 'Completed'",
           "Complete asmt w' verifier 'Not Started' - 'In Review'",
           "Complete asmt w'o verifier 'In Progress' - 'Completed'",
           "Complete asmt w' verifier 'In Progress' - 'In Review'",
           "Verify asmt w' verifier 'In Review' - 'Completed'",
           "Reject asmt w' verifier 'In Review' - 'Rework Needed'"],
      indirect=["dynamic_object_w_factory_params"])
  def test_check_asmt_state_change(
      self, new_program_rest, new_audit_rest, dynamic_object_w_factory_params,
      action, expected_initial_state, expected_final_state, expected_verified,
      selenium
  ):
    """Check Assessment workflow status change to correct state.
    Preconditions:
    - Program created via REST API.
    - Audit created under Program via REST API.
    - Assessment created and updated under Audit via REST API.
    """
    expected_asmt = dynamic_object_w_factory_params
    if expected_initial_state:
      (rest_service.AssessmentsService().
       update_obj(expected_asmt, status=expected_initial_state))
    asmts_ui_service = webui_service.AssessmentsService(selenium)
    getattr(asmts_ui_service, action)(expected_asmt)
    expected_asmt = (expected_asmt.update_attrs(
        title=(element.AssessmentInfoWidget.TITLE_EDITED_PART +
               expected_asmt.title if "edit" in action
               else expected_asmt.title),
        status=expected_final_state.title(),
        verified=expected_verified).repr_ui())
    actual_asmt = asmts_ui_service.get_obj_from_info_page(expected_asmt)
    # 'actual_asmt': updated_at (None)
    self.general_assert(expected_asmt, actual_asmt, "updated_at")

  @pytest.mark.parametrize("operator", [alias.EQUAL_OP, alias.CONTAINS_OP])
  @pytest.mark.smoke_tests
  def test_asmts_gcas_filtering(
      self, new_program_rest, new_audit_rest, new_cas_for_assessments_rest,
      new_assessments_rest, selenium, operator
  ):
    """Test for checking filtering of Assessment by Custom Attributes in
    audit scope.
    Preconditions:
    - Program created via REST API.
    - Audit created via REST API.
    - Assessments created via REST API.
    - Global Custom Attributes for Assessment created via REST API.
    - Set revers value of GCA with Checkbox type for second Assessment.
    """
    custom_attr_values = (
        CustomAttributeDefinitionsFactory().generate_ca_values(
            list_ca_def_objs=new_cas_for_assessments_rest))
    checkbox_id = entity.Entity.filter_objs_by_attrs(
        objs=new_cas_for_assessments_rest,
        attribute_type=element.AdminWidgetCustomAttributes.CHECKBOX).id
    expected_asmt = new_assessments_rest[0]
    (rest_service.AssessmentsService().update_obj(
        obj=expected_asmt, custom_attributes=custom_attr_values))
    (rest_service.AssessmentsService().update_obj(
        obj=new_assessments_rest[1],
        custom_attributes={checkbox_id: not custom_attr_values[checkbox_id]}))
    filter_exprs = FilterUtils().get_filter_exprs_by_cas(
        expected_asmt.custom_attribute_definitions, custom_attr_values,
        operator)
    # due to 'actual_asmt.custom_attributes = {None: None}'
    expected_asmt = expected_asmt.repr_ui().update_attrs(
        custom_attributes={None: None}, status=AssessmentStates.IN_PROGRESS)
    expected_results = [{"filter": filter_expr,
                         "objs": [expected_asmt]}
                        for filter_expr in filter_exprs]
    actual_results = [
        {"filter": filter_expr,
         "objs": webui_service.AssessmentsService(selenium).
         filter_and_get_list_objs_from_tree_view(new_audit_rest, filter_expr)}
        for filter_expr in filter_exprs]
    assert expected_results == actual_results, (
        messages.AssertionMessages.format_err_msg_equal(expected_results,
                                                        actual_results))

  @pytest.mark.parametrize(
      "dynamic_object, dynamic_relationships",
      [("new_objective_rest", "map_new_program_rest_to_new_objective_rest"),
       ("new_control_rest", "map_new_program_rest_to_new_control_rest")],
      indirect=True)
  def test_map_snapsots_to_asmt_via_edit_modal(
      self, new_program_rest, dynamic_object, dynamic_relationships,
      new_audit_rest, new_assessment_rest, selenium
  ):
    """Check Assessment can be mapped with snapshot via Modal Edit
    on Assessments Info Page. Additional check existing of mapped obj Titles
    on Modal Edit.
    Preconditions:
    - Program, dynamic_object created via REST API.
    - dynamic_object mapped to Program via REST API.
    - Audit created under Program via REST API.
    - Assessment created under audit via REST API.
    Test parameters:
    - 'dynamic_object'.
    - 'dynamic_relationships'.
    """
    expected_asmt = (new_assessment_rest.update_attrs(
        objects_under_assessment=[dynamic_object],
        status=AssessmentStates.IN_PROGRESS))
    expected_titles = [dynamic_object.title]
    actual_titles = (webui_service.AssessmentsService(selenium).
                     map_objs_and_get_mapped_titles_from_edit_modal(
                     expected_asmt, expected_asmt.objects_under_assessment))
    actual_asmt = (webui_service.AssessmentsService(selenium).
                   get_obj_from_info_page(expected_asmt))
    # due to GGRC-3157
    attrs_to_exclude = ["updated_at"]
    if actual_asmt.objects_under_assessment is None:
      attrs_to_exclude.append("objects_under_assessment")
    self.general_assert(
        expected_asmt.repr_ui(), actual_asmt, *attrs_to_exclude)
    assert expected_titles == actual_titles
    if "objects_under_assessment" in attrs_to_exclude:
      pytest.xfail(reason="GGRC-3157 Issue")
    else:
      pytest.fail(msg="GGRC-3157 Issue was fixed")
