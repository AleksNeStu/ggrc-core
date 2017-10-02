# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""PyTest fixtures."""
# pylint: disable=invalid-name
# pylint: disable=global-variable-not-assigned
# pylint: disable=unused-argument

import pytest

from lib import dynamic_fixtures
from lib.page import dashboard
from lib.utils import selenium_utils, help_utils
from lib.utils.selenium_utils import get_full_screenshot_as_base64

# pylint: disable=redefined-outer-name
pytest_plugins = "selenium", "xdist", "xvfb", "timeout", "flask", \
                 "rerunfailures", "timeout", "repeat", "pycharm"


def _common_fixtures(fixture):
  """Generate common fixtures and return global dictionary of executed
  common fixtures.
  """
  dynamic_fixtures.generate_common_fixtures(fixture)
  if isinstance(fixture, tuple):
    fixture, _ = fixture
  fixture = dynamic_fixtures.dict_executed_fixtures[fixture]
  return (help_utils.get_single_obj(fixture)
          if not help_utils.is_multiple_objs(fixture) else fixture)


def _snapshots_fixtures(fixturename):
  """Generate snapshot fixtures used generation of common fixtures and return
  dictionary of executed common fixtures in scope of snapshot fixtures.
  """
  return dynamic_fixtures.generate_snapshots_fixtures(fixturename)


@pytest.mark.hookwrapper
def pytest_runtest_makereport(item, call):
  """Replace common screenshot from html-report by full size screenshot."""
  # pylint: disable=too-many-locals
  outcome = yield
  report = outcome.get_result()
  summary = []
  extra = getattr(report, "extra", [])
  driver = getattr(item, "_driver", None)
  xfail = hasattr(report, "wasxfail")
  failure = (report.skipped and xfail) or (report.failed and not xfail)
  when = item.config.getini("selenium_capture_debug").lower()
  capture_debug = when == "always" or (when == "failure" and failure)
  pytest_html = item.config.pluginmanager.getplugin("html")
  if driver is not None and capture_debug and pytest_html is not None:
    exclude = item.config.getini("selenium_exclude_debug").lower()
    if "screenshot" not in exclude:
      try:
        screenshot = get_full_screenshot_as_base64(driver)
        for ex in extra:
          if ex["name"] == "Screenshot":
            extra.remove(ex)
        # add screenshot to the html report
        extra.append(pytest_html.extras.image(screenshot, "Screenshot"))
      except Exception as e:
        summary.append("WARNING: Failed to gather screenshot: {0}".format(e))
  if summary:
    report.sections.append(("pytest-selenium", "\n".join(summary)))
  report.extra = extra


@pytest.fixture(scope="function")
def selenium(selenium):
  """Create Web Driver instance and setup test resources for running test
  in headless mode.
  """
  selenium.set_window_size(1440, 900)
  dynamic_fixtures.dict_executed_fixtures.update({"selenium": selenium})
  yield selenium


@pytest.fixture(scope="function")
def create_tmp_dir(tmpdir_factory, request):
  """Create temporary directory for test and return unconditional full path to
  it according to the next rule:
  selenium/tmp/'name of test method with parameters'.
  Example:
  Test's path to run:
  selenium/src/tests/test_audit_page.py::TestAuditPage::()::
  test_asmts_generation[Assessments generation without Assessment Template]
  Test's temp directory:
  selenium/tmp/
  test_asmts_generation[Assessments generation without Assessment Template]
  """
  test_name = request.node.name
  test_tmp_dir = tmpdir_factory.mktemp(test_name, numbered=True)
  yield test_tmp_dir.strpath


@pytest.fixture
def chrome_options(chrome_options, create_tmp_dir):
  """Set configuration to run Chrome with specific options."""
  prefs = {"download.default_directory": create_tmp_dir,
           "download.prompt_for_download": False}
  chrome_options.add_experimental_option("prefs", prefs)
  return chrome_options


@pytest.fixture(scope="function")
def my_work_dashboard(selenium):
  """Open My Work Dashboard URL and
  return My Work Dashboard page objects model."""
  selenium_utils.open_url(selenium, dashboard.Dashboard.URL)
  return dashboard.Dashboard(selenium)


@pytest.fixture(scope="function")
def header_dashboard(selenium):
  """Open My Work Dashboard URL and
  return Header Dashboard page objects model."""
  selenium_utils.open_url(selenium, dashboard.Dashboard.URL)
  return dashboard.Header(selenium)


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
  yield _common_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def new_risk_ui(selenium, request):
  """Create new Risk Group object via UI (LHN).
  Return: lib.page.widget.Risks
  """
  yield _common_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def new_program_rest(request):
  """Create new Program object via REST API.
  Return: lib.entities.entity.ProgramEntity
  """
  yield _common_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def new_programs_rest(request):
  """Create new Controls objects via REST API.
  Return: [lib.entities.entity.ProgramEntity, ...]
  """
  yield _common_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def new_control_rest(request):
  """Create new Control object via REST API.
  Return: lib.entities.entity.ControlEntity
  """
  yield _common_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def new_controls_rest(request):
  """Create new Controls objects via REST API.
  Return: [lib.entities.entity.ControlEntity, ...]
  """
  yield _common_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def new_objective_rest(request):
  """Create new Objective object via REST API.
  Return: lib.entities.entity.ObjectiveEntity
  """
  yield _common_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def new_objectives_rest(request):
  """Create new Objective objects via REST API.
  Return: [lib.entities.entity.ObjectiveEntity, ...]
  """
  yield _common_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def new_audit_rest(request):
  """Create new Audit under Program object via REST API.
  Return: lib.entities.entity.AuditEntity
  """
  yield _common_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def new_audits_rest(request):
  """Create new Controls objects via REST API.
  Return: [lib.entities.entity.AuditEntity, ...]
  """
  yield _common_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def new_assessment_rest(request):
  """Create new Assessment under Audit object via REST API.
  Return: lib.entities.entity.AssessmentEntity
  """
  yield _common_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def new_assessments_rest(request):
  """Create new Assessments objects via REST API.
   Return: [lib.entities.entity.AssessmentEntity, ...]
   """
  yield _common_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def new_issue_rest(request):
  """Create new Issue under Audit object via REST API.
  Return: lib.entities.entity.IssueEntity
  """
  yield _common_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def new_assessment_template_rest(request):
  """Create new Assessment Template under Audit object via REST API.
  Return: lib.entities.entity.AssessmentTemplateEntity
  """
  yield _common_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def new_assessment_template_with_cas_rest(request):
  """Create new Assessment Template with CAs under Audit object via REST API.
  Return: lib.entities.entity.AssessmentTemplateEntity
  """
  yield _common_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def new_cas_for_assessments_rest(request):
  """New global Custom Attributes for assessments created via REST API.
  Teardown - remove created gCAs.
  """
  cas = _common_fixtures(request.fixturename)
  yield cas
  from lib.service.rest_service import CustomAttributeDefinitionsService
  CustomAttributeDefinitionsService().delete_objs(cas)


@pytest.fixture(scope="function")
def new_cas_for_controls_rest(request):
  """Create new Global Custom Attributes for Controls via REST API and
  delete GCAs as teardown section.
  """
  cas = _common_fixtures(request.fixturename)
  yield cas
  from lib.service.rest_service import CustomAttributeDefinitionsService
  CustomAttributeDefinitionsService().delete_objs(cas)


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
def map_new_control_rest_to_new_objective_rest(request):
  """Map Objective to Control object via REST API return response from server.
  """
  yield _common_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def map_new_control_rest_to_new_objectives_rest(request):
  """Map Objectives to Control object via REST API return response from server.
  """
  yield _common_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def map_new_control_rest_to_new_programs_rest(request):
  """Map Programs to Control objects via REST API return response from server.
  """
  yield _common_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def map_new_control_rest_to_new_assessments_rest(request):
  """Map Assessments to Control via REST API return response from server."""
  yield _common_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def map_new_program_rest_to_new_objective_rest(request):
  """Map Objective to Program object via REST API return response from server.
  """
  yield _common_fixtures(request.fixturename)


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


@pytest.fixture(scope="function")
def map_new_assessment_rest_to_new_issue_rest(request):
  """Map Objectives to Control object via REST API return response from server.
  """
  yield _common_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def map_new_assessment_rest_to_new_control_rest_snapshot(request):
  """Map Objectives to Control object via REST API return response from server.
  """
  yield _common_fixtures(request.fixturename)


def _common_request_param(request):
  """Processing for common fixtures of request object which gives access to the
  requesting test context and has an optional param attribute in case the
  fixture is parametrized indirectly.
  """
  # todo implement '_snapshot_request_param'
  if hasattr(request, "param") and request.param:
    params = request.param
    return (({param: _common_fixtures(param) for param in params}
            if isinstance(params, list) else _common_fixtures(params)) if
            params else None)


@pytest.fixture(scope="function")
def dynamic_create_audit_with_control(request):
  """Create Program and Control, map Control to Program, create Audit
  under Program and dynamically make manipulations on Control (update,
  delete, ...) via REST API according to fixturename. Fixturename is indirect
  parameter that get from 'request.param' and have to be string or boolean.
  Return: lib.entities.entity.AssessmentTemplateEntity
  """
  if hasattr(request, "param") and request.param:
    yield (dynamic_fixtures.generate_snapshots_fixtures(request.param) if
           request.param else None)


@pytest.fixture(scope="function")
def dynamic_objects(request):
  """Create new object or objects via REST API or UI according to indirect
  parameter 'request.param' which can be: str, list of str, bool.
  Examples:
  - 'new_program_rest': lib.entities.entity.ProgramEntity;
  - 'new_programs_rest': [lib.entities.entity.ProgramEntity, ...];
  - ['new_program_rest', 'new_control_rest']:
    {'new_program_rest': lib.entities.entity.ProgramEntity,
     'new_control_rest': lib.entities.entity.ControlEntity};
  - True: None.
  """
  yield _common_request_param(request)


@pytest.fixture(scope="function")
def dynamic_objects_w_factory_params(request):
  """Create new object or objects via REST API or UI according to indirect
  parameter 'request.param' and w/ the same logic as 'dynamic_objects' fixture
  but using extra parameters to have option change default flow.
  """
  yield _common_request_param(request)


@pytest.fixture(scope="function")
def dynamic_relationships(request):
  """Create single or multiply relationships between source and destinations
  objects via REST API according to indirect parameter 'request.param' which
  can be: str, list of str, bool and return response or responses from server.
  Example:
  - 'map_new_program_rest_to_new_control_rest';
  - {'map_new_program_rest_to_new_control_rest': resp1,
     'map_new_control_rest_to_new_objective_rest': resp2}.
  """
  yield _common_request_param(request)
