# Copyright (C) 2017 Google Inc.

# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

import mock
import unittest

import ggrc
from ggrc.models.mixins import Base
from ggrc.models.relationship import Relationship
from ggrc.models.relationship import RelationshipAttr


class RelationshipAttrTestMockModel(Base, ggrc.db.Model):
  __tablename__ = 'relationship_attr_test_mock_model'

  @staticmethod
  def _validate_relationship_attr(cls, source, destination, old, name, value):
    if cls.__name__ not in {source.type, destination.type}:
      return None
    if name != "validated_attr":
      return None
    try:
      int(value)
    except ValueError:
      return None
    return value


class TestRelationshipAttr(unittest.TestCase):

  def setUp(self):
    super(TestRelationshipAttr, self).setUp()

    m1 = RelationshipAttrTestMockModel()
    m2 = RelationshipAttrTestMockModel()
    self.rules_patcher = mock.patch("ggrc.utils.rules."
                                    "get_mapping_validation_rules")
    self.rules_mock = self.rules_patcher.start()
    self.rules_mock.return_value = {
        "RelationshipAttrTestMockModel": "RelationshipAttrTestMockModel",
    }
    self.rel = Relationship(source=m1, destination=m2)

    self.mapper_mock = mock.Mock(name='mapper')
    self.connection_mock = mock.Mock(name='connection')

  def tearDown(self):
    self.rules_patcher.stop()
    super(TestRelationshipAttr, self).tearDown()

  def test_attrs_validation_ok(self):
    self.rel.attrs["validated_attr"] = "123"

    # not raises ValueError
    self.rel.validate_attrs(self.mapper_mock, self.connection_mock, self.rel)

  def test_attrs_validation_invalid_attr(self):
    self.rel.attrs["foo"] = "bar"

    with self.assertRaises(ValueError):
      self.rel.validate_attrs(self.mapper_mock, self.connection_mock, self.rel)

  def test_attrs_validation_invalid_value(self):
    self.rel.attrs["validated_attr"] = "wrong value"

    with self.assertRaises(ValueError):
      self.rel.validate_attrs(self.mapper_mock, self.connection_mock, self.rel)

  def test_gather_validators(self):
    class ValidatorParent(object):
      @staticmethod
      def _validate_relationship_attr(cls):
        return True

    class ValidatorChild(ValidatorParent):
      @staticmethod
      def _validate_relationship_attr(cls):
        return False

    validators = RelationshipAttr._gather_validators(ValidatorChild)
    self.assertEqual({True, False}, {v() for v in validators})
