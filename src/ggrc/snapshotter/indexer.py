# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Manage indexing for snapshotter service"""

import logging
from collections import defaultdict
import itertools

from sqlalchemy.sql.expression import tuple_
from sqlalchemy import orm

from ggrc import db
from ggrc import models
from ggrc.models import all_models
from ggrc.fulltext.mysql import MysqlRecordProperty as Record
from ggrc.fulltext import get_indexer
from ggrc.models.reflection import AttributeInfo
from ggrc.utils import generate_query_chunks

from ggrc.snapshotter.rules import Types
from ggrc.snapshotter.datastructures import Pair
from ggrc.fulltext.attributes import FullTextAttr


LOGGER = logging.getLogger(__name__)


def _get_class_properties():
  """Get indexable properties for all models

  Args:
    None
  Returns:
    class_properties dict - representing a list of searchable attributes
                            for every model
  """
  class_properties = defaultdict(list)
  for klass_name in Types.all:
    full_text_attrs = AttributeInfo.gather_attrs(
        getattr(all_models, klass_name), '_fulltext_attrs'
    )
    for attr in full_text_attrs:
      if not isinstance(attr, FullTextAttr):
        attr = FullTextAttr(attr, attr)
      class_properties[klass_name].append(attr)
  return class_properties


CLASS_PROPERTIES = _get_class_properties()


TAG_TMPL = u"{parent_type}-{parent_id}-{child_type}"
PARENT_PROPERTY_TMPL = u"{parent_type}-{parent_id}"
CHILD_PROPERTY_TMPL = u"{child_type}-{child_id}"


def _get_custom_attribute_dict():
  """Get fulltext indexable properties for all snapshottable objects

  Args:
    None
  Returns:
    custom_attribute_definitions dict - representing dictionary of custom
                                        attribute definition attributes.
  """
  # pylint: disable=protected-access
  cadef_klass_names = {
      getattr(all_models, c)._inflector.table_singular: c for c in Types.all
  }

  query = models.CustomAttributeDefinition.query.filter(
      models.CustomAttributeDefinition.definition_type.in_(
          cadef_klass_names.keys()
      )
  )
  cads = defaultdict(list)
  for cad in query:
    cads[cadef_klass_names[cad.definition_type]].append(cad)
  return cads


def get_searchable_attributes(attributes, cads, content):
  """Get all searchable attributes for a given object that should be indexed

  Args:
    attributes: Attributes that should be extracted from some model
    cads: list of CAD instances
    content: dictionary (JSON) representation of an object
  Return:
    Dict of "key": "value" from objects revision
  """
  searchable_values = {}
  for attr in attributes:
    value = attr.get_attribute_revisioned_value(content)
    searchable_values[attr.alias] = value

  cav_dict = {v["custom_attribute_id"]: v
              for v in content.get("custom_attributes", [])}
  for cad in cads:
    cav = cav_dict.get(cad.id)
    if not cav:
      value = cad.default_value
    elif cad.attribute_type == "Map:Person":
      value = cav.get("attribute_object")
    else:
      value = cav["attribute_value"]
    searchable_values[cad.title] = cad.get_indexed_value(value)
  return searchable_values


def reindex():
  """Reindex all snapshots."""
  columns = db.session.query(
      models.Snapshot.parent_type,
      models.Snapshot.parent_id,
      models.Snapshot.child_type,
      models.Snapshot.child_id,
  )
  for query_chunk in generate_query_chunks(columns):
    pairs = {Pair.from_4tuple(p) for p in query_chunk}
    reindex_pairs(pairs)
    db.session.commit()


def reindex_snapshots(snapshot_ids):
  """Reindex selected snapshots"""
  if not snapshot_ids:
    return
  columns = db.session.query(
      models.Snapshot.parent_type,
      models.Snapshot.parent_id,
      models.Snapshot.child_type,
      models.Snapshot.child_id,
  ).filter(models.Snapshot.id.in_(snapshot_ids))
  for query_chunk in generate_query_chunks(columns):
    pairs = {Pair.from_4tuple(p) for p in query_chunk}
    reindex_pairs(pairs)
    db.session.commit()


def delete_records(snapshot_ids):
  """Delete all records for some snapshots.
  Args:
    snapshot_ids: An iterable with snapshot IDs whose full text records should
        be deleted.
  """
  db.session.query(Record).filter(
      Record.type == "Snapshot",
      Record.key.in_(snapshot_ids)
  ).delete(synchronize_session=False)
  db.session.commit()


def insert_records(payload):
  """Insert records to full text table.

  Args:
    payload: List of dictionaries that represent records entries.
  """
  engine = db.engine
  engine.execute(Record.__table__.insert(), payload)
  db.session.commit()


def get_person_data(rec, person):
  """Get list of Person properties for fulltext indexing
  """
  indexer = get_indexer()
  builder = indexer.get_builder(models.Person)
  subprops = builder.build_person_subprops(person)
  for key, val in subprops.items():
    newrec = rec.copy()
    newrec.update({"subproperty": key, "content": val})
    yield newrec


def get_person_sort_subprop(rec, people):
  """Get a special subproperty for sorting
  """
  indexer = get_indexer()
  builder = indexer.get_builder(models.Person)
  subprops = builder.build_list_sort_subprop(people)
  for key, val in subprops.items():
    newrec = rec.copy()
    newrec.update({"subproperty": key, "content": val})
    yield newrec


def get_access_control_role_data(rec, ac_list_item):
  """Get list of access control data for fulltext indexing
  """
  indexer = get_indexer()
  builder = indexer.get_builder(models.Person)
  ac_role_name, person_id = (builder.get_ac_role_person_id(ac_list_item))
  if ac_role_name:
    for key, val in builder.build_person_subprops({"id": person_id}).items():
      newrec = rec.copy()
      newrec.update({"property": ac_role_name,
                     "subproperty": key,
                     "content": val})
      yield newrec


def get_access_control_sort_subprop(rec, access_control_list):
  """Get a special access_control_list subproperty for sorting
  """
  builder = get_indexer().get_builder(models.Person)
  collection = defaultdict(list)
  for ac_list_item in access_control_list:
    ac_role_name, person_id = builder.get_ac_role_person_id(ac_list_item)
    if ac_role_name:
      collection[ac_role_name].append({"id": person_id})
  for ac_role_name, people in collection.iteritems():
    for prop in get_person_sort_subprop({"property": ac_role_name}, people):
      newrec = rec.copy()
      newrec.update(prop)
      yield newrec


def get_category_sort_subprop(rec, category_list):
  """Get a categories_list subproperty for sorting
  """
  newrec = rec.copy()
  newrec.update({
      "content": ":".join(sorted([c.get("display_name", None)
                                  for c in category_list])),
      "subproperty": "__sort__",
  })
  yield newrec


def get_category_data(rec, category_item):
  """Get category's name for fulltext indexing
  """
  newrec = rec.copy()
  newrec.update({
      "content": category_item.get("display_name"),
      "subproperty": "{}-category".format(category_item.get("id"))})
  yield newrec


def get_properties(snapshot):
  """Return properties for sent revision dict and pair object."""
  properties = snapshot["revision"].copy()
  properties.update({
      "parent": PARENT_PROPERTY_TMPL.format(**snapshot),
      "child": CHILD_PROPERTY_TMPL.format(**snapshot),
      "child_type": snapshot["child_type"],
      "child_id": snapshot["child_id"]
  })
  assignees = properties.pop("assignees", None) or []
  for person, roles in assignees:
    if person:
      for role in roles:
        properties[role] = [person]
  return properties


def get_record_value(prop, val, rec):
  """Return itearble object with record as element of that object."""
  if not prop or val is None:
    return []
  rec["property"] = prop
  rec["content"] = val
  # check custom values at first
  if isinstance(val, dict) and val.get("type") == "Person":
    return itertools.chain(get_person_data(rec, val),
                           get_person_sort_subprop(rec, [val]))
  if isinstance(val, list):
    if all([p.get("type") == "Person" for p in val]):
      sort_getter = get_person_sort_subprop
      item_getter = get_person_data
    elif prop == "access_control_list":
      sort_getter = get_access_control_sort_subprop
      item_getter = get_access_control_role_data
    elif prop in ("assertions", "categories"):
      sort_getter = get_category_sort_subprop
      item_getter = get_category_data
    else:
      return []
    results = [item_getter(rec, i) for i in val]
    results.append(sort_getter(rec, val))
    return itertools.chain(*results)
  if isinstance(val, dict) and "title" in val:
    rec["content"] = val["title"]
  if isinstance(val, (bool, int, long)):
    rec["content"] = unicode(val)
  if isinstance(rec["content"], basestring):
    return [rec]
  LOGGER.warning(u"Unsupported value for %s #%s in %s %s: %r",
                 rec["type"], rec["key"], rec["property"],
                 rec["subproperty"], rec["content"])
  return []


def reindex_pairs(pairs):
  """Reindex selected snapshots.

  Args:
    pairs: A list of parent-child pairs that uniquely represent snapshot
    object whose properties should be reindexed.
  """
  if not pairs:
    return
  snapshots = dict()
  snapshot_query = models.Snapshot.query.filter(
      tuple_(
          models.Snapshot.parent_type,
          models.Snapshot.parent_id,
          models.Snapshot.child_type,
          models.Snapshot.child_id,
      ).in_(
          {pair.to_4tuple() for pair in pairs}
      )
  ).options(
      orm.subqueryload("revision").load_only(
          "id",
          "resource_type",
          "resource_id",
          "_content",
      ),
      orm.load_only(
          "id",
          "context_id",
          "parent_type",
          "parent_id",
          "child_type",
          "child_id",
          "revision_id",
      )
  )
  cad_dict = _get_custom_attribute_dict()
  for snapshot in snapshot_query:
    revision = snapshot.revision
    snapshots[snapshot.id] = {
        "id": snapshot.id,
        "context_id": snapshot.context_id,
        "parent_type": snapshot.parent_type,
        "parent_id": snapshot.parent_id,
        "child_type": snapshot.child_type,
        "child_id": snapshot.child_id,
        "revision": get_searchable_attributes(
            CLASS_PROPERTIES[revision.resource_type],
            cad_dict[revision.resource_type],
            revision.content)
    }
  search_payload = []
  for snapshot in snapshots.values():
    for prop, val in get_properties(snapshot).items():
      search_payload.extend(
          get_record_value(
              prop,
              val,
              {
                  "key": snapshot["id"],
                  "type": "Snapshot",
                  "context_id": snapshot["context_id"],
                  "tags": TAG_TMPL.format(**snapshot),
                  "subproperty": "",
              }
          )
      )
  delete_records(snapshots.keys())
  insert_records(search_payload)
