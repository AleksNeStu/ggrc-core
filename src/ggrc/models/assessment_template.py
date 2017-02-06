# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>


"""A module containing the implementation of the assessment template entity."""

from sqlalchemy.orm import validates

from ggrc import db
from ggrc.models import assessment
from ggrc.models import audit
from ggrc.models import mixins
from ggrc.models import relationship
from ggrc.models.exceptions import ValidationError
from ggrc.models.reflection import AttributeInfo
from ggrc.models.reflection import PublishOnly
from ggrc.models.types import JsonType
from ggrc.services import common


class AssessmentTemplate(assessment.AuditRelationship, relationship.Relatable,
                         mixins.Titled, mixins.CustomAttributable,
                         mixins.Slugged, db.Model):
  """A class representing the assessment template entity.

  An Assessment Template is a template that allows users for easier creation of
  multiple Assessments that are somewhat similar to each other, avoiding the
  need to repeatedly define the same set of properties for every new Assessment
  object.
  """
  __tablename__ = "assessment_templates"
  _mandatory_default_people = ("assessors", "verifiers")

  PER_OBJECT_CUSTOM_ATTRIBUTABLE = True

  # the type of the object under assessment
  template_object_type = db.Column(db.String, nullable=True)

  # whether to use the control test plan as a procedure
  test_plan_procedure = db.Column(db.Boolean, nullable=False, default=False)

  # procedure description
  procedure_description = db.Column(db.Text, nullable=True)

  # the people that should be assigned by default to each assessment created
  # within the releated audit
  default_people = db.Column(JsonType, nullable=False)

  # labels to show to the user in the UI for various default people values
  DEFAULT_PEOPLE_LABELS = {
      "Object Owners": "Object Owners",
      "Audit Lead": "Audit Lead",
      "Auditors": "Auditors",
      "Primary Assessor": "Principal Assessor",
      "Secondary Assessors": "Secondary Assessors",
      "Primary Contact": "Primary Contact",
      "Secondary Contact": "Secondary Contact",
  }

  _title_uniqueness = False

  # REST properties
  _publish_attrs = [
      "template_object_type",
      "test_plan_procedure",
      "procedure_description",
      "default_people",
      PublishOnly("DEFAULT_PEOPLE_LABELS")
  ]

  _aliases = {
      "default_assessors": {
          "display_name": "Default Assessors",
          "mandatory": True,
          "filter_by": "_nop_filter",
      },
      "default_verifier": {
          "display_name": "Default Verifier",
          "mandatory": True,
          "filter_by": "_nop_filter",
      },
      "default_test_plan": {
          "display_name": "Default Test Plan",
          "filter_by": "_nop_filter",
      },
      "test_plan_procedure": {
          "display_name": "Use Control Test Plan",
          "mandatory": False,
      },
      "template_object_type": {
          "display_name": "Object Under Assessment",
          "mandatory": True,
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
  def generate_slug_prefix_for(cls, obj):
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
    }
    assessment_template_copy = AssessmentTemplate(**data)
    db.session.add(assessment_template_copy)
    db.session.flush()
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

    Check if the default_people contains both assessors and verifiers. The
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


def create_audit_relationship(audit_stub, obj):
  """Create audit to assessment template relationship"""
  parent_audit = audit.Audit.query.get(audit_stub["id"])

  rel = relationship.Relationship(
      source=parent_audit,
      destination=obj,
      context=parent_audit.context)
  db.session.add(rel)


@common.Resource.model_posted.connect_via(AssessmentTemplate)
def handle_assessment_template(sender, obj=None, src=None, service=None):
  # pylint: disable=unused-argument
  """Handle Assessment Template POST

  If "audit" is set on POST, create relationship with Assessment template.
  """
  if "audit" in src:
      create_audit_relationship(src["audit"], obj)
