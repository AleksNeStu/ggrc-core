# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Integration tests for "preconditions_failed" CAV and CAable fields logic."""

from ggrc.models.assessment import Assessment
from integration.ggrc import TestCase
from integration.ggrc import generator
from integration.ggrc.models import factories

GENERATOR = generator.ObjectGenerator()


# pylint: disable=too-many-instance-attributes
class CustomAttributeMock(object):
  """Defines CustomAttributeDefinition and CustomAttributeValue objects"""

  # pylint: disable=too-many-arguments
  def __init__(self, attributable, attribute_type="Text", mandatory=False,
               dropdown_parameters=None, global_=False, value=None):
    self.attributable = attributable
    self.attribute_type = attribute_type
    self.mandatory = mandatory
    self.dropdown_parameters = dropdown_parameters
    self.attribute_value = value
    self.global_ = global_
    self.definition = self.make_definition()
    self.value = self.make_value()

  def make_definition(self):
    """Generate a custom attribute definition."""
    definition = factories.CustomAttributeDefinitionFactory(
        attribute_type=self.attribute_type,
        definition_type=self.attributable._inflector.table_singular,
        definition_id=None if self.global_ else self.attributable.id,
        mandatory=self.mandatory,
        multi_choice_options=(self.dropdown_parameters[0]
                              if self.dropdown_parameters else None),
        multi_choice_mandatory=(self.dropdown_parameters[1]
                                if self.dropdown_parameters else None),
    )
    return definition

  def make_value(self):
    """Generate a custom attribute value."""
    if self.attribute_value is not None:
      value = factories.CustomAttributeValueFactory(
          custom_attribute=self.definition,
          attributable=self.attributable,
          attribute_value=self.attribute_value,
      )
    else:
      value = None
    return value


# pylint: disable=super-on-old-class; TestCase is a new-style class
class TestPreconditionsFailed(TestCase):
  """Integration tests suite for preconditions_failed fields logic."""

  # pylint: disable=invalid-name

  def setUp(self):
    super(TestPreconditionsFailed, self).setUp()
    self.assessment = factories.AssessmentFactory(
        status=Assessment.PROGRESS_STATE,
    )

  def test_preconditions_failed_with_no_ca(self):
    """No preconditions failed with no CA restrictions."""
    preconditions_failed = self.assessment.preconditions_failed

    self.assertEqual(preconditions_failed, False)

  def test_preconditions_failed_with_no_mandatory_ca(self):
    """No preconditions failed with no CA-introduced restrictions."""
    ca_text = CustomAttributeMock(self.assessment, attribute_type="Text",
                                  value="")
    ca_cbox = CustomAttributeMock(self.assessment, attribute_type="Checkbox",
                                  value="")

    preconditions_failed = self.assessment.preconditions_failed

    self.assertEqual(preconditions_failed, False)
    self.assertFalse(any(ca_text.value.preconditions_failed.values()))
    self.assertFalse(any(ca_cbox.value.preconditions_failed.values()))

  def test_preconditions_failed_with_mandatory_empty_ca(self):
    """Preconditions failed if mandatory CA is empty."""
    ca = CustomAttributeMock(self.assessment, mandatory=True, value="")

    preconditions_failed = self.assessment.preconditions_failed

    self.assertEqual(preconditions_failed, True)
    self.assertEqual(
        [k for k, v in ca.value.preconditions_failed.items() if v],
        ["value"])

  def test_preconditions_failed_with_mandatory_filled_ca(self):
    """No preconditions failed if mandatory CA is filled."""
    ca = CustomAttributeMock(self.assessment, mandatory=True, value="Foo")

    preconditions_failed = self.assessment.preconditions_failed

    self.assertEqual(preconditions_failed, False)
    self.assertFalse(any(ca.value.preconditions_failed.values()))

  def test_preconditions_failed_with_mandatory_empty_global_ca(self):
    """Preconditions failed if global mandatory CA is empty."""
    ca = CustomAttributeMock(self.assessment, mandatory=True, global_=True,
                             value="")

    preconditions_failed = self.assessment.preconditions_failed

    self.assertEqual(preconditions_failed, True)
    self.assertEqual(
        [k for k, v in ca.value.preconditions_failed.items() if v],
        ["value"])
    self.assertTrue(
        self.assessment.global_attributes[0]['is_preconditions_failed'])

  def test_preconditions_failed_with_mandatory_filled_global_ca(self):
    """No preconditions failed if global mandatory CA is filled."""
    ca = CustomAttributeMock(self.assessment, mandatory=True, global_=True,
                             value="Foo")

    preconditions_failed = self.assessment.preconditions_failed

    self.assertEqual(preconditions_failed, False)
    self.assertFalse(any(ca.value.preconditions_failed.values()))

  def test_preconditions_failed_with_missing_mandatory_comment(self):
    """Preconditions failed if comment required by CA is missing."""
    ca = CustomAttributeMock(
        self.assessment,
        attribute_type="Dropdown",
        dropdown_parameters=("foo,comment_required", "0,1"),
        value="comment_required",
    )

    preconditions_failed = self.assessment.preconditions_failed

    self.assertEqual(preconditions_failed, True)
    self.assertEqual(
        [k for k, v in ca.value.preconditions_failed.items() if v],
        ["comment"])

  def test_preconditions_failed_with_missing_mandatory_evidence(self):
    """Preconditions failed if evidence required by CA is missing."""
    ca = CustomAttributeMock(
        self.assessment,
        attribute_type="Dropdown",
        dropdown_parameters=("foo,evidence_required", "0,2"),
        value="evidence_required",
    )

    preconditions_failed = self.assessment.preconditions_failed

    self.assertEqual(preconditions_failed, True)
    self.assertEqual(
        [k for k, v in ca.value.preconditions_failed.items() if v],
        ["evidence"])

  def test_preconditions_failed_with_present_mandatory_comment(self):
    """No preconditions failed if comment required by CA is present."""
    ca = CustomAttributeMock(
        self.assessment,
        attribute_type="Dropdown",
        dropdown_parameters=("foo,comment_required", "0,1"),
        value=None,  # the value is made with generator to store revision too
    )

    _, ca.value = GENERATOR.generate_custom_attribute_value(
        custom_attribute_id=ca.definition.id,
        attributable=self.assessment,
        attribute_value="comment_required",
    )
    comment = factories.CommentFactory(
        assignee_type="Assessor",
        description="Mandatory comment",
    )
    comment.custom_attribute_revision_upd({
        "custom_attribute_revision_upd": {
            "custom_attribute_value": {
                "id": ca.value.id,
            },
        },
    })
    factories.RelationshipFactory(
        source=self.assessment,
        destination=comment,
    )

    preconditions_failed = self.assessment.preconditions_failed

    self.assertEqual(preconditions_failed, False)
    self.assertFalse(any(ca.value.preconditions_failed.values()))
    self.assertFalse(
        self.assessment.local_attributes[0]['is_preconditions_failed'])

  def test_preconditions_failed_with_present_mandatory_evidence(self):
    """No preconditions failed if evidence required by CA is present."""
    ca = CustomAttributeMock(
        self.assessment,
        attribute_type="Dropdown",
        dropdown_parameters=("foo,evidence_required", "0,2"),
        value="evidence_required",
    )
    evidence = factories.EvidenceFactory(
        title="Mandatory evidence",
    )
    factories.RelationshipFactory(
        source=self.assessment,
        destination=evidence,
    )

    preconditions_failed = self.assessment.preconditions_failed

    self.assertEqual(preconditions_failed, False)
    self.assertFalse(any(ca.value.preconditions_failed.values()))

  def test_preconditions_failed_with_mandatory_comment_and_evidence(self):
    """Preconditions failed with mandatory comment and evidence missing."""
    ca = CustomAttributeMock(
        self.assessment,
        attribute_type="Dropdown",
        dropdown_parameters=("foo,comment_and_evidence_required", "0,3"),
        value="comment_and_evidence_required",
    )

    preconditions_failed = self.assessment.preconditions_failed

    self.assertEqual(preconditions_failed, True)
    self.assertEqual(set([k for k, v in
                          ca.value.preconditions_failed.items() if v]),
                     {"comment", "evidence"})

  def test_preconditions_failed_with_changed_value(self):
    """Preconditions failed and comment invalidated on update to CAV."""
    ca = CustomAttributeMock(
        self.assessment,
        attribute_type="Dropdown",
        dropdown_parameters=("foo,comment_required", "0,1"),
        value=None,  # the value is made with generator to store revision too
    )
    _, ca.value = GENERATOR.generate_custom_attribute_value(
        custom_attribute_id=ca.definition.id,
        attributable=self.assessment,
        attribute_value="comment_required",
    )
    comment = factories.CommentFactory(
        assignee_type="Assessor",
        description="Mandatory comment",
    )
    comment.custom_attribute_revision_upd({
        "custom_attribute_revision_upd": {
            "custom_attribute_value": {
                "id": ca.value.id,
            },
        },
    })
    factories.RelationshipFactory(
        source=self.assessment,
        destination=comment,
    )

    # new CA value not requiring comment
    self.assessment.local_attributes = [{
        "id": ca.definition.id,
        "values": [{"value": "foo"}]
    }]
    GENERATOR.api.modify_object(self.assessment, {})

    # new CA value requiring comment; the old comment should be considered
    # invalid
    self.assessment.local_attributes = [{
        "id": ca.definition.id,
        "values": [{"value": "comment_required"}]
    }]
    GENERATOR.api.modify_object(self.assessment, {})

    preconditions_failed = self.assessment.preconditions_failed

    self.assertEqual(preconditions_failed, True)

  def test_preconditions_failed_with_missing_several_mandatory_evidences(self):
    """Preconditions failed if count(evidences) < count(evidences_required)."""
    ca1 = CustomAttributeMock(
        self.assessment,
        attribute_type="Dropdown",
        dropdown_parameters=("foo,evidence_required", "0,2"),
        value="evidence_required"
    )
    ca2 = CustomAttributeMock(
        self.assessment,
        attribute_type="Dropdown",
        dropdown_parameters=("foo,evidence_required", "0,2"),
        value="evidence_required"
    )
    # only one evidence provided yet
    evidence = factories.EvidenceFactory(
        title="Mandatory evidence",
    )
    factories.RelationshipFactory(
        source=self.assessment,
        destination=evidence,
    )

    preconditions_failed = self.assessment.preconditions_failed

    self.assertEqual(preconditions_failed, True)
    self.assertEqual(
        [k for k, v in ca1.value.preconditions_failed.items() if v],
        ["evidence"])
    self.assertEqual(
        [k for k, v in ca2.value.preconditions_failed.items() if v],
        ["evidence"])

  def test_preconditions_failed_with_several_mandatory_evidences(self):
    """No preconditions failed if evidences required by CAs are present"""
    ca1 = CustomAttributeMock(
        self.assessment,
        attribute_type="Dropdown",
        dropdown_parameters=("foo,evidence_required", "0,2"),
        value="evidence_required"
    )
    ca2 = CustomAttributeMock(
        self.assessment,
        attribute_type="Dropdown",
        dropdown_parameters=("foo,evidence_required", "0,2"),
        value="evidence_required"
    )
    # only one evidence provided yet
    evidence = factories.EvidenceFactory(
        title="Mandatory evidence",
    )
    factories.RelationshipFactory(
        source=self.assessment,
        destination=evidence,
    )

    # the second evidence
    evidence = factories.EvidenceFactory(
        title="Second mandatory evidence",
    )
    factories.RelationshipFactory(
        source=self.assessment,
        destination=evidence,
    )

    preconditions_failed = self.assessment.preconditions_failed

    self.assertEqual(preconditions_failed, False)
    self.assertFalse(any(ca1.value.preconditions_failed.values()))
    self.assertFalse(any(ca2.value.preconditions_failed.values()))
