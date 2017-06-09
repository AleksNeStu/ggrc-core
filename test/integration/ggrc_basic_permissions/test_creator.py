# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""
Test Program Creator role
"""

from integration.ggrc import TestCase
from ggrc.models import get_model
from ggrc.models import all_models
from integration.ggrc.api_helper import Api
from integration.ggrc.generator import Generator
from integration.ggrc.generator import ObjectGenerator
from integration.ggrc.models import factories


class TestCreator(TestCase):
  """ TestCreator """

  def setUp(self):
    super(TestCreator, self).setUp()
    self.generator = Generator()
    self.api = Api()
    self.object_generator = ObjectGenerator()
    self.init_users()

  def init_users(self):
    """ Init users needed by the test cases """

    users = [("creator", "Creator"), ("admin", "Administrator")]
    self.users = {}
    for (name, role) in users:
      _, user = self.object_generator.generate_person(
          data={"name": name}, user_role=role)
      self.users[name] = user

  def test_admin_page_access(self):
    for role, code in (("creator", 403), ("admin", 200)):
      self.api.set_user(self.users[role])
      self.assertEqual(self.api.client.get("/admin").status_code, code)

  def test_creator_can_crud(self):
    """ Test Basic create/read,update/delete operations """
    self.api.set_user(self.users["creator"])
    creator_id = self.users["creator"].id
    audit_id = factories.AuditFactory().id
    all_errors = []
    base_models = set([
        "Control", "DataAsset", "Contract",
        "Policy", "Regulation", "Standard", "Document", "Facility",
        "Market", "Objective", "OrgGroup", "Vendor", "Product",
        "Clause", "System", "Process", "Project", "AccessGroup"
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
                    "id": creator_id,
                },
                "audit": {  # this is ignored on everything but Issues
                    "id": audit_id,
                    "type": "Audit",
                }
            },
        })
        if response.status_code != 201:
          all_errors.append("{} post creation failed {} {}".format(
              model_singular, response.status, response.data))
          continue

        # Test GET when not owner
        obj_id = response.json.get(table_singular).get("id")
        response = self.api.get(model, obj_id)
        if response.status_code != 403:  # we are not onwers yet
          all_errors.append(
              "{} can retrieve object if not owner".format(model_singular))
          continue
        response = self.api.get_collection(model, obj_id)
        collection = response.json.get(
            "{}_collection".format(table_plural)).get(table_plural)
        if len(collection) != 0:
          all_errors.append(
              "{} can retrieve object if not owner (collection)"
              .format(model_singular))
          continue

        # Test GET when owner
        acr = factories.AccessControlRoleAdminFactory(
            object_type=model_singular
        )
        factories.AccessControlListFactory(
            object_id=obj_id,
            object_type=model_singular,
            ac_role=acr,
            person_id=creator_id
        )
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
              "{} cannot retrieve object even if owner (collection)"
              .format(model_singular))
          continue
      except:
        all_errors.append("{} exception thrown".format(model_singular))
        raise
    self.assertEqual(all_errors, [])

  def test_creator_search(self):
    """Test if creator can see the correct object while using the search api"""
    self.api.set_user(self.users['admin'])
    self.api.post(all_models.Regulation, {
        "regulation": {"title": "Admin regulation", "context": None},
    })
    self.api.set_user(self.users['creator'])
    acr_id = factories.AccessControlRoleAdminFactory(object_type="Policy").id
    response = self.api.post(all_models.Policy, {
        "policy": {
            "title": "Creator Policy",
            "context": None,
            "access_control_list": [{
                "person": {
                    "id": self.users["creator"].id,
                    "type": "Person",
                },
                "ac_role_id": acr_id,
                "context": None
            }],
        },
    })
    response.json.get("policy").get("id")
    response, _ = self.api.search("Regulation,Policy")
    entries = response.json["results"]["entries"]
    self.assertEqual(len(entries), 1)
    self.assertEqual(entries[0]["type"], "Policy")
    response, _ = self.api.search("Regulation,Policy", counts=True)
    self.assertEqual(response.json["results"]["counts"]["Policy"], 1)
    self.assertEqual(
        response.json["results"]["counts"].get("Regulation"), None)

  def _get_count(self, obj):
    """ Return the number of counts for the given object from search """
    response, _ = self.api.search(obj, counts=True)
    return response.json["results"]["counts"].get(obj)

  def test_creator_should_see_users(self):
    """ Test if creator can see all the users in the system """
    self.api.set_user(self.users['admin'])
    admin_count = self._get_count("Person")
    self.api.set_user(self.users['creator'])
    creator_count = self._get_count("Person")
    self.assertEqual(admin_count, creator_count)

  def test_relationships_access(self):
    """Check if creator cannot access relationship objects"""
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
    self.api.set_user(self.users['creator'])
    response = self.api.get_collection(all_models.Relationship,
                                       relationship_id)
    self.assertEqual(response.status_code, 200)
    num = len(response.json["relationships_collection"]["relationships"])
    self.assertEqual(num, 0)

  def test_revision_access(self):
    """Check if creator can access the right revision objects."""

    def gen(title, extra_data=None):
      section_content = {"title": title, "context": None}
      section_content.update(**extra_data) if extra_data else None
      return self.generator.generate(all_models.Section, "section", {
          "section": section_content
      })[1]

    def check(obj, expected):
      """Check that how many revisions of an object current user can see."""
      response = self.api.get_query(
          all_models.Revision,
          "resource_type={}&resource_id={}".format(obj.type, obj.id)
      )
      self.assertEqual(response.status_code, 200)
      self.assertEqual(
          len(response.json['revisions_collection']['revisions']),
          expected
      )

    self.api.set_user(self.users["admin"])
    obj_1 = gen("Test Section 1")

    self.api.set_user(self.users["creator"])
    acr_id = factories.AccessControlRoleAdminFactory(object_type="Section").id
    linked_acl = {
        "access_control_list": [{
            "person": {
                "id": self.users["creator"].id,
                "type": "Person",
            },
            "ac_role_id": acr_id,
            "context": None
        }]
    }
    check(obj_1, 0)
    obj_2 = gen("Test Section 2", linked_acl)
    obj2_acl = obj_2.access_control_list[0]
    check(obj_2, 1)
    check(obj2_acl, 1)
