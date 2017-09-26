# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

# pylint: disable=maybe-no-member, invalid-name

"""Test Issue import and updates."""
from collections import OrderedDict

import ddt

from ggrc import models
from ggrc.converters import errors

from integration.ggrc.models import factories
from integration.ggrc import TestCase


@ddt.ddt
class TestImportIssues(TestCase):
  """Basic Issue import tests."""

  def setUp(self):
    """Set up for Issue test cases."""
    super(TestImportIssues, self).setUp()
    self.client.get("/login")

  def test_basic_issue_import(self):
    """Test basic issue import."""
    audit = factories.AuditFactory()
    for i in range(2):
      response = self.import_data(OrderedDict([
          ("object_type", "Issue"),
          ("Code*", ""),
          ("Title*", "Test issue {}".format(i)),
          ("Admin*", "user@example.com"),
          ("map:Audit", audit.slug),
      ]))
      self._check_csv_response(response, {})

    for issue in models.Issue.query:
      self.assertIsNotNone(
          models.Relationship.find_related(issue, audit),
          "Could not find relationship between: {} and {}".format(
              issue.slug, audit.slug)
      )

  def test_audit_change(self):
    """Test audit changing"""
    with factories.single_commit():
      audit = factories.AuditFactory()
      issue = factories.IssueFactory()

    response = self.import_data(OrderedDict([
        ("object_type", "Issue"),
        ("Code*", issue.slug),
        ("map:Audit", audit.slug),
    ]))
    self._check_csv_response(response, {})
    another_audit = factories.AuditFactory()

    response = self.import_data(OrderedDict([
        ("object_type", "Issue"),
        ("Code*", issue.slug),
        ("map:Audit", another_audit.slug),
    ]))
    self._check_csv_response(response, {
        "Issue": {
            "row_warnings": {
                errors.SINGLE_AUDIT_RESTRICTION.format(
                    line=3, mapped_type="Audit", object_type="Issue",
                )
            }
        }
    })

  @ddt.data(
      ("Deprecated", "Deprecated", 0),
      ("Fixed", "Deprecated", 1),
      ("Deprecated", "Fixed", 0),
  )
  @ddt.unpack
  def test_issue_deprecate_change(self, start_state, final_state, dep_count):
    """Test counter on changing state to deprecate"""
    with factories.single_commit():
      factories.AuditFactory()
      issue = factories.IssueFactory(status=start_state)

    response = self.import_data(OrderedDict([
        ("object_type", "Issue"),
        ("Code*", issue.slug),
        ("State", final_state),
    ]))
    self._check_csv_response(response, {})
    self.assertEqual(dep_count, response[0]['deprecated'])
    self.assertEqual(final_state, models.Issue.query.get(issue.id).status)

  def test_issue_state_import(self):
    """Test import of issue state."""
    audit = factories.AuditFactory()
    statuses = ["Fixed", "Fixed and Verified"]
    imported_data = []
    for i in range(2):
      imported_data.append(OrderedDict([
          ("object_type", "Issue"),
          ("Code*", ""),
          ("Title*", "Test issue {}".format(i)),
          ("Admin*", "user@example.com"),
          ("map:Audit", audit.slug),
          ("State", statuses[i]),
      ]))

    response = self.import_data(*imported_data)
    self._check_csv_response(response, {})
    db_statuses = [i.status for i in models.Issue.query.all()]
    self.assertEqual(statuses, db_statuses)

  def test_import_with_mandatory(self):
    """Test import of data with mandatory role"""
    # Import of data should be allowed if mandatory role provided
    # and can process situation when nonmandatory roles are absent
    # without any errors and warnings
    with factories.single_commit():
      mandatory_role = factories.AccessControlRoleFactory(
          object_type="Market",
          mandatory=True
      ).name
      factories.AccessControlRoleFactory(
          object_type="Market",
          mandatory=False
      )
      email = factories.PersonFactory().email

    response_json = self.import_data(OrderedDict([
        ("object_type", "Market"),
        ("code", "market-1"),
        ("title", "Title"),
        ("Admin", "user@example.com"),
        (mandatory_role, email),
    ]))
    self._check_csv_response(response_json, {})
    self.assertEqual(1, response_json[0]["created"])
    self.assertEqual(1, len(models.Market.query.all()))

  def test_import_without_mandatory(self):
    """Test import of data without mandatory role"""
    # Data can't be imported if mandatory role is not provided
    with factories.single_commit():
      mandatory_role = factories.AccessControlRoleFactory(
          object_type="Market",
          mandatory=True
      ).name
      not_mandatory_role = factories.AccessControlRoleFactory(
          object_type="Market",
          mandatory=False
      ).name
      email = factories.PersonFactory().email

    response_json = self.import_data(OrderedDict([
        ("object_type", "Market"),
        ("code", "market-1"),
        ("title", "Title"),
        ("Admin", "user@example.com"),
        (not_mandatory_role, email),
    ]))

    expected_errors = {
        "Market": {
            "row_errors": {
                errors.MISSING_COLUMN.format(
                    line=3, column_names=mandatory_role, s=""
                ),
            }
        }
    }
    self._check_csv_response(response_json, expected_errors)

    markets_count = models.Market.query.count()
    self.assertEqual(markets_count, 0)

  def test_import_empty_mandatory(self):
    """Test import of data with empty mandatory role"""
    with factories.single_commit():
      mandatory_role = factories.AccessControlRoleFactory(
          object_type="Market",
          mandatory=True
      ).name
      not_mandatory_role = factories.AccessControlRoleFactory(
          object_type="Market",
          mandatory=False
      ).name
      email = factories.PersonFactory().email

    response_json = self.import_data(OrderedDict([
        ("object_type", "Market"),
        ("code", "market-1"),
        ("title", "Title"),
        ("Admin", "user@example.com"),
        (not_mandatory_role, email),
        (mandatory_role, ""),
    ]))

    expected_errors = {
        "Market": {
            "row_warnings": {
                errors.OWNER_MISSING.format(
                    line=3, column_name=mandatory_role
                ),
            }
        }
    }

    self._check_csv_response(response_json, expected_errors)

    market_counts = models.Market.query.count()
    self.assertEqual(market_counts, 1)
