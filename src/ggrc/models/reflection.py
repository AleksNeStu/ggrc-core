# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Utilties to deal with introspecting GGRC models for publishing, creation,
and update from resource format representations, such as JSON."""

from sqlalchemy.sql.schema import UniqueConstraint

from ggrc.utils import get_mapping_rules
from ggrc.utils import title_from_camelcase
from ggrc.utils import underscore_from_camelcase


ATTRIBUTE_ORDER = (
    "slug",
    "assessment_template",
    "audit",
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
    "report_start_date",
    "report_end_date",
    "relative_start_date",
    "relative_end_date",
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
    "url",
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
    "delete",
)

EXCLUDE_CUSTOM_ATTRIBUTES = set([
    "AssessmentTemplate",
])

EXCLUDE_MAPPINGS = set([
    "AssessmentTemplate",
])


class PublishOnly(object):
  """Attributes wrapped by ``PublishOnly`` instances should not be considered
  to be a part of an inherited list. For example, ``_update_attrs`` can be
  inherited from ``_publish_attrs`` if left unspecified. This class provides
  a mechanism to use that inheritance while excluding some elements from the
  resultant inherited list. For example, this:

  .. sourcecode::

    _publish_attrs = [
      'inherited_attr',
      PublishOnly('not_inherited_attr'),
      ]

  is equivalent to this:

  .. sourcecode::

    _publish_attrs = [
    'inherited_attr',
    'not_inherited_attr',
    ]
    _update_attrs = [
    'inherited_attr',
    ]
  """
  # pylint: disable=too-few-public-methods

  def __init__(self, attr_name):
    self.attr_name = attr_name


class AttributeInfo(object):

  """Gather model CRUD information by reflecting on model classes. Builds and
  caches a list of the publishing properties for a class by walking the
  class inheritance tree.
  """

  MAPPING_PREFIX = "__mapping__:"
  UNMAPPING_PREFIX = "__unmapping__:"
  CUSTOM_ATTR_PREFIX = "__custom__:"

  class Type(object):
    """Types of model attributes."""
    # TODO: change to enum.
    # pylint: disable=too-few-public-methods
    PROPERTY = "property"
    MAPPING = "mapping"
    SPECIAL_MAPPING = "special_mapping"
    CUSTOM = "custom"  # normal custom attribute
    OBJECT_CUSTOM = "object_custom"  # object level custom attribute
    USER_ROLE = "user_role"

  def __init__(self, tgt_class):
    self._publish_attrs = AttributeInfo.gather_publish_attrs(tgt_class)
    self._update_attrs = AttributeInfo.gather_update_attrs(tgt_class)
    self._create_attrs = AttributeInfo.gather_create_attrs(tgt_class)
    self._include_links = AttributeInfo.gather_include_links(tgt_class)
    self._aliases = AttributeInfo.gather_aliases(tgt_class)

  @classmethod
  def gather_attr_dicts(cls, tgt_class, src_attr):
    """ Gather dictionaries from target class parets """
    result = {}
    for base_class in tgt_class.__bases__:
      base_result = cls.gather_attr_dicts(base_class, src_attr)
      result.update(base_result)
    attrs = getattr(tgt_class, src_attr, {})
    result.update(attrs)
    return result

  @classmethod
  def gather_attrs(cls, tgt_class, src_attrs, accumulator=None,
                   main_class=None):
    """Gathers the attrs to be included in a list for publishing, update, or
    some other purpose. Supports inheritance by iterating the list of
    ``src_attrs`` until a list is found.

    Inheritance of some attributes can be circumvented through use of the
    ``DontPropoagate`` decorator class.
    """
    if main_class is None:
      main_class = tgt_class
    src_attrs = src_attrs if isinstance(src_attrs, list) else [src_attrs]
    accumulator = accumulator if accumulator is not None else set()
    ignore_publishonly = True
    for attr in src_attrs:
      attrs = None
      # Only get the attribute if it is defined on the target class, but
      # get it via `getattr`, to handle `@declared_attr`
      if attr in tgt_class.__dict__:
        attrs = getattr(tgt_class, attr, None)
        if callable(attrs):
          attrs = attrs(main_class)
      if attrs is not None:
        if not ignore_publishonly:
          attrs = [a for a in attrs if not isinstance(a, PublishOnly)]
        else:
          attrs = [a if not isinstance(a, PublishOnly) else a.attr_name for
                   a in attrs]
        accumulator.update(attrs)
        break
      else:
        ignore_publishonly = False
    for base in tgt_class.__bases__:
      cls.gather_attrs(base, src_attrs, accumulator, main_class=main_class)
    return accumulator

  @classmethod
  def gather_publish_attrs(cls, tgt_class):
    return cls.gather_attrs(tgt_class, '_publish_attrs')

  @classmethod
  def gather_aliases(cls, tgt_class):
    return cls.gather_attr_dicts(tgt_class, '_aliases')

  @classmethod
  def gather_update_attrs(cls, tgt_class):
    attrs = cls.gather_attrs(tgt_class, ['_update_attrs', '_publish_attrs'])
    return attrs

  @classmethod
  def gather_create_attrs(cls, tgt_class):
    return cls.gather_attrs(tgt_class, [
        '_create_attrs', '_update_attrs', '_publish_attrs'])

  @classmethod
  def gather_include_links(cls, tgt_class):
    return cls.gather_attrs(tgt_class, ['_include_links'])

  @classmethod
  def get_mapping_definitions(cls, object_class):
    """ Get column definitions for allowed mappings for object_class """
    definitions = {}
    mapping_rules = get_mapping_rules()
    object_mapping_rules = mapping_rules.get(object_class.__name__, [])

    for mapping_class in object_mapping_rules:
      class_name = title_from_camelcase(mapping_class)
      mapping_name = "{}{}".format(cls.MAPPING_PREFIX, class_name)
      definitions[mapping_name.lower()] = {
          "display_name": "map:{}".format(class_name),
          "attr_name": mapping_class.lower(),
          "mandatory": False,
          "unique": False,
          "description": "",
          "type": cls.Type.MAPPING,
      }

      unmapping_name = "{}{}".format(cls.UNMAPPING_PREFIX, class_name)
      definitions[unmapping_name.lower()] = {
          "display_name": "unmap:{}".format(class_name),
          "attr_name": mapping_class.lower(),
          "mandatory": False,
          "unique": False,
          "description": "",
          "type": cls.Type.MAPPING,
      }

    return definitions

  @classmethod
  def get_custom_attr_definitions(cls, object_class, ca_cache=None,
                                  include_oca=True):
    """Get column definitions for custom attributes on object_class.

    Args:
      object_class: Model for which we want the attribute definitions.
      ca_cache: dictionary containing custom attribute definitions. If it's set
        this function will not look for CAD in the database. This should be
        used for bulk operations, and eventually replaced with memcache.
      include_oca: Flag for including object level custom attributes. This
        should be true only for defenitions needed for csv imports.

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
  def get_object_attr_definitions(cls, object_class, ca_cache=None,
                                  include_oca=True):
    """Get all column definitions for object_class.

    This function joins custom attribute definitions, mapping definitions and
    the extra delete column.

    Args:
      object_class: Model for which we want the attribute definitions.
      ca_cache: dictionary containing custom attribute definitions.
      include_oca: Flag for including object level custom attributes.
    """
    definitions = {}

    aliases = AttributeInfo.gather_aliases(object_class)
    filtered_aliases = [(k, v) for k, v in aliases.items() if v is not None]

    # push the extra delete column at the end to override any custom behavior
    if hasattr(object_class, "slug"):
      filtered_aliases.append(("delete", {
          "display_name": "Delete",
          "description": "",
      }))

    unique_columns = cls.get_unique_constraints(object_class)

    for key, value in filtered_aliases:
      column = object_class.__table__.columns.get(key)
      definition = {
          "display_name": value,
          "attr_name": key,
          "mandatory": False if column is None else not column.nullable,
          "unique": key in unique_columns,
          "description": "",
          "type": cls.Type.PROPERTY,
          "handler_key": key,
      }
      if isinstance(value, dict):
        definition.update(value)
      definitions[key] = definition

    if object_class.__name__ not in EXCLUDE_CUSTOM_ATTRIBUTES:
      definitions.update(
          cls.get_custom_attr_definitions(object_class, ca_cache=ca_cache,
                                          include_oca=include_oca))

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


class SanitizeHtmlInfo(AttributeInfo):

  def __init__(self, tgt_class):
    self._sanitize_html = SanitizeHtmlInfo.gather_attrs(
        tgt_class, '_sanitize_html')
