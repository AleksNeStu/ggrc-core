"""Test Track Object State Module"""

import unittest
from ggrc.models import Control  # Random object that implements HasObjectState


class TestTrackObjectState(unittest.TestCase):
  """Test Track Object State"""

  def setUp(self):
    self.obj = Control()

  def test_validate_os_state(self):
    """Test validate_os_state prevents setting os_state"""
    self.obj.os_state = "New State"
    self.obj.validate_os_state()
    assert self.obj.os_state == "Unreviewed"

  def test_set_reviewed_state(self):
    """Test set_reviewed_state updates os_state to Reviewed"""
    self.obj.os_state = "New State"
    self.obj.set_reviewed_state()
    self.obj.validate_os_state()
    assert self.obj.os_state == "Reviewed"
