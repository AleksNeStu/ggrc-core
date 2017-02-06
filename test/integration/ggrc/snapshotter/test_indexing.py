# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Test for indexing of snapshotted objects"""

from sqlalchemy.sql.expression import tuple_

from ggrc import db
from ggrc import models
from ggrc.views import do_reindex
from ggrc.fulltext.mysql import MysqlRecordProperty as Record
from ggrc.snapshotter.indexer import delete_records

from integration.ggrc.snapshotter import SnapshotterBaseTestCase
from integration.ggrc.models import factories


def get_records(_audit, _snapshots):
  return db.session.query(Record).filter(
      tuple_(
          Record.type,
          Record.key,
          Record.property,
          Record.content
      ).in_(
          {("Snapshot", s.id, "parent", "Audit-{}".format(_audit.id))
           for s in _snapshots}
      ))


class TestSnapshotIndexing(SnapshotterBaseTestCase):
  """Test cases for Snapshoter module"""

  # pylint: disable=invalid-name,too-many-locals

  def setUp(self):
    super(TestSnapshotIndexing, self).setUp()

    self.client.get("/login")
    self.headers = {
        'Content-Type': 'application/json',
        "X-Requested-By": "GGRC",
    }

  def test_create_indexing(self):
    """Test that creating objects results in full index"""
    custom_attribute_defs = self.create_custom_attribute_definitions()

    self._import_file("snapshotter_create.csv")

    control = db.session.query(models.Control).filter(
        models.Control.slug == "control-3"
    ).one()
    access_group = db.session.query(models.AccessGroup).filter(
        models.AccessGroup.slug == "ag-2"
    ).one()
    objective = db.session.query(models.Objective).filter(
        models.Objective.slug == "obj-1"
    ).one()
    process = db.session.query(models.Process).filter(
        models.Process.slug == "proc-2"
    ).one()
    custom_attribute_values = [
        {
            "custom_attribute": custom_attribute_defs["control"],
            "attributable": control,
            "attribute_value": "control value 1",
        },
        {
            "custom_attribute": custom_attribute_defs["objective"],
            "attributable": objective,
            "attribute_value": "objective value 1",
        },
        {
            "custom_attribute": custom_attribute_defs["process"],
            "attributable": process,
            "attribute_value": "07/12/2016",
        },
        {
            "custom_attribute": custom_attribute_defs["access_group"],
            "attributable": access_group,
            "attribute_value": "access_group text value 1",
        },
    ]

    for value in custom_attribute_values:
      factories.CustomAttributeValueFactory(**value)

    # Add custom attribute values via factory doesn't create revisions, so
    # we modify all the objects via import, which saves the full object
    # state in revisions table (including custom attribute values).
    self._import_file("snapshotter_update.csv")

    program = db.session.query(models.Program).filter(
        models.Program.slug == "Prog-13211"
    ).one()

    self.create_audit(program)

    audit = db.session.query(models.Audit).filter(
        models.Audit.title.like("%Snapshotable audit%")).first()

    snapshots = db.session.query(models.Snapshot).all()

    records = db.session.query(Record).filter(
        tuple_(
            Record.type,
            Record.key,
            Record.property,
            Record.content
        ).in_(
            {("Snapshot", s.id, "parent", "Audit-{}".format(audit.id))
             for s in snapshots}
        ))

    self.assertEqual(records.count(), 57)

    # At this point all objects are no longer in the session and we have to
    # manually refresh them from the database
    control = db.session.query(models.Control).filter(
        models.Control.slug == "control-3"
    ).one()
    access_group = db.session.query(models.AccessGroup).filter(
        models.AccessGroup.slug == "ag-2"
    ).one()
    objective = db.session.query(models.Objective).filter(
        models.Objective.slug == "obj-1"
    ).one()
    process = db.session.query(models.Process).filter(
        models.Process.slug == "proc-2"
    ).one()

    custom_attributes = [
        (control, "control text field 1", "control value 1"),
        (objective, "objective rich field 1", "objective value 1"),
        (process, "process date field 1", "07/12/2016"),
        (access_group, "access group text field 2",
         "access_group text value 1")
    ]

    for obj, definition, value in custom_attributes:
      snapshot = db.session.query(models.Snapshot).filter(
          models.Snapshot.child_type == obj.type,
          models.Snapshot.child_id == obj.id,
      ).one()

      _cav = db.session.query(Record).filter(
          Record.key == snapshot.id,
          Record.type == "Snapshot",
          Record.property == definition,
          Record.content == value
      )
      _title = db.session.query(Record).filter(
          Record.key == snapshot.id,
          Record.type == "Snapshot",
          Record.property == "title",
          Record.content == obj.title
      )
      _desc = db.session.query(Record).filter(
          Record.key == snapshot.id,
          Record.type == "Snapshot",
          Record.property == "description",
          Record.content == obj.description
      )
      self.assertEqual(_cav.count(), 1)
      self.assertEqual(_title.count(), 1)
      self.assertEqual(_desc.count(), 1)

  def test_update_indexing(self):
    """Test that creating objects results in full index"""
    custom_attribute_defs = self.create_custom_attribute_definitions()

    self._import_file("snapshotter_create.csv")

    access_group = db.session.query(models.AccessGroup).filter(
        models.AccessGroup.title == "ag-2"
    ).one()
    objective = db.session.query(models.Objective).filter(
        models.Objective.title == "obj-1"
    ).one()
    custom_attribute_values = [
        {
            "custom_attribute": custom_attribute_defs["objective"],
            "attributable": objective,
            "attribute_value": "objective value 1",
        },
        {
            "custom_attribute": custom_attribute_defs["access_group"],
            "attributable": access_group,
            "attribute_value": "access_group text value 1",
        },
    ]

    for value in custom_attribute_values:
      factories.CustomAttributeValueFactory(**value)

    # Add custom attribute values via factory doesn't create revisions, so
    # we modify all the objects via import, which saves the full object
    # state in revisions table (including custom attribute values).
    self._import_file("snapshotter_update.csv")

    program = db.session.query(models.Program).filter(
        models.Program.slug == "Prog-13211"
    ).one()

    self.create_audit(program)

    objective_cav = db.session.query(models.CustomAttributeValue).filter(
        models.CustomAttributeValue.attribute_value == "objective value 1"
    ).one()

    access_group_cav = db.session.query(models.CustomAttributeValue).filter(
        models.CustomAttributeValue.attribute_value ==
        "access_group text value 1"
    ).one()

    cavs = [
        (objective_cav, "objective CA value edited after initial index"),
        (access_group_cav, "access_group CA value edited after initial index"),
    ]

    # This is not a correct way to update CAVs but PUT request on CAV
    # doesn't work and attaching full custom attribute signature
    # (custom_attribute_definitions, custom_attribute_values and
    # custom_attributes) is out of scope for this.
    for obj, val in cavs:
      obj.attribute_value = val
      db.session.add(obj)
    db.session.commit()

    access_group = db.session.query(models.AccessGroup).filter(
        models.AccessGroup.slug == "ag-2"
    ).one()
    objective = db.session.query(models.Objective).filter(
        models.Objective.slug == "obj-1"
    ).one()

    obj_edits = [
        (objective, "objective title edited after initial index"),
        (access_group, "access group title edited after initial index")
    ]

    for obj, title in obj_edits:
      obj = self.refresh_object(obj)
      self.api.modify_object(obj, {
          "title": title
      })

    audit = db.session.query(models.Audit).filter(
        models.Audit.title.like("%Snapshotable audit%")).one()
    # Initiate update operation
    self.api.modify_object(audit, {
        "snapshots": {
            "operation": "upsert"
        }
    })

    snapshots = db.session.query(models.Snapshot).all()

    records = db.session.query(Record).filter(
        tuple_(
            Record.type,
            Record.key,
            Record.property,
            Record.content
        ).in_(
            {("Snapshot", s.id, "parent", "Audit-{}".format(s.parent_id))
             for s in snapshots}
        ))

    self.assertEqual(records.count(), 57)

    custom_attributes = [
        (objective,
         "objective title edited after initial index",
         "objective rich field 1",
         "objective CA value edited after initial index"),
        (access_group,
         "access group title edited after initial index",
         "access group text field 2",
         "access_group CA value edited after initial index")
    ]

    for obj, title, definition, value in custom_attributes:
      obj = self.refresh_object(obj)
      snapshot = db.session.query(models.Snapshot).filter(
          models.Snapshot.child_type == obj.type,
          models.Snapshot.child_id == obj.id,
      ).one()

      _cav = db.session.query(Record).filter(
          Record.key == snapshot.id,
          Record.type == "Snapshot",
          Record.property == definition,
          Record.content == value
      )
      _title = db.session.query(Record).filter(
          Record.key == snapshot.id,
          Record.type == "Snapshot",
          Record.property == "title",
          Record.content == title
      )
      _desc = db.session.query(Record).filter(
          Record.key == snapshot.id,
          Record.type == "Snapshot",
          Record.property == "description",
          Record.content == obj.description
      )
      self.assertEqual(_cav.count(), 1)
      self.assertEqual(_title.count(), 1)
      self.assertEqual(_desc.count(), 1)

  def test_full_reindex(self):
    """Test full reindex of all snapshots"""
    self._import_file("snapshotter_create.csv")

    program = db.session.query(models.Program).filter(
        models.Program.slug == "Prog-13211"
    ).one()

    self.create_audit(program)

    audit = db.session.query(models.Audit).filter(
        models.Audit.title.like("%Snapshotable audit%")).first()

    snapshots = db.session.query(models.Snapshot).all()

    records = get_records(audit, snapshots)

    self.assertEqual(records.count(), 57)

    delete_records({s.id for s in snapshots})

    records = get_records(audit, snapshots)
    self.assertEqual(records.count(), 0)

    do_reindex()

    records = get_records(audit, snapshots)

    self.assertEqual(records.count(), 57)
