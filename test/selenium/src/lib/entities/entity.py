# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Create, description, representation and equal of entities."""
# pylint: disable=too-many-arguments
# pylint: disable=too-few-public-methods

import copy
from datetime import datetime

from dateutil import parser, tz

from lib.utils import help_utils
from lib.utils.string_utils import StringMethods


class Representation(object):
  """Class to operate with entities' representation."""
  # pylint: disable=too-many-public-methods
  diff_info = None  # {"equal": {"atr7": val7, ...}, "diff": {"atr3": val3}}
  tree_view_attrs_to_exclude = (
      "created_at", "updated_at", "custom_attributes")
  people_attrs_names = [
      "creators", "assignees", "verifiers", "admins", "primary_contacts",
      "secondary_contacts", "audit_captains", "auditors",
      "principal_assignees", "secondary_assignees"]  # multiply

  @property
  def attrs_names(self):
    """Entity instance's attributes names w/o REST."""
    return self.get_attrs_names(self.__class__)

  @property
  def attrs_names_to_repr(self):
    """Entity instance's attributes names w/o REST and exclude
    'custom_attribute_definitions', 'custom_attribute_values'.
    """
    # todo: add logic to getting 'url', 'id' via UI services
    return [attr_name for attr_name in self.attrs_names if attr_name not in [
        "custom_attribute_definitions", "custom_attribute_values", "href",
        "url", "id"]]

  @classmethod
  def all_attrs_names(cls):
    """All possible entities' attributes names w/ REST."""
    return list(set(cls.get_attrs_names() + [
        "access_control_list", "recipients", "people_values", "default_people",
        "modal_title", "assignee_type", "user_roles"]))

  @classmethod
  def get_attrs_names(cls, entity=None):
    """Get list unique entities attributes' names. If 'entity' then get
    attributes of one entered entity, else get attributes of all entities.
    """
    all_entities_cls = (help_utils.convert_to_list(entity) if entity
                        else list(Entity.all_entities_classes()))
    all_entities_attrs_names = StringMethods.convert_list_elements_to_list(
        [entity_cls().__dict__.keys() for entity_cls in all_entities_cls])
    return list(set(all_entities_attrs_names))

  def __repr__(self):
    """Dictionary representation for entity."""
    return str(dict(
        zip(self.attrs_names_to_repr,
            [getattr(self, attr_name_to_repr) for
             attr_name_to_repr in self.attrs_names_to_repr])))

  @staticmethod
  def remap_collection():
    """Get transformation dictionary {'OLD KEY': 'NEW KEY'}, where
    'OLD KEY' - UI elements and CSV fields correspond to
    'NEW KEY' - objects attributes.
    """
    from lib.constants import element, files
    els = element.TransformationElements
    csv = files.TransformationCSVFields
    # common for UI and CSV
    result_remap_items = {
        els.TITLE: "title", els.ADMIN: "admins",
        els.CODE: "slug", els.REVIEW_STATE: "os_state",
        els.OBJECT_REVIEW: "os_state",
        els.STATE: "status"
    }
    ui_remap_items = {
        els.MANAGER: "manager", els.VERIFIED: "verified",
        els.STATUS: "status", els.LAST_UPDATED: "updated_at",
        els.AUDIT_CAPTAINS: "audit_captains", els.CAS: "custom_attributes",
        els.MAPPED_OBJECTS: "mapped_objects", els.ASSIGNEES: "assignees",
        els.CREATORS: "creators", els.VERIFIERS: "verifiers",
        els.COMMENTS_HEADER: "comments", els.CREATED_AT: "created_at",
        els.MODIFIED_BY: "modified_by", els.LAST_UPDATED_BY: "modified_by",
        els.UPDATED_AT: "updated_at", els.ASMT_TYPE: "assessment_type"
    }
    csv_remap_items = {
        csv.REVISION_DATE: "updated_at"
    }
    result_remap_items.update(ui_remap_items)
    result_remap_items.update(csv_remap_items)
    return StringMethods.dict_keys_to_upper_case(result_remap_items)

  @staticmethod
  def repr_obj_to_dict(objs):
    """Convert objects' representation to dictionary 'obj.attr_name' =
    'attr_value' to dictionary or list of dictionaries with items
    {'attr_name': 'attr_value'}.
    """
    if objs or isinstance(objs, bool):
      if isinstance(objs, list):
        if (all(not isinstance(_, dict) and
                not isinstance(_, (str, unicode, int)) and
                _ for _ in objs)):
          objs = [_.__dict__ for _ in objs]
      else:
        if (not isinstance(objs, dict) and
                not isinstance(objs, (str, unicode, int))):
          objs = objs.__dict__
      return objs

  @staticmethod
  def repr_dict_to_obj(dic):
    """Convert dictionary to Entity representation (dictionary's keys and
    values to attributes names and attributes values).
    """
    # pylint: disable=expression-not-assigned
    # pylint: disable=consider-iterating-dictionary
    entity = Entity()
    [delattr(entity, k) for k in entity.__dict__.keys()]
    [setattr(entity, k, v) for k, v in dic.iteritems()]
    return entity

  def repr_ui(self):
    """Convert entity's attributes values from REST like to UI like
    representation.
    """
    return self.convert_repr_rest_to_ui(objs=self)

  @classmethod  # noqa: ignore=C901
  def convert_repr_rest_to_ui(cls, objs):
    """Convert object's or objects' attributes values from REST like
    (dict or list of dict) representation to UI like with unicode.
    Examples:
    None to None, u'Ex' to u'Ex', [u'Ex1', u'Ex2', ...] to u'Ex1, Ex2',
    {'name': u'Ex', ...} to u'Ex',
    [{'name': u'Ex1', ...}, {'name': u'Ex2', ...}] to u'Ex1, Ex2'
    """
    # pylint: disable=too-many-locals
    # pylint: disable=undefined-loop-variable
    # pylint: disable=invalid-name
    def convert_repr_rest_to_ui(obj):
      """Convert object's attributes from REST to UI like representation."""
      def convert_attr_val_repr_dict_to_unicode(attr_name, attr_value):
        """Convert attribute value from dictionary to unicode representation
        (get value by key from dictionary 'attr_value' where key determine
        according to 'attr_name').
        """
        if isinstance(attr_value, dict):
          converted_attr_value = attr_value
          if attr_name in [
              "manager", "assignees", "creators",
              "verifiers", "created_by", "modified_by"
          ]:
            converted_attr_value = unicode(attr_value.get("email"))
          if attr_name in ["custom_attribute_definitions", "program", "audit",
                           "mapped_objects"]:
            converted_attr_value = (
                unicode(attr_value.get("title")) if
                attr_name != "custom_attribute_definitions" else
                {attr_value.get("id"): attr_value.get("title").upper()}
            )
          if attr_name in ["custom_attribute_values"]:
            converted_attr_value = {attr_value.get("custom_attribute_id"):
                                    attr_value.get("attribute_value")}
          if obj_attr_name == "comments":
            converted_attr_value = {
                k: (parser.parse(v).replace(tzinfo=tz.tzutc()) if
                    k == "created_at" and isinstance(v, unicode) else v)
                for k, v in attr_value.iteritems()
                if k in ["modified_by", "created_at", "description"]}
          return converted_attr_value
      origin_obj = copy.deepcopy(obj)
      for obj_attr_name in obj.__dict__.keys():
        # 'Ex', u'Ex', 1, None to 'Ex', u'Ex', 1, None
        obj_attr_value = getattr(obj, obj_attr_name)
        # REST like u'08-20-2017T04:30:45' to date=2017-08-20,
        # timetz=04:30:45+00:00
        if (obj_attr_name in ["updated_at", "created_at"] and
                isinstance(obj_attr_value, unicode)):
          obj_attr_value = (parser.parse(obj_attr_value).
                            replace(tzinfo=tz.tzutc()))
        if isinstance(obj_attr_value, dict) and obj_attr_value:
          # "modified_by" {"type": "Person", "id": x} to u'user@example.com'
          # todo: deprecated?
          if obj_attr_name == "modified_by":
            from lib.service import rest_service
            obj_attr_value = getattr(rest_service.ObjectsInfoService().get_obj(
                obj=Representation.repr_dict_to_obj(obj_attr_value)), "email")
          # {'name': u'Ex1', 'type': u'Ex2', ...} to u'Ex1'
          else:
            obj_attr_value = convert_attr_val_repr_dict_to_unicode(
                obj_attr_name, obj_attr_value)
        # [el1, el2, ...] or [{item1}, {item2}, ...] to [u'Ex1, u'Ex2', ...]
        if (isinstance(obj_attr_value, list) and
                all(isinstance(item, dict) for item in obj_attr_value)):
          obj_attr_value = [
              convert_attr_val_repr_dict_to_unicode(obj_attr_name, item) for
              item in obj_attr_value]
        setattr(obj, obj_attr_name, obj_attr_value)
      # merge "custom_attribute_definitions" and "custom_attribute_values"
      obj_cas_attrs_names = [
          "custom_attributes", "custom_attribute_definitions",
          "custom_attribute_values"]
      if set(obj_cas_attrs_names).issubset(obj.__dict__.keys()):
        cas_def = obj.custom_attribute_definitions
        cas_val = obj.custom_attribute_values
        # form CAs values of CAs definitions exist but CAs values not, or CAs
        # definitions have different then CAs values lengths
        if (cas_def and
                (not cas_val or (isinstance(cas_def and cas_val, list)) and
                 len(cas_def) != len(cas_val))):
          from lib.entities.entities_factory import (
              CustomAttributeDefinitionsFactory)
          cas_val_dicts_keys = ([_.keys()[0] for _ in cas_val] if
                                isinstance(cas_val, list) else [None])
          _cas_val = [
              {k: v} for k, v in
              CustomAttributeDefinitionsFactory.generate_ca_values(
                  list_ca_def_objs=origin_obj.custom_attribute_definitions,
                  is_none_values=True).iteritems()
              if k not in cas_val_dicts_keys]
          cas_val = _cas_val if not cas_val else cas_val + _cas_val
        cas_def_dict = (
            dict([_def.iteritems().next() for _def in cas_def]) if
            (isinstance(cas_def, list) and
             all(isinstance(_def, dict)
                 for _def in cas_def)) else None)
        cas_val_dict = (
            dict([_val.iteritems().next() for _val in cas_val]) if
            (isinstance(cas_def, list) and
             all(isinstance(_def, dict)
                 for _def in cas_def)) else None)
        cas = StringMethods.merge_dicts_by_same_key(cas_def_dict, cas_val_dict)
        if cas in [{None: None}, {}]:
          cas = None
        setattr(obj, "custom_attributes", cas)
      return obj
    return help_utils.execute_method_according_to_plurality(
        objs=objs, types=Entity.all_entities_classes(),
        method_name=convert_repr_rest_to_ui)

  def repr_snapshot(self, parent_obj):
    """Convert entity's attributes values to Snapshot representation."""
    return (self.convert_repr_to_snapshot(
        objs=self, parent_obj=parent_obj))

  def repr_min_dict(self):
    """Get and return entity's minimal dictionary representation w/
    'type', 'id' keys, e.g. {'type': 'Control', 'id': 1}
    """
    return {"type": getattr(self, "type"),
            "id": getattr(self, "id")}

  @classmethod  # noqa: ignore=C901
  def convert_repr_to_snapshot(cls, objs, parent_obj):
    """Convert object's or objects' attributes values to Snapshot
    representation.
    Retrieved values will be used for: 'id'.
    Set values will be used for: 'title, 'type', 'slug', 'href'.
    """
    def convert_repr_to_snapshot(origin_obj, parent_obj):
      """Convert object's attributes to Snapshot representation."""
      from lib.service import rest_service
      origin_obj = copy.deepcopy(origin_obj)
      snapshoted_obj = (
          rest_service.ObjectsInfoService().get_snapshoted_obj(
              origin_obj=origin_obj, paren_obj=parent_obj))
      origin_obj.__dict__.update(
          {k: v for k, v in snapshoted_obj.__dict__.iteritems()})
      return origin_obj
    return help_utils.execute_method_according_to_plurality(
        objs=objs, types=Entity.all_entities_classes(),
        method_name=convert_repr_to_snapshot, parent_obj=parent_obj)

  def update_attrs(self, is_replace_attrs=True, is_allow_none=True,
                   is_replace_dicts_values=False, **attrs):
    """Update entity's attributes values according to entered data
    (dictionaries of attributes and values).
    If 'is_replace_values_of_dicts' then update values of dicts in list which
    is value of particular object's attribute name.
    """
    return (self.update_objs_attrs_values(
        objs=self, is_replace_attrs_values=is_replace_attrs,
        is_allow_none_values=is_allow_none,
        is_replace_values_of_dicts=is_replace_dicts_values, **attrs))

  def delete_attrs(self, *attrs_names):
    """Delete entity's attributes according to '*attrs_names'."""
    # pylint: disable=expression-not-assigned
    [delattr(self, attr_name)
     for attr_name in attrs_names if hasattr(self, attr_name)]

  def set_attrs(self, *attrs_names, **attrs):
    """Set entity's attributes according to '**attrs' items if key and value
    are corresponding, otherwise set values to None where '*attrs_names'
    is keys.
    """
    # pylint: disable=expression-not-assigned
    [setattr(self, attr_name, attrs.get(attr_name))
     for attr_name in attrs_names]

  @classmethod
  def update_objs_attrs_values(
      cls, objs, is_replace_attrs_values=True,
      is_allow_none_values=True, is_replace_values_of_dicts=False, **attrs
  ):
    """Update object or list of objects ('objs') attributes values by
    manually entered data if attribute name exist in 'attrs_names' witch equal
    to 'all_objs_attrs_names' according to dictionary of attributes and values
    '**attrs'. If 'is_replace_attrs_values' then replace attributes values,
    if not 'is_replace_attrs_values' then update (merge) attributes values
    witch should be lists. If 'is_allow_none_values' then allow to set None
    object's attributes values, and vice versa.
    If 'is_replace_values_of_dicts' then update values of dicts in list which
    is value of particular object's attribute name:
    (**attrs is attr={'key1': 'new_value2', 'key2': 'new_value2'}).
    """
    # pylint: disable=expression-not-assigned
    # pylint: disable=invalid-name
    def update_obj_attrs_values(obj, is_replace_attrs_values,
                                is_allow_none_values, **attrs):
      """Update object's attributes values."""
      for obj_attr_name in attrs:
        obj_attr_value = None
        if (obj_attr_name in Representation.all_attrs_names()):
          _obj_attr_value = attrs.get(obj_attr_name)
          if not is_replace_values_of_dicts:
            # convert repr from objects to dicts exclude datetime objects
            obj_attr_value = (
                cls.repr_obj_to_dict(_obj_attr_value) if
                not isinstance(_obj_attr_value, datetime) else _obj_attr_value)
            if not is_replace_attrs_values:
              origin_obj_attr_value = getattr(obj, obj_attr_name)
              obj_attr_value = (
                  dict(origin_obj_attr_value.items() + obj_attr_value.items())
                  if obj_attr_name == "custom_attributes" else
                  help_utils.convert_to_list(origin_obj_attr_value) +
                  help_utils.convert_to_list(obj_attr_value))
          if is_replace_values_of_dicts and isinstance(_obj_attr_value, dict):
            obj_attr_value = StringMethods.exchange_dicts_items(
                transform_dict=_obj_attr_value,
                dicts=help_utils.convert_to_list(
                    getattr(obj, obj_attr_name)),
                is_keys_not_values=False)
            obj_attr_value = (
                obj_attr_value if isinstance(getattr(obj, obj_attr_name), list)
                else obj_attr_value[0])
          if (is_allow_none_values or
                  (not is_allow_none_values and obj_attr_value)):
            setattr(obj, obj_attr_name, obj_attr_value)
      return obj
    return help_utils.execute_method_according_to_plurality(
        objs=objs, types=Entity.all_entities_classes(),
        method_name=update_obj_attrs_values,
        is_replace_attrs_values=is_replace_attrs_values,
        is_allow_none_values=is_allow_none_values, **attrs)

  @classmethod
  def filter_objs_attrs(cls, objs, attrs_to_include):
    """Make objects's copy and filter objects's attributes (delete attributes
    from objects witch not in list'attrs_to_include').
    'objs' can be list of objects or object.
    """
    # pylint: disable=expression-not-assigned
    def filter_obj_attrs(obj, attrs_to_include):
      """Filter one object's attributes."""
      obj = copy.deepcopy(obj)
      [delattr(obj, obj_attr) for obj_attr in obj.__dict__.keys()
       if obj_attr not in attrs_to_include]
      return obj
    return ([filter_obj_attrs(obj, attrs_to_include) for obj in objs] if
            isinstance(objs, list) else
            filter_obj_attrs(objs, attrs_to_include))

  def __eq__(self, other):
    """Extended equal procedure fore self and other entities."""
    comparison = Representation.compare_entities(self, other)
    self.diff_info = comparison["self_diff"]
    other.diff_info = comparison["other_diff"]
    return comparison["is_equal"]

  @staticmethod
  def attrs_values_types_error(self_attr, other_attr, expected_types):
    raise ValueError("'{}' have to be isinstance of classes: {}\n".
                     format((self_attr, other_attr), expected_types))

  @classmethod
  def is_attrs_equal(cls, attr_name, self_attr_value, other_attr_value):
    """Compare entities' attributes according to attributes' names and values,
    if is equal then return 'True' and vise versa.
    """
    is_equal = False
    if attr_name == "custom_attributes":
      is_equal = cls.compare_cas(self_attr_value, other_attr_value)
    elif attr_name in ["updated_at", "created_at"]:
      is_equal = cls.compare_datetime(self_attr_value, other_attr_value)
    elif attr_name == "comments":
      is_equal = cls.compare_comments(self_attr_value, other_attr_value)
    else:
      is_equal = self_attr_value == other_attr_value
    return is_equal

  @classmethod
  def is_list_of_attrs_equal(cls, self_list_attrs, other_list_attrs):
    """Compare list of entities' attributes according to attributes' names and
    values, if is equal then return 'True' and vise versa.
    """
    return (all(all((self_k == other_k and cls.is_attrs_equal(
        attr_name=self_k, self_attr_value=self_attr[self_k],
        other_attr_value=other_attr[self_k])) for self_k, other_k
        in zip(self_attr.keys(), other_attr.keys()))
        for self_attr, other_attr in zip(self_list_attrs, other_list_attrs)))

  @staticmethod
  def compare_cas(self_cas, other_cas):
    """Compare entities' 'custom_attributes' attributes."""
    if (isinstance(self_cas, (dict, type(None))) and
            isinstance(other_cas, (dict, type(None)))):
      is_equal = False
      if (isinstance(self_cas, dict) and isinstance(other_cas, dict)):
        is_equal = StringMethods.is_subset_of_dicts(self_cas, other_cas)
      else:
        is_equal = self_cas == other_cas
      return is_equal
    else:
      Representation.attrs_values_types_error(
          self_attr=self_cas, other_attr=other_cas,
          expected_types=(dict.__name__, type(None).__name__))

  @staticmethod
  def compare_datetime(self_datetime, other_datetime):
    """Compare entities' datetime ('created_at', 'updated_at') attributes."""
    # pylint: disable=superfluous-parens
    if (isinstance(self_datetime, (datetime, type(None))) and
            isinstance(other_datetime, (datetime, type(None)))):
      return self_datetime == other_datetime
    else:
      Representation.attrs_values_types_error(
          self_attr=self_datetime, other_attr=other_datetime,
          expected_types=(datetime.__name__, type(None).__name__))

  @staticmethod
  def compare_comments(self_comments, other_comments):
    """Compare entities' 'comments' attributes due to specific dictionaries'
    format values in list comments.
    """
    # pylint: disable=no-else-return
    if help_utils.is_multiple_objs(
        StringMethods.convert_list_elements_to_list(
            [self_comments, other_comments]), (dict, type(None))):
      if self_comments and other_comments:
        is_comments_equal_list = []
        for self_comment, other_comment in zip(self_comments, other_comments):
          is_comments_equal = False
          if self_comment and other_comment:
            is_comments_equal = (
                all((Representation.compare_datetime(
                    self_comment.get("created_at"),
                    other_comment.get("created_at")
                ) if (isinstance(_self, datetime) and
                      isinstance(_other, datetime))else
                    _self == _other) for _self, _other in zip(
                    self_comment.iteritems(), other_comment.iteritems())))
            # convert datetime to unicode in order to get visible repr
            if self_comment.get("created_at"):
              self_comment["created_at"] = unicode(
                  self_comment.get("created_at"))
            if other_comment.get("created_at"):
              other_comment["created_at"] = unicode(
                  other_comment.get("created_at"))
          else:
            is_comments_equal = self_comment == other_comment
          is_comments_equal_list.append(is_comments_equal)
        return all(is_equal for is_equal in is_comments_equal_list)
      else:
        return self_comments == other_comments
    else:
      Representation.attrs_values_types_error(
          self_attr=self_comments, other_attr=other_comments,
          expected_types=(list.__name__, type(None).__name__))

  def compare_entities(self, other):
    """Extended compare of entities: 'self_entity' and 'other_entity' according
    to specific 'attrs_names_to_repr' and return:
    - 'is_equal' - True if entities equal else False;
    - 'self_diff' - 'equal' and 'diff' parts of 'self_entity' after compare;
    - 'other_diff' - 'equal' and 'diff' parts of 'other_entity' after compare.
    """
    # pylint: disable=not-an-iterable
    is_equal = False
    self_equal, self_diff, other_equal, other_diff = {}, {}, {}, {}
    if (isinstance(self, other.__class__) and
            self.attrs_names_to_repr == other.attrs_names_to_repr):
      for attr_name in self.attrs_names_to_repr:
        self_attr_value = None
        other_attr_value = None
        if (attr_name in self.__dict__.keys() and
                attr_name in other.__dict__.keys()):
          self_attr_value = getattr(self, attr_name)
          other_attr_value = getattr(other, attr_name)
          is_equal = self.is_attrs_equal(
              attr_name=attr_name, self_attr_value=self_attr_value,
              other_attr_value=other_attr_value)
          # convert datetime to unicode in order to get visible representation
          if isinstance(self_attr_value, datetime):
            self_attr_value = unicode(self_attr_value)
          if isinstance(other_attr_value, datetime):
            other_attr_value = unicode(other_attr_value)
        if is_equal:
          self_equal[attr_name] = self_attr_value
          other_equal[attr_name] = other_attr_value
        else:
          self_diff[attr_name] = self_attr_value, type(self_attr_value)
          other_diff[attr_name] = other_attr_value, type(other_attr_value)
      is_equal = self_diff == other_diff == {}
    return {"is_equal": is_equal,
            "self_diff": {"equal": self_equal, "diff": self_diff},
            "other_diff": {"equal": other_equal, "diff": other_diff}
            }

  @classmethod
  def extract_excluding_attrs(cls, expected_objs, actual_objs, *exclude_attrs):
    """Extract dictionary which contains collections to compare according to
    exclude attributes.
    Where:
    'exp_objs_wo_ex_attrs', 'act_objs_wo_ex_attrs' - list objects w/o excluding
    attributes;
    'exp_ex_attrs', 'act_ex_attrs' - list dictionaries w/ excluding attributes
    (items which contain attributes' names and values);
    ''*exclude_attrs' - tuple of excluding attributes names.
    """
    # pylint: disable=invalid-name
    expected_excluded_attrs, actual_excluded_attrs = (
        cls.extract_simple_collections(
            exclude_attrs, actual_objs, *expected_objs))
    expected_objs_wo_excluded_attrs, actual_objs_wo_excluded_attrs = (
        cls.extract_objs(exclude_attrs, actual_objs, *expected_objs))
    return {"exp_objs_wo_ex_attrs": expected_objs_wo_excluded_attrs,
            "act_objs_wo_ex_attrs": actual_objs_wo_excluded_attrs,
            "exp_ex_attrs": expected_excluded_attrs,
            "act_ex_attrs": actual_excluded_attrs}

  @staticmethod
  def extract_objs_wo_excluded_attrs(objs, *exclude_attrs):
    """Return list objects w/ attributes values set to 'None' according to
    '*exclude_attrs' tuple attributes' names.
    """
    return [expected_obj.update_attrs(
        **dict([(attr, None) for attr in exclude_attrs]))
        for expected_obj in objs]

  @staticmethod
  def extract_excluded_attrs_collection(objs, *exclude_attrs):
    """Return list dictionaries (attributes' names and values) according to
    '*exclude_attrs' tuple attributes' names.
    """
    # pylint: disable=invalid-name
    return [dict([(attr, getattr(expected_obj, attr))
                  for attr in exclude_attrs]) for expected_obj in objs]

  @staticmethod
  def extract_simple_collections(expected_objs, actual_objs, *exclude_attrs):
    """Extract expected and actual simple collections excluded attributes."""
    return [Representation.extract_excluded_attrs_collection(
        copy.deepcopy(objs), *exclude_attrs)
        for objs in [expected_objs, actual_objs]]

  @staticmethod
  def extract_objs(expected_objs, actual_objs, *exclude_attrs):
    """Extract expected and actual objects w/ set to 'None' excluded
    attributes.
    """
    return [Representation.extract_objs_wo_excluded_attrs(
        copy.deepcopy(objs), *exclude_attrs)
        for objs in [expected_objs, actual_objs]]

  @staticmethod
  def filter_objs_by_attrs(objs, **attrs):
    """Filter objects by attributes' items and return matched according to
    plurality.
    'objs' - object or list objects;
    '**attrs' - items of attributes' names and values.
    """
    list_objs = help_utils.convert_to_list(objs)
    matched_objs = [
        obj for obj in list_objs
        if isinstance(obj, Entity.all_entities_classes()) and
        StringMethods.is_subset_of_dicts(dict(**attrs), obj.__dict__)]
    return (help_utils.get_single_obj(matched_objs)
            if not help_utils.is_multiple_objs(matched_objs) else matched_objs)


class Entity(Representation):
  """Class that represent model for base entity."""
  __hash__ = None

  def __init__(self, **attrs):
    self.set_attrs(
        "type", "slug", "id", "title", "href", "url", "admins",
        "primary_contacts", "secondary_contacts", "status", "os_state",
        "comments", "custom_attribute_definitions", "custom_attribute_values",
        "custom_attributes", "created_at", "updated_at", "modified_by",
        **attrs)

  @staticmethod
  def all_entities_classes():
    """Explicitly return tuple of all entities' classes."""
    return (
        PersonEntity, CustomAttributeDefinitionEntity, ProgramEntity,
        ControlEntity, AuditEntity, AssessmentEntity, AssessmentTemplateEntity,
        IssueEntity, CommentEntity, ObjectiveEntity, RoleEntity)

  def __lt__(self, other):
    return self.slug < other.slug


class CommentEntity(Representation):
  """Class that represent model for Comment entity."""
  __hash__ = None

  def __init__(self, **attrs):
    self.set_attrs(
        "type", "id", "href", "description", "created_at", "modified_by",
        **attrs)

  def __lt__(self, other):
    return self.description < other.description


class RoleEntity(Entity):
  """Class that represent model for Person entity."""
  # todo: class's description, relationships w/ PesronEntity, ACLs, user_roles


class PersonEntity(Entity):
  """Class that represent model for Person entity."""

  def __init__(self, **attrs):
    super(PersonEntity, self).__init__()
    self.delete_attrs(
        "slug", "title", "admins", "primary_contacts", "secondary_contacts",
        "status", "os_state", "comments")
    self.set_attrs(
        "name", "email", "company", "system_wide_role", **attrs)

  def __lt__(self, other):
    return self.email < other.email


class CustomAttributeDefinitionEntity(Representation):
  """Class that represent model for Custom Attribute entity."""
  __hash__ = None

  def __init__(self, **attrs):
    super(CustomAttributeDefinitionEntity, self).__init__()
    self.set_attrs(
        "title", "id", "href", "type", "definition_type", "attribute_type",
        "helptext", "placeholder", "mandatory", "multi_choice_options",
        "created_at", "updated_at", "modified_by", **attrs)

  def __lt__(self, other):
    return self.title < other.title


class ProgramEntity(Entity):
  """Class that represent model for Program entity."""

  def __init__(self, **attrs):
    super(ProgramEntity, self).__init__()
    self.delete_attrs("admins")
    self.set_attrs(
        "manager", "primary_contacts", "secondary_contacts", **attrs)


class ControlEntity(Entity):
  """Class that represent model for Control entity."""
  __hash__ = None

  def __init__(self, **attrs):
    super(ControlEntity, self).__init__()
    self.set_attrs(
        "principal_assignees", "secondary_assignees", "program", **attrs)


class ObjectiveEntity(Entity):
  """Class that represent model for Objective entity."""


class AuditEntity(Entity):
  """Class that represent model for Audit enity."""

  def __init__(self, **attrs):
    super(AuditEntity, self).__init__()
    self.delete_attrs(
        "admins", "primary_contacts", "secondary_contacts", "os_state",
        "comments")
    self.set_attrs(
        "audit_captains", "auditors", "program", **attrs)


class AssessmentTemplateEntity(Entity):
  """Class that represent model for Assessment Template entity."""

  def __init__(self, **attrs):
    super(AssessmentTemplateEntity, self).__init__()
    self.delete_attrs(
        "admins", "primary_contacts", "secondary_contacts", "os_state",
        "comments")
    self.set_attrs(
        "assignees", "verifiers", "template_object_type", "audit", **attrs)


class AssessmentEntity(Entity):
  """Class that represent model for Assessment entity."""

  def __init__(self, **attrs):
    super(AssessmentEntity, self).__init__()
    self.delete_attrs("admins", "os_state")
    self.set_attrs(
        "creators", "assignees", "verifiers", "assessment_type", "verified",
        "mapped_objects", "audit", **attrs)


class IssueEntity(Entity):
  """Class that represent model for Issue entity."""
