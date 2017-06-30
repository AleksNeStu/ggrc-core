# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Create, description, representation and equal of entities."""
# pylint: disable=too-many-arguments
# pylint: disable=too-few-public-methods

from lib.constants import element, files
from lib.utils import string_utils


class Representation(object):
  """Class that contains methods to update Entity."""
  # pylint: disable=import-error

  @staticmethod
  def items_of_remap_keys():
    """Get transformation dictionary {'OLD KEY': 'NEW KEY'}, where
    'OLD KEY' - UI elements and CSV fields correspond to
    'NEW KEY' - objects attributes.
    """
    el = element.TransformationSetVisibleFields
    csv = files.TransformationCSVFields
    # common for UI and CSV
    result_remap_items = {
        el.TITLE: "title", el.ADMIN: "owners", el.CODE: "slug",
        el.REVIEW_STATE: "os_state", el.STATE: "status"
    }
    ui_remap_items = {
        el.MANAGER: "manager", el.VERIFIED: "verified",
        el.STATUS: "status", el.LAST_UPDATED: "updated_at",
        el.AUDIT_LEAD: "contact", el.CAS: "custom_attributes",
        el.MAPPED_OBJECTS: "objects_under_assessment",
        el.ASSIGNEES: "assessor", el.CREATORS: "creator",
        el.VERIFIERS: "verifier", el.PRIMARY_CONTACT: "contact"
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
            convert_obj_repr_from_rest_to_ui(obj=self))

  def update_attrs(self, is_replace_attrs=True, is_allow_none=True, **attrs):
    """Update entity's attributes values according to entered data
    (dictionaries of attributes and values).
    """
    from lib.entities import entities_factory
    return (entities_factory.EntitiesFactory().
            update_objs_attrs_values_by_entered_data(
                objs=self, is_replace_attrs_values=is_replace_attrs,
                is_allow_none_values=is_allow_none, **attrs))


class Entity(Representation):
  """Class that represent model for base entity."""
  # pylint: disable=invalid-name
  # pylint: disable=redefined-builtin

  def __init__(self, type=None, id=None, title=None, href=None, url=None):
    self.type = type
    self.id = id
    self.title = title
    self.href = href
    self.url = url

  @staticmethod
  def get_attrs_names_for_entities(entity=None):
    """Get list unique attributes names for entities. If 'entity' then get
    attributes of one entered entity, else get attributes of all entities.
    """
    all_entities_cls = (
        [entity] if entity else
        [PersonEntity, CustomAttributeEntity, ProgramEntity, ControlEntity,
         AuditEntity, AssessmentEntity, AssessmentTemplateEntity, IssueEntity])
    all_entities_attrs_names = string_utils.convert_list_elements_to_list(
        [entity_cls().__dict__.keys() for entity_cls in all_entities_cls])
    return list(set(all_entities_attrs_names))


class PersonEntity(Representation):
  """Class that represent model for Person."""
  # pylint: disable=invalid-name
  # pylint: disable=redefined-builtin
  # pylint: disable=too-many-instance-attributes
  __hash__ = None

  def __init__(self, type=None, id=None, name=None, href=None, url=None,
               email=None, company=None, system_wide_role=None,
               updated_at=None, custom_attribute_definitions=None,
               custom_attribute_values=None, ac_role_id=None):
    super(PersonEntity, self).__init__()
    self.name = name
    self.id = id
    self.href = href
    self.url = url
    self.type = type
    self.email = email
    self.company = company
    self.system_wide_role = system_wide_role  # authorizations
    self.updated_at = updated_at  # last updated
    self.custom_attribute_definitions = custom_attribute_definitions
    self.custom_attribute_values = custom_attribute_values
    self.ac_role_id = ac_role_id

  def __repr__(self):
    return ("type: {type}, id: {id}, name: {name}, href: {href}, url: {url}, "
            "email: {email}, company: {company}, "
            "system_wide_role: {system_wide_role}, updated_at: {updated_at}, "
            "custom_attribute_definitions: {custom_attribute_definitions}, "
            "custom_attribute_values: {custom_attribute_values}, "
            "ac_role_id: {ac_role_id}").format(
        type=self.type, id=self.id, name=self.name, href=self.href,
        url=self.url, email=self.email, company=self.company,
        system_wide_role=self.system_wide_role, updated_at=self.updated_at,
        custom_attribute_definitions=self.custom_attribute_definitions,
        custom_attribute_values=self.custom_attribute_values,
        ac_role_id=self.ac_role_id)


class CustomAttributeEntity(Representation):
  """Class that represent model for Custom Attribute."""
  # pylint: disable=invalid-name
  # pylint: disable=redefined-builtin
  # pylint: disable=too-many-instance-attributes
  __hash__ = None
  entity = Entity()

  def __init__(self, title=None, id=None, href=None, type=None,
               definition_type=None, attribute_type=None, helptext=None,
               placeholder=None, mandatory=None, multi_choice_options=None,
               created_at=None, modified_by=None):
    super(CustomAttributeEntity, self).__init__()
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
    self.created_at = created_at  # to generate same CAs values
    self.modified_by = modified_by

  def __repr__(self):
    return ("type: {type}, title: {title}, id: {id}, href: {href}, "
            "definition_type: {definition_type}, "
            "attribute_type: {attribute_type}, helptext: {helptext}, "
            "placeholder: {placeholder}, mandatory: {mandatory}, "
            "multi_choice_options: {multi_choice_options}, "
            "created_at: {created_at}, modified_by: {modified_by}").format(
        type=self.type, title=self.title, id=self.id, href=self.href,
        definition_type=self.definition_type,
        attribute_type=self.attribute_type, helptext=self.helptext,
        placeholder=self.placeholder, mandatory=self.mandatory,
        multi_choice_options=self.multi_choice_options,
        created_at=self.created_at, modified_by=self.modified_by)

  def __eq__(self, other):
    return (isinstance(other, self.__class__) and self.type == other.type and
            self.title == other.title and
            self.definition_type == other.definition_type and
            self.attribute_type == other.attribute_type and
            self.mandatory == other.mandatory)


class ProgramEntity(Entity):
  """Class that represent model for Program."""
  # pylint: disable=too-many-instance-attributes
  __hash__ = None

  def __init__(self, slug=None, status=None, manager=None, contact=None,
               secondary_contact=None, updated_at=None, os_state=None,
               custom_attribute_definitions=None, custom_attribute_values=None,
               custom_attributes=None):
    super(ProgramEntity, self).__init__()
    self.slug = slug  # code
    self.status = status  # state
    self.manager = manager  # predefined and same as primary contact
    self.contact = contact  # primary contact
    self.secondary_contact = secondary_contact
    self.updated_at = updated_at  # last updated
    self.os_state = os_state  # review state
    self.custom_attribute_definitions = custom_attribute_definitions
    self.custom_attribute_values = custom_attribute_values
    self.custom_attributes = custom_attributes  # map of cas def and values

  def __repr__(self):
    return ("type: {type}, id: {id}, title: {title}, href: {href}, "
            "url: {url}, slug: {slug}, status: {status}, manager: {manager}, "
            "contact: {contact}, secondary_contact: {secondary_contact}, "
            "updated_at: {updated_at}, os_state: {os_state}, "
            "custom_attribute_definitions: {custom_attribute_definitions}, "
            "custom_attribute_values: {custom_attribute_values}, "
            "custom_attributes: {custom_attributes}").format(
        type=self.type, title=self.title, id=self.id, href=self.href,
        url=self.url, slug=self.slug, status=self.status, manager=self.manager,
        contact=self.contact, secondary_contact=self.secondary_contact,
        updated_at=self.updated_at, os_state=self.os_state,
        custom_attribute_definitions=self.custom_attribute_definitions,
        custom_attribute_values=self.custom_attribute_values,
        custom_attributes=self.custom_attributes)

  def __eq__(self, other):
    return (isinstance(other, self.__class__) and
            string_utils.is_one_dict_is_subset_another_dict(
                self.custom_attributes, other.custom_attributes) and
            self.manager == other.manager and
            self.os_state == other.os_state and self.slug == other.slug and
            self.status == other.status and self.title == other.title and
            self.type == other.type and self.updated_at == other.updated_at)

  def __lt__(self, other):
    return self.slug < other.slug


class ControlEntity(Entity):
  """Class that represent model for Control."""
  # pylint: disable=too-many-instance-attributes
  __hash__ = None

  def __init__(self, slug=None, status=None, owners=None, contact=None,
               secondary_contact=None, updated_at=None, os_state=None,
               custom_attribute_definitions=None, custom_attribute_values=None,
               custom_attributes=None, access_control_list=None):
    super(ControlEntity, self).__init__()
    self.slug = slug  # code
    self.status = status  # state
    self.owners = owners
    self.contact = contact  # primary contact
    self.secondary_contact = secondary_contact
    self.updated_at = updated_at  # last updated
    self.os_state = os_state  # review state
    self.custom_attribute_definitions = custom_attribute_definitions
    self.custom_attribute_values = custom_attribute_values
    self.custom_attributes = custom_attributes  # map of cas def and values
    self.access_control_list = access_control_list

  def __repr__(self):
    return ("type: {type}, id: {id}, title: {title}, href: {href}, "
            "url: {url}, slug: {slug}, status: {status}, owners: {owners}, "
            "contact: {contact}, secondary_contact: {secondary_contact}, "
            "updated_at: {updated_at}, os_state: {os_state}, "
            "custom_attribute_definitions: {custom_attribute_definitions}, "
            "custom_attribute_values: {custom_attribute_values}, "
            "custom_attributes: {custom_attributes}, "
            "access_control_list: {access_control_list}").format(
        type=self.type, title=self.title, id=self.id, href=self.href,
        url=self.url, slug=self.slug, status=self.status, owners=self.owners,
        contact=self.contact, secondary_contact=self.secondary_contact,
        updated_at=self.updated_at, os_state=self.os_state,
        custom_attribute_definitions=self.custom_attribute_definitions,
        custom_attribute_values=self.custom_attribute_values,
        custom_attributes=self.custom_attributes,
        access_control_list=self.access_control_list)

  def __eq__(self, other):
    return (isinstance(other, self.__class__) and
            string_utils.is_one_dict_is_subset_another_dict(
                self.custom_attributes, other.custom_attributes) and
            self.os_state == other.os_state and self.owners == other.owners and
            self.slug == other.slug and self.status == other.status and
            self.title == other.title and self.type == other.type and
            self.updated_at == other.updated_at)

  def __lt__(self, other):
    return self.slug < other.slug


class AuditEntity(Entity):
  """Class that represent model for Audit."""
  # pylint: disable=too-many-instance-attributes
  __hash__ = None

  def __init__(self, slug=None, status=None, program=None, contact=None,
               updated_at=None, custom_attribute_definitions=None,
               custom_attribute_values=None, custom_attributes=None):
    super(AuditEntity, self).__init__()
    self.slug = slug  # code
    self.status = status  # status
    self.program = program
    self.contact = contact  # internal audit lead
    self.updated_at = updated_at  # last updated
    self.custom_attribute_definitions = custom_attribute_definitions
    self.custom_attribute_values = custom_attribute_values
    self.custom_attributes = custom_attributes  # map of cas def and values

  def __repr__(self):
    return ("type: {type}, id: {id}, title: {title}, href: {href}, "
            "url: {url}, slug: {slug}, status: {status}, program: {program}, "
            "contact: {contact}, updated_at: {updated_at}, "
            "custom_attribute_definitions: {custom_attribute_definitions}, "
            "custom_attribute_values: {custom_attribute_values}, "
            "custom_attributes: {custom_attributes}").format(
        type=self.type, title=self.title, id=self.id, href=self.href,
        url=self.url, slug=self.slug, status=self.status, program=self.program,
        contact=self.contact, updated_at=self.updated_at,
        custom_attribute_definitions=self.custom_attribute_definitions,
        custom_attribute_values=self.custom_attribute_values,
        custom_attributes=self.custom_attributes)

  def __eq__(self, other):
    return (isinstance(other, self.__class__) and
            self.contact == other.contact and
            string_utils.is_one_dict_is_subset_another_dict(
                self.custom_attributes, other.custom_attributes) and
            self.slug == other.slug and self.status == other.status and
            self.title == other.title and self.type == other.type and
            self.updated_at == other.updated_at)

  def __lt__(self, other):
    return self.slug < other.slug


class AssessmentTemplateEntity(Entity):
  """Class that represent model for Assessment Template."""
  # pylint: disable=superfluous-parens
  # pylint: disable=too-many-instance-attributes
  __hash__ = None

  def __init__(self, slug=None, audit=None, default_people=None,
               verifiers=None, assessors=None, template_object_type=None,
               updated_at=None, custom_attribute_definitions=None,
               custom_attribute_values=None, custom_attributes=None):
    super(AssessmentTemplateEntity, self).__init__()
    self.slug = slug  # code
    self.audit = audit
    self.default_people = default_people  # {"verifiers": *, "assessors": *}
    self.verifiers = verifiers  # item of default_people
    self.assessors = assessors  # item of default_people
    self.template_object_type = template_object_type  # objs under asmt
    self.updated_at = updated_at  # last updated
    self.custom_attribute_definitions = custom_attribute_definitions
    self.custom_attribute_values = custom_attribute_values
    self.custom_attributes = custom_attributes  # map of cas def and values

  def __repr__(self):
    return ("type: {type}, id: {id}, title: {title}, href: {href}, "
            "url: {url}, slug: {slug}, audit: {audit}, "
            "verifiers: {verifiers}, assessors: {assessors}, "
            "template_object_type: {template_object_type}, "
            "updated_at: {updated_at}, "
            "custom_attribute_definitions: {custom_attribute_definitions}, "
            "custom_attribute_values: {custom_attribute_values}, "
            "custom_attributes: {custom_attributes}").format(
        type=self.type, title=self.title, id=self.id, href=self.href,
        url=self.url, slug=self.slug, audit=self.audit,
        verifiers=self.verifiers, assessors=self.assessors,
        template_object_type=self.template_object_type,
        updated_at=self.updated_at,
        custom_attribute_definitions=self.custom_attribute_definitions,
        custom_attribute_values=self.custom_attribute_values,
        custom_attributes=self.custom_attributes)

  def __eq__(self, other):
    return (isinstance(other, self.__class__) and
            string_utils.is_one_dict_is_subset_another_dict(
                self.custom_attributes, other.custom_attributes) and
            self.slug == other.slug and self.title == other.title and
            self.type == other.type and self.updated_at == other.updated_at)

  def __lt__(self, other):
    return self.slug < other.slug


class AssessmentEntity(Entity):
  """Class that represent model for Assessment."""
  # pylint: disable=too-many-instance-attributes
  # pylint: disable=redefined-builtin
  # pylint: disable=too-many-locals
  # pylint: disable=duplicate-code
  __hash__ = None

  def __init__(self, slug=None, status=None, audit=None, owners=None,
               recipients=None, assignees=None, assessor=None, creator=None,
               verifier=None, verified=None, updated_at=None,
               objects_under_assessment=None, os_state=None,
               custom_attribute_definitions=None, custom_attribute_values=None,
               custom_attributes=None):
    super(AssessmentEntity, self).__init__()
    self.slug = slug  # code
    self.status = status  # state
    self.owners = owners
    self.audit = audit
    self.recipients = recipients  # assessor, creator, verifier
    self.assignees = assignees  # {"Assessor": *, "Creator": *, "Verifier": *}
    self.assessor = assessor  # Assignee(s)
    self.creator = creator  # Creator(s)
    self.verifier = verifier  # Verifier(s)
    self.verified = verified
    self.updated_at = updated_at  # last updated
    self.objects_under_assessment = objects_under_assessment  # mapped objs
    self.os_state = os_state  # review state
    self.custom_attribute_definitions = custom_attribute_definitions
    self.custom_attribute_values = custom_attribute_values
    self.custom_attributes = custom_attributes  # map of cas def and values

  def __repr__(self):
    return ("type: {type}, id: {id}, title: {title}, href: {href}, "
            "url: {url}, slug: {slug}, status: {status}, owners: {owners}, "
            "audit: {audit}, recipients: {recipients}, "
            "assignees: {assignees}, assessor: {assessor}, "
            "creator: {creator}, verifier: {verifier}, verified: {verified}, "
            "updated_at: {updated_at}, "
            "objects_under_assessment: {objects_under_assessment}, "
            "os_state: {os_state}, "
            "custom_attribute_definitions: {custom_attribute_definitions}, "
            "custom_attribute_values: {custom_attribute_values}, "
            "custom_attributes: {custom_attributes}").format(
        type=self.type, title=self.title, id=self.id, href=self.href,
        url=self.url, slug=self.slug, status=self.status, owners=self.owners,
        audit=self.audit, recipients=self.recipients, assignees=self.assignees,
        assessor=self.assessor, creator=self.creator, verifier=self.verifier,
        verified=self.verified, updated_at=self.updated_at,
        objects_under_assessment=self.objects_under_assessment,
        os_state=self.os_state,
        custom_attribute_definitions=self.custom_attribute_definitions,
        custom_attribute_values=self.custom_attribute_values,
        custom_attributes=self.custom_attributes)

  def __eq__(self, other):
    return (isinstance(other, self.__class__) and
            self.assessor == other.assessor and
            self.creator == other.creator and
            string_utils.is_one_dict_is_subset_another_dict(
                self.custom_attributes, other.custom_attributes) and
            self.objects_under_assessment == other.objects_under_assessment and
            self.os_state == other.os_state and self.owners == other.owners and
            self.slug == other.slug and self.status == other.status and
            self.title == other.title and self.type == other.type and
            self.updated_at == other.updated_at and
            self.verifier == other.verifier and
            self.verified == other.verified)

  def __lt__(self, other):
    return self.slug < other.slug


class IssueEntity(Entity):
  """Class that represent model for Issue."""
  # pylint: disable=too-many-instance-attributes
  __hash__ = None

  def __init__(self, slug=None, status=None, audit=None, owners=None,
               contact=None, secondary_contact=None, updated_at=None,
               custom_attribute_definitions=None, os_state=None,
               custom_attribute_values=None, custom_attributes=None,
               access_control_list=None):
    super(IssueEntity, self).__init__()
    self.slug = slug  # code
    self.status = status  # state
    self.audit = audit
    self.owners = owners
    self.contact = contact  # primary contact
    self.secondary_contact = secondary_contact
    self.updated_at = updated_at  # last updated
    self.os_state = os_state  # review state
    self.custom_attribute_definitions = custom_attribute_definitions
    self.custom_attribute_values = custom_attribute_values
    self.custom_attributes = custom_attributes  # map of cas def and values
    self.access_control_list = access_control_list

  def __repr__(self):
    return ("type: {type}, id: {id}, title: {title}, href: {href}, "
            "url: {url}, slug: {slug}, status: {status}, audit: {audit}, "
            "owners: {owners}, contact: {contact}, "
            "secondary_contact: {secondary_contact}, "
            "updated_at: {updated_at}, os_state: {os_state}, "
            "custom_attribute_definitions: {custom_attribute_definitions}, "
            "custom_attribute_values: {custom_attribute_values}, "
            "custom_attributes: {custom_attributes}, "
            "access_control_list: {access_control_list}").format(
        type=self.type, title=self.title, id=self.id, href=self.href,
        url=self.url, slug=self.slug, status=self.status, audit=self.audit,
        owners=self.owners, contact=self.contact,
        secondary_contact=self.secondary_contact, updated_at=self.updated_at,
        os_state=self.os_state,
        custom_attribute_definitions=self.custom_attribute_definitions,
        custom_attribute_values=self.custom_attribute_values,
        custom_attributes=self.custom_attributes,
        access_control_list=self.access_control_list)

  def __eq__(self, other):
    return (isinstance(other, self.__class__) and self.type == other.type and
            self.title == other.title and self.slug == other.slug and
            self.status == other.status and self.contact == other.contact and
            self.owners == other.owners)

  def __lt__(self, other):
    return self.slug < other.slug
