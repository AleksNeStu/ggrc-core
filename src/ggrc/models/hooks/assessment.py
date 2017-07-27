# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""
  Assessment generator hooks

  We are applying assessment template properties and make
  new relationships and custom attributes
"""
import logging
from itertools import izip
from collections import defaultdict


from sqlalchemy import orm

from ggrc import db
from ggrc.login import get_current_user_id
from ggrc.models import all_models
from ggrc.models import Assessment
from ggrc.models import Snapshot
from ggrc.models.hooks import common
from ggrc.services import signals
from ggrc.access_control import role

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


def init_hook():
  """ Initialize hooks"""
  # pylint: disable=unused-variable
  @signals.Restful.collection_posted.connect_via(Assessment)
  def handle_assessment_post(sender, objects=None, sources=None):
    # pylint: disable=unused-argument
    """Apply custom attribute definitions and map people roles
    when generating Assessmet with template"""
    db.session.flush()

    audit_ids = []
    template_ids = []
    snapshot_ids = []

    for src in sources:
      snapshot_ids.append(src.get('object', {}).get('id'))
      audit_ids.append(src.get('audit', {}).get('id'))
      template_ids.append(src.get('template', {}).get('id'))

    snapshot_cache = {
        s.id: s for s in Snapshot.query.options(
            orm.undefer_group('Snapshot_complete'),
            orm.Load(Snapshot).joinedload(
                "revision"
            ).undefer_group(
                'Revision_complete'
            )
        ).filter(
            Snapshot.id.in_(snapshot_ids)
        )
    }
    template_cache = {
        t.id: t for t in all_models.AssessmentTemplate.query.options(
            orm.undefer_group('AssessmentTemplate_complete'),
        ).filter(
            all_models.AssessmentTemplate.id.in_(template_ids)
        )
    }
    audit_cache = {
        a.id: a for a in all_models.Audit.query.options(
            orm.undefer_group('Audit_complete'),
        ).filter(
            all_models.Audit.id.in_(audit_ids)
        )
    }

    for assessment, src in izip(objects, sources):
      snapshot_dict = src.get("object") or {}
      common.map_objects(assessment, snapshot_dict)
      common.map_objects(assessment, src.get("audit"))
      snapshot = snapshot_cache.get(snapshot_dict.get('id'))
      if not src.get("_generated") and not snapshot:
        continue
      template = template_cache.get(src.get("template", {}).get("id"))
      audit = audit_cache[src["audit"]["id"]]
      relate_assignees(assessment, snapshot, template, audit)
      relate_ca(assessment, template)
      assessment.title = u'{} assessment for {}'.format(
          snapshot.revision.content['title'],
          audit.title,
      )
      if not template:
        continue
      if template.test_plan_procedure:
        assessment.test_plan = snapshot.revision.content['test_plan']
      else:
        assessment.test_plan = template.procedure_description
      if template.template_object_type:
        assessment.assessment_type = template.template_object_type

  @signals.Restful.model_put.connect_via(Assessment)
  def handle_assessment_put(sender, obj=None, src=None, service=None):
    # pylint: disable=unused-argument
    common.ensure_field_not_changed(obj, "audit")


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
  for person_id in people:
    person = person_dict.get(person_id)
    if person is None:
      continue
    roles = []
    if person_id in assignee_ids:
      roles.append("Assessor")
    if person_id in verifier_ids:
      roles.append("Verifier")
    if person_id in creator_ids:
      roles.append("Creator")
    rel = all_models.Relationship(
        source=person,
        destination=assessment,
        context=assessment.context,
    )
    rel.attrs = {"AssigneeType": ",".join(roles)}
    db.session.add(rel)


def get_people_ids_based_on_role(assignee_role,
                                 default_role,
                                 template_settings,
                                 acl_dict):
  """Get people_ids base on role and template settings."""
  if assignee_role not in template_settings:
    return []
  template_role = template_settings[assignee_role]
  if isinstance(template_role, list):
    return template_role
  return acl_dict.get(template_role, acl_dict.get(default_role)) or []


def generate_role_object_dict(snapshot, audit):
  """Generate roles dict for sent snapshot and audit.

  returns dict of roles with key as role name and list of people ids as values.
  """

  acr_dict = role.get_custom_roles_for(snapshot.child_type)
  acl_dict = defaultdict(list)
  # populated content should have access_control_list
  for acl in snapshot.revision.content["access_control_list"]:
    acl_dict[acr_dict[acl["ac_role_id"]]].append(acl["person_id"])
  # populate Access Control List by generated role from the related Audit
  acl_dict["Audit Lead"].append(audit.contact_id)
  acl_dict["Auditors"].extend([user_role.person_id
                               for user_role in audit.context.user_roles
                               if user_role.role.name == u"Auditor"])
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
    template_settings = {"assessors": "Principal Assignees",
                         "verifiers": "Auditors"}
  acl_dict = generate_role_object_dict(snapshot, audit)
  assignee_ids = get_people_ids_based_on_role("assessors",
                                              "Audit Lead",  # default assessor
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
  assessment.custom_attribute_definitions = [
      all_models.CustomAttributeDefinition(
          title=definition.title,
          definition=assessment,
          attribute_type=definition.attribute_type,
          multi_choice_options=definition.multi_choice_options,
          multi_choice_mandatory=definition.multi_choice_mandatory,
          mandatory=definition.mandatory,
          helptext=definition.helptext,
          placeholder=definition.placeholder,
      ) for definition in ca_definitions
  ] + assessment.custom_attribute_definitions
