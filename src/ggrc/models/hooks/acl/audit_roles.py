# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""All hooks required by audit roles business cases"""


from collections import defaultdict

import flask
import sqlalchemy as sa

from sqlalchemy.orm import load_only
from sqlalchemy.orm.session import Session
from sqlalchemy.sql.expression import true

from ggrc.models import all_models
from ggrc.models.relationship import Stub, RelationshipsCache
from ggrc.models.hooks.relationship import related


def _get_cache(expr, name):
  """Simple cache function"""
  try:
    result = getattr(flask.g, name)
  except AttributeError:
    # not cached yet
    result = expr()
    setattr(flask.g, name, result)
  return result


def _get_acl_audit_roles():
  """Cache captain and auditor roles"""
  return _get_cache(lambda: {
      role.name: role.id for role in
      all_models.AccessControlRole.query.filter(
          # We only load system roles and skip the ones created by users
          all_models.AccessControlRole.non_editable == true()
      ).options(
          load_only("id", "name")).all()
  }, "acl_audit_roles")


def _get_acr_id(acl):
  """Get acr id from acl object"""
  if acl.ac_role_id is not None:
    return acl.ac_role_id
  if acl.ac_role is not None:
    return acl.ac_role.id
  return None


class AccessControlListCache(object):  # pylint: disable=R0903
  """Access Control List helper"""
  def __init__(self):
    self.cache = set()

  def add(self, obj, parent, person, role_id):
    """Add new item if it wasn't already added"""
    key = (obj.id, obj.type, person.id, role_id, parent.id)
    if key in self.cache:
      return
    self.cache.add(key)
    acl = all_models.AccessControlList(
        object_id=obj.id,
        object_type=obj.type,
        parent=parent,
        person=person,
        ac_role_id=role_id)
    if hasattr(obj, "access_control_list"):
      obj.access_control_list.append(acl)


class AuditRolesHandler(object):
  """Handle audit role propagation"""

  def __init__(self):
    self.caches = {}

  def _create_mapped_acls(self, acl, role_map):
    """Helper to propagate roles for auditors and captains"""
    audit = acl.object
    assert isinstance(audit, all_models.Audit), \
        "`{}` role assigned to a non Audit object.".format(acl.ac_role.name)

    # Add Audit Captains Mapped role to all the objects in the audit
    snapshots_cache = self.caches["snapshots_cache"]
    acl_cache = self.caches["access_control_list_cache"]
    relationship_cache = self.caches["relationship_cache"]

    if audit.id not in snapshots_cache:
      snapshots_cache[audit.id] = all_models.Snapshot.query.filter(
          all_models.Snapshot.parent_id == audit.id,
          all_models.Snapshot.parent_type == "Audit"
      ).options(load_only("id")).all()

    for snapshot in snapshots_cache[audit.id]:
      acl_cache.add(snapshot, acl, acl.person, role_map["Snapshot"])

    # Add Audit Captains Mapped to all related
    audit_stub = Stub(acl.object_type, acl.object_id)
    related_stubs = related([audit_stub], relationship_cache)

    for stub in related_stubs[audit_stub]:
      if stub.type not in ("Assessment", "AssessmentTemplate", "Issue",
                           "Comment", "Document"):
        continue
      acl_cache.add(stub, acl, acl.person, role_map[stub.type])

    # Add Audit Captains Mapped to all realted comments and documents
    mapped_stubs = related(related_stubs[audit_stub], relationship_cache)
    for parent in mapped_stubs:
      for stub in mapped_stubs[parent]:
        if stub.type not in ("Comment", "Document"):
          continue
        acl_cache.add(stub, acl, acl.person, role_map[stub.type])

  def _auditors_handler(self, acl, audit_roles):
    """Handle auditor role propagation"""
    role_map = defaultdict(lambda: audit_roles['Auditors Mapped'], {
        "Snapshot": audit_roles["Auditors Snapshot Mapped"],
        "Assessment": audit_roles["Auditors Assessment Mapped"],
        "Issue": audit_roles["Auditors Issue Mapped"],
        "Document": audit_roles["Auditors Document Mapped"]
    })
    self._create_mapped_acls(acl, role_map)

  def _audit_captains_handler(self, acl, audit_roles):
    """Handle audit captain permission added"""
    audit = acl.object
    assert isinstance(audit, all_models.Audit), \
        "`Audit Captains` role assigned to a non Audit object."

    # Add program editor to program
    program = audit.program
    if not any(pacl for pacl in program.access_control_list
               if pacl.person == acl.person):
      acl_cache = self.caches["access_control_list_cache"]
      acl_cache.add(program, acl, acl.person, audit_roles["Program Editors"])

    role_map = defaultdict(lambda: audit_roles['Audit Captains Mapped'])
    self._create_mapped_acls(acl, role_map)

  def handle_access_control_list(self, obj):
    """Handle Access Control List creation"""
    audit_roles = _get_acl_audit_roles()
    role_handlers = {
        audit_roles["Audit Captains"]: self._audit_captains_handler,
        audit_roles["Auditors"]: self._auditors_handler,
    }
    if obj.ac_role_id in role_handlers:
      role_handlers[obj.ac_role_id](obj, audit_roles)

  def handle_snapshot(self, obj):
    """Handle snapshot creation"""
    audit_roles = _get_acl_audit_roles()
    access_control_list = obj.parent.access_control_list
    role_map = {
        audit_roles["Auditors"]: audit_roles["Auditors Snapshot Mapped"],
        audit_roles["Audit Captains"]: audit_roles["Audit Captains Mapped"]
    }
    for acl in access_control_list:
      if acl.ac_role.id not in role_map:
        continue
      acl_cache = self.caches["access_control_list_cache"]
      acl_cache.add(obj, acl, acl.person, role_map[acl.ac_role.id])

  def handle_relationship(self, obj):
    """Handle relationship creation"""
    first, second = sorted([obj.source, obj.destination], key=lambda o: o.type)
    if isinstance(first, all_models.Audit):
      audit, other = first, second
      access_control_list = audit.access_control_list
    elif isinstance(first, (all_models.Assessment,
                            all_models.AssessmentTemplate)):
      if isinstance(second, all_models.Audit):
        audit, other = second, first
        access_control_list = audit.access_control_list
      else:
        assessment, other = first, second
        access_control_list = assessment.access_control_list
    elif (isinstance(first, (all_models.Comment, all_models.Document)) and
          isinstance(second, all_models.Issue)):
      access_control_list = second.access_control_list
      other = first
    else:
      return

    if not isinstance(other, (all_models.Assessment,
                              all_models.AssessmentTemplate,
                              all_models.Audit,
                              all_models.Issue,
                              all_models.Snapshot,
                              all_models.Document,
                              all_models.Comment)):
      return

    audit_roles = _get_acl_audit_roles()
    auditors_mapped_dict = defaultdict(
        lambda: audit_roles["Auditors Mapped"], {
            all_models.Assessment: audit_roles["Auditors Assessment Mapped"],
            all_models.AssessmentTemplate: audit_roles["Auditors Mapped"],
            all_models.Document: audit_roles["Auditors Document Mapped"],
            all_models.Issue: audit_roles["Auditors Issue Mapped"],
            all_models.Comment: audit_roles["Auditors Mapped"],
        })
    role_map = {
        audit_roles["Auditors"]: auditors_mapped_dict,
        audit_roles["Audit Captains"]: defaultdict(
            lambda: audit_roles["Audit Captains Mapped"]),
        audit_roles["Audit Captains Mapped"]: defaultdict(
            lambda: audit_roles["Audit Captains Mapped"]),
        audit_roles["Auditors Assessment Mapped"]: auditors_mapped_dict,
        audit_roles["Auditors Issue Mapped"]: auditors_mapped_dict,
    }
    for acl in access_control_list:
      ac_role_id = _get_acr_id(acl)
      if ac_role_id not in role_map:
        continue
      acl_cache = self.caches["access_control_list_cache"]
      acl_cache.add(other, acl, acl.person,
                    role_map[ac_role_id][type(other)])

  def after_flush(self, session, _):
    """Handle legacy audit captain -> program editor role propagation"""
    self.caches = {
        "relationship_cache": RelationshipsCache(),
        "snapshots_cache": {},
        "access_control_list_cache": AccessControlListCache()
    }
    handlers = {
        all_models.AccessControlList: self.handle_access_control_list,
        all_models.Snapshot: self.handle_snapshot,
        all_models.Relationship: self.handle_relationship,
    }
    for obj in session.new:
      handler = handlers.get(type(obj))
      if callable(handler):
        handler(obj)


def init_hook():
  """Initialize AccessControlList-related hooks."""
  handler = AuditRolesHandler()
  sa.event.listen(Session, "after_flush", handler.after_flush)
