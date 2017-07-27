# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Module containing custom attributable mixin."""

import collections
from logging import getLogger

import cached_property

from sqlalchemy import and_
from sqlalchemy import orm
from sqlalchemy import or_
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import foreign
from sqlalchemy.orm import relationship

from ggrc import builder
from ggrc import db
from ggrc import utils
from ggrc.models import reflection


# pylint: disable=invalid-name
logger = getLogger(__name__)


# pylint: disable=attribute-defined-outside-init; CustomAttributable is a mixin
class CustomAttributable(object):
  """Custom Attributable mixin."""

  _api_attrs = reflection.ApiAttributes(
      'global_attributes',
      'local_attributes',
      reflection.Attribute('custom_attribute_values',
                           create=False,
                           update=False),
      reflection.Attribute('custom_attribute_definitions',
                           create=False,
                           update=False),
      reflection.Attribute('preconditions_failed',
                           create=False,
                           update=False),
      reflection.Attribute('custom_attributes', read=False),
  )
  _include_links = ["custom_attribute_values", "custom_attribute_definitions"]
  _update_raw = ['local_attributes', 'global_attributes']

  @declared_attr
  def custom_attribute_definitions(cls):  # pylint: disable=no-self-argument
    """Load custom attribute definitions"""
    from ggrc.models.custom_attribute_definition\
        import CustomAttributeDefinition

    def join_function():
      """Object and CAD join function."""
      definition_id = foreign(CustomAttributeDefinition.definition_id)
      definition_type = foreign(CustomAttributeDefinition.definition_type)
      return and_(or_(definition_id == cls.id, definition_id.is_(None)),
                  definition_type == cls._inflector.table_singular)

    return relationship(
        "CustomAttributeDefinition",
        primaryjoin=join_function,
        backref='{0}_custom_attributable_definition'.format(cls.__name__),
        order_by=(CustomAttributeDefinition.definition_id.desc(),
                  CustomAttributeDefinition.id.asc()),
        viewonly=True,
    )

  @declared_attr
  def _custom_attributes_deletion(cls):  # pylint: disable=no-self-argument
    """This declared attribute is used only for handling cascade deletions
       for CustomAttributes. This is done in order not to try to delete
       "global" custom attributes that don't have any definition_id related.
       Attempt to delete custom attributes with definition_id=None causes the
       IntegrityError as we shouldn't be able to delete global attributes along
       side with any other object (e.g. Assessments).
    """
    from ggrc.models.custom_attribute_definition import (
        CustomAttributeDefinition
    )

    def join_function():
      """Join condition used for deletion"""
      definition_id = foreign(CustomAttributeDefinition.definition_id)
      definition_type = foreign(CustomAttributeDefinition.definition_type)
      return and_(definition_id == cls.id,
                  definition_type == cls._inflector.table_singular)

    return relationship(
        "CustomAttributeDefinition",
        primaryjoin=join_function,
        cascade='all, delete-orphan',
        order_by="CustomAttributeDefinition.id"
    )

  @property
  def local_cads(self):
    return [d for d in self.custom_attribute_definitions if d.is_local]

  @property
  def global_cads(self):
    return [d for d in self.custom_attribute_definitions if not d.is_local]

  @declared_attr
  def _custom_attribute_values(cls):  # pylint: disable=no-self-argument
    """Load custom attribute values"""
    from ggrc.models.custom_attribute_value import CustomAttributeValue

    def join_function():
      return and_(
          foreign(CustomAttributeValue.attributable_id) == cls.id,
          foreign(CustomAttributeValue.attributable_type) == cls.__name__)
    return relationship(
        "CustomAttributeValue",
        primaryjoin=join_function,
        backref='{0}_custom_attributable'.format(cls.__name__),
        cascade='all, delete-orphan',
    )

  def _api_custom_attributes(self, definitions):
    """Api like getter for CAVs instances."""
    vals = collections.defaultdict(list)
    defs = {d.id for d in definitions}
    for value in self.custom_attribute_values:
      if value.custom_attribute_id in defs:
        vals[value.custom_attribute_id].append(value)
    results = []
    for definition in definitions:
      if definition.attribute_type.startswith("Map:"):
        attribute_name = "attribute_object_id"
      else:
        attribute_name = "attribute_value"
      is_preconditions_failed = False
      values = []
      for val in vals[definition.id]:
        val_preconditions_failed = val.preconditions_failed
        values.append({"id": val.id,
                       "value": getattr(val, attribute_name),
                       "preconditions_failed": val_preconditions_failed})
        if not is_preconditions_failed:
          is_preconditions_failed = any(val_preconditions_failed.values())
      if not is_preconditions_failed:
        is_preconditions_failed = bool(definition.mandatory and not values)
      defenition_json = definition.log_json()
      defenition_json["values"] = values
      defenition_json["is_preconditions_failed"] = is_preconditions_failed
      results.append(defenition_json)
    return results

  def _api_custom_attributes_setter(self, value, definitions):
    """Api like setter for CAVs instances."""
    from ggrc.models.custom_attribute_value import CustomAttributeValue
    value = value or []
    defs = {d.id: d for d in definitions}
    vals = {v.id: v for v in self.custom_attribute_values
            if v.custom_attribute_id in defs}
    for data in value:
      try:
        definition = defs[data["id"]]
      except KeyError:
        raise ValueError("You try to setup invalid custom attribute value")
      mapping_type = None
      if definition.attribute_type.startswith("Map:"):
        mapping_type = definition.attribute_type[4:]
      for val in data['values']:
        attr_val = val['value']
        if mapping_type:
          attr_val = "{}:{}".format(mapping_type, attr_val)
        if val.get("id"):
          vals[int(val['id'])].attribute_value = attr_val
        else:
          # if value doesn't exists then create new value
          CustomAttributeValue(
              custom_attribute=definition,
              attributable=self,
              attribute_value=attr_val,
              context=self.context,
          )

  @builder.simple_property
  def local_attributes(self):
    return self._api_custom_attributes(self.local_cads)

  @local_attributes.setter
  def local_attributes(self, value):
    return self._api_custom_attributes_setter(value, self.local_cads)

  @builder.simple_property
  def global_attributes(self):
    return self._api_custom_attributes(self.global_cads)

  @global_attributes.setter
  def global_attributes(self, value):
    return self._api_custom_attributes_setter(value, self.global_cads)

  @hybrid_property
  def custom_attribute_values(self):
    return self._custom_attribute_values

  @classmethod
  def indexed_query(cls):
    return super(CustomAttributable, cls).indexed_query().options(
        orm.Load(cls).subqueryload(
            "custom_attribute_values"
        ).joinedload(
            "custom_attribute"
        ).undefer_group(
            "CustomAttributeDefinition_complete",
        ),
        orm.Load(cls).subqueryload(
            "custom_attribute_values"
        ).undefer_group(
            "CustomAttributeValue_complete",
        ),
    )

  def insert_definition(self, definition):
    """Insert a new custom attribute definition into database

    Args:
      definition: dictionary with field_name: value
    """
    from ggrc.models.custom_attribute_definition \
        import CustomAttributeDefinition
    field_names = reflection.AttributeInfo.gather_create_attrs(
        CustomAttributeDefinition)

    data = {fname: definition.get(fname) for fname in field_names}
    data["definition_type"] = self._inflector.table_singular
    cad = CustomAttributeDefinition(**data)
    db.session.add(cad)

  def process_definitions(self, definitions):
    """
    Process custom attribute definitions

    If present, delete all related custom attribute definition and insert new
    custom attribute definitions in the order provided.

    Args:
      definitions: Ordered list of (dict) custom attribute definitions
    """
    from ggrc.models.custom_attribute_definition \
        import CustomAttributeDefinition as CADef

    if not hasattr(self, "PER_OBJECT_CUSTOM_ATTRIBUTABLE"):
      return

    if self.id is not None:
      db.session.query(CADef).filter(
          CADef.definition_id == self.id,
          CADef.definition_type == self._inflector.table_singular
      ).delete()
      db.session.flush()
      db.session.expire_all()

    for definition in definitions:
      if "_pending_delete" in definition and definition["_pending_delete"]:
        continue

      definition['context'] = getattr(self, "context", None)
      self.insert_definition(definition)

  def _remove_existing_items(self, attr_values):
    """Remove existing CAV and corresponding full text records."""
    from ggrc.fulltext.mysql import MysqlRecordProperty
    from ggrc.models.custom_attribute_value import CustomAttributeValue
    if not attr_values:
      return
    # 2) Delete all fulltext_record_properties for the list of values
    ftrp_properties = []
    for val in attr_values:
      ftrp_properties.append(val.custom_attribute.title)
      if val.custom_attribute.attribute_type == "Map:Person":
        ftrp_properties.append(val.custom_attribute.title + ".name")
        ftrp_properties.append(val.custom_attribute.title + ".email")
    db.session.query(MysqlRecordProperty)\
        .filter(
            and_(
                MysqlRecordProperty.key == self.id,
                MysqlRecordProperty.type == self.__class__.__name__,
                MysqlRecordProperty.property.in_(ftrp_properties)))\
        .delete(synchronize_session='fetch')

    # 3) Delete the list of custom attribute values
    attr_value_ids = [value.id for value in attr_values]
    db.session.query(CustomAttributeValue)\
        .filter(CustomAttributeValue.id.in_(attr_value_ids))\
        .delete(synchronize_session='fetch')
    db.session.commit()

  def custom_attributes(self, src):
    """Legacy setter for custom attribute values and definitions.

    This code should only be used for custom attribute definitions until
    setter for that is updated.
    """
    from ggrc.models.custom_attribute_value import CustomAttributeValue
    from ggrc.services import signals

    if any(f in src for f in ["local_attributes", 'global_attributes']):
      # This indicates that the new CA API is being used and the legacy API
      # should be ignored. If we need to use the legacy API the
      # custom_attribute_values property should contain stubs instead of entire
      # objects.
      return

    definitions = src.get("custom_attribute_definitions")
    if definitions:
      self.process_definitions(definitions)

    attributes = src.get("custom_attributes")
    if not attributes:
      return

    old_values = collections.defaultdict(list)
    last_values = dict()

    # attributes looks like this:
    #    [ {<id of attribute definition> : attribute value, ... }, ... ]

    # 1) Get all custom attribute values for the CustomAttributable instance
    attr_values = db.session.query(CustomAttributeValue).filter(and_(
        CustomAttributeValue.attributable_type == self.__class__.__name__,
        CustomAttributeValue.attributable_id == self.id)).all()

    # Save previous value of custom attribute. This is a bit complicated by
    # the fact that imports can save multiple values at the time of writing.
    # old_values holds all previous values of attribute, last_values holds
    # chronologically last value.
    for value in attr_values:
      old_values[value.custom_attribute_id].append(
          (value.created_at, value.attribute_value))

    last_values = {str(key): max(old_vals,
                                 key=lambda (created_at, _): created_at)
                   for key, old_vals in old_values.iteritems()}

    self._remove_existing_items(attr_values)

    # 4) Instantiate custom attribute values for each of the definitions
    #    passed in (keys)
    # pylint: disable=not-an-iterable
    # filter out attributes like Person:None
    attributes = {k: v for k, v in attributes.items() if v != "Person:None"}
    definitions = {d.id: d for d in self.get_custom_attribute_definitions()}
    for ad_id in attributes.keys():
      obj_type = self.__class__.__name__
      obj_id = self.id
      new_value = CustomAttributeValue(
          custom_attribute=definitions[int(ad_id)],
          custom_attribute_id=int(ad_id),
          attributable=self,
          attribute_value=attributes[ad_id],
      )
      if definitions[int(ad_id)].attribute_type.startswith("Map:"):
        obj_type, obj_id = new_value.attribute_value.split(":")
        new_value.attribute_value = obj_type
        new_value.attribute_object_id = long(obj_id)
      elif definitions[int(ad_id)].attribute_type == "Checkbox":
        new_value.attribute_value = "1" if new_value.attribute_value else "0"

      # 5) Set the context_id for each custom attribute value to the context id
      #    of the custom attributable.
      # TODO: We are ignoring contexts for now
      # new_value.context_id = cls.context_id

      # new value is appended to self.custom_attribute_values by the ORM
      # self.custom_attribute_values.append(new_value)
      if ad_id in last_values:
        _, previous_value = last_values[ad_id]
        if previous_value != attributes[ad_id]:
          signals.Signals.custom_attribute_changed.send(
              self.__class__,
              obj=self,
              src={
                  "type": obj_type,
                  "id": obj_id,
                  "operation": "UPDATE",
                  "value": new_value,
                  "old": previous_value
              }, service=self.__class__.__name__)
      else:
        signals.Signals.custom_attribute_changed.send(
            self.__class__,
            obj=self,
            src={
                "type": obj_type,
                "id": obj_id,
                "operation": "INSERT",
                "value": new_value,
            }, service=self.__class__.__name__)

  @classmethod
  def get_custom_attribute_definitions(cls):
    """Get all applicable CA definitions (even ones without a value yet)."""
    from ggrc.models.custom_attribute_definition import \
        CustomAttributeDefinition as cad

    if cls.__name__ == "Assessment":
      query = cad.query.filter(or_(
          cad.definition_type == utils.underscore_from_camelcase(cls.__name__),
          cad.definition_type == "assessment_template",
      ))
    else:
      query = cad.query.filter(
          cad.definition_type == utils.underscore_from_camelcase(cls.__name__)
      )
    return query.options(
        orm.undefer_group('CustomAttributeDefinition_complete')
    )

  @classmethod
  def eager_query(cls):
    """Define fields to be loaded eagerly to lower the count of DB queries."""
    return super(CustomAttributable, cls).eager_query().options(
        orm.subqueryload(
            'custom_attribute_definitions'
        ).undefer_group(
            'CustomAttributeDefinition_complete'
        ),
        orm.subqueryload(
            '_custom_attribute_values'
        ).undefer_group(
            'CustomAttributeValue_complete'
        ).subqueryload(
            '{0}_custom_attributable'.format(cls.__name__)
        ),
        orm.subqueryload(
            '_custom_attribute_values'
        ).subqueryload(
            '_related_revisions'
        ),
    )

  def log_json(self):
    """Log custom attribute values."""
    # pylint: disable=not-an-iterable
    from ggrc.models.custom_attribute_definition import \
        CustomAttributeDefinition
    # pylint: disable=not-an-iterable
    res = super(CustomAttributable, self).log_json()

    if self.custom_attribute_values:
      res["custom_attribute_values"] = [
          value.log_json() for value in self.custom_attribute_values]
      # fetch definitions form database because `self.custom_attribute`
      # may not be populated
      defs = CustomAttributeDefinition.query.filter(
          CustomAttributeDefinition.definition_type == self._inflector.table_singular,  # noqa # pylint: disable=protected-access
          CustomAttributeDefinition.id.in_([
              value.custom_attribute_id
              for value in self.custom_attribute_values
          ])
      )
      # also log definitions to freeze field names in time
      res["custom_attribute_definitions"] = [
          definition.log_json() for definition in defs]
    else:
      res["custom_attribute_definitions"] = []
      res["custom_attribute_values"] = []
    res["custom_attributes"] = [v.log_json()
                                for v in self.custom_attribute_values]
    res["local_attributes"] = self.local_attributes
    res["global_attributes"] = self.global_attributes
    return res

  def validate_custom_attributes(self):
    # pylint: disable=not-an-iterable; we can iterate over relationships
    map_ = {d.id: d for d in self.custom_attribute_definitions}
    for value in self._custom_attribute_values:
      if not value.custom_attribute and value.custom_attribute_id:
        value.custom_attribute = map_.get(int(value.custom_attribute_id))
      value.validate()

  @builder.simple_property
  def preconditions_failed(self):
    """Returns True if any mandatory CAV, comment or evidence is missing.

    Note: return value may be incorrect if evidence count is changed
    after the first property calculation (see check_mandatory_evidence
    function).
    """
    values_map = {
        cav.custom_attribute_id or cav.custom_attribute.id: cav
        for cav in self.custom_attribute_values
    }
    # pylint: disable=not-an-iterable; we can iterate over relationships
    for cad in self.custom_attribute_definitions:
      if cad.mandatory:
        cav = values_map.get(cad.id)
        if not cav or not cav.attribute_value:
          return True
    return any((any(cav.preconditions_failed.values())
                for cav in self.custom_attribute_values))

  @cached_property.cached_property
  def cav_evidence_count(self):
    """Check presence of mandatory evidence.

    Note:  mandatory evidence precondition is checked only once.
    Any additional changes to evidences after the first checking
    of the precondition will cause incorrect result of the function.
    """

    # Note: this is a suboptimal implementation of mandatory evidence check;
    # it should be refactored once Evicence-CA mapping is introduced
    count = 0
    for cav in self.custom_attribute_values:
      cav_flags = cav.custom_attribute.options.get(cav.attribute_value)
      if cav_flags and cav_flags.evidence_required:
        count += 1
    return count

  def invalidate_evidence_found(self):
    """Invalidate the cached value"""
    if "cav_evidence_count" in self.__dict__:
      del self.__dict__["cav_evidence_count"]
