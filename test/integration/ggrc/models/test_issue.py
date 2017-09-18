# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Tests for Issue model."""
from ggrc.models import all_models
from integration.ggrc import generator
from integration.ggrc import TestCase, Api
from integration.ggrc.models import factories


class TestIssue(TestCase):
  """ Test Issue class. """
  def setUp(self):
    super(TestIssue, self).setUp()
    self.api = Api()
    with factories.single_commit():
      audit = factories.AuditFactory()
      for status in all_models.Issue.VALID_STATES:
        factories.IssueFactory(audit=audit, status=status)

  def test_filter_by_status(self):
    """Test Issue filtering by status."""
    query_request_data = [{
        'fields': [],
        'filters': {
            'expression': {
                'left': {
                    'left': 'status',
                    'op': {'name': '='},
                    'right': 'Fixed'
                },
                'op': {'name': 'OR'},
                'right': {
                    'left': 'status',
                    'op': {'name': '='},
                    'right': 'Fixed and Verified'
                },
            },
        },
        'object_name': 'Issue',
        'permissions': 'read',
        'type': 'values',
    }]
    response = self.api.send_request(
        self.api.client.post,
        data=query_request_data,
        api_link="/query"
    )
    self.assertEqual(response.status_code, 200)

    statuses = {i["status"] for i in response.json[0]["Issue"]["values"]}
    self.assertEqual(statuses, {"Fixed", "Fixed and Verified"})


class TestIssueAuditMapping(TestCase):
  """Test suite to check the rules for Issue-Audit mappings."""
  # pylint: disable=invalid-name

  def setUp(self):
    super(TestIssueAuditMapping, self).setUp()
    self.generator = generator.ObjectGenerator(fail_no_json=False)
    with factories.single_commit():
      self.audit = factories.AuditFactory()
      self.other_audits = [factories.AuditFactory() for _ in range(2)]
      self.issue_mapped = factories.IssueFactory()
      self.issue_unmapped = factories.IssueFactory()
      self.issue_audit_mapping = factories.RelationshipFactory(
          source=self.audit,
          destination=self.issue_mapped,
          context=self.audit.context,
      )

  def test_map_to_audit(self):
    """Issue can be mapped to an Audit."""
    response, _ = self.generator.generate_relationship(
        source=self.audit,
        destination=self.issue_unmapped,
        context=self.audit.context,
    )
    self.assertStatus(response, 201)

  def test_unmap_from_audit(self):
    """Issue can be unmapped from an Audit."""
    response = self.generator.api.delete(self.issue_audit_mapping)
    self.assert200(response)

  def test_populate_audit_and_context(self):
    """Issue mapped to Audit -> Issue audit_id and context_id are set."""
    response, _ = self.generator.generate_relationship(
        source=self.audit,
        destination=self.issue_unmapped,
        context=self.audit.context,
    )
    self.assertStatus(response, 201)

    self.issue_unmapped = self.refresh_object(self.issue_unmapped)
    self.assertEqual(self.issue_unmapped.audit_id, self.audit.id)
    self.assertEqual(self.issue_unmapped.context_id, self.audit.context_id)

  def test_unpopulate_audit_and_context(self):
    """Issue unmapped from Audit -> Issue audit_id and context_id are unset."""
    # workaround to make sure the id is fetched from the db
    id_ = self.issue_mapped.id
    self.generator.api.delete(self.issue_audit_mapping)
    self.issue_mapped = self.refresh_object(self.issue_mapped, id_=id_)
    self.assertIs(self.issue_mapped.audit_id, None)
    self.assertIs(self.issue_mapped.context_id, None)

  def test_post_issue_with_audit_set(self):
    """Issue isn't mapped to Audit by POSTing with audit field."""
    response, issue = self.generator.generate_object(
        all_models.Issue,
        {"audit": {"type": "Audit", "id": self.audit.id}},
    )
    self.assertStatus(response, 201)
    rel = all_models.Relationship
    source_tuple = rel.source_type, rel.source_id
    destination_tuple = rel.destination_type, rel.destination_id
    audit_tuple = "Audit", self.audit.id
    issue_tuple = "Issue", issue.id
    self.assertEqual(rel.query.filter(
        source_tuple == audit_tuple and destination_tuple == issue_tuple or
        destination_tuple == audit_tuple and source_tuple == issue_tuple
    ).count(), 0)

  def test_deny_mapping_to_two_audits(self):
    """Issue can't be mapped to two Audits at once."""
    issue_stub = self.generator.create_stub(self.issue_unmapped)
    audit_stubs = [self.generator.create_stub(a) for a in self.other_audits]

    response, _ = self.generator.generate_relationship(
        source=self.other_audits[0],
        destination=self.issue_mapped,
        context=self.other_audits[0].context,
    )
    self.assert400(response)

    response = self.generator.api.post(
        all_models.Relationship,
        [{"source": issue_stub,
          "destination": audit_stubs[0],
          "context": None},
         {"source": issue_stub,
          "destination": audit_stubs[1],
          "context": None}],
    )
    self.assert400(response)

  def test_deny_unmapping_from_audit_asmt(self):
    """Issue can't be unmapped from Audit if has common Assessment."""
    with factories.single_commit():
      assessment = factories.AssessmentFactory(audit=self.audit)
      factories.RelationshipFactory(source=assessment, destination=self.audit,
                                    context=self.audit.context)
      factories.RelationshipFactory(source=assessment,
                                    destination=self.issue_mapped,
                                    context=self.audit.context)

    response = self.generator.api.delete(self.issue_audit_mapping)
    self.assert400(response)

  def test_deny_unmapping_from_audit_snapshot(self):
    """Issue can't be unmapped from Audit if has common Snapshot."""
    control = factories.ControlFactory()
    revision = all_models.Revision.query.filter(
        all_models.Revision.resource_type == control.type,
        all_models.Revision.resource_id == control.id,
    ).first()
    with factories.single_commit():
      snapshot = factories.SnapshotFactory(parent=self.audit,
                                           revision=revision)
      factories.RelationshipFactory(source=snapshot,
                                    destination=self.issue_mapped,
                                    context=self.audit.context)

    response = self.generator.api.delete(self.issue_audit_mapping)
    self.assert400(response)
