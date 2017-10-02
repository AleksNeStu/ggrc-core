# Copyright (C) 2017 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Audit smoke tests."""
# pylint: disable=no-self-use
# pylint: disable=invalid-name
# pylint: disable=unused-argument
# pylint: disable=too-many-arguments

import pytest

from lib import base
from lib.constants.element import ObjectStates, objects
from lib.entities import entities_factory
from lib.entities.entity import Representation
from lib.factory import get_cls_rest_service
from lib.service import webui_service


class TestAuditPage(base.Test):
  """Tests for audit functionality."""

  @pytest.fixture(scope="function")
  def create_and_clone_audit_w_params_to_update(
      self, request, new_program_rest, new_control_rest,
      map_new_program_rest_to_new_control_rest, new_audit_rest,
      new_assessment_rest, new_assessment_template_rest, new_issue_rest,
      selenium
  ):
    """Create Audit with clonable and non clonable objects via REST API and
    clone it with them via UI.
    Preconditions:
    - Program, Control created via REST API.
    - Control mapped to Program via REST API.
    - Audit created under Program via REST API.
    - Assessment, Assessment Template, Issue created under Audit via REST API.
    - Issue mapped to Audit via REST API.
    """
    # pylint: disable=too-many-locals
    if hasattr(request, "param") and request.param:
      if isinstance(request.param, tuple):
        fixture, params_to_update = request.param
        # fixtures which are objects
        if fixture in request.fixturenames and fixture.startswith("new_"):
          fixture = locals().get(fixture)
          (get_cls_rest_service(objects.get_plural(fixture.type))().
           update_obj(obj=fixture, **params_to_update))
    expected_audit = entities_factory.AuditsFactory().clone(
        audit=new_audit_rest)[0]
    expected_asmt_tmpl = entities_factory.AssessmentTemplatesFactory().clone(
        asmt_tmpl=new_assessment_template_rest)[0]
    actual_audit = (webui_service.AuditsService(selenium).
                    clone_via_info_page_and_get_obj(audit_obj=new_audit_rest))
    return {
        "audit": new_audit_rest, "expected_audit": expected_audit,
        "actual_audit": actual_audit, "assessment": new_assessment_rest,
        "issue": new_issue_rest,
        "assessment_template": new_assessment_template_rest,
        "expected_assessment_template": expected_asmt_tmpl,
        "control": new_control_rest, "program": new_program_rest
    }

  @pytest.mark.smoke_tests
  def test_asmt_tmpl_creation(self, new_program_rest, new_audit_rest,
                              selenium):
    """Check if Assessment Template can be created from Audit page via
    Assessment Templates widget.
    Preconditions:
    - Audit created under Program via REST API.
    """
    expected_asmt_tmpl = (entities_factory.AssessmentTemplatesFactory().
                          create().repr_ui())
    asmt_tmpls_ui_service = webui_service.AssessmentTemplatesService(selenium)
    asmt_tmpls_ui_service.create_obj_via_tree_view(
        src_obj=new_audit_rest, obj=expected_asmt_tmpl)
    actual_asmt_tmpls_tab_count = (
        asmt_tmpls_ui_service.get_count_objs_from_tab(src_obj=new_audit_rest))
    assert len([expected_asmt_tmpl]) == actual_asmt_tmpls_tab_count
    actual_asmt_tmpls = asmt_tmpls_ui_service.get_list_objs_from_tree_view(
        src_obj=new_audit_rest)
    # 'expected_asmt_tmpl': modified_by (None) *factory
    self.general_equal_assert(
        [expected_asmt_tmpl], actual_asmt_tmpls, "modified_by")

  @pytest.mark.smoke_tests
  def test_asmt_creation(self, new_program_rest, new_audit_rest, selenium):
    """Check if Assessment can be created from Audit page via
    Assessments widget.
    Preconditions:
    - Audit created under Program via REST API.
    """
    expected_asmt = (entities_factory.AssessmentsFactory().
                     create().repr_ui())
    asmts_ui_service = webui_service.AssessmentsService(selenium)
    asmts_ui_service.create_obj_via_tree_view(
        src_obj=new_audit_rest, obj=expected_asmt)
    actual_asmts_tab_count = asmts_ui_service.get_count_objs_from_tab(
        src_obj=new_audit_rest)
    assert len([expected_asmt]) == actual_asmts_tab_count
    actual_asmts = asmts_ui_service.get_list_objs_from_tree_view(
        src_obj=new_audit_rest)
    # 'expected_asmt': modified_by (None) *factory
    self.general_equal_assert([expected_asmt], actual_asmts, "modified_by")

  @pytest.mark.smoke_tests
  @pytest.mark.parametrize(
      "dynamic_objects, dynamic_relationships",
      [("new_control_rest", "map_new_program_rest_to_new_control_rest"),
       ("new_objective_rest", "map_new_program_rest_to_new_objective_rest")],
      indirect=True)
  def test_asmt_creation_with_mapping(
      self, new_program_rest, dynamic_objects, dynamic_relationships,
      new_audit_rest, selenium
  ):
    """Check if Assessment can be created with mapped snapshot via
    Modal Create on Assessments TreeView. Additional check existing of
    mapped objs Titles on Modal Create.
    Preconditions:
    - Program, dynamic_objects created via REST API.
    - dynamic_objects mapped to Program via REST API.
    - Audit created under Program via REST API.
    Test parameters:
    - 'dynamic_objects'.
    - 'dynamic_relationships'.
    """
    expected_asmt = (
        entities_factory.AssessmentsFactory().create(
            objects_under_assessment=[dynamic_objects]))
    expected_titles = [dynamic_objects.title]
    asmts_ui_service = webui_service.AssessmentsService(selenium)
    actual_titles = (
        asmts_ui_service.create_obj_and_get_mapped_titles_from_modal(
            src_obj=new_audit_rest, obj=expected_asmt))
    assert expected_titles == actual_titles
    actual_asmt = asmts_ui_service.get_list_objs_from_info_panels(
        src_obj=new_audit_rest, objs=expected_asmt)
    expected_asmt = expected_asmt.repr_ui()
    # 'expected_asmt': custom_attributes (None) *factory
    self.general_equal_assert(
        expected_asmt, actual_asmt, "custom_attributes", "status")
    self.xfail_equal_assert(
        expected_asmt, actual_asmt,
        "Issue in app GGRC-3033, GGRC-3082", "status")

  @pytest.mark.smoke_tests
  @pytest.mark.parametrize(
      "dynamic_objects",
      [None, "new_assessment_template_rest",
       "new_assessment_template_with_cas_rest"],
      ids=["Assessments generation without Assessment Template",
           "Assessments generation based on Assessment Template without LCAs",
           "Assessments generation based on Assessment Template with LCAs"],
      indirect=True)
  def test_asmts_generation(
      self, new_program_rest, new_controls_rest,
      map_new_program_rest_to_new_controls_rest, new_audit_rest,
      dynamic_objects, selenium
  ):
    """Check if Assessments can be generated from Audit page via Assessments
    widget using Assessment template and Controls.
    Preconditions:
    - Program, Controls created via REST API.
    - Controls mapped to Program via REST API.
    - Audit created under Program via REST API.
    Test parameters:
    - 'dynamic_objects'.
    """
    expected_asmts = (entities_factory.AssessmentsFactory().generate(
        objs_under_asmt=new_controls_rest, audit=new_audit_rest,
        asmt_tmpl=dynamic_objects))
    expected_asmts = [
        expected_asmt.repr_ui() for expected_asmt in expected_asmts]
    asmts_ui_service = webui_service.AssessmentsService(selenium)
    asmts_ui_service.generate_objs_via_tree_view(
        src_obj=new_audit_rest, objs_under_asmt=new_controls_rest,
        asmt_tmpl_obj=dynamic_objects)
    actual_asmts_tab_count = asmts_ui_service.get_count_objs_from_tab(
        src_obj=new_audit_rest)
    assert len(expected_asmts) == actual_asmts_tab_count
    actual_asmts = asmts_ui_service.get_list_objs_from_info_panels(
        src_obj=new_audit_rest, objs=expected_asmts)
    # 'expected_asmt': slug, custom_attributes (None) *factory
    self.general_equal_assert(
        expected_asmts, actual_asmts, "slug", "custom_attributes")

  @pytest.mark.smoke_tests
  @pytest.mark.cloning
  def test_cloned_audit_contains_new_attrs(
      self, create_and_clone_audit_w_params_to_update
  ):
    """Check via UI that cloned Audit contains new predicted attributes.
    Preconditions:
    - Execution and return of fixture
    'create_and_clone_audit_w_params_to_update'.
    """
    expected_audit = (
        create_and_clone_audit_w_params_to_update["expected_audit"].repr_ui())
    actual_audit = create_and_clone_audit_w_params_to_update["actual_audit"]
    # 'expected_audit': created_at, updated_at, slug (None) *factory
    self.general_equal_assert(
        expected_audit, actual_audit, "created_at", "updated_at", "slug")

  @pytest.mark.smoke_tests
  @pytest.mark.cloning
  def test_non_clonable_objs_donot_move_to_cloned_audit(
      self, create_and_clone_audit_w_params_to_update, selenium
  ):
    """Check via UI that non clonable objects
    Assessment, Issue do not move to cloned Audit.
    Preconditions:
    - Execution and return of fixture
    'create_and_clone_audit_w_params_to_update'.
    """
    actual_audit = create_and_clone_audit_w_params_to_update["actual_audit"]
    asmts_ui_service = webui_service.AssessmentsService(selenium)
    actual_asmts_tab_count = asmts_ui_service.get_count_objs_from_tab(
        src_obj=actual_audit)
    actual_asmts = asmts_ui_service.get_list_objs_from_tree_view(
        src_obj=actual_audit)
    issues_ui_service = webui_service.IssuesService(selenium)
    actual_issues_tab_count = issues_ui_service.get_count_objs_from_tab(
        src_obj=actual_audit)
    actual_issues = issues_ui_service.get_list_objs_from_tree_view(
        src_obj=actual_audit)
    assert actual_asmts_tab_count == actual_issues_tab_count == 0
    assert bool(actual_asmts) == bool(actual_issues) == 0

  @pytest.mark.smoke_tests
  @pytest.mark.cloning
  @pytest.mark.parametrize(
      "create_and_clone_audit_w_params_to_update",
      [("new_assessment_template_rest", {"status": ObjectStates.DRAFT}),
       ("new_assessment_template_rest", {"status": ObjectStates.DEPRECATED}),
       ("new_assessment_template_rest", {"status": ObjectStates.ACTIVE})],
      ids=["Using initial Assessment Template w' 'Draft' status",
           "Using initial Assessment Template w' 'Deprecated' status",
           "Using initial Assessment Template w' 'Active' status"],
      indirect=True)
  def test_clonable_audit_related_objs_move_to_cloned_audit(
      self, create_and_clone_audit_w_params_to_update, selenium
  ):
    """Check via UI that clonable audit related object Assessment Template
    move to cloned Audit using all initial Assessment Templates's states.
    Preconditions:
    -Execution and return of fixture
    'create_and_clone_audit_w_params_to_update'.
    Test parameters:
    - 'create_and_clone_audit_w_params_to_update' which contains params to
    update asmt tmpl status via REST API.
    """
    actual_audit = create_and_clone_audit_w_params_to_update["actual_audit"]
    expected_asmt_tmpl = (
        create_and_clone_audit_w_params_to_update[
            "expected_assessment_template"].repr_ui())
    actual_asmt_tmpls = (webui_service.AssessmentTemplatesService(selenium).
                         get_list_objs_from_tree_view(src_obj=actual_audit))
    # 'expected_asmt_tmpl': slug, updated_at (None) *factory
    # 'actual_asmt_tmpls': created_at, updated_at, custom_attributes,
    #                      modified_by (None)
    is_expect_ggrc_3423 = (expected_asmt_tmpl.status != ObjectStates.DRAFT)
    exclude_attrs = (
        Representation.tree_view_attrs_to_exclude + ("slug", "modified_by"))
    self.general_equal_assert(
        expected_asmt_tmpl, actual_asmt_tmpls,
        *(exclude_attrs if not is_expect_ggrc_3423 else
          exclude_attrs + ("status", )))
    if is_expect_ggrc_3423:
      self.xfail_equal_assert(
          expected_asmt_tmpl, actual_asmt_tmpls,
          "Issue in app GGRC-3423", "status")

  @pytest.mark.smoke_tests
  @pytest.mark.cloning
  def test_clonable_not_audit_related_objs_move_to_cloned_audit(
      self, create_and_clone_audit_w_params_to_update, selenium
  ):
    """Check via UI that clonable not audit related objects
    Control, Program move to cloned Audit.
    Preconditions:
    -Execution and return of fixture
    'create_and_clone_audit_w_params_to_update'.
    """
    actual_audit = create_and_clone_audit_w_params_to_update["actual_audit"]
    expected_control = (
        create_and_clone_audit_w_params_to_update["control"].repr_ui())
    expected_program = (
        create_and_clone_audit_w_params_to_update["program"].repr_ui())
    actual_controls = (webui_service.ControlsService(selenium).
                       get_list_objs_from_tree_view(src_obj=actual_audit))
    actual_programs = (webui_service.ProgramsService(selenium).
                       get_list_objs_from_tree_view(src_obj=actual_audit))
    # 'actual_controls, actual_programs': created_at, updated_at,
    #                                     custom_attributes (None)
    self.general_equal_assert(
        [expected_control], actual_controls,
        *Representation.tree_view_attrs_to_exclude)
    self.general_equal_assert(
        [expected_program], actual_programs,
        *Representation.tree_view_attrs_to_exclude)
