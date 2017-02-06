# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>


"""Tests for workflow specific imports."""

from datetime import date
from os.path import abspath
from os.path import dirname
from os.path import join

from integration.ggrc import TestCase

from ggrc import db
from ggrc.converters import errors
from ggrc_workflows.models.task_group import TaskGroup
from ggrc_workflows.models.task_group_object import TaskGroupObject
from ggrc_workflows.models.task_group_task import TaskGroupTask
from ggrc_workflows.models.workflow import Workflow

THIS_ABS_PATH = abspath(dirname(__file__))


class TestWorkflowObjectsImport(TestCase):
  """Test imports for basic workflow objects."""

  CSV_DIR = join(THIS_ABS_PATH, "test_csvs/")

  def setUp(self):
    super(TestWorkflowObjectsImport, self).setUp()
    self.client.get("/login")

  def test_full_good_import(self):
    """Test full good import without any warnings."""
    filename = "workflow_small_sheet.csv"
    response = self.import_file(filename)

    self._check_csv_response(response, {})

    self.assertEqual(1, Workflow.query.count())
    self.assertEqual(1, TaskGroup.query.count())
    self.assertEqual(4, TaskGroupTask.query.count())
    self.assertEqual(2, TaskGroupObject.query.count())

    task2 = TaskGroupTask.query.filter_by(slug="t-2").first()
    task3 = TaskGroupTask.query.filter_by(slug="t-3").first()
    task4 = TaskGroupTask.query.filter_by(slug="t-4").first()
    self.assertEqual(task2.start_date, date(2015, 7, 10))
    self.assertEqual(task2.end_date, date(2016, 12, 30))
    self.assertIn("ch2", task3.response_options)
    self.assertIn("option 1", task4.response_options)

  def test_bad_imports(self):
    """Test workflow import with errors and warnings"""
    filename = "workflow_with_warnings_and_errors.csv"
    response = self.import_file(filename)

    expected_errors = {
        "Workflow": {
            "row_errors": {
                errors.MISSING_VALUE_ERROR.format(
                    line=8, column_name="Manager")
            },
        }
    }
    self._check_csv_response(response, expected_errors)

  def test_import_task_date_format(self):
    """Test import of tasks for workflows

    This is a test for various imports of task dates for all types of
    workflows. This test ignores all warnings returned by the file import,
    since those are verified in a different test.

    Raises:
      AssertionError: if the start and end values on tasks don't match the
        values in the imported csv files.
    """
    filename = "workflow_big_sheet.csv"
    self.import_file(filename)

    # Assert that CSV import got imported correctly
    getters = {
        "one_time": lambda task: (task.start_date, task.end_date),
        "weekly": lambda task: (task.relative_start_day,
                                task.relative_end_day),
        "monthly": lambda task: (task.relative_start_day,
                                 task.relative_end_day),
        "quarterly": lambda task: ((task.relative_start_month,
                                    task.relative_start_day),
                                   (task.relative_end_month,
                                    task.relative_end_day)),
        "annually": lambda task: ((task.relative_start_month,
                                   task.relative_start_day),
                                  (task.relative_end_month,
                                   task.relative_end_day))
    }

    tasks = [
        ["task-1", "one_time", (date(2015, 7, 1), date(2015, 7, 15))],
        ["task-2", "weekly", (2, 5)],
        ["task-3", "monthly", (1, 22)],
        ["task-4", "quarterly", ((1, 5), (2, 15))],
        ["task-10", "quarterly", ((3, 5), (1, 1))],
        ["task-11", "quarterly", ((3, 5), (1, 1))],
        ["task-5", "annually", ((5, 7), (7, 15))],
    ]

    for slug, freq, result in tasks:
      task = db.session.query(TaskGroupTask).filter(
          TaskGroupTask.slug == slug).one()
      getter = getters[freq]
      self.assertEqual(task.task_group.workflow.frequency, freq)
      self.assertEqual(
          getter(task), result,
          "Failed importing data for task with slug = '{}'".format(slug))

  def test_import_task_types(self):
    """Test task import with warnings

    Check that the warnings for bay task type field work and that the task type
    gets set to default when an invalid values is found in the csv.

    Raises:
      AssertionError: When file import does not return correct errors for the
        example csv, or if any of the tasks does not have the expected task
        type.

    """
    filename = "workflow_big_sheet.csv"
    response = self.import_file(filename)
    expected_errors = {
        "Task Group Task": {
            "row_warnings": {
                errors.WRONG_REQUIRED_VALUE.format(
                    line=38, value="aaaa", column_name="Task Type"
                ),
                errors.MISSING_VALUE_WARNING.format(
                    line=39, default_value="Rich Text", column_name="Task Type"
                ),
                errors.MISSING_VALUE_WARNING.format(
                    line=40, default_value="Rich Text", column_name="Task Type"
                ),
            }
        },
    }
    self._check_csv_response(response, expected_errors)

    task_types = {
        "text": [
            "task-1",
            "task-2",
            "task-4",
            "task-7",
            "task-9",
            "task-10",
            "task-11",
        ],
        "menu": [
            "task-5",
            "task-8",
        ],
        "checkbox": [
            "task-3",
            "task-6",
        ],
    }

    for task_type, slugs in task_types.items():
      self._test_task_types(task_type, slugs)

  def test_bad_task_dates(self):
    """Test import updates with invalid task dates.

    This import checks if it's possible to update task dates with start date
    being bigger than the end date.
    """
    self.import_file("workflow_small_sheet.csv")
    response = self.import_file("workflow_bad_task_dates.csv")

    expected_errors = {
        "Task Group Task": {
            "row_errors": {
                errors.INVALID_START_END_DATES.format(
                    line=4, start_date="Start date", end_date="End date"),
                errors.INVALID_START_END_DATES.format(
                    line=5, start_date="Start date", end_date="End date"),
                errors.INVALID_START_END_DATES.format(
                    line=6, start_date="Start date", end_date="End date"),
                errors.INVALID_START_END_DATES.format(
                    line=7, start_date="Start date", end_date="End date"),
            }
        },
    }
    self._check_csv_response(response, expected_errors)

  def test_malformed_task_dates(self):
    """Test import updates with malformed task dates.

    Check that the warnings for task dates in MM/DD/YYYY format of annually
    workflow are shown up and YYYY part of date is ignored.

    Raises:
      AssertionError: When file import does not return correct warnings for the
        example csv, or if any of the tasks does not have the expected
        relative dates.
    """
    response = self.import_file("workflow_malformed_task_dates.csv")

    expected_errors = {
        "Task Group Task": {
            "row_warnings": {
                errors.WRONG_DATE_FORMAT.format(line=15, column_name="Start"),
                errors.WRONG_DATE_FORMAT.format(line=15, column_name="End"),
                errors.WRONG_DATE_FORMAT.format(line=16, column_name="Start"),
                errors.WRONG_DATE_FORMAT.format(line=17, column_name="End"),
            },
        },
    }
    self._check_csv_response(response, expected_errors)
    task_slugs = ["t-1", "t-2", "t-3", "t-4"]
    tasks = db.session.query(TaskGroupTask).filter(
        TaskGroupTask.slug.in_(task_slugs)).all()
    for task in tasks:
      self.assertEqual(task.relative_start_month, 7)
      self.assertEqual(task.relative_start_day, 10)
      self.assertEqual(task.relative_end_month, 12)
      self.assertEqual(task.relative_end_day, 30)

  def _test_task_types(self, expected_type, task_slugs):
    """Test that all listed tasks have rich text type.

    This is a part of the test_import_task_date_format

    Args:
      expected_type: Expected task type for all tasks specified by task_slugs.
      task_slugs: list of slugs for the tasks that will be tested.

    Raises:
      AssertionError: if any of the tasks does not exists or if their type is
        not text.
    """
    tasks = db.session.query(TaskGroupTask).filter(
        TaskGroupTask.slug.in_(task_slugs)).all()
    for task in tasks:
      self.assertEqual(
          task.task_type,
          expected_type,
          "task '{}' has type '{}', expected '{}'".format(
              task.slug,
              task.task_type,
              expected_type,
          )
      )
    self.assertEqual(len(tasks), len(task_slugs))
