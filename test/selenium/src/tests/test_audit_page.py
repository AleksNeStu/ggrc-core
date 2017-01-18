# Copyright (C) 2017 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Tests to Audit object."""

import pytest

from lib import base
from lib.constants import messages
from lib.entities.entities_factory import AsmtTmplFactory, AsmtFactory
from lib.service.rest_service import RelationshipsService
from lib.service.webui_service import AsmtTmplService, AsmtService


class TestAuditPage(base.Test):
  """Tests for the audit page."""

  @pytest.mark.smoke_tests
  def test_asmt_tmpl_creation_via_widget(self, selenium, new_audit_rest):
    """Check if assessment template can be created from Audit page via
    Assessment Templates widget.
    Preconditions:
    - Audit created under Program via REST API.
    """
    audit, program = new_audit_rest
    expected_asmt_tmpl = AsmtTmplFactory().create()
    AsmtTmplService(selenium).create(audit, expected_asmt_tmpl)
    asmt_tmpls_tab_count = AsmtTmplService(selenium).get_count(audit)
    assert len([expected_asmt_tmpl]) == asmt_tmpls_tab_count
    actual_asmt_tmpls = AsmtTmplService(selenium).get_list_of_objs(audit)
    assert [expected_asmt_tmpl] == actual_asmt_tmpls, (
        messages.ERR_MSG_FORMAT.format(
            [expected_asmt_tmpl], actual_asmt_tmpls))

  @pytest.mark.smoke_tests
  def test_asmt_creation_via_widget(self, selenium, new_audit_rest):
    """Check if assessment can be created from Audit page via
    Assessments widget.
    Preconditions:
    - Audit created under Program via REST API.
    """
    audit, program = new_audit_rest
    expected_asmt = AsmtFactory().create()
    AsmtService(selenium).create(audit, expected_asmt)
    asmts_tab_count = AsmtService(selenium).get_count(audit)
    assert len([expected_asmt]) == asmts_tab_count
    actual_asmts = AsmtService(selenium).get_list_of_objs(audit)
    assert [expected_asmt] == actual_asmts, (
        messages.ERR_MSG_FORMAT.format([expected_asmt], actual_asmts))

  @pytest.mark.smoke_tests
  def test_asmts_generation_via_widget(self, selenium,
                                       new_controls_rest_to_new_program_rest,
                                       new_controls_rest, new_asmt_tmpl_rest):
    """Check if assessments can be generated from Audit page via Assessments
    widget using assessment template and controls.
    Preconditions:
    - Program, Controls created via REST API.
    - Controls mapped to Program via REST API.
    - Audit created under Program via REST API.
    - Assessment Template created under Audit via REST API.
    """
    asmt_tmpl, audit, program = new_asmt_tmpl_rest
    RelationshipsService().create(src_obj=program, dest_objs=new_controls_rest)
    expected_asmts = [AsmtFactory().create(
        title=control.title + " assessment for " + audit.title,
        audit=audit.title) for control in new_controls_rest]
    AsmtService(selenium).generate(audit, asmt_tmpl, new_controls_rest)
    asmts_tab_count = AsmtService(selenium).get_count(audit)
    assert len(expected_asmts) == asmts_tab_count
    actual_asmts = AsmtService(selenium).get_list_of_objs(audit)
    assert expected_asmts == actual_asmts, (
        messages.ERR_MSG_FORMAT.format(expected_asmts, actual_asmts))
