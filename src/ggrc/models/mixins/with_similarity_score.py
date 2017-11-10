# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Contains WithSimilarityScore mixin.

This defines a procedure of getting "similar" objects which have similar
relationships.
"""

import sqlalchemy as sa
from sqlalchemy.orm import aliased

from ggrc import db
from ggrc.models.relationship import Relationship
from ggrc.models.snapshot import Snapshot

DEFAULT_WEIGHT = 1


class WithSimilarityScore(object):
  """Defines a routine to get similar object with mappings to same objects."""

  # pylint: disable=too-few-public-methods

  # example of similarity_options:
  # similarity_options = {
  #     "relevant_types": {"Audit": {"weight": 5}, type: {"weight": w}},
  #     "threshold": 10,
  # }

  @classmethod
  def get_similar_objects_query(cls, id_, type_):
    """Get objects of types similar to cls instance by their mappings.

    Args:
      id_: the id of the object to which the search will be applied;
      type_: type of similar object;

    Returns:
      SQLAlchemy query that yields results with columns [(id, type, weight)] -
          the id and type of similar objects with respective weights.
    """
    from ggrc.snapshotter.rules import Types
    if cls.__name__ in Types.all:
      from ggrc.models import relationship_helper
      # For snapshotted objects similar assessments will be the same as related
      return relationship_helper.get_ids_related_to(type_, cls.__name__, id_)

    if not type_ and type_ != "all":
      raise ValueError("Expected types = 'all' or a non-empty list of "
                       "requested types, got {} instead.".format(type_))
    if not hasattr(cls, "assessment_type"):
      raise AttributeError("Expected 'assessment_type' field defined for "
                           "'{c.__name__}' model.".format(c=cls))
    relevant_types = db.session.query(cls.assessment_type)\
                                 .filter(cls.id == id_)

    # naming: self is "object", the object mapped to it is "related",
    # the object mapped to "related" is "similar"
    queries_for_union = []

    # find "similar" objects with Relationship table
    queries_for_union += cls._join_relationships(id_)

    # find "similar" objects based on snapshots
    queries_for_union += cls._join_snapshots(id_, type_)

    joined = queries_for_union.pop().union_all(*queries_for_union).subquery()

    # define weights for every "related" object type with default_weight
    weight_case = sa.case(
        [(joined.c.related_type == relevant_types, DEFAULT_WEIGHT)],
        else_=0)
    weight_sum = sa.func.sum(weight_case).label("weight")

    # return the id and type of "similar" object together with its measure of
    # similarity
    result = db.session.query(
        joined.c.similar_id.label("id"),
        joined.c.similar_type.label("type"),
        weight_sum,
    ).filter(sa.or_(
        # filter out self
        joined.c.similar_id != id_,
        joined.c.similar_type != cls.__name__,
    ))

    # Filter Assessments with proper assessment_type
    asmnt_cond = sa.case([(
        joined.c.similar_type == "Assessment",
        sa.and_(
            joined.c.similar_id == cls.id,
            cls.assessment_type == relevant_types,
        )
    )], else_=True)
    result = result.join(cls, asmnt_cond)

    result = result.filter(joined.c.similar_type == type_)

    threshold = 1
    # group by "similar" objects to remove duplicated rows
    result = result.group_by(
        joined.c.similar_type,
        joined.c.similar_id,
    ).having(
        # filter out "similar" objects that have insufficient similarity
        weight_sum >= threshold,
    )
    return result

  @classmethod
  def _join_snapshots(cls, id_, type_):
    """Retrieves related objects with snapshots

    Performs a query where it first:
    1) Find all directly mapped snapshots
    2) Join with snapshots to find type and id of snapshots (child_type and
    child_id) - left snapshots
    3) Join with snapshots to find snapshots with the same child_type and
    child_id (right_snapshots)
    4) Find all objects mapped to right snapshots (right_relationships)

    Arg:
      id_: ID of instance performing similarity query on
    Return:
      [(related_type, similar_id, similar_type)] where related type is the type
      related objects, similar_id and similar_type being id and type of
      second tier objects.
    """

    left_snapshot = aliased(Snapshot, name="left_snapshot")
    right_snapshot = aliased(Snapshot, name="right_snapshot")
    left_relationship = aliased(Relationship, name="left_relationship")
    right_relationship = aliased(Relationship, name="right_relationship")

    snapshot_ids = sa.select([
        left_relationship.destination_id.label("snapshot_left_id"),
    ]).where(
        sa.and_(
            left_relationship.source_type == cls.__name__,
            left_relationship.source_id == id_,
            left_relationship.destination_type == "Snapshot"
        )
    ).union(
        sa.select([
            left_relationship.source_id.label("snapshot_left_id"),
        ]).where(
            sa.and_(
                left_relationship.destination_type == cls.__name__,
                left_relationship.destination_id == id_,
                left_relationship.source_type == "Snapshot"
            )
        )
    ).alias("snapshot_ids")

    left_snapshot_join = snapshot_ids.outerjoin(
        left_snapshot,
        left_snapshot.id == snapshot_ids.c.snapshot_left_id
    )

    right_snapshot_join = left_snapshot_join.outerjoin(
        right_snapshot,
        sa.and_(
            right_snapshot.child_type == left_snapshot.child_type,
            right_snapshot.child_id == left_snapshot.child_id
        )
    ).alias("right_snapshot_join")

    return [
        db.session.query(
            right_snapshot_join.c.right_snapshot_child_type.label(
                "related_type"),
            right_relationship.source_id.label("similar_id"),
            right_relationship.source_type.label("similar_type"),
        ).filter(
            sa.and_(
                right_relationship.destination_type == "Snapshot",
                right_relationship.destination_id ==
                right_snapshot_join.c.right_snapshot_id,
                right_relationship.source_type == type_
            )
        ),
        db.session.query(
            right_snapshot_join.c.right_snapshot_child_type.label(
                "related_type"),
            right_relationship.destination_id.label("similar_id"),
            right_relationship.destination_type.label("similar_type"),
        ).filter(
            sa.and_(
                right_relationship.source_type == "Snapshot",
                right_relationship.source_id ==
                right_snapshot_join.c.right_snapshot_id,
                right_relationship.destination_type == type_
            )
        )
    ]

  @classmethod
  def _join_relationships(cls, id_):
    """Make a self-join of Relationship table to find common mappings.

    Returns a query with results for [(related_type, similar_id, similar_type)]
    where similar_id and similar_type describe a second-tier mapped object and
    related_type is the type of a common mapped object between "object" and
    "similar".
    """
    # get all Relationships for self
    object_to_related = db.session.query(Relationship).filter(
        sa.or_(sa.and_(Relationship.source_type == cls.__name__,
                 Relationship.source_id == id_),
            sa.and_(Relationship.destination_type == cls.__name__,
                 Relationship.destination_id == id_))).subquery()

    # define how to get id and type of "related" objects
    related_id_case = (sa.case([(sa.and_(object_to_related.c.source_id == id_,
                                   object_to_related.c.source_type ==
                                   cls.__name__),
                              object_to_related.c.destination_id)],
                            else_=object_to_related.c.source_id)
                       .label("related_id"))
    related_type_case = (sa.case([(sa.and_(
                                     object_to_related.c.source_id == id_,
                                     object_to_related.c.source_type ==
                                     cls.__name__),
                                object_to_related.c.destination_type)],
                              else_=object_to_related.c.source_type)
                         .label("related_type"))

    related_to_similar = aliased(Relationship, name="related_to_similar")

    # self-join Relationships to get "similar" id and type; save "related" type
    # to get the weight of this relationship later
    return [
        db.session.query(
            related_type_case,
            related_to_similar.destination_id.label("similar_id"),
            related_to_similar.destination_type.label("similar_type"),
        ).join(
            related_to_similar,
            sa.and_(related_id_case == related_to_similar.source_id,
                 related_type_case == related_to_similar.source_type),
        ).filter(
            related_to_similar.source_type != "Snapshot"
        ),
        db.session.query(
            related_type_case,
            related_to_similar.source_id.label("similar_id"),
            related_to_similar.source_type.label("similar_type"),
        ).join(
            related_to_similar,
            sa.and_(related_id_case == related_to_similar.destination_id,
                 related_type_case == related_to_similar.destination_type),
        ).filter(
            related_to_similar.destination_type != "Snapshot"
        )
    ]
