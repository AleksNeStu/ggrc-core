# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""This module contains custom operators for query helper"""

# pylint: disable=unused-argument
import operator
import functools

import flask
import sqlalchemy
from sqlalchemy.orm import load_only

from ggrc import db
from ggrc import models
from ggrc.query import autocast
from ggrc.query.exceptions import BadQueryException
from ggrc.fulltext.mysql import MysqlRecordProperty as Record
from ggrc.login import is_creator
from ggrc.models import inflector
from ggrc.models import relationship_helper
from ggrc.snapshotter import rules
from ggrc.query import my_objects
from ggrc_basic_permissions import UserRole


GETATTR_WHITELIST = {
    "child_type",
    "id",
    "is_current",
    "program",
}


def validate(*required_fields):
  """Validate decorator.

  Checks if all of required fields are in exp dict.
  If there are some of required fields are not found then raise the
  BadQueryException.
  """
  required_fields_set = set(required_fields)
  required_tmpl = "`{field}` required for operation `{operation}`"

  def decorator(operation):
    """Decorator for operator."""
    @functools.wraps(operation)
    def decorated_operator(exp, *args, **kwargs):
      """Decorated operator """
      operation_name = exp["op"]["name"]
      error_fields = required_fields_set - set(exp.keys())
      if error_fields:
        raise BadQueryException("\n".join([
            required_tmpl.format(field=field, operation=operation_name)
            for field in error_fields]))
      return operation(exp, *args, **kwargs)
    return decorated_operator
  return decorator


def build_op_shortcut(predicate):
  """A shortcut to call build_op with default lhs and rhs."""
  def decorated(exp, object_class, target_class, query):
    """decorator for sended predicate"""
    key = exp['left'].lower()
    key, filter_by = target_class.attributes_map().get(key, (key, None))
    if callable(filter_by):
      return filter_by(lambda x: predicate(x, exp['right']))
    if key in GETATTR_WHITELIST:
      return predicate(getattr(object_class, key, None), exp['right'])
    return object_class.id.in_(
        db.session.query(Record.key).filter(
            Record.type == object_class.__name__,
            Record.property == key,
            predicate(Record.content, exp['right'])
        )
    )
  return decorated


@validate("left", "right")
@build_op_shortcut
def like(left, right):
  """Handle ~ operator with SQL LIKE."""
  return left.ilike(u"%{}%".format(right))


def reverse(operation):
  """ decorator that returns sa.not_ for sending operation"""
  def decorated(*args, **kwargs):
    return sqlalchemy.not_(operation(*args, **kwargs))
  return decorated


@validate("left", "right")
def is_filter(exp, object_class, target_class, query):
  """Handle 'is' operator.

  As in 'CA is empty' expression
  """
  if exp['right'] != u"empty":
    raise BadQueryException(
        u"Invalid operator near 'is': {}".format(exp['right']))
  left = exp['left'].lower()
  left, _ = target_class.attributes_map().get(left, (left, None))
  subquery = db.session.query(Record.key).filter(
      Record.type == object_class.__name__,
      Record.property == left,
      sqlalchemy.not_(
          sqlalchemy.or_(Record.content == u"", Record.content.is_(None))
      ),
  )
  return object_class.id.notin_(subquery)


def unknown(exp, object_class, target_class, query):
  """A fake operator for invalid operator names."""
  name = exp.get("op", {}).get("name")
  if name is None:
    msg = u"No operator name sent"
  else:
    msg = u"Unknown operator \"{}\"".format(name)
  raise BadQueryException(msg)


@validate("object_name", "ids")
def related_people(exp, object_class, target_class, query):
  """Get people related to the specified object.

  Returns the following people:
    for each object type: the users mapped via PeopleObjects,
    for Program: the users that have a Program-wide role,
    for Audit: the users that have a Program-wide or Audit-wide role,
    for Workflow: the users mapped via WorkflowPeople and
                  the users that have a Workflow-wide role.

  Args:
    related_type: the name of the class of the related objects.
    related_ids: the ids of related objects.

  Returns:
    sqlalchemy.sql.elements.BinaryExpression if an object of `object_class`
    is related to the given users.
  """
  if "Person" not in [object_class.__name__, exp['object_name']]:
    return sqlalchemy.sql.false()
  model = inflector.get_model(exp['object_name'])
  res = []
  res.extend(relationship_helper.person_object(
      object_class.__name__,
      exp['object_name'],
      exp['ids'],
  ))

  if exp['object_name'] in ('Program', 'Audit'):
    res.extend(
        db.session.query(UserRole.person_id).join(model, sqlalchemy.and_(
            UserRole.context_id == model.context_id,
            model.id.in_(exp['ids']),
        ))
    )

  if exp['object_name'] == "Audit":
    res.extend(
        db.session.query(UserRole.person_id).join(
            models.Program,
            UserRole.context_id == models.Program.context_id,
        ).join(model, sqlalchemy.and_(
            models.Program.id == model.program_id,
            model.id.in_(exp['ids']),
        ))
    )
  if "Workflow" in (object_class.__name__, exp['object_name']):
    try:
      from ggrc_workflows.models import (relationship_helper as
                                         wf_relationship_handler)
    except ImportError:
      # ggrc_workflows module is not enabled
      return sqlalchemy.sql.false()
    else:
      res.extend(wf_relationship_handler.workflow_person(
          object_class.__name__,
          exp['object_name'],
          exp['ids'],
      ))
  if res:
    return object_class.id.in_([obj[0] for obj in res])
  return sqlalchemy.sql.false()


@validate("ids")
def owned(exp, object_class, target_class, query):
  """Get objects for which the user is owner.

  Note: only the first id from the list of ids is used.

  Args:
    ids: the ids of owners.

  Returns:
    sqlalchemy.sql.elements.BinaryExpression if an object of `object_class`
    is owned by one of the given users.
  """
  res = db.session.query(
      my_objects.get_myobjects_query(
          types=[object_class.__name__],
          contact_id=exp['ids'][0],
          is_creator=is_creator(),
      ).alias().c.id
  )
  res = res.all()
  if res:
    return object_class.id.in_([obj.id for obj in res])
  return sqlalchemy.sql.false()


@validate("text")
def text_search(exp, object_class, target_class, query):
  """Filter by fulltext search.

  The search is done only in fields indexed for fulltext search.

  Args:
    text: the text we are searching for.

  Returns:
    sqlalchemy.sql.elements.BinaryExpression if an object of `object_class`
    has an indexed property that contains `text`.
  """
  return object_class.id.in_(
      db.session.query(Record.key).filter(
          Record.type == object_class.__name__,
          Record.content.ilike(u"%{}%".format(exp['text'])),
      ),
  )


@validate("object_name", "ids")
def similar(exp, object_class, target_class, query):
  """Filter by relationships similarity.

  Note: only the first id from the list of ids is used.

  Args:
    object_name: the name of the class of the objects to which similarity
                 will be computed.
    ids: the ids of similar objects of type `object_name`.

  Returns:
    sqlalchemy.sql.elements.BinaryExpression if an object of `object_class`
    is similar to one the given objects.
  """
  similar_class = inflector.get_model(exp['object_name'])
  if not hasattr(similar_class, "get_similar_objects_query"):
    raise BadQueryException(u"{} does not define weights to count "
                            u"relationships similarity"
                            .format(similar_class.__name__))
  similar_objects_query = similar_class.get_similar_objects_query(
      id_=exp['ids'][0],
      types=[object_class.__name__],
  )
  flask.g.similar_objects_query = similar_objects_query
  similar_objects_ids = [obj.id for obj in similar_objects_query]
  if similar_objects_ids:
    return object_class.id.in_(similar_objects_ids)
  return sqlalchemy.sql.false()


@validate("object_name", "ids")
def relevant(exp, object_class, target_class, query):
  "Filter by relevant object"
  if exp['object_name'] == "__previous__":
    exp = query[exp['ids'][0]]
  object_name = exp['object_name']
  ids = exp['ids']
  check_snapshots = (
      object_class.__name__ in rules.Types.scoped | rules.Types.trans_scope and
      object_name in rules.Types.all
  )
  check_direct = (not check_snapshots or
                  object_class.__name__ in rules.Types.trans_scope)

  result = set()

  if check_direct:
    result.update(*relationship_helper.get_ids_related_to(
        object_class.__name__,
        object_name,
        ids,
    ))

  if check_snapshots:
    snapshot_qs = models.Snapshot.query.filter(
        models.Snapshot.parent_type == models.Audit.__name__,
        models.Snapshot.child_type == object_name,
        models.Snapshot.child_id.in_(ids),
    ).options(
        load_only(models.Snapshot.id),
    ).distinct(
    ).subquery(
        "snapshot"
    )
    dest_qs = db.session.query(models.Relationship.source_id).filter(
        models.Relationship.destination_id == snapshot_qs.c.id,
        models.Relationship.destination_type == models.Snapshot.__name__,
        models.Relationship.source_type == object_class.__name__,
    )
    source_qs = db.session.query(models.Relationship.destination_id).filter(
        models.Relationship.source_id == snapshot_qs.c.id,
        models.Relationship.source_type == models.Snapshot.__name__,
        models.Relationship.destination_type == object_class.__name__,
    )
    ids_qs = dest_qs.union(source_qs)
    result.update(*ids_qs.all())

  if not result:
    return sqlalchemy.sql.false()

  return object_class.id.in_(result)


def build_expression(exp, object_class, target_class, query):
  """Make an SQLAlchemy filtering expression from exp expression tree."""
  if not exp:
    # empty expression doesn't required filter
    return
  if autocast.is_autocast_required_for(exp):
    exp = validate("left", "right")(autocast.autocast)(exp, target_class)
  if not exp:
    # empty expression after autocast is invalid and should raise an exception
    raise BadQueryException("Invalid filter data")
  operation = OPS.get(exp.get("op", {}).get("name")) or unknown
  return operation(exp, object_class, target_class, query)


@validate("left", "right")
def and_operation(exp, object_class, target_class, query):
  """Operator generate sqlalchemy for and operation"""
  return sqlalchemy.and_(
      build_expression(exp["left"], object_class, target_class, query),
      build_expression(exp["right"], object_class, target_class, query))


@validate("left", "right")
def or_operation(exp, object_class, target_class, query):
  """Operator generate sqlalchemy for or operation"""
  return sqlalchemy.or_(
      build_expression(exp["left"], object_class, target_class, query),
      build_expression(exp["right"], object_class, target_class, query))


EQ_OPERATOR = validate("left", "right")(build_op_shortcut(operator.eq))
LT_OPERATOR = validate("left", "right")(build_op_shortcut(operator.lt))
GT_OPERATOR = validate("left", "right")(build_op_shortcut(operator.gt))
LE_OPERATOR = validate("left", "right")(build_op_shortcut(operator.le))
GE_OPERATOR = validate("left", "right")(build_op_shortcut(operator.ge))

OPS = {
    "AND": and_operation,
    "OR": or_operation,
    "=": EQ_OPERATOR,
    "!=": reverse(EQ_OPERATOR),
    "~": like,
    "!~": reverse(like),
    "<": LT_OPERATOR,
    ">": GT_OPERATOR,
    "<=": LE_OPERATOR,
    ">=": GE_OPERATOR,
    "relevant": relevant,
    "similar": similar,
    "owned": owned,
    "related_people": related_people,
    "text_search": text_search,
    "is": is_filter,
}
