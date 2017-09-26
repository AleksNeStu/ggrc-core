# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""
Test Creator role with Audit scoped roles
"""

from ggrc import db
from ggrc.models import all_models
from integration.ggrc import TestCase
from integration.ggrc.api_helper import Api
from integration.ggrc.generator import Generator
from integration.ggrc.generator import ObjectGenerator
from integration.ggrc.models import factories


class TestCreatorAudit(TestCase):
  """Set up necessary objects and test Creator role with Audit roles"""

  def setUp(self):
    super(TestCreatorAudit, self).setUp()
    self.generator = Generator()
    self.api = Api()
    self.object_generator = ObjectGenerator()
    self.init_users()
    self.init_roles()
    self.init_test_cases()
    self.objects = {}

  def init_test_cases(self):
    """Create a dict of all possible test cases."""
    self.test_cases = {
        "Auditor": {
            "audit_role": "Auditor",
            "objects": {
                "audit": {
                    "get": 200,
                    "put": 403,
                    "delete": 403
                },
                "mapped_Issue": {
                    "get": 200,
                    "put": 200,
                    "delete": 200
                },
                "unrelated_Issue": {
                    "get": 403,
                    "put": 403,
                    "delete": 403,
                    "map": 403,
                },
                "mapped_Assessment": {
                    "get": 200,
                    "put": 200,
                    "delete": 200
                },
                "unrelated_Assessment": {
                    "get": 403,
                    "put": 403,
                    "delete": 403,
                    "map": 403,
                }
            }
        },
    }

  def init_roles(self):
    """Create a delete request for the given object."""
    response = self.api.get_query(all_models.Role, "")
    self.roles = {}
    for role in response.json.get("roles_collection").get("roles"):
      self.roles[role.get("name")] = role

  def init_users(self):
    """Create users used by test cases."""
    self.people = {}
    for name in ["creator", "notmapped", "mapped", "Auditor"]:
      _, user = self.object_generator.generate_person(
          data={"name": name}, user_role="Creator")
      self.people[name] = user

    _, user = self.object_generator.generate_person(
        data={"name": "editor"}, user_role="Editor")
    self.people["editor"] = user

  def delete(self, obj):
    """Create a delete request for the given object.

    Args:
        obj (model instance): target object to delete
    Returns:
        int: http response status code
    """
    return self.api.delete(obj).status_code

  def get(self, obj):
    """Create a get request for the given object.

    Args:
        obj (model instance): target object to get
    Returns:
        int: http response status code
    """
    return self.api.get(obj.__class__, obj.id).status_code

  def put(self, obj):
    """Create a put request for the given object.

    Args:
        obj (model instance): target object to put
    Returns:
        int: http response status code
    """
    response = self.api.get(obj.__class__, obj.id)
    if response.status_code == 200:
      return self.api.put(obj, response.json).status_code
    else:
      return response.status_code

  def map(self, dest):
    """Map audit to dest.

    Args:
        dest (model instance): target object to map to the audit
    Returns:
        int: http response status code
    """
    response = self.api.post(all_models.Relationship, {
        "relationship": {"source": {
            "id": self.objects["audit"].id,
            "type": self.objects["audit"].type,
        }, "destination": {
            "id": dest.id,
            "type": dest.type
        }, "context": None},
    })
    return response.status_code

  def init_objects(self, test_case_name):
    """Create a Program, an Audit, and a Mapped object for the test case.

    Args:
        test_case_name (string): test case to init for
    """
    # Create a program
    dummy_audit = factories.AuditFactory()
    unrelated_audit = {
        "type": "Audit",
        "context_id": dummy_audit.context.id,
        "id": dummy_audit.id,
    }
    test_case = self.test_cases[test_case_name]
    editor = self.people.get('editor')
    self.api.set_user(editor)
    random_title = factories.random_str()
    response = self.api.post(all_models.Program, {
        "program": {"title": random_title, "context": None},
    })
    self.assertEqual(response.status_code, 201)
    program_id = response.json.get("program").get("id")
    self.objects["program"] = all_models.Program.query.get(program_id)
    response = self.api.post(all_models.Audit, {
        "audit": {
            "title": random_title + " audit",
            'program': {'id': program_id},
            "status": "Planned",
            "context": None
        }
    })
    self.assertEqual(response.status_code, 201)
    context = response.json.get("audit").get("context")
    audit_id = response.json.get("audit").get("id")
    self.objects["audit"] = all_models.Audit.query.get(audit_id)
    audits = {
        "mapped": {
            "type": "Audit",
            "context_id": context["id"],
            "id": audit_id,
        },
        "unrelated": unrelated_audit,
    }

    for prefix, audit_dict in audits.items():
      random_title = factories.random_str()

      response = self.api.post(all_models.Issue, {
          "issue": {
              "title": random_title,
              "context": None,
          },
      })
      self.assertEqual(response.status_code, 201)
      issue_id = response.json.get("issue").get("id")
      self.objects[prefix + "_Issue"] = all_models.Issue.query.get(issue_id)

      response = self.api.post(all_models.Assessment, {
          "assessment": {
              "title": random_title,
              "context": {
                  "type": "Context",
                  "id": audit_dict["context_id"],
              },
              "audit": audit_dict,
          },
      })
      self.assertEqual(response.status_code, 201)
      assessment_id = response.json.get("assessment").get("id")
      self.objects[prefix + "_Assessment"] = \
          all_models.Assessment.query.get(assessment_id)

    self.assertEqual(self.map(self.objects["mapped_Issue"]), 201)
    self.assertEqual(self.map(self.objects["mapped_Assessment"]), 201)

    # Add roles to mapped users:
    if "audit_role" in test_case:
      person = self.people.get(test_case_name)
      role = self.roles[test_case["audit_role"]]
      response = self.api.post(all_models.UserRole, {"user_role": {
          "person": {
              "id": person.id,
              "type": "Person",
              "href": "/api/people/{}".format(person.id),
          }, "role": {
              "type": "Role",
              "href": "/api/roles/{}".format(role["id"]),
              "id": role["id"],
          }, "context": {
              "type": "Context",
              "id": context.get("id"),
              "href": "/api/contexts/{}".format(context.get("id"))
          }}})
      self.assertEqual(response.status_code, 201)

  def test_creator_audit_roles(self):
    """ Test creator role with all audit scoped roles """
    # Check permissions based on test_cases:
    errors = []
    for test_case in self.test_cases:
      self.init_objects(test_case)
      person = self.people.get(test_case)
      objects = self.test_cases.get(test_case).get('objects')
      self.api.set_user(person)
      for obj, actions in objects.iteritems():
        for action in ("map", "get", "put", "delete"):
          if action not in actions:
            continue
          # reset sesion:
          db.session.commit()
          func = getattr(self, action)
          res = func(self.objects[obj])
          if res != actions[action]:
            errors.append(
                "{}: Tried {} on {}, but received {} instead of {}".format(
                    test_case, action, obj, res, actions[action]))

    self.assertEqual(errors, [])
