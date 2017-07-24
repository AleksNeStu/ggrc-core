# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Integration tests for WithLastAssessmentDate logic."""

import datetime
from operator import itemgetter

import freezegun

from ggrc import db
from ggrc.models import all_models
from ggrc.data_platform import computed_attributes

from integration.ggrc import TestCase
from integration.ggrc.api_helper import Api
from integration.ggrc.query_helper import WithQueryApi
import integration.ggrc.generator
from integration.ggrc.models import factories


class TestWithLastAssessmentDate(TestCase, WithQueryApi):
  """Integration test suite for WithLastAssessmentDate functionality."""

  def setUp(self):
    self.clear_data()
    super(TestWithLastAssessmentDate, self).setUp()
    self.generator = integration.ggrc.generator.ObjectGenerator()
    self.client.get("/login")
    self.api = Api()

    program = factories.ProgramFactory(title="Last Assessment Date")

    controls = [factories.ControlFactory() for _ in range(3)]
    self.control_ids = [c.id for c in controls]
    for control in controls:
      factories.RelationshipFactory(source=program, destination=control)
    objectives = [factories.ObjectiveFactory() for _ in range(3)]
    self.objective_ids = [c.id for c in objectives]
    for objective in objectives:
      factories.RelationshipFactory(source=program, destination=objective)

    self._create_audit(program=program, title="Last Assessment Date Audit")

    c_snapshots = (db.session.query(all_models.Snapshot)
                   .filter_by(child_type="Control").all())
    o_snapshots = (db.session.query(all_models.Snapshot)
                   .filter_by(child_type="Objective").all())
    c_id_to_snap_id = {s.child_id: s.id for s in c_snapshots}
    o_id_to_snap_id = {s.child_id: s.id for s in o_snapshots}

    assessments = [factories.AssessmentFactory() for _ in range(3)]
    self.assessment_ids = [a.id for a in assessments]

    # Mappings:
    # controls[0]: assessments[0], assessments[1], assessments[2],
    # controls[1]: assessments[1], assessments[2],
    # controls[2]: assessments[2]
    # objectives[0]: assessments[0],
    # objectives[1]: assessments[0], assessments[1],
    # objectives[2]: assessments[0], assessments[1], assessments[2],

    # the first Assessment is completed earlier than the second, the third
    # Assessment is not completed.

    self._create_relationships(
        (c_id_to_snap_id[self.control_ids[0]], assessments[0]),
        (c_id_to_snap_id[self.control_ids[0]], assessments[1]),
        (c_id_to_snap_id[self.control_ids[0]], assessments[2]),
        (c_id_to_snap_id[self.control_ids[1]], assessments[1]),
        (c_id_to_snap_id[self.control_ids[1]], assessments[2]),
        (c_id_to_snap_id[self.control_ids[2]], assessments[2]),
        (o_id_to_snap_id[self.objective_ids[2]], assessments[0]),
        (o_id_to_snap_id[self.objective_ids[2]], assessments[1]),
        (o_id_to_snap_id[self.objective_ids[2]], assessments[2]),
        (o_id_to_snap_id[self.objective_ids[1]], assessments[0]),
        (o_id_to_snap_id[self.objective_ids[1]], assessments[1]),
        (o_id_to_snap_id[self.objective_ids[0]], assessments[0]),
    )

    self.finished_dates = [datetime.datetime(2017, 2, 20, 13, 40, 0),
                           datetime.datetime(2017, 3, 30, 14, 55, 0)]

    with freezegun.freeze_time(self.finished_dates[0]):
      assessments[0].status = all_models.Assessment.FINAL_STATE
      db.session.add(assessments[0])
    with freezegun.freeze_time(self.finished_dates[1]):
      assessments[1].status = all_models.Assessment.FINAL_STATE
      db.session.add(assessments[1])
    db.session.commit()

    query = all_models.Revision.query.filter_by(resource_type="Assessment")
    revision_ids = [revision.id for revision in query]
    computed_attributes.compute_attributes(revision_ids)

  def _create_audit(self, program, title):
    """Make a POST to create an Audit.

    AuditFactory doesn't trigger Snapshotter
    """
    _, audit = self.generator.generate_object(all_models.Audit, {
        "title": title,
        "program": {"id": program.id},
        "status": "Planned",
        "snapshots": {
            "operation": "create",
        }
    })

    return audit

  @staticmethod
  def _create_relationships(*assessment_rels):
    """Create mappings for pairs of Snapshot and Assessment passed by id."""
    for snapshot_id, assessment in assessment_rels:
      factories.RelationshipFactory(source=assessment,
                                    destination_type="Snapshot",
                                    destination_id=snapshot_id)

  def test_last_asmt_date_values(self):
    """Last Assessment Date contains correct value for original object."""
    controls = self._get_first_result_set(self._make_query_dict("Control"),
                                          "Control", "values")
    controls_last_asmt_dates = {c["id"]: c["last_assessment_date"]
                                for c in controls}
    self.assertDictEqual(
        controls_last_asmt_dates,
        {self.control_ids[0]: self.finished_dates[1].isoformat(),
         self.control_ids[1]: self.finished_dates[1].isoformat(),
         self.control_ids[2]: None})

    objectives = self._get_first_result_set(self._make_query_dict("Objective"),
                                            "Objective", "values")
    objectives_last_asmt_dates = {c["id"]: c["last_assessment_date"]
                                  for c in objectives}
    self.assertDictEqual(
        objectives_last_asmt_dates,
        {self.objective_ids[0]: self.finished_dates[0].isoformat(),
         self.objective_ids[1]: self.finished_dates[1].isoformat(),
         self.objective_ids[2]: self.finished_dates[1].isoformat()})

  def test_last_asmt_date_filter(self):
    """Last Assessment Date is searchable."""
    controls_result = self._get_first_result_set(
        self._make_query_dict("Control",
                              expression=("Last Assessment Date",
                                          "=",
                                          str(self.finished_dates[1].date()))),
        "Control",
    )
    self.assertEqual(controls_result["count"], 2)
    self.assertSetEqual({c["id"] for c in controls_result["values"]},
                        {self.control_ids[0], self.control_ids[1]})
    objectives_result = self._get_first_result_set(
        self._make_query_dict("Objective",
                              expression=("Last Assessment Date",
                                          "=",
                                          str(self.finished_dates[0].date()))),
        "Objective",
    )
    self.assertEqual(objectives_result["count"], 1)
    self.assertSetEqual({c["id"] for c in objectives_result["values"]},
                        {self.objective_ids[0]})

  def test_last_asmt_date_order(self):
    """Last Assessment Date is sortable."""
    controls = self._get_first_result_set(
        self._make_query_dict("Control",
                              order_by=[{"name": "Last Assessment Date"},
                                        {"name": "id"}]),
        "Control", "values",
    )
    controls_unsorted = self._get_first_result_set(
        self._make_query_dict("Control"),
        "Control", "values",
    )
    controls_sorted_manually = sorted(
        sorted(controls_unsorted,
               key=itemgetter("id")),
        key=itemgetter("last_assessment_date"),
    )
    self.assertListEqual([c["id"] for c in controls],
                         [c["id"] for c in controls_sorted_manually])

    objectives = self._get_first_result_set(
        self._make_query_dict("Objective",
                              order_by=[{"name": "Last Assessment Date"},
                                        {"name": "id"}]),
        "Objective", "values",
    )
    objectives_unsorted = self._get_first_result_set(
        self._make_query_dict("Objective"),
        "Objective", "values",
    )
    objectives_sorted_manually = sorted(
        sorted(objectives_unsorted,
               key=itemgetter("id")),
        key=itemgetter("last_assessment_date"),
    )
    self.assertListEqual([c["id"] for c in objectives],
                         [c["id"] for c in objectives_sorted_manually])
