# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Tests for Snapshot block converter class."""

import mock

from ggrc.converters.snapshot_block import SnapshotBlockConverter
from integration.ggrc import TestCase
from integration.ggrc.models import factories


class TestSnapshotBlockConverter(TestCase):
  """Tests for Snapshot block converter."""
  # Removing protected access checks because we wish to tests even the
  # protected functions.
  # pylint: disable=protected-access

  def test_empty_snapshots(self):
    """Test snapshots property for empty ids list."""
    converter = mock.MagicMock()
    block = SnapshotBlockConverter(converter, [])
    self.assertEqual(block.snapshots, [])

  def test_snapshots_property(self):
    """Test snapshots property and snapshot content."""
    with factories.single_commit():
      snapshots = self._create_snapshots(
          factories.AuditFactory(),
          factories.ControlFactory(),
      )

    converter = mock.MagicMock()
    ids = [s.id for s in snapshots]
    block = SnapshotBlockConverter(converter, ids)
    self.assertEqual(block.snapshots, snapshots)
    for snapshot in snapshots:
      self.assertIn("audit", snapshot.content)

  def test_valid_child_types(self):
    """Test child_type property with valid snapshots list."""
    with factories.single_commit():
      snapshots = self._create_snapshots(
          factories.AuditFactory(),
          factories.ControlFactory(),
          factories.ControlFactory(),
      )
    converter = mock.MagicMock()
    ids = [s.id for s in snapshots]
    block = SnapshotBlockConverter(converter, ids)
    self.assertEqual(block.child_type, "Control")

  def test_empty_child_type(self):
    """Test child_type property with empty snapshots list."""
    converter = mock.MagicMock()
    block = SnapshotBlockConverter(converter, [])
    self.assertEqual(block.child_type, "")

  def test_invalid_child_types(self):
    """Test child_type property with invalid snapshots list."""
    with factories.single_commit():
      snapshots = self._create_snapshots(
          factories.AuditFactory(),
          factories.ControlFactory(),
          factories.PolicyFactory(),
      )
    converter = mock.MagicMock()
    ids = [s.id for s in snapshots]
    block = SnapshotBlockConverter(converter, ids)
    with self.assertRaises(AssertionError):
      block.child_type = block.child_type

  def test_attribute_name_map(self):
    """Test Control snapshot name map and order."""
    converter = mock.MagicMock()
    block = SnapshotBlockConverter(converter, [])
    block.child_type = "Control"
    self.assertEqual(
        block._attribute_name_map.items(),
        [
            ('slug', 'Code'),
            ('audit', 'Audit'),  # inserted attribute
            ('revision_date', 'Revision Date'),  # inserted attribute
            ('title', 'Title'),
            ('description', 'Description'),
            ('notes', 'Notes'),
            ('test_plan', 'Test Plan'),
            ('start_date', 'Effective Date'),
            ('end_date', 'Last Deprecated Date'),
            ('status', 'State'),
            ('os_state', 'Review State'),
            ('assertions', 'Assertions'),
            ('categories', 'Categories'),
            ('fraud_related', 'Fraud Related'),
            ('key_control', 'Significance'),
            ('kind', 'Kind/Nature'),
            ('means', 'Type/Means'),
            ('reference_url', 'Reference URL'),
            ('verify_frequency', 'Frequency'),
            ('document_evidence', 'Evidence'),
            ('last_assessment_date', 'Last Assessment Date'),
        ]
    )
