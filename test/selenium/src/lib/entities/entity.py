# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Create, description, representation and equal of entities."""
# pylint: disable=too-many-arguments
# pylint: disable=too-few-public-methods

import copy
from datetime import datetime

from dateutil import parser, tz

from lib.utils import string_utils, help_utils


class Representation(object):
  """Class that contains methods to update Entity."""
  # pylint: disable=import-error
  diff_info = None  # {"equal": {"atr7": val7, ...}, "diff": {"atr3": val3}}
  attrs_names_to_compare = None
  attrs_names_to_repr = None
  core_attrs_names_to_repr = ["type", "title", "id", "href", "url", "slug"]

  @classmethod
  def get_attrs_names_for_entities(cls, entity=None):
    """Get list unique attributes names for entities. If 'entity' then get
    attributes of one entered entity, else get attributes of all entities.
    """
    all_entities_cls = (string_utils.convert_to_list(entity) if entity
                        else Entity.all_entities_classes())
    all_entities_attrs_names = string_utils.convert_list_elements_to_list(
        [entity_cls().__dict__.keys() for entity_cls in all_entities_cls])
    return list(set(all_entities_attrs_names))

  def __repr__(self):
    # exclude attributes witch are used for REST interaction forming
    # pylint: disable=not-an-iterable
    return str(dict(zip(self.attrs_names_to_repr,
                        [getattr(self, attr_name_to_repr) for attr_name_to_repr
                         in self.attrs_names_to_repr])))

  @staticmethod
  def items_of_remap_keys():
    """Get transformation dictionary {'OLD KEY': 'NEW KEY'}, where
    'OLD KEY' - UI elements and CSV fields correspond to
    'NEW KEY' - objects attributes.
    """
    from lib.constants import element, files
    els = element.TransformationElements
    csv = files.TransformationCSVFields
    # common for UI and CSV
    result_remap_items = {
        els.TITLE: "title", els.ADMIN: "owners",
        els.CODE: "slug", els.REVIEW_STATE: "os_state",
        els.STATE: "status"
    }
    ui_remap_items = {
        els.MANAGER: "manager", els.VERIFIED: "verified",
        els.STATUS: "status", els.LAST_UPDATED: "updated_at",
        els.AUDIT_LEAD: "contact", els.CAS: "custom_attributes",
        els.MAPPED_OBJECTS: "objects_under_assessment",
        els.ASSIGNEES: "assessor", els.ASSIGNEES_: "assessor",
        els.CREATORS: "creator", els.CREATORS_: "creator",
        els.VERIFIERS: "verifier", els.VERIFIERS_: "verifier",
        element.AssessmentInfoWidget.COMMENTS_HEADER: "comments",
        els.PRIMARY_CONTACT: "contact"
    }
    csv_remap_items = {
        csv.REVISION_DATE: "updated_at"
    }
    result_remap_items.update(ui_remap_items)
    result_remap_items.update(csv_remap_items)
    return string_utils.dict_keys_to_upper_case(result_remap_items)

  @staticmethod
  def convert_objs_repr_to_dict(obj_or_objs):
    """Convert objects' representation to dictionary 'obj.attr_name' =
    'attr_value' to dictionary or list of dictionaries with items
    {'attr_name': 'attr_value'}.
    """
    if obj_or_objs or isinstance(obj_or_objs, bool):
      if isinstance(obj_or_objs, list):
        if (all(not isinstance(_, dict) and
                not isinstance(_, (str, unicode, int)) and
                _ for _ in obj_or_objs)):
          obj_or_objs = [_.__dict__ for _ in obj_or_objs]
      else:
        if (not isinstance(obj_or_objs, dict) and
                not isinstance(obj_or_objs, (str, unicode, int))):
          obj_or_objs = obj_or_objs.__dict__
      return obj_or_objs

  @staticmethod
  def convert_dict_to_obj_repr(dic):
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
    return self.convert_objs_repr_from_rest_to_ui(obj_or_objs=self)

  @classmethod  # noqa: ignore=C901
  def convert_objs_repr_from_rest_to_ui(cls, obj_or_objs):
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
    def convert_obj_repr_from_rest_to_ui(obj):
      """Convert object's attributes from REST to UI like representation."""
      def convert_attr_value_from_dict_to_unicode(attr_name, attr_value):
        """Convert attribute value from dictionary to unicode representation
        (get value by key from dictionary 'attr_value' where key determine
        according to 'attr_name').
        """
        if isinstance(attr_value, dict):
          converted_attr_value = attr_value
          if attr_name in [
              "contact", "manager", "owners", "assessor", "creator",
              "verifier", "created_by", "modified_by", "Assessor", "Creator",
              "Verifier"
          ]:
            converted_attr_value = unicode(attr_value.get("email"))
          if attr_name in ["custom_attribute_definitions", "program", "audit",
                           "objects_under_assessment"]:
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
        obj_attr_value = (obj.assignees.get(obj_attr_name.title()) if (
            obj_attr_name in ["assessor", "creator", "verifier"] and
            "assignees" in obj.__dict__.keys())
            else getattr(obj, obj_attr_name))
        # REST like u'08-20-2017T04:30:45' to date=2017-08-20,
        # timetz=04:30:45+00:00
        if (obj_attr_name in ["updated_at", "created_at"] and
                isinstance(obj_attr_value, unicode)):
          obj_attr_value = (parser.parse(obj_attr_value).
                            replace(tzinfo=tz.tzutc()))
        if isinstance(obj_attr_value, dict) and obj_attr_value:
          # to "assignees" = {"Assessor": [], "Creator": [], "Verifier": []}
          if obj_attr_name == "assignees":
            obj_attr_value = {
                k: ([convert_attr_value_from_dict_to_unicode(k, _v)
                     for _v in v] if isinstance(v, list) else
                    convert_attr_value_from_dict_to_unicode(k, v))
                for k, v in obj_attr_value.iteritems()
                if k in ["Assessor", "Creator", "Verifier"]}
          # {'name': u'Ex1', 'type': u'Ex2', ...} to u'Ex1'
          else:
            obj_attr_value = convert_attr_value_from_dict_to_unicode(
                obj_attr_name, obj_attr_value)
        # [el1, el2, ...] or [{item1}, {item2}, ...] to [u'Ex1, u'Ex2', ...]
        if (isinstance(obj_attr_value, list) and
                all(isinstance(item, dict) for item in obj_attr_value)):
          obj_attr_value = [
              convert_attr_value_from_dict_to_unicode(obj_attr_name, item) for
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
                 for _def in cas_def)) else {None: None})
        cas_val_dict = (
            dict([_val.iteritems().next() for _val in cas_val]) if
            (isinstance(cas_def, list) and
             all(isinstance(_def, dict)
                 for _def in cas_def)) else {None: None})
        cas = string_utils.merge_dicts_by_same_key(cas_def_dict, cas_val_dict)
        setattr(obj, "custom_attributes", cas)
      return obj
    return help_utils.execute_method_according_to_plurality(
        obj_or_objs=obj_or_objs, types=Entity.all_entities_classes(),
        method_name=convert_obj_repr_from_rest_to_ui)

  def repr_snapshot(self, parent_obj):
    """Convert entity's attributes values to Snapshot representation."""
    return (self.convert_objs_repr_to_snapshot(
        obj_or_objs=self, parent_obj=parent_obj))

  @classmethod  # noqa: ignore=C901
  def convert_objs_repr_to_snapshot(cls, obj_or_objs, parent_obj):
    """Convert object's or objects' attributes values to Snapshot
    representation.
    Retrieved values will be used for: 'id'.
    Set values will be used for: 'title, 'type', 'slug', 'href'.
    """
    def convert_obj_repr_to_snapshot(origin_obj, parent_obj):
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
        obj_or_objs=obj_or_objs, types=Entity.all_entities_classes(),
        method_name=convert_obj_repr_to_snapshot, parent_obj=parent_obj)

  def update_attrs(self, is_replace_attrs=True, is_allow_none=True,
                   is_replace_dicts_values=False, **attrs):
    """Update entity's attributes values according to entered data
    (dictionaries of attributes and values).
    If 'is_replace_values_of_dicts' then update values of dicts in list which
    is value of particular object's attribute name.
    """
    return (self.update_objs_attrs_values_by_entered_data(
        obj_or_objs=self, is_replace_attrs_values=is_replace_attrs,
        is_allow_none_values=is_allow_none,
        is_replace_values_of_dicts=is_replace_dicts_values, **attrs))

  @classmethod
  def update_objs_attrs_values_by_entered_data(
      cls, obj_or_objs, is_replace_attrs_values=True,
      is_allow_none_values=True, is_replace_values_of_dicts=False, **arguments
  ):
    """Update object or list of objects ('obj_or_objs') attributes values by
    manually entered data if attribute name exist in 'attrs_names' witch equal
    to 'all_objs_attrs_names' according to dictionary of attributes and values
    '**arguments'. If 'is_replace_attrs_values' then replace attributes values,
    if not 'is_replace_attrs_values' then update (merge) attributes values
    witch should be lists. If 'is_allow_none_values' then allow to set None
    object's attributes values, and vice versa.
    If 'is_replace_values_of_dicts' then update values of dicts in list which
    is value of particular object's attribute name:
    (**arguments is attr={'key1': 'new_value2', 'key2': 'new_value2'}).
    """
    # pylint: disable=expression-not-assigned
    # pylint: disable=invalid-name
    def update_obj_attrs_values(obj, is_replace_attrs_values,
                                is_allow_none_values, **arguments):
      """Update object's attributes values."""
      for obj_attr_name in arguments:
        if (obj_attr_name in
                Entity.get_attrs_names_for_entities(obj.__class__)):
          _obj_attr_value = arguments.get(obj_attr_name)
          condition = (True if is_allow_none_values else _obj_attr_value)
          if condition and not is_replace_values_of_dicts:
            # convert repr from objects to dicts exclude datetime objects
            obj_attr_value = (
                cls.convert_objs_repr_to_dict(_obj_attr_value) if
                not isinstance(_obj_attr_value, datetime) else _obj_attr_value)
            if not is_replace_attrs_values:
              origin_obj_attr_value = getattr(obj, obj_attr_name)
              obj_attr_value = (
                  dict(origin_obj_attr_value.items() + obj_attr_value.items())
                  if obj_attr_name == "custom_attributes" else
                  string_utils.convert_to_list(origin_obj_attr_value) +
                  string_utils.convert_to_list(obj_attr_value))
            setattr(obj, obj_attr_name, obj_attr_value)
            if obj_attr_name in ["creator", "assessor", "verifier"]:
              from lib.entities.entities_factory import ObjectPersonsFactory
              if not isinstance(obj.assignees, dict):
                obj.assignees = dict()
              obj.assignees[obj_attr_name.capitalize()] = (
                  [ObjectPersonsFactory().default().__dict__])
          if is_replace_values_of_dicts and isinstance(_obj_attr_value, dict):
            obj_attr_value = string_utils.exchange_dicts_items(
                transform_dict=_obj_attr_value,
                dicts=string_utils.convert_to_list(
                    getattr(obj, obj_attr_name)),
                is_keys_not_values=False)
            obj_attr_value = (
                obj_attr_value if isinstance(getattr(obj, obj_attr_name), list)
                else obj_attr_value[0])
            setattr(obj, obj_attr_name, obj_attr_value)
      return obj
    return help_utils.execute_method_according_to_plurality(
        obj_or_objs=obj_or_objs, types=Entity.all_entities_classes(),
        method_name=update_obj_attrs_values,
        is_replace_attrs_values=is_replace_attrs_values,
        is_allow_none_values=is_allow_none_values, **arguments)

  @classmethod
  def filter_objs_attrs(cls, obj_or_objs, attrs_to_include):
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
    return ([filter_obj_attrs(obj, attrs_to_include) for obj in obj_or_objs] if
            isinstance(obj_or_objs, list) else
            filter_obj_attrs(obj_or_objs, attrs_to_include))

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
    if isinstance(self_cas and other_cas, dict):
      return string_utils.is_subset_of_dicts(self_cas, other_cas)
    else:
      Representation.attrs_values_types_error(
          self_attr=self_cas, other_attr=other_cas,
          expected_types=dict.__name__)

  @staticmethod
  def compare_datetime(self_datetime, other_datetime):
    """Compare entities' datetime ('created_at', 'updated_at') attributes."""
    # pylint: disable=superfluous-parens
    if (isinstance(self_datetime and other_datetime, (datetime, type(None)))):
      return (
          (self_datetime == other_datetime
           if all(str(_.time()) != "00:00:00"
                  for _ in [self_datetime, other_datetime])
           else self_datetime.date() == other_datetime.date())
          if self_datetime and other_datetime
          else self_datetime == other_datetime)
    else:
      Representation.attrs_values_types_error(
          self_attr=self_datetime, other_attr=other_datetime,
          expected_types=(datetime.__name__, type(None).__name__))

  @staticmethod
  def compare_comments(self_comments, other_comments):
    """Compare entities' 'comments' attributes due to specific dictionaries'
    format values in list comments.
    """
    if (isinstance(self_comments and other_comments, list) and
            all(isinstance(self_comment and other_comment, dict) for
                self_comment, other_comment
                in zip(self_comments, other_comments))):
      for self_comment, other_comment in zip(self_comments, other_comments):
        is_comments_datetime_equal = (
            Representation.compare_datetime(self_comment.get("created_at"),
                                            other_comment.get("created_at")))
        self_comment.pop("created_at")
        other_comment.pop("created_at")
        # compare comments' datetime and remaining attributes
        return (is_comments_datetime_equal and
                string_utils.is_subset_of_dicts(self_comment, other_comment))
    if isinstance(self_comments and other_comments, (list, type(None))):
      return self_comments == other_comments
    else:
      Representation.attrs_values_types_error(
          self_attr=self_comments, other_attr=other_comments,
          expected_types=(list.__name__, type(None).__name__))

  def compare_entities(self, other):
    """Extended compare of entities: 'self_entity' and 'other_entity' according
    to specific 'attrs_names_to_compare' and return:
    - 'is_equal' - True if entities equal else False;
    - 'self_diff' - 'equal' and 'diff' parts of 'self_entity' after compare;
    - 'other_diff' - 'equal' and 'diff' parts of 'other_entity' after compare.
    """
    # pylint: disable=not-an-iterable
    is_equal = False
    self_equal, self_diff, other_equal, other_diff = {}, {}, {}, {}
    if (isinstance(self, other.__class__) and
            self.attrs_names_to_compare == other.attrs_names_to_compare):
      for attr_name in self.attrs_names_to_compare:
        self_attr_value = None
        other_attr_value = None
        if (attr_name in self.__dict__.keys() and
                attr_name in other.__dict__.keys()):
          self_attr_value = getattr(self, attr_name)
          other_attr_value = getattr(other, attr_name)
          is_equal = self.is_attrs_equal(
              attr_name=attr_name, self_attr_value=self_attr_value,
              other_attr_value=other_attr_value)
        if is_equal:
          self_equal[attr_name] = self_attr_value
          other_equal[attr_name] = other_attr_value
        else:
          self_diff[attr_name] = {"val": self_attr_value,
                                  "type": type(self_attr_value)}
          other_diff[attr_name] = {"val": other_attr_value,
                                   "type": type(other_attr_value)}
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
    expected_objs = string_utils.convert_to_list(expected_objs)
    actual_objs = string_utils.convert_to_list(actual_objs)
    expected_excluded_attrs = [
        dict([(attr, getattr(expected_obj, attr)) for attr in exclude_attrs])
        for expected_obj in expected_objs]
    actual_excluded_attrs = [
        dict([(attr, getattr(actual_obj, attr)) for attr in exclude_attrs])
        for actual_obj in actual_objs]
    expected_objs_wo_excluded_attrs = [
        expected_obj.update_attrs(**dict(
            [(attr, ({None: None} if attr == "custom_attributes" else None))
             for attr in exclude_attrs])) for expected_obj in expected_objs]
    actual_objs_wo_excluded_attrs = [
        actual_obj.update_attrs(**dict(
            [(attr, ({None: None} if attr == "custom_attributes" else None))
             for attr in exclude_attrs])) for actual_obj in actual_objs]
    return {"exp_objs_wo_ex_attrs": expected_objs_wo_excluded_attrs,
            "act_objs_wo_ex_attrs": actual_objs_wo_excluded_attrs,
            "exp_ex_attrs": expected_excluded_attrs,
            "act_ex_attrs": actual_excluded_attrs}


class Entity(Representation):
  """Class that represent model for base entity."""
  # pylint: disable=invalid-name
  # pylint: disable=redefined-builtin

  def __init__(self, type=None, slug=None, id=None, title=None, href=None,
               url=None):
    # REST and UI
    self.type = type
    self.slug = slug  # code
    self.id = id
    self.title = title
    self.href = href
    self.url = url

  @staticmethod
  def all_entities_classes():
    """Explicitly return list of all entities' classes."""
    return [
        PersonEntity, CustomAttributeEntity, ProgramEntity, ControlEntity,
        AuditEntity, AssessmentEntity, AssessmentTemplateEntity, IssueEntity,
        CommentEntity]

  def __lt__(self, other):
    return self.slug < other.slug


class CommentEntity(Representation):
  """Class that represent model for Comment."""
  # pylint: disable=invalid-name
  # pylint: disable=redefined-builtin
  __hash__ = None

  attrs_names_to_compare = ["type", "modified_by", "created_at", "description"]
  attrs_names_to_repr = [
      "type", "id", "href", "modified_by", "created_at", "description"]

  def __init__(self, type=None, id=None, href=None, modified_by=None,
               created_at=None, description=None):
    super(CommentEntity, self).__init__()
    # REST and UI
    self.type = type
    self.id = id
    self.href = href
    self.modified_by = modified_by
    self.created_at = created_at
    self.description = description

  def __lt__(self, other):
    return self.description < other.description


class PersonEntity(Representation):
  """Class that represent model for Person."""
  # pylint: disable=invalid-name
  # pylint: disable=redefined-builtin
  # pylint: disable=too-many-instance-attributes
  __hash__ = None
  attrs_names_to_compare = [
      "type", "name", "email"]
  attrs_names_to_repr = [
      "type", "id", "name", "href", "url", "email", "company",
      "system_wide_role", "updated_at", "ac_role_id"]

  def __init__(self, type=None, id=None, name=None, href=None, url=None,
               email=None, company=None, system_wide_role=None,
               updated_at=None, custom_attribute_definitions=None,
               custom_attribute_values=None, ac_role_id=None):
    super(PersonEntity, self).__init__()
    # REST and UI
    self.name = name
    self.id = id
    self.href = href
    self.url = url
    self.type = type
    self.email = email
    self.company = company
    self.system_wide_role = system_wide_role  # authorizations
    self.updated_at = updated_at  # last updated datetime
    # REST
    self.custom_attribute_definitions = custom_attribute_definitions
    self.custom_attribute_values = custom_attribute_values
    self.ac_role_id = ac_role_id

  def __lt__(self, other):
    return self.email < other.email


class CustomAttributeEntity(Representation):
  """Class that represent model for Custom Attribute."""
  # pylint: disable=invalid-name
  # pylint: disable=redefined-builtin
  # pylint: disable=too-many-instance-attributes
  __hash__ = None
  attrs_names_to_compare = [
      "type", "title", "definition_type", "attribute_type", "mandatory"]
  attrs_names_to_repr = [
      "type", "title", "id", "href", "definition_type", "attribute_type",
      "helptext", "placeholder", "mandatory", "multi_choice_options",
      "created_at", "modified_by"]

  def __init__(self, title=None, id=None, href=None, type=None,
               definition_type=None, attribute_type=None, helptext=None,
               placeholder=None, mandatory=None, multi_choice_options=None,
               created_at=None, modified_by=None):
    super(CustomAttributeEntity, self).__init__()
    # REST and UI
    self.title = title
    self.id = id
    self.href = href
    self.type = type
    self.definition_type = definition_type
    self.attribute_type = attribute_type
    self.helptext = helptext
    self.placeholder = placeholder
    self.mandatory = mandatory
    self.multi_choice_options = multi_choice_options
    # REST
    self.created_at = created_at  # to generate same CAs values
    self.modified_by = modified_by

  def __lt__(self, other):
    return self.title < other.title


class ProgramEntity(Entity):
  """Class that represent model for Program."""
  # pylint: disable=too-many-instance-attributes
  __hash__ = None

  attrs_names_to_compare = [
      "custom_attributes", "manager", "os_state", "slug", "status", "title",
      "type", "updated_at"]
  attrs_names_to_repr = Representation.core_attrs_names_to_repr + [
      "status", "manager", "contact", "secondary_contact", "updated_at",
      "custom_attributes"]

  def __init__(self, status=None, manager=None, contact=None,
               secondary_contact=None, updated_at=None, os_state=None,
               custom_attribute_definitions=None, custom_attribute_values=None,
               custom_attributes=None):
    super(ProgramEntity, self).__init__()
    # REST and UI
    self.status = status  # state
    self.manager = manager  # predefined
    self.contact = contact  # primary contact
    self.secondary_contact = secondary_contact
    self.updated_at = updated_at  # last updated datetime
    # REST
    self.os_state = os_state  # review state (e.g. "Unreviewed")
    self.custom_attribute_definitions = custom_attribute_definitions
    self.custom_attribute_values = custom_attribute_values
    # additional
    self.custom_attributes = custom_attributes  # map of cas def and values


class ControlEntity(Entity):
  """Class that represent model for Control."""
  # pylint: disable=too-many-instance-attributes
  __hash__ = None

  attrs_names_to_compare = [
      "custom_attributes", "os_state", "slug", "status", "title", "type",
      "updated_at", "owners"]
  attrs_names_to_repr = Representation.core_attrs_names_to_repr + [
      "status", "contact", "secondary_contact", "updated_at",
      "os_state", "custom_attributes", "access_control_list", "owners"]

  def __init__(self, status=None, owners=None, contact=None,
               secondary_contact=None, updated_at=None, os_state=None,
               custom_attribute_definitions=None, custom_attribute_values=None,
               custom_attributes=None, access_control_list=None):
    super(ControlEntity, self).__init__()
    # REST and UI
    self.status = status  # state (e.g. "Draft")
    self.contact = contact  # primary contact
    self.secondary_contact = secondary_contact
    self.updated_at = updated_at  # last updated datetime
    self.os_state = os_state  # review state (e.g. "Unreviewed")
    # REST
    self.owners = owners
    self.custom_attribute_definitions = custom_attribute_definitions
    self.custom_attribute_values = custom_attribute_values
    # additional
    self.custom_attributes = custom_attributes  # map of cas def and values
    self.access_control_list = access_control_list


class ObjectiveEntity(Entity):
  """Class that represent model for Objective."""
  # pylint: disable=too-many-instance-attributes
  __hash__ = None

  attrs_names_to_compare = [
      "custom_attributes", "os_state", "slug", "status", "title", "type",
      "updated_at"]
  attrs_names_to_repr = Representation.core_attrs_names_to_repr + [
      "status", "contact", "secondary_contact", "updated_at",
      "os_state", "custom_attributes", "access_control_list"]

  def __init__(self, status=None, owners=None, contact=None,
               secondary_contact=None, updated_at=None, os_state=None,
               custom_attribute_definitions=None, custom_attribute_values=None,
               custom_attributes=None, access_control_list=None):
    super(ObjectiveEntity, self).__init__()
    # REST and UI
    self.status = status  # state
    self.contact = contact  # primary contact
    self.secondary_contact = secondary_contact
    self.updated_at = updated_at  # last updated
    self.os_state = os_state  # review state
    # REST
    self.owners = owners
    self.custom_attribute_definitions = custom_attribute_definitions
    self.custom_attribute_values = custom_attribute_values
    # additional
    self.custom_attributes = custom_attributes  # map of cas def and values
    self.access_control_list = access_control_list


class AuditEntity(Entity):
  """Class that represent model for Audit."""
  # pylint: disable=too-many-instance-attributes
  __hash__ = None

  attrs_names_to_compare = [
      "contact", "custom_attributes", "slug", "status", "title", "type",
      "updated_at"]
  attrs_names_to_repr = Representation.core_attrs_names_to_repr + [
      "status", "program", "contact", "updated_at", "custom_attributes"]

  def __init__(self, status=None, program=None, contact=None,
               updated_at=None, custom_attribute_definitions=None,
               custom_attribute_values=None, custom_attributes=None):
    super(AuditEntity, self).__init__()
    # REST and UI
    self.status = status  # status (e.g. "Planned")
    self.contact = contact  # audit captain
    self.updated_at = updated_at  # last updated datetime
    # REST
    self.custom_attribute_definitions = custom_attribute_definitions
    self.custom_attribute_values = custom_attribute_values
    # additional
    self.program = program  # program title
    self.custom_attributes = custom_attributes  # map of cas def and values


class AssessmentTemplateEntity(Entity):
  """Class that represent model for Assessment Template."""
  # pylint: disable=superfluous-parens
  # pylint: disable=too-many-instance-attributes
  __hash__ = None

  attrs_names_to_compare = [
      "custom_attributes", "slug", "title", "type", "updated_at"]
  attrs_names_to_repr = Representation.core_attrs_names_to_repr + [
      "audit", "template_object_type", "updated_at", "custom_attributes"]

  def __init__(self, audit=None, default_people=None,
               template_object_type=None, updated_at=None,
               custom_attribute_definitions=None,
               custom_attribute_values=None, custom_attributes=None):
    super(AssessmentTemplateEntity, self).__init__()
    # REST and UI
    self.default_people = default_people  # {"verifiers": *, "assessors": *}
    self.template_object_type = template_object_type  # objs under asmt
    self.updated_at = updated_at  # last updated datetime
    # REST
    self.custom_attribute_definitions = custom_attribute_definitions
    self.custom_attribute_values = custom_attribute_values
    # additional
    self.audit = audit  # audit title
    self.custom_attributes = custom_attributes  # map of cas def and values


class AssessmentEntity(Entity):
  """Class that represent model for Assessment."""
  # pylint: disable=too-many-instance-attributes
  # pylint: disable=redefined-builtin
  # pylint: disable=too-many-locals
  # pylint: disable=duplicate-code
  __hash__ = None

  attrs_names_to_compare = [
      "assessor", "creator", "verifier", "custom_attributes",
      "objects_under_assessment", "slug", "status", "title", "type",
      "updated_at", "verified", "comments"]
  attrs_names_to_repr = Representation.core_attrs_names_to_repr + [
      "status", "audit", "assessor", "creator", "verifier", "verified",
      "updated_at", "objects_under_assessment", "custom_attributes",
      "comments"]

  def __init__(self, status=None, audit=None, owners=None, recipients=None,
               assignees=None, assessor=None, creator=None, verifier=None,
               verified=None, updated_at=None, objects_under_assessment=None,
               os_state=None, custom_attribute_definitions=None,
               custom_attribute_values=None, custom_attributes=None,
               comments=None):
    super(AssessmentEntity, self).__init__()
    # REST and UI
    self.status = status  # state (e.g. "Not Started")
    self.assessor = assessor  # assignees
    self.creator = creator  # creators
    self.verifier = verifier  # verifiers
    self.verified = verified
    self.updated_at = updated_at  # last updated datetime
    self.objects_under_assessment = objects_under_assessment  # mapped objs
    # REST
    # {"Assessor": [{}, {}], "Creator": [{}, {}], "Verifier": [{}, {}]}
    self.assignees = assignees
    self.owners = owners
    self.os_state = os_state  # review state (e.g. "Unreviewed")
    self.recipients = recipients  # "Verifier,Assessor,Creator"
    self.custom_attribute_definitions = custom_attribute_definitions
    self.custom_attribute_values = custom_attribute_values
    # additional
    self.audit = audit  # audit title
    self.custom_attributes = custom_attributes  # map of cas def and values
    # [{"modified_by": *, "created_at": *, "description": *}, {}]
    self.comments = comments


class IssueEntity(Entity):
  """Class that represent model for Issue."""
  # pylint: disable=too-many-instance-attributes
  __hash__ = None

  attrs_names_to_compare = [
      "type", "title", "slug", "status", "contact"]
  attrs_names_to_repr = Representation.core_attrs_names_to_repr + [
      "status", "audit", "contact", "secondary_contact", "updated_at",
      "custom_attributes", "access_control_list"]

  def __init__(self, status=None, audit=None, owners=None,
               contact=None, secondary_contact=None, updated_at=None,
               custom_attribute_definitions=None, os_state=None,
               custom_attribute_values=None, custom_attributes=None,
               access_control_list=None):
    super(IssueEntity, self).__init__()
    # REST and UI
    self.status = status  # state
    self.contact = contact  # primary contact
    self.secondary_contact = secondary_contact
    self.updated_at = updated_at  # last updated datetime
    # REST
    self.owners = owners
    self.os_state = os_state  # review state (e.g. "Unreviewed")
    self.custom_attribute_definitions = custom_attribute_definitions
    self.custom_attribute_values = custom_attribute_values
    # additional
    self.audit = audit  # audit title
    self.custom_attributes = custom_attributes  # map of cas def and values
    self.access_control_list = access_control_list
