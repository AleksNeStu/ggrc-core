# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Base test case for all ggrc integration tests."""

import json
import logging
from collections import defaultdict
from os.path import abspath
from os.path import dirname
from os.path import join

from sqlalchemy import exc
from flask.ext.testing import TestCase as BaseTestCase

from ggrc import db
from ggrc.app import app
from integration.ggrc.api_helper import Api

# Hide errors during testing. Errors are still displayed after all tests are
# done. This is for the bad request error messages while testing the api calls.
logging.disable(logging.CRITICAL)


THIS_ABS_PATH = abspath(dirname(__file__))


class SetEncoder(json.JSONEncoder):
  # pylint: disable=method-hidden
  # false positive: https://github.com/PyCQA/pylint/issues/414

  def default(self, obj):
    if isinstance(obj, set):
      return sorted(obj)
    return super(SetEncoder, self).default(obj)


class TestCase(BaseTestCase, object):
  # because it's required by unittests.

  """Base test case for all ggrc integration tests."""

  CSV_DIR = join(THIS_ABS_PATH, "test_csvs/")

  maxDiff = None

  @classmethod
  def clear_data(cls):
    """Remove data from ggrc tables.

    This is a helper function to remove any data that might have been generated
    during a test. The ignored tables are the ones that don't exist or have
    constant data in them, that was populated with migrations.

    This function is used to speed up resetting of the database for each test.
    the proper way would be to run all migrations on a fresh database, but that
    would take too much time. This function should act as if the database was
    just created, with the exception of autoincrement indexes.

    Note:
      The deletion is a hack because db.metadata.sorted_tables does not sort by
      dependencies. The events table is given before Person table and reversed
      order in then incorrect.
    """
    ignore_tables = (
        "categories",
        "notification_types",
        "object_types",
        "options",
        "relationship_test_mock_model",
        "roles",
        "test_model",
        "contexts",
        "people",
    )
    tables = set(db.metadata.tables).difference(ignore_tables)
    for _ in range(len(tables)):
      if len(tables) == 0:
        break  # stop the loop once all tables have been deleted
      for table in reversed(db.metadata.sorted_tables):
        if table.name in tables:
          try:
            db.engine.execute(table.delete())
            tables.remove(table.name)
          except exc.IntegrityError:
            pass
    contexts = db.metadata.tables["contexts"]
    db.engine.execute(contexts.delete(contexts.c.id > 1))
    people = db.metadata.tables["people"]
    db.engine.execute(people.delete(people.c.email != "user@example.com"))
    db.session.commit()

  def setUp(self):
    self.clear_data()

  def tearDown(self):  # pylint: disable=no-self-use
    db.session.remove()

  @staticmethod
  def create_app():
    """Flask specific function for running an app instance."""
    app.config["SERVER_NAME"] = "localhost"
    app.testing = True
    app.debug = False
    return app

  def _check_csv_response(self, response, expected_messages):
    """Test that response contains all expected errors and warnigs.

    Args:
      response: api response object.
      expected_messages: dict of all expected errors by object type.

    Raises:
      AssertionError if an expected error or warning is not found in the
        proper response block.
    """

    messages = ("block_errors", "block_warnings", "row_errors", "row_warnings")
    counts = ("created", "updated", "rows")

    responses = defaultdict(lambda: defaultdict(set))

    # Set default empty sets for non existing error messages in blocks
    for block in response:
      for message in messages:
        error_block = expected_messages.get(block["name"], {})
        error_block[message] = error_block.get(message, set())
        expected_messages[block["name"]] = error_block

    for block in response:
      for message in messages:
        if message in expected_messages.get(block["name"], {}):
          responses[block["name"]][message] = \
              responses[block["name"]][message].union(set(block[message]))
      for count in counts:
        if count in expected_messages.get(block["name"], {}):
          responses[block["name"]][count] = \
              responses[block["name"]].get(count, 0) + int(block[count])

    response_str = json.dumps(responses, indent=4, sort_keys=True,
                              cls=SetEncoder)
    expected_str = json.dumps(expected_messages, indent=4, sort_keys=True,
                              cls=SetEncoder)

    self.assertEqual(responses, expected_messages,
                     "Expected response does not match received response:\n\n"
                     "EXPECTED:\n{}\n\nRECEIVED:\n{}".format(
                         expected_str, response_str))

  @classmethod
  def _import_file(cls, filename, dry_run=False, person=None):
    data = {"file": (open(join(cls.CSV_DIR, filename)), filename)}
    headers = {
        "X-test-only": "true" if dry_run else "false",
        "X-requested-by": "GGRC",
    }
    api = Api()
    api.set_user(person)  # Ok if person is None
    response = api.tc.post("/_service/import_csv", data=data, headers=headers)

    return json.loads(response.data)

  def import_file(self, filename, dry_run=False, person=None):
    if dry_run:
      return self._import_file(filename, dry_run=True, person=person)
    else:
      response_dry = self._import_file(filename, dry_run=True, person=person)
      response = self._import_file(filename, person=person)
      self.assertEqual(response_dry, response)
      return response

  def export_csv(self, data):
    headers = {
        'Content-Type': 'application/json',
        "X-requested-by": "GGRC",
        "X-export-view": "blocks",
    }
    return self.client.post("/_service/export_csv", data=json.dumps(data),
                            headers=headers)
