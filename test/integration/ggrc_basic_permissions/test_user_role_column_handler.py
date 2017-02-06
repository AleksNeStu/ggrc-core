# Copyright (C) 2016 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Tests for UserRoleColumnHandler methods."""

from os.path import abspath
from os.path import dirname
from os.path import join
from ggrc.converters import errors
from integration.ggrc import TestCase


class TestUserRoleColumnHandler(TestCase):
  """ Test for UserRoleColumnHandler class functionality"""

  CSV_DIR = join(abspath(dirname(__file__)), "test_csvs")

  def setUp(self):
    TestCase.setUp(self)
    self.client.get("/login")

  def test_user_role_title(self):
    """ Test for user role handling

    Tests the correctness of handling user role while importing from csv.
    Correct roles pass without errors, for incorrect role error is generated
    for the whole row.
    """
    response_json = self.import_file("import_with_user_role.csv")
    expected_errors = {
        errors.WRONG_VALUE.format(line="4", column_name="Role"),
        errors.WRONG_VALUE.format(line="7", column_name="Role"),
        errors.WRONG_VALUE.format(line="8", column_name="Role"),
    }

    self.assertEqual(5, response_json[0]["created"])
    self.assertEqual(3, response_json[0]["ignored"])

    response_errors = response_json[0]["row_errors"]
    self.assertEqual(expected_errors, set(response_errors))
