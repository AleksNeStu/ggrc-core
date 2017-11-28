# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Relationship creation/modification hooks."""

from datetime import datetime
import functools
import logging
import itertools

from collections import defaultdict, namedtuple
import sqlalchemy as sa
from sqlalchemy.orm import Session

from ggrc import login, db
from ggrc.access_control.role import get_custom_roles_for
from ggrc.models.mixins.assignable import Assignable
from ggrc.models.relationship import Stub
from ggrc.services import signals
from ggrc.models import all_models
from ggrc.models.comment import Commentable
from ggrc.models.mixins import ChangeTracked
from ggrc.models import exceptions


LOGGER = logging.getLogger(__name__)


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


def _order(src, dst):
  """Sort parameters by classname and id."""
  return ((src, dst) if (src.type, src.id) < (dst.type, dst.id) else
          (dst, src))


def _is_audit_issue(src, dst):
  """Return True if src.type == "Audit" and dst.type == "Issue"."""
  return ((src.type, dst.type) ==
          (all_models.Audit.__name__, all_models.Issue.__name__))


def from_session(*models, **set_selectors):
  """Wrap session listener to run only for required models.

  Args:
    models: list of model classes, only instances of the provided types will
      be passed to the decorated function;
    set_selectors: allowed keys are "new", "dirty", "deleted", allowed values
      are bool, if you pass {"new": True} the matching objects from session.new
      will be passed to the decorated function.
  """

  new = set_selectors.get("new", False)
  dirty = set_selectors.get("dirty", False)
  deleted = set_selectors.get("deleted", False)

  def decorator(function):
    """Decorate function as inner."""
    @functools.wraps(function)
    def inner(session, flush_context, instances):
      """Call function with iterator of only needed items from session.

      flush_context and instances are ignored in the common case.
      """
      # pylint: disable=unused-argument
      sets = []
      if new:
        sets.append(session.new)
      if dirty:
        sets.append(session.dirty)
      if deleted:
        sets.append(session.deleted)

      items = (o for o in itertools.chain(*sets) if isinstance(o, models))

      return function(items)

    return inner

  return decorator


@from_session(all_models.Relationship, new=True, dirty=True)
def handle_new_audit_issue_mapping(instances):
  """Check and process new Audit-Issue mapping rules.

  Triggers rule processing functions for creation of Audit-Issue Relationships.
  """
  # pylint: disable=unused-argument

  for instance in instances:
    if not instance.source:
      # TODO: fix actions to make this impossible
      LOGGER.error(u"Relationship.source is not filled in properly: "
                   u"id=%r, source_id=%r, source_type=%r, "
                   u"destination_id=%r, destination_type=%r.",
                   instance.id, instance.source_id, instance.source_type,
                   instance.destination_id, instance.destination_type)
      continue
    if not instance.destination:
      # TODO: fix Document imports to make this impossible
      LOGGER.error(u"Relationship.destination is not filled in properly: "
                   u"id=%r, source_id=%r, source_type=%r, "
                   u"destination_id=%r, destination_type=%r.",
                   instance.id, instance.source_id, instance.source_type,
                   instance.destination_id, instance.destination_type)
      continue
    src, dst = _order(instance.source, instance.destination)
    if _is_audit_issue(src, dst):
      _handle_new_audit_issue_mapping(audit=src, issue=dst)


@from_session(all_models.Relationship, deleted=True)
def handle_del_audit_issue_mapping(instances):
  """Check and process deleted Audit-Issue mapping rules.

  Triggers rule processing functions for deletion of Audit-Issue Relationships.
  """
  for instance in instances:
    src, dst = _order(instance.source, instance.destination)
    if _is_audit_issue(src, dst):
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


def related(base_objects, rel_cache):
  """Get stubs of related objects

  Args:
    base_objects(list): Stubs of objects for which related objects
    should be collected
    rel_cache(RelationshipsCache): Instance of relationship cache

  Returns:
    Dict of base objects with their mappings
  """
  stubs = [o for o in base_objects if o not in rel_cache.cache]
  if stubs:
    rel_cache.populate_cache(stubs)

  return {o: rel_cache.cache[o] for o in base_objects if o in rel_cache.cache}


def related_regulation_snaps(snapshot_ids):
  """Collect all snapshots of Objective and Regulations mapped to
  snapshot of Control

  Args:
    snapshot_ids(list): Ids of snapshots of controls.

  Returns:
    Query with ids of control snapshot and mapped one.
  """
  related_snapshots = sa.union_all(
      db.session.query(
          all_models.Relationship.destination_id.label("base_snap_id"),
          all_models.Relationship.source_id.label("rel_snap_id"),
          all_models.Snapshot.child_type.label("child_type")
      ).join(
          all_models.Snapshot,
          sa.and_(
              all_models.Relationship.source_id == all_models.Snapshot.id,
              all_models.Relationship.source_type == "Snapshot",
              all_models.Relationship.destination_type == "Snapshot",
          )
      ),
      db.session.query(
          all_models.Relationship.source_id,
          all_models.Relationship.destination_id,
          all_models.Snapshot.child_type
      ).join(
          all_models.Snapshot,
          sa.and_(
              all_models.Relationship.destination_id == all_models.Snapshot.id,
              all_models.Relationship.source_type == "Snapshot",
              all_models.Relationship.destination_type == "Snapshot",
          )
      )
  ).alias("related_snapshots")

  return db.session.query(
      related_snapshots.c.base_snap_id,
      related_snapshots.c.rel_snap_id,
  ).join(
      all_models.Snapshot,
      related_snapshots.c.base_snap_id == all_models.Snapshot.id,
  ).filter(
      all_models.Snapshot.child_type == "Control",
      related_snapshots.c.base_snap_id.in_(snapshot_ids),
      related_snapshots.c.child_type.in_(["Objective", "Regulation"]),
  )


def add_related_snapshots(snapshot_ids, related_objects):
  """Get Stubs of Objective and Regulations snapshots mapped to
  snapshot of Control

  Args:
    snapshot_ids(dict): Ids of control snapshots with Stub of assigned object.
    related_objects(dict): Dict of base assigned objects with Stubs of related.
  """
  related_regulations = related_regulation_snaps(snapshot_ids.keys())
  for base_snap, related_snap in related_regulations:
    rel_snap_stub = Stub("Snapshot", related_snap)
    related_objects[snapshot_ids[base_snap]].add(rel_snap_stub)


def handle_relationship_creation(session, flush_context):
  """Create relations for mapped objects."""
  # pylint: disable=unused-argument
  base_objects = defaultdict(set)
  related_objects = defaultdict(set)
  snapshot_ids = {}
  for obj in session.new:
    if isinstance(obj, all_models.Relationship) and (
        issubclass(type(obj.source), Assignable) or
        issubclass(type(obj.destination), Assignable)
    ):
      assign_obj, other = obj.source, obj.destination
      if not issubclass(type(obj.source), Assignable):
        assign_obj, other = other, assign_obj
      for acl in assign_obj.access_control_list:
        acr_id = acl.ac_role.id if acl.ac_role else acl.ac_role_id
        ac_role = get_custom_roles_for(acl.object_type).get(acr_id, None)
        if ac_role in assign_obj.ASSIGNEE_TYPES:
          assign_stub = Stub(assign_obj.type, assign_obj.id)
          other_stub = Stub(other.type, other.id)
          base_objects[assign_stub].add(acl)
          related_objects[assign_stub].add(other_stub)

          if other.type == "Snapshot":
            snapshot_ids[other.id] = assign_stub

  if base_objects:
    if snapshot_ids:
      add_related_snapshots(snapshot_ids, related_objects)
    create_related_roles(base_objects, related_objects)


def get_mapped_role(object_type, acr_name, mapped_obj_type):
  """Get AC role that is mapped to provided one.

  Args:
    object_type(str): Type of object
    acr_name(str): Name of AC role
    mapped_obj_type(str): Type of mapped object

  Returns:
    Id of AC role with name '<Assignee type> Mapped' or
    '<Assignee type> Document Mapped' will be returned
  """
  obj_roles = {
      role_name: role_id
      for role_id, role_name in get_custom_roles_for(object_type).items()
  }
  doc_part = " Document" if mapped_obj_type == "Document" else ""
  return obj_roles.get("{}{} Mapped".format(acr_name, doc_part))


def create_related_roles(base_objects, related_objects):
  """Create mapped roles for related objects

  Args:
    base_objects(defaultdict(dict)): Objects which have Assignee role
    related_objects(defaultdict(set)): Objects related to assigned
  """
  if not base_objects or not related_objects:
    return

  acl_row = namedtuple(
      "acl_row", "person_id object_id object_type ac_role_id parent_id"
  )
  acl_parent = namedtuple("acl_parent", "context parent")
  acl_data = {}
  for base_stub, related_stubs in related_objects.items():
    for related_stub in related_stubs:
      for acl in base_objects[base_stub]:
        acr_id = acl.ac_role.id if acl.ac_role else acl.ac_role_id
        mapped_acr_id = get_mapped_role(
            base_stub.type,
            get_custom_roles_for(base_stub.type)[acr_id],
            related_stub.type
        )
        if not mapped_acr_id:
          raise Exception(
              "Mapped role wasn't found for role with "
              "id: {}".format(acl.ac_role_id)
          )
        acl_data[acl_row(
            acl.person_id or acl.person.id,
            related_stub.id,
            related_stub.type,
            mapped_acr_id,
            acl.id,
        )] = acl_parent(acl.context, acl)

  # Find existing acl instances in db
  existing_acls = set(db.session.query(
      all_models.AccessControlList.person_id,
      all_models.AccessControlList.object_id,
      all_models.AccessControlList.object_type,
      all_models.AccessControlList.ac_role_id,
      all_models.AccessControlList.parent_id,
  ).filter(
      sa.tuple_(
          all_models.AccessControlList.person_id,
          all_models.AccessControlList.object_id,
          all_models.AccessControlList.object_type,
          all_models.AccessControlList.ac_role_id,
          all_models.AccessControlList.parent_id,
      ).in_(acl_data.keys())
  ).all())
  # Find existing acl instances in session
  session_acls = {
      (
          a.person_id,
          a.object_id,
          a.object_type,
          a.ac_role_id,
          a.parent.id if a.parent else a.parent_id,
      ):
      (a.person_id, a.object_id, a.object_type, a.ac_role_id, a.parent)
      for a in db.session.new if isinstance(a, all_models.AccessControlList)
  }
  existing_acls.update(session_acls.keys())

  current_user_id = login.get_current_user_id()
  # Create new acl instance only if it absent in db and session
  for acl in set(acl_data.keys()) - existing_acls:
    # In some cases parent_id will be None, but parent object is not empty.
    # that's why we should additionally compare parent objects
    if (
        acl.person_id,
        acl.object_id,
        acl.object_type,
        acl.ac_role_id,
        acl_data[acl].parent
    ) not in session_acls.values():
      db.session.add(all_models.AccessControlList(
          person_id=acl.person_id,
          ac_role_id=acl.ac_role_id,
          object_id=acl.object_id,
          object_type=acl.object_type,
          context=acl_data[acl].context,
          modified_by_id=current_user_id,
          parent=acl_data[acl].parent,
      ))


def handle_relationship_delete(relationship):
  """Delete mapped AC roles if object unmapped from Assessment."""
  if (issubclass(type(relationship.source), Assignable) or
     issubclass(type(relationship.destination), Assignable)):
    assign_obj, other = relationship.source, relationship.destination
    if not issubclass(type(relationship.source), Assignable):
      assign_obj, other = other, assign_obj
    parent_ids = {acl.id for acl in assign_obj.access_control_list}
    db.session.query(all_models.AccessControlList).filter(
        all_models.AccessControlList.parent_id.in_(parent_ids),
        all_models.AccessControlList.object_type == other.type,
        all_models.AccessControlList.object_id == other.id,
    ).delete(synchronize_session='fetch')


def init_hook():
  """Initialize Relationship-related hooks."""
  # pylint: disable=unused-variable
  sa.event.listen(Session, "after_flush", handle_relationship_creation)

  @signals.Restful.model_deleted.connect_via(all_models.Relationship)
  def relationship_deleted_listener(sender, obj=None, src=None, service=None):
    """Process relationship removing."""
    # pylint: disable=unused-argument
    handle_relationship_delete(obj)

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
                  handle_new_audit_issue_mapping)
  sa.event.listen(sa.orm.session.Session, "before_flush",
                  handle_del_audit_issue_mapping)

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
