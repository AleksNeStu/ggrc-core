# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Integration test for custom attributable mixin"""

from ggrc import db
from ggrc import models

from integration.ggrc import TestCase
from integration.ggrc.models.factories import ProgramFactory
from integration.ggrc.models.factories import \
    CustomAttributeDefinitionFactory as CAD


class TestCustomAttributableMixin(TestCase):

  """Test cases for functions in custom attributable mixin."""

  def test_setting_ca_values(self):
    """Test normal setting of custom attribute values."""
    prog = ProgramFactory()
    cad1 = CAD(definition_type="program", title="CA 1",)
    cad2 = CAD(definition_type="program", title="CA 2",)

    prog = prog.__class__.query.get(prog.id)

    val1 = models.CustomAttributeValue(
        attribute_value="55",
        custom_attribute=cad1,
    )
    val2 = models.CustomAttributeValue(
        attribute_value="129aaaaaa",
        custom_attribute=cad2,
    )

    prog.custom_attribute_values = [val1, val1, val1]
    db.session.commit()
    prog = prog.__class__.query.get(prog.id)
    self.assertEqual(len(prog.custom_attribute_values), 1)

    prog = ProgramFactory()
    prog.custom_attribute_values.append(val1)
    db.session.commit()
    prog = prog.__class__.query.get(prog.id)
    self.assertEqual(len(prog.custom_attribute_values), 1)
    self.assertEqual(
        {"55"},
        set(v.attribute_value for v in prog.custom_attribute_values),
    )

    prog = ProgramFactory()
    prog.custom_attribute_values = [val1, val2]
    db.session.commit()
    prog = prog.__class__.query.get(prog.id)

    self.assertEqual(
        {"55", "129aaaaaa"},
        set(v.attribute_value for v in prog.custom_attribute_values),
    )
    self.assertEqual(len(prog.custom_attribute_values), 2)

  def test_updating_ca_values(self):
    """Test updating custom attribute values."""
    cad1 = CAD(definition_type="program", title="CA 1",)

    val1 = models.CustomAttributeValue(
        attribute_value="55",
        custom_attribute=cad1,
    )

    prog = ProgramFactory()
    prog.custom_attribute_values = [val1]
    db.session.commit()

    prog = prog.__class__.query.get(prog.id)
    self.assertEqual(prog.custom_attribute_values[0].attribute_value, "55")

    val2 = models.CustomAttributeValue(
        attribute_value="129",
        custom_attribute=cad1,
    )

    prog.custom_attribute_values = [val2]
    db.session.commit()

    prog = prog.__class__.query.get(prog.id)
    self.assertEqual(prog.custom_attribute_values[0].attribute_value, "129")

  def test_ca_setattr(self):
    """Test setting custom attribute values with setattr."""
    prog = ProgramFactory()
    cad1 = CAD(definition_type="program", title="CA 1",)

    setattr(prog, "custom_attribute_values", [{
            "attribute_value": "55",
            "custom_attribute_id": cad1.id,
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

    prog.custom_attribute_values = [
        {
            "attribute_value": "55",
            "custom_attribute_id": cad1.id,
        }, {
            "attribute_value": "129aaaaaa",
            "custom_attribute_id": cad2.id,
        }
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

    prog.custom_attribute_values = [{
        "attribute_value": "55",
        "custom_attribute_id": cad1.id,
    }]
    db.session.commit()
    prog = prog.__class__.query.get(prog.id)

    prog.custom_attribute_values = [{
        "attribute_value": "57",
        "custom_attribute_id": cad1.id,
    }]

    self.assertEqual(len(prog.custom_attribute_values), 1)
    self.assertEqual(prog.custom_attribute_values[0].attribute_value, "57")

  def test_adding_bad_ca_dict(self):
    """Test setting invalid custom attribute values."""
    prog = ProgramFactory()
    cad1 = CAD(definition_type="section", title="CA 1",)

    with self.assertRaises(ValueError):
      prog.custom_attribute_values = [{
          "attribute_value": "55",
          "custom_attribute_id": -1
      }]
      prog.validate_custom_attributes()

    with self.assertRaises(ValueError):
      prog.custom_attribute_values = [{
          "attribute_value": "55",
          "custom_attribute_id": cad1.id,
      }]
      prog.validate_custom_attributes()

  def test_adding_mapping_ca_dict(self):
    """Test adding mapping custom attribute values with a dict."""
    cad1 = CAD(definition_type="program",
               attribute_type="Map:Person", title="CA 1",)
    cad2 = CAD(definition_type="program",
               attribute_type="Map:Person", title="CA 2",)
    db.session.commit()

    prog = ProgramFactory()
    prog.custom_attribute_values = [
        {
            "attribute_value": "Person:1",
            "custom_attribute_id": cad1.id,
        }, {
            "attribute_value": "Person",
            "attribute_object_id": "1",
            "custom_attribute_id": cad2.id,
        }
    ]
    prog.validate_custom_attributes()
    prog = prog.__class__.query.get(prog.id)

    self.assertEqual(
        {"1"},
        set(v.attribute_object_id for v in prog.custom_attribute_values),
    )
    self.assertEqual(
        {"Person"},
        set(v.attribute_value for v in prog.custom_attribute_values),
    )
    self.assertEqual(len(prog.custom_attribute_values), 2)
