# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Base test case for all ggrc integration tests."""
from collections import defaultdict
import contextlib
import json
import logging
import os
import tempfile
import csv
from StringIO import StringIO

from sqlalchemy import exc
from sqlalchemy import func
from sqlalchemy.sql.expression import tuple_
from flask.ext.testing import TestCase as BaseTestCase

from ggrc import db
from ggrc.app import app
from ggrc.models import Revision
from integration.ggrc.api_helper import Api
from integration.ggrc.models import factories

# Hide errors during testing. Errors are still displayed after all tests are
# done. This is for the bad request error messages while testing the api calls.
logging.disable(logging.CRITICAL)


THIS_ABS_PATH = os.path.abspath(os.path.dirname(__file__))


class SetEncoder(json.JSONEncoder):
  # pylint: disable=method-hidden
  # false positive: https://github.com/PyCQA/pylint/issues/414

  def default(self, obj):  # pylint: disable=arguments-differ
    if isinstance(obj, set):
      return sorted(obj)
    return super(SetEncoder, self).default(obj)


class TestCase(BaseTestCase, object):
  # because it's required by unittests.

  """Base test case for all ggrc integration tests."""

  CSV_DIR = os.path.join(THIS_ABS_PATH, "test_csvs/")

  model = None

  DEFAULT_DATETIME_FORMATS = [
      "{year}",
      "{year}-{month}",
      "{month}/{year}",
      "{year}-{month}-{day}",
      "{month}/{day}/{year}",
      "{year}-{month}-{day} {hour}",
      "{month}/{day}/{year} {hour}",
      "{year}-{month}-{day} {hour}:{minute}",
      "{month}/{day}/{year} {hour}:{minute}",
      # skip seconds filter (microseconds problem in mysql5.5)
      # "{year}-{month}-{day} {hour}:{minute}:{second}",
      # "{month}/{day}/{year} {hour}:{minute}:{second}",
  ]

  maxDiff = None

  @contextlib.contextmanager
  def custom_headers(self, headers=None):
    """Context manager that allowed to add some custom headers in request."""
    tmp_headers = self._custom_headers.copy()
    self._custom_headers.update(headers or {})
    try:
      yield
    finally:
      self._custom_headers = tmp_headers

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
        # data platform models that are currently populated with a migration
        "namespaces",
        "attribute_definitions",
        "attribute_types",
        "object_types",
        "attribute_templates",
        "object_templates",
        "access_control_roles",
    )
    tables = set(db.metadata.tables).difference(ignore_tables)
    for _ in range(len(tables)):
      if not tables:
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
    acr = db.metadata.tables["access_control_roles"]
    db.engine.execute(acr.delete(~acr.c.non_editable))
    db.session.reindex_set = set()
    db.session.commit()

  def setUp(self):
    self.clear_data()
    self._custom_headers = {}

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
    self.assertNotIn("message", response, str(response))
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
  def import_data(cls, *import_data, **kwargs):
    """generate tmp file in csv directory and import it after that remove file

    import data is dict with required key object_type, other keys are optional

    kwargs:
        dry_run (optional) default False - is import only for dry run
        person (optional) default None - who makes the import
    """
    dry_run = kwargs.get("dry_run", False)
    person = kwargs.get("person")
    with tempfile.NamedTemporaryFile(dir=cls.CSV_DIR, suffix=".csv") as tmp:
      for data in import_data:
        tmp.write('Object type,\n')
        data = data.copy()
        object_type = data.pop("object_type")
        keys = data.keys()
        tmp.write('{0},{1}\n'.format(object_type, ','.join(keys)))
        line = ','.join(u"\"{}\"".format(data[k]) for k in keys)
        tmp.write(',{0}\n'.format(line))
        tmp.write(',\n')
      tmp.seek(0)
      return cls._import_file(os.path.basename(tmp.name), dry_run, person)

  @classmethod
  def _import_file(cls, filename, dry_run=False, person=None):
    """Function that handle sending file to import_csv service"""
    data = {"file": (open(os.path.join(cls.CSV_DIR, filename)), filename)}
    headers = {
        "X-test-only": "true" if dry_run else "false",
        "X-requested-by": "GGRC",
    }
    api = Api()
    api.set_user(person)  # Ok if person is None
    response = api.client.post("/_service/import_csv",
                               data=data, headers=headers)
    return json.loads(response.data)

  def import_file(self, filename, dry_run=False, person=None):
    """Import a csv file as a specific user."""
    if dry_run:
      return self._import_file(filename, dry_run=True, person=person)

    response_dry = self._import_file(filename, dry_run=True, person=person)
    response = self._import_file(filename, person=person)
    self.assertEqual(response_dry, response)
    return response

  def export_csv(self, data):
    """Export csv handle

    return post action response to export_csv service with data argument as
    sended data
    """
    headers = {
        'Content-Type': 'application/json',
        "X-requested-by": "GGRC",
        "X-export-view": "blocks",
    }
    headers.update(self._custom_headers)
    return self.client.post("/_service/export_csv", data=json.dumps(data),
                            headers=headers)

  def export_parsed_csv(self, data):
    """returns the dict of list of dict

    keys are humanreadable model name

    values are list of dicts
        keys of that dicts are the exportable field names
        values are the values of this field for current instance
    """
    resp = self.export_csv(data)
    self.assert200(resp)
    rows = csv.reader(StringIO(resp.data))

    object_type = None
    keys = []
    results = defaultdict(list)
    for columns in rows:
      if not any(columns):
        continue
      if columns[0] == "Object type":
        # new block started
        object_type = None
        keys = []
        continue
      if object_type is None:
        keys = columns[1:]
        object_type = columns[0]
        continue
      columns = [unicode(val) for val in columns]
      results[object_type].append(dict(zip(keys, columns[1:])))
    return results

  def assert_slugs(self, field, value, slugs, operator=None):
    """Assert slugs for selected search"""
    assert self.model
    search_request = [{
        "object_name": self.model.__name__,
        "filters": {
            "expression": {
                "left": field,
                "op": {"name": operator or "="},
                "right": value,
            },
        },
        "fields": ["slug"],
    }]
    parsed_data = self.export_parsed_csv(
        search_request
    )[self.model._inflector.title_singular.title()]
    self.assertEqual(sorted(slugs),
                     sorted([i["Code*"] for i in parsed_data]))

  def generate_date_strings(self, datetime_value, formats=None):
    """Generator datestrings

    returns datestrings for sent formats
    if it's empty returns datestrings for DEFAULT_DATETIME_FORMATS"""

    parts = ["year", "month", "day", "hour", "minute", "second"]
    kwargs = {i: getattr(datetime_value, i) for i in parts}
    formats = formats if formats is not None else self.DEFAULT_DATETIME_FORMATS
    for f_string in formats:
      yield f_string.format(**kwargs)

  # pylint: disable=too-many-arguments
  def assert_filter_by_datetime(self, alias, datetime_value, slugs,
                                formats=None, operator=None):
    """Assert slugs for each date format ent datetime"""
    for date_string in self.generate_date_strings(datetime_value, formats):
      self.assert_slugs(alias, date_string, slugs, operator)

  @staticmethod
  def _get_latest_object_revisions(objects):
    """Get latest revisions of given objects."""
    object_tuples = [(o.id, o.type) for o in objects]
    revisions = Revision.query.filter(
        Revision.id.in_(
            db.session.query(func.max(Revision.id)).filter(
                tuple_(
                    Revision.resource_id,
                    Revision.resource_type,
                ).in_(object_tuples)
            ).group_by(
                Revision.resource_type,
                Revision.resource_id,
            )
        )
    )
    return revisions

  def _create_snapshots(self, audit, *objects):
    """Create snapshots of latest object revisions for given objects."""
    # This commit is needed if we're using factories with single_commit, so
    # that the latest revisions will be fetched properly.
    db.session.commit()
    revisions = self._get_latest_object_revisions(objects)
    snapshots = [
        factories.SnapshotFactory(
            child_id=revision.resource_id,
            child_type=revision.resource_type,
            revision=revision,
            parent=audit,
        )
        for revision in revisions
    ]
    return snapshots

  def assert_roles(self, obj, **roles):
    """Assert if persons have required role for object"""
    acl_person_roles = [
        (acl.ac_role.name, acl.person) for acl in obj.access_control_list
    ]
    for role, person in roles.items():
      self.assertTrue((role, person) in acl_person_roles)
