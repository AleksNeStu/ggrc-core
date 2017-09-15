# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Issue Model."""

from ggrc import db
from ggrc.access_control.roleable import Roleable
from ggrc.models.deferred import deferred
from ggrc.models.mixins import (
    BusinessObject, LastDeprecatedTimeboxed, CustomAttributable, TestPlanned
)
from ggrc.models.mixins.audit_relationship import AuditRelationship
from ggrc.models.mixins.with_action import WithAction
from ggrc.models.object_document import PublicDocumentable
from ggrc.models.object_person import Personable
from ggrc.models.relationship import Relatable
from ggrc.models import reflection
from ggrc.models.track_object_state import HasObjectState
from ggrc.fulltext.mixin import Indexed


class Issue(Roleable, HasObjectState, TestPlanned, CustomAttributable,
            PublicDocumentable, Personable, LastDeprecatedTimeboxed,
            Relatable, AuditRelationship, WithAction, BusinessObject, Indexed,
            db.Model):
  """Issue Model."""

  __tablename__ = 'issues'

  FIXED = "Fixed"
  FIXED_AND_VERIFIED = "Fixed and Verified"

  VALID_STATES = BusinessObject.VALID_STATES + (FIXED, FIXED_AND_VERIFIED, )

  # REST properties
  _api_attrs = reflection.ApiAttributes("audit")

  _aliases = {
      "test_plan": {
          "display_name": "Remediation Plan"
      },
      "status": {
          "display_name": "State",
          "mandatory": False,
          "description": "Options are: \n{} ".format('\n'.join(VALID_STATES))
      },
  }

  audit_id = deferred(
      db.Column(db.Integer, db.ForeignKey('audits.id'), nullable=True),
      'Issue')
