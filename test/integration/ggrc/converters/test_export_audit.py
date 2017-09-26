# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Tests export of Audit and mapped objects."""
from collections import defaultdict

from ggrc import utils
from ggrc.snapshotter.rules import Types

from integration.ggrc import TestCase
from integration.ggrc.models import factories
from integration.ggrc.models.factories import get_model_factory


class TestAuditExport(TestCase):
  """Test export of Audit"""
  def setUp(self):
    super(TestAuditExport, self).setUp()
    self.client.get("/login")

  def test_export_audit_mappings(self):
    """Test export of audit mapped objects"""
    snap_objects = []
    mapped_slugs = defaultdict(list)
    with factories.single_commit():
      audit = factories.AuditFactory(slug="Audit")
      # Create a group of mapped objects for current audit
      for _ in range(3):
        # All snapshotable objects should be mapped to Audit + Issue
        # and Assessment
        for type_ in Types.all.union(Types.scoped):
          if type_ == "Issue":
            obj = get_model_factory(type_)()
            factories.RelationshipFactory(source=audit, destination=obj)
          elif type_ in Types.scoped:
            obj = get_model_factory(type_)(audit=audit)
            factories.RelationshipFactory(source=audit, destination=obj)
          else:
            obj = get_model_factory(type_)()
          mapped_slugs[type_].append(obj.slug)
          snap_objects.append(obj)

    self._create_snapshots(audit, snap_objects)

    audit_data = self.export_parsed_csv([{
        "object_name": "Audit",
        "filters": {
            "expression": {}
        },
        "fields": "all",
    }])["Audit"][0]

    for type_, slugs in mapped_slugs.items():
      if type_ in Types.all:
        format_ = "map:{} versions"
      else:
        format_ = "map:{}"
      mapping_name = format_.format(utils.title_from_camelcase(type_))
      self.assertIn(mapping_name, audit_data)
      self.assertEqual(audit_data[mapping_name], "\n".join(sorted(slugs)))
