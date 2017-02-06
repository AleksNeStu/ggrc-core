# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Check number of db queries per API request.

This is in converters because it depends on import to provide data
"""

import collections

from ggrc.models import all_models
from ggrc.utils import QueryCounter
from ggrc.views import all_object_views
from integration.ggrc_workflows.generator import WorkflowsGenerator

from integration.ggrc import TestCase
from integration.ggrc.generator import ObjectGenerator
from integration.ggrc.models import factories


class TestComprehensiveSheets(TestCase):

  """
  test sheet from:
    https://docs.google.com/spreadsheets/d/1Jg8jum2eQfvR3kZNVYbVKizWIGZXvfqv3yQpo2rIiD8/edit#gid=0

  """

  # skip abstract models since they are not really first class
  WHITELIST = {"Directive", "SystemOrProcess"}
  MODELS = [getattr(all_models, model_name)
            for model_name in all_models.__all__
            if model_name not in WHITELIST]

  # limit found by trial and error, may need tweaking if models change
  LIMIT = 32

  @classmethod
  def setUpClass(cls):
    cls.first_run = True

  def setUp(self):
    self.client.get("/login")
    self.generator = ObjectGenerator()
    if TestComprehensiveSheets.first_run:
      TestComprehensiveSheets.first_run = False
      super(TestComprehensiveSheets, self).setUp()

      self.create_custom_attributes()
      self.import_file("comprehensive_sheet1.csv")

      gen = WorkflowsGenerator()
      wfs = all_models.Workflow.eager_query().filter_by(status='Draft').all()
      for workflow in wfs:
        _, cycle = gen.generate_cycle(workflow)
        self.assertIsNotNone(cycle)

  def tearDown(self):
    pass

  def test_queries_per_api_call(self):
    """Import comprehensive_sheet1 and count db requests per collection get.

    Query count should be <LIMIT for all model types.
    """
    errors = set()
    with QueryCounter() as counter:
      for model in self.MODELS:
        try:
          counter.queries = []
          self.generator.api.get_query(model, "")
          if counter.get > self.LIMIT:
            print collections.Counter(counter.queries).most_common(1)
          self.assertLess(counter.get, self.LIMIT,
                          "Query count for object {} exceeded: {}/{}".format(
                              model.__name__, counter.get, self.LIMIT)
                          )
        except AssertionError as error:
          errors.add(error.message)
    self.assertEqual(errors, set())

  def test_queries_per_object_page(self):
    """Import comprehensive_sheet1 and count db requests per collection get.

    Query count should be <LIMIT for all model types.
    """
    errors = set()
    with QueryCounter() as counter:
      for view in all_object_views():
        try:
          model = view.model_class
          if model not in self.MODELS:
            continue
          instance = model.query.first()
          if instance is None or getattr(instance, "id", None) is None:
            continue
          counter.queries = []
          res = self.client.get("/{}/{}".format(view.url, instance.id))
          self.assertEqual(res.status_code, 200)
          self.assertLess(counter.get, self.LIMIT,
                          "Query count for object {} exceeded: {}/{}".format(
                              model.__name__, counter.get, self.LIMIT)
                          )
        except AssertionError as e:
          errors.add(e.message)
    self.assertEqual(errors, set())

  def test_queries_for_dashboard(self):
    with QueryCounter() as counter:
      res = self.client.get("/dashboard")
      self.assertEqual(res.status_code, 200)
      self.assertLess(counter.get, self.LIMIT, "Query count for dashboard")

  def test_queries_for_permissions(self):
    with QueryCounter() as counter:
      res = self.client.get("/permissions")
      self.assertEqual(res.status_code, 200)
      self.assertLess(counter.get, self.LIMIT, "Query count for permissions")

  def create_custom_attributes(self):
    """Generate custom attributes needed by comprehensive_sheet1.csv."""
    CAD = factories.CustomAttributeDefinitionFactory
    CAD(definition_type="control", title="my custom text", mandatory=True)
    CAD(definition_type="program", title="my_text", mandatory=True)
    CAD(definition_type="program", title="my_date", attribute_type="Date")
    CAD(definition_type="program", title="my_checkbox",
        attribute_type="Checkbox")
    CAD(definition_type="program", title="my_dropdown",
        attribute_type="Dropdown",
        multi_choice_options="a,b,c,d")
