# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Unit test for ggrc.setvice.common module"""

import collections
import itertools
from contextlib import contextmanager
from unittest import TestCase
import mock

from ddt import ddt, data, unpack

# pylint: disable=unused-import
from ggrc import models  # NOQA
from ggrc.services import common


@ddt
class TestGetRevisionsList(TestCase):
  """Class test for get revision actions"""
  FAKE_USER_ID = 123

  def setUp(self):
    self.pool_of_ids = itertools.count()
    self.simple_objs = []
    self.ownable_obj = []

  @property
  def new_simple_object(self):
    return collections.namedtuple(
        "SimpleObject", ["id", "log_json", "type"]
    )(
        next(self.pool_of_ids), lambda: "{}", "simple"
    )

  @property
  def new_ownable_obj(self):
    return collections.namedtuple(
        "OwnableObject",
        ["id", "log_json", "type", "ownable"]
    )(
        next(self.pool_of_ids),
        lambda: "{}",
        "ObjectOwner", self.new_simple_object
    )

  def populate_object_list(self, simple_count, ownable_count=0):
    """returns combine object list of simple and ownable objects"""
    simple_objs = [self.new_simple_object for _ in range(simple_count)]
    ownable_obj = [self.new_ownable_obj for _ in range(ownable_count)]
    self.simple_objs += simple_objs
    self.ownable_obj += ownable_obj
    return simple_objs + ownable_obj

  @staticmethod
  @contextmanager
  def mock_get_cache(new, deleted, dirty):
    with mock.patch.object(common, "get_cache") as mock_get_cache:
      cache_mock = mock_get_cache.return_value
      cache_mock.new = new
      cache_mock.deleted = deleted
      cache_mock.dirty = dirty
      yield cache_mock
      mock_get_cache.assert_called_once_with()

  def get_log_revisions(self, obj=None):
    # pylint: disable=protected-access
    return common._get_log_revisions(self.FAKE_USER_ID, obj, bool(obj))

  # pylint: disable=too-many-arguments
  @staticmethod
  def build_expected_action_list(created_count,
                                 modified_count,
                                 deleted_count,
                                 ownable_created_count=0,
                                 ownable_modified_count=0,
                                 ownable_deleted_count=0):
    """Returns expected action list for given params"""
    total_created_count = created_count + ownable_created_count
    total_modified_count = modified_count + ownable_modified_count
    total_deleted_count = deleted_count + ownable_deleted_count
    return (["created"] * total_created_count +
            ["modified"] * total_modified_count +
            ["deleted"] * total_deleted_count)

  @data(
      # (created_count, modified_count, deleted_count,
      (5, 5, 5),
      (5, 0, 0),
      (0, 5, 0),
      (0, 0, 5),
      (0, 0, 0),
  )
  @unpack
  def test_with_extra_modified_obj(self,
                                   created_count,
                                   modified_count,
                                   deleted_count):
    """Generated test number of simple objects (new extra obj)"""
    expected_results = self.build_expected_action_list(
        created_count, modified_count + 1, deleted_count)
    new = self.populate_object_list(created_count)
    deleted = self.populate_object_list(deleted_count)
    dirty = self.populate_object_list(modified_count)
    with self.mock_get_cache(new, deleted, dirty):
      self.assertEqual(
          expected_results,
          [r.action for r in self.get_log_revisions(self.new_simple_object)])

  @data(
      # (created_count, modified_count, deleted_count,
      (5, 5, 5),
      (0, 5, 0),
      (5, 5, 0),
      (0, 5, 5),
  )
  @unpack
  def test_with_extra_duplicate_obj(self,
                                    created_count,
                                    modified_count,
                                    deleted_count):
    """Generated test number of simple objects (extra obj from dirty pool)"""
    expected_results = self.build_expected_action_list(
        created_count, modified_count, deleted_count)
    new = self.populate_object_list(created_count)
    deleted = self.populate_object_list(deleted_count)
    dirty = self.populate_object_list(modified_count)
    with self.mock_get_cache(new, deleted, dirty):
      self.assertEqual(
          expected_results,
          [r.action for r in self.get_log_revisions(dirty[0])])
