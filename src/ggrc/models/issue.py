# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Issue Model."""

import itertools

from ggrc import builder
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
  _api_attrs = reflection.ApiAttributes(
      reflection.Attribute("audit", create=False, update=False),
      reflection.Attribute("allow_map_to_audit", create=False, update=False),
      reflection.Attribute("allow_unmap_from_audit",
                           create=False, update=False),
  )

  _aliases = {
      "test_plan": {
          "display_name": "Remediation Plan"
      },
      "status": {
          "display_name": "State",
          "mandatory": False,
          "description": "Options are: \n{} ".format('\n'.join(VALID_STATES))
      },
      "audit": None,
  }

  audit_id = deferred(
      db.Column(db.Integer, db.ForeignKey('audits.id'), nullable=True),
      'Issue')

  @builder.simple_property
  def allow_map_to_audit(self):
    """False if self.audit or self.audit_id is set, True otherwise."""
    return self.audit_id is None and self.audit is None

  @builder.simple_property
  def allow_unmap_from_audit(self):
    """False if Issue is mapped to any Assessment/Snapshot, True otherwise."""
    from ggrc.models import all_models

    restricting_types = {all_models.Assessment, all_models.Snapshot}
    restricting_types = set(m.__name__.lower() for m in restricting_types)

    # pylint: disable=not-an-iterable
    restricting_srcs = (rel.source_type.lower() in restricting_types
                        for rel in self.related_sources
                        if rel not in db.session.deleted)
    restricting_dsts = (rel.destination_type.lower() in restricting_types
                        for rel in self.related_destinations
                        if rel not in db.session.deleted)
    return not any(itertools.chain(restricting_srcs, restricting_dsts))
