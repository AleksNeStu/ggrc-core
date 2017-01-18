# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""PyTest fixtures."""

import pytest   # pylint: disable=import-error

from lib import constants
from lib.constants.test import batch
from lib.page.widget import info_widget
from lib.service.rest_service import (
    ProgramsService, AuditsService, ControlsService, AsmtTmplsService,
    AssessmentsService, RelationshipsService, ObjectsOwnersService)
from lib.utils import conftest_utils
from lib.utils import test_utils

# pylint: disable=redefined-outer-name
pytest_plugins = "selenium", "xdist", "xvfb", "timeout", "flask", \
                 "rerunfailures", "timeout", "repeat", "pycharm"


@pytest.yield_fixture(scope="session")
def db_drop():
  """Reset the DB"""
  # todo
  pass


@pytest.yield_fixture(scope="session")
def db_migrate():
  """Make sure the DB is up to date"""
  # todo
  pass


@pytest.yield_fixture(scope="function")
def selenium(selenium):
  """Setup test resources for running test in headless mode"""

  # todo: here we should use selenium.maximize_window() and env variables to
  #  set xvfb resolution in the docker container. Setting the env vars
  # currently doesn't work for selenium-docker
  selenium.set_window_size(1440, 900)
  yield selenium


@pytest.yield_fixture(scope="function")
def new_control(selenium):
  """Creates a new control object.

  Returns:
      lib.page.widget.Controls
  """
  control_info_page = conftest_utils.create_lhn_object(
      selenium, constants.element.Lhn.CONTROLS)
  yield control_info_page


@pytest.yield_fixture(scope="function")
def new_program(selenium, new_control):
  """Creates a new program object and returns the program info page with the
  saved modal"""
  # pylint: disable=redefined-outer-name
  modal = conftest_utils.get_lhn_accordion(
      selenium, constants.element.Lhn.PROGRAMS)\
      .create_new()
  test_utils.ModalNewPrograms.enter_test_data(modal)
  modal.save_and_close()
  program_info_page = info_widget.Programs(selenium)
  yield modal, program_info_page


@pytest.yield_fixture(scope="function")
def new_org_group(selenium):
  """Creates a new org group object.

  Returns:
      lib.page.widget.OrgGroupInfo
  """
  org_group_page = conftest_utils.create_lhn_object(
      selenium, constants.element.Lhn.ORG_GROUPS)
  yield org_group_page


@pytest.yield_fixture(scope="function")
def new_risk(selenium):
  """Creates a new risk group object.

  Returns:
      lib.page.widget.Risks
  """
  risk_page = conftest_utils.create_lhn_object(
      selenium, constants.element.Lhn.RISKS)
  yield risk_page


@pytest.yield_fixture(scope="function")
def new_issue(selenium):
  """Creates a new issue object.

  Returns:
      lib.page.widget.IssueInfo
  """
  issue_info_page = conftest_utils.create_lhn_object(
      selenium, constants.element.Lhn.ISSUES)
  yield issue_info_page


@pytest.yield_fixture(scope="function")
def new_process(selenium):
  """Creates a new process object.

  Returns:
      lib.page.widget.Processes
  """
  process_info_page = conftest_utils.create_lhn_object(
      selenium, constants.element.Lhn.PROCESSES)
  yield process_info_page


@pytest.yield_fixture(scope="function")
def new_data_asset(selenium):
  """Creates a new data asset object.

  Returns:
      lib.page.widget.DataAssetInfo
  """
  data_asset_page = conftest_utils.create_lhn_object(
      selenium, constants.element.Lhn.DATA_ASSETS)
  yield data_asset_page


@pytest.yield_fixture(scope="function")
def new_system(selenium):
  """Creates a new system object.

  Returns:
      lib.page.widget.IssueInfo
  """
  system_page = conftest_utils.create_lhn_object(
      selenium, constants.element.Lhn.SYSTEMS)
  yield system_page


@pytest.yield_fixture(scope="function")
def new_product(selenium):
  """Creates a new product object.

  Returns:
      lib.page.widget.Product
  """
  product_page = conftest_utils.create_lhn_object(
      selenium, constants.element.Lhn.PRODUCTS)
  yield product_page


@pytest.yield_fixture(scope="function")
def new_project(selenium):
  """Creates a new project object.

  Returns:
      lib.page.widget.ProjectInfo
  """
  project_page = conftest_utils.create_lhn_object(
      selenium, constants.element.Lhn.PROJECTS)
  yield project_page


@pytest.yield_fixture(scope="function")
def battery_of_controls(selenium):
  """Creates 3 control objects"""
  controls = []

  for _ in xrange(batch.BATTERY):
    controls.append(conftest_utils.create_lhn_object(
        selenium, constants.element.Lhn.CONTROLS))
  yield controls


@pytest.yield_fixture(scope="function")
def new_program_rest():
  """Create a new business object Program via REST API.
  Return the object: Program
  """
  yield ProgramsService().create(count=1)[0]


@pytest.yield_fixture(scope="function")
def new_audit_rest(new_program_rest):
  """Create a new business object Audit via REST API.
  Return the list of objects: [Audit, Program]
  """
  yield AuditsService().create(
      count=1, program=new_program_rest)[0], new_program_rest


@pytest.yield_fixture(scope="function")
def new_asmt_tmpl_rest(new_audit_rest):
  """Create a new business object Assessment Template via REST API.
  Return the list of objects: [AssessmentTemplate, Audit, Program]
  """
  yield (AsmtTmplsService().create(
      count=1, audit=new_audit_rest[0])[0],
      new_audit_rest[0], new_audit_rest[1])


@pytest.yield_fixture(scope="function")
def new_asmt_rest(new_audit_rest):
  """Create a new business object Assessment via REST API.
  Return the list of objects: [Assessment, Object, Audit]
  """
  yield (AssessmentsService().create(
      count=1, object=new_audit_rest[1],
      audit=new_audit_rest[0])[0], new_audit_rest[1], new_audit_rest[0])


@pytest.yield_fixture(scope="function")
def new_control_rest():
  """Create a new business object Control via REST API.
  Return the object: Control
  """
  control = ControlsService().create(count=1)[0]
  ObjectsOwnersService().create(objs=control)
  yield control


@pytest.yield_fixture(scope="function")
def new_controls_rest():
  """Create batch of a new business objects Controls via REST API.
  Return the list of objects: [Control#1, Control#2, Control#3].
  """
  controls = ControlsService().create(count=batch.BATTERY)
  ObjectsOwnersService().create(objs=controls)
  yield controls


@pytest.yield_fixture(scope="function")
def update_control_rest(new_control_rest):
  """Update of the existing business object Control via REST API.
  Return the object: Control
  """
  yield ControlsService().update(objs=new_control_rest)[0]


@pytest.yield_fixture(scope="function")
def new_controls_rest_to_new_program_rest(new_program_rest, new_controls_rest):
  """Create a new business objects Program and Controls via REST API.
  Create relationship (map) Controls to Program via REST API.
  """
  yield RelationshipsService().create(src_obj=new_program_rest,
                                      dest_objs=new_controls_rest)

@pytest.yield_fixture(scope="function")
def new_control_rest_to_new_program_rest(new_program_rest, new_control_rest):
  """Create a new business objects Program and Control via REST API.
  Create relationship (map) Control to Program via REST API.
  """
  yield RelationshipsService().create(src_obj=new_program_rest,
                                      dest_objs=new_control_rest)
