# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Module contains integration tests for Cycle Task Group Object Task Object
updates via import"""

# pylint: disable=invalid-name

from os.path import join
from os.path import abspath
from os.path import dirname
from freezegun import freeze_time

from ggrc import db
from ggrc.converters import errors
from ggrc_workflows.models import Cycle
from ggrc_workflows.models import CycleTaskGroupObjectTask
from integration.ggrc import TestCase
from integration.ggrc.generator import ObjectGenerator
from integration.ggrc_workflows.generator import WorkflowsGenerator


# pylint: disable=too-many-instance-attributes
class TestCycleTaskImportUpdate(TestCase):

  """ This class contains simple cycle task update tests using import
  functionality
  """

  CSV_DIR = join(abspath(dirname(__file__)), "test_csvs/")

  def setUp(self):
    super(TestCycleTaskImportUpdate, self).setUp()
    self.wf_generator = WorkflowsGenerator()
    self.object_generator = ObjectGenerator()
    self.random_objects = self.object_generator.generate_random_objects(2)
    _, self.person_1 = self.object_generator.generate_person(
        user_role="Administrator")
    self.ftime_active = "2016-07-01"
    self.ftime_historical = "2014-05-01"
    self._create_test_cases_data()
    # It is needed because cycle-tasks are generated automatically with
    # 'slug' based on auto_increment 'id' field.
    # At start of each test we suppose that created cycle-task's 'slug'
    # lie in range from 1 to 10.
    db.session.execute('ALTER TABLE cycle_task_group_object_tasks '
                       'AUTO_INCREMENT = 1')

  def test_cycle_task_correct(self):
    """Test cycle task update via import with correct data"""
    self._generate_cycle_tasks()
    with freeze_time(self.ftime_active):
      response = self.import_file("cycle_task_correct.csv")
      self._check_csv_response(response, {})
      self._cmp_tasks(self.expected_cycle_task_correct)

  def test_cycle_task_warnings(self):
    """Test cycle task update via import with data which is the reason of
    warnings about non-importable columns."""
    self._generate_cycle_tasks()
    with freeze_time(self.ftime_active):
      response = self.import_file("cycle_task_warnings.csv")
      self._check_csv_response(response, self.expected_warnings)
      self._cmp_tasks(self.expected_cycle_task_correct)

  def test_cycle_task_create_error(self):
    """Test cycle task update via import with data which is the reason of
    errors about new cycle task creation."""
    self._generate_cycle_tasks()
    with freeze_time(self.ftime_active):
      response = self.import_file("cycle_task_create_error.csv")
      self._check_csv_response(response, self.expected_create_error)
      self._cmp_tasks(self.expected_cycle_task_correct)

  def test_cycle_task_date_error(self):
    """Test cycle task update via import with data which is the reason of
    errors about incorrect dates in csv file."""
    self._generate_cycle_tasks()
    with freeze_time(self.ftime_active):
      response = self.import_file("cycle_task_date_error.csv")
      self._check_csv_response(response, self.expected_date_error)
      self._cmp_tasks(self.expected_cycle_task_date_error)

  def test_cycle_task_permission_error(self):
    """Test cycle task update via import with non-admin user which is the
    reason of error. Only admin can update cycle tasks via import."""
    self._generate_cycle_tasks()
    with freeze_time(self.ftime_active):
      _, creator = self.object_generator.generate_person(user_role="Creator")
      response = self.import_file("cycle_task_correct.csv", person=creator)
      self._check_csv_response(response, self.expected_permission_error)
      # Cycle tasks' data shouldn't be changed in test DB after import run from
      # non-admin user
      expected_cycle_task_permission_error = {}
      expected_cycle_task_permission_error.update(
          self.generated_cycle_tasks_active)
      expected_cycle_task_permission_error.update(
          self.generated_cycle_tasks_historical)
      self._cmp_tasks(expected_cycle_task_permission_error)

  def _cmp_tasks(self, expected_ctasks):
    """Compare tasks values from argument's list and test DB."""
    for ctask in db.session.query(CycleTaskGroupObjectTask).all():
      if ctask.slug not in expected_ctasks:
        continue
      exp_task = expected_ctasks[ctask.slug]
      for attr, val in exp_task.iteritems():
        self.assertEqual(str(getattr(ctask, attr, None)), val)

  # pylint: disable=too-many-arguments
  def _activate_workflow(self, ftime, workflow, task_group, task_group_tasks,
                         random_object, cycle_tasks):
    """Helper which is responsible for active cycle-tasks creation"""
    with freeze_time(ftime):
      _, wf = self.wf_generator.generate_workflow(workflow)
      _, tg = self.wf_generator.generate_task_group(wf, task_group)
      for task in task_group_tasks:
        self.wf_generator.generate_task_group_task(tg, task)
      self.wf_generator.generate_task_group_object(tg, random_object)

      _, cycle = self.wf_generator.generate_cycle(wf)
      self.wf_generator.activate_workflow(wf)

      for exp_slug, exp_task in cycle_tasks.iteritems():
        obj = db.session.query(CycleTaskGroupObjectTask).filter_by(
            slug=exp_slug
        ).first()
        if exp_task["status"] == "Verified":
          self.wf_generator.modify_object(obj, {"status": "Finished"})
        self.wf_generator.modify_object(obj, {"status": exp_task["status"]})
    self._cmp_tasks(cycle_tasks)
    return cycle

  def _generate_cycle_tasks(self):
    """Helper which is responsible for test data creation"""
    self._activate_workflow(self.ftime_active, self.workflow_active,
                            self.task_group_active,
                            self.task_group_tasks_active,
                            self.random_objects[0],
                            self.generated_cycle_tasks_active)
    cycle = self._activate_workflow(self.ftime_historical,
                                    self.workflow_historical,
                                    self.task_group_historical,
                                    self.task_group_tasks_historical,
                                    self.random_objects[1],
                                    self.generated_cycle_tasks_historical)
    with freeze_time(self.ftime_historical):
      cycle = Cycle.query.get(cycle.id)
      self.wf_generator.modify_object(cycle, data={"is_current": False})

  def _create_test_cases_data(self):
    """Create test cases data: for object generation,
    expected data for checks"""
    def person_dict(person_id):
      """Return person data"""
      return {
          "href": "/api/people/%d" % person_id,
          "id": person_id,
          "type": "Person"
      }

    self.workflow_active = {
        "title": "workflow active title",
        "description": "workflow active description",
        "frequency": "one_time",
        "owners": [person_dict(self.person_1.id)],
        "notify_on_change": False,
    }

    self.task_group_active = {
        "title": "task group active title",
        "contact": person_dict(self.person_1.id),
    }

    self.task_group_tasks_active = [{
        "title": "task active title 1",
        "description": "task active description 1",
        "contact": person_dict(self.person_1.id),
        "start_date": "07/01/2016",
        "end_date": "07/06/2016",
    }, {
        "title": "task active title 2",
        "description": "task active description 2",
        "contact": person_dict(self.person_1.id),
        "start_date": "07/07/2016",
        "end_date": "07/12/2016",
    }, {
        "title": "task active title 3",
        "description": "task active description 3",
        "contact": person_dict(self.person_1.id),
        "start_date": "07/13/2016",
        "end_date": "07/18/2016",
    }, {
        "title": "task active title 4",
        "description": "task active description 4",
        "contact": person_dict(self.person_1.id),
        "start_date": "07/19/2016",
        "end_date": "07/24/2016",
    }, {
        "title": "task active title 5",
        "description": "task active description 5",
        "contact": person_dict(self.person_1.id),
        "start_date": "07/25/2016",
        "end_date": "07/30/2016",
    }]

    # Active cycle tasks which should be generated from previous structure
    # at the beginning of each test
    self.generated_cycle_tasks_active = {
        "CYCLETASK-1": {
            "title": self.task_group_tasks_active[0]["title"],
            "description": self.task_group_tasks_active[0]["description"],
            "start_date": "2016-07-01",
            "end_date": "2016-07-06",
            "finished_date": "None",
            "verified_date": "None",
            "status": "Assigned"
        },
        "CYCLETASK-2": {
            "title": self.task_group_tasks_active[1]["title"],
            "description": self.task_group_tasks_active[1]["description"],
            "start_date": "2016-07-07",
            "end_date": "2016-07-12",
            "finished_date": "None",
            "verified_date": "None",
            "status": "Declined"
        },
        "CYCLETASK-3": {
            "title": self.task_group_tasks_active[2]["title"],
            "description": self.task_group_tasks_active[2]["description"],
            "start_date": "2016-07-13",
            "end_date": "2016-07-18",
            "finished_date": "None",
            "verified_date": "None",
            "status": "InProgress"
        },
        "CYCLETASK-4": {
            "title": self.task_group_tasks_active[3]["title"],
            "description": self.task_group_tasks_active[3]["description"],
            "start_date": "2016-07-19",
            "end_date": "2016-07-24",
            "finished_date": "2016-07-01 00:00:00",
            "verified_date": "None",
            "status": "Finished"
        },
        "CYCLETASK-5": {
            "title": self.task_group_tasks_active[4]["title"],
            "description": self.task_group_tasks_active[4]["description"],
            "start_date": "2016-07-25",
            "end_date": "2016-07-30",
            "finished_date": "2016-07-01 00:00:00",
            "verified_date": "2016-07-01 00:00:00",
            "status": "Verified"
        }
    }

    self.workflow_historical = {
        "title": "workflow historical title",
        "description": "workflow historical description",
        "frequency": "one_time",
        "owners": [person_dict(self.person_1.id)],
        "notify_on_change": False,
    }

    self.task_group_historical = {
        "title": "task group historical title",
        "contact": person_dict(self.person_1.id),
    }

    self.task_group_tasks_historical = [{
        "title": "task historical title 1",
        "description": "task historical description 1",
        "contact": person_dict(self.person_1.id),
        "start_date": "05/01/2014",
        "end_date": "05/06/2014",
    }, {
        "title": "task historical title 2",
        "description": "task historical description 2",
        "contact": person_dict(self.person_1.id),
        "start_date": "05/07/2014",
        "end_date": "05/12/2014",
    }, {
        "title": "task historical title 3",
        "description": "task historical description 3",
        "contact": person_dict(self.person_1.id),
        "start_date": "05/13/2014",
        "end_date": "05/18/2014",
    }, {
        "title": "task historical title 4",
        "description": "task historical description 4",
        "contact": person_dict(self.person_1.id),
        "start_date": "05/19/2014",
        "end_date": "05/24/2014",
    }, {
        "title": "task historical title 5",
        "description": "task historical description 5",
        "contact": person_dict(self.person_1.id),
        "start_date": "05/25/2014",
        "end_date": "05/30/2014",
    },
    ]

    # Historical cycle tasks which should be generated from previous structure
    # at the beginning of each test.
    self.generated_cycle_tasks_historical = {
        "CYCLETASK-6": {
            "title": self.task_group_tasks_historical[0]["title"],
            "description": self.task_group_tasks_historical[0]["description"],
            "start_date": "2014-05-01",
            "end_date": "2014-05-06",
            "finished_date": "None",
            "verified_date": "None",
            "status": "Assigned"
        },
        "CYCLETASK-7": {
            "title": self.task_group_tasks_historical[1]["title"],
            "description": self.task_group_tasks_historical[1]["description"],
            "start_date": "2014-05-07",
            "end_date": "2014-05-12",
            "finished_date": "None",
            "verified_date": "None",
            "status": "Declined"
        },
        "CYCLETASK-8": {
            "title": self.task_group_tasks_historical[2]["title"],
            "description": self.task_group_tasks_historical[2]["description"],
            "start_date": "2014-05-13",
            "end_date": "2014-05-18",
            "finished_date": "None",
            "verified_date": "None",
            "status": "InProgress"
        },
        "CYCLETASK-9": {
            "title": self.task_group_tasks_historical[3]["title"],
            "description": self.task_group_tasks_historical[3]["description"],
            "start_date": "2014-05-19",
            "end_date": "2014-05-24",
            "finished_date": "2014-05-01 00:00:00",
            "verified_date": "None",
            "status": "Finished"
        },
        "CYCLETASK-10": {
            "title": self.task_group_tasks_historical[4]["title"],
            "description": self.task_group_tasks_historical[4]["description"],
            "start_date": "2014-05-25",
            "end_date": "2014-05-30",
            "finished_date": "2014-05-01 00:00:00",
            "verified_date": "2014-05-01 00:00:00",
            "status": "Verified"
        }
    }

    # Expected cycle tasks which should be created in correct cycle task update
    # case. It is needed for most tests.
    self.expected_cycle_task_correct = {
        "CYCLETASK-1": {
            "title": self.task_group_tasks_active[0]["title"] + " one",
            "description":
                self.task_group_tasks_active[0]["description"] + " one",
            "start_date": "2016-06-01",
            "end_date": "2016-06-06",
            "finished_date": "None",
            "verified_date": "None",
            "status": "Assigned"
        },
        "CYCLETASK-2": {
            "title": self.task_group_tasks_active[1]["title"] + " two",
            "description":
                self.task_group_tasks_active[1]["description"] + " two",
            "start_date": "2016-06-07",
            "end_date": "2016-06-12",
            "finished_date": "None",
            "verified_date": "None",
            "status": "Declined"
        },
        "CYCLETASK-3": {
            "title": self.task_group_tasks_active[2]["title"] + " three",
            "description":
                self.task_group_tasks_active[2]["description"] + " three",
            "start_date": "2016-06-13",
            "end_date": "2016-06-18",
            "finished_date": "None",
            "verified_date": "None",
            "status": "InProgress"
        },
        "CYCLETASK-4": {
            "title": self.task_group_tasks_active[3]["title"] + " four",
            "description":
                self.task_group_tasks_active[3]["description"] + " four",
            "start_date": "2016-06-19",
            "end_date": "2016-06-24",
            "finished_date": "2016-07-19 00:00:00",
            "verified_date": "None",
            "status": "Finished"
        },
        "CYCLETASK-5": {
            "title": self.task_group_tasks_active[4]["title"] + " five",
            "description":
                self.task_group_tasks_active[4]["description"] + " five",
            "start_date": "2016-06-25",
            "end_date": "2016-06-30",
            "finished_date": "2016-07-25 00:00:00",
            "verified_date": "2016-08-30 00:00:00",
            "status": "Verified"
        },
        "CYCLETASK-6": {
            "title": self.task_group_tasks_historical[0]["title"] + " one",
            "description":
                self.task_group_tasks_historical[0]["description"] + " one",
            "start_date": "2014-04-01",
            "end_date": "2014-04-06",
            "finished_date": "2014-05-01 00:00:00",
            "verified_date": "2014-06-06 00:00:00",
            "status": "Assigned"
        },
        "CYCLETASK-7": {
            "title": self.task_group_tasks_historical[1]["title"] + " two",
            "description":
                self.task_group_tasks_historical[1]["description"] + " two",
            "start_date": "2014-04-07",
            "end_date": "2014-04-12",
            "finished_date": "2014-05-07 00:00:00",
            "verified_date": "None",
            "status": "Declined"
        },
        "CYCLETASK-8": {
            "title": self.task_group_tasks_historical[2]["title"] + " three",
            "description":
                self.task_group_tasks_historical[2]["description"] + " three",
            "start_date": "2014-04-13",
            "end_date": "2014-04-18",
            "finished_date": "2014-05-13 00:00:00",
            "verified_date": "2014-06-18 00:00:00",
            "status": "InProgress"
        },
        "CYCLETASK-9": {
            "title": self.task_group_tasks_historical[3]["title"] + " four",
            "description":
                self.task_group_tasks_historical[3]["description"] + " four",
            "start_date": "2014-04-19",
            "end_date": "2014-04-24",
            "finished_date": "2014-05-19 00:00:00",
            "verified_date": "None",
            "status": "Finished"
        },
        "CYCLETASK-10": {
            "title": self.task_group_tasks_historical[4]["title"] + " five",
            "description":
                self.task_group_tasks_historical[4]["description"] + " five",
            "start_date": "2014-04-25",
            "end_date": "2014-04-30",
            "finished_date": "2014-05-25 00:00:00",
            "verified_date": "2014-06-30 00:00:00",
            "status": "Verified"
        }
    }

    # Below is description of warning for non-importable columns. It is needed
    # for test_cycle_task_warnings.
    importable_column_names = []
    for field_name in CycleTaskGroupObjectTask.IMPORTABLE_FIELDS:
      if field_name == 'slug':
        continue
      # pylint: disable=protected-access
      importable_column_names.append(
          CycleTaskGroupObjectTask._aliases.get(field_name, field_name))
    self.expected_warnings = {
        'Cycle Task Group Object Task': {
            'block_warnings': {
                errors.ONLY_IMPORTABLE_COLUMNS_WARNING.format(
                    line=2,
                    columns=", ".join(importable_column_names)
                )
            },
        }
    }

    # This is an error message which should be shown during
    # test_cycle_task_create_error test
    self.expected_create_error = {
        'Cycle Task Group Object Task': {
            'row_errors': {errors.CREATE_INSTANCE_ERROR.format(line=13)}
        }
    }

    # Below is expected date errors for test_cycle_task_date_error. They should
    # be shown during date validator's tests.
    self.expected_date_error = {
        'Cycle Task Group Object Task': {
            'row_errors': {
                errors.INVALID_START_END_DATES.format(
                    line=3,
                    start_date="Start Date",
                    end_date="End Date",
                ),
                errors.INVALID_STATUS_DATE_CORRELATION.format(
                    line=4,
                    date="Actual Finish Date",
                    status="not Finished",
                ),
                errors.INVALID_STATUS_DATE_CORRELATION.format(
                    line=5,
                    date="Actual Verified Date",
                    status="not Verified",
                ),
                errors.INVALID_STATUS_DATE_CORRELATION.format(
                    line=6,
                    date="Actual Verified Date",
                    status="not Verified",
                ),
                errors.INVALID_START_END_DATES.format(
                    line=7,
                    start_date="Actual Finish Date",
                    end_date="Actual Verified Date",
                ),
                errors.INVALID_START_END_DATES.format(
                    line=8,
                    start_date="Start Date",
                    end_date="End Date",
                ),
                errors.MISSING_VALUE_ERROR.format(
                    line=9,
                    column_name="Actual Finish Date",
                ),
                errors.INVALID_START_END_DATES.format(
                    line=10,
                    start_date="Actual Finish Date",
                    end_date="Actual Verified Date",
                ),
            },
        }
    }
    # Below is expected cycle-tasks data which should appear in test DB after
    # test_cycle_task_date_error run
    self.expected_cycle_task_date_error = dict()
    self.expected_cycle_task_date_error.update(
        self.generated_cycle_tasks_active)
    self.expected_cycle_task_date_error.update(
        self.generated_cycle_tasks_historical)
    self.expected_cycle_task_date_error["CYCLETASK-9"] = (
        self.expected_cycle_task_correct["CYCLETASK-9"])
    self.expected_cycle_task_date_error["CYCLETASK-10"] = (
        self.expected_cycle_task_correct["CYCLETASK-10"])

    # Expected error message which should be shown after
    # test_cycle_task_permission_error run
    self.expected_permission_error = {
        'Cycle Task Group Object Task': {
            'block_errors': {errors.PERMISSION_ERROR.format(line=2)}
        }
    }
