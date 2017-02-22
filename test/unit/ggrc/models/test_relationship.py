# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Module for unit test suite for Relationship model."""

import unittest

import mock

import ggrc
from ggrc.models.exceptions import ValidationError
from ggrc.models.mixins import Base
from ggrc.models.relationship import Relationship


class MockModelA(Base, ggrc.db.Model):
  __tablename__ = "mock_model_a"


class MockModelB(Base, ggrc.db.Model):
  __tablename__ = "mock_model_b"


@mock.patch("ggrc.utils.rules.get_mapping_validation_rules")
class TestRelationship(unittest.TestCase):
  """Unit test suite for Relationship model."""

  def test_relationship_validation_ok(self, get_rules_mock):
    """Mapping of allowed source_type and destination_type is OK."""
    get_rules_mock.return_value = {
        "MockModelA": {"MockModelA", "MockModelB"},
        "MockModelB": {"MockModelA", "MockModelB"},
    }
    # nothing raises ValidationError
    for src, dst in [(MockModelA(), MockModelA()),
                     (MockModelA(), MockModelB()),
                     (MockModelB(), MockModelA()),
                     (MockModelB(), MockModelB())]:
      rel = Relationship(source=src, destination=dst)
      self.assertIs(rel.source, src)
      self.assertIs(rel.destination, dst)

  # pylint: disable=invalid-name
  def test_relationship_validation_disallowed_type(self, get_rules_mock):
    """Validation fails when source-destination types pair disallowed."""
    get_rules_mock.return_value = {
        "MockModelA": {"MockModelA"},
    }
    Relationship(source=MockModelA(), destination=MockModelA())
    with self.assertRaises(ValidationError):
      Relationship(source=MockModelA(), destination=MockModelB())
    with self.assertRaises(ValidationError):
      Relationship(source=MockModelB(), destination=MockModelA())
    with self.assertRaises(ValidationError):
      Relationship(source=MockModelB(), destination=MockModelB())
