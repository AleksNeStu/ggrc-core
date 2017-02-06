# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

from integration.ggrc import TestCase


class TestBasicCsvImport(TestCase):

  def setUp(self):
    super(TestBasicCsvImport, self).setUp()
    self.client.get("/login")

  def test_policy_basic_import(self):
    filename = "ca_setup_for_deletion.csv"
    self.import_file(filename)

    filename = "ca_deletion.csv"
    response_data = self.import_file(filename)

    self.assertEqual(response_data[0]["deleted"], 2)
    self.assertEqual(response_data[0]["ignored"], 0)
