# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Tests for bulk updates with CSV import."""

from integration.ggrc import TestCase

from ggrc import models


class TestImportUpdates(TestCase):

  """ Test importing of already existing objects """

  def setUp(self):
    super(TestImportUpdates, self).setUp()
    self.client.get("/login")

  def test_policy_basic_update(self):
    """ Test simple policy title update """
    filename = "policy_basic_import.csv"
    response = self.import_file(filename)

    self._check_csv_response(response, {})

    policy = models.Policy.query.filter_by(slug="p1").first()
    self.assertEqual(policy.title, "some weird policy")
    revision_count = models.Revision.query.filter(
        models.Revision.resource_type == "Policy",
        models.Revision.resource_id == policy.id
    ).count()
    self.assertEqual(revision_count, 2)

    filename = "policy_basic_import_update.csv"
    response = self.import_file(filename)
    self._check_csv_response(response, {})

    policy = models.Policy.query.filter_by(slug="p1").first()
    self.assertEqual(policy.title, "Edited policy")
    revision_count = models.Revision.query.filter(
        models.Revision.resource_type == "Policy",
        models.Revision.resource_id == policy.id
    ).count()
    self.assertEqual(revision_count, 4)
    self.assertEqual(
        policy.access_control_list[0].person.email,
        "user1@example.com"
    )
