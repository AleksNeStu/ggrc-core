# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

from ggrc.models import Audit
from ggrc.models import Program
from ggrc.models import Person
from ggrc_basic_permissions.models import UserRole
from integration.ggrc import TestCase


class TestSpecialObjects(TestCase):

  """
  testing all object with special columns such as workflows, audits, sections

  """

  def setUp(self):
    super(TestSpecialObjects, self).setUp()
    self.client.get("/login")
    pass

  def tearDown(self):
    pass

  def test_audit_imports(self):
    """ this tests if the audit gets imported with a mapped program """

    filename = "program_audit.csv"
    self.import_file(filename)
    self.assertEqual(2, Audit.query.count())
    audit = Audit.query.filter(Audit.slug == "Aud-1").first()
    program = Program.query.filter(Program.slug == "prog-1").first()
    self.assertEqual(audit.program_id, program.id)

  def test_program_roles_imports(self):
    """ this tests if the audit gets imported with a mapped program """

    filename = "program_audit.csv"
    self.import_file(filename)
    self.assertEqual(2, Program.query.count())
    program = Program.query.filter(Program.slug == "prog-1").first()
    p1_roles = UserRole.query.filter_by(context_id=program.context_id).all()
    self.assertEqual(5, len(p1_roles))
    owner_ids = [r.person_id for r in p1_roles if r.role_id == 1]
    editor_ids = [r.person_id for r in p1_roles if r.role_id == 2]
    reader_ids = [r.person_id for r in p1_roles if r.role_id == 3]
    owner_emails = [p.email for p in
                    Person.query.filter(Person.id.in_(owner_ids)).all()]
    editor_emails = [p.email for p in
                     Person.query.filter(Person.id.in_(editor_ids)).all()]
    reader_emails = [p.email for p in
                     Person.query.filter(Person.id.in_(reader_ids)).all()]
    expected_owners = set(["user1@example.com", "user11@example.com"])
    expected_editors = set(["user11@example.com"])
    expected_readers = set(["user12@example.com", "user2@example.com"])
    self.assertEqual(set(owner_emails), expected_owners)
    self.assertEqual(set(editor_emails), expected_editors)
    self.assertEqual(set(reader_emails), expected_readers)
