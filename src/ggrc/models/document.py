# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Module containing Document model."""

from sqlalchemy import orm
from sqlalchemy import func
from sqlalchemy.ext.hybrid import hybrid_property

from ggrc import db
from ggrc.access_control.roleable import Roleable
from ggrc.fulltext.mixin import Indexed
from ggrc.models.deferred import deferred
from ggrc.models.mixins import Base
from ggrc.models.relationship import Relatable
from ggrc.models.utils import validate_option
from ggrc.models import exceptions


class Document(Roleable, Relatable, Base, Indexed, db.Model):
  """Audit model."""
  __tablename__ = 'documents'

  # TODO: inherit from Titled mixin (note: title is nullable here)
  title = deferred(db.Column(db.String), 'Document')
  link = deferred(db.Column(db.String), 'Document')
  description = deferred(db.Column(db.Text), 'Document')
  kind_id = db.Column(db.Integer, db.ForeignKey('options.id'), nullable=True)
  year_id = db.Column(db.Integer, db.ForeignKey('options.id'), nullable=True)
  language_id = db.Column(db.Integer, db.ForeignKey('options.id'),
                          nullable=True)

  URL = "URL"
  ATTACHMENT = "EVIDENCE"
  VALID_DOCUMENT_TYPES = [URL, ATTACHMENT]
  document_type = deferred(db.Column(db.Enum(URL, ATTACHMENT),
                                     default=URL,
                                     nullable=False),
                           'Document')

  kind = db.relationship(
      'Option',
      primaryjoin='and_(foreign(Document.kind_id) == Option.id, '
      'Option.role == "reference_type")',
      uselist=False,
      lazy="joined",
  )
  year = db.relationship(
      'Option',
      primaryjoin='and_(foreign(Document.year_id) == Option.id, '
      'Option.role == "document_year")',
      uselist=False,
      lazy="joined",
  )
  language = db.relationship(
      'Option',
      primaryjoin='and_(foreign(Document.language_id) == Option.id, '
      'Option.role == "language")',
      uselist=False,
      lazy="joined",
  )

  _fulltext_attrs = [
      'title',
      'link',
      'description',
      "document_type",
  ]

  _publish_attrs = [
      'title',
      'link',
      'description',
      'kind',
      'year',
      'language',
      "document_type",
  ]

  _sanitize_html = [
      'title',
      'description',
  ]

  _aliases = {
      'title': "Title",
      'link': "Link",
      'description': "description",
  }

  @orm.validates('kind', 'year', 'language')
  def validate_document_options(self, key, option):
    """Returns correct option, otherwise rises an error"""
    if key == 'year':
      desired_role = 'document_year'
    elif key == 'kind':
      desired_role = 'reference_type'
    else:
      desired_role = key
    return validate_option(self.__class__.__name__, key, option, desired_role)

  @orm.validates('document_type')
  def validate_document_type(self, key, document_type):
    """Returns correct option, otherwise rises an error"""
    if document_type is None:
      document_type = self.URL
    if document_type not in self.VALID_DOCUMENT_TYPES:
      raise exceptions.ValidationError(
          "Invalid value for attribute {attr}. "
          "Expected options are `{url}`, `{attachment}`.".format(
              attr=key,
              url=self.URL,
              attachment=self.ATTACHMENT,
          )
      )
    return document_type

  @classmethod
  def indexed_query(cls):
    return super(Document, cls).indexed_query().options(
        orm.Load(cls).undefer_group(
            "Document_complete",
        ),
    )

  @classmethod
  def eager_query(cls):
    return super(Document, cls).eager_query().options(
        orm.joinedload('kind'),
        orm.joinedload('year'),
        orm.joinedload('language'),
    )

  @hybrid_property
  def slug(self):
    if self.document_type == self.URL:
      return self.link
    return u"{} {}".format(self.link, self.title)

  # pylint: disable=no-self-argument
  @slug.expression
  def slug(cls):
    return func.concat(cls.link, ' ', cls.title)

  def log_json(self):
    tmp = super(Document, self).log_json()
    tmp['type'] = "Document"
    return tmp
