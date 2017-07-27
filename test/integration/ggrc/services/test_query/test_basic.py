# coding: utf-8

# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

# pylint: disable=too-many-lines

"""Tests for /query api endpoint."""

import itertools
import unittest

from datetime import datetime
from operator import itemgetter
from flask import json

import ddt

from ggrc import app
from ggrc import db
from ggrc import models
from ggrc.models import CustomAttributeDefinition as CAD, all_models
from ggrc.snapshotter.rules import Types

from integration.ggrc import TestCase, generator
from integration.ggrc.models import factories


# to be moved into converters.query_helper
DATE_FORMAT_REQUEST = "%m/%d/%Y"
DATE_FORMAT_RESPONSE = "%Y-%m-%d"


# pylint: disable=super-on-old-class; false positive
class BaseQueryAPITestCase(TestCase):
  """Base class for /query api tests with utility methods."""

  def setUp(self):
    """Log in before performing queries."""
    # we don't call super as TestCase.setUp clears the DB
    # super(BaseQueryAPITestCase, self).setUp()
    self.client.get("/login")
    self.generator = generator.ObjectGenerator()

  def _assert_custom_attributes(self, data, attr, **kwargs):
    self._assert_in_custom_attributes(data, attr, *kwargs.keys())
    for key, val in kwargs.iteritems():
      self.assertEqual(val, data[attr][key])

  def _assert_in_custom_attributes(self, data, attr, *args):
    self.assertIn(attr, data)
    for key in args:
      self.assertIn(key, [i['title'] for i in data[attr]])

  def assert_local_cads(self, data, **kwargs):
    self._assert_custom_attributes(data, "local_attributes", **kwargs)

  def assert_global_cads(self, data, **kwargs):
    self._assert_custom_attributes(data, "global_attributes", **kwargs)

  def assert_in_local_cads(self, data, *args):
    self._assert_custom_attributes(data, "local_attributes", *args)

  def assert_in_global_cads(self, data, *args):
    self._assert_in_custom_attributes(data, "global_attributes", *args)

  def _post(self, data):
    """Make a POST to /query endpoint."""
    if not isinstance(data, list):
      data = [data]
    headers = {"Content-Type": "application/json", }
    return self.client.post("/query", data=json.dumps(data), headers=headers)

  def _get_first_result_set(self, data, *keys):
    """Post data, get response, get values from it like in obj["a"]["b"]."""
    response = self._post(data)
    self.assert200(response)
    result = json.loads(response.data)[0]
    for key in keys:
      result = result.get(key)
      self.assertIsNot(result, None)
    return result

  @staticmethod
  def _make_query_dict_base(object_name, type_=None, filters=None, limit=None,
                            order_by=None):
    """Make a dict with query for object_name with optional parameters."""
    query = {
        "object_name": object_name,
        "filters": filters if filters else {"expression": {}},
    }
    if type_:
      query["type"] = type_
    if limit:
      query["limit"] = limit
    if order_by:
      query["order_by"] = order_by
    return query

  @staticmethod
  def make_filter_expression(expression):
    """Convert a three-tuple to a simple expression filter."""
    left, op_name, right = expression
    return {"left": left, "op": {"name": op_name}, "right": right}

  @classmethod
  def _make_query_dict(cls, object_name, expression=None, *args, **kwargs):
    """Make a dict with query for object_name with expression shortcut.

    expression should be in format: (left, op_name, right), like
    ("title", "=", "hello").
    """

    if expression:
      filters = {"expression": cls.make_filter_expression(expression)}
    else:
      filters = None

    return cls._make_query_dict_base(object_name, filters=filters, *args,
                                     **kwargs)


# pylint: disable=too-many-public-methods
@ddt.ddt
class TestAdvancedQueryAPI(BaseQueryAPITestCase):
  """Basic tests for /query api."""

  @classmethod
  def setUpClass(cls):
    """Set up test cases for all tests."""
    TestCase.clear_data()
    # This imported file could be simplified a bit to speed up testing.
    cls._import_file("data_for_export_testing.csv")

  def test_basic_query_eq(self):
    """Filter by = operator."""
    title = "Cat ipsum 1"
    programs = self._get_first_result_set(
        self._make_query_dict("Program", expression=["title", "=", title]),
        "Program",
    )

    self.assertEqual(programs["count"], 1)
    self.assertEqual(len(programs["values"]), programs["count"])
    self.assertEqual(programs["values"][0]["title"], title)

  def test_basic_query_in(self):
    """Filter by ~ operator."""
    title_pattern = "1"
    programs = self._get_first_result_set(
        self._make_query_dict("Program",
                              expression=["title", "~", title_pattern]),
        "Program",
    )

    self.assertEqual(programs["count"], 12)
    self.assertEqual(len(programs["values"]), programs["count"])
    self.assertTrue(all(title_pattern in program["title"]
                        for program in programs["values"]))

  def test_basic_query_ne(self):
    """Filter by != operator."""
    title = "Cat ipsum 1"
    programs = self._get_first_result_set(
        self._make_query_dict("Program",
                              expression=["title", "!=", title]),
        "Program",
    )

    self.assertEqual(programs["count"], 22)
    self.assertEqual(len(programs["values"]), programs["count"])
    self.assertTrue(all(program["title"] != title
                        for program in programs["values"]))

  def test_basic_query_not_in(self):
    """Filter by !~ operator."""
    title_pattern = "1"
    programs = self._get_first_result_set(
        self._make_query_dict("Program",
                              expression=["title", "!~", title_pattern]),
        "Program",
    )

    self.assertEqual(programs["count"], 11)
    self.assertEqual(len(programs["values"]), programs["count"])
    self.assertTrue(all(title_pattern not in program["title"]
                        for program in programs["values"]))

  def test_basic_query_lt(self):
    """Filter by < operator."""
    date = datetime(2015, 5, 18)
    programs = self._get_first_result_set(
        self._make_query_dict("Program",
                              expression=["effective date", "<",
                                          date.strftime(DATE_FORMAT_REQUEST)]),
        "Program",
    )

    self.assertEqual(programs["count"], 9)
    self.assertEqual(len(programs["values"]), programs["count"])
    self.assertTrue(
        all(datetime.strptime(program["start_date"],
                              DATE_FORMAT_RESPONSE) < date
            for program in programs["values"]),
    )

  def test_basic_query_gt(self):
    """Filter by > operator."""
    date = datetime(2015, 5, 18)
    programs = self._get_first_result_set(
        self._make_query_dict("Program",
                              expression=["effective date", ">",
                                          date.strftime(DATE_FORMAT_REQUEST)]),
        "Program",
    )

    self.assertEqual(programs["count"], 13)
    self.assertEqual(len(programs["values"]), programs["count"])
    self.assertTrue(
        all(datetime.strptime(program["start_date"],
                              DATE_FORMAT_RESPONSE) > date
            for program in programs["values"]),
    )

  @unittest.skip("Not implemented.")
  def test_basic_query_missing_field(self):
    """Filter fails on non-existing field."""
    data = self._make_query_dict(
        "Program",
        expression=["This field definitely does not exist", "=", "test"],
    )
    response = self._post(data)
    self.assert400(response)

  # pylint: disable=invalid-name
  def test_basic_query_incorrect_date_format(self):
    """Filtering should fail because of incorrect date input."""
    data = self._make_query_dict(
        "Program",
        expression=["effective date", ">", "05-18-2015"]
    )
    response = self._post(data)
    self.assert400(response)
    self.assertEqual(response.json['message'], "Invalid filter data")

  def test_basic_query_text_search(self):
    """Filter by fulltext search."""
    text_pattern = "ea"
    data = self._make_query_dict("Regulation")
    data["filters"]["expression"] = {
        "op": {"name": "text_search"},
        "text": text_pattern,
    }
    regulations = self._get_first_result_set(data, "Regulation")

    self.assertEqual(regulations["count"], 21)
    self.assertEqual(len(regulations["values"]), regulations["count"])
    self.assertTrue(all((regulation["description"] and
                         text_pattern in regulation["description"]) or
                        (regulation["notes"] and
                         text_pattern in regulation.get("notes", ""))
                        for regulation in regulations["values"]))

  def test_basic_query_pagination(self):
    """Test basic query with pagination info."""
    from_, to_ = 1, 12
    programs = self._get_first_result_set(
        self._make_query_dict("Program",
                              expression=["title", "~", "Cat ipsum"],
                              order_by=[{"name": "title"}],
                              limit=[from_, to_]),
        "Program",
    )
    self.assertEqual(programs["count"], to_ - from_)
    self.assertEqual(len(programs["values"]), programs["count"])
    self.assertEqual(programs["total"], 23)

  def test_basic_query_total(self):
    """The value of "total" doesn't depend on "limit" parameter."""
    programs_no_limit = self._get_first_result_set(
        self._make_query_dict("Program"),
        "Program",
    )
    self.assertEqual(programs_no_limit["count"], programs_no_limit["total"])

    from_, to_ = 3, 5
    programs_limit = self._get_first_result_set(
        self._make_query_dict("Program", limit=[from_, to_]),
        "Program",
    )
    self.assertEqual(programs_limit["count"], to_ - from_)

    self.assertEqual(programs_limit["total"], programs_no_limit["total"])

  def test_query_limit(self):
    """The limit parameter trims the result set."""
    def make_query_dict(limit=None):
      """A shortcut for making queries with different limits."""
      return self._make_query_dict("Program", order_by=[{"name": "title"}],
                                   limit=limit)

    def check_counts_and_values(programs, from_, to_, count=None):
      """Make a typical assertion set for count, total and values."""
      if count is None:
        count = to_ - from_
      self.assertEqual(programs["count"], count)
      self.assertEqual(programs["total"], programs_no_limit["total"])
      self.assertEqual(programs["values"],
                       programs_no_limit["values"][from_:to_])

    programs_no_limit = self._get_first_result_set(
        make_query_dict(),
        "Program",
    )

    self.assertEqual(programs_no_limit["count"], programs_no_limit["total"])

    programs_0_10 = self._get_first_result_set(
        make_query_dict(limit=[0, 10]),
        "Program",
    )

    check_counts_and_values(programs_0_10, from_=0, to_=10)

    programs_10_21 = self._get_first_result_set(
        make_query_dict(limit=[10, 21]),
        "Program",
    )

    check_counts_and_values(programs_10_21, from_=10, to_=21)

    programs_10_top = self._get_first_result_set(
        make_query_dict(limit=[10, programs_no_limit["total"] + 42]),
        "Program",
    )

    check_counts_and_values(programs_10_top, from_=10, to_=None,
                            count=programs_no_limit["total"] - 10)

    # check if a valid integer string representation gets casted
    programs_10_21_str = self._get_first_result_set(
        make_query_dict(limit=[10, "21"]),
        "Program",
    )
    programs_10_str_21 = self._get_first_result_set(
        make_query_dict(limit=["10", 21]),
        "Program",
    )

    self.assertDictEqual(programs_10_21_str, programs_10_21)
    self.assertDictEqual(programs_10_str_21, programs_10_21)

  def test_query_invalid_limit(self):
    """Invalid limit parameters are handled properly."""

    # invalid "from"
    response = self._post(
        self._make_query_dict("Program", limit=["invalid", 12]),
    )
    self.assert400(response)
    self.assertEqual(response.json['message'],
                     "Invalid limit operator. Integers expected.")

    # invalid "to"
    response = self._post(
        self._make_query_dict("Program", limit=[0, "invalid"]),
    )
    self.assert400(response)
    self.assertEqual(response.json['message'],
                     "Invalid limit operator. Integers expected.")

    # "from" >= "to"
    response = self._post(
        self._make_query_dict("Program", limit=[12, 0]),
    )
    self.assert400(response)
    self.assertEqual(response.json['message'],
                     "Limit start should be smaller than end.")

    # negative "from"
    response = self._post(
        self._make_query_dict("Program", limit=[-2, 10]),
    )
    self.assert400(response)
    self.assertEqual(response.json['message'],
                     "Limit cannot contain negative numbers.")

    # negative "to"
    response = self._post(
        self._make_query_dict("Program", limit=[2, -10]),
    )
    self.assert400(response)
    self.assertEqual(response.json['message'],
                     "Limit cannot contain negative numbers.")

  def test_query_order_by(self):
    """Results get sorted by own field."""
    # assumes unique title

    def get_titles(programs):
      return [program["title"] for program in programs]

    programs_default = self._get_first_result_set(
        self._make_query_dict("Program",
                              order_by=[{"name": "title"}]),
        "Program", "values",
    )
    titles_default = get_titles(programs_default)

    programs_asc = self._get_first_result_set(
        self._make_query_dict("Program",
                              order_by=[{"name": "title", "desc": False}]),
        "Program", "values",
    )
    titles_asc = get_titles(programs_asc)

    programs_desc = self._get_first_result_set(
        self._make_query_dict("Program",
                              order_by=[{"name": "title", "desc": True}]),
        "Program", "values",
    )
    titles_desc = get_titles(programs_desc)

    # the titles are sorted ascending with desc=False
    self.assertListEqual(titles_asc, sorted(titles_asc))
    # desc=False by default
    self.assertListEqual(titles_default, titles_asc)
    # the titles are sorted descending with desc=True
    self.assertListEqual(titles_desc, list(reversed(titles_asc)))

  def test_order_by_several_fields(self):
    """Results get sorted by two fields at once."""
    regulations = self._get_first_result_set(
        self._make_query_dict("Regulation",
                              order_by=[{"name": "notes", "desc": True},
                                        {"name": "title"}]),
        "Regulation", "values",
    )

    regulations_unsorted = self._get_first_result_set(
        self._make_query_dict("Regulation"),
        "Regulation", "values",
    )

    self.assertListEqual(
        regulations,
        sorted(sorted(regulations_unsorted,
                      key=itemgetter("title")),
               key=itemgetter("notes"),
               reverse=True),
    )

  def test_order_by_related_titled(self):
    """Results get sorted by title of related Titled object."""
    audits_title = self._get_first_result_set(
        self._make_query_dict("Audit",
                              order_by=[{"name": "program"}, {"name": "id"}]),
        "Audit", "values",
    )

    audits_unsorted = self._get_first_result_set(
        self._make_query_dict("Audit"),
        "Audit", "values",
    )

    # get titles from programs to check ordering
    programs = self._get_first_result_set(
        self._make_query_dict("Program"),
        "Program", "values",
    )
    program_id_title = {program["id"]: program["title"]
                        for program in programs}

    self.assertListEqual(
        audits_title,
        sorted(sorted(audits_unsorted, key=itemgetter("id")),
               key=lambda a: program_id_title[a["program"]["id"]]),
    )

  def test_query_order_by_owners(self):
    """Results get sorted by name or email of the (first) owner."""
    # TODO: the test data set lacks objects with several owners
    policies_owner = self._get_first_result_set(
        self._make_query_dict("Policy",
                              order_by=[{"name": "Admin"}, {"name": "id"}]),
        "Policy", "values",
    )
    policies_unsorted = self._get_first_result_set(
        self._make_query_dict("Policy"),
        "Policy", "values",
    )
    people = self._get_first_result_set(
        self._make_query_dict("Person"),
        "Person", "values",
    )
    person_id_name = {person["id"]: (person["name"], person["email"])
                      for person in people}
    policy_id_owner = {
        policy["id"]: person_id_name[
            policy["access_control_list"][0]["person_id"]
        ]
        for policy in policies_unsorted
    }

    self.assertListEqual(
        policies_owner,
        sorted(sorted(policies_unsorted, key=itemgetter("id")),
               key=lambda p: policy_id_owner[p["id"]]),
    )

  def test_query_order_by_assignee(self):
    """Results get sorted by name or email assignee."""
    controls_by_assignee = self._get_first_result_set(
        self._make_query_dict("Control",
                              order_by=[{"name": "principal_assessor"},
                                        {"name": "id"}]),
        "Control", "values",
    )
    controls_unsorted = self._get_first_result_set(
        self._make_query_dict("Control"),
        "Control", "values",
    )
    people = self._get_first_result_set(
        self._make_query_dict("Person"),
        "Person", "values",
    )
    person_id_name = {person["id"]: (person["name"], person["email"])
                      for person in people}
    control_id_assignee = {
        control["id"]: person_id_name[control["principal_assessor"]["id"]]
        if control["principal_assessor"] else ""
        for control in controls_unsorted
    }

    self.assertListEqual(
        controls_by_assignee,
        sorted(sorted(controls_unsorted, key=itemgetter("id")),
               key=lambda p: control_id_assignee[p["id"]]),
    )

  def test_filter_control_by_frequency(self):
    """Test correct filtering by frequency"""
    controls = self._get_first_result_set(
        self._make_query_dict("Control",
                              expression=["frequency", "=", "yearly"]),
        "Control",
    )
    self.assertEqual(controls["count"], 4)

  def test_order_control_by_frequency(self):
    """Test correct ordering and by frequency"""
    controls_unordered = self._get_first_result_set(
        self._make_query_dict("Control",),
        "Control", "values"
    )
    controls_ordered_1 = self._get_first_result_set(
        self._make_query_dict("Control",
                              order_by=[{"name": "Frequency"},
                                        {"name": "id"}]),
        "Control", "values"
    )
    options_map = {o.id: o.title for o in models.Option.query}

    def sort_key(val):
      """sorting key getter function"""
      freq = val["verify_frequency"]
      if not freq:
        return None
      return options_map[freq["id"]]

    controls_ordered_2 = sorted(controls_unordered, key=sort_key)
    self.assertListEqual(controls_ordered_1, controls_ordered_2)

  def test_filter_control_by_kind(self):
    """Test correct filtering by kind/nature"""
    controls = self._get_first_result_set(
        self._make_query_dict("Control",
                              expression=["kind/nature", "=", "Corrective"]),
        "Control",
    )
    self.assertEqual(controls["count"], 3)

  def test_order_control_by_kind(self):
    """Test correct ordering and by kind/nature"""
    controls_unordered = self._get_first_result_set(
        self._make_query_dict("Control",),
        "Control", "values"
    )
    controls_ordered_1 = self._get_first_result_set(
        self._make_query_dict("Control",
                              order_by=[{"name": "kind/nature"},
                                        {"name": "id"}]),
        "Control", "values"
    )
    options_map = {o.id: o.title for o in models.Option.query}

    def sort_key(val):
      """sorting key getter function"""
      kind = val["kind"]
      if not kind:
        return None
      return options_map[kind["id"]]

    controls_ordered_2 = sorted(controls_unordered, key=sort_key)
    self.assertListEqual(controls_ordered_1, controls_ordered_2)

  def test_filter_control_by_means(self):
    """Test correct filtering by means"""
    controls = self._get_first_result_set(
        self._make_query_dict("Control",
                              expression=["type/means", "=", "Physical"]),
        "Control",
    )
    self.assertEqual(controls["count"], 3)

  def test_order_control_by_means(self):
    """Test correct ordering and by means"""
    controls_unordered = self._get_first_result_set(
        self._make_query_dict("Control",),
        "Control", "values"
    )
    controls_ordered_1 = self._get_first_result_set(
        self._make_query_dict("Control",
                              order_by=[{"name": "type/means"},
                                        {"name": "id"}]),
        "Control", "values"
    )
    options_map = {o.id: o.title for o in models.Option.query}

    def sort_key(val):
      """sorting key getter function"""
      kind = val["means"]
      if not kind:
        return None
      return options_map[kind["id"]]

    controls_ordered_2 = sorted(controls_unordered, key=sort_key)
    self.assertListEqual(controls_ordered_1, controls_ordered_2)

  def test_query_wf_by_frequency(self):
    """Test correct filtering of Workflows by frequency

    The case this test was created for is: frequency = "one time"
    Because it consists of two words, and we need to test the new
    "value mapping"s for such cases
    Also another regular test case added.
    """
    workflows = self._get_first_result_set(
        self._make_query_dict("Workflow",
                              expression=["frequency", "=", "one time"]),
        "Workflow",
    )
    self.assertEqual(workflows["count"], 1)
    workflows = self._get_first_result_set(
        self._make_query_dict("Workflow",
                              expression=["frequency", "=", "monthly"]),
        "Workflow",
    )
    self.assertEqual(workflows["count"], 6)

  def test_filter_control_by_key_control(self):
    """Test correct filtering by SIGNIFICANCE field"""
    controls = self._get_first_result_set(
        self._make_query_dict("Control",
                              expression=["significance", "=", "non-key"]),
        "Control",
    )
    self.assertEqual(controls["count"], 2)

  def test_order_control_by_key_control(self):
    """Test correct ordering and by SIGNIFICANCE field"""
    controls_unordered = self._get_first_result_set(
        self._make_query_dict("Control",),
        "Control", "values"
    )
    controls_ordered_1 = self._get_first_result_set(
        self._make_query_dict("Control",
                              order_by=[{"name": "significance"},
                                        {"name": "id"}]),
        "Control", "values"
    )
    controls_ordered_2 = sorted(controls_unordered,
                                key=lambda ctrl: (ctrl["key_control"] is None,
                                                  ctrl["key_control"]),
                                reverse=True)
    self.assertListEqual(controls_ordered_1, controls_ordered_2)

  def test_filter_control_by_fraud_related(self):
    """Test correct filtering by fraud_related field"""
    controls = self._get_first_result_set(
        self._make_query_dict("Control",
                              expression=["fraud related", "=", "yes"]),
        "Control",
    )
    self.assertEqual(controls["count"], 2)

  def test_order_control_by_fraud_related(self):
    """Test correct ordering and by fraud_related field"""
    controls_unordered = self._get_first_result_set(
        self._make_query_dict("Control",),
        "Control", "values"
    )

    controls_ordered_1 = self._get_first_result_set(
        self._make_query_dict("Control",
                              order_by=[{"name": "fraud related"},
                                        {"name": "id"}]),
        "Control", "values"
    )
    controls_ordered_2 = sorted(controls_unordered,
                                key=lambda ctrl: ctrl["fraud_related"])
    self.assertListEqual(controls_ordered_1, controls_ordered_2)

  def test_filter_control_by_assertions(self):
    """Test correct filtering by assertions field"""
    controls = self._get_first_result_set(
        self._make_query_dict("Control",
                              expression=["assertions", "=", "privacy"]),
        "Control",
    )
    self.assertEqual(controls["count"], 3)

  def test_order_control_by_assertions(self):
    """Test correct ordering and by assertions"""
    controls_unordered = self._get_first_result_set(
        self._make_query_dict("Control",),
        "Control", "values"
    )

    controls_ordered_1 = self._get_first_result_set(
        self._make_query_dict("Control",
                              order_by=[{"name": "assertions"},
                                        {"name": "id"}]),
        "Control", "values"
    )
    categories = {c.id: c.name for c in models.CategoryBase.query}

    def sort_key(val):
      ctrl_assertions = val.get("assertions")
      if isinstance(ctrl_assertions, list) and ctrl_assertions:
        return (categories.get(ctrl_assertions[0]["id"]), val["id"])
      return (None, val["id"])

    controls_ordered_2 = sorted(controls_unordered, key=sort_key)
    self.assertListEqual(controls_ordered_1, controls_ordered_2)

  def test_filter_control_by_categories(self):
    """Test correct filtering by categories field"""
    controls = self._get_first_result_set(
        self._make_query_dict(
            "Control",
            expression=["categories", "=", "Physical Security"]),
        "Control",
    )
    self.assertEqual(controls["count"], 3)

  def test_order_control_by_categories(self):
    """Test correct ordering and by categories"""
    controls_unordered = self._get_first_result_set(
        self._make_query_dict("Control",),
        "Control", "values"
    )

    controls_ordered_1 = self._get_first_result_set(
        self._make_query_dict("Control",
                              order_by=[{"name": "categories"},
                                        {"name": "id"}]),
        "Control", "values"
    )
    categories = {c.id: c.name for c in models.CategoryBase.query}

    def sort_key(val):
      ctrl_categories = val.get("categories")
      if isinstance(ctrl_categories, list) and ctrl_categories:
        return (categories.get(ctrl_categories[0]["id"]), val["id"])
      return (None, val["id"])

    controls_ordered_2 = sorted(controls_unordered, key=sort_key)
    self.assertListEqual(controls_ordered_1, controls_ordered_2)

  def test_query_count(self):
    """The value of "count" is same for "values" and "count" queries."""
    programs_values = self._get_first_result_set(
        self._make_query_dict("Program", type_="values"),
        "Program",
    )
    programs_count = self._get_first_result_set(
        self._make_query_dict("Program", type_="count"),
        "Program",
    )

    self.assertEqual(programs_values["count"], programs_count["count"])

  def test_query_ids(self):
    """The ids are the same for "values" and "ids" queries."""
    programs_values = self._get_first_result_set(
        self._make_query_dict("Program", type_="values"),
        "Program",
    )
    programs_ids = self._get_first_result_set(
        self._make_query_dict("Program", type_="ids"),
        "Program",
    )

    self.assertEqual(
        set(obj.get("id") for obj in programs_values["values"]),
        set(programs_ids["ids"]),
    )

  def test_multiple_queries(self):
    """Multiple queries POST is identical to multiple single-query POSTs."""
    data_list = [
        self._make_query_dict("Program",
                              order_by=[{"name": "title"}],
                              limit=[1, 12],
                              expression=["title", "~", "Cat ipsum"]),
        self._make_query_dict("Program",
                              type_="values"),
        self._make_query_dict("Program",
                              type_="count"),
        self._make_query_dict("Program",
                              type_="ids"),
        self._make_query_dict("Program",
                              type_="ids",
                              expression=["title", "=", "Cat ipsum 1"]),
        self._make_query_dict("Program",
                              expression=["title", "~", "1"]),
        self._make_query_dict("Program",
                              expression=["title", "!=", "Cat ipsum 1"]),
        self._make_query_dict("Program",
                              expression=["title", "!~", "1"]),
        self._make_query_dict("Program",
                              expression=["effective date", "<",
                                          "05/18/2015"]),
        self._make_query_dict("Program",
                              expression=["effective date", ">",
                                          "05/18/2015"]),
        {
            "object_name": "Regulation",
            "fields": ["description", "notes"],
            "filters": {
                "expression": {
                    "op": {"name": "text_search"},
                    "text": "ea",
                },
            },
        },
    ]

    response_multiple_posts = [json.loads(self._post(data).data)[0]
                               for data in data_list]
    response_single_post = json.loads(self._post(data_list).data)

    self.assertEqual(response_multiple_posts, response_single_post)

  def test_is_empty_query_by_native_attrs(self):
    """Filter by navive object attrs with 'is empty' operator."""
    programs = self._get_first_result_set(
        self._make_query_dict("Program",
                              expression=["notes", "is", "empty"]),
        "Program",
    )
    self.assertEqual(programs["count"], 1)
    self.assertEqual(set([u'Cat ipsum 1']),
                     set([program["title"] for program
                          in programs["values"]]))

  @ddt.data(
      (all_models.Control, [all_models.Objective, all_models.Control,
                            all_models.Market, all_models.Objective]),
      (all_models.Assessment, [all_models.Control, all_models.Control,
                               all_models.Market, all_models.Objective]),
      (all_models.Assessment, [all_models.Issue, all_models.Issue,
                               all_models.Issue, all_models.Issue]),
      (all_models.Issue, [all_models.Assessment, all_models.Control,
                          all_models.Market, all_models.Objective]),
  )
  @ddt.unpack
  def test_search_relevant_to_type(self, base_type, relevant_types):
    """Test filter with 'relevant to' conditions."""
    is_scoped = base_type.__name__ in Types.scoped
    audit_data = {}
    if is_scoped:
      audit = factories.AuditFactory()
      audit_data = {"audit": {"id": audit.id}}

    _, base_obj = self.generator.generate_object(base_type, audit_data)
    relevant_objects = [
        self.generator.generate_object(type_, audit_data)[1]
        for type_ in relevant_types
    ]

    with factories.single_commit():
      query_data = []
      for relevant_obj in relevant_objects:
        related_obj = relevant_obj

        # Snapshotable objects are related through the Snapshot
        if is_scoped and relevant_obj.type in Types.all:
          related_obj = factories.SnapshotFactory(
              parent=audit,
              child_id=relevant_obj.id,
              child_type=relevant_obj.type,
              revision_id=models.Revision.query.filter_by(
                  resource_type=relevant_obj.type
              ).first().id,
          )
        factories.RelationshipFactory(source=base_obj, destination=related_obj)

        query_data.append(self._make_query_dict(
            relevant_obj.type,
            expression=["id", "=", relevant_obj.id],
            type_="ids",
        ))

    filter_relevant = {
        "filters": {
            "expression": {
                "left": {
                    "left": {
                        "ids": "0",
                        "object_name": "__previous__",
                        "op": {"name": "relevant"}
                    },
                    "op": {"name": "AND"},
                    "right": {
                        "ids": "1",
                        "object_name": "__previous__",
                        "op": {"name": "relevant"}
                    }
                },
                "op": {"name": "AND"},
                "right": {
                    "left": {
                        "ids": "2",
                        "object_name": "__previous__",
                        "op": {"name": "relevant"}
                    },
                    "op": {"name": "AND"},
                    "right": {
                        "ids": "3",
                        "object_name": "__previous__",
                        "op": {"name": "relevant"}
                    }
                }
            }
        },
        "object_name": base_type.__name__
    }
    query_data.append(filter_relevant)
    response = json.loads(self._post(query_data).data)
    # Last batch contain result for query with "related" condition
    result_count = response[-1][base_type.__name__]["count"]
    self.assertEqual(result_count, 1)


class TestQueryAssessmentCA(BaseQueryAPITestCase):
  """Test filtering assessments by CAs"""

  def setUp(self):
    """Set up test cases for all tests."""
    TestCase.clear_data()
    self._generate_special_assessments()
    response = self._import_file("sorting_assessment_with_ca_setup.csv")
    self._check_csv_response(response, {})
    self.client.get("/login")

  @staticmethod
  def _generate_special_assessments():
    """Generate two Assessments for two local CADs with same name."""
    assessment_with_date = None
    assessment_with_text = None
    audit = factories.AuditFactory(
        slug="audit"
    )
    assessment_with_date = factories.AssessmentFactory(
        title="Assessment with date",
        slug="ASMT-SPECIAL-DATE",
        audit=audit,
    )
    assessment_with_text = factories.AssessmentFactory(
        title="Assessment with text",
        slug="ASMT-SPECIAL-TEXT",
        audit=audit,
    )
    # local CADs for the Assessments
    for title in ["Date or arbitrary text", "Date or text styled as date"]:
      factories.CustomAttributeDefinitionFactory(
          title=title,
          definition_type="assessment",
          definition_id=assessment_with_date.id,
          attribute_type="Date",
      )
      factories.CustomAttributeDefinitionFactory(
          title=title,
          definition_type="assessment",
          definition_id=assessment_with_text.id,
          attribute_type="Text",
      )

  # pylint: disable=invalid-name
  def test_ca_query_different_types_local_ca(self):
    """Filter by local CAs with same title and different types."""
    date = datetime(2016, 10, 31)
    assessments_date = self._get_first_result_set(
        self._make_query_dict(
            "Assessment",
            expression=["Date or arbitrary text", "=",
                        date.strftime(DATE_FORMAT_REQUEST)],
        ),
        "Assessment", "values",
    )

    self.assertItemsEqual([asmt["title"] for asmt in assessments_date],
                          ["Assessment with date"])

    assessments_text = self._get_first_result_set(
        self._make_query_dict(
            "Assessment",
            expression=["Date or arbitrary text", "=", "Some text 2016"],
        ),
        "Assessment", "values",
    )

    self.assertItemsEqual([asmt["title"] for asmt in assessments_text],
                          ["Assessment with text"])

    assessments_mixed = self._get_first_result_set(
        self._make_query_dict(
            "Assessment",
            expression=["Date or arbitrary text", "~", "2016"],
        ),
        "Assessment", "values",
    )

    self.assertItemsEqual([asmt["title"] for asmt in assessments_mixed],
                          ["Assessment with text", "Assessment with date"])

    date = datetime(2016, 11, 9)
    assessments_mixed = self._get_first_result_set(
        self._make_query_dict(
            "Assessment",
            expression=["Date or text styled as date", "=",
                        date.strftime(DATE_FORMAT_REQUEST)],
        ),
        "Assessment", "values",
    )

    self.assertItemsEqual([asmt["title"] for asmt in assessments_mixed],
                          ["Assessment with text", "Assessment with date"])


class TestSortingQuery(BaseQueryAPITestCase):
  """Test sorting is correct requested with query API"""
  def setUp(self):
    TestCase.clear_data()
    super(TestSortingQuery, self).setUp()
    self.client.get("/login")

  @classmethod
  def create_assignees(cls, obj, persons):
    """Create assignees for object.

    This is used only during object creation because we cannot create
    assignees at that point yet.

    Args:
      obj: Assignable object.
      persons: [("(string) email", "Assignee roles"), ...] A list of people
        and their roles
    Returns:
      [(person, object-person relationship,
        object-person relationship attributes), ...] A list of persons with
      their relationships and relationship attributes.
    """
    assignees = []
    for person, roles in persons:
      person = factories.PersonFactory(email=person)

      object_person_rel = factories.RelationshipFactory(
          source=obj,
          destination=person
      )

      object_person_rel_attrs = factories.RelationshipAttrFactory(
          relationship_id=object_person_rel.id,
          attr_name="AssigneeType",
          attr_value=roles
      )
      assignees += [(person, object_person_rel, object_person_rel_attrs)]
    return assignees

  def create_assessment(self, title=None, people=None):
    """Create default assessment with some default assignees in all roles.
    Args:
      people: List of tuples with email address and their assignee roles for
              Assessments.
    Returns:
      Assessment object.
    """
    assessment = factories.AssessmentFactory(title=title)
    context = factories.ContextFactory(related_object=assessment)
    assessment.context = context

    if not people:
      people = [
          ("creator@example.com", "Creator"),
          ("assessor_1@example.com", "Assessor"),
          ("assessor_2@example.com", "Assessor"),
          ("verifier_1@example.com", "Verifier"),
          ("verifier_2@example.com", "Verifier"),
      ]

    defined_assessors = len([1 for _, role in people
                             if "Assessor" in role])
    defined_creators = len([1 for _, role in people
                            if "Creator" in role])
    defined_verifiers = len([1 for _, role in people
                             if "Verifier" in role])

    self.create_assignees(assessment, people)

    creators = [assignee for assignee, roles in assessment.assignees
                if "Creator" in roles]
    assignees = [assignee for assignee, roles in assessment.assignees
                 if "Assessor" in roles]
    verifiers = [assignee for assignee, roles in assessment.assignees
                 if "Verifier" in roles]

    self.assertEqual(len(creators), defined_creators)
    self.assertEqual(len(assignees), defined_assessors)
    self.assertEqual(len(verifiers), defined_verifiers)
    return assessment

  # pylint: disable=invalid-name
  def test_sorting_assessments_by_assignees(self):
    """Test assessments are sorted by multiple assignees correctly"""
    people_set_1 = [
        ("2creator@example.com", "Creator"),
        ("assessor_2@example.com", "Assessor"),
        ("assessor_1@example.com", "Assessor"),
        ("1verifier_1@example.com", "Verifier"),
        ("2verifier_2@example.com", "Verifier"),
    ]
    self.create_assessment("Assessment_1", people_set_1)
    people_set_2 = [
        ("1creator@example.com", "Creator"),
        ("1assessor@example.com", "Assessor"),
        ("2assessor@example.com", "Assessor"),
        ("verifier_1@example.com", "Verifier"),
        ("verifier_2@example.com", "Verifier"),
    ]
    self.create_assessment("Assessment_2", people_set_2)

    assessments_by_creators = self._get_first_result_set(
        self._make_query_dict("Assessment",
                              order_by=[{"name": "creators",
                                         "desc": False}]),
        "Assessment", "values",
    )
    self.assertListEqual([ass["title"] for ass in assessments_by_creators],
                         ["Assessment_2", "Assessment_1"])

    assessments_by_verifiers = self._get_first_result_set(
        self._make_query_dict("Assessment",
                              order_by=[{"name": "verifiers",
                                         "desc": False}]),
        "Assessment", "values",
    )
    self.assertListEqual([ass["title"] for ass in assessments_by_verifiers],
                         ["Assessment_1", "Assessment_2"])

    assessments_by_assessors = self._get_first_result_set(
        self._make_query_dict("Assessment",
                              order_by=[{"name": "assignees",
                                         "desc": False}]),
        "Assessment", "values",
    )
    self.assertListEqual([ass["title"] for ass in assessments_by_assessors],
                         ["Assessment_2", "Assessment_1"])


class TestQueryAssessmentByEvidenceURL(BaseQueryAPITestCase):
  """Test assessments filtering by Evidence and/or URL"""
  def setUp(self):
    """Set up test cases for all tests."""
    TestCase.clear_data()
    response = self._import_file("assessment_full_no_warnings.csv")
    self._check_csv_response(response, {})
    self.client.get("/login")

  def test_query_evidence_url(self):
    """Test assessments query filtered by Evidence"""
    assessments_by_evidence = self._get_first_result_set(
        self._make_query_dict(
            "Assessment",
            expression=["Evidence", "~", "i.imgur.com"],
        ),
        "Assessment", "values",
    )

    self.assertEqual(len(assessments_by_evidence), 2)
    self.assertItemsEqual([asmt["title"] for asmt in assessments_by_evidence],
                          ["Assessment title 1", "Assessment title 3"])

    assessments_by_url = self._get_first_result_set(
        self._make_query_dict(
            "Assessment",
            expression=["Reference URL", "~", "i.imgur.com"],
        ),
        "Assessment", "values",
    )

    self.assertEqual(len(assessments_by_url), 3)
    self.assertItemsEqual([asmt["title"] for asmt in assessments_by_url],
                          ["Assessment title 1",
                           "Assessment title 3",
                           "Assessment title 4"])


class TestQueryWithCA(BaseQueryAPITestCase):
  """Test query API with custom attributes."""

  def setUp(self):
    """Set up test cases for all tests."""
    TestCase.clear_data()
    self._generate_cad()
    response = self._import_file("sorting_with_ca_setup.csv")
    self._check_csv_response(response, {})
    self.client.get("/login")

  @staticmethod
  def _generate_cad():
    """Generate custom attribute definitions."""
    factories.CustomAttributeDefinitionFactory(
        title="CA dropdown",
        definition_type="program",
        multi_choice_options="one,two,three,four,five",
    )
    factories.CustomAttributeDefinitionFactory(
        title="CA text",
        definition_type="program",
    )
    factories.CustomAttributeDefinitionFactory(
        title="CA date",
        definition_type="program",
        attribute_type="Date",
    )
    factories.CustomAttributeDefinitionFactory(
        title="CA person",
        definition_type="program",
        attribute_type="Map:Person",
    )

  def test_single_ca_sorting(self):
    """Results get sorted by single custom attribute field."""

    programs = self._get_first_result_set(
        self._make_query_dict("Program",
                              order_by=[{"name": "title"}]),
        "Program", "values",
    )

    keys = [program["title"] for program in programs]
    self.assertEqual(keys, sorted(keys))

    programs = self._get_first_result_set(
        self._make_query_dict("Program",
                              order_by=[{"name": "CA text"}]),
        "Program", "values",
    )
    keys = []
    for program in programs:
      self.assert_in_global_cads(program, "CA text")
      for attr in program["global_attributes"]:
        if attr["title"] == "CA text":
          keys.append(attr["values"][0]["value"])
    self.assertEqual(keys, sorted(keys))

  def test_mixed_ca_sorting(self):
    """Test sorting by multiple fields with CAs."""

    programs = self._get_first_result_set(
        self._make_query_dict("Program",
                              order_by=[{"name": "CA text"},
                                        {"name": "title"}]),
        "Program", "values",
    )

    keys = []
    for program in programs:
      self.assert_in_global_cads(program, "CA text")
      for attr in program["global_attributes"]:
        if attr["title"] == "CA text":
          keys.append((attr["values"][0]["value"], attr['title']))

    self.assertEqual(keys, sorted(keys))

    programs = self._get_first_result_set(
        self._make_query_dict("Program",
                              order_by=[{"name": "title"},
                                        {"name": "CA text"}]),
        "Program", "values",
    )

    keys = []
    for program in programs:
      self.assert_in_global_cads(program, "CA text")
      for attr in program["global_attributes"]:
        if attr["title"] == "CA text":
          keys.append((program['title'], attr["values"][0]["value"]))

    self.assertEqual(keys, sorted(keys))

  def test_multiple_ca_sorting(self):
    """Test sorting by multiple CA fields"""

    programs = self._get_first_result_set(
        self._make_query_dict("Program",
                              order_by=[{"name": "CA text"},
                                        {"name": "CA dropdown"}]),
        "Program", "values",
    )

    keys = []
    for program in programs:
      self.assert_in_global_cads(
          program, "CA text", "CA dropdown")
      res = []
      for key in ("CA text", "CA dropdown"):
        for attr in program["global_attributes"]:
          if attr["title"] == key:
            res.append(attr["values"][0]["value"])
      keys.append(tuple(res))
    self.assertEqual(keys, sorted(keys))

  def test_ca_query_eq(self):
    """Test CA date fields filtering by = operator."""
    date = datetime(2015, 5, 18)
    programs = self._get_first_result_set(
        self._make_query_dict("Program",
                              expression=["ca date", "=",
                                          date.strftime(DATE_FORMAT_REQUEST)]),
        "Program", "values",
    )
    titles = [prog["title"] for prog in programs]
    self.assertItemsEqual(titles, ("F", "H", "J", "B", "D"))
    self.assertEqual(len(programs), 5)

  def test_ca_filter_by_person(self):
    """Test CA person fields filtering by = operator."""
    programs = self._get_first_result_set(
        self._make_query_dict("Program",
                              expression=["ca person", "=", "three"]),
        "Program", "values",
    )
    titles = [prog["title"] for prog in programs]
    self.assertItemsEqual(titles, ("F",))
    self.assertEqual(len(programs), 1)

  def test_ca_query_lt(self):
    """Test CA date fields filtering by < operator."""
    date = datetime(2015, 5, 18)
    programs = self._get_first_result_set(
        self._make_query_dict("Program",
                              expression=["ca date", "<",
                                          date.strftime(DATE_FORMAT_REQUEST)]),
        "Program", "values",
    )
    titles = [prog["title"] for prog in programs]
    self.assertItemsEqual(titles, ("G", "I"))
    self.assertEqual(len(programs), 2)

  def test_ca_query_gt(self):
    """Test CA date fields filtering by > operator."""
    date = datetime(2015, 5, 18)
    programs = self._get_first_result_set(
        self._make_query_dict("Program",
                              expression=["ca date", ">",
                                          date.strftime(DATE_FORMAT_REQUEST)]),
        "Program", "values",
    )
    titles = [prog["title"] for prog in programs]
    self.assertItemsEqual(titles, ("A", "C", "E"))
    self.assertEqual(len(programs), 3)

  # pylint: disable=invalid-name
  def test_ca_query_incorrect_date_format(self):
    """CA filtering should fail on incorrect date when CA title is unique."""
    data = self._make_query_dict(
        "Program",
        expression=["ca date", ">", "05-18-2015"],
    )
    response = self._post(data)
    self.assert400(response)
    self.assertEqual(response.json['message'], "Invalid filter data")


class TestQueryWithUnicode(BaseQueryAPITestCase):
  """Test query API with unicode values."""

  CAD_TITLE1 = u"CA список" + "X" * 200
  CAD_TITLE2 = u"CA текст" + "X" * 200

  @classmethod
  def setUpClass(cls):
    """Set up test cases for all tests."""
    TestCase.clear_data()
    cls._generate_cad()
    cls._import_file("querying_with_unicode.csv")

  @classmethod
  def _generate_cad(cls):
    """Generate custom attribute definitions."""
    with app.app.app_context():
      factories.CustomAttributeDefinitionFactory(
          title=cls.CAD_TITLE1,
          definition_type="program",
          multi_choice_options=u"один,два,три,четыре,пять",
      )
      factories.CustomAttributeDefinitionFactory(
          title=cls.CAD_TITLE2,
          definition_type="program",
      )

  @staticmethod
  def _flatten_cav(data):
    """Unpack CAVs and put them in data as object attributes."""
    cad_names = dict(db.session.query(CAD.id, CAD.title))
    for entry in data:
      for cav in itertools.chain(entry.get("global_attributes", []),
                                 entry.get("local_attributes", [])):
        for value in cav['values']:
          entry[cad_names[cav["id"]]] = value["value"]
    return data

  def setUp(self):
    self.client.get("/login")

  def test_query(self):
    """Test query by unicode value."""
    title = u"программа A"
    programs = self._get_first_result_set(
        self._make_query_dict("Program", expression=["title", "=", title]),
        "Program",
    )

    self.assertEqual(programs["count"], 1)
    self.assertEqual(len(programs["values"]), programs["count"])
    self.assertEqual(programs["values"][0]["title"], title)

  def test_sorting_by_ca(self):
    """Test sorting by CA fields with unicode names."""
    programs = self._flatten_cav(
        self._get_first_result_set(
            self._make_query_dict("Program",
                                  order_by=[{"name": self.CAD_TITLE2},
                                            {"name": self.CAD_TITLE1}]),
            "Program", "values",
        )
    )

    keys = [(prog[self.CAD_TITLE2], prog[self.CAD_TITLE1])
            for prog in programs]
    self.assertEqual(keys, sorted(keys))
