# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Mixins to add common attributes and relationships. Note, all model classes
must also inherit from ``db.Model``. For example:
color
color
  ..

     class Market(BusinessObject, db.Model):
       __tablename__ = 'markets'

"""

# pylint: disable=no-self-argument
# All declared_attr properties that are class level as per sqlalchemy
# documentatio, are reported as false positives by pylint.

from logging import getLogger
from uuid import uuid1
import datetime

from sqlalchemy import event
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import validates
from sqlalchemy.orm.session import Session

from ggrc import db
from ggrc.models import reflection
from ggrc.models.computed_property import computed_property
from ggrc.models.deferred import deferred
from ggrc.models.inflector import ModelInflectorDescriptor
from ggrc.models.reflection import AttributeInfo
from ggrc.models.mixins.customattributable import CustomAttributable
from ggrc.models.mixins.notifiable import Notifiable


# pylint: disable=invalid-name
logger = getLogger(__name__)


class Identifiable(object):

  """A model with an ``id`` property that is the primary key."""
  id = db.Column(db.Integer, primary_key=True)  # noqa

  # REST properties
  _publish_attrs = ['id', 'type']
  _update_attrs = []

  _inflector = ModelInflectorDescriptor()

  @computed_property
  def type(self):
    return self.__class__.__name__

  @classmethod
  def eager_query(cls):
    mapper_class = cls._sa_class_manager.mapper.base_mapper.class_
    return db.session.query(cls).options(
        db.Load(mapper_class).undefer_group(
            mapper_class.__name__ + '_complete'),
    )

  @classmethod
  def eager_inclusions(cls, query, include_links):
    options = []
    for include_link in include_links:
      inclusion_class = getattr(cls, include_link).property.mapper.class_
      options.append(
          orm.subqueryload(include_link)
          .undefer_group(inclusion_class.__name__ + '_complete'))
    return query.options(*options)

  @declared_attr
  def __table_args__(cls):
    extra_table_args = AttributeInfo.gather_attrs(cls, '_extra_table_args')
    table_args = []
    table_dict = {}
    for table_arg in extra_table_args:
      if callable(table_arg):
        table_arg = table_arg()
      if isinstance(table_arg, (list, tuple, set)):
        if isinstance(table_arg[-1], (dict,)):
          table_dict.update(table_arg[-1])
          table_args.extend(table_arg[:-1])
        else:
          table_args.extend(table_arg)
      elif isinstance(table_arg, (dict,)):
        table_dict.update(table_arg)
      else:
        table_args.append(table_arg)
    if len(table_dict) > 0:
      table_args.append(table_dict)
    return tuple(table_args,)


class ChangeTracked(object):

  """A model with fields to tracked the last user to modify the model, the
  creation time of the model, and the last time the model was updated.
  """
  @declared_attr
  def modified_by_id(cls):
    return deferred(db.Column(db.Integer), cls.__name__)

  @declared_attr
  def created_at(cls):
    column = db.Column(
        db.DateTime,
        nullable=False,
        default=db.text('current_timestamp'),
    )
    return deferred(column, cls.__name__)

  @declared_attr
  def updated_at(cls):
    column = db.Column(
        db.DateTime,
        nullable=False,
        default=db.text('current_timestamp'),
        onupdate=db.text('current_timestamp'),
    )
    return deferred(column, cls.__name__)

  @declared_attr
  def modified_by(cls):
    return db.relationship(
        'Person',
        primaryjoin='{0}.modified_by_id == Person.id'.format(cls.__name__),
        foreign_keys='{0}.modified_by_id'.format(cls.__name__),
        uselist=False,
    )

  @staticmethod
  def _extra_table_args(cls):
    return (
        db.Index('ix_{}_updated_at'.format(cls.__tablename__), 'updated_at'),
    )

  # TODO Add a transaction id, this will be handy for generating etags
  # and for tracking the changes made to several resources together.
  # transaction_id = db.Column(db.Integer)

  # REST properties
  _publish_attrs = [
      'modified_by',
      'created_at',
      'updated_at',
  ]
  _update_attrs = []


class Titled(object):

  @validates('title')
  def validate_title(self, key, value):
    """Validates and cleans Title that has leading/trailing spaces"""
    # pylint: disable=unused-argument,no-self-use
    return value if value is None else value.strip()

  @declared_attr
  def title(cls):
    return deferred(db.Column(db.String, nullable=False), cls.__name__)

  @staticmethod
  def _extra_table_args(cls):
    if getattr(cls, '_title_uniqueness', True):
      return (
          db.UniqueConstraint(
              'title', name='uq_t_{}'.format(cls.__tablename__)),
      )
    return ()

  # REST properties
  _publish_attrs = ['title']
  _fulltext_attrs = ['title']
  _sanitize_html = ['title']
  _aliases = {"title": "Title"}


class Described(object):

  @declared_attr
  def description(cls):
    return deferred(db.Column(db.Text), cls.__name__)

  # REST properties
  _publish_attrs = ['description']
  _fulltext_attrs = ['description']
  _sanitize_html = ['description']
  _aliases = {"description": "Description"}


class Noted(object):

  @declared_attr
  def notes(cls):
    return deferred(db.Column(db.Text), cls.__name__)

  # REST properties
  _publish_attrs = ['notes']
  _fulltext_attrs = ['notes']
  _sanitize_html = ['notes']
  _aliases = {"notes": "Notes"}


class Hyperlinked(object):

  @declared_attr
  def url(cls):
    return deferred(db.Column(db.String), cls.__name__)

  @declared_attr
  def reference_url(cls):
    return deferred(db.Column(db.String), cls.__name__)

  # REST properties
  _publish_attrs = ['url', 'reference_url']

  _aliases = {
      "url": "Url",
      "reference_url": "Reference URL",
  }


class Hierarchical(object):

  @declared_attr
  def parent_id(cls):
    return deferred(db.Column(
        db.Integer, db.ForeignKey('{0}.id'.format(cls.__tablename__))),
        cls.__name__)

  @declared_attr
  def children(cls):
    return db.relationship(
        cls.__name__,
        backref=db.backref(
            'parent', remote_side='{0}.id'.format(cls.__name__)),
    )

  # REST properties
  _publish_attrs = [
      'children',
      'parent',
  ]

  @classmethod
  def eager_query(cls):
    query = super(Hierarchical, cls).eager_query()
    return query.options(
        orm.subqueryload('children'),
        # orm.joinedload('parent'),
    )


class Timeboxed(object):

  @declared_attr
  def start_date(cls):
    return deferred(db.Column(db.Date), cls.__name__)

  @declared_attr
  def end_date(cls):
    return deferred(db.Column(db.Date), cls.__name__)

  # REST properties
  _publish_attrs = ['start_date', 'end_date']

  _aliases = {
      "start_date": "Effective Date",
      "end_date": "Stop Date",
  }


class Stateful(object):

  @declared_attr
  def status(cls):
    return deferred(db.Column(
        db.String, default=cls.default_status, nullable=False), cls.__name__)

  _publish_attrs = ['status']
  _aliases = {
      "status": {
          "display_name": "State",
          "mandatory": False
      }
  }

  @classmethod
  def default_status(cls):
    return cls.valid_statuses()[0]

  @classmethod
  def valid_statuses(cls):
    return cls.VALID_STATES

  @validates('status')
  def validate_status(self, key, value):
    # Sqlalchemy only uses one validator per status (not necessarily the
    # first) and ignores others. This enables cooperation between validators
    # since there are other mixins that want to touch 'status'.
    if hasattr(super(Stateful, self), "validate_status"):
      value = super(Stateful, self).validate_status(key, value)
    if value is None:
      value = self.default_status()
    if value not in self.valid_statuses():
      message = u"Invalid state '{}'".format(value)
      raise ValueError(message)
    return value


class FinishedDate(object):
  """Adds 'Finished Date' which is set when status is set to a finished state.

  Requires Stateful to be mixed in as well.
  """

  NOT_DONE_STATES = None
  DONE_STATES = {}

  # pylint: disable=method-hidden
  # because validator only sets date per model instance
  @declared_attr
  def finished_date(cls):
    return deferred(
        db.Column(db.Date, nullable=True),
        cls.__name__
    )

  _publish_attrs = [
      reflection.PublishOnly('finished_date')
  ]

  _aliases = {
      "finished_date": "Finished Date"
  }

  @validates('status')
  def validate_status(self, key, value):
    """Update finished_date given the right status change."""
    # Sqlalchemy only uses one validator per status (not necessarily the
    # first) and ignores others. This enables cooperation between validators
    # since 'status' is not defined here.
    if hasattr(super(FinishedDate, self), "validate_status"):
      value = super(FinishedDate, self).validate_status(key, value)
    # pylint: disable=unsupported-membership-test
    # short circuit
    if (value in self.DONE_STATES and
        (self.NOT_DONE_STATES is None or
         self.status in self.NOT_DONE_STATES)):
      self.finished_date = datetime.datetime.now()
    elif ((self.NOT_DONE_STATES is None or
           value in self.NOT_DONE_STATES) and
            self.status in self.DONE_STATES):
      self.finished_date = None
    return value


class VerifiedDate(object):
  """Adds 'Verified Date' which is set when status is set to 'Verified'.

  When object is verified the status is overridden to 'Final' and the
  information about verification exposed as the 'verified' boolean.
  Requires Stateful to be mixed in as well.
  """

  VERIFIED_STATES = {u"Verified"}
  DONE_STATES = {}

  # pylint: disable=method-hidden
  # because validator only sets date per model instance
  @declared_attr
  def verified_date(cls):
    return deferred(
        db.Column(db.Date, nullable=True),
        cls.__name__
    )

  @hybrid_property
  def verified(self):
    return self.verified_date != None  # noqa

  _publish_attrs = [
      reflection.PublishOnly('verified'),
      reflection.PublishOnly('verified_date'),
  ]

  _aliases = {
      "verified_date": "Verified Date"
  }

  @validates('status')
  def validate_status(self, key, value):
    """Update verified_date on status change, make verified status final."""
    # Sqlalchemy only uses one validator per status (not necessarily the
    # first) and ignores others. This enables cooperation between validators
    # since 'status' is not defined here.
    if hasattr(super(VerifiedDate, self), "validate_status"):
      value = super(VerifiedDate, self).validate_status(key, value)
    if (value in self.VERIFIED_STATES and
            self.status not in self.VERIFIED_STATES):
      self.verified_date = datetime.datetime.now()
      value = self.FINAL_STATE
    elif (value not in self.VERIFIED_STATES and
          value not in self.DONE_STATES and
          (self.status in self.VERIFIED_STATES or
           self.status in self.DONE_STATES)):
      self.verified_date = None
    return value


class ContextRBAC(object):

  @declared_attr
  def context_id(cls):
    return db.Column(db.Integer, db.ForeignKey('contexts.id'))

  @declared_attr
  def context(cls):
    return db.relationship('Context', uselist=False)

  @staticmethod
  def _extra_table_args(cls):
    return (
        db.Index('fk_{}_contexts'.format(cls.__tablename__), 'context_id'),
    )

  _publish_attrs = ['context']

  # @classmethod
  # def eager_query(cls):
  # from sqlalchemy import orm

  # query = super(ContextRBAC, cls).eager_query()
  # return query.options(
  # orm.subqueryload('context'))


class Base(ChangeTracked, ContextRBAC, Identifiable):

  """Several of the models use the same mixins. This class covers that common
  case.
  """
  _people_log_mappings = [
      "principal_assessor_id",
      "secondary_assessor_id",
      "contact_id",
      "secondary_contact_id",
      "modified_by_id",
      "attribute_object_id",  # used for person mapping CA
  ]

  @staticmethod
  def _person_stub(id_):
    return {
        'type': u"Person",
        'id': id_,
        'context_id': None,
        'href': u"/api/people/{}".format(id_),
    }

  def log_json(self):
    # to integrate with CustomAttributable without order dependencies
    res = getattr(super(Base, self), "log_json", lambda: {})()
    for column in self.__table__.columns:
      try:
        res[column.name] = getattr(self, column.name)
      except AttributeError:
        pass
    res['display_name'] = self.display_name

    for attr in self._people_log_mappings:
      if hasattr(self, attr):
        value = getattr(self, attr)
        res[attr[:-3]] = self._person_stub(value) if value else None
    if hasattr(self, "owners"):
      res["owners"] = [
          self._person_stub(owner.id) for owner in self.owners if owner
      ]

    return res

  @computed_property
  def display_name(self):
    try:
      return self._display_name()
    except:  # pylint: disable=bare-except
      logger.warning("display_name error in %s", type(self), exc_info=True)
      return ""

  def _display_name(self):
    return getattr(self, "title", None) or getattr(self, "name", "")

  def copy_into(self, target_object, columns, **kwargs):
    """Copy current object values into a target object.

    Copy all values listed in columns from current class to target class and
    use kwargs as defaults with precedence. Note that this is a shallow copy
    and any mutable values will be shared between current and target objects.

    Args:
      target_object: object to which we want to copy current values. This
        function will mutate the target_object parameter if it is set.
      columns: list with all attribute names that we want to set in the
        target_object.
      kwargs: additional default values.

    Returns:
      target_object with all values listed in columns set.
    """
    target = target_object or type(self)()

    columns = set(columns).union(kwargs.keys())
    for name in columns:
      if name in kwargs:
        value = kwargs[name]
      else:
        value = getattr(self, name)
      setattr(target, name, value)

    return target


class Slugged(Base):

  """Several classes make use of the common mixins and additional are
  "slugged" and have additional fields related to their publishing in the
  system.
  """

  @declared_attr
  def slug(cls):
    return deferred(db.Column(db.String, nullable=False), cls.__name__)

  @staticmethod
  def _extra_table_args(cls):
    if getattr(cls, '_slug_uniqueness', True):
      return (
          db.UniqueConstraint('slug', name='uq_{}'.format(cls.__tablename__)),
      )
    return ()

  # REST properties
  _publish_attrs = ['slug']
  _fulltext_attrs = ['slug']
  _sanitize_html = ['slug']
  _aliases = {
      "slug": {
          "display_name": "Code",
          "description": ("Must be unique. Can be left empty for "
                          "auto generation. If updating or deleting, "
                          "code is required"),
      }
  }

  @classmethod
  def generate_slug_for(cls, obj):
    _id = getattr(obj, 'id', uuid1())
    obj.slug = "{0}-{1}".format(cls.generate_slug_prefix_for(obj), _id)
    # We need to make sure the generated slug is not already present in the
    # database. If it is, we increment the id until we find a slug that is
    # unique.
    # A better approach would be to query the database for slug uniqueness
    # only if the there was a conflict, but because we can't easily catch a
    # session rollback at this point we are sticking with a
    # suboptimal solution for now.
    INCREMENT = 1000
    while cls.query.filter(cls.slug == obj.slug).count():
      _id += INCREMENT
      obj.slug = "{0}-{1}".format(cls.generate_slug_prefix_for(obj), _id)

  @classmethod
  def generate_slug_prefix_for(cls, obj):
    return obj.__class__.__name__.upper()

  @classmethod
  def ensure_slug_before_flush(cls, session, flush_context, instances):
    """Set the slug to a default string so we don't run afoul of the NOT NULL
    constraint.
    """
    for o in session.new:
      if isinstance(o, Slugged) and (o.slug is None or o.slug == ''):
        o.slug = str(uuid1())
        o._replace_slug = True

  @classmethod
  def ensure_slug_after_flush_postexec(cls, session, flush_context):
    """Replace the placeholder slug with a real slug that will be set on the
    next flush/commit.
    """
    for o in session.identity_map.values():
      if isinstance(o, Slugged) and hasattr(o, '_replace_slug'):
        o.generate_slug_for(o)
        delattr(o, '_replace_slug')


event.listen(Session, 'before_flush', Slugged.ensure_slug_before_flush)
event.listen(
    Session, 'after_flush_postexec', Slugged.ensure_slug_after_flush_postexec)


class WithContact(object):

  @declared_attr
  def contact_id(cls):
    return deferred(
        db.Column(db.Integer, db.ForeignKey('people.id')), cls.__name__)

  @declared_attr
  def secondary_contact_id(cls):
    return deferred(
        db.Column(db.Integer, db.ForeignKey('people.id')), cls.__name__)

  @declared_attr
  def contact(cls):
    return db.relationship(
        'Person',
        uselist=False,
        foreign_keys='{}.contact_id'.format(cls.__name__))

  @declared_attr
  def secondary_contact(cls):
    return db.relationship(
        'Person',
        uselist=False,
        foreign_keys='{}.secondary_contact_id'.format(cls.__name__))

  @staticmethod
  def _extra_table_args(cls):
    return (
        db.Index('fk_{}_contact'.format(cls.__tablename__), 'contact_id'),
        db.Index('fk_{}_secondary_contact'.format(
            cls.__tablename__), 'secondary_contact_id'),
    )

  _publish_attrs = ['contact', 'secondary_contact']
  _aliases = {
      "contact": {
          "display_name": "Primary Contact",
          "filter_by": "_filter_by_contact",
      },
      "secondary_contact": {
          "display_name": "Secondary Contact",
          "filter_by": "_filter_by_secondary_contact",
      },
  }

  @classmethod
  def _filter_by_contact(cls, predicate):
    # dependency cycle mixins.py <~> person.py
    from ggrc.models.person import Person
    return Person.query.filter(
        (Person.id == cls.contact_id) &
        (predicate(Person.name) | predicate(Person.email))
    ).exists()

  @classmethod
  def _filter_by_secondary_contact(cls, predicate):
    # dependency cycle mixins.py <~> person.py
    from ggrc.models.person import Person
    return Person.query.filter(
        (Person.id == cls.secondary_contact_id) &
        (predicate(Person.name) | predicate(Person.email))
    ).exists()


class BusinessObject(Stateful, Noted, Described, Hyperlinked, WithContact,
                     Titled, Slugged):
  VALID_STATES = (
      'Draft',
      'Active',
      'Deprecated'
  )

# This class is just a marker interface/mixin to indicate that a model type
# supports custom attributes.


class TestPlanned(object):

  @declared_attr
  def test_plan(cls):
    return deferred(db.Column(db.Text), cls.__name__)

  # REST properties
  _publish_attrs = ['test_plan']
  _fulltext_attrs = ['test_plan']
  _sanitize_html = ['test_plan']
  _aliases = {"test_plan": "Test Plan"}


__all__ = [
    "Base",
    "BusinessObject",
    "ChangeTracked",
    "ContextRBAC",
    "CustomAttributable",
    "Described",
    "FinishedDate",
    "Hierarchical",
    "Hyperlinked",
    "Identifiable",
    "Noted",
    "Notifiable",
    "Slugged",
    "Stateful",
    "TestPlanned",
    "Timeboxed",
    "Titled",
    "VerifiedDate",
    "WithContact",
]
