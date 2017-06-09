# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Integration tests for Assessment"""

import collections
import datetime

import freezegun
import ddt

from ggrc import db
from ggrc.models import all_models
from ggrc.converters import errors

from integration import ggrc
from integration.ggrc import generator
from integration.ggrc.models import factories
from integration.ggrc_basic_permissions.models import (
    factories as rbac_factories
)

from appengine import base


class TestAssessment(ggrc.TestCase):
  """Assessment test cases"""
  # pylint: disable=invalid-name

  def setUp(self):
    super(TestAssessment, self).setUp()
    self.api = ggrc.api_helper.Api()

  def test_auto_slug_generation(self):
    """Test auto slug generation"""
    factories.AssessmentFactory(title="Some title")
    ca = all_models.Assessment.query.first()
    self.assertEqual("ASSESSMENT-{}".format(ca.id), ca.slug)

  def test_enabling_comment_notifications_by_default(self):
    """New Assessments should have comment notifications enabled by default."""
    asmt = factories.AssessmentFactory()

    self.assertTrue(asmt.send_by_default)
    recipients = asmt.recipients.split(",") if asmt.recipients else []
    self.assertEqual(sorted(recipients), ["Assessor", "Creator", "Verifier"])

  def test_audit_changes_api(self):
    """Test that users can't change the audit mapped to an assessment."""
    audit_id = factories.AuditFactory().id
    asmt = factories.AssessmentFactory()
    correct_audit_id = asmt.audit_id
    response = self.api.put(asmt, {"audit": {"type": "Audit", "id": audit_id}})
    self.assert400(response)
    assessment = all_models.Assessment.query.first()
    self.assertEqual(assessment.audit_id, correct_audit_id)

  def test_put_no_audit_change(self):
    """Test that put requests works without audit changes"""
    asmt = factories.AssessmentFactory()
    correct_audit_id = asmt.audit_id
    response = self.api.put(asmt, {"audit": {
        "type": "Audit", "id": correct_audit_id
    }})
    self.assert200(response)
    assessment = all_models.Assessment.query.first()
    self.assertEqual(assessment.audit_id, correct_audit_id)

  def test_audit_changes_import(self):
    """Test that users can't change the audit mapped to an assessment."""
    audit = factories.AuditFactory()
    asmt = factories.AssessmentFactory()
    correct_audit_id = asmt.audit_id
    response = self.import_data(collections.OrderedDict([
        ("object_type", "Assessment"),
        ("Code*", asmt.slug),
        ("audit", audit.slug),
    ]))
    self._check_csv_response(response, {
        "Assessment": {
            "row_warnings": {
                errors.UNMODIFIABLE_COLUMN.format(line=3, column_name="Audit")
            }
        }
    })
    assessment = all_models.Assessment.query.first()
    self.assertEqual(assessment.audit_id, correct_audit_id)

  def test_no_audit_change_imports(self):
    """Test that imports work if audit field does not contain changes."""
    factories.AuditFactory()
    asmt = factories.AssessmentFactory()
    correct_audit_id = asmt.audit_id
    response = self.import_data(collections.OrderedDict([
        ("object_type", "Assessment"),
        ("Code*", asmt.slug),
        ("audit", asmt.audit.slug),
    ]))
    self._check_csv_response(response, {})
    assessment = all_models.Assessment.query.first()
    self.assertEqual(assessment.audit_id, correct_audit_id)

  def test_empty_audit_import(self):
    """Test empty audit import"""
    factories.AuditFactory()
    asmt = factories.AssessmentFactory()
    correct_audit_id = asmt.audit_id
    response = self.import_data(collections.OrderedDict([
        ("object_type", "Assessment"),
        ("Code*", asmt.slug),
        ("audit", ""),
    ]))
    self._check_csv_response(response, {})
    assessment = all_models.Assessment.query.first()
    self.assertEqual(assessment.audit_id, correct_audit_id)


@base.with_memcache
class TestAssessmentUpdates(ggrc.TestCase):
  """ Test various actions on Assessment updates """

  def setUp(self):
    super(TestAssessmentUpdates, self).setUp()
    self.api = ggrc.api_helper.Api()
    self.generator = generator.ObjectGenerator()
    _, program = self.generator.generate_object(all_models.Program)
    program_id = program.id
    _, audit = self.generator.generate_object(
        all_models.Audit,
        {
            "title": "Audit",
            "program": {"id": program_id},
            "status": "Planned"
        },
    )

    with freezegun.freeze_time("2015-04-01 17:13:15"):
      _, assessment = self.generator.generate_object(
          all_models.Assessment,
          {
              "title": "Assessment-Comment",
              "audit": {"id": audit.id},
              "audit_title": audit.title,
              "people_value": [],
              "default_people": {
                  "assessors": "Object Owners",
                  "verifiers": "Object Owners",
              },
              "context": {"id": audit.context.id},
          }
      )

    self.assessment_id = assessment.id
    self.assessment = all_models.Assessment.query.get(self.assessment_id)

  # pylint: disable=invalid-name
  def test_updated_at_changes_after_comment(self):
    """Test updated_at date is changed after adding a comment to assessment"""
    with freezegun.freeze_time("2016-04-01 18:22:09"):
      self.generator.generate_comment(
          self.assessment,
          "Verifier",
          "some comment",
          send_notification="true"
      )

      asmt = all_models.Assessment.query.get(self.assessment.id)
      self.assertEqual(asmt.updated_at,
                       datetime.datetime(2016, 4, 1, 18, 22, 9))

  def test_update_assessment_and_get_list(self):
    """Test get value for assessment cached value after update."""
    old_state = "In Progress"
    all_models.Assessment.query.filter(
        all_models.Assessment.id == self.assessment_id
    ).update({
        all_models.Assessment.status: old_state,
    })
    db.session.commit()
    # required for populate cache
    content = self.api.client.get(
        "/api/assessments?id__in={}".format(self.assessment_id)
    )
    self.assertEqual(
        old_state,
        content.json['assessments_collection']['assessments'][0]['status']
    )
    new_state = "Ready for Review"
    self.api.put(all_models.Assessment.query.get(self.assessment_id),
                 {"status": new_state})
    content = self.api.client.get(
        "/api/assessments?id__in={}".format(self.assessment_id)
    )
    self.assertEqual(
        new_state,
        content.json['assessments_collection']['assessments'][0]['status']
    )


@ddt.ddt
class TestAssessmentGeneration(ggrc.TestCase):
  """Test assessment generation"""
  # pylint: disable=invalid-name

  def setUp(self):
    super(TestAssessmentGeneration, self).setUp()
    self.api = ggrc.api_helper.Api()
    with factories.single_commit():
      self.audit = factories.AuditFactory()
      self.control = factories.ControlFactory(test_plan="Control Test Plan")
      self.snapshot = self._create_snapshots(self.audit, [self.control])[0]

  def assessment_post(self, template=None, extra_data=None):
    """Helper function to POST an assessment"""
    assessment_dict = {
        "_generated": True,
        "audit": {
            "id": self.audit.id,
            "type": "Audit"
        },
        "object": {
            "id": self.snapshot.id,
            "type": "Snapshot"
        },
        "context": {
            "id": self.audit.context.id,
            "type": "Context"
        },
        "title": "Temp title"
    }
    if template:
      assessment_dict["template"] = {
          "id": template.id,
          "type": "AssessmentTemplate"
      }
    if extra_data:
      assessment_dict.update(extra_data)

    return self.api.post(all_models.Assessment, {
        "assessment": assessment_dict
    })

  def test_autogenerated_title(self):
    """Test autogenerated assessment title"""
    control_title = self.control.title
    audit_title = self.audit.title
    response = self.assessment_post()
    title = response.json["assessment"]["title"]
    self.assertIn(audit_title, title)
    self.assertIn(control_title, title)

  def test_autogenerated_assignees_verifiers(self):
    """Test autogenerated assessment assignees"""
    auditor_role = all_models.Role.query.filter_by(name="Auditor").first()

    audit_context = factories.ContextFactory()
    self.audit.context = audit_context

    users = ["user1@example.com", "user2@example.com"]

    auditors = []
    for user in users:
      person = factories.PersonFactory(email=user)
      auditors += [person]

    for auditor in auditors:
      rbac_factories.UserRoleFactory(
          context=audit_context,
          role=auditor_role,
          person=auditor)

    self.assertEqual(
        all_models.UserRole.query.filter_by(
            role=auditor_role,
            context=self.audit.context).count(), 2, "Auditors not present")

    response = self.assessment_post()
    verifiers = response.json["assessment"]["assignees"]["Verifier"]
    verifiers = set([v.get("email") for v in verifiers])
    self.assertEqual(verifiers, set(users))

    assessors = response.json["assessment"]["assignees"]["Assessor"]
    assessor = assessors[0].get("email")
    db.session.add(self.audit)
    self.assertEqual(assessor, self.audit.contact.email)

    creators = response.json["assessment"]["assignees"]["Creator"]
    creators = set([c.get("email") for c in creators])
    self.assertEqual(set(creators), {"user@example.com"})

  def test_template_test_plan(self):
    """Test if generating assessments from template sets default test plan"""
    template = factories.AssessmentTemplateFactory(
        test_plan_procedure=False,
        procedure_description="Assessment Template Test Plan"
    )
    response = self.assessment_post(template)
    self.assertEqual(response.json["assessment"]["test_plan"],
                     template.procedure_description)

  def test_control_test_plan(self):
    """Test test_plan from control"""
    test_plan = self.control.test_plan
    template = factories.AssessmentTemplateFactory(
        test_plan_procedure=True
    )
    response = self.assessment_post(template)
    self.assertEqual(response.json["assessment"]["test_plan"],
                     test_plan)

  def test_ca_order(self):
    """Test LCA/GCA order in Assessment"""
    template = factories.AssessmentTemplateFactory(
        test_plan_procedure=False,
        procedure_description="Assessment Template Test Plan"
    )

    custom_attribute_definitions = [
        # Global CAs
        {
            "definition_type": "assessment",
            "title": "rich_test_gca",
            "attribute_type": "Rich Text",
            "multi_choice_options": ""
        },
        {
            "definition_type": "assessment",
            "title": "checkbox1_gca",
            "attribute_type": "Checkbox",
            "multi_choice_options": "test checkbox label"
        },
        # Local CAs
        {
            "definition_type": "assessment_template",
            "definition_id": template.id,
            "title": "test text field",
            "attribute_type": "Text",
            "multi_choice_options": ""
        },
        {
            "definition_type": "assessment_template",
            "definition_id": template.id,
            "title": "test RTF",
            "attribute_type": "Rich Text",
            "multi_choice_options": ""
        },
        {
            "definition_type": "assessment_template",
            "definition_id": template.id,
            "title": "test checkbox",
            "attribute_type": "Checkbox",
            "multi_choice_options": "test checkbox label"
        },
    ]

    for attribute in custom_attribute_definitions:
      factories.CustomAttributeDefinitionFactory(**attribute)
    response = self.assessment_post(template)
    self.assertListEqual(
        [u'test text field', u'test RTF', u'test checkbox', u'rich_test_gca',
         u'checkbox1_gca'],
        [cad['title'] for cad in
         response.json["assessment"]["custom_attribute_definitions"]]
    )

  def assert_assignees(self, role, response, *users):
    self.assertEqual(list(users),
                     [a.get("email") for a in
                      response.json["assessment"]["assignees"].get(role, [])])

  def test_autogenerated_assignees_verifiers_with_model(self):
    """Test autogenerated assessment assignees based on template settings."""
    assessor = "user1@example.com"
    verifier = "user2@example.com"
    with factories.single_commit():
      self.audit.context = factories.ContextFactory()
      auditors = {u: factories.PersonFactory(email=u).id
                  for u in [assessor, verifier]}
      template = factories.AssessmentTemplateFactory(
          test_plan_procedure=False,
          procedure_description="Assessment Template Test Plan",
          default_people={
              "assessors": [auditors[assessor]],
              "verifiers": [auditors[verifier]],
          },
      )

    response = self.assessment_post(template)
    self.assert_assignees("Verifier", response, verifier)
    self.assert_assignees("Assessor", response, assessor)
    self.assert_assignees("Creator", response, "user@example.com")

  @ddt.data(
      ("Principal Assignees", None, ),
      ("Principal Assignees", "Principal Assignees", ),
      ("Principal Assignees", "Secondary Assignees", ),
      ("Principal Assignees", "Primary Contacts", ),
      ("Principal Assignees", "Secondary Contacts", ),

      ("Secondary Assignees", None, ),
      ("Secondary Assignees", "Principal Assignees", ),
      ("Secondary Assignees", "Secondary Assignees", ),
      ("Secondary Assignees", "Primary Contacts", ),
      ("Secondary Assignees", "Secondary Contacts", ),

      ("Primary Contacts", None, ),
      ("Primary Contacts", "Principal Assignees", ),
      ("Primary Contacts", "Secondary Assignees", ),
      ("Primary Contacts", "Primary Contacts", ),
      ("Primary Contacts", "Secondary Contacts", ),

      ("Secondary Contacts", None, ),
      ("Secondary Contacts", "Principal Assignees", ),
      ("Secondary Contacts", "Secondary Assignees", ),
      ("Secondary Contacts", "Primary Contacts", ),
      ("Secondary Contacts", "Secondary Contacts", ),
  )
  @ddt.unpack
  def test_autogenerated_assignees_base_on_role(self,
                                                assessor_role,
                                                verifier_role):
    """Test autogenerated assessment assignees base on template settings."""
    assessor = "user1@example.com"
    verifier = "user2@example.com"
    auditors = collections.defaultdict(list)
    with factories.single_commit():
      self.audit.context = factories.ContextFactory()
      auditors[assessor_role].append(factories.PersonFactory(email=assessor))
      if verifier_role is not None:
        auditors[verifier_role].append(factories.PersonFactory(email=verifier))
      for role, people in auditors.iteritems():
        ac_role = all_models.AccessControlRole.query.filter_by(
            name=role,
            object_type=self.snapshot.child_type,
        ).first()
        if not ac_role:
          ac_role = factories.AccessControlRoleFactory(
              name=role,
              object_type=self.snapshot.child_type,
          )
        ac_role_id = ac_role.id
        for user in people:
          factories.AccessControlListFactory(
              person_id=user.id,
              object_id=self.snapshot.child_id,
              object_type=self.snapshot.child_type,
              ac_role_id=ac_role_id,
          )
      default_people = {"assessors": assessor_role}
      if verifier_role is not None:
        default_people["verifiers"] = verifier_role
      template = factories.AssessmentTemplateFactory(
          test_plan_procedure=False,
          procedure_description="Assessment Template Test Plan",
          default_people=default_people
      )
      self.snapshot.revision.content = self.control.log_json()
      db.session.add(self.snapshot.revision)
    response = self.assessment_post(template)
    if assessor_role == verifier_role:
      self.assert_assignees("Verifier", response, assessor, verifier)
      self.assert_assignees("Assessor", response, assessor, verifier)
    elif verifier_role is None:
      self.assert_assignees("Verifier", response)
      self.assert_assignees("Assessor", response, assessor)
    else:
      self.assert_assignees("Verifier", response, verifier)
      self.assert_assignees("Assessor", response, assessor)
    self.assert_assignees("Creator", response, "user@example.com")

  @ddt.data(True, False)
  def test_autogenerated_audit_lead(self, add_verifier):
    """Test autogenerated assessment with audit lead settings."""
    email = "user_1@example.com"
    with factories.single_commit():
      default_people = {"assessors": "Audit Lead"}
      if add_verifier:
        default_people["verifiers"] = "Audit Lead"
      template = factories.AssessmentTemplateFactory(
          test_plan_procedure=False,
          procedure_description="Assessment Template Test Plan",
          default_people=default_people
      )
      self.audit.contact = factories.PersonFactory(email=email)
      db.session.add(self.audit)
    response = self.assessment_post(template)
    self.assert_assignees("Assessor", response, email)
    if add_verifier:
      self.assert_assignees("Verifier", response, email)
    else:
      self.assert_assignees("Verifier", response)
    self.assert_assignees("Creator", response, "user@example.com")

  @ddt.data(True, False)
  def test_autogenerated_object_owner(self, add_verifier):
    """Test autogenerated assessment with object owner settings."""
    email = "user_1@example.com"
    with factories.single_commit():
      default_people = {"assessors": "Object Owners"}
      if add_verifier:
        default_people["verifiers"] = "Object Owners"
      template = factories.AssessmentTemplateFactory(
          test_plan_procedure=False,
          procedure_description="Assessment Template Test Plan",
          default_people=default_people
      )
      self.control.owners = [factories.PersonFactory(email=email)]
      self.snapshot.revision.content = self.control.log_json()
      db.session.add(self.snapshot.revision)
    response = self.assessment_post(template)
    self.assert_assignees("Assessor", response, email)
    if add_verifier:
      self.assert_assignees("Verifier", response, email)
    else:
      self.assert_assignees("Verifier", response)
    self.assert_assignees("Creator", response, "user@example.com")

  @ddt.data(True, False)
  def test_autogenerated_auditors(self, add_verifier):
    """Test autogenerated assessment with auditor settings."""
    auditor_role = all_models.Role.query.filter_by(name="Auditor").first()

    users = ["user1@example.com", "user2@example.com"]
    with factories.single_commit():
      audit_context = factories.ContextFactory()
      self.audit.context = audit_context
      auditors = [factories.PersonFactory(email=e) for e in users]
      for auditor in auditors:
        rbac_factories.UserRoleFactory(
            context=audit_context,
            role=auditor_role,
            person=auditor)
      default_people = {"assessors": "Auditors"}
      if add_verifier:
        default_people["verifiers"] = "Auditors"
      template = factories.AssessmentTemplateFactory(
          test_plan_procedure=False,
          procedure_description="Assessment Template Test Plan",
          default_people=default_people
      )
    response = self.assessment_post(template)
    self.assert_assignees("Assessor", response, *users)
    if add_verifier:
      self.assert_assignees("Verifier", response, *users)
    else:
      self.assert_assignees("Verifier", response)
    self.assert_assignees("Creator", response, "user@example.com")

  def test_autogenerated_no_tmpl(self):
    """Test autogenerated assessment without template ."""
    auditors = ["user1@example.com", "user2@example.com"]
    prince_assignees = ["user3@example.com", "user4@example.com"]
    people = auditors + prince_assignees
    auditor_role = all_models.Role.query.filter_by(name="Auditor").first()
    with factories.single_commit():
      audit_context = factories.ContextFactory()
      self.audit.context = audit_context
      users = [factories.PersonFactory(email=e) for e in people]
      ac_role_id = factories.AccessControlRoleFactory(
          name="Principal Assignees",
          object_type=self.snapshot.child_type,
      ).id
      for user in users:
        if user.email in auditors:
          rbac_factories.UserRoleFactory(
              context=audit_context,
              role=auditor_role,
              person=user)
        else:
          factories.AccessControlListFactory(
              person_id=user.id,
              object_id=self.snapshot.child_id,
              object_type=self.snapshot.child_type,
              ac_role_id=ac_role_id,
          )
      self.snapshot.revision.content = self.control.log_json()
      db.session.add(self.snapshot.revision)
    response = self.assessment_post()
    self.assert_assignees("Assessor", response, *prince_assignees)
    self.assert_assignees("Verifier", response, *auditors)
    self.assert_assignees("Creator", response, "user@example.com")

  @ddt.data(
      ("Principal Assignees", None, ),
      ("Principal Assignees", "Principal Assignees", ),
      ("Principal Assignees", "Secondary Assignees", ),
      ("Principal Assignees", "Primary Contacts", ),
      ("Principal Assignees", "Secondary Contacts", ),

      ("Secondary Assignees", None, ),
      ("Secondary Assignees", "Principal Assignees", ),
      ("Secondary Assignees", "Secondary Assignees", ),
      ("Secondary Assignees", "Primary Contacts", ),
      ("Secondary Assignees", "Secondary Contacts", ),

      ("Primary Contacts", None, ),
      ("Primary Contacts", "Principal Assignees", ),
      ("Primary Contacts", "Secondary Assignees", ),
      ("Primary Contacts", "Primary Contacts", ),
      ("Primary Contacts", "Secondary Contacts", ),

      ("Secondary Contacts", None, ),
      ("Secondary Contacts", "Principal Assignees", ),
      ("Secondary Contacts", "Secondary Assignees", ),
      ("Secondary Contacts", "Primary Contacts", ),
      ("Secondary Contacts", "Secondary Contacts", ),
  )
  @ddt.unpack
  def test_autogenerated_assignees_base_on_audit(self,
                                                 assessor_role,
                                                 verifier_role):
    """Test autogenerated assessment assignees base on audit setting

    and empty tmpl."""
    assessor = "user1@example.com"
    verifier = "user2@example.com"
    assessor_audit = "auditor@example.com"
    verifier_audit = "verifier@example.com"
    auditors = collections.defaultdict(list)
    auditor_role = all_models.Role.query.filter_by(name="Auditor").first()
    with factories.single_commit():
      self.audit.context = factories.ContextFactory()
      auditors[assessor_role].append(factories.PersonFactory(email=assessor))
      if verifier_role is not None:
        auditors[verifier_role].append(factories.PersonFactory(email=verifier))
      for role in auditors:
        factories.AccessControlRoleFactory(
            name=role,
            object_type=self.snapshot.child_type,
        )
      default_people = {"assessors": assessor_role}
      if verifier_role is not None:
        default_people["verifiers"] = verifier_role
      self.audit.contact = factories.PersonFactory(email=assessor_audit)
      db.session.add(self.audit)
      audit_context = factories.ContextFactory()
      self.audit.context = audit_context
      for email in [verifier_audit]:
        rbac_factories.UserRoleFactory(
            context=audit_context,
            role=auditor_role,
            person=factories.PersonFactory(email=email))
      self.snapshot.revision.content = self.control.log_json()
      db.session.add(self.snapshot.revision)
      template = factories.AssessmentTemplateFactory(
          test_plan_procedure=False,
          procedure_description="Assessment Template Test Plan",
          default_people=default_people
      )
    response = self.assessment_post(template)
    self.assert_assignees("Assessor", response, assessor_audit)
    if verifier_role:
      self.assert_assignees("Verifier", response, verifier_audit)
    else:
      self.assert_assignees("Verifier", response)
    self.assert_assignees("Creator", response, "user@example.com")

  @ddt.data(
      ("principal_assessor", "Principal Assignees"),
      ("secondary_assessor", "Secondary Assignees"),
      ("contact", "Primary Contacts"),
      ("secondary_contact", "Secondary Contacts"),
  )
  @ddt.unpack
  def test_autogenerated_no_acl_in_snapshot(self, field, role_name):
    """Test autogenerated assessment assignees base on template settings

    and no ACL list in snapshot."""
    email = "{}@example.com".format(field)
    with factories.single_commit():
      person = factories.PersonFactory(email=email, name=field)
      factories.AccessControlRoleFactory(
          name=role_name,
          object_type=self.snapshot.child_type,
      )
      template = factories.AssessmentTemplateFactory(
          test_plan_procedure=False,
          procedure_description="Assessment Template Test Plan",
          default_people={"assessors": role_name}
      )
      content = self.control.log_json()
      content.pop("access_control_list")
      content[field] = {"id": person.id}
      self.snapshot.revision.content = content
      db.session.add(self.snapshot.revision)
    response = self.assessment_post(template)
    self.assert_assignees("Assessor", response, email)

  @ddt.data(1, 2, 3, 4)
  def test_remap_doc_from_assessment(self, test_asmt_num):
    """Test mappings saving for assessment"""
    urls = ["url1", "url2"]
    evidences = ["evidence1", "evidence2"]

    with factories.single_commit():
      asmts = {i: factories.AssessmentFactory() for i in range(1, 4)}

    url_str = "\n".join(urls)
    evidences_str = "\n".join(evidences)
    import_data, update_data = [], []
    for num, asmt in asmts.items():
      import_data.append(collections.OrderedDict([
          ("object_type", "Assessment"),
          ("Code", asmt.slug),
          ("Url", url_str),
          ("Evidence", evidences_str),
      ]))
      update_data.append(collections.OrderedDict([
          ("object_type", "Assessment"),
          ("Code", asmt.slug),
          ("Url", "" if num == test_asmt_num else url_str),
          ("Evidence", "" if num == test_asmt_num else evidences_str),
      ]))

    res = self.import_data(*import_data)
    self._check_csv_response(res, {})
    res = self.import_data(*update_data)
    self._check_csv_response(res, {})

    for num, asmt in asmts.items():
      asmt = all_models.Assessment.query.get(asmt.id)
      if num == test_asmt_num:
        self.assertFalse(asmt.document_url)
        self.assertFalse(asmt.document_evidence)
      else:
        self.assertEqual([url.link for url in asmt.document_url], urls)
        self.assertEqual([ev.link for ev in asmt.document_evidence], evidences)

  @ddt.data(
      (None, "Control", "Control"),
      (None, "Objective", "Objective"),
      (None, None, "Control"),
      ("Market", "Objective", "Market"),
      ("Objective", "Control", "Objective"),
      ("Objective", "Objective", "Objective"),
      ("Objective", None, "Objective"),
      ("Invalid Type", "Invalid Type", None),
      (None, "Invalid Type", None),
      ("Invalid Type", None, None),
  )
  @ddt.unpack
  def test_generated_assessment_type(self, templ_type, obj_type, exp_type):
    """Test assessment type for generated assessments"""
    template = None
    if templ_type:
      template = factories.AssessmentTemplateFactory(
          template_object_type=templ_type
      )
    assessment_type = None
    if obj_type:
      assessment_type = {"assessment_type": obj_type}

    response = self.assessment_post(
        template=template,
        extra_data=assessment_type
    )
    if exp_type:
      self.assertEqual(response.status_code, 201)
      assessment = all_models.Assessment.query.first()
      self.assertEqual(assessment.assessment_type, exp_type)
    else:
      self.assertEqual(response.status_code, 400)
