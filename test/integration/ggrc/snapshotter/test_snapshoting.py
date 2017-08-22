# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Test for snapshoter"""

import collections

import sqlalchemy as sa

from ggrc import db
import ggrc.models as models
from ggrc.snapshotter.rules import Types

from integration.ggrc.models import factories
from integration.ggrc.snapshotter import SnapshotterBaseTestCase
from integration.ggrc.snapshotter import snapshot_identity


class TestSnapshoting(SnapshotterBaseTestCase):
  """Test cases for Snapshoter module"""

  # pylint: disable=invalid-name,protected-access

  def test_snapshot_create(self):
    """Test simple snapshot creation with a simple change"""
    program = self.create_object(models.Program, {
        "title": "Test Program Snapshot 1"
    })
    control = self.create_object(models.Control, {
        "title": "Test Control Snapshot 1"
    })

    self.create_mapping(program, control)

    control = self.refresh_object(control)

    self.api.modify_object(control, {
        "title": "Test Control Snapshot 1 EDIT 1"
    })

    self.create_object(models.Audit, {
        "title": "Snapshotable audit",
        "program": {"id": program.id},
        "status": "Planned",
        "snapshots": {
            "operation": "create"
        }
    })

    audit = db.session.query(models.Audit).filter(
        models.Audit.title == "Snapshotable audit").one()

    snapshot = db.session.query(models.Snapshot).filter(
        models.Snapshot.child_id == control.id,
        models.Snapshot.child_type == "Control",
    )

    self.assertEqual(snapshot.count(), 1)
    self.assertEqual(
        snapshot.first().revision.content["title"],
        "Test Control Snapshot 1 EDIT 1")

    snapshot_revision = db.session.query(
        models.Revision.resource_type,
        models.Revision.resource_id,
        models.Revision._content
    ).filter(
        models.Revision.resource_type == "Snapshot",
        models.Revision.resource_id == snapshot.first().id,
    )

    self.assertEqual(snapshot_revision.count(), 1)
    snapshot_revision_content = snapshot_revision.first()[2]
    self.assertEqual(snapshot_revision_content["child_type"], "Control")
    self.assertEqual(snapshot_revision_content["child_id"], control.id)

    relationship_columns = db.session.query(models.Relationship)
    relationship = relationship_columns.filter(
        models.Relationship.source_type == "Audit",
        models.Relationship.source_id == audit.id,
        models.Relationship.destination_type == "Control",
        models.Relationship.destination_id == control.id
    ).union(
        relationship_columns.filter(
            models.Relationship.source_type == "Control",
            models.Relationship.source_id == control.id,
            models.Relationship.destination_type == "Audit",
            models.Relationship.destination_id == audit.id
        )
    )
    self.assertEqual(relationship.count(), 1)

    relationship_revision = db.session.query(
        models.Revision.resource_type,
        models.Revision.resource_id,
        models.Revision._content,
    ).filter(
        models.Revision.resource_type == "Relationship",
        models.Revision.resource_id == relationship.first().id,
    )
    self.assertEqual(relationship_revision.count(), 1)

  def test_snapshot_update(self):
    """Test snapshot update with a simple change"""
    program = self.create_object(models.Program, {
        "title": "Test Program Snapshot 1"
    })
    control = self.create_object(models.Control, {
        "title": "Test Control Snapshot 1"
    })

    self.create_mapping(program, control)

    control = self.refresh_object(control)

    self.api.modify_object(control, {
        "title": "Test Control Snapshot 1 EDIT 1"
    })

    self.create_audit(program)

    audit = db.session.query(models.Audit).filter(
        models.Audit.title.like("%Snapshotable audit%")).one()

    control_snapshot = db.session.query(models.Snapshot).filter(
        models.Snapshot.child_id == control.id,
        models.Snapshot.child_type == "Control",
        models.Snapshot.parent_type == "Audit",
        models.Snapshot.parent_id == audit.id)

    self.assertEqual(control_snapshot.count(), 1)
    self.assertEqual(control_snapshot.first().revision.content["title"],
                     "Test Control Snapshot 1 EDIT 1")

    # Create a new objective, add it to program and edit control to detect
    # update.
    # Map the objective to the control to check snapshot-to-snapshot mappings.

    objective = self.create_object(models.Objective, {
        "title": "Test Objective Snapshot UNEDITED"
    })
    self.create_mapping(program, objective)
    self.create_mapping(objective, control)

    control = self.refresh_object(control)
    self.api.modify_object(control, {
        "title": "Test Control Snapshot 1 Edit 2 AFTER initial snapshot"
    })

    audit = self.refresh_object(audit)
    # Initiate update operation
    self.api.modify_object(audit, {
        "snapshots": {
            "operation": "upsert"
        }
    })

    objective_snapshot_query = db.session.query(models.Snapshot).filter(
        models.Snapshot.child_type == "Objective",
        models.Snapshot.child_id == objective.id,
        models.Snapshot.parent_type == "Audit",
        models.Snapshot.parent_id == audit.id
    )
    self.assertEqual(objective_snapshot_query.count(), 1)
    objective_snapshot = objective_snapshot_query.first()
    self.assertEqual(
        objective_snapshot.revision.content["title"],
        "Test Objective Snapshot UNEDITED")

    control_snapshot_query = db.session.query(models.Snapshot).filter(
        models.Snapshot.child_type == "Control",
        models.Snapshot.child_id == control.id,
        models.Snapshot.parent_type == "Audit",
        models.Snapshot.parent_id == audit.id
    )
    self.assertEqual(control_snapshot_query.count(), 1)
    control_snapshot = control_snapshot_query.first()
    self.assertEqual(control_snapshot.revision.content["title"],
                     "Test Control Snapshot 1 Edit 2 AFTER initial snapshot")

    snapshot_mapping = db.session.query(models.Relationship).filter(
        models.Relationship.source_type == "Snapshot",
        models.Relationship.destination_type == "Snapshot",
        sa.or_(
            sa.and_(
                models.Relationship.source_id == control_snapshot.id,
                models.Relationship.destination_id == objective_snapshot.id,
            ),
            sa.and_(
                models.Relationship.source_id == objective_snapshot.id,
                models.Relationship.destination_id == control_snapshot.id,
            ),
        ),
    )
    self.assertEqual(snapshot_mapping.count(), 1)

    control_revisions = db.session.query(models.Revision).filter(
        models.Revision.resource_type == control.type,
        models.Revision.resource_id == control.id)
    # 1 revisions are from the initial creation (as control is not
    # ownable now), and 2 are from edits.
    self.assertEqual(control_revisions.count(), 3)

    self.assertEqual(
        control_revisions.order_by(models.Revision.id.desc()).first().id,
        control_snapshot.revision_id,
    )

  def test_update_to_specific_version(self):
    """Test global update and selecting a specific revision for one object"""
    program = self.create_object(models.Program, {
        "title": "Test Program Snapshot 1"
    })
    control = self.create_object(models.Control, {
        "title": "Test Control Snapshot 1"
    })

    objective = self.create_object(models.Objective, {
        "title": "Test Objective Snapshot 1"
    })

    self.create_mapping(program, control)
    self.create_mapping(program, objective)

    control = self.refresh_object(control)
    for x in xrange(1, 4):
      self.api.modify_object(control, {
          "title": "Test Control Snapshot 1 EDIT {}".format(x)
      })

    self.create_object(models.Audit, {
        "title": "Snapshotable audit",
        "program": {"id": program.id},
        "status": "Planned",
        "snapshots": {
            "operation": "create"
        }
    })

    audit = db.session.query(models.Audit).filter(
        models.Audit.title.like("%Snapshotable audit%")).one()

    revision = db.session.query(
        models.Revision.id,
        models.Revision.resource_type,
        models.Revision.resource_id,
        models.Revision._content,
    ).filter(
        models.Revision.resource_type == control.type,
        models.Revision.resource_id == control.id,
        models.Revision._content.like("%Test Control Snapshot 1 EDIT 2%"),
    ).one()

    audit = self.refresh_object(audit)
    self.api.modify_object(audit, {
        "snapshots": {
            "operation": "upsert",
            "revisions": [{
                "parent": self.objgen.create_stub(audit),
                "child": self.objgen.create_stub(control),
                "revision_id": revision[0]
            }]
        }
    })

    control_snapshot = db.session.query(models.Snapshot).filter(
        models.Snapshot.child_type == control.type,
        models.Snapshot.child_id == control.id,
        models.Snapshot.parent_type == "Audit",
        models.Snapshot.parent_id == audit.id
    )
    self.assertEqual(control_snapshot.count(), 1)
    self.assertEqual(control_snapshot.first().revision.content["title"],
                     "Test Control Snapshot 1 EDIT 2")

  def test_snapshot_update_after_CA_value_changed(self):
    """Test update of a snapshot after CA value changed

    1. Create program with mapped control.
    2. Create audit, verify there is a snapshot for control
    3. Update control's CA value
    4. Run refresh on control's snapshot object
    5. Verify control's CA is changed
    """
    program = self.create_object(models.Program, {
        "title": "Test Program Snapshot 1"
    })
    control = self.create_object(models.Control, {
        "title": "Test Control Snapshot 1"
    })
    custom_attribute_defs = self.create_custom_attribute_definitions()
    cav = {
        "custom_attribute": custom_attribute_defs["control"],
        "attributable": control,
        "attribute_value": "CA value 1",
    }
    factories.CustomAttributeValueFactory(**cav)
    self.create_mapping(program, control)
    control = self.refresh_object(control)
    self.create_audit(program)
    audit = db.session.query(models.Audit).filter(
        models.Audit.title.like("%Snapshotable audit%")).one()
    self.assertEqual(
        db.session.query(models.Snapshot).filter(
            models.Snapshot.parent_type == "Audit",
            models.Snapshot.parent_id == audit.id
        ).count(), 1)
    control = self.refresh_object(control)
    cad2 = models.CustomAttributeDefinition.query.filter(
        models.CustomAttributeDefinition.title == "control text field 1"
    ).one()
    val2 = models.CustomAttributeValue(attribute_value="CA value 1",
                                       custom_attribute=cad2)
    self.api.modify_object(control, {
        "custom_attribute_values": [{
            "attributable_id": control.id,
            "attributable_type": "Assessment",
            "id": val2.id,
            "custom_attribute_id": cad2.id,
            "attribute_value": "CA value 1 EDIT 1",
        }]
    })
    control_snapshot = db.session.query(models.Snapshot).filter(
        models.Snapshot.child_type == "Control",
        models.Snapshot.child_id == control.id
    ).first()
    cav = control_snapshot.revision.content["custom_attribute_values"][0]
    self.assertEqual(cav["attribute_value"], "CA value 1")

    self.api.modify_object(control_snapshot, {"update_revision": "latest"})

    expected = [
        (control, "CA value 1 EDIT 1"),
    ]
    for obj, expected_title in expected:
      snapshot = db.session.query(models.Snapshot).filter(
          models.Snapshot.child_type == obj.__class__.__name__,
          models.Snapshot.child_id == obj.id
      ).first()
      cav = snapshot.revision.content["custom_attribute_values"][0]
      self.assertEquals(cav["attribute_value"], expected_title)

    control_snapshot_revisions = db.session.query(models.Revision).filter(
        models.Revision.resource_type == "Snapshot",
        models.Revision.resource_id == control_snapshot.id
    )
    self.assertEqual(control_snapshot_revisions.count(), 2)

  def test_creation_of_snapshots_for_multiple_parent_objects(self):
    pass

  def test_individual_update(self):
    """Test update of individual snapshot

    1. Create program with mapped control and data asset.
    2. Create audit, verify there are snapshot for control and data asset
    3. Update control and data asset title
    4. Run refresh on control's snapshot object
    5. Verify control's title is changed and data assets NOT
    """

    program = self.create_object(models.Program, {
        "title": "Test Program Snapshot 1"
    })

    control = self.create_object(models.Control, {
        "title": "Test Control Snapshot 1"
    })
    data_asset = self.create_object(models.DataAsset, {
        "title": "Test DataAsset Snapshot 1"
    })

    self.create_mapping(program, control)
    self.create_mapping(program, data_asset)

    control = self.refresh_object(control)
    data_asset = self.refresh_object(data_asset)

    self.create_audit(program)

    audit = db.session.query(models.Audit).filter(
        models.Audit.title.like("%Snapshotable audit%")).one()

    self.assertEqual(
        db.session.query(models.Snapshot).filter(
            models.Snapshot.parent_type == "Audit",
            models.Snapshot.parent_id == audit.id).count(),
        2)

    control = self.refresh_object(control)
    self.api.modify_object(control, {
        "title": "Test Control Snapshot 1 EDIT 1"
    })

    data_asset = self.refresh_object(data_asset)
    self.api.modify_object(data_asset, {
        "title": "Test Data Asset Snapshot 1 EDIT 1"
    })

    control_snapshot = db.session.query(models.Snapshot).filter(
        models.Snapshot.child_type == "Control",
        models.Snapshot.child_id == control.id).first()

    self.assertEqual(
        control_snapshot.revision.content["title"],
        "Test Control Snapshot 1")

    self.api.modify_object(control_snapshot, {
        "update_revision": "latest"
    })

    expected = [
        (control, "Test Control Snapshot 1 EDIT 1"),
        (data_asset, "Test DataAsset Snapshot 1"),
    ]
    for obj, expected_title in expected:
      snapshot = db.session.query(models.Snapshot).filter(
          models.Snapshot.child_type == obj.__class__.__name__,
          models.Snapshot.child_id == obj.id).first()
      self.assertEquals(
          snapshot.revision.content["title"],
          expected_title)

    control_snapshot_event = db.session.query(models.Event).filter(
        models.Event.resource_type == "Snapshot",
        models.Event.resource_id == control_snapshot.id,
        models.Event.action == "PUT"
    )
    self.assertEqual(control_snapshot_event.count(), 1)

    control_snapshot_revisions = db.session.query(models.Revision).filter(
        models.Revision.resource_type == "Snapshot",
        models.Revision.resource_id == control_snapshot.id
    )
    self.assertEqual(control_snapshot_revisions.count(), 2)

  def test_snapshot_put_operation(self):
    """Test that performing PUT operation on snapshot does not change any values
    """

    program = self.create_object(models.Program, {
        "title": "Test Program Snapshot 1"
    })

    control = self.create_object(models.Control, {
        "title": "Test Control Snapshot 1"
    })

    self.create_mapping(program, control)

    control = self.refresh_object(control)

    self.create_audit(program)

    control = self.refresh_object(control)
    self.api.modify_object(control, {
        "title": "Test Control Snapshot 1 EDIT 1"
    })

    control_snapshot = db.session.query(models.Snapshot).filter(
        models.Snapshot.child_type == "Control",
        models.Snapshot.child_id == control.id).first()

    self.assertEqual(
        control_snapshot.revision.content["title"],
        "Test Control Snapshot 1")

    audit = db.session.query(models.Audit).filter(
        models.Audit.title.like("%Snapshotable audit%")).one()

    update_data = {
        "parent_id": audit.id + 123,
        "parent_type": "DataAsset",
        "child_id": control_snapshot.id + 123,
        "child_type": "Regulation",
        "revision_id": control_snapshot.revision_id + 123,
    }
    self.api.modify_object(control_snapshot, update_data)

    control_snapshot_updated = db.session.query(models.Snapshot).filter(
        models.Snapshot.child_type == control.__class__.__name__,
        models.Snapshot.child_id == control.id).one()

    for field in update_data.keys():
      self.assertEqual(
          getattr(control_snapshot, field),
          getattr(control_snapshot_updated, field)
      )

  def test_update_when_mapped_objects_are_deleted(self):
    """Test global update when object got deleted or unmapped"""
    pass

  def test_snapshoting_of_objects(self):
    """Test that all object types that should be snapshotted are snapshotted

    It is expected that all objects will be triplets.
    """

    self._import_file("snapshotter_create.csv")

    # Verify that all objects got imported correctly.
    for _type in Types.all:
      self.assertEqual(
          db.session.query(getattr(models.all_models, _type)).count(),
          3)

    program = db.session.query(models.Program).filter(
        models.Program.slug == "Prog-13211"
    ).one()

    self.create_audit(program)

    audit = db.session.query(models.Audit).filter(
        models.Audit.title.like("%Snapshotable audit%")).first()

    snapshots = db.session.query(models.Snapshot).filter(
        models.Snapshot.parent_type == "Audit",
        models.Snapshot.parent_id == audit.id,
    )

    self.assertEqual(snapshots.count(), len(Types.all) * 3)

    type_count = collections.defaultdict(int)
    for snapshot in snapshots:
      type_count[snapshot.child_type] += 1

    missing_types = set()
    for snapshottable_type in Types.all:
      if type_count[snapshottable_type] != 3:
        missing_types.add(snapshottable_type)

    self.assertEqual(missing_types, set())

  def test_snapshot_update_is_idempotent(self):
    """Test that nothing has changed if there's nothing to update"""
    self._import_file("snapshotter_create.csv")

    program = db.session.query(models.Program).filter(
        models.Program.slug == "Prog-13211"
    ).one()

    self.create_audit(program)

    audit = db.session.query(models.Audit).filter(
        models.Audit.title == "Snapshotable audit").one()

    snapshots = db.session.query(models.Snapshot).filter(
        models.Snapshot.parent_type == "Audit",
        models.Snapshot.parent_id == audit.id,
    )

    self.assertEqual(snapshots.count(), len(Types.all) * 3)

    audit = self.refresh_object(audit)
    self.api.modify_object(audit, {
        "snapshots": {
            "operation": "upsert"
        }
    })

    old_snapshots = {s.id: s for s in snapshots}

    snapshots = db.session.query(models.Snapshot).filter(
        models.Snapshot.parent_type == "Audit",
        models.Snapshot.parent_id == audit.id,
    )

    new_snapshots = {s.id: s for s in snapshots}

    for _id, snapshot in new_snapshots.items():
      self.assertEqual(snapshot_identity(old_snapshots[_id], snapshot), True)

  def test_audit_creation_if_nothing_in_program_scope(self):
    """Test audit creation if there's nothing in prog scope"""
    program_title = "empty program"
    audit_title = "Audit for empty program"

    self.create_object(models.Program, {
        "title": program_title,
    })

    program = db.session.query(models.Program).filter(
        models.Program.title == "empty program"
    ).one()

    self.create_object(models.Audit, {
        "title": "Audit for empty program",
        "program": {"id": program.id},
        "status": "Planned",
        "snapshots": {
            "operation": "create",
        }
    })

    audit = db.session.query(models.Audit).filter(
        models.Audit.title == audit_title).one()

    self.assertEqual(
        db.session.query(models.Audit).filter(
            models.Audit.title == audit_title).count(), 1)

    snapshots = db.session.query(models.Snapshot).filter(
        models.Snapshot.parent_type == "Audit",
        models.Snapshot.parent_id == audit.id,
    )

    self.assertEqual(snapshots.count(), 0)

  def test_snapshot_post_api(self):
    """Test snapshot creation when object is in program scope already"""
    program = self.create_object(models.Program, {
        "title": "Test Program Snapshot 1"
    })
    program2 = self.create_object(models.Program, {
        "title": "Test Program Snapshot 2"
    })

    control = self.create_object(models.Control, {
        "title": "Test Control Snapshot 1"
    })

    self.create_audit(program, title="Audit1")
    self.create_audit(program2, title="Audit2")

    objective = self.create_object(models.Objective, {
        "title": "Test Objective Snapshot UNEDITED"
    })
    self.create_mapping(objective, program)
    self.create_mapping(program2, objective)  # different direction than above

    audit = db.session.query(models.Audit).filter(
        models.Audit.program_id == program.id).one()
    audit2 = db.session.query(models.Audit).filter(
        models.Audit.program_id == program2.id).one()

    self.api.post(models.Snapshot, [
        {
            "snapshot": {
                "parent": {
                    "id": audit.id,
                    "type": "Audit",
                    "href": "/api/audits/{}".format(audit.id)
                },
                "child_type": "Objective",
                "child_id": objective.id,
                "update_revision": "new",
                "context": {
                    "id": audit.context_id,
                    "type": "Context",
                    "href": "/api/contexts/{}".format(audit.context_id)
                }
            }
        },
        {
            "snapshot": {
                "parent": {
                    "id": audit.id,
                    "type": "Audit",
                    "href": "/api/audits/{}".format(audit.id)
                },
                "child_type": "Control",
                "child_id": control.id,
                "update_revision": "new",
                "context": {
                    "id": audit.context_id,
                    "type": "Context",
                    "href": "/api/contexts/{}".format(audit.context_id)
                }
            }
        },
        {
            "snapshot": {
                "parent": {
                    "id": audit2.id,
                    "type": "Audit",
                    "href": "/api/audits/{}".format(audit2.id)
                },
                "child_type": "Control",
                "child_id": control.id,
                "update_revision": "new",
                "context": {
                    "id": audit2.context_id,
                    "type": "Context",
                    "href": "/api/contexts/{}".format(audit2.context_id)
                }
            }
        },
        {
            "snapshot": {
                "parent": {
                    "id": audit2.id,
                    "type": "Audit",
                    "href": "/api/audits/{}".format(audit2.id)
                },
                "child_type": "Objective",
                "child_id": objective.id,
                "update_revision": "new",
                "context": {
                    "id": audit2.context_id,
                    "type": "Context",
                    "href": "/api/contexts/{}".format(audit2.context_id)
                }
            }
        }
    ])

    objective_snapshot = db.session.query(models.Snapshot).filter(
        models.Snapshot.child_type == "Objective",
        models.Snapshot.child_id == objective.id
    )

    objective_revision = db.session.query(models.Revision).filter(
        models.Revision.resource_type == "Objective",
        models.Revision.resource_id == objective.id
    ).all()[-1]

    self.assertEquals(objective_snapshot.count(), 2)
    self.assertEquals(objective_snapshot.first().revision_id,
                      objective_revision.id)

    control_snapshots = db.session.query(models.Snapshot).filter(
        models.Snapshot.child_type == "Control",
        models.Snapshot.child_id == control.id,
    )
    control_revision = db.session.query(models.Revision).filter(
        models.Revision.resource_type == "Control",
        models.Revision.resource_id == control.id,
    ).all()[-1]

    self.assertEquals(control_snapshots.count(), 2)
    self.assertSetEqual({s.revision_id for s in control_snapshots},
                        {control_revision.id})

    def _assert_exactly_one_relationship(src, dst):
      """Assert only one of Rel(src, dst) and Rel(dst, src) exists."""
      rels = db.session.query(models.Relationship).filter(
          models.Relationship.source_id == src.id,
          models.Relationship.source_type == src.type,
          models.Relationship.destination_id == dst.id,
          models.Relationship.destination_type == dst.type,
      ).union_all(db.session.query(models.Relationship).filter(
          models.Relationship.destination_id == src.id,
          models.Relationship.destination_type == src.type,
          models.Relationship.source_id == dst.id,
          models.Relationship.source_type == dst.type,
      ))
      self.assertEqual(rels.count(), 1)

    _assert_exactly_one_relationship(program, objective)
    _assert_exactly_one_relationship(program, control)
    _assert_exactly_one_relationship(program2, objective)
    _assert_exactly_one_relationship(program2, control)

  def test_relationship_post_api(self):
    """Test snapshot creation when creating relationships to Audit"""
    program = self.create_object(models.Program, {
        "title": "Test Program Snapshot 1"
    })

    control = self.create_object(models.Control, {
        "title": "Test Control Snapshot 1"
    })

    self.create_audit(program)

    objective = self.create_object(models.Objective, {
        "title": "Test Objective Snapshot UNEDITED"
    })
    self.create_mapping(program, objective)

    audit = db.session.query(models.Audit).filter(
        models.Audit.title.like("%Snapshotable audit%")).one()

    self.create_mapping(audit, objective)
    self.create_mapping(control, audit)  # different direction than above

    objective_snapshot = db.session.query(models.Snapshot).filter(
        models.Snapshot.child_type == "Objective",
        models.Snapshot.child_id == objective.id
    )

    objective_revision = db.session.query(models.Revision).filter(
        models.Revision.resource_type == "Objective",
        models.Revision.resource_id == objective.id
    ).all()[-1]

    self.assertEquals(objective_snapshot.count(), 1)
    self.assertEquals(objective_snapshot.first().revision_id,
                      objective_revision.id)

    self.assertIsNotNone(models.Relationship.find_related(program, objective))
    self.assertIsNotNone(models.Relationship.find_related(program, control))
