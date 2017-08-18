# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Integration tests for custom attribute definitions model."""

import ddt
import sqlalchemy.exc

from ggrc import db
from ggrc import views
from ggrc.models import all_models
from ggrc.fulltext import mysql
from integration.ggrc import TestCase
from integration.ggrc.models import factories

CAD = factories.CustomAttributeDefinitionFactory
CAV = factories.CustomAttributeValueFactory


@ddt.ddt
class TestCAD(TestCase):
  """Tests for basic functionality of cad model."""

  def test_cad_length(self):
    """Custom attribute titles must support all lengths that can be stored."""

    title1 = "a" * 200 + "1"
    title2 = "a" * 200 + "2"
    cad1 = CAD(title=title1, definition_type="market")
    cad2 = CAD(title=title2, definition_type="market",)
    factory = factories.MarketFactory()
    CAV(custom_attribute=cad1, attributable=factory, attribute_value="x")
    CAV(custom_attribute=cad2, attributable=factory, attribute_value="x")

    views.do_reindex()

    title1_count = mysql.MysqlRecordProperty.query.filter(
        mysql.MysqlRecordProperty.property == title1
    ).count()
    self.assertEqual(title1_count, 1)

  def test_type_cad(self):
    """Test CAD with the name 'type' """

    title1 = "type"
    cad1 = CAD(title=title1, definition_type="market")
    factory = factories.MarketFactory()
    CAV(custom_attribute=cad1, attributable=factory, attribute_value="x")

    views.do_reindex()

    title1_count = mysql.MysqlRecordProperty.query.filter(
        mysql.MysqlRecordProperty.property == title1
    ).count()
    self.assertEqual(title1_count, 1)

  @ddt.data(
      (True, "Yes"),
      (False, "No"),
      (1, "Yes"),
      (0, "No"),
      ("1", "Yes"),
      ("0", "No"),
  )
  @ddt.unpack
  def test_checkbox_fulltext(self, value, search_value):
    """Test filter by checkbox value."""

    title = "checkbox"
    checkbox_type = all_models.CustomAttributeDefinition.ValidTypes.CHECKBOX
    with factories.single_commit():
      market = factories.MarketFactory()
      cad = factories.CustomAttributeDefinitionFactory(
          title=title,
          definition_type="market",
          attribute_type=checkbox_type)
      factories.CustomAttributeValueFactory(
          custom_attribute=cad,
          attributable=market,
          attribute_value=value)

    views.do_reindex()

    contents = [
        i.content
        for i in mysql.MysqlRecordProperty.query.filter(
            mysql.MysqlRecordProperty.property == title,
            mysql.MysqlRecordProperty.type == market.type,
            mysql.MysqlRecordProperty.key == market.id,
        )
    ]
    self.assertEqual([search_value], contents)

  def test_checkbox_fulltext_no_cav(self):
    """Test filter by checkbox value without cav."""

    title = "checkbox"
    search_value = "No"
    checkbox_type = all_models.CustomAttributeDefinition.ValidTypes.CHECKBOX
    with factories.single_commit():
      market = factories.MarketFactory()
      factories.CustomAttributeDefinitionFactory(
          title=title,
          definition_type="market",
          attribute_type=checkbox_type)

    views.do_reindex()

    contents = [
        i.content
        for i in mysql.MysqlRecordProperty.query.filter(
            mysql.MysqlRecordProperty.property == title,
            mysql.MysqlRecordProperty.type == market.type,
            mysql.MysqlRecordProperty.key == market.id,
        )
    ]
    self.assertEqual([search_value], contents)

  def test_unique_key(self):
    """Test object property uniqueness."""
    db.session.add(mysql.MysqlRecordProperty(
        key=1,
        type="my_type",
        property=u"\u5555" * 240 + u"1",
    ))
    db.session.add(mysql.MysqlRecordProperty(
        key=1,
        type="my_type",
        property=u"\u5555" * 240 + u"2",
    ))
    db.session.commit()
    self.assertEqual(mysql.MysqlRecordProperty.query.count(), 2)

    with self.assertRaises(sqlalchemy.exc.IntegrityError):
      db.session.add(mysql.MysqlRecordProperty(
          key=1,
          type="my_type",
          property=u"\u5555" * 240 + u"2",
      ))
      db.session.commit()
