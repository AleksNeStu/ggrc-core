"""Test Object State Module"""

import unittest
import ggrc.app  # noqa pylint: disable=unused-import
from ddt import ddt
from ddt import data
from ggrc.models import all_models


@ddt
class TestStates(unittest.TestCase):
  """Test Object State main Test Case class"""

  BASIC_STATE_OBJECTS = (
      'AccessGroup', 'Clause', 'Contract',
      'Control', 'DataAsset', 'Directive', 'Facility', 'Issue', 'Market',
      'Objective', 'OrgGroup', 'Policy', 'Process', 'Product', 'Program',
      'Project', 'Regulation', 'Risk', 'Section', 'Standard', 'System',
      'SystemOrProcess', 'Threat', 'Vendor')

  def _assert_states(self, objType, expected_states, default):
    # pylint: disable=no-self-use
    for model in all_models.all_models:
      if model.__name__ != objType:
        continue

      assert hasattr(model, "valid_statuses"), \
          "{} does not have valid_statuses".format(model.__name__)

      assert set(model.valid_statuses()) == set(expected_states), \
          "{} does not have expected states {}. Current states {}".format(
              model.__name__, ', '.join(expected_states),
              ', '.join(model.valid_statuses()))

      assert model.default_status() == default, \
          "{} does not have expected default status {}, but {} instead".format(
              model.__name__,
              default,
              model.default_status())

  @data(*BASIC_STATE_OBJECTS)
  def test_basic_states(self, obj):
    """Test basic object states"""
    basic_states = ('Draft', 'Active', 'Deprecated')

    self._assert_states(obj, basic_states, 'Draft')

  def test_audit_states(self):
    """Test states for Audit object"""
    audit_states = ('Planned', 'In Progress', 'Manager Review',
                    'Ready for External Review', 'Completed')
    self._assert_states('Audit', audit_states, 'Planned')

  def test_assignable_states(self):
    """Test states for Assignable objects (Assessment)"""
    assignable_states = (
        'In Progress', 'Completed', 'Not Started', 'Verified',
        'Ready for Review')
    self._assert_states('Assessment', assignable_states, 'Not Started')
