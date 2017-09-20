# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Tests for Issue model."""
from ggrc import db
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


class TestIssueUnmap(TestCase):
  """Test suite to check the rules for Issue-Audit mappings."""
  def setUp(self):
    """Setup tests data"""
    super(TestIssueUnmap, self).setUp()
    self.generator = generator.ObjectGenerator(fail_no_json=False)

    # TODO: replace this hack with a special test util
    from ggrc.login import noop
    noop.login()  # this is needed to pass the permission checks in automapper

    with factories.single_commit():
      audit = factories.AuditFactory()
      self.audit_id = audit.id
      assessments = [
          factories.AssessmentFactory(audit=audit) for _ in range(2)
      ]

      controls = [factories.ControlFactory() for _ in range(2)]
      snapshots = self._create_snapshots(audit, controls)
      self.snapshot_ids = [s.id for s in snapshots]

      issue = factories.IssueFactory()
      self.issue_id = issue.id

      factories.RelationshipFactory(source=audit, destination=assessments[0])
      factories.RelationshipFactory(source=audit, destination=assessments[1])
      factories.RelationshipFactory(
          source=assessments[0], destination=snapshots[0]
      )
      factories.RelationshipFactory(
          source=assessments[0], destination=snapshots[1]
      )
      factories.RelationshipFactory(
          source=assessments[1], destination=snapshots[1]
      )
      self.unmap_rel_id1 = factories.RelationshipFactory(
          source=issue, destination=assessments[0]
      ).id
      self.unmap_rel_id2 = factories.RelationshipFactory(
          source=issue, destination=assessments[1]
      ).id

  def get_relationships(self, obj1_id, obj1_type, obj2_id, obj2_type):
    """Get relationships between objects"""
    # pylint: disable=no-self-use
    return db.session.query(all_models.Relationship.id).filter_by(
        source_type=obj1_type,
        source_id=obj1_id,
        destination_type=obj2_type,
        destination_id=obj2_id,
    ).union(
        db.session.query(all_models.Relationship.id).filter_by(
            source_type=obj2_type,
            source_id=obj2_id,
            destination_type=obj1_type,
            destination_id=obj1_id,
        )
    )

  def test_issue_cascade_unmap(self):
    """Test cascade unmapping Issue from Assessment"""
    unmap_rel1 = all_models.Relationship.query.get(self.unmap_rel_id1)
    response = self.generator.api.delete(unmap_rel1, {"cascade": "true"})
    self.assert200(response)

    snap0_issue_rel = self.get_relationships(
        self.snapshot_ids[0], "Snapshot", self.issue_id, "Issue"
    )
    self.assertEqual(snap0_issue_rel.count(), 0)
    self.assertEqual(
        all_models.Relationship.query.filter_by(id=self.unmap_rel_id1).count(),
        0
    )
    self.assertEqual(all_models.Relationship.query.count(), 8)

    unmap_rel2 = all_models.Relationship.query.get(self.unmap_rel_id2)
    response = self.generator.api.delete(unmap_rel2, {"cascade": "true"})
    self.assert200(response)

    snap1_issue_rel = self.get_relationships(
        self.snapshot_ids[1], "Snapshot", self.issue_id, "Issue"
    )
    audit_issue_rel = self.get_relationships(
        self.audit_id, "Audit", self.issue_id, "Issue"
    )
    self.assertEqual(snap1_issue_rel.count(), 0)
    self.assertEqual(audit_issue_rel.count(), 0)
    self.assertEqual(
        all_models.Relationship.query.filter_by(id=self.unmap_rel_id2).count(),
        0
    )
    self.assertEqual(all_models.Relationship.query.count(), 5)

  def test_cascade_unmap_automapped(self):
    """Test if cascade unmapping Issue will not work for automapped"""
    # Set all Relationships as manually created
    db.session.query(all_models.Relationship).update({"automapping_id": None})
    db.session.commit()

    unmap_rel1 = all_models.Relationship.query.get(self.unmap_rel_id1)
    response = self.generator.api.delete(unmap_rel1, {"cascade": "true"})
    self.assert200(response)

    unmap_rel2 = all_models.Relationship.query.get(self.unmap_rel_id2)
    response = self.generator.api.delete(unmap_rel2, {"cascade": "true"})
    self.assert200(response)

    # No Issue-Snapshot, no Issue-Audit relationships should be removed
    # as they manually mapped
    snap0_issue_rel = self.get_relationships(
        self.snapshot_ids[0], "Snapshot", self.issue_id, "Issue"
    )
    self.assertEqual(snap0_issue_rel.count(), 1)

    snap1_issue_rel = self.get_relationships(
        self.snapshot_ids[1], "Snapshot", self.issue_id, "Issue"
    )
    self.assertEqual(snap1_issue_rel.count(), 1)

    audit_issue_rel = self.get_relationships(
        self.audit_id, "Audit", self.issue_id, "Issue"
    )
    self.assertEqual(audit_issue_rel.count(), 1)

  def test_cascade_unmap_man_audit(self):
    """Test cascade unmapping Issue from Audit if it manually mapped"""
    audit_issue_rel = self.get_relationships(
        self.audit_id, "Audit", self.issue_id, "Issue"
    )
    all_models.Relationship.query.filter(
        all_models.Relationship.id.in_(audit_issue_rel.subquery())
    ).update({"automapping_id": None}, synchronize_session="fetch")
    db.session.commit()

    unmap_rel1 = all_models.Relationship.query.get(self.unmap_rel_id1)
    response = self.generator.api.delete(unmap_rel1, {"cascade": "true"})
    self.assert200(response)
    # Snapshot is unmapped in cascade as it's automapped
    self.assertEqual(all_models.Relationship.query.count(), 8)

    unmap_rel2 = all_models.Relationship.query.get(self.unmap_rel_id2)
    response = self.generator.api.delete(unmap_rel2, {"cascade": "true"})
    self.assert200(response)

    snap1_issue_rel = self.get_relationships(
        self.snapshot_ids[1], "Snapshot", self.issue_id, "Issue"
    )
    audit_issue_rel = self.get_relationships(
        self.audit_id, "Audit", self.issue_id, "Issue"
    )
    self.assertEqual(snap1_issue_rel.count(), 0)
    # Audit is not removed in cascade as it was manually created
    self.assertEqual(audit_issue_rel.count(), 1)
    self.assertEqual(
        all_models.Relationship.query.filter_by(id=self.unmap_rel_id2).count(),
        0
    )
    self.assertEqual(all_models.Relationship.query.count(), 6)
