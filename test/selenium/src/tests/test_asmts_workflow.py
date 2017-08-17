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
from lib.constants import roles
from lib.constants.element import AssessmentStates
from lib.entities import entities_factory
from lib.service import webui_service, rest_service


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
    self.extended_assert_w_excluded_attrs(expected_asmt, actual_asmt)

  @pytest.mark.smoke_tests
  def test_asmt_related_asmts(
      self, new_programs_rest, new_control_rest,
      map_new_control_rest_to_new_programs_rest, new_audits_rest,
      new_assessments_rest, selenium
  ):
    """Test for checking Related Assessments. Map two Assessments to one
    snapshot of control. And check second Assessment contains in "Related
    Assessments" Tab of first Assessment. 3 Titles will be compared:
    Assessment, Audit of Assessment, generic Control
    """
    expected_titles = [(new_assessments_rest[1].title,
                        new_control_rest.title,
                        new_audits_rest[1].title)]
    asmt_service = webui_service.AssessmentsService(selenium)
    asmt_service.map_objs_via_tree_view_item(
        src_obj=new_audits_rest[0], dest_objs=[new_control_rest])
    asmt_service.map_objs_via_tree_view_item(
        src_obj=new_audits_rest[1], dest_objs=[new_control_rest])
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
       "expected_initial_state", "expected_final_state"),
      [(("new_assessment_rest", {"status":
                                 AssessmentStates.NOT_STARTED}),
        "edit_obj_via_edit_modal_from_info_page",
        None, AssessmentStates.IN_PROGRESS),
       (("new_assessment_rest", {"status": AssessmentStates.NOT_STARTED,
                                 "verifier": [roles.DEFAULT_USER]}),
        "edit_obj_via_edit_modal_from_info_page",
        None, AssessmentStates.IN_PROGRESS),
       (("new_assessment_rest", {"status": AssessmentStates.IN_PROGRESS}),
        "edit_obj_via_edit_modal_from_info_page",
        None, AssessmentStates.IN_PROGRESS),
       (("new_assessment_rest", {"status": AssessmentStates.IN_PROGRESS,
                                 "verifier": [roles.DEFAULT_USER]}),
        "edit_obj_via_edit_modal_from_info_page",
        None, AssessmentStates.IN_PROGRESS),
       (("new_assessment_rest", {"status": AssessmentStates.IN_PROGRESS}),
        "edit_obj_via_edit_modal_from_info_page",
        AssessmentStates.COMPLETED, AssessmentStates.IN_PROGRESS),
       (("new_assessment_rest", {"status": AssessmentStates.IN_PROGRESS,
                                 "verifier": [roles.DEFAULT_USER]}),
        "edit_obj_via_edit_modal_from_info_page",
        AssessmentStates.COMPLETED, AssessmentStates.IN_PROGRESS),
       (("new_assessment_rest", {"status": AssessmentStates.NOT_STARTED}),
        "complete_assessment", None, AssessmentStates.COMPLETED),
       (("new_assessment_rest", {"status": AssessmentStates.NOT_STARTED,
                                 "verifier": [roles.DEFAULT_USER]}),
        "complete_assessment", None, AssessmentStates.READY_FOR_REVIEW),
       (("new_assessment_rest", {"status": AssessmentStates.IN_PROGRESS}),
        "complete_assessment", None, AssessmentStates.COMPLETED),
       (("new_assessment_rest", {"status": AssessmentStates.IN_PROGRESS,
                                 "verifier": [roles.DEFAULT_USER]}),
        "complete_assessment", None, AssessmentStates.READY_FOR_REVIEW),
       (("new_assessment_rest", {"status": AssessmentStates.IN_PROGRESS,
                                 "verifier": [roles.DEFAULT_USER]}),
        "verify_assessment",
        AssessmentStates.READY_FOR_REVIEW, AssessmentStates.COMPLETED),
       (("new_assessment_rest", {"status": AssessmentStates.IN_PROGRESS,
                                 "verifier": [roles.DEFAULT_USER]}),
        "reject_assessment",
        AssessmentStates.READY_FOR_REVIEW, AssessmentStates.IN_PROGRESS)],
      ids=["Edit asmt w'o verifier 'Not Started' - 'In Progress'",
           "Edit asmt w' verifier 'Not Started' - 'In Progress'",
           "Edit asmt w'o verifier 'In Progress' - 'In Progress'",
           "Edit asmt w' verifier 'In Progress' - 'In Progress'",
           "Edit asmt w'o verifier 'Completed' - 'In Progress'",
           "Edit asmt w' verifier 'Completed' - 'In Progress'",
           "Complete asmt w'o verifier 'Not Started' - 'Completed'",
           "Complete asmt w' verifier 'Not Started' - 'Ready for Review'",
           "Complete asmt w'o verifier 'In Progress' - 'Completed'",
           "Complete asmt w' verifier 'In Progress' - 'Ready for Review'",
           "Verify asmt w' verifier 'Ready for Review' - 'Completed'",
           "Reject asmt w' verifier 'Ready for Review' - 'In Progress'"],
      indirect=["dynamic_object_w_factory_params"])
  def test_check_asmt_state_change(
      self, new_program_rest, new_audit_rest, dynamic_object_w_factory_params,
      action, expected_initial_state, expected_final_state, selenium
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
    assessments_service = webui_service.AssessmentsService(selenium)
    getattr(assessments_service, action)(expected_asmt)
    actual_asmt = assessments_service.get_obj_from_info_page(expected_asmt)
    self.extended_assert_w_excluded_attrs(
        expected_asmt.update_attrs(status=expected_final_state.title(),
                                   title=actual_asmt.title,
                                   verified=actual_asmt.verified).repr_ui(),
        actual_asmt, "updated_at")
