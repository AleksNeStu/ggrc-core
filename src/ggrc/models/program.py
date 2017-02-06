# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

from ggrc import db
from ggrc.models.context import HasOwnContext
from ggrc.models.mixins import BusinessObject
from ggrc.models.mixins import CustomAttributable
from ggrc.models.mixins import Timeboxed
from ggrc.models.deferred import deferred
from ggrc.models.object_owner import Ownable
from ggrc.models.object_person import Personable
from ggrc.models.reflection import AttributeInfo
from ggrc.models.relationship import Relatable
from ggrc.models.track_object_state import HasObjectState


class Program(HasObjectState, CustomAttributable,
              Personable, Relatable, HasOwnContext, Timeboxed,
              Ownable, BusinessObject, db.Model):
  __tablename__ = 'programs'

  KINDS = ['Directive']
  KINDS_HIDDEN = ['Company Controls Policy']

  kind = deferred(db.Column(db.String), 'Program')

  audits = db.relationship(
      'Audit', backref='program', cascade='all, delete-orphan')

  _publish_attrs = [
      'kind',
      'audits',
  ]
  _include_links = []
  _aliases = {
      "url": "Program URL",
      "owners": None,
      "program_owner": {
          "display_name": "Manager",
          "mandatory": True,
          "type": AttributeInfo.Type.USER_ROLE,
          "filter_by": "_filter_by_program_owner",
      },
      "program_editor": {
          "display_name": "Editor",
          "type": AttributeInfo.Type.USER_ROLE,
          "filter_by": "_filter_by_program_editor",
      },
      "program_reader": {
          "display_name": "Reader",
          "type": AttributeInfo.Type.USER_ROLE,
          "filter_by": "_filter_by_program_reader",
      },
  }

  @classmethod
  def _filter_by_program_owner(cls, predicate):
    return cls._filter_by_role("ProgramOwner", predicate)

  @classmethod
  def _filter_by_program_editor(cls, predicate):
    return cls._filter_by_role("ProgramEditor", predicate)

  @classmethod
  def _filter_by_program_reader(cls, predicate):
    return cls._filter_by_role("ProgramReader", predicate)

  @classmethod
  def eager_query(cls):
    from sqlalchemy import orm

    query = super(Program, cls).eager_query()
    return cls.eager_inclusions(query, Program._include_links).options(
        orm.subqueryload('audits'))
