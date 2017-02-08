# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""This module contains a class for handling request queries."""

# flake8: noqa

import collections
import datetime
import functools
import operator

import flask
import sqlalchemy as sa

from ggrc import db
from ggrc import models
from ggrc.login import is_creator
from ggrc.fulltext.mysql import MysqlRecordProperty as Record
from ggrc.models import inflector
from ggrc.models.reflection import AttributeInfo
from ggrc.models.relationship_helper import RelationshipHelper
from ggrc.models.custom_attribute_definition import CustomAttributeDefinition
from ggrc.models.custom_attribute_value import CustomAttributeValue
from ggrc.converters import get_exportables
from ggrc.rbac import context_query_filter
from ggrc.utils import query_helpers, benchmark, convert_date_format
from ggrc_basic_permissions import UserRole


class BadQueryException(Exception):
  pass


# pylint: disable=too-few-public-methods

class QueryHelper(object):

  """Helper class for handling request queries

  Primary use for this class is to get list of object ids for each object type
  defined in the query. All objects must pass the query filters if they are
  defined.

  query object = [
    {
      object_name: search class name,
      permissions: either read or update, if none are given it defaults to read
      order_by: [
        {
          "name": the name of the field by which to do the sorting
          "desc": optional; if True, invert the sorting order
        }
      ]
      limit: [from, to] - limit the result list to a slice result[from, to]
      filters: {
        relevant_filters:
          these filters will return all ids of the "search class name" object
          that are mapped to objects defined in the dictionary inside the list.
          [ list of filters joined by OR expression
            [ list of filters joined by AND expression
              {
                "object_name": class of relevant object,
                "slugs": list of relevant object slugs,
                        optional and if exists will be converted into ids
                "ids": list of relevant object ids
              }
            ]
          ],
        object_filters: {
          TODO: allow filtering by title, description and other object fields
        }
      }
    }
  ]

  After the query is done (by `get_ids` method), the results are appended to
  each query object:

  query object with results = [
    {
      object_name: search class name,
      (all other object query fields)
      ids: [ list of filtered objects ids ]
    }
  ]

  The result fields may or may not be present in the resulting query depending
  on the attributes of `get` method.

  """

  def __init__(self, query, ca_disabled=False):
    self.object_map = {o.__name__: o for o in models.all_models.all_models}
    self.query = self._clean_query(query)
    self.ca_disabled = ca_disabled
    self._set_attr_name_map()
    self._count = 0

  def _set_attr_name_map(self):
    """ build a map for attributes names and display names

    Dict containing all display_name to attr_name mappings
    for all objects used in the current query
    Example:
        { Program: {"Program URL": "url", "Code": "slug", ...} ...}
    """
    self.attr_name_map = {}
    for object_query in self.query:
      object_name = object_query["object_name"]
      object_class = self.object_map[object_name]
      tgt_class = object_class
      if object_name == "Snapshot":
        child_type = self._get_snapshot_child_type(object_query)
        tgt_class = getattr(models.all_models, child_type, object_class)
      aliases = AttributeInfo.gather_aliases(tgt_class)
      self.attr_name_map[tgt_class] = {}
      for key, value in aliases.items():
        filter_by = None
        if isinstance(value, dict):
          filter_name = value.get("filter_by", None)
          if filter_name is not None:
            filter_by = getattr(tgt_class, filter_name, None)
          name = value["display_name"]
        else:
          name = value
        if name:
          self.attr_name_map[tgt_class][name.lower()] = (key.lower(),
                                                         filter_by)

  def _get_snapshot_child_type(self, object_query):
    """Return child_type for snapshot from a query"""
    return self._find_child_type(
        object_query.get("filters", {}).get("expression"), ""
    )

  def _find_child_type(self, expr, child_type):
    """Search for child_type recursively down the query expression."""
    if child_type:
      return child_type
    left, oper, right = expr.get("left"), expr.get("op"), expr.get("right")
    if oper.get("name") == "=":
      if left == "child_type" and isinstance(right, basestring):
        child_type = right
    else:
      for node in (left, right):
        if isinstance(node, dict):
          child_type = self._find_child_type(node, child_type)
    return child_type

  def _clean_query(self, query):
    """ sanitize the query object """
    for object_query in query:
      filters = object_query.get("filters", {}).get("expression")
      self._clean_filters(filters)
      self._macro_expand_object_query(object_query)
    return query

  def _clean_filters(self, expression):
    """Prepare the filter expression for building the query."""
    if not expression or not isinstance(expression, dict):
      return
    slugs = expression.get("slugs")
    if slugs:
      ids = expression.get("ids", [])
      ids.extend(self._slugs_to_ids(expression["object_name"], slugs))
      expression["ids"] = ids
    try:
      expression["ids"] = [int(id_) for id_ in expression.get("ids", [])]
    except ValueError as error:
      # catch missing relevant filter (undefined id)
      if expression.get("op", {}).get("name", "") == "relevant":
        raise BadQueryException(u"Invalid relevant filter for {}".format(
                                expression.get("object_name", "")))
      raise error
    self._clean_filters(expression.get("left"))
    self._clean_filters(expression.get("right"))

  def _expression_keys(self, exp):
    """Return the list of keys specified in the expression."""
    operator_name = exp.get("op", {}).get("name", None)
    if operator_name in ["AND", "OR"]:
      return self._expression_keys(exp["left"]).union(
          self._expression_keys(exp["right"]))
    left = exp.get("left", None)
    if left is not None and isinstance(left, collections.Hashable):
      return set([left])
    else:
      return set()

  def _macro_expand_object_query(self, object_query):
    """Expand object query."""
    def expand_task_dates(exp):
      """Parse task dates from the specified expression."""
      if not isinstance(exp, dict) or "op" not in exp:
        return
      operator_name = exp["op"]["name"]
      if operator_name in ["AND", "OR"]:
        expand_task_dates(exp["left"])
        expand_task_dates(exp["right"])
      elif isinstance(exp["left"], (str, unicode)):
        key = exp["left"]
        if key in ["start", "end"]:
          parts = exp["right"].split("/")
          if len(parts) == 3:
            try:
              month, day, year = [int(part) for part in parts]
            except Exception:
              raise BadQueryException(
                  "Date must consist of numbers")
            exp["left"] = key + "_date"
            exp["right"] = datetime.date(year, month, day)
          elif len(parts) == 2:
            month, day = parts
            exp["op"] = {"name": u"AND"}
            exp["left"] = {
                "op": {"name": operator_name},
                "left": "relative_" + key + "_month",
                "right": month,
            }
            exp["right"] = {
                "op": {"name": operator_name},
                "left": "relative_" + key + "_day",
                "right": day,
            }
          elif len(parts) == 1:
            exp["left"] = "relative_" + key + "_day"
          else:
            raise BadQueryException(u"Field {} should be a date of one of the"
                                    u" following forms: DD, MM/DD, MM/DD/YYYY"
                                    .format(key))

    if object_query["object_name"] == "TaskGroupTask":
      filters = object_query.get("filters")
      if filters is not None:
        exp = filters["expression"]
        keys = self._expression_keys(exp)
        if "start" in keys or "end" in keys:
          expand_task_dates(exp)

  def get_ids(self):
    """Get a list of filtered object IDs.

    self.query should contain a list of queries for different objects which
    will get evaluated and turned into a list of object IDs.

    Returns:
      list of dicts: same query as the input with all ids that match the filter
    """
    for object_query in self.query:
      ids = self._get_ids(object_query)
      object_query["ids"] = ids
    return self.query

  @staticmethod
  def _get_type_query(model, permission_type):
    """Filter by contexts and resources

    Prepare query to filter models based on the available contexts and
    resources for the given type of object.
    """
    contexts, resources = query_helpers.get_context_resource(
        model_name=model.__name__, permission_type=permission_type
    )

    if contexts is not None:
      if resources:
        resource_sql = model.id.in_(resources)
      else:
        resource_sql = sa.sql.false()

      return sa.or_(
          context_query_filter(model.context_id, contexts),
          resource_sql)

  def _get_objects(self, object_query):
    """Get a set of objects described in the filters."""

    with benchmark("Get ids: _get_objects -> _get_ids"):
      ids = self._get_ids(object_query)
    if not ids:
      return set()

    object_name = object_query["object_name"]
    object_class = self.object_map[object_name]
    query = object_class.eager_query()
    query = query.filter(object_class.id.in_(ids))

    with benchmark("Get objects by ids: _get_objects -> obj in query"):
      id_object_map = {obj.id: obj for obj in query}

    with benchmark("Order objects by ids: _get_objects"):
      objects = [id_object_map[id_] for id_ in ids]

    return objects

  def _get_ids(self, object_query):
    """Get a set of ids of objects described in the filters."""

    object_name = object_query["object_name"]
    expression = object_query.get("filters", {}).get("expression")

    if expression is None:
      return set()
    object_class = self.object_map[object_name]
    query = db.session.query(object_class.id)

    tgt_class = object_class
    if object_name == "Snapshot":
      child_type = self._get_snapshot_child_type(object_query)
      tgt_class = getattr(models.all_models, child_type, object_class)

    requested_permissions = object_query.get("permissions", "read")
    with benchmark("Get permissions: _get_ids > _get_type_query"):
      type_query = self._get_type_query(object_class, requested_permissions)
      if type_query is not None:
        query = query.filter(type_query)
    with benchmark("Parse filter query: _get_ids > _build_expression"):
      filter_expression = self._build_expression(
          expression,
          object_class,
          tgt_class
      )
      if filter_expression is not None:
        query = query.filter(filter_expression)
    if object_query.get("order_by"):
      with benchmark("Sorting: _get_ids > order_by"):
        query = self._apply_order_by(
            object_class,
            query,
            object_query["order_by"],
        )
    with benchmark("Apply limit"):
      limit = object_query.get("limit")
      if limit:
        ids, total = self._apply_limit(query, limit)
      else:
        ids = [obj.id for obj in query]
        total = len(ids)
      object_query["total"] = total

    if hasattr(flask.g, "similar_objects_query"):
      # delete similar_objects_query for the case when several queries are
      # POSTed in one request, the first one filters by similarity and the
      # second one doesn't but tries to sort by __similarity__
      delattr(flask.g, "similar_objects_query")
    return ids

  @staticmethod
  def _apply_limit(query, limit):
    """Apply limits for pagination.

    Args:
      query: filter query;
      limit: a tuple of indexes in format (from, to); objects is sliced to
            objects[from, to].

    Returns:
      matched objects ids and total count.
    """
    try:
      first, last = limit
      first, last = int(first), int(last)
    except (ValueError, TypeError):
      raise BadQueryException("Invalid limit operator. Integers expected.")

    if first < 0 or last < 0:
      raise BadQueryException("Limit cannot contain negative numbers.")
    elif first >= last:
      raise BadQueryException("Limit start should be smaller than end.")
    else:
      page_size = last - first
      with benchmark("Apply limit: _apply_limit > query_limit"):
        # Note: limit request syntax is limit:[0,10]. We are counting
        # offset from 0 as the offset of the initial row for sql is 0 (not 1).
        ids = [obj.id for obj in query.limit(page_size).offset(first)]
      with benchmark("Apply limit: _apply_limit > query_count"):
        if len(ids) < page_size:
          total = len(ids) + first
        else:
          # Note: using func.count() as query.count() is generating additional
          # subquery
          count_q = query.statement.with_only_columns([sa.func.count()])
          total = db.session.execute(count_q).scalar()

    return ids, total

  def _apply_order_by(self, model, query, order_by):
    """Add ordering parameters to a query for objects.

    This works only on direct model properties and related objects defined with
    foreign keys and fails if any CAs are specified in order_by.

    Args:
      model: the model instances of which are requested in query;
      query: a query to get objects from the db;
      order_by: a list of dicts with keys "name" (the name of the field by which
                to sort) and "desc" (optional; do reverse sort if True).

    If order_by["name"] == "__similarity__" (a special non-field value),
    similarity weights returned by get_similar_objects_query are used for
    sorting.

    If sorting by a relationship field is requested, the following sorting is
    applied:
    1. If the field is a relationship to a Titled model, sort by its title.
    2. If the field is a relationship to Person, sort by its name or email (if
       name is None or empty string for a person object).
    3. Otherwise, raise a NotImplementedError.

    Returns:
      the query with sorting parameters.
    """
    def sorting_field_for_person(person):
      """Get right field to sort people by: name if defined or email."""
      return sa.case([(sa.not_(sa.or_(person.name.is_(None),
                                      person.name == '')),
                       person.name)],
                     else_=person.email)

    def joins_and_order(clause):
      """Get join operations and ordering field from item of order_by list.

      Args:
        clause: {"name": the name of model's field,
                 "desc": reverse sort on this field if True}

      Returns:
        ([joins], order) - a tuple of joins required for this ordering to work
                           and ordering clause itself; join is None if no join
                           required or [(aliased entity, relationship field)]
                           if joins required.
      """
      def by_similarity():
        """Join similar_objects subquery, order by weight from it."""
        join_target = flask.g.similar_objects_query.subquery()
        join_condition = model.id == join_target.c.id
        joins = [(join_target, join_condition)]
        order = join_target.c.weight
        return joins, order

      def by_ca():
        """Join fulltext index table, order by indexed CA value."""
        alias = sa.orm.aliased(Record, name=u"fulltext_{}".format(self._count))
        joins = [(alias, sa.and_(
            alias.key == model.id,
            alias.type == model.__name__,
            alias.property == key)
        )]
        order = alias.content
        return joins, order

      def by_foreign_key():
        """Join the related model, order by title or name/email."""
        related_model = attr.property.mapper.class_
        if issubclass(related_model, models.mixins.Titled):
          joins = [(alias, _)] = [(sa.orm.aliased(attr), attr)]
          order = alias.title
        elif issubclass(related_model, models.Person):
          joins = [(alias, _)] = [(sa.orm.aliased(attr), attr)]
          order = sorting_field_for_person(alias)
        else:
          raise NotImplementedError(u"Sorting by {model.__name__} is "
                                    u"not implemented yet."
                                    .format(model=related_model))
        return joins, order

      def by_m2m():
        """Join the Person model, order by name/email.

        Implemented only for ObjectOwner mapping.
        """
        if issubclass(attr.target_class, models.object_owner.ObjectOwner):
          # NOTE: In the current implementation we sort only by the first
          # assigned owner if multiple owners defined
          oo_alias_1 = sa.orm.aliased(models.object_owner.ObjectOwner)
          oo_alias_2 = sa.orm.aliased(models.object_owner.ObjectOwner)
          oo_subq = db.session.query(
              oo_alias_1.ownable_id,
              oo_alias_1.ownable_type,
              oo_alias_1.person_id,
          ).filter(
              oo_alias_1.ownable_type == model.__name__,
              ~sa.exists().where(sa.and_(
                  oo_alias_2.ownable_id == oo_alias_1.ownable_id,
                  oo_alias_2.ownable_type == oo_alias_1.ownable_type,
                  oo_alias_2.id < oo_alias_1.id,
              )),
          ).subquery()

          owner = sa.orm.aliased(models.Person, name="owner")

          joins = [
              (oo_subq, sa.and_(model.__name__ == oo_subq.c.ownable_type,
                                model.id == oo_subq.c.ownable_id)),
              (owner, oo_subq.c.person_id == owner.id),
          ]

          order = sorting_field_for_person(owner)
        else:
          raise NotImplementedError(u"Sorting by m2m-field '{key}' "
                                    u"is not implemented yet."
                                    .format(key=key))
        return joins, order

      # transform clause["name"] into a model's field name
      key = clause["name"].lower()

      if key == "__similarity__":
        # special case
        if hasattr(flask.g, "similar_objects_query"):
          joins, order = by_similarity()
        else:
          raise BadQueryException("Can't order by '__similarity__' when no "
                                  "'similar' filter was applied.")
      else:
        key, _ = self.attr_name_map[model].get(key, (key, None))
        attr = getattr(model, key.encode('utf-8'), None)
        if attr is None:
          # non object attributes are treated as custom attributes
          self._count += 1
          joins, order = by_ca()
        elif (isinstance(attr, sa.orm.attributes.InstrumentedAttribute) and
                isinstance(attr.property,
                           sa.orm.properties.RelationshipProperty)):
          joins, order = by_foreign_key()
        elif isinstance(attr, sa.ext.associationproxy.AssociationProxy):
          joins, order = by_m2m()
        else:
          # a simple attribute
          joins, order = None, attr

      if clause.get("desc", False):
        order = order.desc()

      return joins, order

    join_lists, orders = zip(*[joins_and_order(clause) for clause in order_by])
    for join_list in join_lists:
      if join_list is not None:
        for join in join_list:
          query = query.outerjoin(*join)

    return query.order_by(*orders)

  def _build_expression(self, exp, object_class, tgt_class):
    """Make an SQLAlchemy filtering expression from exp expression tree."""
    if "op" not in exp:
      return None

    def autocast(o_key, operator_name, value):
      """Try to guess the type of `value` and parse it from the string.

      Args:
        o_key (basestring): the name of the field being compared; the `value`
                            is converted to the type of that field.
        operator_name: the name of the operator being applied.
        value: the value being compared.

      Returns:
        a list of one or several possible meanings of `value` type compliant
        with `getattr(object_class, o_key)`.
      """
      def has_date_or_non_date_cad(title, definition_type):
        """Check if there is a date and a non-date CA named title.

        Returns:
          (bool, bool) - flags indicating the presence of date and non-date CA.
        """
        cad_query = db.session.query(CustomAttributeDefinition).filter(
          CustomAttributeDefinition.title == title,
          CustomAttributeDefinition.definition_type == definition_type,
        )
        date_cad = bool(cad_query.filter(
          CustomAttributeDefinition.
              attribute_type == CustomAttributeDefinition.ValidTypes.DATE,
        ).count())
        non_date_cad = bool(cad_query.filter(
          CustomAttributeDefinition.
              attribute_type != CustomAttributeDefinition.ValidTypes.DATE,
        ).count())
        return date_cad, non_date_cad

      if not isinstance(o_key, basestring):
        return [value]
      key, custom_filter = (self.attr_name_map[tgt_class].get(o_key,
                                                              (o_key, None)))

      date_attr = date_cad = non_date_cad = False
      try:
        attr_type = getattr(tgt_class, key).property.columns[0].type
      except AttributeError:
        date_cad, non_date_cad = has_date_or_non_date_cad(
            title=key,
            definition_type=tgt_class.__name__,
        )
        if not (date_cad or non_date_cad) and not custom_filter:
          # TODO: this logic fails on CA search for Snapshots
          pass
          # no CA with this name and no custom filter for the field
          # raise BadQueryException(u"Model {} has no field or CA {}"
          #                         .format(object_class.__name__, o_key))
      else:
        if isinstance(attr_type, sa.sql.sqltypes.Date):
          date_attr = True

      converted_date = None
      if (date_attr or date_cad) and isinstance(value, basestring):
        try:
          converted_date = convert_date_format(
              value,
              CustomAttributeValue.DATE_FORMAT_US,
              CustomAttributeValue.DATE_FORMAT_ISO,
          )
        except (TypeError, ValueError):
          # wrong format or not a date
          if not non_date_cad:
            # o_key is not a non-date CA
            raise BadQueryException(u"Field '{}' expects a '{}' date"
                                    .format(
                                        o_key,
                                        CustomAttributeValue.DATE_FORMAT_US,
                                    ))


      if date_attr or (date_cad and not non_date_cad):
        # Filter by converted date
        return [converted_date]
      elif date_cad and non_date_cad and converted_date is None:
        # Filter by unconverted string as date conversion was unsuccessful
        return [value]
      elif date_cad and non_date_cad:
        if operator_name in ("<", ">"):
          # "<" and ">" works incorrectly when searching by CA in both formats
          return [converted_date]
        else:
          # Since we can have two local CADs with same name when one is Date
          # and another is Text, we should handle the case when the user wants
          # to search by the Text CA that should not be converted
          return [converted_date, value]
      else:
        # Filter by unconverted string
        return [value]

    def _backlink(object_name, ids):
      """Convert ("__previous__", [query_id]) into (model_name, ids).

      If `object_name` == "__previous__", return `object_name` and resulting
      `ids` from a previous query with index `ids[0]`.

      Example:
        self.query[0] = {object_name: "Assessment",
                         type: "ids",
                         expression: {something}}
        _backlink("__previous__", [0]) will return ("Assessment",
                                                    ids returned by query[0])

      Returns:
        (object_name, ids) if object_name != "__previous__",
        (self.query[ids[0]]["object_name"],
         self.query[ids[0]]["ids"]) otherwise.
      """

      if object_name == "__previous__":
        previous_query = self.query[ids[0]]
        return (previous_query["object_name"], previous_query["ids"])
      else:
        return object_name, ids

    def relevant(object_name, ids):
      """Filter by relevant object.

      Args:
        object_name (basestring): the name of the related model.
        ids ([int]): the ids of related objects of type `object_name`.

      Returns:
        sqlalchemy.sql.elements.BinaryExpression if an object of `object_class`
        is related (via a Relationship or another m2m) to one the given objects.
      """
      return object_class.id.in_(
          RelationshipHelper.get_ids_related_to(
              object_class.__name__,
              object_name,
              ids,
          )
      )

    def similar(object_name, ids):
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
      similar_class = self.object_map[object_name]
      if not hasattr(similar_class, "get_similar_objects_query"):
        return BadQueryException(u"{} does not define weights to count "
                                 u"relationships similarity"
                                 .format(similar_class.__name__))
      similar_objects_query = similar_class.get_similar_objects_query(
          id_=ids[0],
          types=[object_class.__name__],
      )
      flask.g.similar_objects_query = similar_objects_query
      similar_objects_ids = [obj.id for obj in similar_objects_query]
      if similar_objects_ids:
        return object_class.id.in_(similar_objects_ids)
      return sa.sql.false()

    def unknown():
      """A fake operator for invalid operator names."""
      raise BadQueryException(u"Unknown operator \"{}\""
                              .format(exp["op"]["name"]))

    def default_filter_by(object_class, key, predicate):
      """Default filter option that tries to mach predicate in fulltext index.

      This function tries to match the predicate for a give key with entries in
      the full text index table.

      Args:
        object_class: class of the object we are querying for.
        key: string containing attribute name on which we are filtering.
        predicate: function containing the correct comparison predicate for
          the attribute value.

      Returs:
        Query predicate if the given predicate matches a value for the correct
          custom attribute.
      """
      return object_class.id.in_(db.session.query(Record.key).filter(
          Record.type == object_class.__name__,
          Record.property == key,
          predicate(Record.content)
      ))

    def with_key(key, predicate):
      """Apply keys to the filter expression.

      Args:
        key: string containing attribute name on which we are filtering.
        predicate: function containing a comparison for attribute value.

      Returns:
        sqlalchemy.sql.elements.BinaryExpression with:
          `filter_by(predicate)` if there is custom filtering logic for `key`,
          `predicate(getattr(object_class, key))` for own attributes,
          `predicate(value of corresponding custom attribute)` otherwise.
      """
      key = key.lower()
      key, filter_by = self.attr_name_map[
          tgt_class].get(key, (key, None))
      if callable(filter_by):
        return filter_by(predicate)
      else:
        attr = getattr(object_class, key, None)
        if attr:
          return predicate(attr)
        else:
          return default_filter_by(object_class, key, predicate)

    lift_bin = lambda f: f(self._build_expression(exp["left"], object_class,
                                                  tgt_class),
                           self._build_expression(exp["right"], object_class,
                                                  tgt_class))

    def text_search(text):
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
              Record.content.ilike(u"%{}%".format(text)),
          ),
      )

    rhs_variants = lambda: autocast(exp["left"],
                                    exp["op"]["name"],
                                    exp["right"])

    def owned(ids):
      """Get objects for which the user is owner.

      Note: only the first id from the list of ids is used.

      Args:
        ids: the ids of owners.

      Returns:
        sqlalchemy.sql.elements.BinaryExpression if an object of `object_class`
        is owned by one of the given users.
      """
      res = db.session.query(
        query_helpers.get_myobjects_query(
            types=[object_class.__name__],
            contact_id=ids[0],
            is_creator=is_creator(),
        ).alias().c.id
      )
      res = res.all()
      if res:
        return object_class.id.in_([obj.id for obj in res])
      return sa.sql.false()

    def related_people(related_type, related_ids):
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
      if "Person" not in [object_class.__name__, related_type]:
        return sa.sql.false()
      model = inflector.get_model(related_type)
      res = []
      res.extend(RelationshipHelper.person_object(
          object_class.__name__,
          related_type,
          related_ids,
      ))

      if related_type in ('Program', 'Audit'):
        res.extend(
            db.session.query(UserRole.person_id).join(model, sa.and_(
                UserRole.context_id == model.context_id,
                model.id.in_(related_ids),
            ))
        )

        if related_type == "Audit":
          res.extend(
              db.session.query(UserRole.person_id).join(
                  models.Program,
                  UserRole.context_id == models.Program.context_id,
              ).join(model, sa.and_(
                  models.Program.id == model.program_id,
                  model.id.in_(related_ids),
              ))
          )
      if "Workflow" in (object_class.__name__, related_type):
        try:
          from ggrc_workflows.models import (relationship_helper as
                                             wf_relationship_handler)
        except ImportError:
          # ggrc_workflows module is not enabled
          return sa.sql.false()
        else:
          res.extend(wf_relationship_handler.workflow_person(
              object_class.__name__,
              related_type,
              related_ids,
          ))
      if res:
        return object_class.id.in_([obj[0] for obj in res])
      return sa.sql.false()

    def build_op(exp_left, predicate, rhs_variants):
      """Apply predicate to `exp_left` and each `rhs` and join them with SQL OR.

      Args:
        exp_left: description of left operand from the expression tree.
        predicate: a comparison function between a field and a value.
        rhs_variants: a list of possible interpretations of right operand,
                      typically a list of strings.

      Raises:
        ValueError if rhs_variants is empty.

      Returns:
        sqlalchemy.sql.elements.BinaryExpression if predicate matches exp_left
        and any of rhs variants.
      """

      if not rhs_variants:
        raise ValueError("Expected non-empty sequence in 'rhs_variants', got "
                         "{!r} instead".format(rhs_variants))
      return with_key(
          exp_left,
          lambda lhs: functools.reduce(
              sa.or_,
              (predicate(lhs, rhs) for rhs in rhs_variants),
          ),
      )

    def build_op_shortcut(predicate):
      """A shortcut to call build_op with default lhs and rhs."""
      return build_op(exp["left"], predicate, rhs_variants())

    def like(left, right):
      """Handle ~ operator with SQL LIKE."""
      return left.ilike(u"%{}%".format(right))

    ops = {
        "AND": lambda: lift_bin(sa.and_),
        "OR": lambda: lift_bin(sa.or_),

        "=": lambda: build_op_shortcut(operator.eq),
        "!=": lambda: sa.not_(build_op_shortcut(operator.eq)),
        "~": lambda: build_op_shortcut(like),
        "!~": lambda: sa.not_(build_op_shortcut(like)),
        "<": lambda: build_op_shortcut(operator.lt),
        ">": lambda: build_op_shortcut(operator.gt),

        "relevant": lambda: relevant(*_backlink(exp["object_name"],
                                                exp["ids"])),
        "text_search": lambda: text_search(exp["text"]),
        "similar": lambda: similar(exp["object_name"], exp["ids"]),
        "owned": lambda: owned(exp["ids"]),
        "related_people": lambda: related_people(exp["object_name"],
                                                 exp["ids"]),
    }

    return ops.get(exp["op"]["name"], unknown)()

  def _slugs_to_ids(self, object_name, slugs):
    """Convert SLUG to proper ids for the given objec."""
    object_class = self.object_map.get(object_name)
    if not object_class:
      return []
    ids = [c.id for c in object_class.query.filter(
        object_class.slug.in_(slugs)).all()]
    return ids
