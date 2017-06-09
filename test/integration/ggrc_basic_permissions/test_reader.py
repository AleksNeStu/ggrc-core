# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""
Test Reader role
"""

from integration.ggrc import TestCase
from ggrc.models import get_model
from ggrc.models import all_models
from integration.ggrc.api_helper import Api
from integration.ggrc.generator import Generator
from integration.ggrc.generator import ObjectGenerator


class TestReader(TestCase):
  """ Test reader role """

  def setUp(self):
    super(TestReader, self).setUp()
    self.generator = Generator()
    self.api = Api()
    self.object_generator = ObjectGenerator()
    self.init_users()

  def init_users(self):
    """ Init users needed by the test cases """
    users = [("reader", "Reader"), ("admin", "Administrator")]
    self.users = {}
    for (name, role) in users:
      _, user = self.object_generator.generate_person(
          data={"name": name}, user_role=role)
      self.users[name] = user

  def test_admin_page_access(self):
    return
    for role, code in (("reader", 403), ("admin", 200)):
      self.api.set_user(self.users[role])
      self.assertEqual(self.api.client.get("/admin").status_code, code)

  def test_reader_can_crud(self):
    return
    """ Test Basic create/read,update/delete operations """
    self.api.set_user(self.users["reader"])
    all_errors = []
    base_models = set([
        "Control", "Assessment", "DataAsset", "Contract",
        "Policy", "Regulation", "Standard", "Document", "Facility",
        "Market", "Objective", "OrgGroup", "Vendor", "Product",
        "Clause", "System", "Process", "Issue", "Project", "AccessGroup",
    ])
    for model_singular in base_models:
      try:
        model = get_model(model_singular)
        table_singular = model._inflector.table_singular
        table_plural = model._inflector.table_plural
        # Test POST creation
        response = self.api.post(model, {
            table_singular: {
                "title": model_singular,
                "context": None,
                "reference_url": "ref",
                "contact": {
                    "type": "Person",
                    "id": self.users["reader"].id,
                },
            },
        })
        if response.status_code != 201:
          all_errors.append("{} post creation failed {} {}".format(
              model_singular, response.status, response.data))
          continue

        obj_id = response.json.get(table_singular).get("id")

        # Test GET when owner
        response = self.api.get(model, obj_id)
        if response.status_code != 200:
          all_errors.append("{} can't GET object {}".format(
              model_singular, response.status))
          continue

        # Test GET collection when owner
        response = self.api.get_collection(model, obj_id)
        collection = response.json.get(
            "{}_collection".format(table_plural)).get(table_plural)
        if len(collection) == 0:
          all_errors.append(
              "{} cannot retrieve object even if owner (collection)".format(
                  model_singular))
          continue
      except:
          all_errors.append("{} exception thrown".format(model_singular))
          raise
    self.assertEqual(all_errors, [])

  def test_reader_search(self):
    return
    """ Test if reader can see the correct object while using search api """
    self.api.set_user(self.users['admin'])
    self.api.post(all_models.Regulation, {
        "regulation": {"title": "Admin regulation", "context": None},
    })
    self.api.set_user(self.users['reader'])
    response = self.api.post(all_models.Policy, {
        "policy": {"title": "reader Policy", "context": None},
    })
    obj_id = response.json.get("policy").get("id")
    self.api.post(all_models.ObjectOwner, {"object_owner": {
        "person": {
            "id": self.users['reader'].id,
            "type": "Person",
        }, "ownable": {
            "type": "Policy",
            "id": obj_id,
        }, "context": None}})
    response, _ = self.api.search("Regulation,Policy")
    entries = response.json["results"]["entries"]
    self.assertEqual(len(entries), 2)
    response, _ = self.api.search("Regulation,Policy", counts=True)
    self.assertEqual(response.json["results"]["counts"]["Policy"], 1)
    self.assertEqual(response.json["results"]["counts"]["Regulation"], 1)

  def _get_count(self, obj):
    """ Return the number of counts for the given object from search """
    response, _ = self.api.search(obj, counts=True)
    return response.json["results"]["counts"].get(obj)

  def test_reader_should_see_users(self):
    """ Test if creator can see all the users in the system """
    self.api.set_user(self.users['admin'])
    admin_count = self._get_count("Person")
    self.api.set_user(self.users['reader'])
    reader_count = self._get_count("Person")
    self.assertEqual(admin_count, reader_count)

  def test_relationships_access(self):
    """Check if reader can access relationship objects"""
    self.api.set_user(self.users['admin'])
    _, obj_0 = self.generator.generate(all_models.Regulation, "regulation", {
        "regulation": {"title": "Test regulation", "context": None},
    })
    _, obj_1 = self.generator.generate(all_models.Regulation, "regulation", {
        "regulation": {"title": "Test regulation 2", "context": None},
    })
    response, rel = self.generator.generate(
        all_models.Relationship, "relationship", {
            "relationship": {"source": {
                "id": obj_0.id,
                "type": "Regulation"
            }, "destination": {
                "id": obj_1.id,
                "type": "Regulation"
            }, "context": None},
        }
    )
    relationship_id = rel.id
    self.assertEqual(response.status_code, 201)
    self.api.set_user(self.users['reader'])
    response = self.api.get_collection(all_models.Relationship,
                                       relationship_id)
    self.assertEqual(response.status_code, 200)
    num = len(response.json["relationships_collection"]["relationships"])
    self.assertEqual(num, 1)

  def test_creation_of_mappings(self):
    self.generator.api.set_user(self.users["admin"])
    _, control = self.generator.generate(all_models.Control, "control", {
        "control": {"title": "Test Control", "context": None},
    })
    self.generator.api.set_user(self.users['reader'])
    _, program = self.generator.generate(all_models.Program, "program", {
        "program": {"title": "Test Program", "context": None},
    })

    response, _ = self.generator.generate(
        all_models.Relationship, "relationship", {
            "relationship": {"destination": {
                "id": program.id,
                "type": "Program"
            }, "source": {
                "id": control.id,
                "type": "Control"
            }, "context": {
                "id": program.context.id,
                "type": "context"
            }},
        })
    self.assertEqual(response.status_code, 403)
