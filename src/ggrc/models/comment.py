# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Module containing comment model and comment related mixins."""

import itertools

from collections import defaultdict

from sqlalchemy import case
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import validates
from werkzeug.exceptions import BadRequest

from ggrc import builder
from ggrc import db
from ggrc.models.deferred import deferred
from ggrc.models.revision import Revision
from ggrc.models.mixins import Base
from ggrc.models.mixins import Described
from ggrc.models.mixins import Notifiable
from ggrc.models.relationship import Relatable, Relationship
from ggrc.access_control.roleable import Roleable
from ggrc.fulltext.mixin import Indexed, ReindexRule
from ggrc.fulltext.attributes import MultipleSubpropertyFullTextAttr
from ggrc.models import inflector


class Commentable(object):
  """Mixin for commentable objects.

  This is a mixin for adding default options to objects on which people can
  comment.

  recipients is used for setting who gets notified (Verifer, Requester, ...).
  send_by_default should be used for setting the "send notification" flag in
  the comment modal.

  """
  # pylint: disable=too-few-public-methods

  VALID_RECIPIENTS = frozenset([
      "Assessor",
      "Assignee",
      "Creator",
      "Verifier",
  ])

  @validates("recipients")
  def validate_recipients(self, key, value):
    """
      Validate recipients list

      Args:
        value (string): Can be either empty, or
                        list of comma separated `VALID_RECIPIENTS`
    """
    # pylint: disable=unused-argument
    if value:
      value = set(name for name in value.split(",") if name)

    if value and value.issubset(self.VALID_RECIPIENTS):
      # The validator is a bit more smart and also makes some filtering of the
      # given data - this is intended.
      return ",".join(value)
    elif not value:
      return None
    else:
      raise ValueError(value,
                       'Value should be either empty ' +
                       'or comma separated list of ' +
                       ', '.join(sorted(self.VALID_RECIPIENTS))
                       )

  recipients = db.Column(
      db.String,
      nullable=True,
      default=u"Assessor,Creator,Verifier")

  send_by_default = db.Column(db.Boolean, nullable=True, default=True)

  _publish_attrs = [
      "recipients",
      "send_by_default",
  ]
  _aliases = {
      "recipients": "Recipients",
      "send_by_default": "Send by default",
  }
  _fulltext_attrs = [
      MultipleSubpropertyFullTextAttr("comment", "comments", ["description"]),
  ]

  @classmethod
  def indexed_query(cls):
    return super(Commentable, cls).indexed_query().options(
        orm.Load(cls).subqueryload("comments").load_only("id", "description")
    )

  @declared_attr
  def comments(cls):  # pylint: disable=no-self-argument
    """Comments related to self via Relationship table."""
    comment_id = case(
        [(Relationship.destination_type == "Comment",
          Relationship.destination_id)],
        else_=Relationship.source_id,
    )
    commentable_id = case(
        [(Relationship.destination_type == "Comment",
          Relationship.source_id)],
        else_=Relationship.destination_id,
    )

    return db.relationship(
        Comment,
        primaryjoin=lambda: cls.id == commentable_id,
        secondary=Relationship.__table__,
        secondaryjoin=lambda: Comment.id == comment_id,
        viewonly=True,
    )


def reindex_by_relationship(relationship):
  """Reindex comment if relationship changed or created or deleted"""
  if relationship.destination_type == Comment.__name__:
    instance = relationship.source
  elif relationship.source_type == Comment.__name__:
    instance = relationship.destination
  else:
    return []
  if isinstance(instance, (Indexed, Commentable)):
    return [instance]
  return []


class Comment(Roleable, Relatable, Described, Notifiable,
              Base, Indexed, db.Model):
  """Basic comment model."""
  __tablename__ = "comments"

  assignee_type = db.Column(db.String)
  revision_id = deferred(db.Column(
      db.Integer,
      db.ForeignKey('revisions.id', ondelete='SET NULL'),
      nullable=True,
  ), 'Comment')
  revision = db.relationship(
      'Revision',
      uselist=False,
  )
  custom_attribute_definition_id = deferred(db.Column(
      db.Integer,
      db.ForeignKey('custom_attribute_definitions.id', ondelete='SET NULL'),
      nullable=True,
  ), 'Comment')
  custom_attribute_definition = db.relationship(
      'CustomAttributeDefinition',
      uselist=False,
  )

  # REST properties
  _publish_attrs = [
      "assignee_type",
      "custom_attribute_revision",
  ]

  _update_attrs = [
      "assignee_type",
      "custom_attribute_revision_upd",
  ]

  _sanitize_html = [
      "description",
  ]

  def get_objects_to_reindex(self):
    """Return list required objects for reindex if comment C.U.D."""
    source_qs = db.session.query(
        Relationship.destination_type, Relationship.destination_id
    ).filter(
        Relationship.source_type == self.__class__.__name__,
        Relationship.source_id == self.id
    )
    destination_qs = db.session.query(
        Relationship.source_type, Relationship.source_id
    ).filter(
        Relationship.destination_type == self.__class__.__name__,
        Relationship.destination_id == self.id
    )
    result_qs = source_qs.union(destination_qs)
    klass_dict = defaultdict(set)
    for klass, object_id in result_qs:
      klass_dict[klass].add(object_id)

    queries = []
    for klass, object_ids in klass_dict.iteritems():
      model = inflector.get_model(klass)
      if not model:
        continue
      if issubclass(model, (Indexed, Commentable)):
        queries.append(model.query.filter(model.id.in_(list(object_ids))))
    return list(itertools.chain(*queries))

  AUTO_REINDEX_RULES = [
      ReindexRule("Comment", lambda x: x.get_objects_to_reindex()),
      ReindexRule("Relationship", reindex_by_relationship),
  ]

  @classmethod
  def eager_query(cls):
    query = super(Comment, cls).eager_query()
    return query.options(
        orm.joinedload('revision'),
        orm.joinedload('custom_attribute_definition')
           .undefer_group('CustomAttributeDefinition_complete'),
    )

  @builder.simple_property
  def custom_attribute_revision(self):
    """Get the historical value of the relevant CA value."""
    if not self.revision:
      return None
    revision = self.revision.content
    cav_stored_value = revision['attribute_value']
    cad = self.custom_attribute_definition
    return {
        'custom_attribute': {
            'id': cad.id if cad else None,
            'title': cad.title if cad else 'DELETED DEFINITION',
        },
        'custom_attribute_stored_value': cav_stored_value,
    }

  def custom_attribute_revision_upd(self, value):
    """Create a Comment-CA mapping with current CA value stored."""
    ca_revision_dict = value.get('custom_attribute_revision_upd')
    if not ca_revision_dict:
      return
    ca_val_dict = self._get_ca_value(ca_revision_dict)

    ca_val_id = ca_val_dict['id']
    ca_val_revision = Revision.query.filter_by(
        resource_type='CustomAttributeValue',
        resource_id=ca_val_id,
    ).order_by(
        Revision.created_at.desc(),
    ).limit(1).first()
    if not ca_val_revision:
      raise BadRequest("No Revision found for CA value with id provided under "
                       "'custom_attribute_value': {}"
                       .format(ca_val_dict))

    self.revision_id = ca_val_revision.id
    self.custom_attribute_definition_id = ca_val_revision.content.get(
        'custom_attribute_id',
    )

  @staticmethod
  def _get_ca_value(ca_revision_dict):
    """Get CA value dict from json and do a basic validation."""
    ca_val_dict = ca_revision_dict.get('custom_attribute_value')
    if not ca_val_dict:
      raise ValueError("CA value expected under "
                       "'custom_attribute_value': {}"
                       .format(ca_revision_dict))
    if not ca_val_dict.get('id'):
      raise ValueError("CA value id expected under 'id': {}"
                       .format(ca_val_dict))
    return ca_val_dict
