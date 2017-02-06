# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

from ggrc import db
from ggrc.models.mixins import CustomAttributable
from ggrc.models.mixins import Described
from ggrc.models.mixins import Noted
from ggrc.models.mixins import Slugged
from ggrc.models.mixins import Timeboxed
from ggrc.models.mixins import Titled
from ggrc.models.deferred import deferred
from ggrc.models.object_document import Documentable
from ggrc.models.person import Person
from ggrc.models.program import Program
from ggrc.models.relationship import Relatable


class RiskAssessment(Documentable, Timeboxed, Noted, Described,
                     CustomAttributable, Titled, Relatable, Slugged, db.Model):
  __tablename__ = 'risk_assessments'
  _title_uniqueness = False

  ra_manager_id = deferred(
      db.Column(db.Integer, db.ForeignKey('people.id')), 'RiskAssessment')
  ra_manager = db.relationship(
      'Person', uselist=False, foreign_keys='RiskAssessment.ra_manager_id')

  ra_counsel_id = deferred(
      db.Column(db.Integer, db.ForeignKey('people.id')), 'RiskAssessment')
  ra_counsel = db.relationship(
      'Person', uselist=False, foreign_keys='RiskAssessment.ra_counsel_id')

  program_id = deferred(
      db.Column(db.Integer, db.ForeignKey('programs.id'), nullable=False),
      'RiskAssessment')
  program = db.relationship(
      'Program',
      backref='risk_assessments',
      uselist=False,
      foreign_keys='RiskAssessment.program_id')

  _fulltext_attrs = []

  _publish_attrs = [
      'ra_manager',
      'ra_counsel',
      'program',
  ]

  _aliases = {
      "ra_manager": {
          "display_name": "Risk Manager",
          "filter_by": "_filter_by_risk_manager",
      },
      "ra_counsel": {
          "display_name": "Risk Counsel",
          "filter_by": "_filter_by_risk_counsel",
      },
      "start_date": {
          "display_name": "Start Date",
          "mandatory": True,
      },
      "end_date": {
          "display_name": "End Date",
          "mandatory": True,
      },
      "program": {
          "display_name": "Program",
          "mandatory": True,
          "filter_by": "_filter_by_program",
      }
  }

  @classmethod
  def _filter_by_program(cls, predicate):
    return Program.query.filter(
        (Program.id == cls.program_id) &
        (predicate(Program.slug) | predicate(Program.title))
    ).exists()

  @classmethod
  def _filter_by_risk_manager(cls, predicate):
    return Person.query.filter(
        (Person.id == cls.ra_manager_id) &
        (predicate(Person.name) | predicate(Person.email))
    ).exists()

  @classmethod
  def _filter_by_risk_counsel(cls, predicate):
    return Person.query.filter(
        (Person.id == cls.ra_counsel_id) &
        (predicate(Person.name) | predicate(Person.email))
    ).exists()
