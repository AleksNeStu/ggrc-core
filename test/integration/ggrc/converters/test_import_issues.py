# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

# pylint: disable=maybe-no-member, invalid-name

"""Test Issue import and updates."""
from collections import OrderedDict

import ddt

from ggrc import models
from ggrc.models import all_models
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

  def _import_issue(self, slug, additional_fields=None,
                    expected_errors=None):
    """Do a typical import for a Issue with optional additional fields."""
    if expected_errors is None:
      expected_errors = {}

    if additional_fields is None:
      additional_fields = []

    self._check_csv_response(self.import_data(OrderedDict([
        ("object_type", "Issue"),
        ("Code*", slug),
        ("Title*", slug + " title"),
        ("Admin*", "user@example.com"),
    ] + additional_fields)), expected_errors)

  def test_import_no_audit(self):
    """Issue can be imported with no Audit."""

    self._import_issue("Issue with no Audit")

    self._import_issue("Another issue with no Audit", additional_fields=[
        ("Map:Audit", ""),
    ])

  def test_import_with_audit(self):
    """Issue can be imported with Audit."""
    audit = factories.AuditFactory()

    self._import_issue("Issue with audit", additional_fields=[
        ("Map:Audit", audit.slug),
    ])

    audit = all_models.Audit.query.one()
    issue = all_models.Issue.query.one()

    self.assertIsNotNone(all_models.Relationship.find_related(issue, audit))
    self.assertEqual(issue.audit_id, audit.id)
    self.assertEqual(issue.context_id, audit.context_id)

  def test_map_audit(self):
    """Issue can be mapped to Audit through import."""
    self._import_issue("Issue with Audit mapped", additional_fields=[
        ("Map:Audit", ""),
    ])
    audit = factories.AuditFactory()

    self._import_issue("Issue with Audit mapped", additional_fields=[
        ("Map:Audit", audit.slug),
    ])

    audit = all_models.Audit.query.one()
    issue = all_models.Issue.query.one()

    self.assertIsNotNone(all_models.Relationship.find_related(issue, audit))
    self.assertEqual(issue.audit_id, audit.id)
    self.assertEqual(issue.context_id, audit.context_id)

  def test_unmap_audit(self):
    """Issue can be unmapped from Audit through import."""
    audit = factories.AuditFactory()
    slug = audit.slug
    self._import_issue("Issue with Audit unmapped", additional_fields=[
        ("Map:Audit", slug),
    ])

    self._import_issue("Issue with Audit unmapped", additional_fields=[
        ("Unmap:Audit", slug),
    ])

    audit = all_models.Audit.query.one()
    issue = all_models.Issue.query.one()
    self.assertIsNone(all_models.Relationship.find_related(issue, audit))
    self.assertIsNone(issue.audit_id)
    self.assertIsNone(issue.context_id)

  def test_map_snapshottable(self):
    """Snapshottable objects can be mapped to Issue through import."""
    self._import_issue("Issue with Control mapped")

    control = factories.ControlFactory()

    self._import_issue("Issue with Control mapped", additional_fields=[
        ("Map:Control", control.slug),
    ])

    control = all_models.Control.query.one()
    issue = all_models.Issue.query.one()

    self.assertIsNotNone(all_models.Relationship.find_related(control, issue))

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
