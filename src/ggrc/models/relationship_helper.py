# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Helper for getting related objects."""

from sqlalchemy import and_
from sqlalchemy import sql

from ggrc import db
from ggrc.extensions import get_extension_modules
from ggrc import models
from ggrc.models import Audit
from ggrc.models import Snapshot
from ggrc.models import all_models
from ggrc.models.relationship import Relationship
from ggrc.snapshotter.rules import Types


def program_audit(object_type, related_type, related_ids):
  if {object_type, related_type} != {"Program", "Audit"} or not related_ids:
    return None

  if object_type == "Program":
    return db.session.query(Audit.program_id).filter(
        Audit.id.in_(related_ids))
  else:
    return db.session.query(Audit.id).filter(
        Audit.program_id.in_(related_ids))


def person_withcontact(object_type, related_type, related_ids):
  object_model = getattr(models, object_type, None)
  related_model = getattr(models, related_type, None)
  if None in [object_model, related_model]:
    return None
  if object_model == models.Person:
    if issubclass(related_model, models.mixins.WithContact):
      return db.session.query(related_model.contact_id).filter(
          related_model.id.in_(related_ids)).union(
          db.session.query(related_model.secondary_contact_id).filter(
              related_model.id.in_(related_ids)))
    else:
      return None
  elif related_model == models.Person:
    if issubclass(object_model, models.mixins.WithContact):
      return db.session.query(object_model.id).filter(
          object_model.contact_id.in_(related_ids) |
          object_model.secondary_contact_id.in_(related_ids))
  else:
    return None


def acl_obj_id(object_type, related_type, related_ids, role=None):
  if object_type == "Person":
    return db.session.query(models.AccessControlList.person_id).filter(
        (models.AccessControlList.object_type == related_type) &
        (models.AccessControlList.object_id.in_(related_ids)) &
        (models.AccessControlRole.name == role if role else True)
    )
  elif related_type == "Person":
    return db.session.query(models.AccessControlList.object_id).filter(
        (models.AccessControlList.object_type == object_type) &
        (models.AccessControlList.person_id.in_(related_ids)) &
        (models.AccessControlRole.name == role if role else True)
    )
  else:
    return None


def person_object(object_type, related_type, related_ids):
  if "Person" not in [object_type, related_type]:
    return None
  if object_type == "Person":
    return db.session.query(models.ObjectPerson.person_id).filter(
        (models.ObjectPerson.personable_type == related_type) &
        (models.ObjectPerson.personable_id.in_(related_ids))
    )
  else:
    return db.session.query(models.ObjectPerson.personable_id).filter(
        (models.ObjectPerson.personable_type == object_type) &
        (models.ObjectPerson.person_id.in_(related_ids))
    )


def custom_attribute_mapping(object_type, related_type, related_ids):
  return db.session.query(models.CustomAttributeValue.attributable_id)\
      .filter(
          (models.CustomAttributeValue.attributable_type == object_type) &
          (models.CustomAttributeValue.attribute_value == related_type) &
          models.CustomAttributeValue.attribute_object_id.in_(related_ids))\
      .union(
      db.session.query(models.CustomAttributeValue.attribute_object_id)
      .filter(
          (models.CustomAttributeValue.attribute_value == object_type) &
          (models.CustomAttributeValue.attributable_type == related_type) &
          models.CustomAttributeValue.attributable_id.in_(related_ids)
      )
  )


def program_risk_assessment(object_type, related_type, related_ids):
  if {object_type, related_type} != {"Program", "RiskAssessment"} or \
          not related_ids:
    return None
  if object_type == "Program":
    return db.session.query(all_models.RiskAssessment.program_id).filter(
        all_models.RiskAssessment.id.in_(related_ids))
  else:
    return db.session.query(all_models.RiskAssessment.id).filter(
        all_models.RiskAssessment.program_id.in_(related_ids))


def task_group_object(object_type, related_type, related_ids):
  if not related_ids:
    return None
  if object_type == "TaskGroup":
    return db.session.query(all_models.TaskGroupObject.task_group_id).filter(
        (all_models.TaskGroupObject.object_type == related_type) &
        all_models.TaskGroupObject.object_id.in_(related_ids))
  elif related_type == "TaskGroup":
    return db.session.query(all_models.TaskGroupObject.object_id).filter(
        (all_models.TaskGroupObject.object_type == related_type) &
        all_models.TaskGroupObject.task_group_id.in_(related_ids))
  else:
    return None


def _audit_snapshot(object_type, related_type, related_ids):
  if {object_type, related_type} != {"Audit", "Snapshot"} or not related_ids:
    return None

  if object_type == "Audit":
    return db.session.query(Snapshot.parent_id).filter(
        Snapshot.id.in_(related_ids))
  else:
    return db.session.query(Snapshot.id).filter(
        Snapshot.parent_id.in_(related_ids))


def get_special_mappings(object_type, related_type, related_ids):
  return [
      _audit_snapshot(object_type, related_type, related_ids),
      person_object(object_type, related_type, related_ids),
      acl_obj_id(object_type, related_type, related_ids),
      person_withcontact(object_type, related_type, related_ids),
      program_audit(object_type, related_type, related_ids),
      program_risk_assessment(object_type, related_type, related_ids),
      task_group_object(object_type, related_type, related_ids),
      custom_attribute_mapping(object_type, related_type, related_ids),
  ]


def get_extension_mappings(object_type, related_type, related_ids):
  queries = []
  for extension in get_extension_modules():
    get_ids = getattr(extension, "contributed_get_ids_related_to", None)
    if callable(get_ids):
      queries.append(get_ids(object_type, related_type, related_ids))
  return queries


def _array_union(queries):
  """ Union of all valid queries in array """
  clean_queries = [q for q in queries if q]
  if not clean_queries:
    return db.session.query(Relationship.source_id).filter(sql.false())

  query = clean_queries.pop()
  return query.union(*clean_queries)


def _assessment_object_mappings(object_type, related_type, related_ids):
  """Get Object ids for audit scope objects and snapshotted objects."""

  if (object_type in Types.scoped | Types.trans_scope and
          related_type in Types.all):

    source_query = db.session.query(
        Relationship.destination_id.label("result_id"),
    ).join(
        Snapshot,
        and_(
            Relationship.source_id == Snapshot.id,
            Relationship.source_type == Snapshot.__name__,
            Relationship.destination_type == object_type,
            Snapshot.child_type == related_type,
            Snapshot.child_id.in_(related_ids),
        )
    )

    destination_query = db.session.query(
        Relationship.source_id.label("result_id"),
    ).join(
        Snapshot,
        and_(
            Relationship.destination_id == Snapshot.id,
            Relationship.destination_type == Snapshot.__name__,
            Relationship.source_type == object_type,
            Snapshot.child_type == related_type,
            Snapshot.child_id.in_(related_ids),
        )
    )

  elif (object_type in Types.all and
        related_type in Types.scoped | Types.trans_scope):
    source_query = db.session.query(
        Snapshot.child_id.label("result_id"),
    ).join(
        Relationship,
        and_(
            Relationship.source_id == Snapshot.id,
            Relationship.source_type == Snapshot.__name__,
            Relationship.destination_type == related_type,
            Relationship.destination_id.in_(related_ids),
            Snapshot.child_type == object_type,
        )
    )

    destination_query = db.session.query(
        Snapshot.child_id.label("result_id"),
    ).join(
        Relationship,
        and_(
            Relationship.destination_id == Snapshot.id,
            Relationship.destination_type == Snapshot.__name__,
            Relationship.source_type == related_type,
            Relationship.source_id.in_(related_ids),
            Snapshot.child_type == object_type,
        )
    )

  else:
    raise Exception(
        "Snapshot relationship called with invalid types.\n"
        "object types: '{}' - '{}'".format(object_type, related_type)
    )

  return source_query.union_all(destination_query)


def _parent_object_mappings(object_type, related_type, related_ids):
  """Get Object ids for audit and snapshotted object mappings."""

  if object_type in Types.parents and related_type in Types.all:
    query = db.session.query(Snapshot.parent_id).filter(
        Snapshot.parent_type == object_type,
        Snapshot.child_type == related_type,
        Snapshot.child_id.in_(related_ids)
    )
  elif related_type in Types.parents and object_type in Types.all:
    query = db.session.query(Snapshot.child_id).filter(
        Snapshot.parent_type == related_type,
        Snapshot.parent_id.in_(related_ids),
        Snapshot.child_type == object_type,
    )
  else:
    raise Exception(
        "Parent relationship called with invalid types.\n"
        "object types: '{}' - '{}'".format(object_type, related_type)
    )

  return query


def get_ids_related_to(object_type, related_type, related_ids=None):
  """ get ids of objects

  Get a list of all ids for object with object_type, that are related to any
  of the objects with type related_type and id in related_ids
  """

  if isinstance(related_ids, (int, long)):
    related_ids = [related_ids]

  if not related_ids:
    return db.session.query(Relationship.source_id).filter(sql.false())

  if (object_type in Types.scoped and related_type in Types.all or
          related_type in Types.scoped and object_type in Types.all):
    return _assessment_object_mappings(
        object_type, related_type, related_ids)

  if (object_type in Types.parents and related_type in Types.all or
          related_type in Types.parents and object_type in Types.all):
    return _parent_object_mappings(
        object_type, related_type, related_ids)

  destination_ids = db.session.query(Relationship.destination_id).filter(
      and_(
          Relationship.destination_type == object_type,
          Relationship.source_type == related_type,
          Relationship.source_id.in_(related_ids),
      )
  )
  source_ids = db.session.query(Relationship.source_id).filter(
      and_(
          Relationship.source_type == object_type,
          Relationship.destination_type == related_type,
          Relationship.destination_id.in_(related_ids),
      )
  )

  queries = [destination_ids, source_ids]
  queries.extend(get_extension_mappings(
      object_type, related_type, related_ids))
  queries.extend(get_special_mappings(
      object_type, related_type, related_ids))

  if (object_type in Types.trans_scope and related_type in Types.all or
          object_type in Types.all and related_type in Types.trans_scope):
    queries.append(_assessment_object_mappings(
        object_type, related_type, related_ids))

  return _array_union(queries)
