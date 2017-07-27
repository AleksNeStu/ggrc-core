# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Integration test for custom attributable mixin"""

import copy

from ggrc import db

from integration.ggrc import TestCase
from integration.ggrc.models.factories import ProgramFactory
from integration.ggrc.models.factories import \
    CustomAttributeDefinitionFactory as CAD


class TestCustomAttributableMixin(TestCase):

  """Test cases for functions in custom attributable mixin."""

  def test_ca_setattr(self):
    """Test setting custom attribute values with setattr."""
    prog = ProgramFactory()
    cad1 = CAD(definition_type="program", title="CA 1",)

    setattr(
        prog,
        "global_attributes",
        [{
            "id": cad1.id,
            "values": [{"value": "55"}],
        }])
    db.session.commit()
    prog = prog.__class__.query.get(prog.id)

    self.assertEqual(
        {"55"},
        set(v.attribute_value for v in prog.custom_attribute_values),
    )
    self.assertEqual(len(prog.custom_attribute_values), 1)

  def test_setting_ca_dict(self):
    """Test setting custom attribute values dict."""
    prog = ProgramFactory()
    cad1 = CAD(definition_type="program", title="CA 1",)
    cad2 = CAD(definition_type="program", title="CA 2",)

    prog.global_attributes = [
        {
            "id": cad1.id,
            "values": [{"value": "55"}],
        }, {
            "id": cad2.id,
            "values": [{"value": "129aaaaaa"}],
        },
    ]
    db.session.commit()
    prog = prog.__class__.query.get(prog.id)

    self.assertEqual(
        {"55", "129aaaaaa"},
        set(v.attribute_value for v in prog.custom_attribute_values),
    )
    self.assertEqual(len(prog.custom_attribute_values), 2)

  def test_updating_ca_dict(self):
    """Test updating custom attribute values with a dict."""
    prog = ProgramFactory()
    cad1 = CAD(definition_type="program", title="CA 1",)

    prog.global_attributes = [{
        "id": cad1.id,
        "values": [{"value": "55"}],
    }]
    db.session.commit()
    prog = prog.__class__.query.get(prog.id)

    data = copy.deepcopy(prog.global_attributes)
    for cad in data:
      if cad["id"] == cad1.id:
        cad["values"][0]["value"] = "57"
    prog.global_attributes = data
    self.assertEqual(len(prog.custom_attribute_values), 1)
    self.assertEqual(prog.custom_attribute_values[0].attribute_value, "57")

  def test_adding_bad_ca_dict(self):
    """Test setting invalid custom attribute values."""
    prog = ProgramFactory()
    cad1 = CAD(definition_type="section", title="CA 1",)

    with self.assertRaises(ValueError):
      prog.global_attributes = [{
          "id": -1,
          "values": [{"value": "55"}],
      }]

    with self.assertRaises(ValueError):
      prog.global_attributes = [{
          "id": cad1.id,
          "values": [{"value": "55"}],
      }]

  def test_adding_mapping_ca_dict(self):
    """Test adding mapping custom attribute values with a dict."""
    cad1 = CAD(definition_type="program",
               attribute_type="Map:Person", title="CA 1",)
    cad2 = CAD(definition_type="program",
               attribute_type="Map:Person", title="CA 2",)
    db.session.commit()

    prog = ProgramFactory()
    prog.global_attributes = [
        {"id": cad1.id, "values": [{"value": "1"}]},
        {"id": cad2.id, "values": [{"value": 1}]},
    ]
    prog.validate_custom_attributes()
    prog = prog.__class__.query.get(prog.id)

    current_values = {
        c.custom_attribute.id: (c.attribute_value, c.attribute_object_id)
        for c in prog.custom_attribute_values}

    self.assertEqual(("Person", 1), current_values[cad1.id])
    self.assertEqual(("Person", 1), current_values[cad2.id])
    self.assertEqual(len(prog.custom_attribute_values), 2)
