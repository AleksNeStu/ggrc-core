# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Module for full text index record builder."""

import logging

from ggrc import db
from ggrc.models import all_models
from ggrc.models.reflection import AttributeInfo
from ggrc.models.person import Person
from ggrc.models.mixins import CustomAttributable
from ggrc.fulltext.attributes import FullTextAttr
from ggrc.fulltext.mixin import Indexed


LOGGER = logging.getLogger(__name__)


class Record(object):  # pylint: disable=too-few-public-methods
  """"Class required to collection index properties on build procedure."""

  __slots__ = (
      "key",
      "type",
      "context_id",
      "tags",
      "properties",
  )

  def __init__(self,  # pylint: disable=too-many-arguments
               key,
               rec_type,
               context_id,
               properties,
               tags=""):
    self.key = key
    self.type = rec_type
    self.context_id = context_id
    self.tags = tags
    self.properties = properties


class RecordBuilder(object):
  """Basic record builder for full text index table."""
  # pylint: disable=too-few-public-methods

  def __init__(self, tgt_class, indexer):
    self._fulltext_attrs = AttributeInfo.gather_attrs(
        tgt_class, '_fulltext_attrs')
    self.indexer = indexer

  def _get_properties(self, obj):
    """Get indexable properties and values.

    Properties should be returned in the following format:
    {
      property1: {
        subproperty1: value1,
        subproperty2: value2,
        ...
      },
      ...
    }
    If there is no subproperty - empty string is used as a key
    """
    if obj.type == "Snapshot":
      # Snapshots do not have any indexable content. The object content for
      # snapshots is stored in the revision. Snapshots can also be made for
      # different models so we have to get fulltext attrs for the actual child
      # that was snapshotted and get data for those from the revision content.
      tgt_class = getattr(all_models, obj.child_type, None)
      if not tgt_class:
        return {}
      attrs = AttributeInfo.gather_attrs(tgt_class, '_fulltext_attrs')
      return {attr: {"": obj.revision.content.get(attr)} for attr in attrs}

    if isinstance(obj, Indexed):
      property_tmpl = obj.PROPERTY_TEMPLATE
    else:
      property_tmpl = u"{}"

    properties = {}
    for attr in self._fulltext_attrs:
      if isinstance(attr, basestring):
        properties[property_tmpl.format(attr)] = {"": getattr(obj, attr)}
      elif isinstance(attr, FullTextAttr):
        properties.update(attr.get_property_for(obj))
    return properties

  def get_person_id_name_email(self, person):
    """Get id, name and email for person (either object or dict).

    If there is a global people map, get the data from it instead of the DB.
    """
    if isinstance(person, dict):
      person_id = person["id"]
    else:
      person_id = person.id
    if person_id in self.indexer.cache['people_map']:
      person_name, person_email = self.indexer.cache['people_map'][person_id]
    else:
      if isinstance(person, dict):
        person = db.session.query(Person).filter_by(
            id=person["id"]
        ).one()
      person_id = person.id
      person_name = person.name
      person_email = person.email
      self.indexer.cache['people_map'][person_id] = (person_name, person_email)
    return person_id, person_name, person_email

  def get_ac_role_person_id(self, ac_list):
    """Get ac_role name and person name for ac_role (either object or dict).

    If there is a global ac_role map, get the data from it instead of the DB.
    """
    if isinstance(ac_list, dict):
      ac_role_id = ac_list["ac_role_id"]
      ac_person_id = ac_list["person_id"]
    else:
      ac_role_id = ac_list.role_id
      ac_person_id = ac_list.person_id
    if ac_role_id not in self.indexer.cache['ac_role_map']:
      ac_role = db.session.query(all_models.AccessControlRole).get(ac_role_id)
      ac_role_name = ac_role.name if ac_role else None
      self.indexer.cache['ac_role_map'][ac_role_id] = ac_role_name
      if ac_role_name is None:
        # index only existed role, if it have already been
        # removed than nothing to index.
        LOGGER.error("Trying to index not existing ACR with id %s", ac_role_id)
    ac_role_name = self.indexer.cache['ac_role_map'][ac_role_id]
    if ac_role_name:
      ac_role_name = ac_role_name.lower()
    return ac_role_name, ac_person_id

  def build_person_subprops(self, person):
    """Get dict of Person properties for fulltext indexing

    If Person provided by Revision, need to go to DB to get Person data
    """
    subproperties = {}
    person_id, person_name, person_email = self.get_person_id_name_email(
        person
    )
    subproperties["{}-name".format(person_id)] = person_name
    subproperties["{}-user_name".format(person_id)] = \
        person_email.split("@")[0]
    subproperties["{}-email".format(person_id)] = person_email
    return subproperties

  def build_list_sort_subprop(self, people):
    """Get a special subproperty for sorting.

    Its content is :-separated sorted list of (name or email) of the people in
    list.
    """
    if not people:
      return {"__sort__": ""}
    _, _, emails = zip(*(self.get_person_id_name_email(p) for p in people))
    sort_values = (email.split("@")[0] for email in emails)
    content = ":".join(sorted(sort_values))
    return {"__sort__": content}

  def get_custom_attribute_properties(self, definition, value):
    """Get property value in case of indexing CA
    """
    # The name of the attribute property needs to be unique for each object,
    # the value comes from the custom_attribute_value
    attribute_name = definition.title
    properties = {}
    if value and definition.attribute_type == "Map:Person":
      properties[attribute_name] = self.build_person_subprops(value)
      properties[attribute_name].update(self.build_list_sort_subprop([value]))
    else:
      properties[attribute_name] = {"": definition.get_indexed_value(value)}
    return properties

  def as_record(self, obj):  # noqa  # pylint:disable=too-many-branches
    """Generate record representation for an object.

    Properties should be returned in the following format:
    {
      property1: {
        subproperty1: value1,
        subproperty2: value2,
        ...
      },
      ...
    }
    If there is no subproperty - empty string is used as a key
    """
    # Defaults. These work when the record is not a custom attribute

    properties = self._get_properties(obj)
    if isinstance(obj, CustomAttributable):
      cavs = {v.custom_attribute_id: v for v in obj.custom_attribute_values}
      for cad in obj.custom_attribute_definitions:
        cav = cavs.get(cad.id)
        if not cav:
          value = cad.default_value
        elif cad.attribute_type == "Map:Person":
          value = cav.attribute_object if cav.attribute_object_id else None
        else:
          value = cav.attribute_value
        properties.update(self.get_custom_attribute_properties(cad, value))

    return Record(
        # This logic saves custom attribute values as attributes of the object
        # that owns the attribute values. When obj is not a
        # CustomAttributeValue the values are saved directly.
        obj.id,
        obj.__class__.__name__,
        obj.context_id,
        properties
    )
