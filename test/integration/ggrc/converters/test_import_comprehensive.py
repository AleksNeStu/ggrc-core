# -*- coding: utf-8 -*-

# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Comprehensive import tests.

These tests should eventually contain all good imports and imports with all
possible errors and warnings.
"""

import unittest

from ggrc import db
from ggrc.models import AccessGroup
from ggrc.models import Program
from ggrc.converters import errors
from ggrc_basic_permissions import Role
from ggrc_basic_permissions import UserRole
from integration.ggrc import TestCase
from integration.ggrc.generator import ObjectGenerator


class TestComprehensiveSheets(TestCase):

  """
  test sheet from:
    https://docs.google.com/spreadsheets/d/1Jg8jum2eQfvR3kZNVYbVKizWIGZXvfqv3yQpo2rIiD8/edit#gid=0

  """

  def setUp(self):
    super(TestComprehensiveSheets, self).setUp()
    self.generator = ObjectGenerator()
    self.client.get("/login")

  def test_comprehensive_with_ca(self):
    """Test comprehensive sheet with custom attributes."""
    self.create_custom_attributes()
    filename = "comprehensive_sheet1.csv"
    response = self.import_file(filename)
    indexed = {r["name"]: r for r in response}

    expected = {
        "Control": {
            "created": 14,
            "ignored": 2,
            "row_errors": 2,
            "row_warnings": 3,
            "rows": 16,
        },
        "Objective": {
            "created": 8,
            "ignored": 7,
            "row_errors": 5,
            "row_warnings": 4,
            "rows": 15,
        },
        "Program": {
            "created": 13,
            "ignored": 3,
            "row_errors": 3,
            "row_warnings": 4,
            "rows": 16,
        },
        "Policy": {
            "created": 13,
            "ignored": 3,
            "row_errors": 3,
            "row_warnings": 4,
            "rows": 16,
        },
        "Regulation": {
            "created": 13,
            "ignored": 2,
            "row_errors": 3,
            "row_warnings": 3,
            "rows": 15,
        },
        "Standard": {
            "created": 14,
            "ignored": 2,
            "row_errors": 3,
            "row_warnings": 4,
            "rows": 16,
        },
        "Contract": {
            "created": 14,
            "ignored": 2,
            "row_errors": 3,
            "row_warnings": 4,
            "rows": 16,
        },
        "System": {
            "created": 14,
            "ignored": 2,
            "row_errors": 3,
            "row_warnings": 4,
            "rows": 16,
        },
        "Clause": {
            "created": 14,
            "ignored": 2,
            "row_errors": 3,
            "row_warnings": 4,
            "rows": 16,
        },
        "Process": {
            "created": 14,
            "ignored": 2,
            "row_errors": 3,
            "row_warnings": 4,
            "rows": 16,
        },
        "Data Asset": {
            "created": 14,
            "ignored": 2,
            "row_errors": 3,
            "row_warnings": 4,
            "rows": 16,
        },
        "Product": {
            "created": 14,
            "ignored": 2,
            "row_errors": 3,
            "row_warnings": 4,
            "rows": 16,
        },
        "Project": {
            "created": 8,
            "ignored": 0,
            "row_errors": 0,
            "row_warnings": 0,
            "rows": 8,
        },
        "Facility": {
            "created": 14,
            "ignored": 2,
            "row_errors": 3,
            "row_warnings": 4,
            "rows": 16,
        },
        "Market": {
            "created": 13,
            "ignored": 2,
            "row_errors": 3,
            "row_warnings": 3,
            "rows": 15,
        },
        "Org Group": {
            "created": 13,
            "ignored": 2,
            "row_errors": 3,
            "row_warnings": 3,
            "rows": 15,
        },
        "Vendor": {
            "created": 13,
            "ignored": 2,
            "row_errors": 3,
            "row_warnings": 3,
            "rows": 15,
        },
        "Person": {
            "created": 13,
            "ignored": 1,
            "row_errors": 1,
            "row_warnings": 0,
            "rows": 14,
        }
    }

    # general numbers check
    for name, data in expected.items():
      current = indexed[name]
      self.assertEqual(current["rows"], data["rows"], name)
      self.assertEqual(current["ignored"], data["ignored"], name)
      self.assertEqual(current["created"], data["created"], name)
      self.assertEqual(len(current["row_errors"]), data["row_errors"], name)
      self.assertEqual(
          len(current["row_warnings"]), data["row_warnings"], name)

    prog = Program.query.filter_by(slug="prog-8").first()
    self.assertEqual(prog.title, "program 8")
    self.assertEqual(prog.status, "Draft")
    self.assertEqual(prog.description, "test")

    custom_vals = [v.attribute_value for v in prog.custom_attribute_values]
    expected_custom_vals = ['0', 'a', '2015-12-12', 'test1']
    self.assertEqual(set(custom_vals), set(expected_custom_vals))

  @unittest.skip("unskip when import/export fixed for workflows")
  def test_full_good_import(self):
    """Test import of all objects with no warnings or errors."""
    filename = "full_good_import_no_warnings.csv"
    response = self.import_file(filename)

    admin = db.session.query(Role.id).filter(Role.name == "Administrator")
    reader = db.session.query(Role.id).filter(Role.name == "Reader")
    creator = db.session.query(Role.id).filter(Role.name == "Creator")
    admins = UserRole.query.filter(UserRole.role_id == admin).all()
    readers = UserRole.query.filter(UserRole.role_id == reader).all()
    creators = UserRole.query.filter(UserRole.role_id == creator).all()
    access_groups = db.session.query(AccessGroup).all()
    self.assertEqual(len(admins), 12)
    self.assertEqual(len(readers), 5)
    self.assertEqual(len(creators), 6)
    self.assertEqual(len(access_groups), 10)

    expected_errors = {}
    self._check_csv_response(response, expected_errors)

  def test_errors_and_warnings(self):
    """Test all possible errors and warnings.

    This test should test for all possible warnings and errors but it is still
    incomplete.
    """
    response = self.import_file("import_with_all_warnings_and_errors.csv")
    expected_errors = {
        "Control": {
            "block_errors": {
                errors.DUPLICATE_COLUMN.format(
                    line=1, duplicates="title, assessment procedure, notes"),
            },
            "row_warnings": {
                errors.EXPORT_ONLY_WARNING.format(
                    line=55, column_name="Last Deprecated Date"),
                errors.EXPORT_ONLY_WARNING.format(
                    line=56, column_name="Last Deprecated Date"),
                errors.EXPORT_ONLY_WARNING.format(
                    line=57, column_name="Last Deprecated Date"),
                errors.EXPORT_ONLY_WARNING.format(
                    line=58, column_name="Last Deprecated Date"),
            },
        },
        "Program": {
            "row_warnings": {
                errors.OWNER_MISSING.format(
                    line=7, column_name="Program Managers"),
                errors.EXPORT_ONLY_WARNING.format(
                    line=7, column_name="Last Deprecated Date"),
                errors.EXPORT_ONLY_WARNING.format(
                    line=8, column_name="Last Deprecated Date"),
                errors.EXPORT_ONLY_WARNING.format(
                    line=9, column_name="Last Deprecated Date"),
            },
            "row_errors": {
                errors.UNKNOWN_DATE_FORMAT.format(
                    line=8, column_name="Effective Date"),
                errors.WRONG_VALUE_ERROR.format(
                    line=9, column_name="Effective Date"),
            },
        },
        "Assessment": {
            "row_warnings": {
                errors.UNKNOWN_OBJECT.format(
                    line=14, object_type="Audit", slug="x"),
            },
            "row_errors": {
                errors.MISSING_VALUE_ERROR.format(
                    line=14, column_name="Audit"),
                errors.MISSING_VALUE_ERROR.format(
                    line=15, column_name="Audit"),
            },
        },
        "Regulation": {
            "row_warnings": {
                errors.DUPLICATE_IN_MULTI_VALUE.format(
                    line=21,
                    column_name=u"Reference URL",
                    duplicates=u"double-url.com, duplicate-nonascii-url-€™.com"
                )
            }
        }
    }

    self._check_csv_response(response, expected_errors)

  def create_custom_attributes(self):
    """Generate custom attributes needed for comprehensive sheet."""
    gen = self.generator.generate_custom_attribute
    gen("control", title="my custom text", mandatory=True)
    gen("program", title="my_text", mandatory=True)
    gen("program", title="my_date", attribute_type="Date")
    gen("program", title="my_checkbox", attribute_type="Checkbox")
    gen("program", title="my_dropdown", attribute_type="Dropdown",
        options="a,b,c,d")
    # gen("program", title="my_description", attribute_type="Rich Text")

  def test_case_sensitive_slugs(self):
    """Test that mapping with case sensitive slugs work."""
    response = self.import_file("case_sensitive_slugs.csv")
    expected_errors = {
        "Control": {
            "row_errors": {
                errors.DUPLICATE_VALUE_IN_CSV.format(
                    line_list="3, 4",
                    column_name="Code",
                    s="",
                    value="a",
                    ignore_lines="4",
                ),
                errors.DUPLICATE_VALUE_IN_CSV.format(
                    line_list="3, 4",
                    column_name="Title",
                    s="",
                    value="a",
                    ignore_lines="4",
                ),
            }
        }
    }
    self._check_csv_response(response, expected_errors)

  @unittest.skip("unskip when import/export fixed for workflows")
  def test_task_groups_tasks(self):
    """Test task group task warnings and errors.

    These tests are taken from manual test grid:
    https://docs.google.com/spreadsheets/d/1sfNXxw_kmiw1r-\
      Qfzv1jUM48mpeZNjIAnLdSxiCQSsI/edit?pli=1#gid=627526582

    The import file had an additional users block that contains missing users.
    """
    response = self.import_file(
        "importing_task_group_task_warnings_and_errors.csv")

    expected_errors = {
        "Task Group Task": {
            "row_errors": {
                errors.MISSING_VALUE_ERROR.format(
                    line="5",
                    column_name="End",
                ),
                errors.MISSING_VALUE_ERROR.format(
                    line="4",
                    column_name="Start",
                ),
                errors.WRONG_VALUE_ERROR.format(
                    line="6",
                    column_name="Start",
                ),
                errors.WRONG_VALUE_ERROR.format(
                    line="7",
                    column_name="End",
                ),
            },
        },
    }
    self._check_csv_response(response, expected_errors)

  def test_missing_rich_text_field(self):
    """MISSING_VALUE_ERROR is returned on empty mandatory description."""
    response = self.import_file("risk_missing_mandatory_description.csv")

    expected_errors = {
        "Risk": {
            "row_errors": {
                errors.MISSING_VALUE_ERROR.format(
                    line="3",
                    column_name="Description",
                ),
            },
        },
    }
    self._check_csv_response(response, expected_errors)
