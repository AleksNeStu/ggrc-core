# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Factories and methods for operating with objects based on entities models.
"""
# pylint: disable=too-many-arguments
# pylint: disable=invalid-name
# pylint: disable=redefined-builtin

import copy
import random

from lib.constants import (element, objects, roles, value_aliases,
                           url as const_url)
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
  entity_cls = Entity
  obj_name = None

  obj_person = objects.get_singular(objects.PEOPLE, title=True)
  obj_program = objects.get_singular(objects.PROGRAMS, title=True)
  obj_control = objects.get_singular(objects.CONTROLS, title=True)
  obj_objective = objects.get_singular(objects.OBJECTIVES, title=True)
  obj_audit = objects.get_singular(objects.AUDITS, title=True)
  obj_asmt_tmpl = objects.get_singular(
      objects.ASSESSMENT_TEMPLATES, title=True)
  obj_asmt = objects.get_singular(objects.ASSESSMENTS, title=True)
  obj_ca = objects.get_singular(objects.CUSTOM_ATTRIBUTES)
  obj_comment = objects.get_singular(objects.COMMENTS, title=True)
  obj_snapshot = objects.get_singular(objects.SNAPSHOTS, title=True)

  def __init__(self, is_rest=True):
    self.is_rest = is_rest  # if not is_rest then is_ui
    self.obj = self.entity_cls()
    if self.obj_name:
      self.obj_type = objects.get_singular(self.obj_name, title=True)
      self.obj.type = self.obj_type

  @classmethod
  def generate_string(cls, first_part):
    """Generate string in according object type and random data.
    """
    special_chars = string_utils.SPECIAL
    return "{first_part}_{uuid}_{rand_str}".format(
        first_part=first_part, uuid=random_uuid(),
        rand_str=random_string(size=len(special_chars), chars=special_chars))

  @classmethod
  def generate_slug(cls):
    """Generate slug according str part and random data."""
    return "code-{slug}".format(slug=random_uuid())

  @classmethod
  def generate_email(cls, domain=roles.DEFAULT_EMAIL_DOMAIN):
    """Generate email according to domain."""
    return "{mail_name}@{domain}".format(
        mail_name=random_uuid(), domain=domain)











  def set_obj_base_random_attrs(self):
    """Create Issue entity with randomly and predictably filled fields (admin,
    primary_contacts - not REST).
    """
    self.obj.slug = self.generate_slug()
    self.obj.title = self.generate_string(self.obj_type)





class ObjectPersonsFactory(EntitiesFactory):
  """Factory class for Persons entities."""

  obj_attrs_names = Entity.get_attrs_names_for_entities(PersonEntity)

  @property
  def default(self):
    """Create default system Person object."""
    return self.create(
        name=roles.DEFAULT_USER, id=1, href=const_url.DEFAULT_USER_HREF,
        email=roles.DEFAULT_USER_EMAIL,
        system_wide_role=roles.SystemWideRoles.SUPERUSER)

  @classmethod
  def create(cls, type=None, id=None, name=None, href=None, url=None,
             email=None, company=None, system_wide_role=None, updated_at=None,
             custom_attribute_definitions=None, custom_attribute_values=None,
             custom_attributes=None, created_at=None):
    """Create Person object.
    Random values will be used for name.
    Predictable values will be used for type, email and system_wide_role.
    """
    person_entity = cls._create_random_person()
    person_entity = Entity.update_obj_attrs_values_by_entered_data(
        obj=person_entity, is_allow_none_values=False, type=type,
        id=id, name=name, href=href, url=url, email=email, company=company,
        system_wide_role=system_wide_role, updated_at=updated_at,
        custom_attribute_definitions=custom_attribute_definitions,
        custom_attribute_values=custom_attribute_values,
        custom_attributes=custom_attributes, created_at=created_at)
    return person_entity

  @classmethod
  def get_acl_member(cls, role_id, person):
    """Return ACL member as dict."""
    person_value = ({"id": person.id} if isinstance(person, PersonEntity) else
                    person)
    return {"ac_role_id": role_id, "person": person_value}

  @classmethod
  def _create_random_person(cls):
    """Create Person entity with randomly filled fields."""
    random_person = PersonEntity()
    random_person.type = cls.obj_person
    random_person.name = cls.generate_string(cls.obj_person)
    random_person.email = cls.generate_email()
    random_person.system_wide_role = roles.SystemWideRoles.SUPERUSER
    return random_person


class CommentsFactory(EntitiesFactory):
  """Factory class for Comments entities."""
  # pylint: disable=too-many-locals

  obj_attrs_names = Entity.get_attrs_names_for_entities(CommentEntity)

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
    comment_entity = Entity.update_obj_attrs_values_by_entered_data(
        obj=comment_entity, is_allow_none_values=False, type=type,
        id=id, href=href, modified_by=modified_by, created_at=created_at,
        description=description)
    return comment_entity

  @classmethod
  def _create_random_comment(cls):
    """Create Comment entity with randomly and predictably filled fields."""
    random_comment = CommentEntity()
    random_comment.type = cls.obj_comment
    random_comment.modified_by = ObjectPersonsFactory().default.__dict__
    random_comment.description = cls.generate_string(cls.obj_comment)
    return random_comment


class CustomAttributeDefinitionsFactory(EntitiesFactory):
  """Factory class for entities."""

  obj_attrs_names = Entity.get_attrs_names_for_entities(
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
            ca_value = ca["created_at"][:10]
          if ca_attr_type == AdminWidgetCustomAttributes.CHECKBOX:
            ca_value = random.choice((True, False))
          if ca_attr_type == AdminWidgetCustomAttributes.DROPDOWN:
            ca_value = random.choice(ca["multi_choice_options"].split(","))
          if ca_attr_type == AdminWidgetCustomAttributes.PERSON:
            ca_value = ":".join([ca["modified_by"]["type"],
                                 ca["modified_by"]["id"]])
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
             updated_at=None, modified_by=None, created_at=None):
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
        modified_by=modified_by, created_at=created_at)
    return ca_entity

  @classmethod
  def _create_random_ca(cls):
    """Create CustomAttribute entity with randomly filled fields."""
    random_ca = CustomAttributeEntity()
    random_ca.type = cls.obj_ca
    random_ca.attribute_type = random.choice(
        AdminWidgetCustomAttributes.ALL_CA_TYPES)
    random_ca.title = cls.generate_string(random_ca.attribute_type)
    if random_ca.attribute_type == AdminWidgetCustomAttributes.DROPDOWN:
      random_ca.multi_choice_options = random_list_strings()
    random_ca.definition_type = objects.get_singular(
        random.choice(objects.ALL_CA_OBJS))
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
    return Entity.update_obj_attrs_values_by_entered_data(
        obj=obj, **arguments)

  @classmethod
  def create_dashboard_ca(cls, definition_type):
    """Create and return CA entity with valid filled fields for
    creating N'Dashboard'.
    """
    dashboard_ca = CustomAttributeEntity()
    dashboard_ca.type = cls.obj_ca
    dashboard_ca.attribute_type = AdminWidgetCustomAttributes.TEXT
    dashboard_ca.title = cls.generate_string(value_aliases.DASHBOARD)
    dashboard_ca.mandatory = False
    dashboard_ca.definition_type = definition_type
    return dashboard_ca


class ProgramsFactory(EntitiesFactory):
  """Factory class for Programs entities."""
  # pylint: disable=too-many-locals

  obj_attrs_names = Entity.get_attrs_names_for_entities(ProgramEntity)
  default_person = ObjectPersonsFactory().default

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
             custom_attributes=None, created_at=None, modified_by=None):
    """Create Program object.
    Random values will be used for title and slug.
    Predictable values will be used for type, status, manager, contact.
    """
    program_entity = cls._create_random_program()
    program_entity = Entity.update_obj_attrs_values_by_entered_data(
        obj=program_entity, is_allow_none_values=False, type=type,
        id=id, title=title, href=href, url=url, slug=slug, status=status,
        manager=manager, contact=contact, secondary_contact=secondary_contact,
        updated_at=updated_at, os_state=os_state,
        custom_attribute_definitions=custom_attribute_definitions,
        custom_attribute_values=custom_attribute_values,
        custom_attributes=custom_attributes, created_at=created_at,
        modified_by=modified_by)
    return program_entity

  @classmethod
  def _create_random_program(cls):
    """Create Program entity with randomly and predictably filled fields."""
    random_program = ProgramEntity()
    random_program.type = cls.obj_program
    random_program.title = cls.generate_string(cls.obj_program)
    random_program.slug = cls.generate_slug()
    random_program.status = element.ObjectStates.DRAFT
    random_program.manager = cls.default_person.__dict__
    random_program.contact = cls.default_person.__dict__
    random_program.os_state = element.ReviewStates.UNREVIEWED
    return random_program


class ControlsFactory(EntitiesFactory):
  """Factory class for Controls entities."""
  # pylint: disable=too-many-locals

  obj_attrs_names = Entity.get_attrs_names_for_entities(ControlEntity)
  default_person = ObjectPersonsFactory().default

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
             custom_attributes=None, access_control_list=None, created_at=None,
             modified_by=None):
    """Create Control object.
    Random values will be used for title and slug.
    Predictable values will be used for type, status, owners and contact.
    """
    control_entity = cls._create_random_control()
    control_entity = Entity.update_obj_attrs_values_by_entered_data(
        obj=control_entity, is_allow_none_values=False, type=type,
        id=id, title=title, href=href, url=url, slug=slug, status=status,
        owners=owners, contact=contact, secondary_contact=secondary_contact,
        updated_at=updated_at, os_state=os_state,
        custom_attribute_definitions=custom_attribute_definitions,
        custom_attribute_values=custom_attribute_values,
        custom_attributes=custom_attributes,
        access_control_list=access_control_list, created_at=created_at,
        modified_by=modified_by)
    return control_entity

  @classmethod
  def _create_random_control(cls):
    """Create Control entity with randomly and predictably filled fields."""
    random_control = ControlEntity()
    random_control.type = cls.obj_control
    random_control.title = cls.generate_string(cls.obj_control)
    random_control.slug = cls.generate_slug()
    random_control.status = element.ObjectStates.DRAFT
    random_control.contact = cls.default_person.__dict__
    random_control.owners = [cls.default_person.__dict__]
    random_control.access_control_list = [
        ObjectPersonsFactory().get_acl_member(
            roles.CONTROL_ADMIN_ID, random_control.owners[0]),
        ObjectPersonsFactory().get_acl_member(
            roles.CONTROL_PRIMARY_CONTACTS_ID, random_control.contact)]
    random_control.os_state = element.ReviewStates.UNREVIEWED
    return random_control


class ObjectivesFactory(EntitiesFactory):
  """Factory class for Objectives entities."""
  # pylint: disable=too-many-locals

  obj_attrs_names = Entity.get_attrs_names_for_entities(ObjectiveEntity)
  default_person = ObjectPersonsFactory().default

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
             custom_attributes=None, created_at=None, modified_by=None):
    """Create Objective object.
    Random values will be used for title and slug.
    Predictable values will be used for type, status, owners.
    """
    objective_entity = cls._create_random_objective()
    objective_entity = Entity.update_obj_attrs_values_by_entered_data(
        obj=objective_entity, is_allow_none_values=False, type=type,
        id=id, title=title, href=href, url=url, slug=slug, status=status,
        owners=owners, contact=contact, secondary_contact=secondary_contact,
        updated_at=updated_at, os_state=os_state,
        custom_attribute_definitions=custom_attribute_definitions,
        custom_attribute_values=custom_attribute_values,
        custom_attributes=custom_attributes, created_at=created_at,
        modified_by=modified_by)
    return objective_entity

  @classmethod
  def _create_random_objective(cls):
    """Create Objective entity with randomly and predictably filled fields."""
    random_objective = ObjectiveEntity()
    random_objective.type = cls.obj_objective
    random_objective.title = cls.generate_string(cls.obj_objective)
    random_objective.slug = cls.generate_slug()
    random_objective.status = element.ObjectStates.DRAFT
    random_objective.owners = [cls.default_person.__dict__]
    random_objective.os_state = element.ReviewStates.UNREVIEWED
    return random_objective


class AuditsFactory(EntitiesFactory):
  """Factory class for Audit entity."""

  obj_attrs_names = Entity.get_attrs_names_for_entities(AuditEntity)
  default_person = ObjectPersonsFactory().default

  @classmethod
  def clone(cls, audit, count_to_clone=1):
    """Clone Audit object.
    Predictable values will be used for type, title.
    """
    # pylint: disable=anomalous-backslash-in-string
    return [Entity.update_obj_attrs_values_by_entered_data(
        obj=copy.deepcopy(audit),
        title=audit.title + " - copy " + str(num), slug=None, created_at=None,
        updated_at=None, href=None, url=None, id=None)
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
             custom_attribute_values=None, custom_attributes=None,
             created_at=None, modified_by=None):
    """Create Audit object.
    Random values will be used for title and slug.
    Predictable values will be used for type, status, contact.
    """
    # pylint: disable=too-many-locals
    audit_entity = cls._create_random_audit()
    audit_entity = Entity.update_obj_attrs_values_by_entered_data(
        obj=audit_entity, is_allow_none_values=False, type=type,
        id=id, title=title, href=href, url=url, slug=slug, status=status,
        program=program, contact=contact, updated_at=updated_at,
        custom_attribute_definitions=custom_attribute_definitions,
        custom_attribute_values=custom_attribute_values,
        custom_attributes=custom_attributes, created_at=created_at,
        modified_by=modified_by)
    return audit_entity

  @classmethod
  def _create_random_audit(cls):
    """Create Audit entity with randomly and predictably filled fields."""
    random_audit = AuditEntity()
    random_audit.type = cls.obj_audit
    random_audit.title = cls.generate_string(cls.obj_audit)
    random_audit.slug = cls.generate_slug()
    random_audit.status = element.AuditStates().PLANNED
    random_audit.contact = cls.default_person.__dict__
    return random_audit


class AssessmentTemplatesFactory(EntitiesFactory):
  """Factory class for Assessment Templates entities."""

  obj_attrs_names = Entity.get_attrs_names_for_entities(
      AssessmentTemplateEntity)

  @classmethod
  def clone(cls, asmt_tmpl, count_to_clone=1):
    """Clone Assessment Template object.
    Predictable values will be used for type, title.
    """
    # pylint: disable=anomalous-backslash-in-string
    return [Entity.update_obj_attrs_values_by_entered_data(
        obj=copy.deepcopy(asmt_tmpl), slug=None, updated_at=None,
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
             custom_attributes=None, created_at=None, modified_by=None,
             status=None):
    """Create Assessment Template object.
    Random values will be used for title and slug.
    Predictable values will be used for type, template_object_type and
    default_people {"verifiers": *, "assignees": *}.
    """
    # pylint: disable=too-many-locals
    asmt_tmpl_entity = cls._create_random_asmt_tmpl()
    asmt_tmpl_entity = Entity.update_obj_attrs_values_by_entered_data(
        obj=asmt_tmpl_entity, is_allow_none_values=False, type=type,
        id=id, title=title, href=href, url=url, slug=slug, audit=audit,
        default_people=default_people,
        template_object_type=template_object_type, updated_at=updated_at,
        custom_attribute_definitions=custom_attribute_definitions,
        custom_attribute_values=custom_attribute_values,
        custom_attributes=custom_attributes, created_at=created_at,
        modified_by=modified_by, status=status)
    return asmt_tmpl_entity

  @classmethod
  def _create_random_asmt_tmpl(cls):
    """Create Assessment Template entity with randomly and predictably
    filled fields.
    """
    random_asmt_tmpl = AssessmentTemplateEntity()
    random_asmt_tmpl.type = cls.obj_asmt_tmpl
    random_asmt_tmpl.title = cls.generate_string(cls.obj_asmt_tmpl)
    random_asmt_tmpl.assignees = roles.AUDIT_LEAD
    random_asmt_tmpl.slug = cls.generate_slug()
    random_asmt_tmpl.template_object_type = cls.obj_control.title()
    random_asmt_tmpl.status = element.ObjectStates.DRAFT
    random_asmt_tmpl.default_people = {"verifiers": roles.AUDITORS,
                                       "assignees": roles.AUDIT_LEAD}
    return random_asmt_tmpl


class AssessmentsFactory(EntitiesFactory):
  """Factory class for Assessments entities."""

  obj_attrs_names = Entity.get_attrs_names_for_entities(AssessmentEntity)
  default_person = ObjectPersonsFactory().default

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
    return [Entity.update_obj_attrs_values_by_entered_data(
        obj=asmt_obj, slug=None) for asmt_obj in asmts_objs]

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
             slug=None, status=None, owners=None, audit=None, recipients=None,
             assignees=None, verified=None, verifier=None, creator=None,
             assignee=None, updated_at=None, objects_under_assessment=None,
             custom_attribute_definitions=None, custom_attribute_values=None,
             custom_attributes=None, created_at=None, modified_by=None):
    """Create Assessment object.
    Random values will be used for title and slug.
    Predictable values will be used for type, status, recipients,
    verified, owners.
    """
    # pylint: disable=too-many-locals
    asmt_entity = cls._create_random_asmt()
    asmt_entity = Entity.update_obj_attrs_values_by_entered_data(
        obj=asmt_entity, is_allow_none_values=False, type=type, id=id,
        title=title, href=href, url=url, slug=slug, status=status,
        owners=owners, audit=audit, recipients=recipients, assignees=assignees,
        verified=verified, verifier=verifier, creator=creator,
        assignee=assignee, updated_at=updated_at,
        objects_under_assessment=objects_under_assessment,
        custom_attribute_definitions=custom_attribute_definitions,
        custom_attribute_values=custom_attribute_values,
        custom_attributes=custom_attributes, created_at=created_at,
        modified_by=modified_by)
    if verifier:
      asmt_entity.access_control_list.append(
          ObjectPersonsFactory.get_acl_member(roles.ASMT_VERIFIER_ID,
                                              cls.default_person))
    return asmt_entity

  @classmethod
  def _create_random_asmt(cls):
    """Create Assessment entity with randomly and predictably filled fields."""
    random_asmt = AssessmentEntity()
    random_asmt.type = cls.obj_asmt
    random_asmt.title = cls.generate_string(cls.obj_asmt)
    random_asmt.slug = cls.generate_slug()
    random_asmt.status = element.AssessmentStates.NOT_STARTED
    random_asmt.recipients = ",".join(
        (roles.ASSIGNEE, roles.ASMT_CREATOR, roles.VERIFIER))
    random_asmt.access_control_list = (
        [ObjectPersonsFactory.get_acl_member(roles.ASMT_CREATOR_ID,
                                             cls.default_person),
         ObjectPersonsFactory.get_acl_member(roles.ASMT_ASSIGNEE_ID,
                                             cls.default_person)]
    )
    random_asmt.verified = False
    random_asmt.assignee = [cls.default_person.name]
    random_asmt.creator = [cls.default_person.name]
    random_asmt.assignees = {
        "Assignee": [cls.default_person.__dict__],
        "Creator": [cls.default_person.__dict__]}
    return random_asmt


class IssuesFactory(EntitiesFactory):
  """Factory class for Issues entities."""
  entity_cls = IssueEntity
  obj_name = objects.ISSUES

  def create_empty(self):
    """Create blank Issue object."""
    self.obj.custom_attributes = {None: None}
    self.obj.access_control_list = []
    return self.obj

  def create(self, is_random=True, **attrs):
    """Create Issue object.
    Random values will be used for title, slug.
    Predictable values will be used for type, status, os_state, admin,
    primary_contacts.
    """
    # pylint: disable=too-many-locals
    if is_random:
      self.set_obj_random_attrs()
    return self.obj.update(is_allow_none_values=False, **attrs)

  def set_obj_random_attrs(self):
    """Create Issue entity with randomly and predictably filled fields (admin,
    primary_contacts - not REST).
    """
    self.set_obj_base_random_attrs()
    self.obj.status = element.IssueStates.DRAFT
    self.obj.os_state = element.ReviewStates.UNREVIEWED
    self.obj.admin = [ObjectPersonsFactory().default]
    self.obj.primary_contacts = [ObjectPersonsFactory().default]
    if self.is_rest:
      self.obj.access_control_list = help_utils.convert_list_els_to_list(
          [ObjectPersonsFactory().get_acl_member(
              role_id=roles.ISSUE_ADMIN_ID, person=admin)
              for admin in self.obj.admin] +
          [ObjectPersonsFactory().get_acl_member(
              role_id=roles.ISSUE_PRIMARY_CONTACTS_ID, person=primary_contact)
              for primary_contact in self.obj.primary_contacts])
    self.obj.admin = [admin.email for admin in self.obj.admin]
    self.obj.primary_contacts = [
        primary_contact.email for primary_contact in self.obj.primary_contacts]
