# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

from ggrc import db
from sqlalchemy.orm import validates
from ggrc.models.deferred import deferred
from ggrc.models.mixins import BusinessObject, Timeboxed, CustomAttributable
from ggrc.models.object_owner import Ownable
from ggrc.models.object_person import Personable
from ggrc.models.option import Option
from ggrc.models.relationship import Relatable
from ggrc.models.utils import validate_option
from ggrc.models.track_object_state import HasObjectState


class Product(HasObjectState, CustomAttributable, Personable,
              Relatable, Timeboxed, Ownable, BusinessObject, db.Model):
  __tablename__ = 'products'

  kind_id = deferred(db.Column(db.Integer), 'Product')
  version = deferred(db.Column(db.String), 'Product')

  kind = db.relationship(
      'Option',
      primaryjoin='and_(foreign(Product.kind_id) == Option.id, '
      'Option.role == "product_type")',
      uselist=False,
  )

  _publish_attrs = [
      'kind',
      'version',
  ]
  _sanitize_html = ['version', ]
  _aliases = {
      "url": "Product URL",
      "kind": {
          "display_name": "Kind/Type",
          "filter_by": "_filter_by_kind",
      },
  }

  @validates('kind')
  def validate_product_options(self, key, option):
    return validate_option(
        self.__class__.__name__, key, option, 'product_type')

  @classmethod
  def _filter_by_kind(cls, predicate):
    return Option.query.filter(
        (Option.id == cls.kind_id) & predicate(Option.title)
    ).exists()

  @classmethod
  def eager_query(cls):
    from sqlalchemy import orm

    query = super(Product, cls).eager_query()
    return query.options(orm.joinedload('kind'))
