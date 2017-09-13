# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Test import and export of objects with custom attributes."""

from flask.json import dumps

from integration.ggrc import TestCase
from integration.ggrc.generator import ObjectGenerator
from ggrc.models import AccessGroup
from ggrc.models import Product
from ggrc.converters import errors


class TestCustomAttributeImportExport(TestCase):
  """Test import and export with custom attributes."""

  _set_up = True

  def setUp(self):
    """Setup stage for each test.

    Generate all required objects and custom attributes for import of csvs
    containing custom attributes. This stage also initializes a http client
    that is used for sending import/export requests.
    """
    if TestCustomAttributeImportExport._set_up:
      super(TestCustomAttributeImportExport, self).setUp()
      self.generator = ObjectGenerator()
      self.create_custom_attributes()
      self.create_people()
    self.client.get("/login")
    self.headers = ObjectGenerator.get_header()
    TestCustomAttributeImportExport._set_up = False

  def create_custom_attributes(self):
    """Generate custom attributes needed for csv import

    This function generates all custom attributes on Product and Access Group,
    that are used in custom_attribute_tests.csv and
    multi_word_object_custom_attribute_test.csv files.
    """
    gen = self.generator.generate_custom_attribute
    gen("product", attribute_type="Text", title="normal text")
    gen("product", attribute_type="Text", title="man text", mandatory=True)
    gen("product", attribute_type="Rich Text", title="normal RT")
    gen("product", attribute_type="Rich Text", title="man RT", mandatory=True)
    gen("product", attribute_type="Date", title="normal Date")
    gen("product", attribute_type="Date", title="man Date", mandatory=True,
        helptext="Birthday")
    gen("product", attribute_type="Checkbox", title="normal CH")
    gen("product", attribute_type="Checkbox", title="man CH", mandatory=True)
    gen("product", attribute_type="Dropdown", title="normal select",
        options=u"a,b,c,\u017e", helptext="Your favorite number.")
    gen("product", attribute_type="Dropdown", title="man select",
        options="e,f,g", mandatory=True)
    gen("product", attribute_type="Map:Person", title="normal person")
    gen("product", attribute_type="Map:Person", title="man person",
        mandatory=True)

    gen("access_group", attribute_type="Text",
        title="access group test custom", mandatory=True)

  def create_people(self):
    """Create people used in the csv files.

    This function should be removed and people should be added into the csv
    file as a Person block.
    """
    emails = [
        "user1@ggrc.com",
        "miha@policy.com",
        "someone.else@ggrc.com",
        "another@user.com",
    ]
    for email in emails:
      self.generator.generate_person({
          "name": email.split("@")[0].title(),
          "email": email,
      }, "Administrator")

  def test_product_ca_import(self):
    """Test import of product with all custom attributes.

    This tests covers all possible custom attributes with mandatory flag turned
    off and on, and checks for all warnings that should be present.
    """
    filename = "custom_attribute_tests.csv"
    response = self.import_file(filename)[0]
    expected_warnings = {
        errors.WRONG_VALUE.format(line=6, column_name="man CH"),
        errors.WRONG_VALUE.format(line=8, column_name="normal select"),
        errors.WRONG_VALUE.format(line=10, column_name="man select"),
        errors.WRONG_VALUE.format(line=11, column_name="normal CH"),
        errors.WRONG_VALUE.format(line=12, column_name="man CH"),
        errors.WRONG_VALUE.format(line=14, column_name="normal Date"),
        errors.WRONG_VALUE.format(line=16, column_name="man Date"),
        errors.OWNER_MISSING.format(line=21, column_name="Admin"),
        errors.UNKNOWN_USER_WARNING.format(line=22, email="kr@en.com"),
        errors.OWNER_MISSING.format(line=22, column_name="Admin"),
        errors.OWNER_MISSING.format(line=26, column_name="Admin"),
        errors.UNKNOWN_USER_WARNING.format(
            line=27, email="user@exameuple.com"),
        errors.OWNER_MISSING.format(line=27, column_name="Admin"),
    }

    expected_errors = {
        "Line 6: Field 'man CH' is required. The line will be ignored.",
        "Line 9: Field 'man select' is required. The line will be ignored.",
        "Line 10: Field 'man select' is required. The line will be ignored.",
        "Line 12: Field 'man CH' is required. The line will be ignored.",
        "Line 16: Field 'man Date' is required. The line will be ignored.",
        "Line 18: Field 'man RT' is required. The line will be ignored.",
        "Line 20: Field 'man text' is required. The line will be ignored.",
        "Line 21: Field 'man person' is required. The line will be ignored.",
        "Line 28: Field 'Title' is required. The line will be ignored."
    }

    self.assertEqual(expected_warnings, set(response["row_warnings"]))
    self.assertEqual(expected_errors, set(response["row_errors"]))
    self.assertEqual(17, response["created"])
    self.assertEqual(9, response["ignored"])
    self.assertEqual(17, Product.query.count())

    product10 = Product.query.filter_by(slug="prod10").first()
    people_emails = {cav.attribute_object.email
                     for cav in product10.custom_attribute_values
                     if cav.custom_attribute.attribute_type == "Map:Person"}

    self.assertEqual(people_emails, {"user1@ggrc.com", "user@example.com"})

  def test_product_ca_import_update(self):
    """Test updating of product with all custom attributes.

    This tests covers updates for all possible custom attributes
    """
    self.import_file("custom_attribute_tests.csv")
    self.import_file("custom_attribute_update_tests.csv")
    prod_0 = Product.query.filter(Product.slug == "prod0").first()
    prod_0_expected = {
        u"normal text": u"edited normal text",
        u"man text": u"edited man text",
        u"normal RT": u"some <br> edited rich <br> text",
        u"man RT": u"other edited <br> rich text",
        u"normal Date": u"2017-09-14",
        u"man Date": u"2018-01-17",
        u"normal CH": u"1",
        u"man CH": u"0",
        u"normal select": u"\u017e",
        u"man select": u"f",
        u"normal person": u"Person",
        u"man person": u"Person",
    }
    prod_0_new = {c.custom_attribute.title: c.attribute_value
                  for c in prod_0.custom_attribute_values}
    self.assertEqual(prod_0_expected, prod_0_new)

    people_emails = {cav.attribute_object.email
                     for cav in prod_0.custom_attribute_values
                     if cav.custom_attribute.attribute_type == "Map:Person"}

    self.assertEqual(people_emails, {"user@example.com", "user@example.com"})

  def tests_ca_export(self):
    """Test exporting products with custom attributes

    This test checks that we get a proper response when exporting objects with
    custom attributes and that the response data actually contains more lines
    than an empty template would.
    This tests relys on the import tests to work. If those fail they need to be
    fixied before this one.
    """
    filename = "custom_attribute_tests.csv"
    self.import_file(filename)

    data = {
        "export_to": "csv",
        "objects": [{
            "object_name": "Product",
            "filters": {
                "expression": {},
            },
            "fields": "all",
        }]
    }
    response = self.client.post("/_service/export_csv", data=dumps(data),
                                headers=self.headers)

    self.assert200(response)
    self.assertEqual(len(response.data.splitlines()), 33)
    self.assertIn("\"Accepted values are", response.data)
    self.assertIn("number.\n\nAccepted values are", response.data)
    self.assertIn("Birthday", response.data)

  def tests_ca_export_filters(self):
    """Test filtering on custom attribute values."""

    filename = "custom_attribute_tests.csv"
    self.import_file(filename)

    # TODO: there is a bug that imports do not index all custom attributes.
    # After fixing this bug remove the following two lines.
    from ggrc import views
    views.do_reindex()

    data = {
        "export_to": "csv",
        "objects": [{
            "object_name": "Product",
            "filters": {
                "expression": {
                    "left": "normal text",
                    "op": {"name": "="},
                    "right": "some text",
                },
            },
            "fields": "all",
        }]
    }
    response = self.client.post("/_service/export_csv", data=dumps(data),
                                headers=self.headers)
    self.assert200(response)
    self.assertIn("some text", response.data)

  def test_multi_word_object_with_ca(self):
    """Test multi-word (e.g. Access Group, Data Asset) object import"""
    filename = "multi_word_object_custom_attribute_test.csv"
    response = self.import_file(filename)[0]
    self.assertEqual([], response["row_warnings"])
    self.assertEqual([], response["row_errors"])
    self.assertEqual(10, response["created"])
    self.assertEqual(0, response["ignored"])
    self.assertEqual(0, response["updated"])
    self.assertEqual(10, AccessGroup.query.count())

    for id_ in range(1, 11):
      access_group = AccessGroup.query.filter(
          AccessGroup.slug == "ag-{}".format(id_)).first()
      filtered = [val for val in access_group.custom_attribute_values if
                  val.attribute_value == "some text {}".format(id_)]
      self.assertEqual(len(filtered), 1)
