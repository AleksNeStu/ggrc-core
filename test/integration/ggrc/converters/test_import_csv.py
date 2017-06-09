# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Tests for basic csv imports."""

from collections import OrderedDict

from ggrc import models
from ggrc.converters import errors
from integration.ggrc import TestCase
from integration.ggrc import generator
from integration.ggrc.models import factories


class TestBasicCsvImport(TestCase):
  """Test basic CSV imports."""

  def setUp(self):
    super(TestBasicCsvImport, self).setUp()
    self.generator = generator.ObjectGenerator()
    self.client.get("/login")

  def tearDown(self):
    pass

  def generate_people(self, people):
    for person in people:
      self.generator.generate_person({
          "name": person,
          "email": "{}@reciprocitylabs.com".format(person),
      }, "Administrator")

  def test_policy_basic_import(self):
    """Test basic policy import."""
    filename = "policy_basic_import.csv"
    self.import_file(filename)
    policies = models.Policy.query.count()
    self.assertEqual(policies, 3)
    revisions = models.Revision.query.filter(
        models.Revision.resource_type == "Policy"
    ).count()
    self.assertEqual(revisions, 6)
    policy = models.Policy.eager_query().first()
    self.assertEqual(policy.modified_by.email, "user@example.com")

  def test_policy_import_working_with_warnings(self):
    """Test Policy import with warnings."""
    def test_owners(policy):
      self.assertNotEqual([], policy.access_control_list)
      self.assertEqual(
          "user@example.com",
          policy.access_control_list[0].person.email
      )
      owner = models.Person.query.filter_by(email="user@example.com").first()
      self.assert_roles(policy, Admin=owner)

    filename = "policy_import_working_with_warnings.csv"
    response_json = self.import_file(filename)

    expected_warnings = {
        errors.UNKNOWN_USER_WARNING.format(line=3, email="miha@policy.com"),
        errors.UNKNOWN_OBJECT.format(
            line=3, object_type="Program", slug="p753"),
        errors.OWNER_MISSING.format(line=4, column_name="Admin"),
        errors.UNKNOWN_USER_WARNING.format(line=6, email="not@a.user"),
        errors.OWNER_MISSING.format(line=6, column_name="Admin"),
    }
    response_warnings = response_json[0]["row_warnings"]
    self.assertEqual(expected_warnings, set(response_warnings))
    response_errors = response_json[0]["row_errors"]
    self.assertEqual(set(), set(response_errors))
    self.assertEqual(4, response_json[0]["created"])

    policies = models.Policy.query.all()
    self.assertEqual(len(policies), 4)
    # Only 1 and 3 policies should have owners
    test_owners(policies[0])
    test_owners(policies[2])

  def test_policy_same_titles(self):
    """Test Policy imports with title collisions."""
    def test_owners(policy):
      self.assertNotEqual([], policy.access_control_list)
      self.assertEqual("user@example.com",
                       policy.access_control_list[0].person.email)
      owner = models.Person.query.filter_by(email="user@example.com").first()
      self.assert_roles(policy, Admin=owner)

    filename = "policy_same_titles.csv"
    response_json = self.import_file(filename)

    self.assertEqual(3, response_json[0]["created"])
    self.assertEqual(6, response_json[0]["ignored"])
    self.assertEqual(0, response_json[0]["updated"])
    self.assertEqual(9, response_json[0]["rows"])

    expected_errors = {
        errors.DUPLICATE_VALUE_IN_CSV.format(
            line_list="3, 4, 6, 10, 11", column_name="Title",
            value="A title", s="s", ignore_lines="4, 6, 10, 11"),
        errors.DUPLICATE_VALUE_IN_CSV.format(
            line_list="5, 7", column_name="Title", value="A different title",
            s="", ignore_lines="7"),
        errors.DUPLICATE_VALUE_IN_CSV.format(
            line_list="8, 9, 10, 11", column_name="Code", value="code",
            s="s", ignore_lines="9, 10, 11"),
    }
    response_errors = response_json[0]["row_errors"]
    self.assertEqual(expected_errors, set(response_errors))

    policies = models.Policy.query.all()
    self.assertEqual(len(policies), 3)
    for policy in policies:
      test_owners(policy)

  def test_intermappings(self):
    self.generate_people(["miha", "predrag", "vladan", "ivan"])

    filename = "intermappings.csv"
    response_json = self.import_file(filename)

    self.assertEqual(4, response_json[0]["created"])  # Facility
    self.assertEqual(4, response_json[1]["created"])  # Objective

    response_warnings = response_json[0]["row_warnings"]
    self.assertEqual(set(), set(response_warnings))
    self.assertEqual(13, models.Relationship.query.count())

    obj2 = models.Objective.query.filter_by(slug="O2").first()
    obj3 = models.Objective.query.filter_by(slug="O3").first()
    self.assertNotEqual(None, models.Relationship.find_related(obj2, obj2))
    self.assertEqual(None, models.Relationship.find_related(obj3, obj3))

  def test_policy_unique_title(self):
    filename = "policy_sample1.csv"
    response_json = self.import_file(filename)

    self.assertEqual(response_json[0]["row_errors"], [])

    filename = "policy_sample2.csv"
    response_json = self.import_file(filename)

    self.assertEqual(response_json[0]["row_errors"], [
        "Line 3: title 'will this work' already exists.Record will be ignored."
    ])

  def test_assessments_import_update(self):
    """Test for updating Assessment with import

    Checks for fields being updarted correctly
    """
    filename = "pci_program.csv"
    response = self.import_file(filename)

    self._check_csv_response(response, {})

    assessment = models.Assessment.query.filter_by(slug="CA.PCI 1.1").first()
    audit = models.Audit.query.filter_by(slug="AUDIT-Consolidated").first()
    self.assertEqual(assessment.design, "Effective")
    self.assertEqual(assessment.operationally, "Effective")
    self.assertIsNone(models.Relationship.find_related(assessment, audit))

    filename = "pci_program_update.csv"
    response = self.import_file(filename)

    self._check_csv_response(response, {
        "Assessment": {
            "row_warnings": {
                errors.UNMODIFIABLE_COLUMN.format(line=3, column_name="Audit")
            }
        }
    })

    assessment = models.Assessment.query.filter_by(slug="CA.PCI 1.1").first()
    audit = models.Audit.query.filter_by(slug="AUDIT-Consolidated").first()
    self.assertEqual(assessment.design, "Needs improvement")
    self.assertEqual(assessment.operationally, "Ineffective")
    self.assertIsNone(models.Relationship.find_related(assessment, audit))

  def test_person_imports(self):
    """Test imports for Person object with user roles."""
    filename = "people_test.csv"
    response = self.import_file(filename)[0]

    expected_errors = {
        errors.MISSING_VALUE_ERROR.format(line=8, column_name="Email"),
        errors.WRONG_VALUE_ERROR.format(line=10, column_name="Email"),
        errors.WRONG_VALUE_ERROR.format(line=11, column_name="Email"),
    }

    self.assertEqual(expected_errors, set(response["row_errors"]))
    self.assertEqual(0, models.Person.query.filter_by(email=None).count())

  def test_duplicate_people(self):
    """Test adding two of the same object people objects in the same row."""
    filename = "duplicate_object_person.csv"
    response = self.import_file(filename)[0]

    self.assertEqual(0, len(response["row_warnings"]))
    self.assertEqual(0, len(response["row_errors"]))

  def test_duplicate_people_objective(self):
    """Test duplicate error that causes request to fail."""
    self.generator.generate_object(models.Objective, {"slug": "objective1"})
    filename = "duplicate_object_person_objective_error.csv"
    response = self.import_file(filename)[0]

    self.assertEqual(0, len(response["row_warnings"]))
    self.assertEqual(0, len(response["row_errors"]))

  def test_audit_import_context(self):
    """Test audit context on edits via import."""
    factories.ProgramFactory(slug="p")
    response = self.import_data(OrderedDict([
        ("object_type", "Audit"),
        ("Code*", "audit"),
        ("title", "audit"),
        ("Internal Audit Lead", "user@example.com"),
        ("status", "In Progress"),
        ("program", "P"),
    ]))
    self._check_csv_response(response, {})

    audit = models.Audit.query.first()
    program = models.Program.query.first()
    self.assertNotEqual(audit.context_id, program.context_id)

    response = self.import_data(OrderedDict([
        ("object_type", "Audit"),
        ("Code*", "audit"),
        ("title", "audit"),
        ("Internal Audit Lead", "user@example.com"),
        ("status", "In Progress"),
        ("program", "P"),
    ]))
    self._check_csv_response(response, {})

    audit = models.Audit.query.first()
    program = models.Program.query.first()
    self.assertNotEqual(audit.context_id, program.context_id)
