# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

from ggrc.models import Person
from integration.ggrc import TestCase
from integration.ggrc.generator import ObjectGenerator


class TestBasicCsvImport(TestCase):

  def setUp(self):
    super(TestBasicCsvImport, self).setUp()
    self.generator = ObjectGenerator()
    self.client.get("/login")

  def test_people_import(self):
    filename = "people_basic_import.csv"
    self.import_file(filename)
    self.assertEqual(5, Person.query.count())

  def test_people_import_correct_order_dry_run(self):
    filename = "people_import_correct_order.csv"
    response = self.import_file(filename, dry_run=True)
    self.assertEqual(1, Person.query.count())
    self._check_csv_response(response, {})

  def test_people_import_wrong_order_dry_run(self):
    filename = "people_import_wrong_order.csv"
    response = self.import_file(filename, dry_run=True)
    self.assertEqual(1, Person.query.count())
    self._check_csv_response(response, {})

  def test_people_import_correct_order(self):
    filename = "people_import_correct_order.csv"
    response = self.import_file(filename)
    self.assertEqual(5, Person.query.count())
    self._check_csv_response(response, {})

  def test_people_import_wrong_order(self):
    filename = "people_import_wrong_order.csv"
    response = self.import_file(filename)
    self.assertEqual(5, Person.query.count())
    self._check_csv_response(response, {})
