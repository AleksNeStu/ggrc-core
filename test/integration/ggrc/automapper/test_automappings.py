# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Test automappings"""

import itertools
from contextlib import contextmanager

import ggrc
from ggrc import automapper
from ggrc import models
from ggrc.models import all_models
from ggrc.models import Automapping
from integration.ggrc import TestCase
from integration.ggrc import generator
from integration.ggrc.models import factories
from integration.ggrc.models.factories import random_str


def make_name(msg):
  """Make name helper function"""
  return random_str(prefix=msg)


@contextmanager
def automapping_count_limit(new_limit):
  """Automapping count limit"""
  original_limit = ggrc.automapper.AutomapperGenerator.COUNT_LIMIT
  ggrc.automapper.AutomapperGenerator.COUNT_LIMIT = new_limit
  yield
  ggrc.automapper.AutomapperGenerator.COUNT_LIMIT = original_limit


class TestAutomappings(TestCase):
  """Test automappings"""
  def setUp(self):
    super(TestAutomappings, self).setUp()
    self.gen = generator.ObjectGenerator()
    self.api = self.gen.api

  @classmethod
  def create_ac_roles(cls, obj, person_id):
    """Create access control roles"""
    ac_role = models.AccessControlRole.query.filter_by(
        object_type=obj.type,
        name="Admin"
    ).first()
    factories.AccessControlListFactory(
        ac_role=ac_role,
        object=obj,
        person_id=person_id
    )

  def create_object(self, cls, data):
    """Helper function for creating an object"""
    name = cls._inflector.table_singular
    data['context'] = None
    res, obj = self.gen.generate(cls, name, {name: data})
    self.assertIsNotNone(obj, '%s, %s: %s' % (name, str(data), str(res)))
    return obj

  def create_mapping(self, src, dst):
    """Helper function for creating mappings"""
    return self.gen.generate_relationship(src, dst)[1]

  def assert_mapping(self, obj1, obj2, missing=False):
    """Helper function for asserting mappings"""
    ggrc.db.session.flush()
    rel = models.Relationship.find_related(obj1, obj2)
    if not missing:
      self.assertIsNotNone(rel,
                           msg='%s not mapped to %s' % (obj1.type, obj2.type))
      revisions = models.Revision.query.filter_by(
          resource_type='Relationship',
          resource_id=rel.id,
      ).count()
      self.assertEqual(revisions, 1)
    else:
      self.assertIsNone(rel,
                        msg='%s mapped to %s' % (obj1.type, obj2.type))

  def assert_mapping_implication(self, to_create, implied, relevant=None):
    """Helper function for asserting mapping implication"""
    if relevant is None:
      relevant = set()
    objects = set()
    for obj in relevant:
      objects.add(obj)
    mappings = set()
    if not isinstance(to_create, list):
      to_create = [to_create]
    for src, dst in to_create:
      objects.add(src)
      objects.add(dst)
      self.create_mapping(src, dst)
      mappings.add(automapper.AutomapperGenerator.order(src, dst))
    if not isinstance(implied, list):
      implied = [implied]
    for src, dst in implied:
      objects.add(src)
      objects.add(dst)
      self.assert_mapping(src, dst)
      mappings.add(automapper.AutomapperGenerator.order(src, dst))
    possible = set()
    for src, dst in itertools.product(objects, objects):
      possible.add(automapper.AutomapperGenerator.order(src, dst))
    for src, dst in possible - mappings:
      self.assert_mapping(src, dst, missing=True)

  def with_permutations(self, mk1, mk2, mk3):
    """Helper function for creating permutations"""
    obj1, obj2, obj3 = mk1(), mk2(), mk3()
    self.assert_mapping_implication(
        to_create=[(obj1, obj2), (obj2, obj3)],
        implied=(obj1, obj3),
    )
    obj1, obj2, obj3 = mk1(), mk2(), mk3()
    self.assert_mapping_implication(
        to_create=[(obj2, obj3), (obj1, obj2)],
        implied=(obj1, obj3),
    )

  def test_directive_program_mapping(self):
    """Test mapping directive to a program"""
    self.with_permutations(
        lambda: self.create_object(models.Program, {
            'title': make_name('Program')
        }),
        lambda: self.create_object(models.Regulation, {
            'title': make_name('Test PD Regulation')
        }),
        lambda: self.create_object(models.Objective, {
            'title': make_name('Objective')
        }),
    )
    program = self.create_object(models.Program, {
        'title': make_name('Program')
    })
    objective1 = self.create_object(models.Objective, {
        'title': make_name('Objective')
    })
    objective2 = self.create_object(models.Objective, {
        'title': make_name('Objective')
    })
    self.assert_mapping_implication(
        to_create=[(program, objective1), (objective1, objective2)],
        implied=[],
    )

  def test_mapping_to_sections(self):
    """Test mapping to section"""
    regulation = self.create_object(models.Regulation, {
        'title': make_name('Test Regulation')
    })
    section = self.create_object(models.Section, {
        'title': make_name('Test section'),
    })
    objective = self.create_object(models.Objective, {
        'title': make_name('Objective')
    })
    self.assert_mapping_implication(
        to_create=[(regulation, section), (objective, section)],
        implied=(objective, regulation),

    )
    program = self.create_object(models.Program, {
        'title': make_name('Program')
    })
    self.assert_mapping_implication(
        to_create=[(objective, program)],
        implied=[(regulation, section),
                 (objective, section),
                 (objective, regulation)],
        relevant=[regulation, section, objective]
    )

  def test_automapping_limit(self):
    """Test mapping limit"""
    with automapping_count_limit(-1):
      regulation = self.create_object(models.Regulation, {
          'title': make_name('Test Regulation')
      })
      section = self.create_object(models.Section, {
          'title': make_name('Test section'),
      })
      objective = self.create_object(models.Objective, {
          'title': make_name('Objective')
      })
      self.assert_mapping_implication(
          to_create=[(regulation, section), (objective, section)],
          implied=[],
      )

  def test_mapping_to_objective(self):
    """Test mapping to objective"""
    regulation = self.create_object(models.Regulation, {
        'title': make_name('Test PD Regulation')
    })
    section = self.create_object(models.Section, {
        'title': make_name('Test section'),
        'directive': {'id': regulation.id},
    })
    control = self.create_object(models.Control, {
        'title': make_name('Test control')
    })
    objective = self.create_object(models.Objective, {
        'title': make_name('Test control')
    })
    self.assert_mapping_implication(
        to_create=[(regulation, section),
                   (section, objective),
                   (objective, control)],
        implied=[
            (regulation, objective),
            (section, control),
            (regulation, control),
        ]
    )

    program = self.create_object(models.Program, {
        'title': make_name('Program')
    })
    self.assert_mapping_implication(
        to_create=[(control, program)],
        implied=[
            (regulation, section),
            (section, objective),
            (objective, control),
            (regulation, objective),
            (section, control),
            (regulation, control),
        ],
        relevant=[regulation, section, objective, control]
    )

  def test_mapping_between_objectives(self):
    """Test mapping between objectives"""
    regulation = self.create_object(models.Regulation, {
        'title': make_name('Test PD Regulation')
    })
    section = self.create_object(models.Section, {
        'title': make_name('Test section'),
        'directive': {'id': regulation.id},
    })
    objective1 = self.create_object(models.Objective, {
        'title': make_name('Test Objective')
    })
    objective2 = self.create_object(models.Objective, {
        'title': make_name('Test Objective')
    })
    self.assert_mapping_implication(
        to_create=[(regulation, section),
                   (section, objective1),
                   (objective1, objective2)],
        implied=[
            (section, objective2),
            (regulation, objective1),
            (regulation, objective2),
        ]
    )

  def test_mapping_nested_controls(self):
    """Test mapping of nested controls"""
    objective = self.create_object(models.Objective, {
        'title': make_name('Test Objective')
    })
    control_p = self.create_object(models.Control, {
        'title': make_name('Test control')
    })
    control1 = self.create_object(models.Control, {
        'title': make_name('Test control')
    })
    control2 = self.create_object(models.Control, {
        'title': make_name('Test control')
    })
    self.assert_mapping_implication(
        to_create=[(objective, control_p),
                   (control_p, control1),
                   (control_p, control2)],
        implied=[(objective, control1), (objective, control2)]
    )

  def test_automapping_permissions(self):
    """Test automapping permissions"""
    _, creator = self.gen.generate_person(user_role="Creator")
    _, admin = self.gen.generate_person(user_role="Administrator")
    program = self.create_object(models.Program, {
        'title': make_name('Program')
    })
    program = program.query.get(program.id)

    regulation = self.create_object(models.Regulation, {
        'title': make_name('Regulation'),
    })
    self.create_ac_roles(regulation, admin.id)
    regulation = regulation.query.get(regulation.id)

    self.api.set_user(creator)
    section = self.create_object(models.Section, {
        'title': make_name('Section'),
    })
    self.create_ac_roles(section, creator.id)
    section = section.query.get(section.id)

    objective = self.create_object(models.Objective, {
        'title': make_name('Objective'),
    })
    self.create_ac_roles(objective, creator.id)
    objective = objective.query.get(objective.id)

    control = self.create_object(models.Control, {
        'title': make_name('Control'),
    })
    self.create_ac_roles(control, creator.id)
    control = control.query.get(control.id)

    self.api.set_user(admin)
    self.assert_mapping_implication(
        to_create=[(program, regulation), (regulation, section)],
        implied=[(program, section)]
    )

    self.api.set_user(creator)
    self.assert_mapping_implication(
        to_create=[(section, objective),
                   (control, objective)],
        implied=[(program, regulation),
                 (program, section),
                 (section, regulation),
                 (control, section)],
    )

  def test_automapping_deletion(self):
    """Test if automapping data is preserved even when the parent relationship
       is deleted.
    """
    # Prepare some data:
    program = self.create_object(models.Program, {
        'title': make_name('Program')
    })
    regulation = self.create_object(models.Regulation, {
        'title': make_name('Regulation')
    })
    control = self.create_object(models.Control, {
        'title': make_name('Control')
    })
    self.create_mapping(program, regulation)
    rel1 = self.create_mapping(regulation, control)

    # Check if the correct automapping row is inserted:
    auto = Automapping.query.filter_by(
        source_id=rel1.source_id,
        source_type=rel1.source_type,
        destination_id=rel1.destination_id,
        destination_type=rel1.destination_type
    ).one()
    assert auto is not None

    # Check if the correct parent id is set:
    rel2 = models.Relationship.query.filter_by(
        parent_id=rel1.id
    ).one()
    assert rel2 is not None

    # Check if the new relationship points to the correct automapping
    assert rel2.automapping_id == auto.id

    # Delete the parent relationship
    self.api.delete(rel1)

    # Use the automapping_id to find the relationship again
    rel2_after_delete = models.Relationship.query.filter_by(
        automapping_id=auto.id
    ).one()

    assert rel2_after_delete is not None
    # Make sure we are looking at the same object
    assert rel2.id == rel2_after_delete.id
    # Parent id should now be None
    assert rel2_after_delete.parent_id is None


class TestIssueAutomappings(TestCase):
  """Test suite for Issue-related automappings."""
  # pylint: disable=invalid-name

  def setUp(self):
    super(TestIssueAutomappings, self).setUp()

    # TODO: replace this hack with a special test util
    from ggrc.login import noop
    noop.login()  # this is needed to pass the permission checks in automapper

    snapshottable = factories.ControlFactory()
    with factories.single_commit():
      self.audit, self.asmt, self.snapshot = self._make_audit_asmt_snapshot(
          snapshottable,
      )

      self.issue = factories.IssueFactory()
      self.issue_audit = factories.IssueFactory()
      self.issue_snapshot = factories.IssueFactory()

      factories.RelationshipFactory(source=self.issue_audit,
                                    destination=self.audit)

      # to map an Issue to a Snapshot, you first should map it to Audit
      factories.RelationshipFactory(source=self.issue_snapshot,
                                    destination=self.audit)
      factories.RelationshipFactory(source=self.issue_snapshot,
                                    destination=self.snapshot)

  @staticmethod
  def _make_audit_asmt_snapshot(snapshottable):
    """Make Audit, Assessment, Snapshot and map them correctly."""
    audit = factories.AuditFactory()
    assessment = factories.AssessmentFactory(audit=audit)

    revision = all_models.Revision.query.filter(
        all_models.Revision.resource_id == snapshottable.id,
        all_models.Revision.resource_type == snapshottable.type,
    ).first()
    snapshot = factories.SnapshotFactory(
        parent=audit,
        revision_id=revision.id,
        child_type=snapshottable.type,
        child_id=snapshottable.id,
    )

    # Audit-Assessment Relationship is created only on Assessment POST
    factories.RelationshipFactory(source=audit, destination=assessment)
    factories.RelationshipFactory(source=assessment, destination=snapshot)

    return audit, assessment, snapshot

  @staticmethod
  def _ordered_pairs_from_relationships(relationships):
    """Make list of ordered src, dst from a list of Relationship objects."""
    def order(src, dst):
      return ((src, dst) if (src.type, src.id) < (dst.type, dst.id) else
              (dst, src))

    return [order(r.source, r.destination) for r in relationships]

  @classmethod
  def _get_automapped_relationships(cls):
    """Get list of ordered src, dst mapped by the only automapping."""
    automapping = all_models.Automapping.query.one()
    automapped = all_models.Relationship.query.filter(
        all_models.Relationship.automapping_id == automapping.id,
    ).all()
    return cls._ordered_pairs_from_relationships(automapped)

  def test_issue_assessment_automapping(self):
    """Issue is automapped to Audit and Snapshot."""
    factories.RelationshipFactory(source=self.issue,
                                  destination=self.asmt)

    automapped = self._get_automapped_relationships()

    self.assertItemsEqual(automapped,
                          [(self.audit, self.issue),
                           (self.issue, self.snapshot)])

  def test_issue_assessment_automapping_no_audit(self):
    """Issue is automapped to Snapshot if Audit already mapped."""
    factories.RelationshipFactory(source=self.issue_audit,
                                  destination=self.asmt)

    automapped = self._get_automapped_relationships()

    self.assertItemsEqual(automapped,
                          [(self.issue_audit, self.snapshot)])

  def test_issue_assessment_automapping_all_mapped(self):
    """Issue is not automapped to Snapshot and Audit if already mapped."""
    factories.RelationshipFactory(source=self.issue_snapshot,
                                  destination=self.asmt)

    self.assertEqual(all_models.Automapping.query.count(), 0)
