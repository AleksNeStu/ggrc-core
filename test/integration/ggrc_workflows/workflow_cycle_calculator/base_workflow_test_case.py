# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

import random
from integration.ggrc import TestCase

import os
from integration.ggrc_workflows import generator as workflow_generator
from integration.ggrc import api_helper
from integration.ggrc import generator


if os.environ.get('TRAVIS', False):
  random.seed(1)  # so we can reproduce the tests if needed


class BaseWorkflowTestCase(TestCase):
  """Base test class for workflow cycle calculator tests."""

  def setUp(self):
    super(BaseWorkflowTestCase, self).setUp()
    self.api = api_helper.Api()
    self.generator = workflow_generator.WorkflowsGenerator()
    self.object_generator = generator.ObjectGenerator()

    self.random_objects = self.object_generator.generate_random_objects()

  def tearDown(self):
    pass
