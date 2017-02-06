# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

# pylint: disable=maybe-no-member

"""Test Assessment Template import."""

from ggrc import models
from ggrc.converters import errors
from integration.ggrc import TestCase


class TestAssessmentTemplatesImport(TestCase):
  """Assessment Template import tests."""

  def setUp(self):
    """Set up for Assessment Template test cases."""
    super(TestAssessmentTemplatesImport, self).setUp()
    self.client.get("/login")

  def test_valid_import(self):
    """Test valid import."""
    response = self.import_file("assessment_template_no_warnings.csv")
    expected_messages = {
        "Assessment Template": {
            "rows": 4,
            "updated": 0,
            "created": 4,
        }
    }
    self._check_csv_response(response, expected_messages)

    people = {p.email: p.id for p in models.Person.query.all()}
    template = models.AssessmentTemplate.query \
        .filter(models.AssessmentTemplate.slug == "T-2") \
        .first()

    self.assertEqual(
        template.default_people["verifiers"],
        [people["user3@a.com"], people["user1@a.com"]],
    )

  def test_invalid_import(self):
    """Test invalid import."""
    data = "assessment_template_with_warnings_and_errors.csv"
    response = self.import_file(data)

    expected_messages = {
        "Assessment Template": {
            "rows": 4,
            "updated": 0,
            "created": 3,
            "row_errors": {
                errors.MISSING_VALUE_ERROR.format(
                    line=5, column_name="Default Verifier")
            },
            "row_warnings": {
                errors.UNKNOWN_USER_WARNING.format(
                    line=5,
                    column_name="Default Verifier",
                    email="user3@a.com",
                ),
                errors.UNKNOWN_USER_WARNING.format(
                    line=5,
                    column_name="Default Verifier",
                    email="user1@a.com"
                ),
            },
        }
    }
    self._check_csv_response(response, expected_messages)
