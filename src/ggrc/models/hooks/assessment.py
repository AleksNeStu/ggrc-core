# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""
  Assessment generator hooks

  We are applying assessment template properties and make
  new relationships and custom attributes
"""

from itertools import izip

from ggrc import db
from ggrc.login import get_current_user_id
from ggrc.models import all_models
from ggrc.models import Assessment
from ggrc.models import Person
from ggrc.models import Relationship
from ggrc.models import Snapshot
from ggrc.services.common import Resource


def init_hook():
  """ Initialize hooks"""
  # pylint: disable=unused-variable
  @Resource.collection_posted.connect_via(Assessment)
  def handle_assessment_post(sender, objects=None, sources=None):
    # pylint: disable=unused-argument
    """Apply custom attribute definitions and map people roles
    when generating Assessmet with template"""
    db.session.flush()

    snapshot_ids = [src.get('object', {}).get('id') for src in sources]
    snapshots = Snapshot.eager_query().filter(Snapshot.id.in_(snapshot_ids))
    snapshots = {snapshot.id: snapshot for snapshot in snapshots}

    for obj, src in izip(objects, sources):
      src_obj = src.get("object")
      audit = src.get("audit")
      program = src.get("program")
      map_assessment(obj, src_obj)
      map_assessment(obj, audit)
      # The program may also be set as the src_obj. If so then it should not be
      # mapped again.
      if (src_obj and program and
          (src_obj["id"] != program["id"] or
           src_obj["type"] != program["type"])):
        map_assessment(obj, program)

      if not src.get("_generated"):
        continue

      related = {
          "template": get_by_id(src.get("template")),
          "obj": get_by_id(src.get("object")),
          "audit": get_by_id(src.get("audit")),
      }
      relate_assignees(obj, related)
      relate_ca(obj, related)

      if src_obj:
        snapshot = snapshots.get(src_obj.get('id'))
        if snapshot:
          parent_title = snapshot.parent.title
          child_revision_title = snapshot.revision.content['title']
          obj.title = u'{} assessment for {}'.format(child_revision_title,
                                                     parent_title)


def map_assessment(assessment, obj):
  """Creates a relationship between an assessment and an object. This also
  generates automappings. Fails silently if obj dict does not have id and type
  keys.

  Args:
    assessment (models.Assessment): The assessment model
    obj (dict): A dict with `id` and `type`.
  Returns:
    None
  """
  obj = obj or {}
  if 'id' not in obj or 'type' not in obj:
    return
  rel = Relationship(**{
      "source": assessment,
      "destination_id": obj["id"],
      "destination_type": obj["type"],
      "context": assessment.context,
  })
  db.session.add(rel)


def get_by_id(obj):
  """Get object instance by id"""
  if not obj:
    return

  model = get_model_query(obj["type"])
  return model.get(obj["id"])


def get_model_query(model_type):
  """Get model query"""
  model = getattr(all_models, model_type, None)
  return db.session.query(model)


def get_value(people_group, audit, obj, template=None):
  """Return the people related to an Audit belonging to the given role group.

  Args:
    people_group: (string) the name of the group of people to return,
      e.g. "assessors"
    template: (ggrc.models.AssessmentTemplate) a template to take into
      consideration
    audit: (ggrc.models.Audit) an audit instance
    obj: an object related to `audit`, can be anything that can be mapped
      to an Audit, e.g. Control, Issue, Facility, etc.
  Returns:
    Either a Person object, a list of Person objects, or None if no people
    matching the criteria are found.
  """
  auditors = (
      user_role.person for user_role in audit.context.user_roles
      if user_role.role.name == u"Auditor"
  )

  if not template:
    if people_group == "creator":
      # don't use get_current_user because that returns a proxy
      return Person.query.get(get_current_user_id())
    elif people_group == "assessors":
      return list(auditors)

    return None

  types = {
      "Object Owners": [
          get_by_id(owner)
          for owner in obj.revision.content.get("owners", [])
      ],
      "Audit Lead": getattr(audit, "contact", None),
      "Primary Contact": get_by_id(obj.revision.content.get("contact")),
      "Secondary Contact": get_by_id(
          obj.revision.content.get("secondary_contact")),
      "Primary Assessor": get_by_id(
          obj.revision.content.get("principal_assessor")),
      "Secondary Assessor": get_by_id(
          obj.revision.content.get("secondary_assessor")),
  }
  people = template.default_people.get(people_group)
  if not people:
    return None

  if isinstance(people, list):
    return [get_by_id({
        'type': 'Person',
        'id': person_id
    }) for person_id in people]

  # only consume the generator if it will be used in the return value
  if people == u"Auditors":
    types[u"Auditors"] = list(auditors)

  return types.get(people)


def assign_people(assignees, assignee_role, assessment, relationships):
  """Create a list of people with roles

      Args:
        assignees (list of model instances): List of people
        assignee_role (string): It can be either Assessor or Verifier
        assessment (model instance): Assessment model
        relationships (list): List relationships between assignees and
                              assessment with merged AssigneeType's
  """
  assignees = assignees if isinstance(assignees, list) else [assignees]
  assignees = [assignee for assignee in assignees if assignee is not None]

  if not assignees and assignee_role != "Verifier":
    assignees.append(assessment.modified_by)

  for assignee in assignees:
    rel = (val for val in relationships if val["source"] == assignee)
    rel = next(rel, None)
    if rel:
      values = rel["attrs"]["AssigneeType"].split(",")
      values.append(assignee_role)
      rel["attrs"]["AssigneeType"] = ",".join(set(values))
    else:
      relationships.append(
          get_relationship_dict(assignee, assessment, assignee_role))


def get_relationship_dict(source, destination, role):
  """ Returns relationship object with Assignee Type"""
  return {
      "source": source,
      "destination": destination,
      "context": destination.context,
      "attrs": {
          "AssigneeType": role,
      },
  }


def relate_assignees(assessment, related):
  """Generates assignee list and relates them to Assessment objects

    Args:
        assessment (model instance): Assessment model
        related (dict): Dict containing model instances related to assessment
                        - obj
                        - audit
                        - template (an AssessmentTemplate, can be None)
  """
  people_types = {
      "assessors": "Assessor",
      "verifiers": "Verifier",
      "creator": "Creator",
  }
  people_list = []

  for person_key, person_type in people_types.iteritems():
    assign_people(
        get_value(person_key, **related),
        person_type, assessment, people_list)

  for person in people_list:
    if person['source'] is not None and person['destination'] is not None:
      rel = Relationship(
          source=person['source'],
          destination=person['destination'],
          context=person['context'])
      rel.attrs = person['attrs']
      db.session.add(rel)


def relate_ca(assessment, related):
  """Generates custom attribute list and relates it to Assessment objects

    Args:
        assessment (model instance): Assessment model
        related (dict): Dict containing model instances related to assessment
                        - template
                        - obj
                        - audit
  """
  if not related["template"]:
    return

  ca_query = all_models.CustomAttributeDefinition.eager_query()
  ca_definitions = ca_query.filter_by(
      definition_id=related["template"].id,
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
