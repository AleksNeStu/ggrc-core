# coding: utf-8

# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Tests for /query api endpoint."""

from sqlalchemy import func
from flask import json

from ggrc import app
from ggrc import views
from ggrc import models
from ggrc import db

from integration.ggrc import TestCase
from integration.ggrc.models import factories


# pylint: disable=super-on-old-class
class TestAuditSnapshotQueries(TestCase):
  """Tests for /query api for Audit snapshots"""

  def setUp(self):
    """Log in before performing queries."""
    self.client.get("/login")

  def _post(self, data):
    return self.client.post(
        "/query",
        data=json.dumps(data),
        headers={"Content-Type": "application/json", }
    )

  @classmethod
  def setUpClass(cls):
    TestCase.clear_data()
    with app.app.app_context():
      cls._setup_objects()

  @staticmethod
  def _setup_objects():
    """Create and reindex objects needed for tests"""
    text_cad = factories.CustomAttributeDefinitionFactory(
        title="text cad",
        definition_type="market",
    )
    date_cad = factories.CustomAttributeDefinitionFactory(
        title="date cad",
        definition_type="market",
        attribute_type="Date",
    )

    audit = factories.AuditFactory()

    for i in range(5):
      factories.OrgGroupFactory()
      market = factories.MarketFactory()
      factories.CustomAttributeValueFactory(
          custom_attribute=date_cad,
          attributable=market,
          attribute_value="2016-11-0{}".format(i + 3),
      )
      factories.CustomAttributeValueFactory(
          custom_attribute=text_cad,
          attributable=market,
          attribute_value="2016-11-0{}".format(i + 1),
      )

    revisions = models.Revision.query.filter(
        models.Revision.resource_type.in_(["OrgGroup", "Market"]),
        models.Revision.id.in_(
            db.session.query(func.max(models.Revision.id)).group_by(
                models.Revision.resource_type,
                models.Revision.resource_id,
            )
        ),
    )

    for revision in revisions:
      factories.SnapshotFactory(
          child_id=revision.resource_id,
          child_type=revision.resource_type,
          revision=revision,
          parent=audit,
      )
    views.do_reindex()

  def test_basic_snapshot_query(self):
    """Test fetching all snapshots for a given Audit."""
    result = self._post([
        {
            "object_name": "Snapshot",
            "filters": {
                "expression": self._get_model_expression(),
                "keys": [],
                "order_by": {"keys": [], "order": "", "compare": None}
            }
        }
    ])
    self.assertEqual(len(result.json[0]["Snapshot"]["values"]), 5)

    result = self._post([
        {
            "object_name": "Snapshot",
            "filters": {
                "expression": self._get_model_expression("OrgGroup"),
                "keys": [],
                "order_by": {"keys": [], "order": "", "compare": None}
            }
        }
    ])
    self.assertEqual(len(result.json[0]["Snapshot"]["values"]), 5)

  def test_snapshot_attribute_filter(self):
    """Test filtering snapshots on object attributes."""
    market_title = models.Market.query.first().title
    result = self._post([
        {
            "object_name": "Snapshot",
            "filters": {
                "expression": {
                    "left": self._get_model_expression(),
                    "op": {"name": "AND"},
                    "right": {
                        "left": "title",
                        "op": {"name": "="},
                        "right": market_title,
                    },
                },
                "keys": [],
                "order_by": {"keys": [], "order": "", "compare": None}
            }
        }
    ])
    self.assertEqual(len(result.json[0]["Snapshot"]["values"]), 1)
    content = result.json[0]["Snapshot"]["values"][0]["revision"]["content"]
    self.assertEqual(
        content["title"],
        market_title,
    )

    result = self._post([
        {
            "object_name": "Snapshot",
            "filters": {
                "expression": {
                    "left": self._get_model_expression("OrgGroup"),
                    "op": {"name": "AND"},
                    "right": {
                        "left": "title",
                        "op": {"name": "!="},
                        "right": models.OrgGroup.query.first().title,
                    },
                },
                "keys": [],
                "order_by": {"keys": [], "order": "", "compare": None}
            }
        }
    ])
    self.assertEqual(len(result.json[0]["Snapshot"]["values"]), 4)

  def test_snapshot_ca_filter(self):
    """Test filtering snapshots on custom attributes."""
    result = self._post([
        {
            "object_name": "Snapshot",
            "filters": {
                "expression": {
                    "left": self._get_model_expression(),
                    "op": {"name": "AND"},
                    "right": {
                        "left": {
                            "left": "text cad",
                            "op": {"name": "="},
                            "right": "2016-11-01",  # one match
                        },
                        "op": {"name": "OR"},
                        "right": {
                            "left": "date cad",
                            "op": {"name": ">"},
                            "right": "2016-11-05",  # 2 matches
                        },
                    },
                },
                "keys": [],
                "order_by": {"keys": [], "order": "", "compare": None}
            }
        }
    ])
    self.assertEqual(len(result.json[0]["Snapshot"]["values"]), 3)

  @staticmethod
  def _get_model_expression(model_name="Market"):
    return {
        "left": {
            "left": "child_type",
            "op": {"name": "="},
            "right": model_name,
        },
        "op": {"name": "AND"},
        "right": {
            "object_name": "Audit",
            "op": {"name": "relevant"},
            "ids": [models.Audit.query.first().id]
        }
    }
