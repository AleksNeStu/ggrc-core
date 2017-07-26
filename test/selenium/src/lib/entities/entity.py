# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Create, description, representation and equal of entities."""
# pylint: disable=too-many-arguments
# pylint: disable=too-few-public-methods

from datetime import datetime
import pytest

from lib.utils import string_utils


class Representation(object):
  """Class that contains methods to update Entity."""
  # pylint: disable=import-error

  diff_info = None  # {"equal": {"atr7": val7, ...}, "diff": {"atr3": val3}}
  attrs_names_to_compare = None
  attrs_names_to_repr = None
  core_attrs_names_to_repr = ["type", "title", "id", "href", "url", "slug"]

  def extended_equal(self, other):
    """Extended equal procedure fore self and other entities."""
    comparison = Representation.compare_entities(self, other)
    self.diff_info = comparison["self_diff"]
    other.diff_info = comparison["other_diff"]
    return comparison["is_equal"]

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

  def repr_ui(self):
    """Convert entity's attributes values from REST like to UI like
    representation.
    """
    from lib.entities import entities_factory
    return (entities_factory.EntitiesFactory().
            convert_objs_repr_from_rest_to_ui(obj_or_objs=self))

  def repr_snapshot(self, parent_obj):
    """Convert entity's attributes values to Snapshot representation."""
    from lib.entities import entities_factory
    return (entities_factory.EntitiesFactory().
            convert_objs_repr_to_snapshot(
                obj_or_objs=self, parent_obj=parent_obj))

  def update_attrs(self, is_replace_attrs=True, is_allow_none=True,
                   is_replace_dicts_values=False, **attrs):
    """Update entity's attributes values according to entered data
    (dictionaries of attributes and values).
    If 'is_replace_values_of_dicts' then update values of dicts in list which
    is value of particular object's attribute name.
    """
    from lib.entities import entities_factory
    return (entities_factory.EntitiesFactory().
            update_objs_attrs_values_by_entered_data(
                obj_or_objs=self, is_replace_attrs_values=is_replace_attrs,
                is_allow_none_values=is_allow_none,
                is_replace_values_of_dicts=is_replace_dicts_values, **attrs))

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
              attr_name, self_attr_value, other_attr_value)
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

  @staticmethod
  def attrs_values_types_error(self_attr, other_attr, expected_types):
    raise ValueError("'{}' have to be isinstance of classes: {}\n".
                     format((self_attr, other_attr), expected_types))

  @classmethod
  def issue_assert(cls, expected_objs, actual_objs, issue_msg,
                   **exclude_attrs):
    """Assert list of self (expected) and other (actual) objects according to
    dictionary of attributes to exclude due to exist issue providing
    description of it.
    """
    from lib.constants import messages
    expected_objs = string_utils.convert_to_list(expected_objs)
    actual_objs = string_utils.convert_to_list(actual_objs)
    expected_exclude_attrs = [
        {k: getattr(expected_obj, k) for k in exclude_attrs.iterkeys()}
        for expected_obj in expected_objs]
    actual_exclude_attrs = [
        {k: getattr(actual_obj, k) for k in exclude_attrs.iterkeys()}
        for actual_obj in actual_objs]
    expected_objs_wo_exclude_attrs = [
        expected_obj.update_attrs(**exclude_attrs)
        for expected_obj in expected_objs]
    actual_objs_wo_exclude_attrs = [
        actual_obj.update_attrs(**exclude_attrs)
        for actual_obj in actual_objs]
    assert expected_objs_wo_exclude_attrs == actual_objs_wo_exclude_attrs, (
        messages.AssertionMessages.format_err_msg_equal(
            expected_objs_wo_exclude_attrs, actual_objs_wo_exclude_attrs))
    return (True if all(all((exp_k == act_k and cls.is_attrs_equal(
        attr_name=exp_k, self_attr_value=expected_exclude_attr[exp_k],
        other_attr_value=actual_exclude_attr[exp_k])) for exp_k, act_k
        in zip(expected_exclude_attr.keys(), actual_exclude_attr.keys()))
        for expected_exclude_attr, actual_exclude_attr
        in zip(expected_exclude_attrs, actual_exclude_attrs))
        else pytest.xfail(reason=issue_msg))

  def __eq__(self, other):
    return self.extended_equal(other)

  def __repr__(self):
    # exclude attributes witch are used for REST interaction forming
    # pylint: disable=not-an-iterable
    return str(dict(zip(self.attrs_names_to_repr,
                        [getattr(self, attr_name_to_repr) for attr_name_to_repr
                         in self.attrs_names_to_repr])))


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
  entity = Entity()
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
    self.contact = contact  # internal audit lead
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

  def __init__(self, status=None, audit=None, owners=None,
               recipients=None, assignees=None, assessor=None, creator=None,
               verifier=None, verified=None, updated_at=None,
               objects_under_assessment=None, os_state=None,
               custom_attribute_definitions=None, custom_attribute_values=None,
               custom_attributes=None, comments=None):
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
