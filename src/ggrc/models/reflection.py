# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Utilties to deal with introspecting GGRC models for publishing, creation,
and update from resource format representations, such as JSON."""

from collections import defaultdict

import flask
from sqlalchemy.sql.schema import UniqueConstraint

from ggrc.utils import rules
from ggrc.utils import title_from_camelcase
from ggrc.utils import underscore_from_camelcase


ATTRIBUTE_ORDER = (
    "slug",
    "assessment_template",
    "audit",
    "revision_date",
    "control",
    "program",
    "task_group",
    "workflow",
    "title",
    "description",
    "notes",
    "test_plan",
    "owners",
    "related_assessors",
    "related_creators",
    "related_assignees",
    "related_verifiers",
    "program_owner",
    "program_editor",
    "program_reader",
    "workflow_owner",
    "workflow_member",
    "task_type",
    "due_on",
    "start_date",
    "end_date",
    "archived",
    "report_start_date",
    "report_end_date",
    "finished_date",
    "verified_date",
    "status",
    'os_state',
    "assertions",
    "categories",
    "contact",
    "design",
    "directive",
    "fraud_related",
    "key_control",
    "kind",
    "link",
    "means",
    "network_zone",
    "operationally",
    "principal_assessor",
    "secondary_assessor",
    "secondary_contact",
    "assessment_type",
    "reference_url",
    "verify_frequency",
    "name",
    "email",
    "is_enabled",
    "company",
    "user_role",
    "recipients",
    "send_by_default",
    "document_url",
    "document_evidence",
    "notify_custom_message",
    "frequency",
    "notify_on_change",
    "is_verification_needed",
    "updated_at",
    "modified_by",
    "created_at",
    "delete",
    "repeat_every",
    "unit",
)

EXCLUDE_CUSTOM_ATTRIBUTES = set([
    "AssessmentTemplate",
])

EXCLUDE_MAPPINGS = set([
    "AssessmentTemplate",
])


def is_filter_only(alias_properties):
  """Determine if alias is for filter use only.

  Prevents alias filters from being exportable.

  Args:
    alias_properties: Alias properties.
  Returns:
    Boolean reflecting if it's filter only or not.
  """
  if isinstance(alias_properties, dict):
    if alias_properties.get("filter_only"):
      return True
  return False


# pylint: disable=too-few-public-methods
class Attribute(object):
  """Class to define api attribute with allowed actions with that attribute."""

  __slots__ = ["attr", "create", "update", "read"]

  def __init__(self, attr, create=True, update=True, read=True):
    self.attr = attr
    self.create = create
    self.update = update
    self.read = read


class ApiAttributes(dict):
  """Class to collect all required api attributes."""

  def __init__(self, *attrs):
    super(ApiAttributes, self).__init__()
    self.add(*attrs)

  def add(self, *attrs):
    """Append attrs.

    Attrs is the list of strings/unicodes or instances of Attribute class.
    """
    for attr in attrs:
      if isinstance(attr, basestring):
        attr = Attribute(attr)
      self[attr.attr] = attr


class AttributeInfo(object):

  """Gather model CRUD information by reflecting on model classes. Builds and
  caches a list of the publishing properties for a class by walking the
  class inheritance tree.
  """

  MAPPING_PREFIX = "__mapping__:"
  UNMAPPING_PREFIX = "__unmapping__:"
  CUSTOM_ATTR_PREFIX = "__custom__:"
  OBJECT_CUSTOM_ATTR_PREFIX = "__object_custom__:"
  SNAPSHOT_MAPPING_PREFIX = "__snapshot_mapping__:"
  ALIASES_PREFIX = "__acl__"

  class Type(object):
    """Types of model attributes."""
    # TODO: change to enum.
    # pylint: disable=too-few-public-methods
    PROPERTY = "property"
    MAPPING = "mapping"
    AC_ROLE = "mapping"
    SPECIAL_MAPPING = "special_mapping"
    CUSTOM = "custom"  # normal custom attribute
    OBJECT_CUSTOM = "object_custom"  # object level custom attribute
    USER_ROLE = "user_role"

  def __init__(self, tgt_class):
    self._publish_attrs = AttributeInfo.gather_publish_attrs(tgt_class)
    self._update_attrs = AttributeInfo.gather_update_attrs(tgt_class)
    self._create_attrs = AttributeInfo.gather_create_attrs(tgt_class)
    self._include_links = AttributeInfo.gather_include_links(tgt_class)
    self._update_raw = AttributeInfo.gather_update_raw(tgt_class)
    self._aliases = AttributeInfo.gather_aliases(tgt_class)
    self._visible_aliases = AttributeInfo.gather_visible_aliases(tgt_class)

  @classmethod
  def gather_attr_dicts(cls, tgt_class, src_attr):
    """ Gather dictionaries from target class parets """
    result = {}
    for base in reversed(tgt_class.__mro__):
      result.update(getattr(base, src_attr, None) or {})
    return result

  @classmethod
  def gather_attrs(cls, tgt_class, src_attr):
    """Gathers the attrs to be included in a list for publishing, update, or
    some other purpose. Supports inheritance by iterating the list of
    ``src_attrs`` until a list is found.
    """
    accumulator = set()
    callable_attrs = set()
    for base in tgt_class.__mro__:
      attrs = getattr(base, src_attr, None)
      if callable(attrs):
        callable_attrs.add(attrs)
      else:
        accumulator = accumulator.union(set(attrs or []))
    for attr in callable_attrs:
      accumulator = accumulator.union(attr(tgt_class))
    return accumulator

  @classmethod
  def gather_publish_attrs(cls, tgt_class):
    return [attr_name for attr_name, attr in
            cls.gather_attr_dicts(tgt_class, "_api_attrs").iteritems()
            if attr.read]

  @classmethod
  def gather_aliases(cls, tgt_class):
    return cls.gather_attr_dicts(tgt_class, '_aliases')

  @classmethod
  def gather_visible_aliases(cls, tgt_class):
    return {
        attr: props for attr, props
        in AttributeInfo.gather_aliases(tgt_class).iteritems()
        if props is not None and not is_filter_only(props)
    }

  @classmethod
  def gather_update_attrs(cls, tgt_class):
    return [attr_name for attr_name, attr in
            cls.gather_attr_dicts(tgt_class, "_api_attrs").iteritems()
            if attr.update]

  @classmethod
  def gather_create_attrs(cls, tgt_class):
    return [attr_name for attr_name, attr in
            cls.gather_attr_dicts(tgt_class, "_api_attrs").iteritems()
            if attr.create]

  @classmethod
  def gather_include_links(cls, tgt_class):
    return cls.gather_attrs(tgt_class, '_include_links')

  @classmethod
  def gather_update_raw(cls, tgt_class):
    return cls.gather_attrs(tgt_class, '_update_raw')

  @classmethod
  def get_acl_definitions(cls, object_class):
    """Return list of ACL dicts."""
    from ggrc.access_control.role import AccessControlRole
    from ggrc import db
    if not hasattr(flask.g, "acl_role_names"):
      flask.g.acl_role_names = defaultdict(set)
      names_query = db.session.query(
          AccessControlRole.object_type,
          AccessControlRole.name,
          AccessControlRole.mandatory,
      )
      for object_type, name, mandatory in names_query:
        flask.g.acl_role_names[object_type].add((name, mandatory))

    return {
        "{}:{}".format(cls.ALIASES_PREFIX, name): {
            "display_name": name,
            "attr_name": name,
            "mandatory": mandatory,
            "unique": False,
            "description": "List of people with '{}' role".format(name),
            "type": cls.Type.AC_ROLE,
        }
        for name, mandatory in flask.g.acl_role_names[object_class.__name__]
    }

  @classmethod
  def _generate_mapping_definition(cls, rules_set, prefix, display_name_tmpl):
    "Generate definition from template"
    definitions = {}
    from ggrc.snapshotter.rules import Types
    read_only = Types.parents | Types.scoped
    read_only_text = "Read only column and will be ignored on import."
    for klass in rules_set:
      klass_name = title_from_camelcase(klass)
      key = "{}{}".format(prefix, klass_name)
      definitions[key.lower()] = {
          "display_name": display_name_tmpl.format(klass_name),
          "attr_name": klass.lower(),
          "mandatory": False,
          "unique": False,
          "description": read_only_text if klass in read_only else "",
          "type": cls.Type.MAPPING,
      }
    return definitions

  @classmethod
  def get_mapping_definitions(cls, object_class):
    """Get column definitions for allowed (un)mappings for object_class.

    For an Audit-scope object, generates snapshot mappings for all allowed
    mappings with snapshottable objects and direct mappings with all allowed
    mappings with non-snapshottable objects.

    For a normal object, generates direct mappings with all allowed mappings.

    For every direct mapping column generated it also generates an unmapping
    column.
    """

    definitions = {}

    definitions.update(cls._generate_mapping_definition(
        rules.get_mapping_rules().get(object_class.__name__, set()),
        cls.MAPPING_PREFIX, "map:{}",
    ))
    definitions.update(cls._generate_mapping_definition(
        rules.get_snapshot_mapping_rules().get(object_class.__name__, set()),
        cls.SNAPSHOT_MAPPING_PREFIX, "map:{} versions",
    ))
    definitions.update(cls._generate_mapping_definition(
        rules.get_unmapping_rules().get(object_class.__name__, set()),
        cls.UNMAPPING_PREFIX, "unmap:{}",
    ))
    return definitions

  @classmethod
  def get_custom_attr_definitions(cls, object_class, ca_cache=None):
    """Get column definitions for custom attributes on object_class.

    Args:
      object_class: Model for which we want the attribute definitions.
      ca_cache: dictionary containing custom attribute definitions. If it's set
        this function will not look for CAD in the database. This should be
        used for bulk operations, and eventually replaced with memcache.

    returns:
      dict of custom attribute definitions.
    """
    definitions = {}
    if not hasattr(object_class, "get_custom_attribute_definitions"):
      return definitions
    object_name = underscore_from_camelcase(object_class.__name__)
    if isinstance(ca_cache, dict) and object_name:
      custom_attributes = ca_cache.get(object_name, [])
    else:
      custom_attributes = object_class.get_custom_attribute_definitions()
    for attr in custom_attributes:
      description = attr.helptext or u""
      if (attr.attribute_type == attr.ValidTypes.DROPDOWN and
              attr.multi_choice_options):
        if description:
          description += "\n\n"
        description += u"Accepted values are:\n{}".format(
            attr.multi_choice_options.replace(",", "\n")
        )
      if attr.definition_id:
        ca_type = cls.Type.OBJECT_CUSTOM
        attr_name = u"{}{}".format(
            cls.OBJECT_CUSTOM_ATTR_PREFIX, attr.title).lower()
      else:
        ca_type = cls.Type.CUSTOM
        attr_name = u"{}{}".format(cls.CUSTOM_ATTR_PREFIX, attr.title).lower()

      definition_ids = definitions.get(attr_name, {}).get("definition_ids", [])
      definition_ids.append(attr.id)

      definitions[attr_name] = {
          "display_name": attr.title,
          "attr_name": attr.title,
          "mandatory": attr.mandatory,
          "unique": False,
          "description": description,
          "type": ca_type,
          "definition_ids": definition_ids,
      }
    return definitions

  @classmethod
  def get_unique_constraints(cls, object_class):
    """ Return a set of attribute names for single unique columns """
    constraints = object_class.__table__.constraints
    unique = [con for con in constraints if isinstance(con, UniqueConstraint)]
    # we only handle single column unique constraints
    unique_columns = [u.columns.keys() for u in unique if len(u.columns) == 1]
    return set(sum(unique_columns, []))

  @classmethod
  def get_object_attr_definitions(cls, object_class, ca_cache=None):
    """Get all column definitions for object_class.

    This function joins custom attribute definitions, mapping definitions and
    the extra delete column.

    Args:
      object_class: Model for which we want the attribute definitions.
      ca_cache: dictionary containing custom attribute definitions.
    """
    definitions = {}

    aliases = AttributeInfo.gather_visible_aliases(object_class).items()

    # push the extra delete column at the end to override any custom behavior
    if hasattr(object_class, "slug"):
      aliases.append(("delete", {
          "display_name": "Delete",
          "description": "",
      }))

    unique_columns = cls.get_unique_constraints(object_class)

    for key, value in aliases:
      column = object_class.__table__.columns.get(key)
      mandatory = False
      if column is not None:
        mandatory = not column.nullable and not column.default
      definition = {
          "display_name": value,
          "attr_name": key,
          "mandatory": mandatory,
          "unique": key in unique_columns,
          "description": "",
          "type": cls.Type.PROPERTY,
          "handler_key": key,
      }
      if isinstance(value, dict):
        definition.update(value)
      definitions[key] = definition

    definitions.update(cls.get_acl_definitions(object_class))

    if object_class.__name__ not in EXCLUDE_CUSTOM_ATTRIBUTES:
      definitions.update(cls.get_custom_attr_definitions(
          object_class, ca_cache=ca_cache
      ))

    if object_class.__name__ not in EXCLUDE_MAPPINGS:
      definitions.update(cls.get_mapping_definitions(object_class))

    return definitions

  @classmethod
  def get_attr_definitions_array(cls, object_class, ca_cache=None):
    """ get all column definitions containing only json serializable data """
    definitions = cls.get_object_attr_definitions(object_class,
                                                  ca_cache=ca_cache)
    order = cls.get_column_order(definitions.keys())
    result = []
    for key in order:
      item = definitions[key]
      item["key"] = key
      result.append(item)
    return result

  @classmethod
  def get_column_order(cls, attr_list):
    """ Sort attribute list

    Attribute list should be sorted with 3 rules:
      - attributes in ATTRIBUTE_ORDER variable must be fist and in the same
        order as defined in that variable.
      - Custom Attributes are sorted alphabetically after default attributes
      - mapping attributes are sorted alphabetically and placed last
    """
    attr_set = set(attr_list)
    default_attrs = [v for v in ATTRIBUTE_ORDER if v in attr_set]
    default_set = set(default_attrs)
    other_attrs = [v for v in attr_list if v not in default_set]
    custom_attrs = [v for v in other_attrs if not v.lower().startswith("map:")]
    mapping_attrs = [v for v in other_attrs if v.lower().startswith("map:")]
    custom_attrs.sort(key=lambda x: x.lower())
    mapping_attrs.sort(key=lambda x: x.lower())
    return default_attrs + custom_attrs + mapping_attrs
