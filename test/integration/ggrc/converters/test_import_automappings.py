# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

from integration.ggrc import TestCase
from integration.ggrc.generator import ObjectGenerator


class TestBasicCsvImport(TestCase):

  def setUp(self):
    super(TestBasicCsvImport, self).setUp()
    self.generator = ObjectGenerator()
    self.client.get("/login")

  def test_basic_automappings(self):
    filename = "automappings.csv"
    response = self.import_file(filename)
    data = [{
        "object_name": "Program",
        "filters": {
            "expression": {
                "left": "title",
                "op": {"name": "="},
                "right": "program 1",
            },
        },
        "fields": "all",
    }]
    response = self.export_csv(data)
    for i in range(1, 8):
      self.assertIn("reg-{}".format(i), response.data)
      self.assertIn("control-{}".format(i), response.data)
