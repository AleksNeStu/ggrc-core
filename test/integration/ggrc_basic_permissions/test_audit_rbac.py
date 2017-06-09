# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Test audit RBAC"""
import copy

from os.path import abspath
from os.path import dirname
from os.path import join
from collections import defaultdict

# pylint: disable=unused-import
from ggrc.app import app  # NOQA
from ggrc.models import all_models
import ggrc_basic_permissions as perms

from integration.ggrc import TestCase
from integration.ggrc.api_helper import Api
from integration.ggrc.generator import ObjectGenerator
from integration.ggrc.models import factories

from appengine import base


class TestAuditRBAC(TestCase):
  """Test audit RBAC"""

  CSV_DIR = join(abspath(dirname(__file__)), "test_csvs")

  @classmethod
  def setUpClass(cls):
    TestCase.clear_data()
    cls.response = cls._import_file("audit_rbac.csv")
    cls.people = all_models.Person.eager_query().all()
    cls.audit = all_models.Audit.eager_query().first()
    sources = set(r.source for r in cls.audit.related_sources)
    destinations = set(r.destination for r in cls.audit.related_destinations)
    related = [obj for obj in sources.union(destinations)
               if not isinstance(obj, all_models.Person)]
    cls.related_objects = related

  def setUp(self):
    """Imports test_csvs/audit_rbac.csv needed by the tests"""
    self._check_csv_response(self.response, {})
    self.api = Api()
    self.client.get("/login")

  def read(self, objects):
    """Attempt to do a GET request for every object in the objects list"""
    responses = []
    for obj in objects:
      status_code = self.api.get(obj.__class__, obj.id).status_code
      responses.append((obj.type, status_code))
    return responses

  def update(self, objects):
    """Attempt to do a PUT request for every object in the objects list"""
    responses = []
    for obj in objects:
      response = self.api.get(obj.__class__, obj.id)
      status_code = response.status_code
      if response.status_code == 200:
        status_code = self.api.put(obj, response.json).status_code
      responses.append((obj.type, status_code))
    return responses

  def call_api(self, method, expected_statuses):
    """Calls the REST api with a given method and returns a list of
       status_codes that do not match the expected_statuses dict"""
    all_errors = []
    for person in self.people:
      self.api.set_user(person)
      responses = method(self.related_objects + [self.audit])
      for type_, code in responses:
        if code != expected_statuses[person.email]:
          all_errors.append("{} does not have {} access to {} ({})".format(
              person.email, method.__name__, type_, code))
    return all_errors

  def test_read_access_on_mapped(self):
    """Test if people have read access to mapped objects.

    All users except creator@test.com should have read access."""
    expected_statuses = defaultdict(lambda: 200)
    for exception in ("creator@test.com",):
      expected_statuses[exception] = 403
    errors = self.call_api(self.read, expected_statuses)
    assert not errors, "\n".join(errors)

  def test_update_access_on_mapped(self):
    """Test if people have upate access to mapped objects.

    All users except creator@test.com, reader@test.com, creatorpr@test.com,
    readerpr@test.com should have update access."""
    expected_statuses = defaultdict(lambda: 200)
    for exception in ("creator@test.com", "reader@test.com",
                      "creatorpr@test.com", "readerpr@test.com"):
      expected_statuses[exception] = 403
    errors = self.call_api(self.update, expected_statuses)
    assert not errors, "\n".join(errors)


@base.with_memcache
class TestPermissionsOnAssessmentTemplate(TestCase):
  """ Test check permissions for ProgramEditor on

  get and post assessment_temaplte action"""

  def setUp(self):
    super(TestPermissionsOnAssessmentTemplate, self).setUp()
    self.api = Api()
    self.generator = ObjectGenerator()
    _, program = self.generator.generate_object(all_models.Program)
    program_id = program.id
    _, self.editor = self.generator.generate_person(
        user_role="Creator"
    )
    role = perms.all_models.Role.query.filter(
        perms.all_models.Role.name == "ProgramEditor"
    ).first()
    self.generator.generate_user_role(
        self.editor,
        role,
        all_models.Program.query.get(program_id)
    )
    _, audit = self.generator.generate_object(
        all_models.Audit,
        {
            "title": "Audit",
            "program": {"id": program_id},
            "status": "Planned"
        },
    )
    audit_id = audit.id

    generated_at = self.generator.generate_object(
        all_models.AssessmentTemplate,
        {
            "title": "Template",
            "_NON_RELEVANT_OBJ_TYPES": {},
            "_objectTypes": {},
            "audit": {"id": audit.id},
            "audit_title": audit.title,
            "people_value": [],
            "default_people": {
                "assessors": "Admin",
                "verifiers": "Admin",
            },
            "context": {"id": audit.context.id},
        }
    )
    self.assessment_template_resp, assessment_template = generated_at
    assessment_template_id = assessment_template.id
    self.api.set_user(self.editor)
    self.perms_data = self.api.client.get("/permissions").json
    self.audit = all_models.Audit.query.get(audit_id)
    self.assessment_template = all_models.AssessmentTemplate.query.get(
        assessment_template_id)

  def test_post_action(self):
    """Test create action on AssessmentTemplate created by api"""
    data = [{
        "assessment_template": {
            "_NON_RELEVANT_OBJ_TYPES": {},
            "_objectTypes": {},
            "audit": {"id": self.audit.id},
            "audit_title": self.audit.title,
            "people_value": [],
            "default_people": {
                "assessors": "Admin",
                "verifiers": "Admin",
            },
            "context": {"id": self.audit.context.id},
            "title": "123",
        }
    }]
    self.api.set_user(self.editor)
    resp = self.api.post(all_models.AssessmentTemplate, data)
    self.assert200(resp)

  def test_get_action(self):
    """Test read action on AssessmentTemplate created by api"""
    resp = self.api.get(all_models.AssessmentTemplate,
                        self.assessment_template.id)
    self.assert200(resp)

  def test_put_action(self):
    """Test update action on AssessmentTemplate created by api"""
    to_update = copy.deepcopy(self.assessment_template_resp.json)
    new_title = "new_{}".format(self.assessment_template.title)
    to_update['assessment_template']['title'] = new_title
    resp = self.api.put(self.assessment_template, to_update)
    self.assert200(resp)
    assessment_tmpl = all_models.AssessmentTemplate.query.get(
        self.assessment_template.id
    )
    self.assertEqual(new_title, assessment_tmpl.title)

  def test_delete_action(self):
    """Test delete action on AssessmentTemplate created by api"""
    resp = self.api.delete(self.assessment_template)
    self.assert200(resp)
    self.assertFalse(all_models.AssessmentTemplate.query.filter(
        all_models.AssessmentTemplate == self.assessment_template.id).all())


@base.with_memcache
class TestPermissionsOnAssessmentRelatedAssignables(TestCase):
  """Test check Reader permissions for Assessment related assignables

  Global Reader once assigned to Assessment as Assessor, should have
  permissions to read/update/delete URLs(Documents) related to this Assessment
  """
  def setUp(self):
    super(TestPermissionsOnAssessmentRelatedAssignables, self).setUp()
    self.api = Api()
    self.generator = ObjectGenerator()

    _, self.reader = self.generator.generate_person(
        user_role="Reader"
    )
    audit = factories.AuditFactory()
    assessment = factories.AssessmentFactory(audit=audit)
    object_person_rel = factories.RelationshipFactory(
        source=assessment,
        destination=self.reader
    )
    factories.RelationshipAttrFactory(
        relationship_id=object_person_rel.id,
        attr_name="AssigneeType",
        attr_value="Assessor"
    )

    factories.RelationshipFactory(source=audit, destination=assessment)
    document = factories.DocumentFactory()
    document_id = document.id
    doc_rel = factories.RelationshipFactory(source=assessment,
                                            destination=document)
    doc_rel_id = doc_rel.id

    self.api.set_user(self.reader)
    self.document = all_models.Document.query.get(document_id)
    self.doc_relationship = all_models.Relationship.query.get(doc_rel_id)

  def test_delete_action(self):
    """Test permissions for delete action on Document"""
    resp = self.api.delete(self.document)
    self.assert200(resp)
    self.assertFalse(all_models.Document.query.filter(
        all_models.Document.id == self.document.id).all())

  def test_unmap_action(self):
    """Test permissions for unmap action on Document"""
    resp = self.api.delete(self.doc_relationship)
    self.assert200(resp)
    self.assertFalse(all_models.Relationship.query.filter(
        all_models.Relationship.id == self.doc_relationship.id).all())
