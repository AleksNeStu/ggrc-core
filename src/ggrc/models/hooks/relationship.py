# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Relationship creation/modification hooks."""

from datetime import datetime

import itertools

import sqlalchemy as sa

from ggrc import db
from ggrc.services import signals
from ggrc.models import all_models
from ggrc.models.comment import Commentable
from ggrc.models.mixins import ChangeTracked
from ggrc.models import exceptions


def _handle_del_audit_issue_mapping(audit, issue):
  """Unset audit_id and context_id from issue if allowed else fail."""
  if issue in db.session.deleted:
    # the issue is being removed, no action needed
    return
  if audit not in db.session.deleted and not issue.allow_unmap_from_audit:
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
      if not instance.destination:
        # TODO: fix Document imports to make this impossible
        continue
      src, dst = order(instance.source, instance.destination)
      if is_audit_issue(src, dst):
        _handle_new_audit_issue_mapping(audit=src, issue=dst)

  for instance in session.deleted:
    if isinstance(instance, all_models.Relationship):
      src, dst = order(instance.source, instance.destination)
      if is_audit_issue(src, dst):
        _handle_del_audit_issue_mapping(audit=src, issue=dst)


def related_condition(obj, type_):
  """Get condition to select all relationships between objects"""
  return sa.or_(
      sa.and_(
          all_models.Relationship.source_id == obj.id,
          all_models.Relationship.source_type == obj.type,
          all_models.Relationship.destination_type == type_,
      ),
      sa.and_(
          all_models.Relationship.destination_id == obj.id,
          all_models.Relationship.destination_type == obj.type,
          all_models.Relationship.source_type == type_,
      )
  )


def related_to_other_condition(obj, other):
  """Get condition to select all relationships between
   objects except passed one"""
  return sa.or_(
      sa.and_(
          all_models.Relationship.source_id == obj.id,
          all_models.Relationship.source_type == obj.type,
          all_models.Relationship.destination_type == other.type,
          all_models.Relationship.destination_id != other.id,
      ),
      sa.and_(
          all_models.Relationship.destination_id == obj.id,
          all_models.Relationship.destination_type == obj.type,
          all_models.Relationship.source_type == other.type,
          all_models.Relationship.source_id != other.id,
      )
  )


def related_id(related_to_type, label):
  """Get source_id/destination_id related to provided type"""
  return sa.case(
      [(
          all_models.Relationship.source_type == related_to_type,
          all_models.Relationship.destination_id
      )],
      else_=all_models.Relationship.source_id
  ).label(label)


def unmap_issue_cascade(asmnt, issue):
  """Unmap issue cascade: unmap all Audits/Snapshots mapped both to Issue and
  Assessment and not mapped to any other Assessment
  """
  # All relationships of current Issue and Assessments except current one
  other_asmnts = db.session.query(related_id("Issue", "asmnt_id")).filter(
      related_to_other_condition(issue, asmnt)
  )

  other_asmnt_snap_ids = db.session.query(
      related_id("Assessment", "snapshot_id"),
  ).filter(
      sa.or_(
          sa.and_(
              all_models.Relationship.source_id.in_(other_asmnts),
              all_models.Relationship.source_type == "Assessment",
              all_models.Relationship.destination_type == "Snapshot",
          ),
          sa.and_(
              all_models.Relationship.destination_id.in_(other_asmnts),
              all_models.Relationship.destination_type == "Assessment",
              all_models.Relationship.source_type == "Snapshot",
          )
      )
  ).subquery()

  asmnt_snap_ids = db.session.query(
      related_id("Assessment", "snapshot_id"),
  ).filter(
      related_condition(asmnt, "Snapshot")
  ).subquery()

  # Find relationships between Snapshot and Issue to unmap
  snapshot_rels = all_models.Relationship.query.filter(
      sa.and_(
          related_condition(issue, "Snapshot"),
          related_id("Issue", "snapshot_id").in_(asmnt_snap_ids),
          ~related_id("Issue", "snapshot_id").in_(other_asmnt_snap_ids),
          all_models.Relationship.automapping_id.isnot(None),
      )
  )

  # If there are not any relationships between Issue and Assessment
  # except one we received in request, we can unmap Issue from Audit
  if not db.session.query(other_asmnts.exists()).scalar():
    audit_rels = all_models.Relationship.query.filter(
        sa.or_(
            sa.and_(
                all_models.Relationship.source_id == issue.id,
                all_models.Relationship.source_type == issue.type,
                all_models.Relationship.destination_type == issue.audit.type,
                all_models.Relationship.destination_id == issue.audit.id,
                all_models.Relationship.automapping_id.isnot(None),
            ),
            sa.and_(
                all_models.Relationship.source_id == issue.audit.id,
                all_models.Relationship.source_type == issue.audit.type,
                all_models.Relationship.destination_id == issue.id,
                all_models.Relationship.destination_type == issue.type,
                all_models.Relationship.automapping_id.isnot(None),
            )
        )
    )
  else:
    audit_rels = []

  for instance in itertools.chain(snapshot_rels, audit_rels):
    # this loop makes sure that before_flush hooks are executed
    db.session.delete(instance)


def init_hook():
  """Initialize Relationship-related hooks."""
  # pylint: disable=unused-variable
  sa.event.listen(all_models.Relationship, "before_insert",
                  all_models.Relationship.validate_attrs)
  sa.event.listen(all_models.Relationship, "before_update",
                  all_models.Relationship.validate_attrs)

  @signals.Restful.collection_posted.connect_via(all_models.Relationship)
  def handle_comment_mapping(sender, objects=None, **kwargs):
    """Update Commentable.updated_at when Comment mapped."""
    # pylint: disable=unused-argument
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

  @signals.Restful.model_deleted.connect_via(all_models.Relationship)
  def handle_cascade_delete(sender, obj, service):
    """Process cascade removing of relationship."""
    # pylint: disable=unused-argument
    is_asmnt_issue_rel = (
        obj.source_type == "Assessment" and
        obj.destination_type == "Issue"
    ) or (
        obj.source_type == "Issue" and
        obj.destination_type == "Assessment"
    )
    cascade = service.request.args.get("cascade")
    if cascade and cascade.lower() == "true" and is_asmnt_issue_rel:
      asmnt, issue = obj.source, obj.destination
      if asmnt.type != "Assessment":
        asmnt, issue = issue, asmnt

      unmap_issue_cascade(asmnt, issue)
