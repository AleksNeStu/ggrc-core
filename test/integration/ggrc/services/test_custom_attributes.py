# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Tests for PUT and POST requests for objects with custom attributes

These tests include:
- Creating an object with custom attributes (POST request).
- Editing existing custom attributes on an object.
- Adding custom attributes to existing object.

"""


from ggrc import utils
from ggrc import models
from ggrc import builder

from integration.ggrc.services import TestCase
from integration.ggrc.generator import ObjectGenerator


class ProductTestCase(TestCase):
  """Test case for Product post and put requests."""

  def setUp(self):
    super(ProductTestCase, self).setUp()
    self.generator = ObjectGenerator()
    self.client.get("/login")

  def _put(self, url, data, extra_headers=None):
    """Perform a put request."""
    headers = {'X-Requested-By': 'Unit Tests'}
    headers.update(extra_headers)
    return self.client.put(
        url,
        content_type='application/json',
        data=utils.as_json(data),
        headers=headers,
    )

  def _post(self, data):
    """Perform a post request."""
    return self.client.post(
        "/api/products",
        content_type='application/json',
        data=utils.as_json(data),
        headers={'X-Requested-By': 'Unit Tests'},
    )


class TestGlobalCustomAttributes(ProductTestCase):
  """Tests for API updates for custom attribute values."""

  def test_custom_attribute_post(self):
    """Test post object with custom attributes."""
    gen = self.generator.generate_custom_attribute
    _, cad = gen("product", attribute_type="Text", title="normal text")
    pid = models.Person.query.first().id

    product_data = [
        {
            "product": {
                "kind": None,
                "owners": [],
                "custom_attribute_values": [{
                    "attribute_value": "my custom attribute value",
                    "custom_attribute_id": cad.id,
                }],
                "contact": {
                    "id": pid,
                    "href": "/api/people/{}".format(pid),
                    "type": "Person"
                },
                "title": "simple product",
                "description": "",
                "secondary_contact": None,
                "notes": "",
                "url": "",
                "reference_url": "",
                "slug": "",
                "context": None
            }
        }
    ]

    response = self._post(product_data)
    ca_json = response.json[0][1]["product"]["custom_attribute_values"][0]
    self.assertIn("attributable_id", ca_json)
    self.assertIn("attributable_type", ca_json)
    self.assertIn("attribute_value", ca_json)
    self.assertIn("id", ca_json)
    self.assertEqual(ca_json["attribute_value"],
                     "my custom attribute value")

    product = models.Product.eager_query().first()
    self.assertEqual(len(product.custom_attribute_values), 1)
    self.assertEqual(
        product.custom_attribute_values[0].attribute_value,
        "my custom attribute value"
    )

  def test_custom_attribute_put_add(self):
    """Test edits with adding new CA values."""
    gen = self.generator.generate_custom_attribute
    _, cad = gen("product", attribute_type="Text", title="normal text")
    pid = models.Person.query.first().id

    product_data = [
        {
            "product": {
                "kind": None,
                "owners": [],
                "contact": {
                    "id": pid,
                    "href": "/api/people/{}".format(pid),
                    "type": "Person"
                },
                "title": "simple product",
                "description": "",
                "secondary_contact": None,
                "notes": "",
                "url": "",
                "reference_url": "",
                "slug": "",
                "context": None
            }
        }
    ]

    response = self._post(product_data)
    product_url = response.json[0][1]["product"]["selfLink"]
    headers = self.client.get(product_url).headers

    product_data[0]["product"]["custom_attribute_values"] = [{
        "attribute_value": "added value",
        "custom_attribute_id": cad.id,
    }]

    response = self._put(product_url, product_data[0], extra_headers={
        'If-Unmodified-Since': headers["Last-Modified"],
        'If-Match': headers["Etag"],
    })

    product = response.json["product"]

    self.assertEqual(len(product["custom_attribute_values"]), 1)
    ca_json = product["custom_attribute_values"][0]
    self.assertIn("attributable_id", ca_json)
    self.assertIn("attributable_type", ca_json)
    self.assertIn("attribute_value", ca_json)
    self.assertIn("id", ca_json)
    self.assertEqual(ca_json["attribute_value"],
                     "added value")

    product = models.Product.eager_query().first()
    self.assertEqual(len(product.custom_attribute_values), 1)
    self.assertEqual(
        product.custom_attribute_values[0].attribute_value,
        "added value"
    )

    headers = self.client.get(product_url).headers

    product_data[0]["product"]["custom_attribute_values"] = [{
        "attribute_value": "edited value",
        "custom_attribute_id": cad.id,
    }]

    response = self._put(product_url, product_data[0], extra_headers={
        'If-Unmodified-Since': headers["Last-Modified"],
        'If-Match': headers["Etag"],
    })

    product = response.json["product"]
    ca_json = product["custom_attribute_values"][0]
    self.assertIn("attributable_id", ca_json)
    self.assertIn("attributable_type", ca_json)
    self.assertIn("attribute_value", ca_json)
    self.assertIn("id", ca_json)
    self.assertEqual(ca_json["attribute_value"],
                     "edited value")

  def test_custom_attribute_get(self):
    """Check if get returns the whole CA value and not just the stub."""
    gen = self.generator.generate_custom_attribute
    _, cad = gen("product", attribute_type="Text", title="normal text")
    pid = models.Person.query.first().id

    product_data = [
        {
            "product": {
                "kind": None,
                "owners": [],
                "custom_attribute_values": [{
                    "attribute_value": "my custom attribute value",
                    "custom_attribute_id": cad.id,
                }],
                "contact": {
                    "id": pid,
                    "href": "/api/people/{}".format(pid),
                    "type": "Person"
                },
                "title": "simple product",
                "description": "",
                "secondary_contact": None,
                "notes": "",
                "url": "",
                "reference_url": "",
                "slug": "",
                "context": None
            }
        }
    ]

    response = self._post(product_data)
    product_url = response.json[0][1]["product"]["selfLink"]
    get_response = self.client.get(product_url)
    product = get_response.json["product"]
    self.assertIn("custom_attribute_values", product)
    self.assertEqual(len(product["custom_attribute_values"]), 1)
    cav = product["custom_attribute_values"][0]
    self.assertIn("custom_attribute_id", cav)
    self.assertIn("attribute_value", cav)
    self.assertIn("id", cav)


class TestOldApiCompatibility(ProductTestCase):
  """Test Legacy CA values API.

  These tests check that the old way of setting custom attribute values still
  works and that If both ways are used, the legacy code is ignored.
  """

  def test_custom_attribute_post_both(self):
    """Test post with both custom attribute api options.

    This tests tries to set a custom attribute on the new and the old way at
    once. The old option should be ignored and the new value should be set.
    """
    gen = self.generator.generate_custom_attribute
    _, cad = gen("product", attribute_type="Text", title="normal text")
    cad_json = builder.json.publish(cad.__class__.query.get(cad.id))
    cad_json = builder.json.publish_representation(cad_json)
    pid = models.Person.query.first().id

    product_data = [
        {
            "product": {
                "kind": None,
                "owners": [],
                "custom_attribute_definitions":[
                    cad_json,
                ],
                "custom_attribute_values": [{
                    "attribute_value": "new value",
                    "custom_attribute_id": cad.id,
                }],
                "custom_attributes": {
                    cad.id: "old value",
                },
                "contact": {
                    "id": pid,
                    "href": "/api/people/{}".format(pid),
                    "type": "Person"
                },
                "title": "simple product",
                "description": "",
                "secondary_contact": None,
                "notes": "",
                "url": "",
                "reference_url": "",
                "slug": "",
                "context": None
            }
        }
    ]

    response = self._post(product_data)
    ca_json = response.json[0][1]["product"]["custom_attribute_values"][0]
    self.assertEqual(ca_json["attribute_value"], "new value")

    product = models.Product.eager_query().first()
    self.assertEqual(len(product.custom_attribute_values), 1)
    self.assertEqual(
        product.custom_attribute_values[0].attribute_value,
        "new value"
    )

  def test_custom_attribute_post_old(self):
    """Test post with old style custom attribute values.

    This tests that the legacy way of setting custom attribute values still
    works.
    """
    gen = self.generator.generate_custom_attribute
    _, cad = gen("product", attribute_type="Text", title="normal text")
    cad_json = builder.json.publish(cad.__class__.query.get(cad.id))
    cad_json = builder.json.publish_representation(cad_json)
    pid = models.Person.query.first().id

    product_data = [
        {
            "product": {
                "kind": None,
                "owners": [],
                "custom_attribute_definitions":[
                    cad_json,
                ],
                "custom_attribute_values": [{
                    "id": 1,
                    "href": "/api/custom_attribute_values/1",
                    "type": "CustomAttributeValues"
                }],
                "custom_attributes": {
                    cad.id: "old value",
                },
                "contact": {
                    "id": pid,
                    "href": "/api/people/{}".format(pid),
                    "type": "Person"
                },
                "title": "simple product",
                "description": "",
                "secondary_contact": None,
                "notes": "",
                "url": "",
                "reference_url": "",
                "slug": "",
                "context": None
            }
        }
    ]

    response = self._post(product_data)
    self.assert200(response)
    ca_json = response.json[0][1]["product"]["custom_attribute_values"][0]
    self.assertEqual(ca_json["attribute_value"], "old value")

    product = models.Product.eager_query().first()
    self.assertEqual(len(product.custom_attribute_values), 1)
    self.assertEqual(
        product.custom_attribute_values[0].attribute_value,
        "old value"
    )
