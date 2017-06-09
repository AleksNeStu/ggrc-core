# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Test object owner of comments."""
from ggrc.models import Assessment, AccessControlList, Revision, all_models
from integration.ggrc import TestCase
from integration.ggrc import generator


class TestCommentObjectOwner(TestCase):

  """Test object owner of comments."""

  def setUp(self):
    """Setup test case."""
    super(TestCommentObjectOwner, self).setUp()
    self.response = self.client.get("/login")
    self.generator = generator.ObjectGenerator()

  def test_object_owner(self):
    """Test object owner and its revision of assessment comment."""
    acr_comment_id = all_models.AccessControlRole.query.filter_by(
        object_type="Comment",
        name="Admin"
    ).first().id
    self.import_file("assessment_full_no_warnings.csv")
    asmt1 = Assessment.query.filter_by(slug="Assessment 1").first()
    _, comment = self.generator.generate_comment(
        asmt1, "Verifier", "some comment", send_notification="false")

    acl = AccessControlList.query.filter_by(
        object_id=comment.id,
        object_type=comment.type,
        ac_role_id=acr_comment_id
    ).first()
    self.assertTrue(acl, "ACL row is not created")

    revision = Revision.query.filter_by(
        resource_id=acl.id,
        resource_type=acl.type
    ).first()
    self.assertTrue(revision, "Revision of ACL is not created")
