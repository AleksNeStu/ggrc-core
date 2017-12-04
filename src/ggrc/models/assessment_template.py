# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>


"""A module containing the implementation of the assessment template entity."""

from sqlalchemy.orm import validates
from werkzeug.exceptions import Forbidden

from ggrc import db
from ggrc.access_control.roleable import Roleable
from ggrc import login
from ggrc.builder import simple_property
from ggrc.models import assessment
from ggrc.models import audit
from ggrc.models import issuetracker_issue
from ggrc.models import mixins
from ggrc.models import relationship
from ggrc.models.mixins import clonable
from ggrc.models.exceptions import ValidationError
from ggrc.models.reflection import AttributeInfo
from ggrc.models import reflection
from ggrc.models.types import JsonType
from ggrc.services import signals
from ggrc.fulltext.mixin import Indexed
from ggrc.rbac.permissions import permissions_for


class AssessmentTemplate(assessment.AuditRelationship, relationship.Relatable,
                         mixins.Titled, mixins.CustomAttributable,
                         Roleable, mixins.Slugged, mixins.Stateful,
                         clonable.MultiClonable, Indexed, db.Model):
  """A class representing the assessment template entity.

  An Assessment Template is a template that allows users for easier creation of
  multiple Assessments that are somewhat similar to each other, avoiding the
  need to repeatedly define the same set of properties for every new Assessment
  object.
  """
  __tablename__ = "assessment_templates"
  _mandatory_default_people = ("assignees",)

  PER_OBJECT_CUSTOM_ATTRIBUTABLE = True

  RELATED_TYPE = 'assessment'

  # the type of the object under assessment
  template_object_type = db.Column(db.String, nullable=True)

  # whether to use the control test plan as a procedure
  test_plan_procedure = db.Column(db.Boolean, nullable=False, default=False)

  # procedure description
  procedure_description = db.Column(db.Text, nullable=False, default=u"")

  # the people that should be assigned by default to each assessment created
  # within the releated audit
  default_people = db.Column(JsonType, nullable=False)

  # labels to show to the user in the UI for various default people values
  DEFAULT_PEOPLE_LABELS = {
      "Admin": "Object Admins",
      "Audit Lead": "Audit Captain",
      "Auditors": "Auditors",
      "Principal Assignees": "Principal Assignees",
      "Secondary Assignees": "Secondary Assignees",
      "Primary Contacts": "Primary Contacts",
      "Secondary Contacts": "Secondary Contacts",
  }

  _title_uniqueness = False

  DRAFT = 'Draft'
  ACTIVE = 'Active'
  DEPRECATED = 'Deprecated'

  VALID_STATES = (DRAFT, ACTIVE, DEPRECATED, )

  # REST properties
  _api_attrs = reflection.ApiAttributes(
      'template_object_type',
      'test_plan_procedure',
      'procedure_description',
      'default_people',
      reflection.Attribute('issue_tracker', create=False, update=False),
      reflection.Attribute('archived', create=False, update=False),
      reflection.Attribute(
          'DEFAULT_PEOPLE_LABELS', create=False, update=False),
  )

  _fulltext_attrs = [
      "archived"
  ]

  _aliases = {
      "status": {
          "display_name": "State",
          "mandatory": False,
          "description": "Options are:\n{}".format('\n'.join(VALID_STATES))
      },
      "default_assignees": {
          "display_name": "Default Assignees",
          "mandatory": True,
          "filter_by": "_nop_filter",
      },
      "default_verifier": {
          "display_name": "Default Verifiers",
          "mandatory": False,
          "filter_by": "_nop_filter",
      },
      "default_test_plan": {
          "display_name": "Default Test Plan",
          "filter_by": "_nop_filter",
      },
      "test_plan_procedure": {
          "display_name": "Use Control Assessment Procedure",
          "mandatory": False,
      },
      "template_object_type": {
          "display_name": "Object Under Assessment",
          "mandatory": True,
      },
      "archived": {
          "display_name": "Archived",
          "mandatory": False,
          "ignore_on_update": True,
          "view_only": True,
      },
      "template_custom_attributes": {
          "display_name": "Custom Attributes",
          "type": AttributeInfo.Type.SPECIAL_MAPPING,
          "filter_by": "_nop_filter",
          "description": (
              "List of custom attributes for the assessment template\n"
              "One attribute per line. fields are separated by commas ','\n\n"
              "<attribute type>, <attribute name>, [<attribute value1>, "
              "<attribute value2>, ...]\n\n"
              "Valid attribute types: Text, Rich Text, Date, Checkbox, Person,"
              "Dropdown.\n"
              "attribute name: Any single line string without commas. Leading "
              "and trailing spaces are ignored.\n"
              "list of attribute values: Comma separated list, only used if "
              "attribute type is 'Dropdown'. Prepend '(a)' if the value has a "
              "mandatory attachment and/or (c) if the value requires a "
              "mandatory comment.\n\n"
              "Limitations: Dropdown values can not start with either '(a)' or"
              "'(c)' and attribute names can not contain commas ','."
          ),
      },
  }

  @classmethod
  def _nop_filter(cls, _):
    """No operation filter.

    This is used for objects for which we can not implement a normal sql query
    filter. Example is default_verifier field that is a json string in the db
    and we can not create direct queries on json fields.
    """
    return None

  @classmethod
  def generate_slug_prefix(cls):
    return "TEMPLATE"

  def _clone(self):
    """Clone Assessment Template.

    Returns:
      Instance of assessment template copy.
    """
    data = {
        "title": self.title,
        "template_object_type": self.template_object_type,
        "test_plan_procedure": self.test_plan_procedure,
        "procedure_description": self.procedure_description,
        "default_people": self.default_people,
        "modified_by": login.get_current_user(),
    }
    assessment_template_copy = AssessmentTemplate(**data)
    db.session.add(assessment_template_copy)
    return assessment_template_copy

  def clone(self, target):
    """Clone Assessment Template and related custom attributes."""
    assessment_template_copy = self._clone()
    rel = relationship.Relationship(
        source=target,
        destination=assessment_template_copy
    )
    db.session.add(rel)
    db.session.flush()

    for cad in self.custom_attribute_definitions:
      # pylint: disable=protected-access
      cad._clone(assessment_template_copy)

    return (assessment_template_copy, rel)

  @validates('default_people')
  def validate_default_people(self, key, value):
    """Check that default people lists are not empty.

    Check if the default_people contains both assignees and verifiers. The
    values of those fields must be truthy, and if the value is a string it
    must be a valid default people label. If the value is not a string, it
    should be a list of valid user ids, but that is too expensive to test in
    this validator.
    """
    # pylint: disable=unused-argument
    for mandatory in self._mandatory_default_people:
      mandatory_value = value.get(mandatory)
      if (not mandatory_value or
              isinstance(mandatory_value, list) and
              any(not isinstance(p_id, (int, long))
                  for p_id in mandatory_value) or
              isinstance(mandatory_value, basestring) and
              mandatory_value not in self.DEFAULT_PEOPLE_LABELS):
        raise ValidationError(
            'Invalid value for default_people.{field}. Expected a people '
            'label in string or a list of int people ids, received {value}.'
            .format(field=mandatory, value=mandatory_value),
        )

    return value

  @simple_property
  def archived(self):
    """Fetch the archived boolean from Audit"""
    if hasattr(self, 'context') and hasattr(self.context, 'related_object'):
      return getattr(self.context.related_object, 'archived', False)
    return False

  @simple_property
  def issue_tracker(self):
    """Returns representation of issue tracker related info as a dict."""
    issue_obj = issuetracker_issue.IssuetrackerIssue.get_issue(
        'AssessmentTemplate', self.id)
    return issue_obj.to_dict() if issue_obj is not None else {}


def create_audit_relationship(audit_stub, obj):
  """Create audit to assessment template relationship"""
  # pylint: disable=W0212
  parent_audit = audit.Audit.query.get(audit_stub["id"])
  if not permissions_for()._is_allowed_for(parent_audit, "update"):
    raise Forbidden()
  rel = relationship.Relationship(
      source=parent_audit,
      destination=obj,
      context=parent_audit.context)
  db.session.add(rel)


@signals.Restful.model_posted.connect_via(AssessmentTemplate)
def handle_assessment_template(sender, obj=None, src=None, service=None):
  # pylint: disable=unused-argument
  """Handle Assessment Template POST

  If "audit" is set on POST, create relationship with Assessment template.
  """
  if "audit" in src:
    create_audit_relationship(src["audit"], obj)
