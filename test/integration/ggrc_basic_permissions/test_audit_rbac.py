# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Test audit RBAC"""

from os.path import abspath
from os.path import dirname
from os.path import join
from collections import defaultdict
from integration.ggrc import TestCase
from integration.ggrc.api_helper import Api
from ggrc.models import all_models


class TestAuditRBAC(TestCase):
  """Test audit RBAC"""

  CSV_DIR = join(abspath(dirname(__file__)), "test_csvs")

  @classmethod
  def setUpClass(cls):
    TestCase.clear_data()
    cls._import_file("audit_rbac.csv")
    cls.people = all_models.Person.eager_query().all()
    cls.audit = all_models.Audit.eager_query().first()
    sources = set(r.source for r in cls.audit.related_sources)
    destinations = set(r.destination for r in cls.audit.related_destinations)
    related = [obj for obj in sources.union(destinations)
               if not isinstance(obj, all_models.Person)]
    cls.related_objects = related

  def setUp(self):
    """Imports test_csvs/audit_rbac.csv needed by the tests"""
    self.api = Api()
    self.client.get("/login")
    self.sanity_check()

  def sanity_check(self):
    """Sanity check if the audit_rbac.csv was imported correctly"""
    assert len(self.people) == 17, \
        "Expecting 17 people not {}.".format(len(self.people))
    assert len(self.related_objects) == 11, \
        "Expecting 11 objects mapped to audit not {}."\
        .format(len(self.related_objects))

  def read(self, objects):
    """Attempt to do a GET request for every object in the objects list"""
    responses = []
    for obj in objects:
      status_code = self.api.get(obj.__class__, obj.id).status_code
      responses.append((obj.type, status_code))
    return responses

  def update(self, objects):
    """Attempt to do a PUT request for every object in the objects list"""
    responses = []
    for obj in objects:
      response = self.api.get(obj.__class__, obj.id)
      status_code = response.status_code
      if response.status_code == 200:
        status_code = self.api.put(obj, response.json).status_code
      responses.append((obj.type, status_code))
    return responses

  def call_api(self, method, expected_statuses):
    """Calls the REST api with a given method and returns a list of
       status_codes that do not match the expected_statuses dict"""
    all_errors = []
    for person in self.people:
      self.api.set_user(person)
      responses = method(self.related_objects + [self.audit])
      for type_, code in responses:
        if code != expected_statuses[person.email]:
          all_errors.append("{} does not have {} access to {} ({})".format(
              person.email, method.__name__, type_, code))
    return all_errors

  def test_read_access_on_mapped(self):
    """Test if people have read access to mapped objects.

    All users except creator@test.com should have read access."""
    expected_statuses = defaultdict(lambda: 200)
    for exception in ("creator@test.com",):
      expected_statuses[exception] = 403
    errors = self.call_api(self.read, expected_statuses)
    assert not errors, "\n".join(errors)

  def test_update_access_on_mapped(self):
    """Test if people have upate access to mapped objects.

    All users except creator@test.com, reader@test.com, creatorpr@test.com,
    readerpr@test.com should have update access."""
    expected_statuses = defaultdict(lambda: 200)
    for exception in ("creator@test.com", "reader@test.com",
                      "creatorpr@test.com", "readerpr@test.com"):
      expected_statuses[exception] = 403
    errors = self.call_api(self.update, expected_statuses)
    assert not errors, "\n".join(errors)
