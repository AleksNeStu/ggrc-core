# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>


"""GGRC Collection REST services implementation. Common to all GGRC collection
resources.
"""

import datetime
import hashlib
import itertools
import json
import time
from logging import getLogger
from collections import defaultdict
from exceptions import TypeError
from wsgiref.handlers import format_date_time
from urllib import urlencode

from flask import url_for, request, current_app, g, has_request_context
from flask.views import View
from flask.ext.sqlalchemy import Pagination
import sqlalchemy.orm.exc
from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.expression import tuple_
from werkzeug.exceptions import BadRequest, Forbidden

import ggrc.builder.json
import ggrc.models
from ggrc import db, utils
from ggrc.utils import as_json, benchmark
from ggrc.fulltext import get_indexer
from ggrc.login import get_current_user_id, get_current_user
from ggrc.models.cache import Cache
from ggrc.models.event import Event
from ggrc.models.revision import Revision
from ggrc.models.exceptions import ValidationError, translate_message
from ggrc.rbac import permissions, context_query_filter
from ggrc.services.attribute_query import AttributeQueryBuilder
from ggrc.services import signals
from ggrc.models.background_task import BackgroundTask, create_task
from ggrc.query import utils as query_utils
from ggrc import settings


# pylint: disable=invalid-name
logger = getLogger(__name__)


CACHE_EXPIRY_COLLECTION = 60


def _get_cache_manager():
  from ggrc.cache import CacheManager, MemCache
  cache_manager = CacheManager()
  cache_manager.initialize(MemCache())
  return cache_manager


def get_cache_key(obj, type=None, id=None):
  """Returns a string identifier for the specified object or stub.

  `obj` can be:
    <db.Model> -- declarative model instance
    (type, id) -- tuple
    { 'type': type, 'id': id } -- dict
  """
  if isinstance(obj, tuple):
    type, id = obj
  elif isinstance(obj, dict):
    type = obj.get('type', None)
    id = obj.get('id', None)
  if isinstance(type, (str, unicode)):
    model = ggrc.models.get_model(type)
    assert model is not None, "Invalid model name: {}".format(type)
    type = ggrc.models.get_model(type)._inflector.table_plural
  if not isinstance(obj, (tuple, dict)):
    if type is None:
      type = obj._inflector.table_plural
    if id is None:
      id = obj.id
  return 'collection:{type}:{id}'.format(type=type, id=id)


def get_cache_class(obj):
  return obj.__class__.__name__


def get_related_keys_for_expiration(context, o):
  cls = get_cache_class(o)
  keys = []
  mappings = context.cache_manager.supported_mappings.get(cls, [])
  if len(mappings) > 0:
    for (cls, attr, polymorph) in mappings:
      if polymorph:
        key = get_cache_key(
            None,
            type=getattr(o, '{0}_type'.format(attr)),
            id=getattr(o, '{0}_id'.format(attr)))
        keys.append(key)
      else:
        obj = getattr(o, attr, None)
        if obj:
          if isinstance(obj, list):
            for inner_o in obj:
              key = get_cache_key(inner_o)
              keys.append(key)
          else:
            key = get_cache_key(obj)
            keys.append(key)
  return keys


def set_ids_for_new_custom_attributes(parent_obj):
  """
  When we are creating custom attribute values and definitions for
  POST requests, parent object ID is not yet defined. This is why we update
  custom attribute values at this point and set the correct attributable_id

  Args:
    parent_obj: parent object to be set as attributable

  Returns:
    None
  """
  if not hasattr(parent_obj, "PER_OBJECT_CUSTOM_ATTRIBUTABLE"):
    return
  for obj in get_modified_objects(db.session).new:
    if obj.type == "CustomAttributeValue":
      obj.attributable = parent_obj
    elif obj.type == "CustomAttributeDefinition":
      obj.definition = parent_obj


def memcache_mark_for_deletion(context, objects_to_mark):
  """
  Mark objects for deletion from memcache

  Args:
    context: application context
    objects_to_mark: A list of objects to be deleted from memcache

  Returns:
    None
  """
  for o, _ in objects_to_mark:
    cls = get_cache_class(o)
    if cls in context.cache_manager.supported_classes:
      key = get_cache_key(o)
      context.cache_manager.marked_for_delete.append(key)
      context.cache_manager.marked_for_delete.extend(
          get_related_keys_for_expiration(context, o))


def update_memcache_before_commit(context, modified_objects, expiry_time):
  """
  Preparing the memccache entries to be updated before DB commit
  Also update the memcache to indicate the status cache operation
  'InProgress' waiting for DB commit
  Raises Exception on failures, cannot proceed with DB commit

  Args:
    context: POST/PUT/DELETE HTTP request or import Converter contextual object
    modified_objects:  objects in cache maintained prior to committing to DB
    expiry_time: Expiry time specified for memcache ADD and DELETE
  Returns:
    None

  """
  if getattr(settings, 'MEMCACHE_MECHANISM', False) is False:
    return

  context.cache_manager = _get_cache_manager()

  if modified_objects is not None:
    if len(modified_objects.new) > 0:
      memcache_mark_for_deletion(context, modified_objects.new.items())

    if len(modified_objects.dirty) > 0:
      memcache_mark_for_deletion(context, modified_objects.dirty.items())

    if len(modified_objects.deleted) > 0:
      memcache_mark_for_deletion(context, modified_objects.deleted.items())

  status_entries = {}
  for key in context.cache_manager.marked_for_delete:
    build_cache_status(status_entries, 'DeleteOp:' + key,
                       expiry_time, 'InProgress')
  if len(status_entries) > 0:
    logger.info("CACHE: status entries: %s", status_entries)
    ret = context.cache_manager.bulk_add(status_entries, expiry_time)
    if ret is not None and len(ret) == 0:
      pass
    else:
      logger.error('CACHE: Unable to add status for newly created entries %s',
                   ret)


def update_memcache_after_commit(context):
  """
  The memccache entries is updated after DB commit
  Logs error if there are errors in updating entries in cache

  Args:
    context: POST/PUT/DELETE HTTP request or import Converter contextual object
    modified_objects:  objects in cache maintained prior to committing to DB
  Returns:
    None

  """
  if getattr(settings, 'MEMCACHE_MECHANISM', False) is False:
    return

  if context.cache_manager is None:
    logger.error("CACHE: Error in initiaizing cache manager")
    return

  cache_manager = context.cache_manager

  related_objs = list()
  for val in getattr(g, "referenced_objects", {}).itervalues():
    obj_list = val.values()
    if obj_list:
      related_objs.append((obj_list[0], None))
  memcache_mark_for_deletion(context, related_objs)

  # TODO(dan): check for duplicates in marked_for_delete
  if len(cache_manager.marked_for_delete) > 0:
    delete_result = cache_manager.bulk_delete(
        cache_manager.marked_for_delete, 0)
    # TODO(dan): handling failure including network errors,
    #            currently we log errors
    if delete_result is not True:
      logger.error("CACHE: Failed to remove collection from cache")

  status_entries = []
  for key in cache_manager.marked_for_delete:
    status_entries.append('DeleteOp:' + str(key))
  if len(status_entries) > 0:
    delete_result = cache_manager.bulk_delete(status_entries, 0)
    # TODO(dan): handling failure including network errors,
    #            currently we log errors
    if delete_result is not True:
      logger.error("CACHE: Failed to remove status entries from cache")

  clear_permission_cache()
  cache_manager.clear_cache()


def build_cache_status(data, key, expiry_timeout, status):
  """
  Build the dictionary for storing operational status of cache

  Args:
    data: dictionary to update
    key: key to dictionary
    expiry_timeout: timeout for expiry cache
    status: Update status entry, e.g.InProgress
  Returns:
    None
  """
  data[key] = {'expiry': expiry_timeout, 'status': status}


def inclusion_filter(obj):
  return permissions.is_allowed_read(obj.__class__.__name__,
                                     obj.id, obj.context_id)


def get_cache(create=False):
  """
  Retrieves the cache from the Flask global object. The create arg
  indicates if a new cache should be created if none exists. If we
  are not in a request context, no cache is created (return None).
  """
  if has_request_context():
    cache = getattr(g, 'cache', None)
    if cache is None and create:
      cache = g.cache = Cache()
    return cache
  else:
    logger.warning("No request context - no cache created")
    return None


def get_modified_objects(session):
  session.flush()
  cache = get_cache()
  if cache:
    return cache.copy()
  else:
    return None


def update_snapshot_index(session, cache):
  """Update fulltext index records for cached snapshtos."""
  from ggrc.snapshotter.indexer import reindex_snapshots
  if cache is None:
    return
  objs = itertools.chain(cache.new, cache.dirty, cache.deleted)
  reindex_snapshots_ids = [o.id for o in objs if o.type == "Snapshot"]
  get_indexer().delete_records_by_ids("Snapshot",
                                      reindex_snapshots_ids,
                                      commit=False)
  reindex_snapshots(reindex_snapshots_ids)


def _revision_generator(user_id, action, objects):
  for obj in objects:
    yield Revision(obj, user_id, action, obj.log_json())


def _get_log_revisions(current_user_id, obj=None, force_obj=False):
  """Generate and return revisions for all cached objects."""
  revisions = []
  cache = get_cache()
  if not cache:
    return revisions
  modified_objects = set(cache.dirty)
  new_objects = set(cache.new)
  delete_objects = set(cache.deleted)
  all_edited_objects = itertools.chain(cache.new, cache.dirty, cache.deleted)
  for o in all_edited_objects:
    if o.type == "ObjectFolder" and o.folderable:
      modified_objects.add(o.folderable)
    if o.type == "Relationship" and o.get_related_for("Document"):
      documentable = o.get_related_for("Document")
      document = o.get_related_for(documentable.type)
      if o in new_objects and document not in documentable.documents:
        documentable.documents.append(document)
      if o in delete_objects and document in documentable.documents:
        documentable.documents.remove(document)
      if (
              documentable not in new_objects and
              documentable not in delete_objects):
         modified_objects.add(documentable)

  revisions.extend(_revision_generator(
      current_user_id, "created", cache.new
  ))
  revisions.extend(_revision_generator(
      current_user_id, "modified", modified_objects
  ))
  if force_obj and obj is not None and obj not in cache.dirty:
    # If the ``obj`` has been updated, but only its custom attributes have
    # been changed, then this object will not be added into
    # ``cache.dirty set``. So that its revision will not be created.
    # The ``force_obj`` flag solves the issue, but in a bit dirty way.
    revision = Revision(obj, current_user_id, 'modified', obj.log_json())
    revisions.append(revision)
  revisions.extend(_revision_generator(
      current_user_id, "deleted", cache.deleted
  ))
  return revisions


def log_event(session, obj=None, current_user_id=None, flush=True,
              force_obj=False):
  """Logs an event on object `obj`.

  Args:
    session: Current SQLAlchemy session (db.session)
    obj: object on which some operation took place
    current_user_id: ID of the user performing operation
    flush: If set to true, flush the session at the start
    force_obj: Used in case of custom attribute changes to force revision write
  Returns:
    Uncommitted models.Event instance
  """
  event = None
  if flush:
    session.flush()
  if current_user_id is None:
    current_user_id = get_current_user_id()
  revisions = _get_log_revisions(current_user_id, obj=obj, force_obj=force_obj)
  if obj is None:
    resource_id = 0
    resource_type = None
    action = 'BULK'
    context_id = 0
  else:
    resource_id = obj.id
    resource_type = str(obj.__class__.__name__)
    action = request.method
    context_id = obj.context_id
  if revisions:
    event = Event(
        modified_by_id=current_user_id,
        action=action,
        resource_id=resource_id,
        resource_type=resource_type,
        context_id=context_id)
    event.revisions = revisions
    session.add(event)
  return event


def clear_permission_cache():
  if not getattr(settings, 'MEMCACHE_MECHANISM', False):
    return
  cache = _get_cache_manager().cache_object.memcache_client
  cached_keys_set = cache.get('permissions:list') or set()
  cached_keys_set.add('permissions:list')
  # We delete all the cached user permissions as well as
  # the permissions:list value itself
  cache.delete_multi(cached_keys_set)


class ModelView(View):
  """Basic view handler for all models"""
  # pylint: disable=protected-access
  # access to _sa_class_manager is needed for fetching the right mapper
  DEFAULT_PAGE_SIZE = 20
  MAX_PAGE_SIZE = 100
  pk = 'id'
  pk_type = 'int'

  _model = None

  # Simple accessor properties
  @property
  def request(self):
    return request

  @property
  def model(self):
    return self._model

  @property
  def modified_attr_name(self):
    return 'updated_at'

  @property
  def modified_attr(self):
    """Return the model attribute to be used for Last-Modified header and
    sorting collection elements.
    """
    return getattr(self.model, self.modified_attr_name)

  def modified_at(self, obj):
    return getattr(obj, self.modified_attr_name)

  def _get_type_where_clause(self, model):
    mapper = model._sa_class_manager.mapper
    if mapper.polymorphic_on is None:
      return True
    else:
      mappers = list(mapper.self_and_descendants)
      polymorphic_on_values = list(
          val
          for val, m in mapper.polymorphic_map.items()
          if m in mappers)
      return mapper.polymorphic_on.in_(polymorphic_on_values)

  def _get_matching_types(self, model):
    mapper = model._sa_class_manager.mapper
    if len(list(mapper.self_and_descendants)) == 1:
      return mapper.class_.__name__
    else:
      # FIXME: Actually needs to use 'self_and_descendants'
      return [m.class_.__name__ for m in mapper.self_and_descendants]

  def get_match_columns(self, model):
    mapper = model._sa_class_manager.mapper
    columns = []
    columns.append(mapper.primary_key[0].label('id'))
    # columns.append(model.id.label('id'))
    columns.append(query_utils.get_type_select_column(model).label('type'))
    if hasattr(mapper.c, 'context_id'):
      columns.append(mapper.c.context_id.label('context_id'))
    if hasattr(mapper.c, 'updated_at'):
      columns.append(mapper.c.updated_at.label('updated_at'))
    # columns.append(self._get_polymorphic_column(model))
    return columns

  def get_collection_matches(self, model, filter_by_contexts=True):
    columns = self.get_match_columns(self.model)
    query = db.session.query(*columns).filter(
        self._get_type_where_clause(model))
    return self.filter_query_by_request(
        query, filter_by_contexts=filter_by_contexts)

  def get_resource_match_query(self, model, id):
    columns = self.get_match_columns(model)
    query = db.session.query(*columns).filter(
        and_(
            self._get_type_where_clause(model),
            columns[0] == id))
    return query

  # Default model/DB helpers
  def get_collection(self, filter_by_contexts=True):
    if '__stubs_only' not in request.args and \
       hasattr(self.model, 'eager_query'):
      query = self.model.eager_query()
    else:
      query = db.session.query(self.model)
    return self.filter_query_by_request(
        query, filter_by_contexts=filter_by_contexts)

  def filter_query_by_request(self, query, filter_by_contexts=True):  # noqa
    joinlist = []
    if request.args:
      querybuilder = AttributeQueryBuilder(self.model)
      filter_, joinlist, _ = querybuilder.collection_filters(request.args)
      if filter_ is not None:
        for j in joinlist:
          query = query.join(j)
        query = query.filter(filter_)

    if "__no_role" in request.args:
      attr = getattr(self.model, "user_roles")
      query = query.outerjoin(attr)
      user_roles_module = attr.mapper.class_
      superusers = getattr(settings, "BOOTSTRAP_ADMIN_USERS", [])
      # Filter out:
      # non superusers AND
      #   (users without user_role OR
      #    users with user_role BUT without global role:
      #    Reader, Editor, Administrator)
      subq = db.session.query(user_roles_module.person_id).filter(
          or_(
              # all users that have global user_role
              user_roles_module.context_id.is_(None),
              user_roles_module.context_id == 0
          )
      ).subquery()
      filter_ = and_(
          # user is not superuser
          ~self.model.email.in_(superusers),
          or_(
              # user hasn't user_role in user_role table
              user_roles_module.id.is_(None),
              and_(
                  # user has user_role in user_role table
                  user_roles_module.id.isnot(None),
                  # user hasn't global role
                  ~user_roles_module.person_id.in_(subq)
              )
          )
      )
      query = query.filter(filter_)

    if filter_by_contexts:
      contexts = permissions.read_contexts_for(self.model.__name__)
      resources = permissions.read_resources_for(self.model.__name__)
      filter_expr = context_query_filter(self.model.context_id, contexts)
      if resources:
        filter_expr = or_(filter_expr, self.model.id.in_(resources))
      query = query.filter(filter_expr)
      for j in joinlist:
        j_class = j.property.mapper.class_
        j_contexts = permissions.read_contexts_for(j_class.__name__)
        j_resources = permissions.read_resources_for(j_class.__name__)
        if j_contexts is not None:
          j_filter_expr = context_query_filter(j_class.context_id, j_contexts)
          if resources:
            j_filter_expr = or_(j_filter_expr, self.model.id.in_(j_resources))
          query = query.filter(j_filter_expr)
        elif resources:
          query = query.filter(self.model.id.in_(resources))
    if '__search' in request.args:
      terms = request.args['__search']
      types = self._get_matching_types(self.model)
      indexer = get_indexer()
      models = indexer._get_grouped_types(types)
      search_query = indexer.get_permissions_query(models, 'read', None)
      search_query = and_(search_query, indexer._get_filter_query(terms))
      search_query = db.session.query(indexer.record_type.key).filter(
          search_query)
      if '__mywork' in request.args:
        search_query = indexer._add_owner_query(
            search_query, models, get_current_user_id())
      search_subquery = search_query.subquery()
      query = query.filter(self.model.id.in_(search_subquery))
    order_properties = []
    if '__sort' in request.args:
      sort_attrs = request.args['__sort'].split(",")
      sort_desc = request.args.get('__sort_desc', False)
      for sort_attr in sort_attrs:
        attr_desc = sort_desc
        if sort_attr.startswith('-'):
          attr_desc = not sort_desc
          sort_attr = sort_attr[1:]
        order_property = getattr(self.model, sort_attr, None)
        if order_property and hasattr(order_property, 'desc'):
          if attr_desc:
            order_property = order_property.desc()
          order_properties.append(order_property)
        else:
          # Possibly throw an exception instead,
          # if sorting by invalid attribute?
          pass
    order_properties.append(self.modified_attr.desc())
    order_properties.append(self.model.id.desc())
    query = query.order_by(*order_properties)
    if '__limit' in request.args:
      try:
        limit = int(request.args['__limit'])
        query = query.limit(limit)
      except (TypeError, ValueError):
        pass
    query = query.distinct()
    return query

  def get_object(self, id):
    # This could also use `self.pk`
    # .one() is required as long as any .eager_load() adds joins using
    #   'contains_eager()' to the core query, because 'LIMIT 1' breaks up
    #   that JOIN result (e.g. Categorizable)
    try:
      return self.get_collection(filter_by_contexts=False)\
          .filter(self.model.id == id).one()
    except sqlalchemy.orm.exc.NoResultFound:
      return None

  def not_found_message(self):
    return '{0} not found.'.format(self.model._inflector.title_singular)

  def not_found_response(self):
    return current_app.make_response((self.not_found_message(), 404, []))

  def collection_last_modified(self):
    """Calculate the last time a member of the collection was modified. This
    method relies on the fact that the collection table has an `updated_at` or
    other column with a relevant timestamp; services for models that don't have
    this field **MUST** override this method.
    """
    result = db.session.query(
        self.modified_attr).order_by(self.modified_attr.desc()).first()
    if result is not None:
      return self.modified_at(result)
    return datetime.datetime.now()

  # Routing helpers
  @classmethod
  def endpoint_name(cls):
    return cls.__name__

  @classmethod
  def url_for_preserving_querystring(cls, *args, **kwargs):
    url = cls.url_for(*args, **kwargs)
    # preserve original query string
    idx = request.url.find('?')
    querystring = '' if idx < 0 else '?' + request.url[idx + 1:]
    return url + querystring

  @classmethod
  def base_url_for(cls, _memoized_base_url={}):
    if cls not in _memoized_base_url:
      _memoized_base_url[cls] = url_for(cls.endpoint_name())
    return _memoized_base_url[cls]

  @classmethod
  def url_for(cls, *args, **kwargs):
    url = cls.base_url_for()
    if len(args) > 0:
      arg = args[0]
      id = arg if not isinstance(arg, db.Model) else arg.id
      url = url + '/' + str(id)
    if 'id' in kwargs:
      url = url + '/' + str(kwargs['id'])
      del kwargs['id']
    if len(kwargs) > 0:
      url = url + '?' + urlencode(kwargs)
    return url

  @classmethod
  def decorate_view_func(cls, view_func, decorators):
    if not isinstance(decorators, (list, tuple)):
      decorators = (decorators,)
    for decorator in reversed(decorators):
      view_func = decorator(view_func)
    return view_func


# View base class for Views handling
#   - /resources (GET, POST)
#   - /resources/<pk:pk_type> (GET, PUT, POST, DELETE)
class Resource(ModelView):
  """View base class for Views handling.  Will typically be registered with an
  application following a collection style for routes. Collection `GET` and
  `POST` will have a route like `/resources` while collection member
  resource routes will have routes likej `/resources/<pk:pk_type>`.

  To register a Resource subclass FooCollection with a Flask application:

  ..

     FooCollection.add_to(app, '/foos')

  By default will only support the `application/json` content-type.
  """

  def dispatch_request(self, *args, **kwargs):  # noqa
    with benchmark("Dispatch request"):
      with benchmark("dispatch_request > Check Headers"):
        method = request.method
        if method in ('POST', 'PUT', 'DELETE')\
           and 'X-Requested-By' not in request.headers:
          raise BadRequest('X-Requested-By header is REQUIRED.')

      with benchmark("dispatch_request > Try"):
        try:
          if method == 'GET':
            if self.pk in kwargs and kwargs[self.pk] is not None:
              return self.get(*args, **kwargs)
            else:
              return self.collection_get()
          elif method == 'POST':
            if self.pk in kwargs and kwargs[self.pk] is not None:
              return self.post(*args, **kwargs)
            else:
              return self.collection_post()
          elif method == 'PUT':
            return self.put(*args, **kwargs)
          elif method == 'DELETE':
            return self.delete(*args, **kwargs)
          else:
            raise NotImplementedError()
        except (IntegrityError, ValidationError, ValueError) as err:
          message = translate_message(err)
          logger.warning(message)
          raise BadRequest(message)
        except Exception as err:
          logger.exception(err)
          raise
        finally:
          # When running integration tests, cache sometimes does not clear
          # correctly
          if getattr(settings, 'TESTING', False):
            cache = get_cache()
            if cache:
              cache.clear()

  def post(*args, **kwargs):
    raise NotImplementedError()

  def get(self, id):
    """Default JSON request handlers"""
    with benchmark("Query for object"):
      obj = self.get_object(id)
    if obj is None:
      return self.not_found_response()

    accept_header = self.request.headers.get('Accept', '').strip()
    if (
        accept_header and
        accept_header != '*/*' and
        'application/json' not in accept_header
    ):
      return current_app.make_response((
          'application/json', 406, [('Content-Type', 'text/plain')]))

    with benchmark("Query read permissions"):
      if not permissions.is_allowed_read(
          self.model.__name__, obj.id, obj.context_id)\
         and not permissions.has_conditions('read', self.model.__name__):
        raise Forbidden()
      if not permissions.is_allowed_read_for(obj):
        raise Forbidden()
    with benchmark("Serialize object"):
      object_for_json = self.object_for_json(obj)

    obj_etag = etag(self.modified_at(obj), get_info(obj))
    if 'If-None-Match' in self.request.headers and \
       self.request.headers['If-None-Match'] == obj_etag:
      with benchmark("Make response"):
        return current_app.make_response(
            ('', 304, [('Etag', obj_etag)]))
    with benchmark("Make response"):
      return self.json_success_response(
          object_for_json, self.modified_at(obj), obj_etag=obj_etag)

  def validate_headers_for_put_or_delete(self, obj):
    """rfc 6585 defines a new status code for missing required headers"""
    required_headers = set(["If-Match", "If-Unmodified-Since"])
    missing_headers = required_headers.difference(
        set(self.request.headers.keys()))
    if missing_headers:
      return current_app.make_response((
          json.dumps({
              "message": "Missing headers: " + ", ".join(missing_headers),
          }),
          428,
          [("Content-Type", "application/json")],
      ))

    object_etag = etag(self.modified_at(obj), get_info(obj))
    object_timestamp = self.http_timestamp(self.modified_at(obj))
    if (request.headers["If-Match"] != object_etag or
            request.headers["If-Unmodified-Since"] != object_timestamp):
      return current_app.make_response((
          json.dumps({
              "message": "The resource could not be updated due to a conflict "
                         "with the current state on the server. Please "
                         "resolve the conflict by refreshing the resource.",
          }),
          409,
          [("Content-Type", "application/json")]
      ))
    return None

  def json_update(self, obj, src):
    ggrc.builder.json.update(obj, src)

  def _check_put_permissions(self, obj, new_context):
    """Check context and resource permissions for PUT."""
    if not permissions.is_allowed_update(
        self.model.__name__, obj.id, obj.context_id)\
       and not permissions.has_conditions('update', self.model.__name__):
      raise Forbidden()
    if not permissions.is_allowed_update_for(obj):
      raise Forbidden()
    if new_context != obj.context_id \
       and not permissions.is_allowed_update(
            self.model.__name__, obj.id, new_context)\
       and not permissions.has_conditions('update', self.model.__name__):
      raise Forbidden()

  def put(self, id):
    with benchmark("Query for object"):
      obj = self.get_object(id)
    if obj is None:
      return self.not_found_response()
    src = self.request.json
    if self.request.mimetype != 'application/json':
      return current_app.make_response(
          ('Content-Type must be application/json', 415, []))
    header_error = self.validate_headers_for_put_or_delete(obj)
    if header_error:
      return header_error
    root_attribute = self.model._inflector.table_singular
    try:
      src = src[root_attribute]
    except KeyError:
      raise BadRequest('Required attribute "{0}" not found'.format(
          root_attribute))
    with benchmark("Deserialize object"):
      self.json_update(obj, src)
    obj.modified_by_id = get_current_user_id()
    db.session.add(obj)
    with benchmark("Query update permissions"):
      new_context = self.get_context_id_from_json(src)
      self._check_put_permissions(obj, new_context)
    with benchmark("Process actions"):
      self.process_actions(obj)
    with benchmark("Validate custom attributes"):
      if hasattr(obj, "validate_custom_attributes"):
        obj.validate_custom_attributes()
    with benchmark("Send PUT event"):
      signals.Restful.model_put.send(
          obj.__class__, obj=obj, src=src, service=self)
    with benchmark("Get modified objects"):
      modified_objects = get_modified_objects(db.session)
    with benchmark("Update custom attribute values"):
      set_ids_for_new_custom_attributes(obj)
    with benchmark("Log event"):
      event = log_event(db.session, obj, force_obj=True)
    with benchmark("Update memcache before commit for collection PUT"):
      update_memcache_before_commit(
          self.request, modified_objects, CACHE_EXPIRY_COLLECTION)
    with benchmark("Commit"):
      db.session.commit()
    with benchmark("Query for object"):
      obj = self.get_object(id)
    with benchmark("Serialize collection"):
      object_for_json = self.object_for_json(obj)
    with benchmark("Update index"):
      update_snapshot_index(db.session, modified_objects)
    with benchmark("Update memcache after commit for collection PUT"):
      update_memcache_after_commit(self.request)
    with benchmark("Send PUT - after commit event"):
      signals.Restful.model_put_after_commit.send(
          obj.__class__, obj=obj, src=src, service=self, event=event)
      # Note: Some data is created in listeners for model_put_after_commit
      # (like updates to snapshots), so we need to commit the changes
      with benchmark("Get modified objects"):
        modified_objects = get_modified_objects(db.session)
      with benchmark("Update memcache before commit"):
        update_memcache_before_commit(
            self.request, modified_objects, CACHE_EXPIRY_COLLECTION)
      db.session.commit()
      with benchmark("Update memcache after commit"):
        update_memcache_after_commit(self.request)
      if self.has_cache():
        self.invalidate_cache_to(obj)
    with benchmark("Send event job"):
      send_event_job(event)
    with benchmark("Make response"):
      return self.json_success_response(
          object_for_json, self.modified_at(obj),
          obj_etag=etag(self.modified_at(obj), get_info(obj)))

  def delete(self, id):
    with benchmark("Query for object"):
      obj = self.get_object(id)
    if obj is None:
      return self.not_found_response()
    with benchmark("Query delete permissions"):
      if not permissions.is_allowed_delete(
          self.model.__name__, obj.id, obj.context_id)\
         and not permissions.has_conditions("delete", self.model.__name__):
        raise Forbidden()
      if not permissions.is_allowed_delete_for(obj):
        raise Forbidden()
    header_error = self.validate_headers_for_put_or_delete(obj)
    if header_error:
      return header_error
    db.session.delete(obj)
    with benchmark("Send DELETEd event"):
      signals.Restful.model_deleted.send(
          obj.__class__, obj=obj, service=self)
    with benchmark("Get modified objects"):
      modified_objects = get_modified_objects(db.session)
    with benchmark("Log event"):
      event = log_event(db.session, obj)
    with benchmark("Update memcache before commit for collection DELETE"):
      update_memcache_before_commit(
          self.request, modified_objects, CACHE_EXPIRY_COLLECTION)
    with benchmark("Commit"):
      db.session.commit()
    with benchmark("Update index"):
      update_snapshot_index(db.session, modified_objects)
    with benchmark("Update memcache after commit for collection DELETE"):
      update_memcache_after_commit(self.request)
    with benchmark("Send DELETEd - after commit event"):
      signals.Restful.model_deleted_after_commit.send(
          obj.__class__, obj=obj, service=self, event=event)
    with benchmark("Send event job"):
      send_event_job(event)
    with benchmark("Make response"):
      result = self.json_success_response({}, datetime.datetime.now())
    return result

  def has_cache(self):
    return getattr(settings, 'MEMCACHE_MECHANISM', False)

  def apply_paging(self, matches_query):
    page_size = min(
        int(request.args.get('__page_size', self.DEFAULT_PAGE_SIZE)),
        self.MAX_PAGE_SIZE)
    if '__page_only' in request.args:
      page_number = int(request.args.get('__page', 0))
      matches = []
      total = matches_query.count()
    else:
      page_number = int(request.args.get('__page', 1))
      matches = matches_query\
          .limit(page_size)\
          .offset((page_number - 1) * page_size)\
          .all()
      if page_number == 1 and len(matches) < page_size:
        total = len(matches)
      else:
        total = matches_query.count()
    page = Pagination(
        matches_query, page_number, page_size, total, matches)
    collection_extras = {
        'paging': self.build_page_object_for_json(page)
    }
    return matches, collection_extras

  def get_matched_resources(self, matches):
    cache_objs = {}
    if self.has_cache():
      self.request.cache_manager = _get_cache_manager()
      with benchmark("Query cache for resources"):
        cache_objs = self.get_resources_from_cache(matches)
      database_matches = [m for m in matches if m not in cache_objs]
    else:
      database_matches = matches

    database_objs = {}
    if len(database_matches) > 0:
      database_objs = self.get_resources_from_database(matches)
      if self.has_cache():
        with benchmark("Add resources to cache"):
          self.add_resources_to_cache(database_objs)
    return cache_objs, database_objs

  def collection_get(self):
    with benchmark("dispatch_request > collection_get > Check headers"):
      accept_header = self.request.headers.get('Accept', '').strip()
      if (
          accept_header and
          accept_header != '*/*' and
          'application/json' not in accept_header
      ):
        return current_app.make_response((
            'application/json', 406, [('Content-Type', 'text/plain')]))

    with benchmark("dispatch_request > collection_get > Collection matches"):
      # We skip querying by contexts for Creator role and relationship objects,
      # because it will filter out objects that the Creator can access.
      # We are doing a special permissions check for these objects
      # below in the filter_resource method.
      filter_by_contexts = not (
          self.model.__name__ in ("Relationship", "Revision") and _is_creator()
      )
      matches_query = self.get_collection_matches(
          self.model, filter_by_contexts)
    with benchmark("dispatch_request > collection_get > Query Data"):
      if '__page' in request.args or '__page_only' in request.args:
        with benchmark("Query matches with paging"):
          matches, extras = self.apply_paging(matches_query)
      else:
        with benchmark("Query matches"):
          matches = matches_query.all()
          extras = {}
    with benchmark("dispatch_request > collection_get > Matched resources"):
      cache_op = None
      if '__stubs_only' in request.args:
        objs = [{
            'id': m[0],
            'type': m[1],
            'href': utils.url_for(m[1], id=m[0]),
            'context_id': m[2]
        } for m in matches]

      else:
        cache_objs, database_objs = self.get_matched_resources(matches)
        objs = {}
        objs.update(cache_objs)
        objs.update(database_objs)

        objs = [objs[m] for m in matches if m in objs]
        with benchmark("Filter resources based on permissions"):
          objs = filter_resource(objs)

        cache_op = 'Hit' if len(cache_objs) > 0 else 'Miss'
    with benchmark("dispatch_request > collection_get > Create Response"):
      # Return custom fields specified via `__fields=id,title,description` etc.
      # TODO this can be optimized by filter_resource() not retrieving
      # the other fields to being with
      if '__fields' in request.args:
        custom_fields = request.args['__fields'].split(',')
        objs = [{f: o[f] for f in custom_fields if f in o} for o in objs]
      with benchmark("Serialize collection"):
        collection = self.build_collection_representation(
            objs, extras=extras)

      if 'If-None-Match' in self.request.headers and \
         self.request.headers['If-None-Match'] == etag(collection):
        return current_app.make_response((
            '', 304, [('Etag', etag(collection))]))

      with benchmark("Make response"):
        return self.json_success_response(
            collection, self.collection_last_modified(), cache_op=cache_op)

  def get_resources_from_cache(self, matches):
    """Get resources from cache for specified matches"""
    resources = {}
    # Disable caching for background tasks
    # Setting background task status circumvents our memcache
    # invalidation logic so we have to disabling memcache.
    if self.model.__name__ == 'BackgroundTask':
      return resources
    # Skip right to memcache
    memcache_client = self.request.cache_manager.cache_object.memcache_client
    for match in matches:
      key = get_cache_key(None, id=match[0], type=match[1])
      val = memcache_client.get(key) or {}
      if "selfLink" in val:
        resources[match] = val
    return resources

  def add_resources_to_cache(self, match_obj_pairs):
    """Add resources to cache if they are not blocked by DeleteOp entries"""
    # Skip right to memcache
    memcache_client = self.request.cache_manager.cache_object.memcache_client
    for match, obj in match_obj_pairs.items():
      memcache_client.add(get_cache_key(None, id=match[0], type=match[1]), obj)

  def invalidate_cache_to(self, obj):
    """Invalidate api cache for sent object."""
    memcache_client = self.request.cache_manager.cache_object.memcache_client
    memcache_client.delete(get_cache_key(None, id=obj.id, type=obj.type))

  def json_create(self, obj, src):
    ggrc.builder.json.create(obj, src)

  def get_context_id_from_json(self, src):
    context = src.get('context', None)
    if context:
      context_id = context.get('id', None)
      try:
        return int(context_id)
      except (ValueError, TypeError):
        return None
    return None

  def handle_create(self, obj, src):
    """Do NOTHING by default"""
    pass

  def _unwrap_collection_post_src(self, wrapped_src):
    """Get a valid source dict.

    Wrapped source example:
      {"policy": {"title": "A", context: None}}

    This function unwraps the first dict, returns only a dict containing
    model attributes and checks that the source contains a mandatory context
    attribute.

    Args:
      wrapped_src: dict containing a dict with all model attributes.

    Returns:
      inner dict containing only the model attributes.

    Raises:
      BadRequest if any of the required attributes are missing.
    """
    root_attribute = self.model._inflector.table_singular
    try:
      src = wrapped_src[root_attribute]
    except KeyError:
      raise BadRequest('Required attribute "{0}" not found'.format(
          root_attribute))

    if 'context' not in src:
      raise BadRequest('context MUST be specified.')

    return src

  def _get_relationships_cache(self, body):
    cache = getattr(self, "_relationship_cache", None)
    if cache is not None:
      return cache
    relationships = self.model.query.filter(tuple_(
        self.model.source_id, self.model.source_type,
        self.model.destination_id, self.model.destination_type).in_((
            src["relationship"]["source"].get("id", -1),
            src["relationship"]["source"].get("type"),
            src["relationship"]["destination"].get("id", -1),
            src["relationship"]["destination"].get("type")
        ) for src in body)
    )

    cache = {
        (
            relationship.source_id,
            relationship.source_type,
            relationship.destination_id,
            relationship.destination_type,
        ): relationship
        for relationship in relationships
    }
    setattr(self, "_relationship_cache", cache)
    return cache

  def _get_model_instance(self, src=None, body=None):
    """Get a model instance.

    This function creates a new model instance and returns it. The function is
    needed for correct handling of Relationship objects. Relationship post
    request should not fail if a relationship already exists, since some
    relationships can be created with auto mappings.

    Args:
      src: dict containing new object source.

    Returns:
      An instance of current model.
    """

    obj = None
    if self.model.__name__ == "Relationship":
      obj = self._get_relationships_cache(body).get((
          src["source"]["id"],
          src["source"]["type"],
          src["destination"]["id"],
          src["destination"]["type"]
      ))
    if obj is None:
      obj = self.model()
      db.session.add(obj)
    return obj

  def _check_post_permissions(self, objects):
    """Check create permissions for a list of objects.append

    Args:
      objects: List of objects.

    Raises:
      Forbidden error if user does not have create permission for all objects
      in the objects list.
    """
    for obj in objects:
      if not permissions.is_allowed_create_for(obj):
        # json_create sometimes adds objects to session, so we need to
        # make sure the session is cleared
        db.session.expunge_all()
        raise Forbidden()

  def _gather_referenced_objects(self, data, accomulator=None):
    if accomulator is None:
      accomulator = defaultdict(set)
    if isinstance(data, list):
      for value in data:
        self._gather_referenced_objects(value, accomulator)
    elif isinstance(data, dict):
      if "type" in data and data.get("id"):
        accomulator[data["type"]].add(data["id"])
      for value in data.values():
        self._gather_referenced_objects(value, accomulator)
    return accomulator

  def _build_request_stub_cache(self, data):
    objects = self._gather_referenced_objects(data)
    g.referenced_objects = {}
    for class_name, ids in objects.items():
      class_ = getattr(ggrc.models, class_name, None)
      if hasattr(class_, "query"):
        g.referenced_objects[class_] = {
            obj.id: obj for obj in class_.query.filter(class_.id.in_(ids))
        }

  def collection_post_loop(self, body, res, no_result, running_async):
    """Handle all posted objects.

    Args:
      body: list of dictionaries containing json object representations.
      res: List that will get responses appended to it.
      no_result: Flag for suppressing results.
      running_async: Flag for async jobs.
    """

    with benchmark("Generate objects"):
      objects = []
      sources = []
      for wrapped_src in body:
        src = self._unwrap_collection_post_src(wrapped_src)
        obj = self._get_model_instance(src, body)
        with benchmark("Deserialize object"):
          self.json_create(obj, src)
        with benchmark("Send model POSTed event"):
          signals.Restful.model_posted.send(
              obj.__class__, obj=obj, src=src, service=self)
        with benchmark("Update custom attribute values"):
          set_ids_for_new_custom_attributes(obj)

        obj.modified_by = get_current_user()
        objects.append(obj)
        sources.append(src)

    with benchmark("Check create permissions"):
      self._check_post_permissions(objects)
    with benchmark("Send collection POSTed event"):
      signals.Restful.collection_posted.send(
          obj.__class__, objects=objects, sources=sources)
    with benchmark("Flush posted objects"):
      db.session.flush()
    with benchmark("Validate custom attributes"):
      for obj in objects:
        if hasattr(obj, "validate_custom_attributes"):
          obj.validate_custom_attributes()
    with benchmark("Get modified objects"):
      modified_objects = get_modified_objects(db.session)
    with benchmark("Log event for all objects"):
      event = log_event(db.session, obj, flush=False)
    with benchmark("Update memcache before commit for collection POST"):
      update_memcache_before_commit(
          self.request, modified_objects, CACHE_EXPIRY_COLLECTION)
    with benchmark("Serialize objects"):
      for obj in objects:
        object_for_json = {} if no_result else self.object_for_json(obj)
        res.append((201, object_for_json))
    with benchmark("Commit collection"):
      db.session.commit()
    with benchmark("Update index"):
      update_snapshot_index(db.session, modified_objects)
    with benchmark("Update memcache after commit for collection POST"):
      update_memcache_after_commit(self.request)

    with benchmark("Send model POSTed - after commit event"):
      for obj, src in itertools.izip(objects, sources):
        signals.Restful.model_posted_after_commit.send(
            obj.__class__, obj=obj, src=src, service=self, event=event)
        # Note: In model_posted_after_commit necessary mapping and
        # relationships are set, so need to commit the changes
      db.session.commit()
    with benchmark("Send event job"):
      send_event_job(event)

  @staticmethod
  def _make_error_from_exception(exc):
    """Return a 400-code with the exception message."""
    message = translate_message(exc)
    logger.warning(message)
    return (400, message)

  def collection_post(self):  # noqa
    with benchmark("collection post"):
      if self.request.mimetype != 'application/json':
        return current_app.make_response((
            'Content-Type must be application/json', 415, []))

      running_async = False
      if 'X-GGRC-BackgroundTask' in request.headers:
        if 'X-Appengine-Taskname' not in request.headers:
          task = create_task(request.method, request.full_path,
                             None, request.data)
          if getattr(settings, 'APP_ENGINE', False):
            return self.json_success_response(
                self.object_for_json(task, 'background_task'),
                self.modified_at(task))
          body = self.request.json
        else:
          task_id = int(self.request.headers.get('x-task-id'))
          task = BackgroundTask.query.get(task_id)
          body = json.loads(task.parameters)
          running_async = True
        task.start()
        no_result = True
      else:
        body = self.request.json
        no_result = False
      wrap = isinstance(body, dict)
      if wrap:
        body = [body]
      res = []
      with benchmark("collection post > body loop: {}".format(len(body))):
        with benchmark("Build stub query cache"):
          self._build_request_stub_cache(body)
        try:
          self.collection_post_loop(body, res, no_result, running_async)
        except (IntegrityError, ValidationError, ValueError) as error:
          res.append(self._make_error_from_exception(error))
          db.session.rollback()
        except Exception as error:
          res.append((getattr(error, "code", 500), error.message))
          logger.warning("Collection POST commit failed", exc_info=True)
          db.session.rollback()
        if hasattr(g, "referenced_objects"):
          delattr(g, "referenced_objects")
      with benchmark("collection post > calculate response statuses"):
        headers = {"Content-Type": "application/json"}
        errors = []
        if wrap:
          status, res = res[0]
          if isinstance(res, dict) and len(res) == 1:
            value = res.values()[0]
            if "id" in value:
              headers['Location'] = self.url_for(id=value["id"])
        else:
          for res_status, body in res:
            if not 200 <= res_status < 300:
              errors.append((res_status, body))
          if len(errors) > 0:
            status = errors[0][0]
            headers[
                "X-Flash-Error"] = ' || '.join((error for _, error in errors))
          else:
            status = 200
      with benchmark("collection post > make response"):
        result = current_app.make_response(
            (self.as_json(res), status, headers))

      with benchmark("collection post > return resullt"):
        if 'X-GGRC-BackgroundTask' in request.headers:
          if status == 200:
            task.finish("Success", result)
          else:
            task.finish("Failure", result)
        return result

  @classmethod
  def add_to(cls, app, url, model_class=None, decorators=()):
    if model_class:
      service_class = type(model_class.__name__, (cls,), {
          '_model': model_class,
      })
      import ggrc.services
      setattr(ggrc.services, model_class.__name__, service_class)
    else:
      service_class = cls
    view_func = service_class.as_view(service_class.endpoint_name())
    view_func = cls.decorate_view_func(view_func, decorators)
    app.add_url_rule(
        url,
        defaults={cls.pk: None},
        view_func=view_func,
        methods=['GET', 'POST'])
    app.add_url_rule(
        '{url}/<{type}:{pk}>'.format(url=url, type=cls.pk_type, pk=cls.pk),
        view_func=view_func,
        methods=['GET', 'PUT', 'DELETE'])

  # Response helpers
  @classmethod
  def as_json(cls, obj, **kwargs):
    return as_json(obj, **kwargs)

  def get_properties_to_include(self, inclusions):
    # FIXME This needs to be improved to deal with branching paths... if that's
    # desirable or needed.
    if inclusions is not None:
      if len(inclusions) == 0:
        raise BadRequest(
            'The __include query parameter requires at least one field to be '
            'included.')
      paths = inclusions.split(',')
      inclusions = []
      for p in paths:
        path = p.split('.')
        if len(path) == 1:
          inclusions.append(tuple(path))
        else:
          inclusions.append((path[0], tuple(path[1:])))
    else:
      inclusions = ()
    return inclusions

  def build_page_object_for_json(self, paging):
    def page_url(params):
      return base_url + '?' + urlencode(utils.encoded_dict(params))

    def page_args(next_num, per_page):
      # coerce the values to be plain strings, rather than unicode
      ret = dict([(k, unicode(v)) for k, v in request.args.items()])
      ret['__page'] = next_num
      if '__page_size' in ret:
        ret['__page_size'] = per_page
      return ret
    paging_obj = {}
    base_url = self.url_for()
    if paging.has_next:
      paging_obj['next'] = page_url(
          page_args(paging.next_num, paging.per_page))
    if paging.has_prev:
      paging_obj['prev'] = page_url(
          page_args(paging.prev_num, paging.per_page))
    paging_obj['first'] = page_url(page_args(1, paging.per_page))
    paging_obj['last'] = page_url(page_args(paging.pages, paging.per_page))
    paging_obj['count'] = paging.pages
    paging_obj['total'] = paging.total
    return paging_obj

  def get_resources_from_database(self, matches):
    # FIXME: This is cheating -- `matches` should be allowed to be any model
    model = self.model
    ids = {m[0]: m for m in matches}
    with benchmark("Query database for matches"):
      query = model.eager_query()
      # We force the query here so that we can benchmark it
      objs = query.filter(model.id.in_(ids.keys())).all()
    with benchmark("Publish objects"):
      resources = {}
      includes = self.get_properties_to_include(request.args.get('__include'))
      for obj in objs:
        resources[ids[obj.id]] = ggrc.builder.json.publish(obj, includes)
    with benchmark("Publish representation"):
      ggrc.builder.json.publish_representation(resources)
    return resources

  def build_collection_representation(self, objs, extras=None):
    table_plural = self.model._inflector.table_plural
    collection_name = '{0}_collection'.format(table_plural)
    resource = {
        collection_name: {
            'selfLink': self.url_for_preserving_querystring(),
            table_plural: objs,
        }
    }
    if extras:
      resource[collection_name].update(extras)
    return resource

  def object_for_json(self, obj, model_name=None, properties_to_include=None):
    model_name = model_name or self.model._inflector.table_singular
    json_obj = ggrc.builder.json.publish(
        obj, properties_to_include or [], inclusion_filter)
    ggrc.builder.json.publish_representation(json_obj)
    if hasattr(obj, "_json_extras"):
      json_obj["extras"] = obj._json_extras
    return {model_name: json_obj}

  def build_resource_representation(self, obj, extras=None):
    table_singular = self.model._inflector.table_singular
    resource = {
        table_singular: obj,
    }
    if extras:
      resource.update(extras)
    return resource

  def http_timestamp(self, timestamp):
    return format_date_time(time.mktime(timestamp.utctimetuple()))

  def json_success_response(self, response_object, last_modified=None,
                            status=200, id=None, cache_op=None,
                            obj_etag=None):
    headers = [('Content-Type', 'application/json')]
    if last_modified:
      headers.append(('Last-Modified', self.http_timestamp(last_modified)))
    if obj_etag:
      headers.append(('Etag', obj_etag))
    if id is not None:
      headers.append(('Location', self.url_for(id=id)))
    if cache_op:
      headers.append(('X-GGRC-Cache', cache_op))
    return current_app.make_response(
        (self.as_json(response_object), status, headers))

  def process_actions(self, obj):
    if hasattr(obj, 'process_actions'):
      # process actionsS
      added, deleted = obj.process_actions()
      # send signals for added/deleted objects
      for _class, _objects in added.items():
        if not _objects:
          continue
        signals.Restful.collection_posted.send(
            _class, objects=_objects, service=self,
            sources=[{} for _ in xrange(len(_objects))])
        for _obj in _objects:
          signals.Restful.model_posted.send(
              _class, obj=_obj, service=self)
      for _obj in deleted:
        signals.Restful.model_deleted.send(
            _obj.__class__, obj=_obj, service=self)
      if added or deleted:
        obj.invalidate_evidence_found()


class ReadOnlyResource(Resource):

  def dispatch_request(self, *args, **kwargs):
    method = request.method

    if method == 'GET':
      return super(ReadOnlyResource, self).dispatch_request(*args, **kwargs)
    else:
      raise NotImplementedError()


class ExtendedResource(Resource):
  """Extended resource with additional command support."""

  @classmethod
  def add_to(cls, app, url, model_class=None, decorators=()):
    """Register view methods.

    This method only extends original resource add_to, with a command option
    for get requests.
    """
    if model_class:
      service_class = type(model_class.__name__, (cls,), {
          '_model': model_class,
      })
      import ggrc.services
      setattr(ggrc.services, model_class.__name__, service_class)
    else:
      service_class = cls
    view_func = service_class.as_view(service_class.endpoint_name())
    view_func = cls.decorate_view_func(view_func, decorators)
    app.add_url_rule(
        url,
        defaults={cls.pk: None},
        view_func=view_func,
        methods=['GET', 'POST'])
    app.add_url_rule(
        '{url}/<{type}:{pk}>'.format(url=url, type=cls.pk_type, pk=cls.pk),
        view_func=view_func,
        methods=['GET', 'PUT', 'DELETE'])
    app.add_url_rule(
        '{url}/<{type}:{pk}>/<command>'.format(
            url=url,
            type=cls.pk_type,
            pk=cls.pk
        ),
        view_func=view_func,
        methods=['GET']
    )


def filter_resource(resource, depth=0, user_permissions=None):  # noqa
  """
  Returns:
     The subset of resources which are readable based on user_permissions
  """

  if user_permissions is None:
    user_permissions = permissions.permissions_for(get_current_user())

  if isinstance(resource, (list, tuple)):
    filtered = []
    for sub_resource in resource:
      filtered_sub_resource = filter_resource(
          sub_resource, depth=depth + 1, user_permissions=user_permissions)
      if filtered_sub_resource is not None:
        filtered.append(filtered_sub_resource)
    return filtered
  elif isinstance(resource, dict) and 'type' in resource:
    # First check current level
    context_id = False
    if 'context' in resource:
      if resource['context'] is None:
        context_id = None
      else:
        context_id = resource['context']['id']
    elif 'context_id' in resource:
      context_id = resource['context_id']
    assert context_id is not False, "No context found for object"

    # In order to avoid loading full instances and using is_allowed_read_for,
    # we are making a special test for the Creator here. Creator can only
    # see relationship objects where he has read access on both source and
    # destination. This is defined in Creator.py:220 file, but is_allowed_read
    # can not check conditions without the full instance
    if resource['type'] == "Relationship" and _is_creator():
      # Make a check for relationship objects that are a special case
      can_read = True
      for name in ('source', 'destination'):
        inst = resource[name]
        if not inst:
          # If object was deleted but relationship still exists
          continue
        contexts = permissions.read_contexts_for(inst['type'])
        if contexts is None:
          # read_contexts_for returns None if the user has access to all the
          # objects of this type. If the user doesn't have access to any object
          # an empty list ([]) will be returned
          continue
        resources = permissions.read_resources_for(inst['type']) or []
        if inst['context_id'] in contexts or inst['id'] in resources:
          continue
        can_read = False
      if not can_read:
        return None
    elif resource['type'] == "Revision" and _is_creator():
      # Make a check for revision objects that are a special case
      if not hasattr(ggrc.models.all_models, resource['resource_type']):
        # there are no permissions for old objects
        return None
      res_model = getattr(ggrc.models.all_models, resource['resource_type'])
      instance = res_model.query.get(resource['resource_id'])
      if instance is None or\
         not user_permissions.is_allowed_read_for(instance):
        return None
    else:
      if not user_permissions.is_allowed_read(resource['type'],
                                              resource['id'], context_id):
        return None
    # Then, filter any typed keys
    for key, value in resource.items():
      if key == 'context':
        # Explicitly allow `context` objects to pass through
        pass
      else:
        # Apply filtering to sub-resources
        if isinstance(value, dict) and 'type' in value:
          resource[key] = filter_resource(
              value, depth=depth + 1, user_permissions=user_permissions)

    return resource
  else:
    assert False, "Non-object passed to filter_resource"


def _is_creator():
  current_user = get_current_user()
  return hasattr(current_user, 'system_wide_role') \
      and current_user.system_wide_role == "Creator"


def get_info(obj):
  """Get object info string."""
  return '%s %s' % (obj.__class__.__name__, str(obj.id))


def etag(last_modified, info=''):
  """Generate the etag given a datetime for the last time the resource was
  modified. This isn't as good as an etag generated off of a hash of the
  representation, but, it doesn't require the representation in order to be
  calculated. An alternative would be to keep an etag on the stored
  representation, but this will do for now.

  .. note::

      Using the datetime implies the need for some care - the resolution of
      the time object needs to be sufficient such that you don't end up with
      the same etag due to two updates performed in rapid succession.
  """
  return '"{0}"'.format(hashlib.sha1(str(last_modified) + info).hexdigest())


def send_event_job(event):
  """Create bacground job for handling new revisions."""
  revision_ids = [revision.id for revision in event.revisions]
  from ggrc import views
  views.start_compute_attributes(revision_ids)
