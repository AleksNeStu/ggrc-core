# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

# pylint: disable=maybe-no-member, invalid-name

"""Test request import and updates."""

from ggrc import db
from ggrc import models
from ggrc.converters import errors
from integration.ggrc import TestCase
from flask.json import dumps


class TestAssessmentImport(TestCase):
  """Basic Assessment import tests with.

  This test suite should test new Assessment imports, exports, and updates.
  The main focus of these tests is checking error messages for invalid state
  transitions.
  """

  def setUp(self):
    """Set up for Assessment test cases."""
    super(TestAssessmentImport, self).setUp()
    self.client.get("/login")

  def test_import_assessments_with_templates(self):
    """Test importing of assessments with templates."""

    self.import_file("assessment_template_no_warnings.csv")
    response = self.import_file("assessment_with_templates.csv")
    self._check_csv_response(response, {})

    assessment = models.Assessment.query.filter(
        models.Assessment.slug == "A 4").first()

    values = set(v.attribute_value for v in assessment.custom_attribute_values)
    self.assertIn("abc", values)
    self.assertIn("2015-07-15", values)

  def _test_assessment_users(self, asmt, users):
    """ Test that all users have correct roles on specified Assessment"""
    verification_errors = ""
    for user_name, expected_types in users.items():
      try:
        user = models.Person.query.filter_by(name=user_name).first()
        rel = models.Relationship.find_related(asmt, user)
        if expected_types:
          self.assertNotEqual(
              rel, None,
              "User {} is not mapped to {}".format(user.email, asmt.slug))
          self.assertIn("AssigneeType", rel.relationship_attrs)
          self.assertEqual(
              set(rel.relationship_attrs[
                  "AssigneeType"].attr_value.split(",")),
              expected_types
          )
        else:
          self.assertEqual(
              rel, None,
              "User {} is mapped to {}".format(user.email, asmt.slug))
      except AssertionError as error:
        verification_errors += "\n\nChecks for Users-Assessment mapping "\
            "failed for user '{}' with:\n{}".format(user_name, str(error))

    self.assertEqual(verification_errors, "", verification_errors)

  def test_assessment_full_no_warnings(self):
    """ Test full assessment import with no warnings

    CSV sheet:
      https://docs.google.com/spreadsheets/d/1Jg8jum2eQfvR3kZNVYbVKizWIGZXvfqv3yQpo2rIiD8/edit#gid=704933240&vpid=A7
    """
    response = self.import_file("assessment_full_no_warnings.csv")
    self._check_csv_response(response, {})

    # Test first Assessment line in the CSV file
    asmt_1 = models.Assessment.query.filter_by(slug="Assessment 1").first()
    users = {
        "user 1": {"Assessor"},
        "user 2": {"Assessor", "Creator"}
    }
    self._test_assessment_users(asmt_1, users)
    self.assertEqual(asmt_1.status, models.Assessment.START_STATE)

    # Test second Assessment line in the CSV file
    asmt_2 = models.Assessment.query.filter_by(slug="Assessment 2").first()
    users = {
        "user 1": {"Assessor"},
        "user 2": {"Creator"},
        "user 3": {},
        "user 4": {},
        "user 5": {},
    }
    self._test_assessment_users(asmt_2, users)
    self.assertEqual(asmt_2.status, models.Assessment.PROGRESS_STATE)

  def test_assessment_import_states(self):
    """ Test Assessment state imports

    These tests are an intermediate part for zucchini release and will be
    updated in the next release.

    CSV sheet:
      https://docs.google.com/spreadsheets/d/1Jg8jum2eQfvR3kZNVYbVKizWIGZXvfqv3yQpo2rIiD8/edit#gid=299569476
    """
    self.import_file("assessment_full_no_warnings.csv")
    response = self.import_file("assessment_update_intermediate.csv")
    expected_errors = {
        "Assessment": {
            "block_errors": set(),
            "block_warnings": set(),
            "row_errors": set(),
            "row_warnings": set(),
        }
    }
    self._check_csv_response(response, expected_errors)

    assessments = {r.slug: r for r in models.Assessment.query.all()}
    self.assertEqual(assessments["Assessment 60"].status,
                     models.Assessment.START_STATE)
    self.assertEqual(assessments["Assessment 61"].status,
                     models.Assessment.PROGRESS_STATE)
    self.assertEqual(assessments["Assessment 62"].status,
                     models.Assessment.DONE_STATE)
    self.assertEqual(assessments["Assessment 63"].status,
                     models.Assessment.FINAL_STATE)
    self.assertEqual(assessments["Assessment 64"].status,
                     models.Assessment.FINAL_STATE)
    self.assertEqual(assessments["Assessment 3"].status,
                     models.Assessment.FINAL_STATE)
    self.assertEqual(assessments["Assessment 4"].status,
                     models.Assessment.FINAL_STATE)

    # Check that there is only one attachment left
    asmt1 = assessments["Assessment 1"]
    self.assertEqual(len(asmt1.documents), 1)

    # Check that there are only the two new URLs present in asessment 1
    url_titles = set(obj.title for obj in asmt1.related_objects()
                     if isinstance(obj, models.Document))
    self.assertEqual(url_titles, set(["a.b.com", "c.d.com"]))

  def test_assessment_warnings_errors(self):
    """ Test full assessment import with warnings and errors

    CSV sheet:
      https://docs.google.com/spreadsheets/d/1Jg8jum2eQfvR3kZNVYbVKizWIGZXvfqv3yQpo2rIiD8/edit#gid=889865936
    """
    self.import_file("assessment_full_no_warnings.csv")
    response = self.import_file("assessment_with_warnings_and_errors.csv")

    expected_errors = {
        "Assessment": {
            "block_errors": set([]),
            "block_warnings": {
                errors.UNKNOWN_COLUMN.format(
                    line=2,
                    column_name="error description - non existing column will "
                    "be ignored"
                ),
                errors.UNKNOWN_COLUMN.format(
                    line=2,
                    column_name="actual error message"
                ),
            },
            "row_errors": {
                errors.MISSING_VALUE_ERROR.format(
                    line=19,
                    column_name="Audit"
                ),
                errors.DUPLICATE_VALUE_IN_CSV.format(
                    line_list="20, 22",
                    column_name="Code",
                    value="Assessment 22",
                    s="",
                    ignore_lines="22",
                ),
            },
            "row_warnings": {
                errors.UNKNOWN_OBJECT.format(
                    line=14,
                    object_type="Project",
                    slug="proj-55"
                ),
                errors.UNKNOWN_OBJECT.format(
                    line=19,
                    object_type="Audit",
                    slug="not existing"
                ),
                errors.WRONG_VALUE_DEFAULT.format(
                    line=20,
                    column_name="State",
                    value="open",
                ),
                errors.WRONG_VALUE.format(line=3, column_name="Url"),
            },
        }
    }
    self._check_csv_response(response, expected_errors)


class TestAssessmentExport(TestCase):
  """Test Assessment object export."""

  def setUp(self):
    """ Set up for Assessment test cases """
    super(TestAssessmentExport, self).setUp()
    self.client.get("/login")
    self.headers = {
        'Content-Type': 'application/json',
        "X-Requested-By": "GGRC",
        "X-export-view": "blocks",
    }

  def export_csv(self, data):
    return self.client.post("/_service/export_csv", data=dumps(data),
                            headers=self.headers)

  def test_simple_export(self):
    """ Test full assessment export with no warnings

    CSV sheet:
      https://docs.google.com/spreadsheets/d/1Jg8jum2eQfvR3kZNVYbVKizWIGZXvfqv3yQpo2rIiD8/edit#gid=704933240&vpid=A7
    """

    self.import_file("assessment_full_no_warnings.csv")
    data = [{
        "object_name": "Assessment",
        "filters": {"expression": {}},
        "fields": "all",
    }]
    response = self.export_csv(data)
    self.assertIn(u"\u5555", response.data.decode("utf8"))

  def test_export_assessments_with_filters_and_conflicting_ca_names(self):
    """Test exporting assessments with conflicting custom attribute names."""
    self.import_file(u"assessment_template_no_warnings.csv")
    self.import_file(u"assessment_with_templates.csv")

    # also create an object level custom attribute with a name that clashes
    # with a name of a "regular" attribute
    assessment = models.Assessment.query.filter(
        models.Assessment.slug == u"A 2").first()
    cad = models.CustomAttributeDefinition(
        attribute_type=u"Text",
        title=u"ca title",
        definition_type=u"assessment",
        definition_id=assessment.id
    )
    db.session.add(cad)
    db.session.commit()

    data = [{
        "object_name": "Assessment",
        "fields": ["slug", "title", "description", "status"],
        "filters": {
            "expression": {
                "left": {
                    "left": "code",
                    "op": {"name": "~"},
                    "right": "A 2"
                },
                "op": {"name": "AND"},
                "right": {
                    "left": "title",
                    "op": {"name": "~"},
                    "right": "no template Assessment"
                }
            },
            "keys": ["code", "title", "status"],
            "order_by": {
                "keys": [],
                "order": "",
                "compare": None
            }
        }
    }]

    response = self.export_csv(data)
    self.assertIn(u"No template Assessment 2", response.data)
