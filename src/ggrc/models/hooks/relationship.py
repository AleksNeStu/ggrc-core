# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Relationship creation/modification hooks."""

from datetime import datetime

import itertools

import sqlalchemy as sa

from ggrc.services import signals
from ggrc.models import all_models
from ggrc.models.comment import Commentable
from ggrc.models.mixins import ChangeTracked
from ggrc.models import exceptions


def _handle_del_audit_issue_mapping(audit, issue):
  """Unset audit_id and context_id from issue if allowed else fail."""
  if not issue.allow_unmap_from_audit:
    raise exceptions.ValidationError("Issue#{issue.id} can't be unmapped "
                                     "from Audit#{audit.id}: common mappings."
                                     .format(issue=issue, audit=audit))

  issue.audit = None
  issue.context = None


def _handle_new_audit_issue_mapping(audit, issue):
  """Set audit_id and context_id on issue if allowed else fail."""
  if not issue.allow_map_to_audit:
    raise exceptions.ValidationError(
        "Issue#{issue.id} can't be mapped to Audit#{audit.id}: already mapped "
        "to Audit#{mapped_audit_id}"
        .format(issue=issue, audit=audit,
                mapped_audit_id=issue.audit_id or issue.audit.id))

  issue.audit = audit
  issue.context = audit.context


def handle_audit_issue_mapping(session, flush_context, instances):
  """Check and process Audit-Issue mapping rules.

  Triggers rule processing functions for creation and deletion of
  Audit-Issue Relationships.
  """
  # pylint: disable=unused-argument

  def order(src, dst):
    return ((src, dst) if (src.type, src.id) < (dst.type, dst.id) else
            (dst, src))

  def is_audit_issue(src, dst):
    return ((src.type, dst.type) ==
            (all_models.Audit.__name__, all_models.Issue.__name__))

  for instance in itertools.chain(session.new, session.dirty):
    if isinstance(instance, all_models.Relationship):
      src, dst = order(instance.source, instance.destination)
      if is_audit_issue(src, dst):
        _handle_new_audit_issue_mapping(audit=src, issue=dst)

  for instance in session.deleted:
    if isinstance(instance, all_models.Relationship):
      src, dst = order(instance.source, instance.destination)
      if is_audit_issue(src, dst):
        _handle_del_audit_issue_mapping(audit=src, issue=dst)


def init_hook():
  """Initialize Relationship-related hooks."""
  sa.event.listen(all_models.Relationship, "before_insert",
                  all_models.Relationship.validate_attrs)
  sa.event.listen(all_models.Relationship, "before_update",
                  all_models.Relationship.validate_attrs)

  @signals.Restful.collection_posted.connect_via(all_models.Relationship)
  def handle_comment_mapping(sender, objects=None, **kwargs):
    """Update Commentable.updated_at when Comment mapped."""
    for obj in objects:
      if obj.source_type != u"Comment" and obj.destination_type != u"Comment":
        continue

      comment, other = obj.source, obj.destination
      if comment.type != u"Comment":
        comment, other = other, comment

      if isinstance(other, (Commentable, ChangeTracked)):
        other.updated_at = datetime.now()

  sa.event.listen(sa.orm.session.Session, "before_flush",
                  handle_audit_issue_mapping)
