# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""
  Assessment generator hooks

  We are applying assessment template properties and make
  new relationships and custom attributes
"""
import collections
import itertools

from sqlalchemy import orm

from ggrc import db
from ggrc import access_control
from ggrc.login import get_current_user_id
from ggrc.models import all_models
from ggrc.models.hooks import common
from ggrc.models.hooks import issue_tracker
from ggrc.services import signals
from ggrc.utils import referenced_objects


def _load_templates(template_ids):
  """Returns assessment templates for given IDs."""
  return {
      t.id: t for t in all_models.AssessmentTemplate.query.options(
          orm.undefer_group('AssessmentTemplate_complete'),
      ).filter(
          all_models.AssessmentTemplate.id.in_(template_ids)
      )
  }


def _load_audits(audit_ids):
  """Returns audits for given IDs."""
  return {
      a.id: a for a in all_models.Audit.query.options(
          orm.undefer_group('Audit_complete'),
      ).filter(
          all_models.Audit.id.in_(audit_ids)
      )
  }


def _handle_assessment(assessment, src, templates, audits):
  """Handles auto calculated properties for Assessment model."""
  snapshot_dict = src.get('object') or {}
  common.map_objects(assessment, snapshot_dict)
  common.map_objects(assessment, src.get('audit'))
  snapshot = referenced_objects.get("Snapshot", snapshot_dict.get('id'))

  if not src.get('_generated') and not snapshot:
    return

  template = templates.get(src.get('template', {}).get('id'))
  audit = audits[src['audit']['id']]
  relate_assignees(assessment, snapshot, template, audit)
  relate_ca(assessment, template)
  assessment.title = u'{} assessment for {}'.format(
      snapshot.revision.content['title'],
      audit.title,
  )

  if not template:
    # Assessment test plan should inherit test plan of snapshot
    assessment.test_plan = snapshot.revision.content.get("test_plan")
    return

  assessment.test_plan = template.procedure_description
  if template.test_plan_procedure:
    copy_snapshot_plan(assessment, snapshot)
  if template.template_object_type:
    assessment.assessment_type = template.template_object_type


def init_hook():
  """Initializes hooks."""

  # pylint: disable=unused-variable
  @signals.Restful.collection_posted.connect_via(all_models.Assessment)
  def handle_assessment_post(sender, objects=None, sources=None, service=None):
    """Applies custom attribute definitions and maps people roles.

    Applicable when generating Assessment with template.

    Args:
      sender: A class of Resource handling the POST request.
      objects: A list of model instances created from the POSTed JSON.
      sources: A list of original POSTed JSON dictionaries.
    """
    del sender, service  # Unused

    db.session.flush()
    audit_ids = set()
    template_ids = set()

    for src in sources:
      audit_ids.add(src.get('audit', {}).get('id'))
      template_ids.add(src.get('template', {}).get('id'))

    template_cache = _load_templates(template_ids)
    audit_cache = _load_audits(audit_ids)

    for assessment, src in itertools.izip(objects, sources):
      _handle_assessment(assessment, src, template_cache, audit_cache)

    # Flush roles objects for generated assessments.
    db.session.flush()

    for assessment, src in itertools.izip(objects, sources):
      # Handling IssueTracker info here rather than in hooks/issue_tracker
      # would avoid querying same data (such as snapshots, audits and
      # templates) twice.
      issue_tracker.handle_assessment_create(
          assessment, src, template_cache, audit_cache)

  # pylint: disable=unused-variable
  @signals.Restful.model_put.connect_via(all_models.Assessment)
  def handle_assessment_put(sender, obj=None, src=None, service=None):
    """Handles assessment update event."""
    del sender, src, service  # Unused
    common.ensure_field_not_changed(obj, 'audit')


def generate_assignee_relations(assessment,
                                assignee_ids,
                                verifier_ids,
                                creator_ids):
  """Generates db relations to assessment for sent role ids.

    Args:
        assessment (model instance): Assessment model
        assignee_ids (list): list of person ids
        verifier_ids (list): list of person ids
        creator_ids (list): list of person ids
  """
  people = set(assignee_ids + verifier_ids + creator_ids)
  person_dict = {i.id: i for i in all_models.Person.query.filter(
      all_models.Person.id.in_(people)
  )}

  person_roles = []
  for person_id in people:
    person = person_dict.get(person_id)
    if person is None:
      continue
    if person_id in assignee_ids:
      person_roles.append((person, "Assignees"))
    if person_id in verifier_ids:
      person_roles.append((person, "Verifiers"))
    if person_id in creator_ids:
      person_roles.append((person, "Creators"))

  ac_roles = {
      acr_name: acr_id
      for acr_id, acr_name in access_control.role.get_custom_roles_for(
          assessment.type).iteritems()
  }

  db.session.add_all(
      all_models.AccessControlList(
          ac_role_id=ac_roles[role],
          person=person,
          object=assessment
      ) for person, role in person_roles
  )


def get_people_ids_based_on_role(assignee_role,
                                 default_role,
                                 template_settings,
                                 acl_dict):
  """Get people_ids base on role and template settings."""
  if assignee_role not in template_settings or \
     not template_settings.get(assignee_role):
    return []
  template_role = template_settings[assignee_role]
  if isinstance(template_role, list):
    return template_role
  return acl_dict.get(template_role, acl_dict.get(default_role)) or []


def generate_role_object_dict(snapshot, audit):
  """Generate roles dict for sent snapshot and audit.

  returns dict of roles with key as role name and list of people ids as values.
  """

  acr_dict = access_control.role.get_custom_roles_for(snapshot.child_type)
  audit_acr = access_control.role.get_custom_roles_for("Audit")
  auditors_role = next(id_ for id_, val in audit_acr.iteritems()
                       if val == "Auditors")
  leads_role = next(id_ for id_, val in audit_acr.iteritems()
                    if val == "Audit Captains")

  acl_dict = collections.defaultdict(list)
  # populated content should have access_control_list
  for acl in snapshot.revision.content["access_control_list"]:
    acl_dict[acr_dict[acl["ac_role_id"]]].append(acl["person_id"])
  # populate Access Control List by generated role from the related Audit
  acl_dict["Audit Lead"].extend([acl.person_id
                                for acl in audit.access_control_list
                                if acl.ac_role_id == leads_role])
  auditors = [
      acl.person_id for acl in audit.access_control_list
      if acl.ac_role_id == auditors_role
  ]
  acl_dict["Auditors"].extend(auditors or acl_dict["Audit Lead"])
  return acl_dict


def relate_assignees(assessment, snapshot, template, audit):
  """Generates assignee list and relates them to Assessment objects

    Args:
        assessment (model instance): Assessment model
        snapshot (model instance): Snapshot,
        template (model instance): AssessmentTemplate model nullable,
        audit (model instance): Audit
  """
  if template:
    template_settings = template.default_people
  else:
    template_settings = {"assignees": "Principal Assignees",
                         "verifiers": "Auditors"}
  acl_dict = generate_role_object_dict(snapshot, audit)
  assignee_ids = get_people_ids_based_on_role("assignees",
                                              "Audit Lead",  # default assignee
                                              template_settings,
                                              acl_dict)
  verifier_ids = get_people_ids_based_on_role("verifiers",
                                              "Auditors",  # default verifier
                                              template_settings,
                                              acl_dict)
  generate_assignee_relations(assessment,
                              assignee_ids,
                              verifier_ids,
                              [get_current_user_id()])


def relate_ca(assessment, template):
  """Generates custom attribute list and relates it to Assessment objects

    Args:
        assessment (model instance): Assessment model
        template: Assessment Temaplte instance (may be None)
  """
  if not template:
    return

  ca_definitions = all_models.CustomAttributeDefinition.query.options(
      orm.undefer_group('CustomAttributeDefinition_complete'),
  ).filter_by(
      definition_id=template.id,
      definition_type="assessment_template",
  ).order_by(
      all_models.CustomAttributeDefinition.id
  )
  for definition in ca_definitions:
    cad = all_models.CustomAttributeDefinition(
        title=definition.title,
        definition=assessment,
        attribute_type=definition.attribute_type,
        multi_choice_options=definition.multi_choice_options,
        multi_choice_mandatory=definition.multi_choice_mandatory,
        mandatory=definition.mandatory,
        helptext=definition.helptext,
        placeholder=definition.placeholder,
    )
    db.session.add(cad)


def copy_snapshot_plan(assessment, snapshot):
  """Copy test plan of Snapshot into Assessment"""
  if assessment.test_plan and snapshot.revision.content["test_plan"]:
    assessment.test_plan += "<br>"
    assessment.test_plan += snapshot.revision.content["test_plan"]
  elif snapshot.revision.content["test_plan"]:
    assessment.test_plan = snapshot.revision.content["test_plan"]
