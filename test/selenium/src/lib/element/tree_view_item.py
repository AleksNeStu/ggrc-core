# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Module of TreeViewItem dropdownsMenu presented on Genetic TreeView."""
from lib import base


class CommonDropdownTreeViewItem(base.DropdownMenu):
  """Common Dropdown for TreeView Item"""

  def __init__(self, driver, obj_name, parent_element):
    super(CommonDropdownTreeViewItem, self).__init__(driver, parent_element)
    self.obj_name = obj_name


class SnapshotsDropdownTreeViewItem(CommonDropdownTreeViewItem):
  """Class for Dropdown of Snapshotable TreeViewItem"""


class AssessmentTemplates(CommonDropdownTreeViewItem):
  """Class for Dropdown of AssessmentTemplates TreeViewItem"""


class Audits(CommonDropdownTreeViewItem):
  """Class for Dropdown of Audits TreeViewItem"""


class Assessments(CommonDropdownTreeViewItem):
  """Class for Dropdown of Assessments TreeViewItem"""


class Issues(CommonDropdownTreeViewItem):
  """Class for Dropdown of Assessments TreeViewItem"""


class Controls(SnapshotsDropdownTreeViewItem):
  """Class for Dropdown of Controls TreeViewItem"""


class Programs(CommonDropdownTreeViewItem):
  """Class for Dropdown of Programs TreeViewItem"""


class DataAssets(SnapshotsDropdownTreeViewItem):
  """Class for Dropdown of DataAssets TreeViewItem"""


class Systems(SnapshotsDropdownTreeViewItem):
  """Class for Dropdown of Systems TreeViewItem"""


class Processes(SnapshotsDropdownTreeViewItem):
  """Class for Dropdown of Processes TreeViewItem"""


class Products(SnapshotsDropdownTreeViewItem):
  """Class for Dropdown of Products TreeViewItem"""


class Projects(SnapshotsDropdownTreeViewItem):
  """Class for Dropdown of Projects TreeViewItem"""


class OrgGroups(SnapshotsDropdownTreeViewItem):
  """Class for Dropdown of Products TreeViewItem"""
