# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""A mixin for objects that can be cloned"""

import itertools

import datetime

from collections import defaultdict

import sqlalchemy as sa

from werkzeug.exceptions import BadRequest

from ggrc import db
from ggrc.models import relationship, inflector
from ggrc.services import signals


# TODO: Clonning of Audit should be done with MultiClonable mixin and
# SingleClonable should be removed
class SingleClonable(object):
  """Clonable mixin"""

  __lazy_init__ = True

  CLONEABLE_CHILDREN = {}

  _operation_data = {}

  @classmethod
  def init(cls, model):
    cls.set_handlers(model)

  @classmethod
  def set_handlers(cls, model):
    """Set up handlers for cloning"""
    # pylint: disable=unused-argument, unused-variable
    @signals.Restful.collection_posted.connect_via(model)
    def handle_model_clone(sender, objects=None, sources=None):
      for obj, src in itertools.izip(objects, sources):
        if src.get("operation") == "clone":
          options = src.get("cloneOptions")
          mapped_objects = options.get("mappedObjects", [])
          source_id = int(options.get("sourceObjectId"))
          obj.clone(
              source_id=source_id,
              mapped_objects={obj for obj in mapped_objects
                              if obj in model.CLONEABLE_CHILDREN})

    @signals.Restful.model_posted_after_commit.connect_via(model)
    def handle_scope_clone(sender, obj=None, src=None, service=None,
                           event=None):
      if src.get("operation") == "clone":
        from ggrc.snapshotter import clone_scope

        options = src.get("cloneOptions")
        source_id = int(options.get("sourceObjectId"))
        base_object = model.query.get(source_id)
        clone_scope(base_object, obj, event)

  def generate_attribute(self, attribute):
    """Generate a new unique attribute as a copy of original"""
    attr = getattr(self, attribute)

    def count_values(key, value):
      return self.query.filter_by(**{key: value}).count()

    i = 1
    generated_attr_value = "{0} - copy {1}".format(attr, i)
    while count_values(attribute, generated_attr_value):
      i += 1
      generated_attr_value = "{0} - copy {1}".format(attr, i)
    return generated_attr_value

  def clone_custom_attribute_values(self, obj):
    """Copy object's custom attribute values"""
    ca_values = obj.custom_attribute_values

    for value in ca_values:
      value._clone(self)  # pylint: disable=protected-access

  def update_attrs(self, values):
    for key, value in values.items():
      setattr(self, key, value)


# TODO: This should be renamed to Clonable when Audit clone logic will be
# refactored and SingleClonable will be removed
class MultiClonable(object):
  """Clonable mixin"""

  CLONEABLE_CHILDREN = {}  # Types of related objects to clone with base one
  RETURN_OBJ_JSON = False  # Return json for created object

  @classmethod
  def _parse_query(cls, query):
    """Parse cloning parameters from input query.

    Args:
        query: Dict with cloning parameters.

    Returns:
        Tuple that include list objects to clone, destination object and
        list of possible mapped types (source_objs, destination, mapped_types).
    """
    if not query:
      raise BadRequest()

    source_ids = query.get("sourceObjectIds", [])
    if not source_ids:
      raise BadRequest("sourceObjectIds parameter wasn't provided")
    source_objs = cls.query.options(
        sa.orm.subqueryload('custom_attribute_definitions'),
        sa.orm.subqueryload('custom_attribute_values'),
    ).filter(cls.id.in_(source_ids)).all()

    dest_query = query.get("destination", {})
    destination = None
    if dest_query and dest_query.get("type") and dest_query.get("id"):
      destination_cls = inflector.get_model(dest_query.get("type"))
      destination = destination_cls.query.filter_by(
          id=dest_query.get("id")
      ).first()

    mapped_types = {
        type_ for type_ in query.get("mappedObjects", [])
        if type_ in cls.CLONEABLE_CHILDREN
    }
    return source_objs, destination, mapped_types

  @classmethod
  def handle_model_clone(cls, query):
    """Process cloning of objects.

    Args:
        query: Dict with parameters for cloning procedure. It should have
            following structure:
            {
              "sourceObjectIds": [1, 2],
              "destination": {"type": "Audit", "id": 2},  # optional
              "mappedObjects":[]  # optional
            }.

    Returns:
        Response with status code 200 in case of success and 400 if provided
        parameters are invalid.
    """
    source_objs, destination, mapped_types = cls._parse_query(query)

    clonned_objs = {}
    for source_obj in source_objs:
      clonned_objs[source_obj] = cls._clone_obj(source_obj, destination)

    for target, mapped_obj in cls._collect_mapped(source_objs, mapped_types):
      clonned_objs[mapped_obj] = cls._clone_obj(mapped_obj, target)

    cls._set_parent_context(clonned_objs.values(), destination)
    db.session.flush()

    for source, clonned in clonned_objs.items():
      cls._clone_cads(source, clonned)

    db.session.commit()

    from ggrc.query import views
    collections = []
    if cls.RETURN_OBJ_JSON:
      for obj in clonned_objs:
        collections.append(
            views.build_collection_representation(cls, obj.log_json())
        )
    return views.json_success_response(collections, datetime.datetime.now())

  @classmethod
  def _clone_obj(cls, source, target=None):
    """Make object copy of source into target as destination.

    Source will be cloned and mapped to target if it's provided.

    Args:
        source: Object that should be clonned.
        target: Destination for coppied object.

    Returns:
        Cloned object.
    """
    # _clone() should not be private, it will be refactored when Audit
    # migrate to new Clonable mixin
    # pylint: disable=protected-access
    clonned_object = source._clone()
    if target:
      db.session.add(relationship.Relationship(
          source=target,
          destination=clonned_object,
      ))
    return clonned_object

  @classmethod
  def _clone_cads(cls, source, target):
    """Clone CADs from source to target.

    Args:
        source: Object with CADs.
        target: Object in which CADs should be copied.
    """
    for cad in source.custom_attribute_definitions:
      # Copy only local CADs
      if cad.definition_id:
        # _clone() should not be private, it will be refactored when Audit
        # migrate to new Clonable mixin
        # pylint: disable=protected-access
        cad._clone(target)

  @classmethod
  def _collect_mapped(cls, source_objs, mapped_types):
    """Collect mapped objects.

    Args:
        source_objs: List of objects for which mapped should be collected.
        mapped_types: List of possible types of mapped objects.

    Returns:
        List of tuples containing source and mapped object
        [(source1, mapped1), (source2, mapped2), ...].
    """
    if not mapped_types:
      return []

    source_ids = {obj.id: obj for obj in source_objs}
    related_data = db.session.query(
        relationship.Relationship.source_id,
        relationship.Relationship.destination_type,
        relationship.Relationship.destination_id,
    ).filter(
        relationship.Relationship.source_type == cls.__name__,
        relationship.Relationship.source_id.in_(source_ids),
        relationship.Relationship.destination_type.in_(mapped_types)
    ).union_all(
        db.session.query(
            relationship.Relationship.destination_id,
            relationship.Relationship.source_type,
            relationship.Relationship.source_id,
        ).filter(
            relationship.Relationship.destination_type == cls.__name__,
            relationship.Relationship.destination_id.in_(source_ids),
            relationship.Relationship.source_type.in_(mapped_types)
        )
    ).all()

    related_objs = cls.load_objs([(id_, type_) for id_, type_ in related_data])
    source_related_objs = []
    for src_id, rel_type, rel_id in related_data:
      source_related_objs.append(
          (source_ids[src_id], related_objs[rel_type][rel_id])
      )
    return source_related_objs

  @classmethod
  def load_objs(cls, obj_stubs):
    """Load objects by their ids and types.

    Args:
        obj_stubs: List of stubs [(type, id),] for objects to load.

    Returns:
        Dict with object type and id as keys and instance as value.
    """
    # Combine ids of one type together to load them in one query
    type_ids = defaultdict(set)
    for type_, id_ in obj_stubs:
      type_ids[type_].add(id_)

    type_id_objs = defaultdict(dict)
    # We can't load all objects with different types in one step, so we
    # load them for each type separately
    for type_, ids in type_ids.items():
      related_model = inflector.get_model(type_)
      related_query = related_model.query.options(
          sa.orm.subqueryload('custom_attribute_definitions'),
      ).filter(related_model.id.in_(ids))
      for related in related_query:
        type_id_objs[type_][related.id] = related
    return type_id_objs

  @classmethod
  def _set_parent_context(cls, objs, parent):
    """Set up parent context to child objects.

    Args:
        clonned_objs: List of objects where context should be changed.
        parent: Parent object which determine context for children.
    """
    if not parent.context_id:
      return
    for clonned in objs:
      clonned.context_id = parent.context_id
