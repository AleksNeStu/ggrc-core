# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

from sqlalchemy.ext.declarative import declared_attr

from ggrc import db
from ggrc.models.associationproxy import association_proxy
from ggrc.models import mixins
from ggrc.models.deferred import deferred
from ggrc.models.object_owner import Ownable
from ggrc.models.object_person import Personable
from ggrc.models.reflection import PublishOnly
from ggrc.models.relationship import Relatable
from ggrc.models.track_object_state import HasObjectState


class Risk(HasObjectState, mixins.CustomAttributable, mixins.Stateful,
           Relatable, mixins.Described, Ownable, Personable,
           mixins.WithContact, mixins.Titled, mixins.Timeboxed,
           mixins.Noted, mixins.Hyperlinked, mixins.Slugged,
           db.Model):
  __tablename__ = 'risks'

  VALID_STATES = [
      'Draft',
      'Deprecated',
      'Active'
  ]

  # Overriding mixin to make mandatory
  @declared_attr
  def description(cls):
    return deferred(db.Column(db.Text, nullable=False), cls.__name__)

  risk_objects = db.relationship(
      'RiskObject', backref='risk', cascade='all, delete-orphan')
  objects = association_proxy('risk_objects', 'object', 'RiskObject')

  _publish_attrs = [
      'risk_objects',
      PublishOnly('objects'),
  ]

  _aliases = {
      "contact": {
          "display_name": "Contact",
          "filter_by": "_filter_by_contact",
      },
      "secondary_contact": None,
  }
