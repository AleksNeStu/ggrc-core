# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Factories that create entities."""
# pylint: disable=too-many-arguments
# pylint: disable=invalid-name
# pylint: disable=redefined-builtin

import copy
import random

from datetime import datetime

from lib.constants import element, objects, roles, url as const_url
from lib.constants.element import AdminWidgetCustomAttributes
from lib.entities.entity import (
    Entity, PersonEntity, CustomAttributeEntity, ProgramEntity, ControlEntity,
    ObjectiveEntity, AuditEntity, AssessmentTemplateEntity, AssessmentEntity,
    IssueEntity, CommentEntity)
from lib.utils import string_utils, help_utils
from lib.utils.string_utils import (random_list_strings, random_string,
                                    random_uuid)


class EntitiesFactory(object):
  """Common factory class for entities."""
  # pylint: disable=too-few-public-methods
  obj_person = unicode(objects.get_singular(objects.PEOPLE, title=True))
  obj_program = unicode(objects.get_singular(objects.PROGRAMS, title=True))
  obj_control = unicode(objects.get_singular(objects.CONTROLS, title=True))
  obj_objective = unicode(objects.get_singular(objects.OBJECTIVES, title=True))
  obj_audit = unicode(objects.get_singular(objects.AUDITS, title=True))
  obj_asmt_tmpl = unicode(objects.get_singular(
      objects.ASSESSMENT_TEMPLATES, title=True))
  obj_asmt = unicode(objects.get_singular(objects.ASSESSMENTS, title=True))
  obj_issue = unicode(objects.get_singular(objects.ISSUES, title=True))
  obj_ca = unicode(objects.get_singular(objects.CUSTOM_ATTRIBUTES))
  obj_comment = unicode(objects.get_singular(objects.COMMENTS, title=True))
  obj_snapshot = unicode(objects.get_singular(objects.SNAPSHOTS, title=True))

  types_of_values_ui_like_attrs = (str, unicode, int)
  all_objs_attrs_names = Entity().get_attrs_names_for_entities()
  all_entities_classes = tuple(Entity().all_entities_classes())

  @staticmethod
  def convert_dict_to_obj_repr(dic):
    """Convert dictionary to fake Entity representation."""
    # pylint: disable=redefined-outer-name
    # pylint: disable=old-style-class
    class Entity:
      """Object got after converting dictionary."""
      def __init__(self, dic):
        self.__dict__.update(dic)
    return Entity(dic)

  @classmethod
  def convert_objs_repr_to_dict(cls, obj_or_objs):
    """Convert object' or objects from object representation
    'obj.attr_name' = 'attr_value' to dictionary or list of dictionaries with
    items {'attr_name': 'attr_value'}.
    """
    if obj_or_objs:
      if isinstance(obj_or_objs, list):
        if (all(not isinstance(_, dict) and
                not isinstance(_, cls.types_of_values_ui_like_attrs) and
                _ for _ in obj_or_objs)):
          obj_or_objs = [_.__dict__ for _ in obj_or_objs]
      else:
        if (not isinstance(obj_or_objs, dict) and
                not isinstance(
                    obj_or_objs, cls.types_of_values_ui_like_attrs)):
          obj_or_objs = obj_or_objs.__dict__
      return obj_or_objs

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
        obj_or_objs=obj_or_objs, types=cls.all_entities_classes,
        method_name=convert_obj_repr_to_snapshot, parent_obj=parent_obj)

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
            converted_attr_value = unicode(attr_value.get("name"))
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
                k: (string_utils.convert_str_to_datetime(v) if
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
        # u'2017-06-07T16:50:16' and u'2017-06-07 16:50:16' to datetime
        if (obj_attr_name in ["updated_at", "created_at"] and
                isinstance(obj_attr_value, unicode)):
          obj_attr_value = string_utils.convert_str_to_datetime(obj_attr_value)
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
          cas_val_dicts_keys = ([_.keys()[0] for _ in cas_val] if
                                isinstance(cas_val, list) else [None])
          _cas_val = [
              {k: v} for k, v in
              CustomAttributeDefinitionsFactory().generate_ca_values(
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
        obj_or_objs=obj_or_objs, types=cls.all_entities_classes,
        method_name=convert_obj_repr_from_rest_to_ui)

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
    def update_obj_attrs_values(obj, is_replace_attrs_values,
                                is_allow_none_values, **arguments):
      """Update object's attributes values."""
      for obj_attr_name in arguments:
        if (obj_attr_name in
                Entity().get_attrs_names_for_entities(obj.__class__)):
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
        obj_or_objs=obj_or_objs, types=cls.all_entities_classes,
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

  @classmethod
  def generate_string(cls, first_part):
    """Generate string in unicode format according object type and random data.
    """
    special_chars = string_utils.SPECIAL
    return unicode("{first_part}_{uuid}_{rand_str}".format(
        first_part=first_part, uuid=random_uuid(),
        rand_str=random_string(size=len(special_chars), chars=special_chars)))

  @classmethod
  def generate_slug(cls):
    """Generate slug in unicode format according str part and random data."""
    return unicode("{slug}".format(slug=random_uuid()))

  @classmethod
  def generate_email(cls, domain=const_url.DEFAULT_EMAIL_DOMAIN):
    """Generate email in unicode format according to domain."""
    return unicode("{mail_name}@{domain}".format(
        mail_name=random_uuid(), domain=domain))


class CommentsFactory(EntitiesFactory):
  """Factory class for Comments entities."""
  # pylint: disable=too-many-locals

  obj_attrs_names = Entity().get_attrs_names_for_entities(CommentEntity)

  @classmethod
  def create_empty(cls):
    """Create blank Comment object."""
    empty_comment = CommentEntity()
    empty_comment.type = cls.obj_comment
    return empty_comment

  @classmethod
  def create(cls, type=None, id=None, href=None, modified_by=None,
             created_at=None, description=None):
    """Create Comment object.
    Random values will be used for description.
    Predictable values will be used for type, owners, modified_by.
    """
    comment_entity = cls._create_random_comment()
    comment_entity = cls.update_objs_attrs_values_by_entered_data(
        obj_or_objs=comment_entity, is_allow_none_values=False, type=type,
        id=id, href=href, modified_by=modified_by,
        created_at=created_at, description=description)
    return comment_entity

  @classmethod
  def _create_random_comment(cls):
    """Create Comment entity with randomly and predictably filled fields."""
    random_comment = CommentEntity()
    random_comment.type = cls.obj_comment
    random_comment.modified_by = ObjectPersonsFactory().default().__dict__
    random_comment.description = cls.generate_string(cls.obj_comment)
    return random_comment


class ObjectPersonsFactory(EntitiesFactory):
  """Factory class for Persons entities."""

  obj_attrs_names = Entity().get_attrs_names_for_entities(PersonEntity)

  @classmethod
  def default(cls):
    """Create default system Person object."""
    return cls.create(
        name=roles.DEFAULT_USER, id=1, href=const_url.DEFAULT_USER_HREF,
        email=const_url.DEFAULT_USER_EMAIL, system_wide_role=roles.SUPERUSER)

  @classmethod
  def create(cls, type=None, id=None, name=None, href=None, url=None,
             email=None, company=None, system_wide_role=None, updated_at=None,
             custom_attribute_definitions=None, custom_attribute_values=None,
             custom_attributes=None):
    """Create Person object.
    Random values will be used for name.
    Predictable values will be used for type, email and system_wide_role.
    """
    person_entity = cls._create_random_person()
    person_entity = cls.update_objs_attrs_values_by_entered_data(
        obj_or_objs=person_entity, is_allow_none_values=False, type=type,
        id=id, name=name, href=href, url=url, email=email, company=company,
        system_wide_role=system_wide_role, updated_at=updated_at,
        custom_attribute_definitions=custom_attribute_definitions,
        custom_attribute_values=custom_attribute_values,
        custom_attributes=custom_attributes)
    return person_entity

  @classmethod
  def get_acl_member(cls, role_id, person):
    return {"ac_role_id": role_id, "person": person}

  @classmethod
  def _create_random_person(cls):
    """Create Person entity with randomly filled fields."""
    random_person = PersonEntity()
    random_person.type = cls.obj_person
    random_person.name = cls.generate_string(cls.obj_person)
    random_person.email = cls.generate_email()
    random_person.system_wide_role = unicode(roles.SUPERUSER)
    return random_person


class CustomAttributeDefinitionsFactory(EntitiesFactory):
  """Factory class for entities."""

  obj_attrs_names = Entity().get_attrs_names_for_entities(
      CustomAttributeEntity)

  @classmethod
  def generate_ca_values(cls, list_ca_def_objs, is_none_values=False):
    """Generate dictionary of CA random values from exist list CA definitions
    objects according to CA 'id', 'attribute_type' and 'multi_choice_options'
    for Dropdown. Return dictionary of CA items that ready to use via REST API:
    If 'is_none_values' then generate None like CA values according to CA
    definitions types.
    Example:
    list_ca_objs = [{'attribute_type': 'Text', 'id': 1},
    {'attribute_type': 'Dropdown', 'id': 2, 'multi_choice_options': 'a,b,c'}]
    :return {"1": "text_example", "2": "b"}
    """
    def generate_ca_value(ca):
      """Generate CA value according to CA 'id', 'attribute_type' and
      'multi_choice_options' for Dropdown.
      """
      if not isinstance(ca, dict):
        ca = ca.__dict__
      ca_attr_type = ca.get("attribute_type")
      ca_value = None
      if ca_attr_type in AdminWidgetCustomAttributes.ALL_CA_TYPES:
        if not is_none_values:
          if ca_attr_type in (AdminWidgetCustomAttributes.TEXT,
                              AdminWidgetCustomAttributes.RICH_TEXT):
            ca_value = cls.generate_string(ca_attr_type)
          if ca_attr_type == AdminWidgetCustomAttributes.DATE:
            ca_value = unicode(ca["created_at"][:10])
          if ca_attr_type == AdminWidgetCustomAttributes.CHECKBOX:
            ca_value = random.choice((True, False))
          if ca_attr_type == AdminWidgetCustomAttributes.DROPDOWN:
            ca_value = unicode(
                random.choice(ca["multi_choice_options"].split(",")))
          if ca_attr_type == AdminWidgetCustomAttributes.PERSON:
            ca_value = ":".join([unicode(ca["modified_by"]["type"]),
                                 unicode(ca["modified_by"]["id"])])
        else:
          ca_value = (
              None if ca_attr_type != AdminWidgetCustomAttributes.CHECKBOX
              else u"0")
      return {ca["id"]: ca_value}
    return {k: v for _ in [generate_ca_value(ca) for ca in list_ca_def_objs]
            for k, v in _.items()}

  @classmethod
  def generate_ca_defenitions_for_asmt_tmpls(cls, list_ca_definitions):
    """Generate list of dictionaries of CA random values from exist list CA
    definitions according to CA 'title', 'attribute_type' and
    'multi_choice_options' for Dropdown. Return list of dictionaries of CA
    definitions that ready to use via REST API:
    Example:
    :return
    [{"title": "t1", "attribute_type": "Text", "multi_choice_options": ""},
     {"title":"t2", "attribute_type":"Rich Text", "multi_choice_options":""}]
    """
    return [{k: (v if v else "") for k, v in ca_def.__dict__.items()
             if k in ("title", "attribute_type", "multi_choice_options")}
            for ca_def in list_ca_definitions]

  @classmethod
  def create(cls, title=None, id=None, href=None, type=None,
             definition_type=None, attribute_type=None, helptext=None,
             placeholder=None, mandatory=None, multi_choice_options=None,
             updated_at=None, modified_by=None):
    """Create Custom Attribute object. CA object attribute 'definition_type'
    is used as default for REST operations e.g. 'risk_assessment', for UI
    operations need convert to normal form used method objects.get_normal_form
    e.q. 'Risk Assessments'.
    Random values will be used for title, attribute_type, definition_type and
    multi_choice_options if randomly generated attribute_type is 'Dropdown'.
    """
    ca_entity = cls._create_random_ca()
    ca_entity = cls._update_ca_attrs_values(
        obj=ca_entity, is_allow_none_values=False, title=title, id=id,
        href=href, type=type, definition_type=definition_type,
        attribute_type=attribute_type, helptext=helptext,
        placeholder=placeholder, mandatory=mandatory,
        multi_choice_options=multi_choice_options, updated_at=updated_at,
        modified_by=modified_by)
    return ca_entity

  @classmethod
  def _create_random_ca(cls):
    """Create CustomAttribute entity with randomly filled fields."""
    random_ca = CustomAttributeEntity()
    random_ca.type = cls.obj_ca
    random_ca.attribute_type = unicode(random.choice(
        AdminWidgetCustomAttributes.ALL_CA_TYPES))
    random_ca.title = cls.generate_string(random_ca.attribute_type)
    if random_ca.attribute_type == AdminWidgetCustomAttributes.DROPDOWN:
      random_ca.multi_choice_options = random_list_strings()
    random_ca.definition_type = unicode(objects.get_singular(
        random.choice(objects.ALL_CA_OBJS)))
    random_ca.mandatory = False
    return random_ca

  @classmethod
  def _update_ca_attrs_values(cls, obj, **arguments):
    """Update CA's (obj) attributes values according to dictionary of
    arguments (key = value). Restrictions: 'multi_choice_options' is a
    mandatory attribute for Dropdown CA and 'placeholder' is a attribute that
    exists only for Text and Rich Text CA.
    Generated data - 'obj', entered data - '**arguments'.
    """
    # fix generated data
    if arguments.get("attribute_type"):
      obj.title = cls.generate_string(arguments["attribute_type"])
    if (obj.multi_choice_options and
            obj.attribute_type == AdminWidgetCustomAttributes.DROPDOWN and
            arguments.get("attribute_type") !=
            AdminWidgetCustomAttributes.DROPDOWN):
      obj.multi_choice_options = None
    # fix entered data
    if (arguments.get("multi_choice_options") and
            arguments.get("attribute_type") !=
            AdminWidgetCustomAttributes.DROPDOWN):
      arguments["multi_choice_options"] = None
    if (arguments.get("placeholder") and arguments.get("attribute_type") not in
        (AdminWidgetCustomAttributes.TEXT,
         AdminWidgetCustomAttributes.RICH_TEXT)):
      arguments["placeholder"] = None
    # extend entered data
    if (arguments.get("attribute_type") ==
            AdminWidgetCustomAttributes.DROPDOWN and not
            obj.multi_choice_options):
      obj.multi_choice_options = random_list_strings()
    return cls.update_objs_attrs_values_by_entered_data(
        obj_or_objs=obj, **arguments)


class ProgramsFactory(EntitiesFactory):
  """Factory class for Programs entities."""
  # pylint: disable=too-many-locals

  obj_attrs_names = Entity().get_attrs_names_for_entities(ProgramEntity)

  @classmethod
  def create_empty(cls):
    """Create blank Program object."""
    empty_program = ProgramEntity()
    empty_program.type = cls.obj_program
    empty_program.custom_attributes = {None: None}
    return empty_program

  @classmethod
  def create(cls, type=None, id=None, title=None, href=None, url=None,
             slug=None, status=None, manager=None, contact=None,
             secondary_contact=None, updated_at=None, os_state=None,
             custom_attribute_definitions=None, custom_attribute_values=None,
             custom_attributes=None):
    """Create Program object.
    Random values will be used for title and slug.
    Predictable values will be used for type, status, manager, contact.
    """
    program_entity = cls._create_random_program()
    program_entity = cls.update_objs_attrs_values_by_entered_data(
        obj_or_objs=program_entity, is_allow_none_values=False, type=type,
        id=id, title=title, href=href, url=url, slug=slug, status=status,
        manager=manager, contact=contact, secondary_contact=secondary_contact,
        updated_at=updated_at, os_state=os_state,
        custom_attribute_definitions=custom_attribute_definitions,
        custom_attribute_values=custom_attribute_values,
        custom_attributes=custom_attributes)
    return program_entity

  @classmethod
  def _create_random_program(cls):
    """Create Program entity with randomly and predictably filled fields."""
    random_program = ProgramEntity()
    random_program.type = cls.obj_program
    random_program.title = cls.generate_string(cls.obj_program)
    random_program.slug = cls.generate_slug()
    random_program.status = unicode(element.ObjectStates.DRAFT)
    random_program.manager = ObjectPersonsFactory().default().__dict__
    random_program.contact = ObjectPersonsFactory().default().__dict__
    return random_program


class ControlsFactory(EntitiesFactory):
  """Factory class for Controls entities."""
  # pylint: disable=too-many-locals

  obj_attrs_names = Entity().get_attrs_names_for_entities(ControlEntity)

  @classmethod
  def create_empty(cls):
    """Create blank Control object."""
    empty_control = ControlEntity()
    empty_control.type = cls.obj_control
    empty_control.custom_attributes = {None: None}
    empty_control.access_control_list = []
    return empty_control

  @classmethod
  def create(cls, type=None, id=None, title=None, href=None, url=None,
             slug=None, status=None, owners=None, contact=None,
             secondary_contact=None, updated_at=None, os_state=None,
             custom_attribute_definitions=None, custom_attribute_values=None,
             custom_attributes=None, access_control_list=None):
    """Create Control object.
    Random values will be used for title and slug.
    Predictable values will be used for type, status, owners and contact.
    """
    control_entity = cls._create_random_control()
    control_entity = cls.update_objs_attrs_values_by_entered_data(
        obj_or_objs=control_entity, is_allow_none_values=False, type=type,
        id=id, title=title, href=href, url=url, slug=slug, status=status,
        owners=owners, contact=contact, secondary_contact=secondary_contact,
        updated_at=updated_at, os_state=os_state,
        custom_attribute_definitions=custom_attribute_definitions,
        custom_attribute_values=custom_attribute_values,
        custom_attributes=custom_attributes,
        access_control_list=access_control_list)
    return control_entity

  @classmethod
  def _create_random_control(cls):
    """Create Control entity with randomly and predictably filled fields."""
    random_control = ControlEntity()
    random_control.type = cls.obj_control
    random_control.title = cls.generate_string(cls.obj_control)
    random_control.slug = cls.generate_slug()
    random_control.status = unicode(element.ObjectStates.DRAFT)
    random_control.contact = ObjectPersonsFactory().default().__dict__
    random_control.owners = [ObjectPersonsFactory().default().__dict__]
    random_control.access_control_list = [
        ObjectPersonsFactory().get_acl_member(roles.ADMIN_ID,
                                              random_control.owners[0]),
        ObjectPersonsFactory().get_acl_member(roles.PRIMARY_CONTACT_ID,
                                              random_control.contact)]
    return random_control


class ObjectivesFactory(EntitiesFactory):
  """Factory class for Objectives entities."""
  # pylint: disable=too-many-locals

  obj_attrs_names = Entity().get_attrs_names_for_entities(ObjectiveEntity)

  @classmethod
  def create_empty(cls):
    """Create blank Objective object."""
    empty_objective = ObjectiveEntity()
    empty_objective.type = cls.obj_objective
    empty_objective.custom_attributes = {None: None}
    return empty_objective

  @classmethod
  def create(cls, type=None, id=None, title=None, href=None, url=None,
             slug=None, status=None, owners=None, contact=None,
             secondary_contact=None, updated_at=None, os_state=None,
             custom_attribute_definitions=None, custom_attribute_values=None,
             custom_attributes=None):
    """Create Objective object.
    Random values will be used for title and slug.
    Predictable values will be used for type, status, owners.
    """
    objective_entity = cls._create_random_objective()
    objective_entity = cls.update_objs_attrs_values_by_entered_data(
        obj_or_objs=objective_entity, is_allow_none_values=False, type=type,
        id=id, title=title, href=href, url=url, slug=slug, status=status,
        owners=owners, contact=contact, secondary_contact=secondary_contact,
        updated_at=updated_at, os_state=os_state,
        custom_attribute_definitions=custom_attribute_definitions,
        custom_attribute_values=custom_attribute_values,
        custom_attributes=custom_attributes)
    return objective_entity

  @classmethod
  def _create_random_objective(cls):
    """Create Objective entity with randomly and predictably filled fields."""
    random_objective = ObjectiveEntity()
    random_objective.type = cls.obj_objective
    random_objective.title = cls.generate_string(cls.obj_objective)
    random_objective.slug = cls.generate_slug()
    random_objective.status = unicode(element.ObjectStates.DRAFT)
    random_objective.owners = [ObjectPersonsFactory().default().__dict__]
    return random_objective


class AuditsFactory(EntitiesFactory):
  """Factory class for Audit entity."""

  obj_attrs_names = Entity().get_attrs_names_for_entities(AuditEntity)

  @classmethod
  def clone(cls, audit, count_to_clone=1):
    """Clone Audit object.
    Predictable values will be used for type, title.
    """
    # pylint: disable=anomalous-backslash-in-string
    return [cls.update_objs_attrs_values_by_entered_data(
        obj_or_objs=copy.deepcopy(audit),
        title=audit.title + " - copy " + str(num),
        slug=None, updated_at=None, href=None, url=None, id=None)
        for num in xrange(1, count_to_clone + 1)]

  @classmethod
  def create_empty(cls):
    """Create blank Audit object."""
    empty_audit = AuditEntity()
    empty_audit.type = cls.obj_audit
    empty_audit.custom_attributes = {None: None}
    return empty_audit

  @classmethod
  def create(cls, type=None, id=None, title=None, href=None, url=None,
             slug=None, status=None, program=None, contact=None,
             updated_at=None, custom_attribute_definitions=None,
             custom_attribute_values=None, custom_attributes=None):
    """Create Audit object.
    Random values will be used for title and slug.
    Predictable values will be used for type, status, contact.
    """
    audit_entity = cls._create_random_audit()
    audit_entity = cls.update_objs_attrs_values_by_entered_data(
        obj_or_objs=audit_entity, is_allow_none_values=False, type=type,
        id=id, title=title, href=href, url=url, slug=slug, status=status,
        program=program, contact=contact, updated_at=updated_at,
        custom_attribute_definitions=custom_attribute_definitions,
        custom_attribute_values=custom_attribute_values,
        custom_attributes=custom_attributes)
    return audit_entity

  @classmethod
  def _create_random_audit(cls):
    """Create Audit entity with randomly and predictably filled fields."""
    random_audit = AuditEntity()
    random_audit.type = cls.obj_audit
    random_audit.title = cls.generate_string(cls.obj_audit)
    random_audit.slug = cls.generate_slug()
    random_audit.status = unicode(element.AuditStates().PLANNED)
    random_audit.contact = ObjectPersonsFactory().default().__dict__
    return random_audit


class AssessmentTemplatesFactory(EntitiesFactory):
  """Factory class for Assessment Templates entities."""

  obj_attrs_names = Entity().get_attrs_names_for_entities(
      AssessmentTemplateEntity)

  @classmethod
  def clone(cls, asmt_tmpl, count_to_clone=1):
    """Clone Assessment Template object.
    Predictable values will be used for type, title.
    """
    # pylint: disable=anomalous-backslash-in-string
    return [cls.update_objs_attrs_values_by_entered_data(
        obj_or_objs=copy.deepcopy(asmt_tmpl), slug=None, updated_at=None,
        href=None, url=None, id=None) for _ in xrange(1, count_to_clone + 1)]

  @classmethod
  def create_empty(cls):
    """Create blank Assessment Template object."""
    empty_asmt_tmpl = AssessmentTemplateEntity()
    empty_asmt_tmpl.type = cls.obj_asmt_tmpl
    empty_asmt_tmpl.custom_attributes = {None: None}
    return empty_asmt_tmpl

  @classmethod
  def create(cls, type=None, id=None, title=None, href=None, url=None,
             slug=None, audit=None, default_people=None,
             template_object_type=None, updated_at=None,
             custom_attribute_definitions=None, custom_attribute_values=None,
             custom_attributes=None):
    """Create Assessment Template object.
    Random values will be used for title and slug.
    Predictable values will be used for type, template_object_type and
    default_people {"verifiers": *, "assessors": *}.
    """
    # pylint: disable=too-many-locals
    asmt_tmpl_entity = cls._create_random_asmt_tmpl()
    asmt_tmpl_entity = cls.update_objs_attrs_values_by_entered_data(
        obj_or_objs=asmt_tmpl_entity, is_allow_none_values=False, type=type,
        id=id, title=title, href=href, url=url, slug=slug, audit=audit,
        default_people=default_people,
        template_object_type=template_object_type, updated_at=updated_at,
        custom_attribute_definitions=custom_attribute_definitions,
        custom_attribute_values=custom_attribute_values,
        custom_attributes=custom_attributes)
    return asmt_tmpl_entity

  @classmethod
  def _create_random_asmt_tmpl(cls):
    """Create Assessment Template entity with randomly and predictably
    filled fields.
    """
    random_asmt_tmpl = AssessmentTemplateEntity()
    random_asmt_tmpl.type = cls.obj_asmt_tmpl
    random_asmt_tmpl.title = cls.generate_string(cls.obj_asmt_tmpl)
    random_asmt_tmpl.assessors = unicode(roles.AUDIT_LEAD)
    random_asmt_tmpl.slug = cls.generate_slug()
    random_asmt_tmpl.template_object_type = cls.obj_control.title()
    random_asmt_tmpl.default_people = {"verifiers": unicode(roles.AUDITORS),
                                       "assessors": unicode(roles.AUDIT_LEAD)}
    return random_asmt_tmpl


class AssessmentsFactory(EntitiesFactory):
  """Factory class for Assessments entities."""

  obj_attrs_names = Entity().get_attrs_names_for_entities(AssessmentEntity)

  @classmethod
  def generate(cls, objs_under_asmt, audit, asmt_tmpl=None):
    """Generate Assessment objects according to objects under Assessment,
    Audit, Assessment Template.
    If 'asmt_tmpl' then generate with Assessment Template, if not 'asmt_tmpl'
    then generate without Assessment Template. Slug will not be predicted to
    avoid of rising errors in case of tests parallel running. Predictable
    values will be used for type, title, audit, objects_under_assessment
    custom_attribute_definitions and custom_attribute_values.
    """
    # pylint: disable=too-many-locals
    cas_def = asmt_tmpl.custom_attribute_definitions if asmt_tmpl and getattr(
        asmt_tmpl, "custom_attribute_definitions") else None
    asmts_objs = [cls.create(
        title=obj_under_asmt.title + " assessment for " + audit.title,
        audit=audit.title, objects_under_assessment=[obj_under_asmt],
        custom_attribute_definitions=cas_def) for
        obj_under_asmt in objs_under_asmt]
    return [cls.update_objs_attrs_values_by_entered_data(
        obj_or_objs=asmt_obj, slug=None) for asmt_obj in asmts_objs]

  @classmethod
  def create_empty(cls):
    """Create blank Assessment object."""
    empty_asmt = AssessmentEntity()
    empty_asmt.type = cls.obj_asmt
    empty_asmt.verified = False
    empty_asmt.custom_attributes = {None: None}
    return empty_asmt

  @classmethod
  def create(cls, type=None, id=None, title=None, href=None, url=None,
             slug=None, status=None, owners=None, audit=None,
             recipients=None, assignees=None, verified=None, updated_at=None,
             objects_under_assessment=None, os_state=None,
             custom_attribute_definitions=None, custom_attribute_values=None,
             custom_attributes=None):
    """Create Assessment object.
    Random values will be used for title and slug.
    Predictable values will be used for type, status, recipients,
    verified, owners.
    """
    # pylint: disable=too-many-locals
    asmt_entity = cls._create_random_asmt()
    asmt_entity = cls.update_objs_attrs_values_by_entered_data(
        obj_or_objs=asmt_entity, is_allow_none_values=False, type=type, id=id,
        title=title, href=href, url=url, slug=slug, status=status,
        owners=owners, audit=audit, recipients=recipients, assignees=assignees,
        verified=verified, updated_at=updated_at,
        objects_under_assessment=objects_under_assessment, os_state=os_state,
        custom_attribute_definitions=custom_attribute_definitions,
        custom_attribute_values=custom_attribute_values,
        custom_attributes=custom_attributes)
    return asmt_entity

  @classmethod
  def _create_random_asmt(cls):
    """Create Assessment entity with randomly and predictably filled fields."""
    random_asmt = AssessmentEntity()
    random_asmt.type = cls.obj_asmt
    random_asmt.title = cls.generate_string(cls.obj_asmt)
    random_asmt.slug = cls.generate_slug()
    random_asmt.status = unicode(element.AssessmentStates.NOT_STARTED)
    random_asmt.recipients = ",".join(
        (unicode(roles.ASSESSOR), unicode(roles.CREATOR),
         unicode(roles.VERIFIER)))
    random_asmt.verified = False
    random_asmt.assignees = {
        "Assessor": [ObjectPersonsFactory().default().__dict__],
        "Creator": [ObjectPersonsFactory().default().__dict__]}
    return random_asmt


class IssuesFactory(EntitiesFactory):
  """Factory class for Issues entities."""

  obj_attrs_names = Entity().get_attrs_names_for_entities(IssueEntity)

  @classmethod
  def create_empty(cls):
    """Create blank Issue object."""
    empty_issue = IssueEntity
    empty_issue.type = cls.obj_issue
    empty_issue.custom_attributes = {None: None}
    empty_issue.access_control_list = []
    return empty_issue

  @classmethod
  def create(cls, type=None, id=None, title=None, href=None, url=None,
             slug=None, status=None, audit=None, owners=None, contact=None,
             secondary_contact=None, updated_at=None, os_state=None,
             custom_attribute_definitions=None, custom_attribute_values=None,
             custom_attributes=None, access_control_list=None):
    """Create Issue object.
    Random values will be used for title and slug.
    Predictable values will be used for type, status, owners and contact.
    """
    # pylint: disable=too-many-locals
    issue_entity = cls._create_random_issue()
    issue_entity = cls.update_objs_attrs_values_by_entered_data(
        obj_or_objs=issue_entity, is_allow_none_values=False, type=type, id=id,
        title=title, href=href, url=url, slug=slug, status=status, audit=audit,
        owners=owners, contact=contact, secondary_contact=secondary_contact,
        updated_at=updated_at, os_state=os_state,
        custom_attribute_definitions=custom_attribute_definitions,
        custom_attribute_values=custom_attribute_values,
        custom_attributes=custom_attributes,
        access_control_list=access_control_list)
    return issue_entity

  @classmethod
  def _create_random_issue(cls):
    """Create Issue entity with randomly and predictably filled fields."""
    random_issue = IssueEntity()
    random_issue.type = cls.obj_issue
    random_issue.title = cls.generate_string(cls.obj_issue)
    random_issue.slug = cls.generate_slug()
    random_issue.status = unicode(element.IssueStates.DRAFT)
    random_issue.owners = [ObjectPersonsFactory().default().__dict__]
    random_issue.contact = ObjectPersonsFactory().default().__dict__
    random_issue.access_control_list = [
        ObjectPersonsFactory().get_acl_member(roles.ADMIN_ID,
                                              random_issue.owners[0]),
        ObjectPersonsFactory().get_acl_member(roles.PRIMARY_CONTACT_ID,
                                              random_issue.contact)]
    return random_issue
