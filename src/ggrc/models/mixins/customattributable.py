# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Module containing custom attributable mixin."""

import collections
from logging import getLogger

from sqlalchemy import and_
from sqlalchemy import orm
from sqlalchemy import or_
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import foreign
from sqlalchemy.orm import relationship
from werkzeug.exceptions import BadRequest

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
      'custom_attribute_values',
      reflection.Attribute('custom_attribute_definitions',
                           create=False,
                           update=False),
      reflection.Attribute('preconditions_failed',
                           create=False,
                           update=False),
      reflection.Attribute('custom_attributes', read=False),
  )
  _include_links = ['custom_attribute_values', 'custom_attribute_definitions']
  _update_raw = ['custom_attribute_values']

  _evidence_found = None

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
        ).load_only(
            "id",
            "title",
            "attribute_type",
        ),
        orm.Load(cls).subqueryload(
            "custom_attribute_definitions"
        ).undefer_group(
            "CustomAttributeDefinition_complete"
        ),
        orm.Load(cls).subqueryload("custom_attribute_values").load_only(
            "id",
            "attribute_value",
            "attribute_object_id",
        ),
    )

  @custom_attribute_values.setter
  def custom_attribute_values(self, values):
    """Setter function for custom attribute values.

    This setter function accepts 2 kinds of values:
      - list of custom attributes. This is used on the back-end by developers.
      - list of dictionaries containing custom attribute values. This is to
        have a clean API where the front-end can put the custom attribute
        values into the custom_attribute_values property and the json builder
        can then handle the attributes just by setting them.

    Args:
      value: List of custom attribute values or dicts containing json
        representation of custom attribute values.
    """
    if not values:
      return

    self._values_map = {
        value.custom_attribute_id or value.custom_attribute.id: value
        for value in self.custom_attribute_values
    }
    self._definitions_map = {
        definition.id: definition
        for definition in self.custom_attribute_definitions
    }

    if isinstance(values[0], dict):
      self._add_ca_value_dicts(values)
    else:
      self._add_ca_values(values)

  def _add_ca_values(self, values):
    """Add CA value objects to _custom_attributes_values property.

    Args:
      values: list of CustomAttributeValue models
    """
    for new_value in values:
      existing_value = self._values_map.get(new_value.custom_attribute.id)
      if existing_value:
        existing_value.attribute_value = new_value.attribute_value
        existing_value.attribute_object_id = new_value.attribute_object_id
      else:
        new_value.attributable = self
        # new_value is automatically appended to self._custom_attribute_values
        # on new_value.attributable = self

  def _add_ca_value_dicts(self, values):
    """Add CA dict representations to _custom_attributes_values property.

    This adds or updates the _custom_attribute_values with the values in the
    custom attribute values serialized dictionary.

    Args:
      values: List of dictionaries that represent custom attribute values.
    """
    from ggrc.models.custom_attribute_value import CustomAttributeValue

    for value in values:
      if not value.get("attribute_object_id"):
        # value.get("attribute_object", {}).get("id") won't help because
        # value["attribute_object"] can be None
        value["attribute_object_id"] = (value["attribute_object"].get("id") if
                                        value.get("attribute_object") else
                                        None)

      attr = self._values_map.get(value.get("custom_attribute_id"))
      if attr:
        attr.attributable = self
        attr.attribute_value = value.get("attribute_value")
        attr.attribute_object_id = value.get("attribute_object_id")
      elif "custom_attribute_id" in value:
        # this is automatically appended to self._custom_attribute_values
        # on attributable=self
        CustomAttributeValue(
            attributable=self,
            custom_attribute_id=value.get("custom_attribute_id"),
            attribute_value=value.get("attribute_value"),
            attribute_object_id=value.get("attribute_object_id"),
        )
      elif "href" in value:
        # Ignore setting of custom attribute stubs. Getting here means that the
        # front-end is not using the API correctly and needs to be updated.
        logger.info("Ignoring post/put of custom attribute stubs.")
      else:
        raise BadRequest("Bad custom attribute value inserted")

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

    ca_values = src.get("custom_attribute_values")
    if ca_values and "attribute_value" in ca_values[0]:
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
    query = super(CustomAttributable, cls).eager_query()
    query = query.options(
        orm.subqueryload('custom_attribute_definitions')
           .undefer_group('CustomAttributeDefinition_complete'),
        orm.subqueryload('_custom_attribute_values')
           .undefer_group('CustomAttributeValue_complete')
           .subqueryload('{0}_custom_attributable'.format(cls.__name__)),
        orm.subqueryload('_custom_attribute_values')
           .subqueryload('_related_revisions'),
    )
    if hasattr(cls, 'comments'):
      # only for Commentable classess
      query = query.options(
          orm.subqueryload('comments')
             .undefer_group('Comment_complete'),
      )
    return query

  def log_json(self):
    """Log custom attribute values."""
    # pylint: disable=not-an-iterable
    from ggrc.models.custom_attribute_definition import \
        CustomAttributeDefinition

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

    res["custom_attributes"] = res["custom_attribute_values"]
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

    return any(c.preconditions_failed
               for c in self.custom_attribute_values)

  def check_mandatory_evidence(self):
    """Check presence of mandatory evidence.

    Note:  mandatory evidence precondition is checked only once.
    Any additional changes to evidences after the first checking
    of the precondition will cause incorrect result of the function.
    """
    from ggrc.models.object_document import Documentable
    if isinstance(self, Documentable):
      # Note: this is a suboptimal implementation of mandatory evidence check;
      # it should be refactored once Evicence-CA mapping is introduced
      def evidence_required(cav):
        """Return True if an evidence is required for this `cav`."""
        flags = (cav._multi_choice_options_to_flags(cav.custom_attribute)
                 .get(cav.attribute_value))
        return flags and flags.evidence_required

      if self._evidence_found is None:
        self._evidence_found = (len(self.document_evidence) >=
                                len([cav
                                     for cav in self.custom_attribute_values
                                     if evidence_required(cav)]))

      if not self._evidence_found:
        return ["evidence"]

      return []

  def invalidate_evidence_found(self):
    """Invalidate the cached value"""
    self._evidence_found = None
