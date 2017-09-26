# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Integration tests for WithSimilarityScore logic."""

import json

import ddt

from ggrc import db
from ggrc import models
from ggrc.snapshotter.rules import Types
from ggrc_risks import models as risk_models

from integration.ggrc import TestCase
import integration.ggrc.generator
from integration.ggrc.models import factories


@ddt.ddt
class TestWithSimilarityScore(TestCase):
  """Integration test suite for WithSimilarityScore functionality."""

  def setUp(self):
    super(TestWithSimilarityScore, self).setUp()
    self.obj_gen = integration.ggrc.generator.ObjectGenerator()
    self.client.get("/login")

  @staticmethod
  def make_relationships(source, destinations):
    for destination in destinations:
      factories.RelationshipFactory(
          source=source,
          destination=destination,
      )

  @staticmethod
  def get_object_snapshot(scope_parent, object_):
    # pylint: disable=protected-access
    return db.session.query(models.Snapshot).filter(
        models.Snapshot.parent_type == scope_parent._inflector.table_singular,
        models.Snapshot.parent_id == scope_parent.id,
        models.Snapshot.child_type == object_._inflector.table_singular,
        models.Snapshot.child_id == object_.id
    ).one()

  def make_scope_relationships(self, source, scope_parent, objects):
    """Create relationships between object and snapshots of provided object"""
    snapshots = []
    for object_ in objects:
      snapshot = self.get_object_snapshot(scope_parent, object_)
      snapshots += [snapshot]
    self.make_relationships(source, snapshots)

  def make_assessments(self, assessment_mappings, with_types=False):
    """Create six assessments and map them to audit, control, objective.

    Each of the created assessments is mapped to its own subset of {audit,
    control, objective} so each of them has different similarity weight.

    Returns: the six generated assessments and their weights in a dict.
    """

    assessments = []
    for all_mappings in assessment_mappings:
      audit = [x for x in all_mappings
               if hasattr(x, "type") and x.type == "Audit"][0]
      if with_types:
        assessment_type = all_mappings[1]
        mappings_bound = 2
      else:
        assessment_type = "Control"
        mappings_bound = 1
      assessment = factories.AssessmentFactory(
          audit=audit, assessment_type=assessment_type
      )
      mappings = all_mappings[mappings_bound:]
      ordinary_mappings = [x for x in mappings if x.type not in Types.all]
      snapshot_mappings = [x for x in mappings if x.type in Types.all]
      self.make_relationships(assessment, [audit] + ordinary_mappings)
      self.make_scope_relationships(assessment, audit,
                                    snapshot_mappings)
      assessments.append(assessment)

    return assessments

  @ddt.data(
      ("Risk", "Risk", "Risk"),
      ("Risk", "Control", "Risk"),
      ("Control", "Control", "Risk"),
      ("Control", "Control", "Control"),
  )
  def test_get_similar_basic(self, asmnt_types):
    """Basic check of similar objects manually and via Query API.

    We create three programs, map them to the same risk, create thress audits
    and verify that we get the same result manually and via Query API.
    """
    # pylint: disable=too-many-locals
    with factories.single_commit():
      program_1 = factories.ProgramFactory(title="Program 1")
      program_2 = factories.ProgramFactory(title="Program 2")
      program_3 = factories.ProgramFactory(title="Program 3")

      risk_program_1 = factories.RiskFactory(title="Risk 1")

    self.make_relationships(
        program_1, [
            risk_program_1,
        ],
    )
    self.make_relationships(
        program_2, [
            risk_program_1,
        ],
    )
    self.make_relationships(
        program_3, [
            risk_program_1,
        ],
    )

    program_1 = models.Program.query.filter_by(title="Program 1").one()
    program_2 = models.Program.query.filter_by(title="Program 2").one()
    program_3 = models.Program.query.filter_by(title="Program 3").one()
    risk_program_1 = risk_models.Risk.query.get(risk_program_1.id)

    audit_1 = self.obj_gen.generate_object(models.Audit, {
        "title": "Audit 1",
        "program": {"id": program_1.id},
        "status": "Planned"
    })[1]
    audit_2 = self.obj_gen.generate_object(models.Audit, {
        "title": "Audit 2",
        "program": {"id": program_2.id},
        "status": "Planned"
    })[1]
    audit_3 = self.obj_gen.generate_object(models.Audit, {
        "title": "Audit 3",
        "program": {"id": program_3.id},
        "status": "Planned"
    })[1]

    assessment_mappings = [
        [audit_1, asmnt_types[0], risk_program_1],
        [audit_2, asmnt_types[1], risk_program_1],
        [audit_3, asmnt_types[2], risk_program_1],
    ]
    assessments = self.make_assessments(assessment_mappings, with_types=True)

    risk_asmnt_ids = {asmnt.id for asmnt in assessments
                      if asmnt.assessment_type == "Risk"}
    for assessment in assessments:
      similar_objects = models.Assessment.get_similar_objects_query(
          id_=assessment.id,
          types=["Assessment"],
      ).all()

      # Current assessment is not similar to itself
      if risk_asmnt_ids and assessment.id in risk_asmnt_ids:
        expected_ids = risk_asmnt_ids - {assessment.id}
      else:
        expected_ids = set()

      self.assertSetEqual(
          {obj.id for obj in similar_objects},
          expected_ids,
      )

      query = [{
          "object_name": "Assessment",
          "type": "ids",
          "filters": {
              "expression": {
                  "op": {"name": "similar"},
                  "object_name": "Assessment",
                  "ids": [str(assessment.id)],
              },
          },
      }]
      response = self.client.post(
          "/query",
          data=json.dumps(query),
          headers={"Content-Type": "application/json"},
      )
      self.assertSetEqual(
          set(json.loads(response.data)[0]["Assessment"]["ids"]),
          expected_ids,
      )

  def test_similar_partially_matching(self):
    """Basic check of similar objects manually and via Query API.

    We create three programs, map one them to the two objectives, create two
    audits and verify that we get the same result manually and via Query API.

    We also ensure that for only single matching objective we do not
    fetch that assessment is as related.
    """

    # pylint: disable=too-many-locals
    with factories.single_commit():
      program_1 = factories.ProgramFactory(title="Program 1")
      program_2 = factories.ProgramFactory(title="Program 2")
      program_3 = factories.ProgramFactory(title="Program 3")

      objective_1_program_1 = factories.ObjectiveFactory(title="Objective 1")
      objective_2_program_1 = factories.ObjectiveFactory(title="Objective 2")

    self.make_relationships(
        program_1, [
            objective_1_program_1,
            objective_2_program_1,
        ],
    )

    self.make_relationships(
        program_2, [
            objective_1_program_1,
            objective_2_program_1,
        ],
    )

    self.make_relationships(
        program_3, [
            objective_1_program_1,
        ],
    )

    program_1 = models.Program.query.filter_by(title="Program 1").one()
    program_2 = models.Program.query.filter_by(title="Program 2").one()
    program_3 = models.Program.query.filter_by(title="Program 3").one()

    objective_1_program_1 = models.Objective.query.filter_by(
        title="Objective 1").one()
    objective_2_program_1 = models.Objective.query.filter_by(
        title="Objective 2").one()

    _, audit_1 = self.obj_gen.generate_object(models.Audit, {
        "title": "Audit 1",
        "program": {"id": program_1.id},
        "status": "Planned",
    })

    _, audit_2 = self.obj_gen.generate_object(models.Audit, {
        "title": "Audit 2",
        "program": {"id": program_2.id},
        "status": "Planned",
    })

    _, audit_3 = self.obj_gen.generate_object(models.Audit, {
        "title": "Audit 3",
        "program": {"id": program_3.id},
        "status": "Planned",
    })

    assessment_mappings = [
        [audit_1, "Objective", objective_1_program_1, objective_2_program_1],
        [audit_2, "Objective", objective_1_program_1, objective_2_program_1],
        [audit_3, "Objective"],
    ]

    assessments = self.make_assessments(assessment_mappings, with_types=True)

    similar_objects = models.Assessment.get_similar_objects_query(
        id_=assessments[0].id,
        types=["Assessment"],
    ).all()

    expected_ids = {assessments[1].id}

    self.assertSetEqual(
        {obj.id for obj in similar_objects},
        expected_ids,
    )
    self.assertNotIn(assessments[2].id, similar_objects)

    query = [{
        "object_name": "Assessment",
        "type": "ids",
        "filters": {
            "expression": {
                "op": {"name": "similar"},
                "object_name": "Assessment",
                "ids": [str(assessments[0].id)],
            },
        },
    }]
    response = self.client.post(
        "/query",
        data=json.dumps(query),
        headers={"Content-Type": "application/json"},
    )
    self.assertSetEqual(
        set(json.loads(response.data)[0]["Assessment"]["ids"]),
        expected_ids,
    )

  def test_sort_by_similarity(self):
    """Check sorting by __similarity__ value with query API."""

    # pylint: disable=too-many-locals
    with factories.single_commit():
      program_1 = factories.ProgramFactory(title="Program 1")

      objective_1_program_1 = factories.ObjectiveFactory(title="Objective 1")
      objective_2_program_1 = factories.ObjectiveFactory(title="Objective 2")
      control_1_program_1 = factories.ControlFactory(title="Control 1")
      control_2_program_1 = factories.ControlFactory(title="Control 2")

    self.make_relationships(
        program_1, [
            objective_1_program_1,
            objective_2_program_1,
            control_1_program_1,
            control_2_program_1
        ],
    )

    program_1 = models.Program.query.filter_by(title="Program 1").one()

    _, audit_1 = self.obj_gen.generate_object(models.Audit, {
        "title": "Audit 1",
        "program": {"id": program_1.id},
        "status": "Planned",
    })

    _, audit_2 = self.obj_gen.generate_object(models.Audit, {
        "title": "Audit 2",
        "program": {"id": program_1.id},
        "status": "Planned",
    })

    objective_1_program_1 = models.Objective.query.filter_by(
        title="Objective 1").one()
    objective_2_program_1 = models.Objective.query.filter_by(
        title="Objective 2").one()
    control_1_program_1 = models.Control.query.filter_by(
        title="Control 1").one()
    control_2_program_1 = models.Control.query.filter_by(
        title="Control 2").one()

    assessment_mappings = [
        [audit_1,
         objective_1_program_1, objective_2_program_1,
         control_1_program_1, control_2_program_1],
        [audit_1, control_1_program_1, control_2_program_1],
        [audit_1,
         objective_1_program_1, control_1_program_1],
        [audit_2,
         objective_1_program_1, objective_2_program_1,
         control_1_program_1, control_2_program_1],
        [audit_2,
         objective_1_program_1, control_1_program_1],
        [audit_2, control_1_program_1, control_2_program_1],
    ]

    # All created Assessments has 'Control' type so result weights are
    # equal to count of controls in assessment objects related to current one
    weights = [
        [1, 1, 2, 2, 2],
        [1, 1, 2, 2, 2],
        [1, 1, 1, 1, 1],
        [1, 1, 2, 2, 2],
        [1, 1, 1, 1, 1],
        [1, 1, 2, 2, 2],
    ]

    assessments = self.make_assessments(assessment_mappings)
    assessment_ids = [ass.id for ass in assessments]

    for aid, weight_defs in zip(assessment_ids, weights):
      similar_objects = models.Assessment.get_similar_objects_query(
          id_=aid,
          types=["Assessment"],
      ).all()

      sorted_similar = sorted(similar_objects,
                              key=lambda x: x.weight)

      self.assertEqual(
          weight_defs,
          [x.weight for x in sorted_similar]
      )

      query = [{
          "object_name": "Assessment",
          "type": "ids",
          "order_by": [{"name": "__similarity__"}],
          "filters": {
              "expression": {
                  "op": {"name": "similar"},
                  "object_name": "Assessment",
                  "ids": [str(aid)],
              },
          },
      }]
      response = self.client.post(
          "/query",
          data=json.dumps(query),
          headers={"Content-Type": "application/json"},
      )

      # our sorted results are only unstably sorted. As such we verify that
      # weights match and not actual object ids
      obj_weight = {so.id: so.weight for so in similar_objects}
      response_ids = json.loads(response.data)[0]["Assessment"]["ids"]
      response_weights = [obj_weight[rid] for rid in response_ids]

      self.assertListEqual(
          response_weights,
          [obj.weight for obj in sorted_similar],
      )

  def test_empty_similar_results(self):
    """Check empty similarity result."""
    query = [{
        "object_name": "Assessment",
        "type": "ids",
        "filters": {
            "expression": {
                "op": {"name": "similar"},
                "object_name": "Assessment",
                "ids": ["-1"],
            },
        },
    }]
    response = self.client.post(
        "/query",
        data=json.dumps(query),
        headers={"Content-Type": "application/json"},
    )

    self.assertListEqual(
        response.json[0]["Assessment"]["ids"],
        [],
    )

  def test_invalid_sort_by_similarity(self):
    """Check sorting by __similarity__ with query API when it is impossible."""

    # no filter by similarity but order by similarity
    query = [{
        "object_name": "Assessment",
        "order_by": [{"name": "__similarity__"}],
        "filters": {"expression": {}},
    }]

    response = self.client.post(
        "/query",
        data=json.dumps(query),
        headers={"Content-Type": "application/json"},
    )
    self.assert400(response)
    self.assertEqual(response.json["message"],
                     "Can't order by '__similarity__' when no 'similar' "
                     "filter was applied.")

    # filter by similarity in one query and order by similarity in another
    query = [
        {
            "object_name": "Assessment",
            "filters": {
                "expression": {
                    "op": {"name": "similar"},
                    "object_name": "Assessment",
                    "ids": [1],
                },
            },
        },
        {
            "object_name": "Assessment",
            "order_by": [{"name": "__similarity__"}],
            "filters": {"expression": {}},
        },
    ]

    response = self.client.post(
        "/query",
        data=json.dumps(query),
        headers={"Content-Type": "application/json"},
    )
    self.assert400(response)

  @ddt.data(
      ("Control", factories.ControlFactory, True),
      ("Objective", factories.ControlFactory, False),
      ("Control", factories.ObjectiveFactory, False),
      ("Objective", factories.ObjectiveFactory, True),
  )
  @ddt.unpack
  def test_asmt_issue_similarity(self, asmnt_type, obj_factory, issue_exists):
    """Test Issues related to assessments with 'similar' operation."""
    # Test object has to be created before others to produce revision
    obj = obj_factory()

    with factories.single_commit():
      audit = factories.AuditFactory()
      assessment1 = factories.AssessmentFactory(
          audit=audit, assessment_type=asmnt_type
      )
      assessment2 = factories.AssessmentFactory(audit=audit)
      issue = factories.IssueFactory()

      snapshot = factories.SnapshotFactory(
          parent=audit,
          child_id=obj.id,
          child_type=obj.type,
          revision_id=models.Revision.query.filter_by(
              resource_type=obj.type).one().id
      )

      factories.RelationshipFactory(source=audit, destination=assessment1)
      factories.RelationshipFactory(source=audit, destination=assessment2)
      factories.RelationshipFactory(source=audit, destination=issue)
      factories.RelationshipFactory(source=snapshot, destination=assessment1)
      factories.RelationshipFactory(source=snapshot, destination=issue)

    query = [{
        "object_name": "Issue",
        "type": "ids",
        "filters": {
            "expression": {
                "op": {"name": "similar"},
                "object_name": "Assessment",
                "ids": [assessment1.id],
            },
        },
    }]
    expected_ids = [issue.id]

    response = self.client.post(
        "/query",
        data=json.dumps(query),
        headers={"Content-Type": "application/json"},
    )
    if issue_exists:
      self.assertListEqual(
          response.json[0]["Issue"]["ids"],
          expected_ids
      )
    else:
      self.assertListEqual(
          response.json[0]["Issue"]["ids"],
          []
      )

  @ddt.data(
      (("Risk", "Risk"), False, (True, True)),
      (("Risk", "Risk"), True, (True, True)),
      (("Risk", "Control"), False, (True, False)),
      (("Risk", "Control"), True, (True, True)),
      (("Control", "Risk"), False, (False, True)),
      (("Control", "Risk"), True, (False, True)),
      (("Control", "Control"), False, (False, False)),
      (("Control", "Control"), True, (False, True)),
  )
  @ddt.unpack
  def test_asmt_issue_related(self, asmnt_types, asmnt_related, issues_exist):
    """Test Issues related to assessments."""
    # pylint: disable=too-many-locals

    # Test object has to be created before others to produce revision
    obj = factories.RiskFactory()

    with factories.single_commit():
      assessments = []
      for asmnt_type in asmnt_types:
        audit = factories.AuditFactory()
        assessment = factories.AssessmentFactory(
            audit=audit, assessment_type=asmnt_type
        )
        assessments.append(assessment)
        snapshot = factories.SnapshotFactory(
            parent=audit,
            child_id=obj.id,
            child_type=obj.type,
            revision_id=models.Revision.query.filter_by(
                resource_type=obj.type).one().id
        )
        factories.RelationshipFactory(source=audit, destination=assessment)
        factories.RelationshipFactory(source=snapshot, destination=assessment)

      # Create one issue in the last audit linked to snapshot/assessment
      issue = factories.IssueFactory()
      factories.RelationshipFactory(source=audit, destination=issue)
      factories.RelationshipFactory(source=snapshot, destination=issue)
      if asmnt_related:
        factories.RelationshipFactory(source=issue, destination=assessment)

    query = []
    for assessment in assessments:
      query.append({
          "object_name": "Issue",
          "type": "ids",
          "filters": {
              "expression": {
                  "left": {
                      "object_name": "Assessment",
                      "op": {"name": "relevant"},
                      "ids": [assessment.id],
                  },
                  "op": {"name": "OR"},
                  "right": {
                      "object_name": "Assessment",
                      "op": {"name": "similar"},
                      "ids": [assessment.id],
                  },
              },
          },
      })

    expected_ids = [issue.id]
    response = self.client.post(
        "/query",
        data=json.dumps(query),
        headers={"Content-Type": "application/json"},
    )
    for num, data in enumerate(response.json):
      if issues_exist[num]:
        self.assertListEqual(
            data["Issue"]["ids"],
            expected_ids
        )
      else:
        self.assertListEqual(
            data["Issue"]["ids"],
            []
        )
