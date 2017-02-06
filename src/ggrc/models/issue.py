# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

from ggrc import db
from .mixins import (
    BusinessObject, Timeboxed, CustomAttributable, TestPlanned
)
from .object_owner import Ownable
from .object_person import Personable
from .relationship import Relatable
from .track_object_state import HasObjectState


class Issue(HasObjectState, TestPlanned, CustomAttributable,
            Personable, Timeboxed, Ownable, Relatable,
            BusinessObject, db.Model):

  __tablename__ = 'issues'

  # REST properties
  _publish_attrs = [
  ]

  _aliases = {"url": "Issue URL"}
