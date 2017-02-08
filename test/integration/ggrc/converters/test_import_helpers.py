# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

from os.path import abspath, dirname, join

from ggrc import converters
from ggrc import models
from ggrc.converters import column_handlers
from ggrc.converters import import_helper
from ggrc.converters.import_helper import get_object_column_definitions
from ggrc.utils import get_mapping_rules
from ggrc.utils import title_from_camelcase
from ggrc_risks import models as r_models
from ggrc_risk_assessments import models as ra_models
from ggrc_workflows import models as wf_models
from integration.ggrc import TestCase
from integration.ggrc.generator import ObjectGenerator

THIS_ABS_PATH = abspath(dirname(__file__))
CSV_DIR = join(THIS_ABS_PATH, 'example_csvs/')


def get_mapping_names(class_name):
  mapping_rules = get_mapping_rules().get(class_name, set())
  pretty_rules = map(title_from_camelcase, mapping_rules)
  mapping_names = {"map:{}".format(name) for name in pretty_rules}
  unmapping_names = {"unmap:{}".format(name) for name in pretty_rules}
  return mapping_names.union(unmapping_names)


class TestCustomAttributesDefinitions(TestCase):

  def setUp(self):
    super(TestCustomAttributesDefinitions, self).setUp()
    self.generator = ObjectGenerator()

  def test_policy_definitions(self):
    self.generator.generate_custom_attribute("policy", title="My Attribute")
    self.generator.generate_custom_attribute(
        "policy", title="Mandatory Attribute", mandatory=True)
    definitions = get_object_column_definitions(models.Policy)
    mapping_names = get_mapping_names(models.Policy.__name__)
    display_names = {val["display_name"] for val in definitions.itervalues()}
    element_names = {
        "Code",
        "Title",
        "Description",
        "Notes",
        "Owner",
        "Primary Contact",
        "Secondary Contact",
        "Policy URL",
        "Reference URL",
        "Kind/Type",
        "Effective Date",
        "Stop Date",
        "State",
        "My Attribute",
        "Mandatory Attribute",
        "Review State",
        "Delete",
    }
    expected_names = element_names.union(mapping_names)
    self.assertEqual(expected_names, display_names)
    vals = {val["display_name"]: val for val in definitions.itervalues()}
    self.assertTrue(vals["Title"]["mandatory"])
    self.assertTrue(vals["Owner"]["mandatory"])
    self.assertTrue(vals["Title"]["unique"])
    self.assertTrue(vals["Mandatory Attribute"]["mandatory"])

  def test_program_definitions(self):
    """ test custom attribute headers for Program """

    self.generator.generate_custom_attribute(
        "program",
        title="My Attribute")
    self.generator.generate_custom_attribute(
        "program",
        title="Mandatory Attribute",
        mandatory=True)
    self.generator.generate_custom_attribute(
        "program",
        title="Choose",
        mandatory=True,
        attribute_type="Dropdown",
        multi_choice="hello,world,what's,up"
    )
    definitions = get_object_column_definitions(models.Program)
    mapping_names = get_mapping_names(models.Program.__name__)
    display_names = {val["display_name"] for val in definitions.itervalues()}
    element_names = {
        "Title",
        "Description",
        "Notes",
        "Manager",
        "Reader",
        "Editor",
        "Primary Contact",
        "Secondary Contact",
        "Program URL",
        "Reference URL",
        "Code",
        "Effective Date",
        "Stop Date",
        "State",
        "My Attribute",
        "Mandatory Attribute",
        "Choose",
        "Review State",
        "Delete",
    }
    expected_names = element_names.union(mapping_names)
    self.assertEqual(expected_names, display_names)
    vals = {val["display_name"]: val for val in definitions.itervalues()}
    self.assertTrue(vals["Title"]["mandatory"])
    self.assertTrue(vals["Manager"]["mandatory"])
    self.assertTrue(vals["Title"]["unique"])
    self.assertTrue(vals["Mandatory Attribute"]["mandatory"])
    self.assertTrue(vals["Choose"]["mandatory"])


class TestGetObjectColumnDefinitions(TestCase):

  """
  Test default column difinitions for all objcts

  order of these test functions is the same as the objects in LHN
  """

  COMMON_EXPECTED = {
      "mandatory": {
          "Title",
          "Owner",
          "Code",
      },
      "unique": {
          "Code",
          "Title",
      },
  }

  @classmethod
  def setUpClass(cls):
    TestCase.clear_data()

  def setUp(self):
    pass

  def _test_definition_names(self, obj_class, names, has_mappings=True):
    """ Test name definitions for one class

    This function checks if names returned by get_object_column_definitions
    match provided list of names with the appropriate mapping names fro that
    class if has_mappings attribute is set.
    """
    definitions = get_object_column_definitions(obj_class)
    display_names = {val["display_name"] for val in definitions.itervalues()}
    mapping_names = get_mapping_names(obj_class.__name__)
    expected_names = names.union(mapping_names)
    self.assertEqual(expected_names, display_names)
    if has_mappings:
      self.assertNotEqual(set(), mapping_names)
    else:
      self.assertEqual(set(), mapping_names)

  def _test_definition_fields(self, obj_class, field_name, expected):
    """ Test expected fields in column definitions.

    Check that the definitions contain correct values in the fields for all
    names in the expected list.

    Args:
      obj_class (db.Model): class to check definitions.
      field_name (str): Name of the field we want to check (ie. manatory).
      expected (list of str): List of display names for all attributes that
        should have the field field_name set to true.
    """
    definitions = get_object_column_definitions(obj_class)
    definition_fields = {
        val["display_name"] for val in definitions.itervalues()
        if val.get(field_name)
    }
    self.assertEqual(definition_fields, expected)

  def _test_single_object(self, obj_class, names, expected_fields,
                          has_mappings=True):
    """ Test object definitions

    This is a helper function to aggregate tests for column name definitions,
    mandatory fields and unique fields.
    """
    errors = ""
    try:
      self._test_definition_names(obj_class, names, has_mappings)
    except AssertionError as error:
      errors += "\n\n{} definition names missmatch.\n{}".format(
          obj_class.__name__, str(error))

    for field_name, expected in expected_fields.iteritems():
      try:
        self._test_definition_fields(obj_class, field_name, expected)
      except AssertionError as error:
        errors += "\n\n{} {} fields missmatch.\n{}".format(
            obj_class.__name__, field_name, str(error))

    self.assertEqual(errors, "", errors)

  def test_object_column_handlers(self):
    """Test column handlers on all exportable objects.

    This function makes sure that we don't use get wrong hadlers when fetching
    object column definitions. If a column has a specified handler_key then
    the appropriate handler must override the default handler for the column
    with the same name.

    Raises:
      AssertionError if any unexpected colum handlers are found.
    """

    def test_single_object(obj):
      """Test colum handlers for a single object.

      Args:
        obj: sqlachemy model.

      Raises:
        AssertionError if object definition contains the wrong handler.
      """
      handlers = column_handlers.COLUMN_HANDLERS
      column_definitions = import_helper.get_object_column_definitions(obj)
      for key, value in column_definitions.items():
        if key in handlers:
          handler_key = value.get("handler_key", key)
          self.assertEqual(
              value["handler"],
              handlers[handler_key],
              "Object '{}', column '{}': expected {}, found {}".format(
                  obj.__name__,
                  key,
                  handlers[key].__name__,
                  value["handler"].__name__,
              )
          )

    verification_errors = []
    for obj in set(converters.get_exportables().itervalues()):
      try:
        test_single_object(obj)
      except AssertionError as error:
        verification_errors.append(str(error))

    verification_errors.sort()
    self.assertEqual(verification_errors, [])

  def test_program_definitions(self):
    """ test default headers for Program """
    names = {
        "Title",
        "Description",
        "Notes",
        "Manager",
        "Reader",
        "Editor",
        "Primary Contact",
        "Secondary Contact",
        "Program URL",
        "Reference URL",
        "Code",
        "Effective Date",
        "Stop Date",
        "State",
        "Review State",
        "Delete",
    }
    expected_fields = {
        "mandatory": {
            "Code",
            "Title",
            "Manager",
        },
        "unique": {
            "Code",
            "Title",
        },
    }
    self._test_single_object(models.Program, names, expected_fields)

    definitions = get_object_column_definitions(models.Program)
    vals = {val["display_name"]: val for val in definitions.itervalues()}
    self.assertEqual(vals["Manager"]["type"], "user_role")

  def test_audit_definitions(self):
    """ test default headers for Audit """
    names = {
        "Program",
        "Code",
        "Title",
        "Description",
        "Internal Audit Lead",
        "Status",
        "Planned Start Date",
        "Planned End Date",
        "Planned Report Period from",
        "Planned Report Period to",
        "Auditors",
        "Delete",
    }
    expected_fields = {
        "mandatory": {
            "Code",
            "Title",
            "Program",
            "Status",
            "Internal Audit Lead",
        },
        "unique": {
            "Title",
        },
    }
    self._test_single_object(models.Audit, names, expected_fields)

  def test_assessment_template_defs(self):
    """Test default headers for Assessment Template."""

    names = {
        "Title",
        "Audit",
        "Object Under Assessment",
        "Use Control Test Plan",
        "Default Test Plan",
        "Default Assessors",
        "Default Verifier",
        "Custom Attributes",
        "Code",
        "Delete",
    }
    expected_fields = {
        "mandatory": {
            "Title",
            "Object Under Assessment",
            "Audit",
            "Code",
            "Default Assessors",
            "Default Verifier",
        },
        "unique": {
            "Code",
        },
        "ignore_on_update": {
            "Audit",
        }
    }
    self._test_single_object(models.AssessmentTemplate, names, expected_fields,
                             has_mappings=False)

  def test_assessment_definitions(self):
    """Test default headers for Assessment."""

    names = {
        "Title",
        "Template",
        "Description",
        "Evidence Collection Guidance",
        "Notes",
        "Audit",
        "Creator",
        "Assessor",
        "Verifier",
        "Primary Contact",
        "Secondary Contact",
        "Assessment URL",
        "Reference URL",
        "Evidence",
        "Url",
        "Code",
        "Effective Date",
        "Stop Date",
        "Verified Date",
        "Finished Date",
        "State",
        "Conclusion: Design",
        "Conclusion: Operation",
        "Recipients",
        "Send by default",
        "Review State",
        "Delete",
    }
    expected_fields = {
        "mandatory": {
            "Title",
            "Audit",
            "Creator",
            "Assessor",
            "Code"
        },
        "unique": {
            "Code",
        },
        "ignore_on_update": {
            "Template",
            "Audit",
        }
    }
    self._test_single_object(models.Assessment, names, expected_fields)

  def test_issue_definitions(self):
    """ test default headers for Issue """
    names = {
        "Title",
        "Description",
        "Notes",
        "Evidence Collection Guidance",
        "Owner",
        "Primary Contact",
        "Secondary Contact",
        "Issue URL",
        "Reference URL",
        "Code",
        "Effective Date",
        "Stop Date",
        "State",
        "Review State",
        "Delete",
    }
    self._test_single_object(models.Issue, names, self.COMMON_EXPECTED)

  def test_regulation_definitions(self):
    """ test default headers for Regulation """
    names = {
        "Title",
        "Description",
        "Notes",
        "Owner",
        "Primary Contact",
        "Secondary Contact",
        "Regulation URL",
        "Reference URL",
        "Code",
        "Effective Date",
        "Stop Date",
        "State",
        "Review State",
        "Delete",
    }
    self._test_single_object(models.Regulation, names, self.COMMON_EXPECTED)

  def test_policy_definitions(self):
    """ test default headers for Policy """
    names = {
        "Title",
        "Description",
        "Notes",
        "Owner",
        "Primary Contact",
        "Secondary Contact",
        "Policy URL",
        "Reference URL",
        "Kind/Type",
        "Code",
        "Effective Date",
        "Stop Date",
        "State",
        "Review State",
        "Delete",
    }
    self._test_single_object(models.Policy, names, self.COMMON_EXPECTED)

  def test_standard_definitions(self):
    """ test default headers for Standard """
    names = {
        "Title",
        "Description",
        "Notes",
        "Owner",
        "Primary Contact",
        "Secondary Contact",
        "Standard URL",
        "Reference URL",
        "Code",
        "Effective Date",
        "Stop Date",
        "State",
        "Review State",
        "Delete",
    }
    self._test_single_object(models.Standard, names, self.COMMON_EXPECTED)

  def test_contract_definitions(self):
    """ test default headers for Contract """
    names = {
        "Title",
        "Description",
        "Notes",
        "Owner",
        "Primary Contact",
        "Secondary Contact",
        "Contract URL",
        "Reference URL",
        "Code",
        "Effective Date",
        "Stop Date",
        "State",
        "Review State",
        "Delete",
    }
    self._test_single_object(models.Contract, names, self.COMMON_EXPECTED)

  def test_clause_definitions(self):
    """ test default headers for Clause """
    names = {
        "Title",
        "Text of Clause",
        "Notes",
        "Owner",
        "Primary Contact",
        "Secondary Contact",
        "Clause URL",
        "Reference URL",
        "Code",
        "Effective Date",
        "Stop Date",
        "State",
        "Review State",
        "Delete",
    }
    self._test_single_object(models.Clause, names, self.COMMON_EXPECTED)

  def test_section_definitions(self):
    """ test default headers for Section """
    names = {
        "Title",
        "Text of Section",
        "Notes",
        "Policy / Regulation / Standard / Contract",
        "Owner",
        "Primary Contact",
        "Secondary Contact",
        "Section URL",
        "Reference URL",
        "Code",
        "State",
        "Review State",
        "Delete",
    }
    self._test_single_object(models.Section, names, self.COMMON_EXPECTED)

  def test_control_definitions(self):
    """ test default headers for Control """
    names = {
        "Title",
        "Description",
        "Evidence Collection Guidance",
        "Notes",
        "Owner",
        "Primary Contact",
        "Secondary Contact",
        "Control URL",
        "Reference URL",
        "Code",
        "Kind/Nature",
        "Fraud Related",
        "Significance",
        "Type/Means",
        "Effective Date",
        "Stop Date",
        "Frequency",
        "Assertions",
        "Categories",
        "Principal Assessor",
        "Secondary Assessor",
        "State",
        "Review State",
        "Delete",
    }
    self._test_single_object(models.Control, names, self.COMMON_EXPECTED)

  def test_objective_definitions(self):
    """ test default headers for Objective """
    names = {
        "Title",
        "Description",
        "Notes",
        "Owner",
        "Primary Contact",
        "Secondary Contact",
        "Objective URL",
        "Reference URL",
        "Code",
        "State",
        "Review State",
        "Delete",
    }
    self._test_single_object(models.Objective, names, self.COMMON_EXPECTED)

  def test_person_definitions(self):
    """ test default headers for Person """
    names = {
        "Name",
        "Email",
        "Company",
        "Role",
    }
    expected_fields = {
        "mandatory": {
            "Email",
        },
        "unique": {
            "Email",
        },
    }
    self._test_single_object(models.Person, names, expected_fields)

  def test_org_group_definitions(self):
    """ test default headers for OrgGroup """
    names = {
        "Title",
        "Description",
        "Notes",
        "Owner",
        "Primary Contact",
        "Secondary Contact",
        "Org Group URL",
        "Reference URL",
        "Code",
        "Effective Date",
        "Stop Date",
        "State",
        "Review State",
        "Delete",
    }
    self._test_single_object(models.OrgGroup, names, self.COMMON_EXPECTED)

  def test_vendor_definitions(self):
    """ test default headers for Vendor """
    names = {
        "Title",
        "Description",
        "Notes",
        "Owner",
        "Primary Contact",
        "Secondary Contact",
        "Vendor URL",
        "Reference URL",
        "Code",
        "Effective Date",
        "Stop Date",
        "State",
        "Review State",
        "Delete",
    }
    self._test_single_object(models.Vendor, names, self.COMMON_EXPECTED)

  def test_system_definitions(self):
    """ test default headers for System """
    names = {
        "Title",
        "Description",
        "Notes",
        "Owner",
        "Primary Contact",
        "Secondary Contact",
        "System URL",
        "Reference URL",
        "Code",
        "Network Zone",
        "Effective Date",
        "Stop Date",
        "State",
        "Review State",
        "Delete",
    }
    self._test_single_object(models.System, names, self.COMMON_EXPECTED)

  def test_process_definitions(self):
    """ test default headers for Process """
    names = {
        "Title",
        "Description",
        "Notes",
        "Owner",
        "Primary Contact",
        "Secondary Contact",
        "Process URL",
        "Reference URL",
        "Code",
        "Network Zone",
        "Effective Date",
        "Stop Date",
        "State",
        "Review State",
        "Delete",
    }
    self._test_single_object(models.Process, names, self.COMMON_EXPECTED)

  def test_data_asset_definitions(self):
    """ test default headers for DataAsset """
    names = {
        "Title",
        "Description",
        "Notes",
        "Owner",
        "Primary Contact",
        "Secondary Contact",
        "Data Asset URL",
        "Reference URL",
        "Code",
        "Effective Date",
        "Stop Date",
        "State",
        "Review State",
        "Delete",
    }
    self._test_single_object(models.DataAsset, names, self.COMMON_EXPECTED)

  def test_access_group_definitions(self):
    """ test default headers for AccessGroup """
    names = {
        "Title",
        "Description",
        "Notes",
        "Owner",
        "Primary Contact",
        "Secondary Contact",
        "Access Group URL",
        "Reference URL",
        "Code",
        "Effective Date",
        "Stop Date",
        "State",
        "Review State",
        "Delete",
    }
    self._test_single_object(models.AccessGroup, names, self.COMMON_EXPECTED)

  def test_product_definitions(self):
    """ test default headers for Product """
    names = {
        "Title",
        "Description",
        "Notes",
        "Owner",
        "Primary Contact",
        "Secondary Contact",
        "Product URL",
        "Reference URL",
        "Code",
        "Kind/Type",
        "Effective Date",
        "Stop Date",
        "State",
        "Review State",
        "Delete",
    }
    self._test_single_object(models.Product, names, self.COMMON_EXPECTED)

  def test_project_definitions(self):
    """ test default headers for Project """
    names = {
        "Title",
        "Description",
        "Notes",
        "Owner",
        "Primary Contact",
        "Secondary Contact",
        "Project URL",
        "Reference URL",
        "Code",
        "Effective Date",
        "Stop Date",
        "State",
        "Review State",
        "Delete",
    }
    self._test_single_object(models.Project, names, self.COMMON_EXPECTED)

  def test_facility_definitions(self):
    """ test default headers for Facility """
    names = {
        "Title",
        "Description",
        "Notes",
        "Owner",
        "Primary Contact",
        "Secondary Contact",
        "Facility URL",
        "Reference URL",
        "Code",
        "Effective Date",
        "Stop Date",
        "State",
        "Review State",
        "Delete",
    }
    self._test_single_object(models.Facility, names, self.COMMON_EXPECTED)

  def test_market_definitions(self):
    """ test default headers for Market """
    names = {
        "Title",
        "Description",
        "Notes",
        "Owner",
        "Primary Contact",
        "Secondary Contact",
        "Market URL",
        "Reference URL",
        "Code",
        "Effective Date",
        "Stop Date",
        "State",
        "Review State",
        "Delete",
    }
    self._test_single_object(models.Market, names, self.COMMON_EXPECTED)

  def test_risk_definitions(self):
    """Test default headers for Risk."""

    names = {
        "Code",
        "Contact",
        "Delete",
        "Description",
        "Effective Date",
        "Notes",
        "Owner",
        "Reference URL",
        "State",
        "Review State",
        "Stop Date",
        "Title",
        "Url",
    }
    expected_fields = {
        "mandatory": {
            "Code",
            "Description",
            "Owner",
            "Title",
        },
        "unique": {
            "Code",
            "Title",
        },
    }
    self._test_single_object(r_models.Risk, names, expected_fields)


class TestGetWorkflowObjectColumnDefinitions(TestCase):
  """Test default column difinitions for workflow objcts.
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
    display_names = {val["display_name"] for val in definitions.itervalues()}
    element_names = {
        "Code",
        "Cycle",
        "Summary",
        "Task Type",
        "Assignee",
        "Task Details",
        "Start Date",
        "End Date",
        "Actual Verified Date",
        "Actual Finish Date",
        "Task Group",
        "State",
        "Delete",
    }
    expected_names = element_names.union(mapping_names)
    self.assertEqual(expected_names, display_names)
    vals = {val["display_name"]: val for val in definitions.itervalues()}
    self.assertTrue(vals["Summary"]["mandatory"])
    self.assertTrue(vals["Assignee"]["mandatory"])


class TestGetRiskAssessmentObjectColumnDefinitions(TestCase):
  """Test default column difinitions for risk assessment objcts.
  """

  @classmethod
  def setUpClass(cls):
    TestCase.clear_data()

  def setUp(self):
    pass

  def test_risk_assessemnt_definitions(self):
    """ test default headers for Workflow """
    definitions = get_object_column_definitions(ra_models.RiskAssessment)
    display_names = {val["display_name"] for val in definitions.itervalues()}
    expected_names = {
        "Title",
        "Description",
        "Notes",
        "Start Date",
        "End Date",
        "Risk Manager",
        "Risk Counsel",
        "Code",
        "Program",
        "Delete",
    }
    self.assertEqual(expected_names, display_names)
    vals = {val["display_name"]: val for val in definitions.itervalues()}
    self.assertTrue(vals["Title"]["mandatory"])
    self.assertTrue(vals["Start Date"]["mandatory"])
    self.assertTrue(vals["End Date"]["mandatory"])
