# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Module for Objective model."""

from ggrc import db
from ggrc.access_control.roleable import Roleable
from ggrc.fulltext.mixin import Indexed
from ggrc.models.comment import Commentable
from .mixins import BusinessObject, CustomAttributable, TestPlanned
from .object_document import PublicDocumentable
from .object_person import Personable
from .audit_object import Auditable
from .track_object_state import HasObjectState
from .relationship import Relatable
from .mixins.with_last_assessment_date import WithLastAssessmentDate
from .mixins.with_similarity_score import WithSimilarityScore


class Objective(WithLastAssessmentDate, Roleable, HasObjectState,
                CustomAttributable, Auditable, Relatable, Personable,
                PublicDocumentable, Commentable, TestPlanned,
                WithSimilarityScore, BusinessObject, Indexed, db.Model):
  """Class representing Objective."""

  __tablename__ = 'objectives'
  _include_links = []
  _aliases = {
      "document_url": None,
      "document_evidence": None,
  }
