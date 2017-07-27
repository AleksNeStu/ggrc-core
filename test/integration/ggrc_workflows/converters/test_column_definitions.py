# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>


from ggrc.converters.import_helper import get_object_column_definitions
from ggrc.utils.rules import get_mapping_rules, get_unmapping_rules
from ggrc.utils import title_from_camelcase
from ggrc_workflows import models as wf_models
from integration.ggrc import TestCase


def get_mapping_names(class_name):
  mapping_rules = get_mapping_rules().get(class_name)
  if mapping_rules is not None:
    pretty_mapping_rules = (title_from_camelcase(r) for r in mapping_rules)
    mapping_names = {"map:{}".format(n) for n in pretty_mapping_rules}
  else:
    mapping_names = None
  return mapping_names


def get_unmapping_names(class_name):
  unmapping_rules = get_unmapping_rules().get(class_name)
  if unmapping_rules is not None:
    pretty_unmapping_rules = (title_from_camelcase(r) for r in unmapping_rules)
    unmapping_names = {"unmap:{}".format(n) for n in pretty_unmapping_rules}
  else:
    unmapping_names = None
  return unmapping_names


class TestWorkflowObjectColumnDefinitions(TestCase):
  """Test default column difinitions for workflow objects.
  """

  @classmethod
  def setUpClass(cls):
    TestCase.clear_data()

  def setUp(self):
    pass

  def test_workflow_definitions(self):
    """ test default headers for Workflow """
    definitions = get_object_column_definitions(wf_models.Workflow)
    display_names = {val["display_name"] for val in definitions.itervalues()}
    expected_names = {
        "Title",
        "Description",
        "Custom email message",
        "Manager",
        "Member",
        "Frequency",
        "Force real-time email updates",
        "Code",
        "Delete",
        "Need Verification",
    }
    self.assertEqual(expected_names, display_names)
    vals = {val["display_name"]: val for val in definitions.itervalues()}
    self.assertTrue(vals["Title"]["mandatory"])
    self.assertTrue(vals["Manager"]["mandatory"])
    self.assertTrue(vals["Frequency"]["mandatory"])
    self.assertIn("type", vals["Manager"])
    self.assertIn("type", vals["Member"])
    self.assertEqual(vals["Manager"]["type"], "user_role")
    self.assertEqual(vals["Member"]["type"], "user_role")

  def test_task_group_definitions(self):
    """ test default headers for Task Group """
    definitions = get_object_column_definitions(wf_models.TaskGroup)
    display_names = {val["display_name"] for val in definitions.itervalues()}
    expected_names = {
        "Summary",
        "Details",
        "Assignee",
        "Code",
        "Workflow",
        "Objects",
        "Delete",
    }
    self.assertEqual(expected_names, display_names)
    vals = {val["display_name"]: val for val in definitions.itervalues()}
    self.assertTrue(vals["Summary"]["mandatory"])
    self.assertTrue(vals["Assignee"]["mandatory"])

  def test_task_group_task_definitions(self):
    """ test default headers for Task Group Task """
    definitions = get_object_column_definitions(wf_models.TaskGroupTask)
    display_names = {val["display_name"] for val in definitions.itervalues()}
    expected_names = {
        "Summary",
        "Task Type",
        "Assignee",
        "Task Description",
        "Start",
        "End",
        "Task Group",
        "Code",
        "Delete",
    }
    self.assertEqual(expected_names, display_names)
    vals = {val["display_name"]: val for val in definitions.itervalues()}
    self.assertTrue(vals["Summary"]["mandatory"])
    self.assertTrue(vals["Assignee"]["mandatory"])

  def test_cycle_task_definitions(self):
    """ test default headers for Cycle Task Group Object Task """
    definitions = get_object_column_definitions(
        wf_models.CycleTaskGroupObjectTask)
    mapping_names = get_mapping_names(
        wf_models.CycleTaskGroupObjectTask.__name__)
    unmapping_names = get_unmapping_names(
        wf_models.CycleTaskGroupObjectTask.__name__)
    display_names = {val["display_name"] for val in definitions.itervalues()}
    element_names = {
        "Code",
        "Cycle",
        "Summary",
        "Task Type",
        "Assignee",
        "Task Details",
        "Start Date",
        "Due Date",
        "Actual Verified Date",
        "Actual Finish Date",
        "Task Group",
        "State",
        "Delete",
    }
    expected_names = element_names.union(mapping_names).union(unmapping_names)
    self.assertEqual(expected_names, display_names)
    vals = {val["display_name"]: val for val in definitions.itervalues()}
    self.assertTrue(vals["Summary"]["mandatory"])
    self.assertTrue(vals["Assignee"]["mandatory"])
