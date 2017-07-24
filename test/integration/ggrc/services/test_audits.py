# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Tests for actions available on audits handle."""

from ggrc.models import Audit
from ggrc.models import Program
from ggrc.models import all_models

from integration.ggrc import generator
from integration.ggrc import TestCase
from integration.ggrc.query_helper import WithQueryApi
from integration.ggrc.models import factories


class TestAuditActions(TestCase, WithQueryApi):
  """Test Audit related actions"""

  def setUp(self):
    self.clear_data()
    super(TestAuditActions, self).setUp()
    self.client.get("/login")
    self.gen = generator.ObjectGenerator()
    filename = "program_audit.csv"
    self.import_file(filename)
    self.assertEqual(2, Audit.query.count())
    audit = Audit.query.filter(Audit.slug == "Aud-1").first()
    program = Program.query.filter(Program.slug == "prog-1").first()
    self.assertEqual(audit.program_id, program.id)

  def test_filter_by_evidence_url(self):
    """Filter by = operator."""
    evidence = "Some title 3"
    audits = self._get_first_result_set(
        self._make_query_dict("Audit", expression=["evidence", "=", evidence]),
        "Audit",
    )
    self.assertEqual(audits["count"], 1)
    self.assertEqual(len(audits["values"]), audits["count"])

  def test_audit_post_put(self):
    """Test create document and map it to audit"""
    data = {
        "link": "test_link",
    }
    doc_type = all_models.Document.URL
    data["document_type"] = doc_type
    resp, doc = self.gen.generate_object(
        all_models.Document,
        data
    )
    self.assertEqual(resp.status_code, 201)
    self.assertTrue(
        all_models.Document.query.filter(
            all_models.Document.id == resp.json["document"]['id'],
            all_models.Document.document_type == doc_type,
        ).all()
    )
    doc = all_models.Document.query.get(doc.id)
    self.assertEqual(doc.link, "test_link")

    audit = Audit.query.filter(Audit.slug == "Aud-1").first()
    data = {
        "source": self.gen.create_stub(audit),
        "destination": self.gen.create_stub(doc),
        "context": self.gen.create_stub(audit.context)
    }
    resp, _ = self.gen.generate_object(
        all_models.Relationship, add_fields=False, data=data)
    self.assertEqual(resp.status_code, 201)

    audits = self._get_first_result_set(
        self._make_query_dict("Audit",
                              expression=["url", "=", "test_link"]),
        "Audit",
    )
    self.assertEqual(audits["count"], 1)

  def test_evidence_create_an_map(self):
    """Test document is created and mapped to audit"""
    audit = factories.AuditFactory(slug="Audit")
    evidence = factories.EvidenceFactory(
        title="evidence",
    )
    factories.RelationshipFactory(
        source=audit,
        destination=evidence,
    )
    self.assertEqual(audit.document_evidence[0].title, "evidence")
