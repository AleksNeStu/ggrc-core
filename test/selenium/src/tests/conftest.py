# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""PyTest fixtures."""
# pylint: disable=invalid-name
# pylint: disable=global-variable-not-assigned
# pylint: disable=unused-argument

import pytest

from lib import dynamic_fixtures


# pylint: disable=redefined-outer-name
pytest_plugins = "selenium", "xdist", "xvfb", "timeout", "flask", \
                 "rerunfailures", "timeout", "repeat", "pycharm"


def _common_fixtures(fixturename):
  """Generate common fixtures and return global dictionary of executed
  common fixtures.
  """
  dynamic_fixtures.generate_common_fixtures(fixturename)
  return dynamic_fixtures.dict_executed_fixtures[fixturename]


@pytest.fixture(scope="function")
def selenium(selenium):
  """Create Web Driver instance and setup test resources for running test
  in headless mode.
  """
  selenium.set_window_size(1440, 900)
  dynamic_fixtures.dict_executed_fixtures.update({"selenium": selenium})
  yield selenium


@pytest.fixture(scope="function")
def dynamic_new_assessment_template(request):
  """Dynamically create new Assessment Template under Audit object according
  to fixturename. Fixturename is indirect parameter that get from
  'request.param' and have to be string or boolean.
  Return: lib.entities.entity.AssessmentTemplateEntity
  """
  yield _common_fixtures(request.param)[0] if request.param else None


@pytest.fixture(scope="function")
def new_program_ui(selenium, request):
  """Create new Program object via UI (LHN).
  Return: (Program modal, Program Info widget).
  """
  yield _common_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def new_org_group_ui(selenium, request):
  """Create new Org Group object via UI (LHN).
  Return: lib.page.widget.OrgGroupInfo
  """
  yield _common_fixtures(request.fixturename)[0]


@pytest.fixture(scope="function")
def new_risk_ui(selenium, request):
  """Create new Risk Group object via UI (LHN).
  Return: lib.page.widget.Risks
  """
  yield _common_fixtures(request.fixturename)[0]


@pytest.fixture(scope="function")
def new_program_rest(request):
  """Create new Program object via REST API.
  Return: lib.entities.entity.ProgramEntity
  """
  yield _common_fixtures(request.fixturename)[0]


@pytest.fixture(scope="function")
def new_control_rest(request):
  """Create new Control object via REST API.
  Return: lib.entities.entity.ControlEntity
  """
  yield _common_fixtures(request.fixturename)[0]


@pytest.fixture(scope="function")
def new_controls_rest(request):
  """Create new Controls objects via REST API.
  Return: [lib.entities.entity.ControlEntity, ...]
  """
  yield _common_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def new_audit_rest(request):
  """Create new Audit under Program object via REST API.
  Return: lib.entities.entity.AuditEntity
  """
  yield _common_fixtures(request.fixturename)[0]


@pytest.fixture(scope="function")
def new_assessment_rest(request):
  """Create new Assessment under Audit object via REST API.
  Return: lib.entities.entity.AssessmentEntity
  """
  yield _common_fixtures(request.fixturename)[0]


@pytest.fixture(scope="function")
def new_issue_rest(request):
  """Create new Issue under Audit object via REST API.
  Return: lib.entities.entity.IssueEntity
  """
  yield _common_fixtures(request.fixturename)[0]


@pytest.fixture(scope="function")
def new_assessment_template_rest(request):
  """Create new Assessment Template under Audit object via REST API.
  Return: lib.entities.entity.AssessmentTemplateEntity
  """
  yield _common_fixtures(request.fixturename)[0]


@pytest.fixture(scope="function")
def new_assessment_template_with_cas_rest(request):
  """Create new Assessment Template with CAs under Audit object via REST API.
  Return: lib.entities.entity.AssessmentTemplateEntity
  """
  yield _common_fixtures(request.fixturename)[0]


@pytest.fixture(scope="function")
def map_new_program_rest_to_new_control_rest(request):
  """Map Control to Program object via REST API return response from server.
  """
  yield _common_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def map_new_program_rest_to_new_controls_rest(request):
  """Map Controls to Program object via REST API return response from server.
  """
  yield _common_fixtures(request.fixturename)


def _snapshots_fixtures(fixturename):
  """Generate snapshot fixtures used generation of common fixtures and return
  dictionary of executed common fixtures in scope of snapshot fixtures.
  """
  return dynamic_fixtures.generate_snapshots_fixtures(fixturename)


@pytest.fixture(scope="function")
def dynamic_create_audit_with_control(request):
  """Create Program and Control, map Control to Program, create Audit
  under Program and dynamically make manipulations on Control (update,
  delete, ...) via REST API according to fixturename. Fixturename is indirect
  parameter that get from 'request.param' and have to be string or boolean.
  Return: lib.entities.entity.AssessmentTemplateEntity
  """
  yield (dynamic_fixtures.generate_snapshots_fixtures(request.param) if
         request.param else None)


@pytest.fixture(scope="function")
def create_audit_with_control(request):
  """Create Program and Control, map Control to Program, create Audit
  under Program via REST API and return dictionary of executed fixtures.
  """
  yield _snapshots_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def create_audit_with_control_and_update_control(request):
  """Create Program and Control, map Control to Program, create Audit
  under Program, update Control via REST API and return dictionary of executed
  fixtures.
  """
  yield _snapshots_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def create_audit_with_control_and_delete_control(request):
  """Create Program and Control, map Control to Program, create Audit
  under Program, delete Control via REST API and return dictionary of executed
  fixtures.
  """
  yield _snapshots_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def dynamic_object(request):
  """Create object by passed indirect parameter in test"""
  yield _common_fixtures(request.param)
