# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

""" Tests for ggrc.models.Revision """

import ggrc.models
import integration.ggrc.generator
from integration.ggrc import TestCase

from integration.ggrc.models import factories


def _get_revisions(obj, field="resource"):
  return ggrc.models.Revision.query.filter_by(**{
      field + "_type": obj.__class__.__name__,
      field + "_id": obj.id
  }).all()


def _project_content(content):
  return {
      "source": {
          "type": content["source_type"],
          "id": content["source_id"],
      },
      "destination": {
          "type": content["destination_type"],
          "id": content["destination_id"],
      },
  }


class TestRevisions(TestCase):
  """ Tests for ggrc.models.Revision """

  def setUp(self):
    super(TestRevisions, self).setUp()
    self.gen = integration.ggrc.generator.ObjectGenerator()

  def test_revisions(self):
    """ Test revision creation for POST and PUT """
    cls = ggrc.models.DataAsset
    name = cls._inflector.table_singular  # pylint: disable=protected-access
    _, obj = self.gen.generate(cls, name, {name: {
        "title": "revisioned v1",
        "context": None,
    }})
    revisions = _get_revisions(obj)
    self.assertEqual(len(revisions), 1)

    _, obj = self.gen.modify(obj, name, {name: {
        "slug": obj.slug,
        "title": "revisioned v2",
        "context": None,
    }})
    revisions = _get_revisions(obj)
    expected = {("created", "revisioned v1"), ("modified", "revisioned v2")}
    actual = {(r.action, r.content["title"]) for r in revisions}
    self.assertEqual(actual, expected)

  def test_relevant_revisions(self):
    """ Test revision creation for mapping to an object """
    cls = ggrc.models.DataAsset
    name = cls._inflector.table_singular  # pylint: disable=protected-access

    _, obj1 = self.gen.generate(cls, name, {name: {
        "title": "connected 1",
        "context": None,
    }})

    _, obj2 = self.gen.generate(cls, name, {name: {
        "title": "connected 2",
        "context": None,
    }})

    rel_data = {
        "source": {"id": obj1.id, "type": cls.__name__},
        "destination": {"id": obj2.id, "type": cls.__name__},
        "context": None,
    }
    _, rel = self.gen.generate(ggrc.models.Relationship, "relationship", {
                               "relationship": rel_data})

    revisions_source = _get_revisions(obj1, "source")
    revisions_destination = _get_revisions(obj2, "destination")

    self.assertEqual(revisions_source, revisions_destination)
    self.assertEqual(len(revisions_source), 1)

    self.gen.api.delete(rel)

    revisions_source = _get_revisions(obj1, "source")
    revisions_destination = _get_revisions(obj2, "destination")

    self.assertEqual(revisions_source, revisions_destination)
    self.assertEqual(len(revisions_source), 2)

    expected_data = {
        "source": {
            "type": cls.__name__,
            "id": obj1.id,
        },
        "destination": {
            "type": cls.__name__,
            "id": obj2.id,
        },
    }
    expected = [(u"created", expected_data), ("deleted", expected_data)]

    actual = [(r.action, _project_content(r.content))
              for r in revisions_source]
    self.assertEqual(sorted(actual), sorted(expected))

  def test_content_length(self):
    """Test revision content length restrictions."""
    process = factories.ProcessFactory(
        title="a" * 200,
        description="b" * 65000,
        notes="c" * 65000,
    )
    revision = ggrc.models.Revision.query.filter(
        ggrc.models.Revision.resource_id == process.id,
        ggrc.models.Revision.resource_type == process.type,
    ).first()
    self.assertIsNotNone(revision)
    self.assertEqual(revision.content["title"], process.title)
    self.assertEqual(revision.content["description"], process.description)
