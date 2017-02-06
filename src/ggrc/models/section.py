# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

from ggrc import db
from ggrc.models.directive import Directive
from ggrc.models.mixins import CustomAttributable
from ggrc.models.mixins import Hierarchical
from ggrc.models.mixins import BusinessObject
from ggrc.models.deferred import deferred
from ggrc.models.object_owner import Ownable
from ggrc.models.object_person import Personable
from ggrc.models.reflection import AttributeInfo
from ggrc.models.relationship import Relatable
from ggrc.models.relationship import Relationship
from ggrc.models.track_object_state import HasObjectState


class Section(HasObjectState, Hierarchical, db.Model, CustomAttributable,
              Personable, Ownable, Relatable, BusinessObject):

  __tablename__ = 'sections'
  _table_plural = 'sections'
  _aliases = {
      "url": "Section URL",
      "description": "Text of Section",
      "directive": {
          "display_name": "Policy / Regulation / Standard / Contract",
          "type": AttributeInfo.Type.MAPPING,
          "filter_by": "_filter_by_directive",
      }
  }

  na = deferred(db.Column(db.Boolean, default=False, nullable=False),
                'Section')
  notes = deferred(db.Column(db.Text), 'Section')

  _publish_attrs = [
      'na',
      'notes',
  ]
  _sanitize_html = ['notes']
  _include_links = []

  @classmethod
  def _filter_by_directive(cls, predicate):
    types = ["Policy", "Regulation", "Standard", "Contract"]
    dst = Relationship.query \
        .filter(
            (Relationship.source_id == cls.id) &
            (Relationship.source_type == cls.__name__) &
            (Relationship.destination_type.in_(types))) \
        .join(Directive, Directive.id == Relationship.destination_id) \
        .filter(predicate(Directive.slug) | predicate(Directive.title)) \
        .exists()
    src = Relationship.query \
        .filter(
            (Relationship.destination_id == cls.id) &
            (Relationship.destination_type == cls.__name__) &
            (Relationship.source_type.in_(types))) \
        .join(Directive, Directive.id == Relationship.source_id) \
        .filter(predicate(Directive.slug) | predicate(Directive.title)) \
        .exists()
    return dst | src
