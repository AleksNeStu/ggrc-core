# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Tests for snapshot model."""

from ggrc.app import app
from ggrc.models import all_models
from ggrc.snapshotter.rules import Types
from integration.ggrc import TestCase
from integration.ggrc.models import factories


def get_snapshottable_models():
  return {getattr(all_models, stype) for stype in Types.all}


class TestSnapshot(TestCase):
  """Basic tests for /query api."""

  IGNORE_KEYS = {
      # currently not working fields:
      "audit_duration",
      "audit_duration_id",

      "audit_frequency",
      "audit_frequency_id",

      "directive",
      "directive_id",

      "kind",
      "kind_id",

      "means",
      "means_id",

      "meta_kind",

      "network_zone",
      "network_zone_id",

      "verify_frequency",
      "verify_frequency_id",

      "assertions",
      "categories",
      "categorizations",
      "categorized_assertions",

      # special fields not needed for snapshots.
      "display_name",
      "preconditions_failed",
      "type",
      "workflow_state",

      "selfLink",
      "viewLink",


      # relationships and mappings
      "audit_objects",
      "audits",
      "controls",
      "object_people",
      "objects",
      "people",
      "related_destinations",
      "related_sources",
      "risk_objects",
      "risks",
      "task_group_objects",
      "task_group_tasks",
      "task_groups",

      "children",
      "parent",
      "parent_id",

      # we don't need context for snapshots since they are all under an audit.
      "context",
      "context_id",

      # obsolete fields that will be removed
      "custom_attributes",

      # following fields have been handled in fields without _id prefix. That
      # means that "contact" fields should exists and have correct values.
      "contact_id",
      "secondary_contact_id",

      "principal_assessor_id",
      "secondary_assessor_id",

      "modified_by_id",

      "attribute_object_id",

      # revisions require complete data for documents,
      # while api returns only basic data in stubs
      "document_url",
      "document_evidence",
      "reference_url",

      # computed attributes are not stored in revisions and should be ignored.
      "attributes",
      "last_assessment_date",

      "access_control_list",  # TODO: remove this line (GGRC-2402)
  }

  def setUp(self):
    """Set up test cases for all tests."""
    super(TestSnapshot, self).setUp()
    self._create_cas()
    response = self._import_file("all_snapshottable_objects.csv")
    self._check_csv_response(response, {})

  @staticmethod
  def _create_cas():
    """Create custom attribute definitions."""
    ca_model_names = [
        "facility",
        "control",
        "market",
        "section",
        "threat",
        "access_group",
        "data_asset"
    ]
    ca_args = [
        {"title": "CA text", "attribute_type": "Text"},
        {"title": "CA rich text", "attribute_type": "Rich Text"},
        {"title": "CA date", "attribute_type": "Date"},
        {"title": "CA checkbox", "attribute_type": "Checkbox"},
        {"title": "CA person", "attribute_type": "Map:Person"},
        {"title": "CA dropdown", "attribute_type": "Dropdown",
         "multi_choice_options": "one,two,three,four,five"},
    ]
    for type_ in ca_model_names:
      with app.app_context():
        for args in ca_args:
          factories.CustomAttributeDefinitionFactory(
              definition_type=type_,
              **args
          )

  def test_revision_content(self):
    """Test that revision contains all content needed."""

    facility_revision = all_models.Revision.query.filter(
        all_models.Revision.resource_type == "Facility").order_by(
        all_models.Revision.id.desc()).first()

    self.assertIn("global_attributes", facility_revision.content)
    self.assertNotEqual(facility_revision.content["global_attributes"], [])
    self.assertIn("local_attributes", facility_revision.content)
    self.assertEqual(facility_revision.content["local_attributes"], [])

  def _get_object(self, obj):
    return self.client.get(
        "/api/{}/{}".format(obj._inflector.table_plural, obj.id)  # noqa # pylint: disable=protected-access
    ).json[obj._inflector.table_singular]  # noqa # pylint: disable=protected-access

  def _clean_json(self, content):
    """Remove ignored items from JSON content.

    This function removes all ignored items from dicts, changes dates to
    isoformat changes values to int or unicode, so that the end result is a
    dict that can be compared with the JSON dict that was received from the
    server.

    Args:
      content: object that we want to clean, it can be a dict list or a value.

    Returns:
      content with all values cleaned up
    """
    if isinstance(content, list):
      return sorted(self._clean_json(value) for value in content)

    if hasattr(content, 'isoformat'):
      return unicode(content.isoformat())

    if isinstance(content, int):
      # We convert all numbers to the same type so that the diff of a failed
      # test looks nicer. This conversion does not affect the test results just
      # the output.
      return long(content)

    if not isinstance(content, dict):
      return content

    clean = {}
    for key, value in content.items():
      if key not in self.IGNORE_KEYS:
        clean[str(key)] = self._clean_json(value)

    return clean

  def test_snapshot_content(self):
    """Test the content of stored revisions

    The content in the revision (that is set by log_json) must match closely to
    what the api returns for a get request. This ensures that when a model is
    created from a snapshot on the fronend, it will have all the needed fields.
    """
    self.client.get("/login")
    test_models = get_snapshottable_models()
    for model in test_models:
      obj = model.eager_query().first()
      generated_json = self._clean_json(obj.log_json())
      expected_json = self._clean_json(self._get_object(obj))
      self.assertEqual(expected_json, generated_json)
