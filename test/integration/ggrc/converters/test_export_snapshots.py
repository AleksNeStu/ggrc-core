# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Tests for snapshot export."""


from ggrc import models
from ggrc.utils import QueryCounter
from integration.ggrc import TestCase
from integration.ggrc.models import factories


class TestExportSnapshots(TestCase):
  """Tests basic snapshot export."""

  def setUp(self):
    super(TestExportSnapshots, self).setUp()
    self.client.get("/login")
    self.headers = {
        "Content-Type": "application/json",
        "X-Requested-By": "GGRC",
        "X-export-view": "blocks",
    }

  def test_simple_export(self):
    """Test simple empty snapshot export."""
    search_request = [{
        "object_name": "Snapshot",
        "filters": {
            "expression": {
                "left": "child_type",
                "op": {"name": "="},
                "right": "Control",
            },
        },
    }]
    parsed_data = self.export_parsed_csv(search_request)["Snapshot"]
    self.assertEqual(parsed_data, [])

  @staticmethod
  def _get_cav(control, cad_name):
    """Get proper CA value for a given CAD name."""
    for cav in control.custom_attribute_values:
      if cav.custom_attribute.title == cad_name:
        if cav.custom_attribute.attribute_type == "Checkbox":
          return u"yes" if int(cav.attribute_value) else u"no"
        elif cav.custom_attribute.attribute_type == "Map:Person":
          return cav.attribute_object.email if cav.attribute_object else u""
        elif cav.custom_attribute.attribute_type == "Date":
          parts = cav.attribute_value.split("-")
          return u"{}/{}/{}".format(parts[1], parts[2], parts[0])

        return cav.attribute_value
    return u""

  @staticmethod
  def _create_cads(type_):
    with factories.single_commit():
      cad = factories.CustomAttributeDefinitionFactory
      return [
          cad(title="date", definition_type=type_, attribute_type="Date"),
          cad(title="checkbox", definition_type=type_,
              attribute_type="Checkbox"),
          cad(title="person", definition_type=type_,
              attribute_type="Map:Person"),
          cad(title="RT", definition_type=type_, attribute_type="Rich Text"),
          cad(title="dropdown",
              definition_type=type_,
              attribute_type="Dropdown",
              multi_choice_options="one,two,three,four,five"),
      ]

  def test_full_control_export(self):
    """Test exporting of a single full control snapshot."""
    self._create_cads("control")
    self.import_file("control_snapshot_data_single.csv")
    # Duplicate import because we have a bug in logging revisions and this
    # makes sure that the fixture created properly.
    self.import_file("control_snapshot_data_single.csv")

    controls = models.Control.query.all()
    with factories.single_commit():
      audit = factories.AuditFactory()
      snapshots = self._create_snapshots(audit, controls)

    control_dicts = {
        control.slug: {
            # normal fields
            "Code": "*" + control.slug,
            "Revision Date": unicode(snapshot.revision.created_at),
            "Control URL": control.url,
            "Description": control.description,
            "Effective Date": control.start_date.strftime("%m/%d/%Y"),
            "Fraud Related": u"yes" if control.fraud_related else u"no",
            "Frequency": control.verify_frequency.display_name,
            "Kind/Nature": control.kind.display_name,
            "Notes": control.notes,
            "Reference URL": control.reference_url,
            "Review State": control.os_state,
            "Significance": u"key" if control.key_control else u"non-key",
            "State": control.status,
            "Last Deprecated Date": control.end_date.strftime("%m/%d/%Y"),
            "Test Plan": control.test_plan,
            "Title": control.title,
            "Type/Means": control.means.display_name,
            # Custom attributes
            "RT": self._get_cav(control, "RT"),
            "checkbox": self._get_cav(control, "checkbox"),
            "date": self._get_cav(control, "date"),
            "dropdown": self._get_cav(control, "dropdown"),
            "person": self._get_cav(control, "person"),
            # Special snapshot export fields
            "Audit": audit.slug,
            "Evidence": u"\n".join(c.slug for c in control.document_evidence),
            "Assertions": u"\n".join(c.name for c in control.assertions),
            "Categories": u"\n".join(c.name for c in control.categories),
            # Computed attributes
            "Last Assessment Date": u"",
        }
        for snapshot, control in zip(snapshots, controls)
    }

    search_request = [{
        "object_name": "Snapshot",
        "filters": {
            "expression": {
                "left": "child_type",
                "op": {"name": "="},
                "right": "Control",
            },
        },
    }]
    parsed_data = self.export_parsed_csv(search_request)["Control Snapshot"]
    parsed_dict = {line["Code"]: line for line in parsed_data}

    self.assertEqual(
        parsed_dict["*Control 1"],
        control_dicts["Control 1"],
    )

  def test_snapshot_mappings_export(self):
    """Test exporting snapshots with object mappings."""
    with factories.single_commit():
      control = factories.ControlFactory(slug="Control 1")
      audit = factories.AuditFactory()
      snapshot = self._create_snapshots(audit, [control])[0]
      assessments = [factories.AssessmentFactory() for _ in range(3)]
      issues = [factories.IssueFactory() for _ in range(3)]
      assessment_slugs = {assessment.slug for assessment in assessments}
      issue_slugs = {issue.slug for issue in issues}

      for assessment, issue in zip(assessments, issues):
        factories.RelationshipFactory(source=snapshot, destination=assessment)
        factories.RelationshipFactory(source=issue, destination=snapshot)

    search_request = [{
        "object_name": "Snapshot",
        "filters": {
            "expression": {
                "left": "child_type",
                "op": {"name": "="},
                "right": "Control",
            },
        },
        "fields": ["mappings"]
    }]
    parsed_data = self.export_parsed_csv(search_request)["Control Snapshot"]
    exported_control_dict = parsed_data[0]

    self.assertEqual(
        set(exported_control_dict["Map: Assessment"].splitlines()),
        assessment_slugs,
    )
    self.assertEqual(
        set(exported_control_dict["Map: Issue"].splitlines()),
        issue_slugs,
    )

  def test_empty_control_export(self):
    """Test exporting of a single full control snapshot."""
    cads = self._create_cads("control")
    with factories.single_commit():
      controls = [factories.ControlFactory(slug="Control 1")]
      for cad in cads:
        factories.CustomAttributeValueFactory(
            attributable=controls[0],
            custom_attribute=cad,
        )
      audit = factories.AuditFactory()
      snapshots = self._create_snapshots(audit, controls)

    control_dicts = {
        control.slug: {
            # normal fields
            "Code": "*" + control.slug,
            "Revision Date": unicode(snapshot.revision.created_at),
            "Control URL": u"",
            "Description": u"",
            "Effective Date": u"",
            "Fraud Related": u"",
            "Frequency": u"",
            "Kind/Nature": u"",
            "Notes": u"",
            "Reference URL": u"",
            "Review State": u"Unreviewed",
            "Significance": u"",
            "State": u"Draft",
            "Last Deprecated Date": u"",
            "Test Plan": u"",
            "Title": control.title,
            "Type/Means": u"",
            # Special snapshot export fields
            "Audit": audit.slug,
            # Computed attributes
            "Last Assessment Date": u"",

            # Custom attributes
            "RT": u"",
            "checkbox": u"no",
            "date": u"",
            "dropdown": u"",
            "person": u"",

            # Fields that are not included in snapshots - Known bugs.
            "Assertions": u"",
            "Categories": u"",
            "Evidence": u"",
        }
        for snapshot, control in zip(snapshots, controls)
    }

    search_request = [{
        "object_name": "Snapshot",
        "filters": {
            "expression": {
                "left": "child_type",
                "op": {"name": "="},
                "right": "Control",
            },
        },
    }]
    parsed_data = self.export_parsed_csv(search_request)["Control Snapshot"]
    parsed_dict = {line["Code"]: line for line in parsed_data}

    self.assertEqual(
        parsed_dict["*Control 1"],
        control_dicts["Control 1"],
    )

  def test_same_revison_export(self):
    """Exporting the same revision multiple times."""
    with factories.single_commit():
      controls = [factories.ControlFactory(slug="Control 1")]
      audit1 = factories.AuditFactory()
      self._create_snapshots(audit1, controls)
      audit2 = factories.AuditFactory()
      self._create_snapshots(audit2, controls)
      audit_codes = {audit1.slug, audit2.slug}

    search_request = [{
        "object_name": "Snapshot",
        "filters": {
            "expression": {
                "left": "child_type",
                "op": {"name": "="},
                "right": "Control",
            },
        },
    }]
    parsed_data = self.export_parsed_csv(search_request)["Control Snapshot"]

    self.assertEqual(
        [line["Code"] for line in parsed_data],
        ["*Control 1", "*Control 1"],
    )
    self.assertEqual(
        {line["Audit"] for line in parsed_data},
        audit_codes,
    )

  def test_export_query_count(self):
    """Test for a constant number of queries for snapshot export

    The number of database queries should not be linked to the amount of data
    that is being exported.
    """
    self._create_cads("control")
    self.import_file("control_snapshot_data_multiple.csv")
    # Duplicate import because we have a bug in logging revisions and this
    # makes sure that the fixture created properly.
    self.import_file("control_snapshot_data_multiple.csv")

    controls = models.Control.query.all()
    with factories.single_commit():
      audit = factories.AuditFactory()
      snapshots = self._create_snapshots(audit, controls)
      count = len(snapshots)
      assessments = [factories.AssessmentFactory() for _ in range(count)]
      issues = [factories.IssueFactory() for _ in range(count)]

      for snapshot, assessment, issue in zip(snapshots, assessments, issues):
        factories.RelationshipFactory(source=snapshot, destination=assessment)
        factories.RelationshipFactory(source=issue, destination=snapshot)

    with QueryCounter() as counter:
      search_request = [{
          "object_name": "Snapshot",
          "filters": {
              "expression": {
                  "left": {
                      "left": "child_type",
                      "op": {"name": "="},
                      "right": "Control",
                  },
                  "op": {"name": "AND"},
                  "right": {
                      "left": "Code",
                      "op": {"name": "="},
                      "right": "Control 1",
                  },
              },
          },
          "fields": ["mappings"],
      }]
      self.assertEqual(
          len(self.export_parsed_csv(search_request)["Control Snapshot"]),
          1,
      )
      single_query_count = counter.get

    with QueryCounter() as counter:
      search_request = [{
          "object_name": "Snapshot",
          "filters": {
              "expression": {
                  "left": "child_type",
                  "op": {"name": "="},
                  "right": "Control",
              },
          },
          "fields": ["mappings"],
      }]
      self.assertEqual(
          len(self.export_parsed_csv(search_request)["Control Snapshot"]),
          5,
      )
      multiple_query_count = counter.get

    self.assertEqual(multiple_query_count, single_query_count)
