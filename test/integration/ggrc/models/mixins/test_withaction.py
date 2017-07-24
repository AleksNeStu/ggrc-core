# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Integration test for WithAction mixin"""

import copy

from ggrc.models import all_models

from integration.ggrc import api_helper

from integration.ggrc import TestCase
from integration.ggrc.generator import ObjectGenerator
from integration.ggrc.models import factories
from integration.ggrc.query_helper import WithQueryApi


class TestDocumentWithActionMixin(TestCase, WithQueryApi):
  """Test case for WithAction mixin and Document actions."""

  def setUp(self):
    super(TestDocumentWithActionMixin, self).setUp()
    self.client.get("/login")
    self.api = api_helper.Api()

  def test_add_url(self):
    """Test add url action."""
    assessment = factories.AssessmentFactory()
    context = factories.ContextFactory(related_object=assessment)
    assessment.context = context
    response = self.api.put(assessment, {"actions": {"add_related": [
        {
            "id": None,
            "type": "Document",
            "link": "google.com",
            "title": "google.com",
            "document_type": all_models.Document.URL
        }
    ]}})
    self.assert200(response)

    rel_id = response.json["assessment"]["related_destinations"][0]["id"]
    relationship = all_models.Relationship.query.get(rel_id)
    self.assertIsNotNone(relationship)
    document = all_models.Document.query.get(relationship.destination_id)
    self.assertEqual(document.link, "google.com")
    self.assertEqual(document.document_type, all_models.Document.URL)
    self.assertEqual(document.context_id, assessment.context_id)

  def test_map_document(self):
    """Test map document action """
    assessment = factories.AssessmentFactory()
    document = factories.DocumentFactory()
    response = self.api.put(assessment, {"actions": {"add_related": [
        {
            "id": document.id,
            "type": "Document"
        }
    ]}})
    self.assert200(response)

    rel_id = response.json["assessment"]["related_destinations"][0]["id"]
    relationship = all_models.Relationship.query.get(rel_id)
    self.assertEqual(relationship.destination_id, document.id)
    self.assertEqual(relationship.source_id, assessment.id)

  def test_wrong_add_url(self):
    """Test wrong add url action."""
    assessment = factories.AssessmentFactory()
    wrong_params = {
        "id": None,
        "type": "Document"
    }
    response = self.api.put(assessment, {"actions": {"add_related": [
        wrong_params
    ]}})
    self.assert400(response)

    wrong_params["document_type"] = "URL"
    response = self.api.put(assessment, {"actions": {"add_related": [
        wrong_params
    ]}})
    self.assert400(response)

    wrong_params["link"] = "google.com"
    response = self.api.put(assessment, {"actions": {"add_related": [
        wrong_params
    ]}})
    self.assert400(response)

  def test_wrong_add_action(self):
    """Test wrong add action."""
    assessment = factories.AssessmentFactory()
    response = self.api.put(assessment, {"actions": {"add_related": []}})
    self.assert400(response)

    response = self.api.put(assessment, {"actions": {"add_related": [{}]}})
    self.assert400(response)

    response = self.api.put(assessment, {"actions": {"add_related": [
        {
            "type": "Document"
        }
    ]}})
    self.assert400(response)

    response = self.api.put(assessment, {"actions": {"add_related": [
        {
            "id": None
        }
    ]}})
    self.assert400(response)

  def test_unmap_document(self):
    """Test unmap document action."""
    assessment = factories.AssessmentFactory()
    document = factories.DocumentFactory()
    rel_id = factories.RelationshipFactory(source=assessment,
                                           destination=document).id
    response = self.api.put(assessment, {"actions": {"remove_related": [
        {
            "id": document.id,
            "type": "Document"
        }
    ]}})
    self.assert200(response)
    relationship = all_models.Relationship.query.get(rel_id)
    self.assertIsNone(relationship)

  def test_unmap_document2(self):
    """Test unmap document action."""
    assessment = factories.AssessmentFactory()
    document = factories.DocumentFactory()
    rel_id = factories.RelationshipFactory(destination=assessment,
                                           source=document).id
    response = self.api.put(assessment, {"actions": {"remove_related": [
        {
            "id": document.id,
            "type": "Document"
        }
    ]}})
    self.assert200(response)
    relationship = all_models.Relationship.query.get(rel_id)
    self.assertIsNone(relationship)

  def test_wrong_remove_action(self):
    """Test wrong remove action."""
    assessment = factories.AssessmentFactory()
    document_id = factories.DocumentFactory().id

    response = self.api.put(assessment, {"actions": {"remove_related": []}})
    self.assert400(response)

    response = self.api.put(assessment, {"actions": {"remove_related": [{}]}})
    self.assert400(response)

    response = self.api.put(assessment, {"actions": {"remove_related": [
        {
            "id": document_id
        }
    ]}})
    self.assert400(response)

    response = self.api.put(assessment, {"actions": {"remove_related": [
        {
            "type": "Document"
        }
    ]}})
    self.assert400(response)

    response = self.api.put(assessment, {"actions": {"remove_related": [
        {
            "id": None,
            "type": "Document"
        }
    ]}})
    self.assert400(response)

  def test_unmap_nonexistent_url(self):
    """Test unmap nonexistent url action."""
    assessment = factories.AssessmentFactory()
    response = self.api.put(assessment, {"actions": {"remove_related": [
        {
            "id": 0,
            "type": "Document"
        }
    ]}})
    self.assert400(response)

  def test_wrong_unmap_url(self):
    """Test wrong unmap url action."""
    assessment = factories.AssessmentFactory()
    response = self.api.put(assessment, {"actions": {"remove_related": [
        {
            "type": "Document"
        }
    ]}})
    self.assert400(response)

  def test_add_evidence(self):
    """Test add evidence action."""
    assessment = factories.AssessmentFactory()
    response = self.api.put(assessment, {"actions": {"add_related": [
        {
            "id": None,
            "type": "Document",
            "document_type": "EVIDENCE",
            "title": "evidence1",
            "link": "google.com"

        }
    ]}})
    self.assert200(response)

    rel_id = response.json["assessment"]["related_destinations"][0]["id"]
    relationship = all_models.Relationship.query.get(rel_id)
    self.assertIsNotNone(relationship)
    document = all_models.Document.query.get(relationship.destination_id)
    self.assertEqual(document.link, "google.com")
    self.assertEqual(document.title, "evidence1")
    self.assertEqual(document.document_type, all_models.Document.ATTACHMENT)

  def test_wrong_add_evidence(self):
    """Test wrong add evidence action."""
    assessment = factories.AssessmentFactory()
    proper_values = {
        "id": None,
        "type": "Document",
        "document_type": "EVIDENCE",
        "title": "evidence1",
        "link": "google.com"
    }

    wrong_values = copy.copy(proper_values)
    del wrong_values["title"]
    response = self.api.put(assessment, {"actions": {"add_related":
                                         [wrong_values]}})
    self.assert400(response)

    wrong_values = copy.copy(proper_values)
    del wrong_values["link"]
    response = self.api.put(assessment, {"actions": {"add_related":
                                         [wrong_values]}})
    self.assert400(response)

    wrong_values = copy.copy(proper_values)
    wrong_values["document_type"] = "EVDNCE"
    response = self.api.put(assessment, {"actions": {"add_related":
                                         [wrong_values]}})
    self.assert400(response)

  def test_status_change_document(self):
    """Test auto status change after add document action"""
    assessment = factories.AssessmentFactory(
        status=all_models.Assessment.FINAL_STATE)
    response = self.api.put(assessment, {"actions": {"add_related": [
        {
            "id": None,
            "type": "Document",
            "link": "google.com",
            "title": "google.com",
            "document_type": "URL"
        }
    ]}})
    self.assert200(response)
    self.assertEqual(response.json["assessment"]["status"],
                     all_models.Assessment.PROGRESS_STATE)

  def test_put_without_actions(self):
    """Test assessment put without actions"""
    assessment = factories.AssessmentFactory()
    response = self.api.put(assessment, {"description": "test"})
    self.assert200(response)

  def test_document_indexing(self):
    """Test document_indexing"""
    assessment = factories.AssessmentFactory()
    response = self.api.put(assessment, {"actions": {"add_related": [
        {
            "id": None,
            "type": "Document",
            "link": "google.com",
            "title": "google.com",
            "document_type": "URL"
        }
    ]}})
    self.assert200(response)

    assessments_by_url = self.simple_query(
        "Assessment",
        expression=["url", "~", "google.com"]
    )
    self.assertEqual(len(assessments_by_url), 1)

    rel_id = response.json["assessment"]["related_destinations"][0]["id"]
    relationship = all_models.Relationship.query.get(rel_id)

    response = self.api.put(assessment, {"actions": {"remove_related": [
        {
            "id": relationship.destination_id,
            "type": "Document",
        }
    ]}})

    self.assert200(response)

    assessments_by_url = self.simple_query(
        "Assessment",
        expression=["url", "~", "google.com"]
    )
    self.assertFalse(assessments_by_url)


class TestCommentWithActionMixin(TestCase):
  """Test case for WithAction mixin and Comment actions."""

  def setUp(self):
    super(TestCommentWithActionMixin, self).setUp()
    self.client.get("/login")
    self.api = api_helper.Api()

  def test_add_comment(self):
    """Test add comment action."""
    generator = ObjectGenerator()

    _, reader = generator.generate_person(user_role="Reader")
    self.api.set_user(reader)

    assessment = factories.AssessmentFactory()
    context = factories.ContextFactory(related_object=assessment)
    assessment.context = context

    object_person_rel = factories.RelationshipFactory(
        source=assessment,
        destination=reader
    )
    factories.RelationshipAttrFactory(
        relationship_id=object_person_rel.id,
        attr_name="AssigneeType",
        attr_value="Creator,Assessor"
    )

    response = self.api.put(assessment, {"actions": {"add_related": [
        {
            "id": None,
            "type": "Comment",
            "description": "comment",
            "custom_attribute_definition_id": None
        }
    ]}})
    self.assert200(response)
    rel_id = response.json["assessment"]["related_destinations"][0]["id"]
    relationship = all_models.Relationship.query.get(rel_id)
    self.assertIsNotNone(relationship)
    comment = all_models.Comment.query.get(relationship.destination_id)
    self.assertEqual(comment.description, "comment")
    self.assertEqual(comment.assignee_type, "Creator,Assessor")
    self.assertEqual(comment.context_id, assessment.context_id)

  def test_add_custom_comment(self):
    """Test add custom attribute comment action."""
    assessment = factories.AssessmentFactory()
    ca_def = factories.CustomAttributeDefinitionFactory(
        title="def1",
        definition_type="assessment",
        attribute_type="Dropdown",
        multi_choice_options="no,yes"
    )
    response = self.api.put(assessment, {"actions": {"add_related": [
        {
            "id": None,
            "type": "Comment",
            "description": "comment",
            "custom_attribute_definition_id": ca_def.id
        }
    ]}})
    self.assert200(response)
    rel_id = response.json["assessment"]["related_destinations"][0]["id"]
    relationship = all_models.Relationship.query.get(rel_id)
    self.assertIsNotNone(relationship)
    comment = all_models.Comment.query.get(relationship.destination_id)
    self.assertEqual(comment.description, "comment")
    self.assertEqual(comment.custom_attribute_definition_id, ca_def.id)

  def test_wrong_add_comment(self):
    """Test add comment action."""
    assessment = factories.AssessmentFactory()
    response = self.api.put(assessment, {"actions": {"add_related": [
        {
            "id": None,
            "type": "Comment"
        }
    ]}})
    self.assert400(response)

  def test_remove_comment(self):
    """Test remove comment action."""
    assessment = factories.AssessmentFactory()
    comment = factories.CommentFactory(description="123")
    rel_id = factories.RelationshipFactory(source=assessment,
                                           destination=comment).id
    response = self.api.put(assessment, {"actions": {"remove_related": [
        {
            "id": comment.id,
            "type": "Comment"
        }
    ]}})
    self.assert200(response)
    relationship = all_models.Relationship.query.get(rel_id)
    self.assertIsNone(relationship)

  def test_status_unchanged(self):
    """Test auto status isn't change after add comment action"""
    assessment = factories.AssessmentFactory()
    comment = factories.CommentFactory()
    response = self.api.put(assessment, {"actions": {"add_related": [
        {
            "id": comment.id,
            "type": "Comment"
        }
    ]}})
    self.assert200(response)
    self.assertEqual(response.json["assessment"]["status"],
                     all_models.Assessment.START_STATE)


def _create_snapshot():
  """Create snapshot for test"""
  audit = factories.AuditFactory()
  assessment = factories.AssessmentFactory(audit=audit)
  context = factories.ContextFactory(related_object=assessment)
  assessment.context = context
  factories.RelationshipFactory(source=audit, destination=assessment)
  control = factories.ControlFactory(description='control-9')
  revision = all_models.Revision.query.filter(
      all_models.Revision.resource_id == control.id,
      all_models.Revision.resource_type == control.__class__.__name__
  ).order_by(
      all_models.Revision.id.desc()
  ).first()
  snapshot = factories.SnapshotFactory(
      parent=audit,
      child_id=control.id,
      child_type=control.__class__.__name__,
      revision_id=revision.id
  )
  return assessment, snapshot


class TestSnapshotWithActionMixin(TestCase, WithQueryApi):
  """Test case for WithAction mixin and Snapshot actions."""

  def setUp(self):
    super(TestSnapshotWithActionMixin, self).setUp()
    self.client.get("/login")
    self.api = api_helper.Api()

  def test_add_snapshot(self):
    """Test add snapshot action."""
    assessment, snapshot = _create_snapshot()
    response = self.api.put(assessment, {"actions": {"add_related": [
        {
            "id": snapshot.id,
            "type": "Snapshot"
        }
    ]}})
    self.assert200(response)
    rel_id = response.json["assessment"]["related_destinations"][0]["id"]
    relationship = all_models.Relationship.query.get(rel_id)
    self.assertIsNotNone(relationship)
    self.assertEqual(relationship.destination_id, snapshot.id)
    self.assertEqual(relationship.destination_type, "Snapshot")
    self.assertEqual(relationship.context_id, assessment.context_id)

    audits = self.simple_query('Audit',
                               expression=["description", "~", "'control-9'"])
    self.assertFalse(audits)

  def test_wrong_add_snapshot(self):
    """Test wrong add snapshot action."""
    assessment = factories.AssessmentFactory()
    response = self.api.put(assessment, {"actions": {"add_related": [
        {
            "id": None,
            "type": "Snapshot"
        }
    ]}})
    self.assert400(response)

  def test_remove_snapshot(self):
    """Test remove snapshot action."""
    assessment, snapshot = _create_snapshot()
    rel_id = factories.RelationshipFactory(source=assessment,
                                           destination=snapshot).id
    response = self.api.put(assessment, {"actions": {"remove_related": [
        {
            "id": snapshot.id,
            "type": "Snapshot"
        }
    ]}})
    self.assert200(response)
    snapshot = all_models.Relationship.query.get(rel_id)
    self.assertIsNone(snapshot)

  def test_status_change_snapshot(self):
    """Test auto status change after add snapshot action"""
    assessment, snapshot = _create_snapshot()
    response = self.api.put(assessment, {"actions": {"add_related": [
        {
            "id": snapshot.id,
            "type": "Snapshot"
        }
    ]}})
    self.assert200(response)
    self.assertEqual(response.json["assessment"]["status"],
                     all_models.Assessment.PROGRESS_STATE)
