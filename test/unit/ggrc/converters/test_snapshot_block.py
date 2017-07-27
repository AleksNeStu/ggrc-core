# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Unit tests for Snapshot block converter class."""

from collections import OrderedDict

import unittest
import mock
import ddt

from ggrc.converters.snapshot_block import SnapshotBlockConverter


@ddt.ddt
class TestSnapshotBlockConverter(unittest.TestCase):
  """Unit tests for Snapshot block converter."""
  # Removing protected access checks because we wish to tests even the
  # protected functions.
  # pylint: disable=protected-access

  def setUp(self):
    super(TestSnapshotBlockConverter, self).setUp()
    converter = mock.MagicMock()
    ids = []
    self.block = SnapshotBlockConverter(converter, ids)

  @staticmethod
  def _mock_snapshot_factory(content_list):
    return [mock.MagicMock(content=content) for content in content_list]

  @classmethod
  def _dummy_cad_snapshots(cls):
    return cls._mock_snapshot_factory([{
        "id": 44,
        "global_attributes": [
            {"id": 1, "title": "CCC"},
            {"id": 2, "title": "BBB"},
        ],
    }, {
        "id": 45,
        "global_attributes": [
            {"id": 1, "title": "CCC"},
            {"id": 3, "title": "AAA"},
            {"id": 4, "title": "DDD"},
        ],
    }])

  def test_gather_stubs(self):
    """Test _gather_stubs method."""
    self.block.snapshots = self._mock_snapshot_factory([{
        "id": 44,
        "owners": [
            {"type": "person", "id": 1},
            {"type": "person", "id": 2},
        ],
        "contact": {"type": "person", "id": 2},
        "cavs": [
            {"cav_value": {"type": "person", "id": 3}},
            {
                "cav_value": {"type": "option", "id": 3},
                "type": "cav",
                "id": 6,
            },
        ],
        "options": [{"type": "option", "id": 1}],
    }, {
        "id": 44,
        "type": "other",
        "options": [{"type": "option", "id": 4}],
    }])
    stubs = self.block._gather_stubs()
    self.assertEqual(
        stubs,
        {
            "person": {1, 2, 3},
            "option": {1, 3, 4},
            "other": {44},
            "cav": {6},
        }
    )

  def test_cad_map(self):
    """Test gathering name map for all custom attribute definitions."""
    self.block.snapshots = self._dummy_cad_snapshots()
    self.assertEqual(
        self.block._cad_map.items(),
        [
            (3, "AAA"),
            (2, "BBB"),
            (1, "CCC"),
            (4, "DDD"),
        ]
    )

  @mock.patch("ggrc.converters.snapshot_block.models")
  @mock.patch("ggrc.converters.snapshot_block.AttributeInfo")
  def test_attribute_name_map(self, attribute_info, _):
    """Test getting attribute name map for a valid model."""
    self.block.child_type = "Dummy"
    attribute_info.gather_visible_aliases.return_value = {
        "key_1": "BBB",
        "key_2": "DDD",
        "key_3": {"display_name": "AAA"},
        "key_4": {"display_name": "CCC"},
    }
    attribute_info.get_column_order.return_value = [
        "key_3",
        "audit",
        "key_2",
        "key_1",
        "key_4",
    ]
    self.assertEqual(
        self.block._attribute_name_map.items(),
        [
            ("key_3", "AAA"),
            ("audit", "Audit"),  # inserted snapshot attribute
            ("key_2", "DDD"),
            ("key_1", "BBB"),
            ("key_4", "CCC"),
        ]
    )

  @mock.patch("ggrc.converters.snapshot_block.models")
  def test_bad_attribute_name_map(self, models):
    """Test getting attribute name map for an invalid model."""
    self.block.child_type = "Dummy"
    models.all_models.Dummy = None
    self.assertEqual(
        self.block._attribute_name_map.items(),
        []
    )

  @ddt.data(
      ({"random_item": "Random value"}, "random_item", "Random value"),
      ({"dummy_item": "stored_value_1"}, "dummy_item", "User Text"),
      ({"dummy_item": True}, "dummy_item", "Stored boolean value"),
      ({"dummy_item": None}, "dummy_item", ""),
  )
  @ddt.unpack
  def test_get_content_string(self, content, attr_name, expected_value):
    """Test getting content for special mapped values."""
    self.block.get_value_string = lambda x: x or ""
    self.block.child_type = "Dummy Object"
    self.block._content_value_map = {
        "Dummy Object": {
            "dummy_item": {
                "stored_value_1": "User Text",
                True: "Stored boolean value",
            }
        }
    }
    self.assertEqual(
        self.block.get_content_string(content, attr_name),
        expected_value
    )

  @ddt.data(
      ({"dummy_date": None}, "dummy_date", ""),
      ({"dummy_date": ""}, "dummy_date", ""),
      ({"random_item": "Random value", }, "random_item", "Random value"),
      ({"dummy_date": "2022-02-22", }, "dummy_date", "02/22/2022"),
      ({"dummy_date": "2017-04-08T17:57:09", }, "dummy_date",
          "2017-04-08 17:57:09"),
  )
  @ddt.unpack
  def test_get_content_string_date(self, content, attr_name, expected_value):
    """Test getting content for date values."""
    self.block.get_value_string = lambda x: x or ""
    self.block.DATE_FIELDS = {
        "dummy_date"
    }
    self.assertEqual(
        self.block.get_content_string(content, attr_name),
        expected_value
    )

  @ddt.data(
      (None, ""),
      ([], ""),
      ({}, ""),
      (True, "yes"),
      (False, "no"),
      ("Foo", "Foo"),
      ({"type": "Fake", "id": 4}, ""),
      ({"type": "Dummy", "id": -3}, ""),
      ({"type": "Dummy", "id": 1}, "AAA"),
      (
          [
              {"type": "Dummy", "id": 1},
              {"type": "Object", "id": 1},
              {"type": "Dummy", "id": 3},
          ],
          "AAA\nDDD\nCCC"
      ),
  )
  @ddt.unpack
  def test_get_value_string(self, value, expected_value):
    """Test get value string function for all value types."""
    self.block._stub_cache = {
        "Dummy": {
            1: "AAA",
            2: "BBB",
            3: "CCC",
        },
        "Object": {
            1: "DDD",
        }
    }
    self.assertEqual(self.block.get_value_string(value), expected_value)

  @ddt.data(
      ({"name": "1", "third": "2", "other": "3", }, ["1", "3", "2"]),
      ({"name": "1", "third": "2", }, ["1", "", "2"]),
  )
  @ddt.unpack
  def test_obj_attr_line(self, content, expected_line):
    """Test get object attribute CSV values."""
    self.block.get_content_string = lambda x, name: x.get(name, "")
    self.block._attribute_name_map = OrderedDict([
        ("name", "display name"),
        ("other", "other display name"),
        ("third", "third display name"),
    ])
    self.assertEqual(self.block._obj_attr_line(content), expected_line)

  @ddt.data(
      ({}, ["", "", ""]),
      ({"global_attributes": []}, ["", "", ""]),
      ({"global_attributes": [{"id": 5, "values": [{"value": "five"}]},
                              {"id": 3, "values": [{"value": "three"}]}]},
       ["three", "", "five"]),
      ({"global_attributes": [{"id": 5, "values": [{"value": "five"}]},
                              {"id": 8, "values": [{"value": "eight"}]}]},
       ["", "", "five"]),
  )
  @ddt.unpack
  def test_cav_attr_line(self, content, expected_line):
    """Test get custom attribute CSV values."""
    self.block._cad_map = OrderedDict([(3, "AAA"), (2, "BBB"), (5, "DDD")])
    self.assertEqual(self.block._cav_attr_line(content), expected_line)

  def test_header_list(self):
    """Test snapshot export header data."""
    self.block._attribute_name_map = OrderedDict([
        ("key_3", "AAA"),
        ("audit", "Audit"),  # inserted snapshot attribute
        ("key_2", "DDD"),
        ("key_1", "BBB"),
        ("key_4", "CCC"),
    ])
    self.block._cad_map = OrderedDict([
        (3, "A"),
        (2, "B"),
        (1, "C"),
        (4, "D"),
    ])
    self.assertEquals(
        self.block._header_list,
        [[], ["AAA", "Audit", "DDD", "BBB", "CCC", "A", "B", "C", "D"]]
    )

  @ddt.data(
      ([], [[]]),
      ([1, 2, 3], [[], [], []]),
  )
  @ddt.unpack
  def test_body_list(self, snapshots, block_list):
    """Test basic CSV body format."""
    self.block._content_line_list = lambda x: []
    self.block.snapshots = snapshots
    self.assertEqual(self.block._body_list, block_list)
