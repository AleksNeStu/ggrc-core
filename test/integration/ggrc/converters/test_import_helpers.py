# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Module for CSV column definition tests."""

import ddt

from ggrc import converters
from ggrc import models
from ggrc.access_control import roleable
from ggrc.converters import column_handlers
from ggrc.converters import import_helper
from ggrc.converters.import_helper import get_object_column_definitions
from ggrc.utils import rules
from ggrc.utils import title_from_camelcase
from ggrc_risks import models as r_models
from ggrc_risk_assessments import models as ra_models
from integration.ggrc import TestCase
from integration.ggrc.models import factories
from integration.ggrc.generator import ObjectGenerator


def get_mapping_names(class_name):
  """Get mapping, unmapping and snapshot mapping column names."""
  map_rules = rules.get_mapping_rules().get(class_name) or set()
  unmap_rules = rules.get_unmapping_rules().get(class_name) or set()
  unmap_sn_rules = rules.get_snapshot_mapping_rules().get(class_name) or set()

  format_rules = [("map:{}", map_rules),
                  ("unmap:{}", unmap_rules),
                  ("map:{} versions", unmap_sn_rules)]

  column_names = set()
  for format_, rule_set in format_rules:
    pretty_rules = (title_from_camelcase(r) for r in rule_set)
    column_names.update(format_.format(r) for r in pretty_rules)

  return column_names


@ddt.ddt
class TestACLAttributeDefinitions(TestCase):
  """Tests for ACL column definitions on all models."""

  @ddt.data(*models.all_models.all_models)
  def test_acl_definitions(self, model):
    """Test ACL column definitions."""
    with factories.single_commit():
      factory = factories.AccessControlRoleFactory
      factories.AccessControlRoleFactory(
          object_type="Control",
          read=True
      )
      role_names = {factory(object_type=model.__name__).name for _ in range(2)}

    expected_names = set()
    if issubclass(model, roleable.Roleable):
      expected_names = role_names

    definitions = get_object_column_definitions(model)
    definition_names = {d["display_name"]: d for d in definitions.values()}
    self.assertLessEqual(expected_names, set(definition_names.keys()))


class TestCustomAttributesDefinitions(TestCase):
  """Test for custom attribute definition columns."""

  def setUp(self):
    super(TestCustomAttributesDefinitions, self).setUp()
    self.generator = ObjectGenerator()

  def test_policy_definitions(self):
    """Test custom attribute definitions on Policy model."""
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
        "Admin",
        "Reference URL",
        "Kind/Type",
        "Effective Date",
        "Last Deprecated Date",
        "State",
        "My Attribute",
        "Mandatory Attribute",
        "Review State",
        "Delete",
        "Primary Contacts",
        "Secondary Contacts",
        'Created Date',
        'Last Updated',
        'Last Updated By',
    }
    expected_names = element_names.union(mapping_names)
    self.assertEqual(expected_names, display_names)
    vals = {val["display_name"]: val for val in definitions.itervalues()}
    self.assertTrue(vals["Title"]["mandatory"])
    self.assertTrue(vals["Admin"]["mandatory"])
    self.assertTrue(vals["Title"]["unique"])
    self.assertTrue(vals["Mandatory Attribute"]["mandatory"])

  def test_program_definitions(self):
    """ test custom attribute headers for Program."""

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
        "Reference URL",
        "Code",
        "Effective Date",
        "Last Deprecated Date",
        "State",
        "My Attribute",
        "Mandatory Attribute",
        "Choose",
        "Review State",
        "Delete",
        "Primary Contacts",
        "Secondary Contacts",
        'Created Date',
        'Last Updated',
        'Last Updated By',
    }
    expected_names = element_names.union(mapping_names)
    self.assertEqual(expected_names, display_names)
    vals = {val["display_name"]: val for val in definitions.itervalues()}
    self.assertTrue(vals["Title"]["mandatory"])
    self.assertTrue(vals["Manager"]["mandatory"])
    self.assertTrue(vals["Title"]["unique"])
    self.assertTrue(vals["Mandatory Attribute"]["mandatory"])
    self.assertTrue(vals["Choose"]["mandatory"])


@ddt.ddt
class TestGetObjectColumnDefinitions(TestCase):

  """Test default column difinitions for all objects.

  order of these test functions is the same as the objects in LHN
  """

  COMMON_EXPECTED = {
      "mandatory": {
          "Title",
          "Admin",
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
    """Test name definitions for one class

    This function checks if names returned by get_object_column_definitions
    match provided list of names with the appropriate mapping names fro that
    class if has_mappings attribute is set.
    """
    definitions = get_object_column_definitions(obj_class)
    display_names = {val["display_name"] for val in definitions.itervalues()}
    mapping_names = get_mapping_names(obj_class.__name__)
    if has_mappings:
      self.assertTrue(mapping_names)
      expected_names = names.union(mapping_names)
    else:
      self.assertFalse(mapping_names)
      expected_names = names
    self.assertEqual(display_names, expected_names)

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
    """Test default headers for Program."""
    names = {
        "Title",
        "Description",
        "Notes",
        "Manager",
        "Reader",
        "Editor",
        "Reference URL",
        "Code",
        "Effective Date",
        "Last Deprecated Date",
        "State",
        "Review State",
        "Delete",
        "Primary Contacts",
        "Secondary Contacts",
        'Created Date',
        'Last Updated',
        'Last Updated By',
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
    """Test default headers for Audit."""
    names = {
        "Program",
        "Code",
        "Title",
        "Description",
        "Audit Captain",
        "Status",
        "Planned Start Date",
        "Planned End Date",
        "Planned Report Period from",
        "Planned Report Period to",
        "Auditors",
        "Archived",
        "Delete",
        "Evidence URL",
        "Evidence File",
        'Created Date',
        'Last Updated',
        'Last Updated By',
    }
    expected_fields = {
        "mandatory": {
            "Code",
            "Title",
            "Program",
            "Status",
            "Audit Captain",
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
        "Use Control Assessment Procedure",
        "Default Test Plan",
        "Default Assignee",
        "Default Verifier",
        "Custom Attributes",
        "Code",
        "Archived",
        'Created Date',
        'Last Updated',
        'Last Updated By',
        "Delete",
        "State",
    }
    expected_fields = {
        "mandatory": {
            "Title",
            "Object Under Assessment",
            "Audit",
            "Code",
            "Default Assignee",
        },
        "unique": {
            "Code",
        },
        "ignore_on_update": {
            "Audit",
            "Archived",
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
        "Assessment Procedure",
        "Notes",
        "Audit",
        "Archived",
        "Creators",
        "Assignees",
        "Verifiers",
        "Assessment Type",
        "Reference URL",
        "Evidence File",
        "Evidence URL",
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
        "Primary Contacts",
        "Secondary Contacts",
        'Created Date',
        'Last Updated',
        'Last Updated By',
    }
    expected_fields = {
        "mandatory": {
            "Title",
            "Audit",
            "Creators",
            "Assignees",
            "Code"
        },
        "unique": {
            "Code",
        },
        "ignore_on_update": {
            "Template",
            "Audit",
            "Archived",
        }
    }
    self._test_single_object(models.Assessment, names, expected_fields)

  def test_issue_definitions(self):
    """Test default headers for Issue."""
    names = {
        "Title",
        "Description",
        "Notes",
        "Audit",
        "Remediation Plan",
        "Admin",
        "Reference URL",
        "Code",
        "Effective Date",
        "Last Deprecated Date",
        "State",
        "Review State",
        "Evidence URL",
        "Evidence File",
        "Delete",
        "Primary Contacts",
        "Secondary Contacts",
        'Created Date',
        'Last Updated',
        'Last Updated By',
    }
    expected_fields = {
        "mandatory": {
            "Title",
            "Admin",
            "Audit",
            "Code"
        },
        "unique": {
            "Code",
            "Title",
        },
        "ignore_on_update": {
            "Audit",
        }
    }
    self._test_single_object(models.Issue, names, expected_fields)

  def test_policy_definitions(self):
    """Test default headers for Policy."""
    names = {
        "Title",
        "Description",
        "Notes",
        "Admin",
        "Reference URL",
        "Kind/Type",
        "Code",
        "Effective Date",
        "Last Deprecated Date",
        "State",
        "Review State",
        "Delete",
        "Primary Contacts",
        "Secondary Contacts",
        'Created Date',
        'Last Updated',
        'Last Updated By',
    }
    self._test_single_object(models.Policy, names, self.COMMON_EXPECTED)

  def test_clause_definitions(self):
    """Test default headers for Clause."""
    names = {
        "Title",
        "Text of Clause",
        "Notes",
        "Admin",
        "Reference URL",
        "Code",
        "Effective Date",
        "Last Deprecated Date",
        "State",
        "Review State",
        "Delete",
        "Primary Contacts",
        "Secondary Contacts",
        'Created Date',
        'Last Updated',
        'Last Updated By',
    }
    self._test_single_object(models.Clause, names, self.COMMON_EXPECTED)

  def test_section_definitions(self):
    """Test default headers for Section."""
    names = {
        "Title",
        "Text of Section",
        "Notes",
        "Policy / Regulation / Standard / Contract",
        "Admin",
        "Reference URL",
        "Code",
        "State",
        "Review State",
        "Delete",
        "Primary Contacts",
        "Secondary Contacts",
        'Created Date',
        'Last Updated',
        'Last Updated By',
    }
    self._test_single_object(models.Section, names, self.COMMON_EXPECTED)

  def test_control_definitions(self):
    """Test default headers for Control."""
    names = {
        "Title",
        "Description",
        "Assessment Procedure",
        "Notes",
        "Admin",
        "Reference URL",
        "Code",
        "Kind/Nature",
        "Fraud Related",
        "Significance",
        "Type/Means",
        "Effective Date",
        "Last Deprecated Date",
        "Frequency",
        "Assertions",
        "Categories",
        "State",
        "Last Assessment Date",
        "Review State",
        "Evidence File",
        "Delete",
        "Primary Contacts",
        "Secondary Contacts",
        "Principal Assignees",
        "Secondary Assignees",
        'Created Date',
        'Last Updated',
        'Last Updated By',
    }
    self._test_single_object(models.Control, names, self.COMMON_EXPECTED)

  def test_objective_definitions(self):
    """Test default headers for Objective."""
    names = {
        "Title",
        "Description",
        "Notes",
        "Admin",
        "Reference URL",
        "Last Assessment Date",
        "Code",
        "State",
        "Review State",
        "Delete",
        "Primary Contacts",
        "Secondary Contacts",
        'Created Date',
        'Last Updated',
        'Last Updated By',
    }
    self._test_single_object(models.Objective, names, self.COMMON_EXPECTED)

  def test_person_definitions(self):
    """Test default headers for Person."""
    names = {
        "Name",
        "Email",
        "Company",
        "Role",
        'Created Date',
        'Last Updated',
        'Last Updated By',
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

  def test_system_definitions(self):
    """Test default headers for System."""
    names = {
        "Title",
        "Description",
        "Notes",
        "Admin",
        "Reference URL",
        "Code",
        "Network Zone",
        "Effective Date",
        "Last Deprecated Date",
        "State",
        "Review State",
        "Delete",
        "Primary Contacts",
        "Secondary Contacts",
        'Created Date',
        'Last Updated',
        'Last Updated By',
    }
    self._test_single_object(models.System, names, self.COMMON_EXPECTED)

  def test_process_definitions(self):
    """Test default headers for Process."""
    names = {
        "Title",
        "Description",
        "Notes",
        "Admin",
        "Reference URL",
        "Code",
        "Network Zone",
        "Effective Date",
        "Last Deprecated Date",
        "State",
        "Review State",
        "Delete",
        "Primary Contacts",
        "Secondary Contacts",
        'Created Date',
        'Last Updated',
        'Last Updated By',
    }
    self._test_single_object(models.Process, names, self.COMMON_EXPECTED)

  def test_product_definitions(self):
    """Test default headers for Product."""
    names = {
        "Title",
        "Description",
        "Notes",
        "Admin",
        "Reference URL",
        "Code",
        "Kind/Type",
        "Effective Date",
        "Last Deprecated Date",
        "State",
        "Review State",
        "Delete",
        "Primary Contacts",
        "Secondary Contacts",
        'Created Date',
        'Last Updated',
        'Last Updated By',
    }
    self._test_single_object(models.Product, names, self.COMMON_EXPECTED)

  def test_risk_definitions(self):
    """Test default headers for Risk."""
    names = {
        "Code",
        "Delete",
        "Description",
        "Effective Date",
        "Notes",
        "Admin",
        "Reference URL",
        "State",
        "Review State",
        "Last Deprecated Date",
        "Title",
        "Primary Contacts",
        "Secondary Contacts",
        'Created Date',
        'Last Updated',
        'Last Updated By',
    }
    expected_fields = {
        "mandatory": {
            "Code",
            "Description",
            "Admin",
            "Title",
        },
        "unique": {
            "Code",
            "Title",
        },
    }
    self._test_single_object(r_models.Risk, names, expected_fields)

  @ddt.data(
      models.AccessGroup,
      models.Contract,
      models.DataAsset,
      models.Facility,
      models.Market,
      models.OrgGroup,
      models.Project,
      models.Regulation,
      models.Standard,
      models.Vendor,
  )
  def test_common_model_definitions(self, model):
    """Test common definition names"""
    names = {
        "Title",
        "Description",
        "Notes",
        "Admin",
        "Reference URL",
        "Code",
        "Effective Date",
        "Last Deprecated Date",
        "State",
        "Review State",
        "Delete",
        "Primary Contacts",
        "Secondary Contacts",
        'Created Date',
        'Last Updated',
        'Last Updated By',
    }
    self._test_single_object(model, names, self.COMMON_EXPECTED)


class TestRiskAssessmentColumnDefinitions(TestCase):
  """Test default column difinitions for risk assessment objcts."""

  @classmethod
  def setUpClass(cls):
    TestCase.clear_data()

  def setUp(self):
    pass

  def test_risk_assessemnt(self):
    """Test default headers for Risk Assessment."""
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
        'Created Date',
        'Last Updated',
        'Last Updated By',
    }
    self.assertEqual(expected_names, display_names)
    vals = {val["display_name"]: val for val in definitions.itervalues()}
    self.assertTrue(vals["Title"]["mandatory"])
    self.assertTrue(vals["Start Date"]["mandatory"])
    self.assertTrue(vals["End Date"]["mandatory"])
