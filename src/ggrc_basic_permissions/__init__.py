# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Initialize RBAC"""

import datetime
import itertools

import sqlalchemy.orm
from sqlalchemy import and_
from sqlalchemy import case
from sqlalchemy import literal
from sqlalchemy import or_
from sqlalchemy.orm import aliased
from flask import Blueprint
from flask import g

from ggrc import db
from ggrc import settings
from ggrc.app import app
from ggrc.login import get_current_user
from ggrc.models import all_models
from ggrc.models.audit import Audit
from ggrc.models.program import Program
from ggrc.models.object_owner import ObjectOwner
from ggrc.rbac import permissions as rbac_permissions
from ggrc.rbac.permissions_provider import DefaultUserPermissions
from ggrc.services.common import _get_cache_manager
from ggrc.services.common import Resource
from ggrc.services.registry import service
from ggrc.utils import benchmark
from ggrc_basic_permissions import basic_roles
from ggrc_basic_permissions.contributed_roles import lookup_role_implications
from ggrc_basic_permissions.contributed_roles import BasicRoleDeclarations
from ggrc_basic_permissions.contributed_roles import BasicRoleImplications
from ggrc_basic_permissions.converters.handlers import COLUMN_HANDLERS
from ggrc_basic_permissions.models import ContextImplication
from ggrc_basic_permissions.models import get_ids_related_to
from ggrc_basic_permissions.models import Role
from ggrc_basic_permissions.models import UserRole


blueprint = Blueprint(
    'permissions',
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/static/ggrc_basic_permissions',
)

PERMISSION_CACHE_TIMEOUT = 3600  # 60 minutes


def get_public_config(_):
  """Expose additional permissions-dependent config to client.
    Specifically here, expose GGRC_BOOTSTRAP_ADMIN values to ADMIN users.
  """
  public_config = {}
  if rbac_permissions.is_admin():
    if hasattr(settings, 'BOOTSTRAP_ADMIN_USERS'):
      public_config['BOOTSTRAP_ADMIN_USERS'] = settings.BOOTSTRAP_ADMIN_USERS
  return public_config


def objects_via_assignable_query(user_id, context_not_role=True):
  """Creates a query that returns objects a user can access because she is
     assigned via the assignable mixin.

    Args:
        user_id (int): id of the user

    Returns:
        db.session.query object that selects the following columns:
            | id | type | context_id |
  """

  rel1 = aliased(all_models.Relationship, name="rel1")
  rel2 = aliased(all_models.Relationship, name="rel2")
  _attrs = aliased(all_models.RelationshipAttr, name="attrs")

  def assignable_join(query):
    """Joins relationship_attrs to the query. This filters out only the
       relationship objects where the user is mapped with an AssigneeType.
    """
    return query.join(
        _attrs, and_(
            _attrs.relationship_id == rel1.id,
            _attrs.attr_name == "AssigneeType",
            case([
                (rel1.destination_type == "Person",
                 rel1.destination_id)
            ], else_=rel1.source_id) == user_id))

  def related_assignables():
    """Header for the mapped_objects join"""
    return db.session.query(
        case([
            (rel2.destination_type == rel1.destination_type,
             rel2.source_id)
        ], else_=rel2.destination_id).label('id'),
        case([
            (rel2.destination_type == rel1.destination_type,
             rel2.source_type)
        ], else_=rel2.destination_type).label('type'),
        rel1.context_id if context_not_role else literal('R')
    ).select_from(rel1)

  # First we fetch objects where a user is mapped as an assignee
  assigned_objects = assignable_join(db.session.query(
      case([
          (rel1.destination_type == "Person",
           rel1.source_id)
      ], else_=rel1.destination_id),
      case([
          (rel1.destination_type == "Person",
           rel1.source_type)
      ], else_=rel1.destination_type),
      rel1.context_id if context_not_role else literal('RUD')))

  # The user should also have access to objects mapped to the assigned_objects
  # We accomplish this by filtering out relationships where the user is
  # assigned and then joining the relationship table for the second time,
  # retrieving the mapped objects.
  #
  # We have a union here because using or_ to join both by destination and
  # source was not performing well (8s+ query times)
  mapped_objects = assignable_join(
      # Join by destination:
      related_assignables()).join(rel2, and_(
          case([
              (rel1.destination_type == "Person",
               rel1.source_id)
          ], else_=rel1.destination_id) == rel2.destination_id,
          case([
              (rel1.destination_type == "Person",
               rel1.source_type)
          ], else_=rel1.destination_type) == rel2.destination_type)
  ).union(assignable_join(
      # Join by source:
      related_assignables()).join(rel2, and_(
          case([
              (rel1.destination_type == "Person",
               rel1.source_id)
          ], else_=rel1.destination_id) == rel2.source_id,
          case([
              (rel1.destination_type == "Person",
               rel1.source_type)
          ], else_=rel1.destination_type) == rel2.source_type))
  )
  return mapped_objects.union(assigned_objects)


def objects_via_relationships_query(model, roles, user_id, context_not_role):
  """Creates a query that returns objects a user can access via mappings.

    Args:
        model: base model upon the roles are given
        roles: list of roles names to check
        user_id: id of the user
        context_not_role: use context instead of the role for the third column
            in the search api we need to return (obj_id, obj_type, context_id),
            but in ggrc_basic_permissions we need a role instead of a
            context_id (obj_id, obj_type, role_name)

    Returns:
        db.session.query object that selects the following columns:
            | id | type | role_name or context |
        Rows represent objects that are mapped to objects of the given model
        (where the user has a listed role) and the corresponding relationships.
  """
  _role = aliased(all_models.Role, name="r")
  _implications = aliased(all_models.ContextImplication, name="ci")
  _model = aliased(model, name="p")
  _relationship = aliased(all_models.Relationship, name="rl")
  _user_role = aliased(all_models.UserRole, name="ur")

  def _join_filter(query, cond):
    """Filter a query based on user roles

    Args:
        query (sqlalchemy.orm.query.Query): query to be filtered
        cond (sqlalchemy.sql.elements.BooleanClauseList): condition used for
            the initial model query

    Returns:
        query (sqlalchemy.orm.query.Query): object with applied conditions
    """
    user_role_cond = and_(_user_role.person_id == user_id,
                          _user_role.context_id == _implications.context_id)
    role_cond = and_(_user_role.role_id == _role.id,
                     _role.name.in_(roles))
    return query.join(_model, cond).join(
        _implications, _model.context_id == _implications.source_context_id).\
        join(_user_role, user_role_cond).\
        join(_role, role_cond).\
        distinct().\
        union(query.join(_model, cond).join(
            _implications, _model.context_id == _implications.context_id).
        join(_user_role, user_role_cond).
        join(_role, role_cond).
        distinct())

  def _add_relationship_join(query):
    # We do a UNION here because using an OR to JOIN both destination
    # and source causes a full table scan
    return _join_filter(query,
                        and_(_relationship.source_type == model.__name__,
                             _model.id == _relationship.source_id))\
        .union(_join_filter(
            query,
            and_(_relationship.destination_type == model.__name__,
                 _model.id == _relationship.destination_id)
        ))

  objects = _add_relationship_join(db.session.query(
      case([
          (_relationship.destination_type == model.__name__,
           _relationship.source_id.label('id'))
      ], else_=_relationship.destination_id.label('id')),
      case([
          (_relationship.destination_type == model.__name__,
           _relationship.source_type.label('type'))
      ], else_=_relationship.destination_type.label('type')),
      literal(None).label('context_id') if context_not_role else _role.name))

  # We also need to return relationships themselves:
  relationships = _add_relationship_join(db.session.query(
      _relationship.id, literal("Relationship"), _relationship.context_id))
  return objects.union(relationships)


def program_relationship_query(user_id, context_not_role=False):
  """Creates a query that returns objects a user can access via program.

    Args:
        user_id: id of the user
        context_not_role: use context instead of the role for the third column
            in the search api we need to return (obj_id, obj_type, context_id),
            but in ggrc_basic_permissions we need a role instead of a
            context_id (obj_id, obj_type, role_name)

    Returns:
        db.session.query object that selects the following columns:
            | id | type | role_name or context |
  """
  return objects_via_relationships_query(
      model=all_models.Program,
      roles=('ProgramEditor', 'ProgramOwner', 'ProgramReader'),
      user_id=user_id,
      context_not_role=context_not_role
  )


class CompletePermissionsProvider(object):
  """Permission provider set in the USER_PERMISSIONS_PROVIDER setting"""

  def __init__(self, _):
    pass

  def permissions_for(self, user):
    """Load user permissions and make sure they get loaded into session"""
    ret = UserPermissions()
    # force the permissions to be loaded into session, otherwise templates
    # that depend on the permissions being available in session may assert
    # the user has no permissions!
    ret.check_permissions()
    return ret

  def handle_admin_user(self, user):
    pass


class BasicUserPermissions(DefaultUserPermissions):
  """User permissions that aren't kept in session."""

  def __init__(self, user):
    self.user = user
    with benchmark('BasicUserPermissions > load permissions for user'):
      self.permissions = load_permissions_for(user)

  def _permissions(self):
    return self.permissions


class UserPermissions(DefaultUserPermissions):

  @property
  def _request_permissions(self):
    return getattr(g, '_request_permissions', None)

  @_request_permissions.setter
  def _request_permissions(self, value):
    setattr(g, '_request_permissions', value)

  def _permissions(self):
    self.check_permissions()
    return self._request_permissions

  def check_permissions(self):
    if not self._request_permissions:
      self.load_permissions()

  def get_email_for(self, user):
    return user.email if hasattr(user, 'email') else 'ANONYMOUS'

  def load_permissions(self):
    user = get_current_user()
    email = self.get_email_for(user)
    self._request_permissions = {}
    self._request_permissions['__user'] = email
    if user is None or user.is_anonymous():
      self._request_permissions = {}
    else:
      with benchmark('load_permissions'):
        self._request_permissions = load_permissions_for(user)


def collect_permissions(src_permissions, context_id, permissions):
  for action, resource_permissions in src_permissions.items():
    if not resource_permissions:
      permissions.setdefault(action, dict())
    for resource_permission in resource_permissions:
      if type(resource_permission) in [str, unicode]:
        resource_type = str(resource_permission)
        condition = None
      else:
        resource_type = str(resource_permission['type'])
        condition = resource_permission.get('condition', None)
        terms = resource_permission.get('terms', [])
      permissions.setdefault(action, {})\
          .setdefault(resource_type, dict())\
          .setdefault('contexts', list())
      if context_id is not None:
        permissions[action][resource_type]['contexts'].append(context_id)
      elif condition in (None, "forbid"):
        permissions[action][resource_type]['contexts'].append(context_id)
      if condition:
        permissions[action][resource_type]\
            .setdefault('conditions', dict())\
            .setdefault(context_id, list())\
            .append({
                'condition': condition,
                'terms': terms,
            })


def query_memcache(key):
  """Check if cached permissions are available

  Args:
      key (string): key of the stored permissions
  Returns:
      cache (memcache_client): memcache client or None if caching
                               is not available
      permissions_cache (dict): dict with all permissions or None if there
                                was a cache miss
  """
  if not getattr(settings, 'MEMCACHE_MECHANISM', False):
    return None, None

  cache = _get_cache_manager().cache_object.memcache_client
  cached_keys_set = cache.get('permissions:list') or set()
  if key not in cached_keys_set:
    # We set the permissions:list variable so that we are able to batch
    # remove all permissions related keys from memcache
    cached_keys_set.add(key)
    cache.set('permissions:list', cached_keys_set, PERMISSION_CACHE_TIMEOUT)
    return cache, None

  permissions_cache = cache.get(key)
  if permissions_cache:
    # If the key is both in permissions:list and in memcache itself
    # it is safe to return the cached permissions
    return cache, permissions_cache
  return cache, None


def load_default_permissions(permissions):
  """Load default permissions for all users

  Args:
      permissions (dict): dict where the permissions will be stored
  Returns:
      None
  """
  default_permissions = {
      "read": [
          "Help",
          "CustomAttributeDefinition",
          {
              "type": "CustomAttributeValue",
              "terms": {
                  "list_property": "owners",
                  "value": "$current_user"
              },
              "condition": "contains"
          },
          {
              "type": "NotificationConfig",
              "terms": {
                  "property_name": "person",
                  "value": "$current_user"
              },
              "condition": "is"
          },
      ],
      "create": [
          {
              "type": "NotificationConfig",
              "terms": {
                  "property_name": "person",
                  "value": "$current_user"
              },
              "condition": "is"
          },
      ],
      "update": [
          {
              "type": "NotificationConfig",
              "terms": {
                  "property_name": "person",
                  "value": "$current_user"
              },
              "condition": "is"
          },
      ]
  }
  collect_permissions(default_permissions, None, permissions)


def load_bootstrap_admin(user, permissions):
  """Add bootstrap admin permissions if user is in BOOTSTRAP_ADMIN_USERS

  Args:
      user (Person): Person object
      permissions (dict): dict where the permissions will be stored
  Returns:
      None
  """
  # Add `ADMIN_PERMISSION` for "bootstrap admin" users
  if hasattr(settings, 'BOOTSTRAP_ADMIN_USERS') \
     and user.email in settings.BOOTSTRAP_ADMIN_USERS:
    admin_permissions = {
        DefaultUserPermissions.ADMIN_PERMISSION.action: [
            DefaultUserPermissions.ADMIN_PERMISSION.resource_type
        ]
    }
    collect_permissions(
        admin_permissions,
        DefaultUserPermissions.ADMIN_PERMISSION.context_id,
        permissions)


def load_user_roles(user, permissions):
  """Load all user roles for user

  Args:
      user (Person): Person object
      permissions (dict): dict where the permissions will be stored
  Returns:
      source_contexts_to_rolenames (dict): Role names for contexts
  """
  # Add permissions from all DB-managed roles
  user_roles = db.session.query(UserRole)\
      .options(
          sqlalchemy.orm.undefer_group('UserRole_complete'),
          sqlalchemy.orm.undefer_group('Role_complete'),
          sqlalchemy.orm.joinedload('role'))\
      .filter(UserRole.person_id == user.id)\
      .order_by(UserRole.updated_at.desc())\
      .all()

  source_contexts_to_rolenames = {}
  for user_role in user_roles:
    source_contexts_to_rolenames.setdefault(
        user_role.context_id, list()).append(user_role.role.name)
    if isinstance(user_role.role.permissions, dict):
      collect_permissions(
          user_role.role.permissions, user_role.context_id, permissions)
  return source_contexts_to_rolenames


def load_all_context_implications(source_contexts_to_rolenames):
  """Load context implications based on rolenames

  Args:
      source_contexts_to_rolenames (dict): Role names for contexts
  Returns:
      all_context_implications (list): List of possible context implications
  """
  # apply role implications per context implication
  all_context_implications = db.session.query(ContextImplication)
  keys = [k for k in source_contexts_to_rolenames.keys() if k is not None]
  if keys and None in source_contexts_to_rolenames:
    all_context_implications = all_context_implications.filter(
        or_(
            ContextImplication.source_context_id.is_(None),
            ContextImplication.source_context_id.in_(keys),
        )).all()
  elif keys:
    all_context_implications = all_context_implications.filter(
        ContextImplication.source_context_id.in_(keys)).all()
  elif None in source_contexts_to_rolenames:
    all_context_implications = all_context_implications.filter(
        ContextImplication.source_context_id.is_(None)).all()
  else:
    all_context_implications = []
  return all_context_implications


def load_implied_roles(permissions, source_contexts_to_rolenames,
                       all_context_implications):
  """Load roles from implied contexts

  Args:
      permissions (dict): dict where the permissions will be stored
      source_contexts_to_rolenames (dict): Role names for contexts
      all_context_implications (list): List of possible context implications
  Returns:
      None
  """
  # Gather all roles required by context implications
  implied_context_to_implied_roles = {}
  all_implied_roles_set = set()
  for context_implication in all_context_implications:
    for rolename in source_contexts_to_rolenames.get(
            context_implication.source_context_id, []):
      implied_role_names_list = implied_context_to_implied_roles.setdefault(
          context_implication.context_id, list())
      implied_role_names = lookup_role_implications(
          rolename, context_implication)
      all_implied_roles_set.update(implied_role_names)
      implied_role_names_list.extend(implied_role_names)
  # If some roles are required, query for them in bulk
  all_implied_roles_by_name = {}
  if implied_context_to_implied_roles and all_implied_roles_set:
    implied_roles = db.session.query(Role)\
        .filter(Role.name.in_(all_implied_roles_set))\
        .options(sqlalchemy.orm.undefer_group('Role_complete'))\
        .all()
    for implied_role in implied_roles:
      all_implied_roles_by_name[implied_role.name] = implied_role
  # Now aggregate permissions resulting from these roles
  for implied_context_id, implied_rolenames \
          in implied_context_to_implied_roles.items():
    if implied_context_id is None:
      continue
    for implied_rolename in implied_rolenames:
      implied_role = all_implied_roles_by_name[implied_rolename]
      collect_permissions(
          implied_role.permissions, implied_context_id, permissions)


def load_object_owners(user, permissions):
  """Load object owners permissions

  Args:
      user (Person): Person object
      permissions (dict): dict where the permissions will be stored
  Returns:
      None
  """
  with benchmark("load_object_owners > get owners"):
    object_owners = db.session.query(
        ObjectOwner.ownable_type, ObjectOwner.ownable_id
    ).filter(ObjectOwner.person_id == user.id).all()
  with benchmark("load_object_owners > update permissions"):
    actions = ("read", "create", "update", "delete", "view_object_page")
    for ownable_type, ownable_id in object_owners:
      for action in actions:
        permissions.setdefault(action, {})\
            .setdefault(ownable_type, {})\
            .setdefault('resources', list())\
            .append(ownable_id)


def context_relationship_query(contexts):
  """Load a list of objects related to the given contexts

  Args:
    contexts (list(int)): A list of context ids
  Returns:
    objects (list((id, type, None))): Related objects
  """
  if not len(contexts):
    return []

  _context = aliased(all_models.Context, name="c")
  _relationship = aliased(all_models.Relationship, name="rl")

  headers = (case([
      (_relationship.destination_type == _context.related_object_type,
       _relationship.source_id.label('id'))
  ], else_=_relationship.destination_id.label('id')),
      case([
          (_relationship.destination_type == _context.related_object_type,
           _relationship.source_type.label('type'))
      ], else_=_relationship.destination_type.label('type')),
      literal(None))

  return db.session.query(*headers).join(_context, and_(
      _context.id.in_(contexts),
      _relationship.destination_id == _context.related_object_id,
      _relationship.destination_type == _context.related_object_type,
  )).union(db.session.query(*headers).join(_context, and_(
      _context.id.in_(contexts),
      _relationship.source_id == _context.related_object_id,
      _relationship.source_type == _context.related_object_type,
  ))).all()


def load_context_relationships(permissions):
  """Load context relationship permissions

  Args:
      user (Person): Person object
      permissions (dict): dict where the permissions will be stored
  Returns:
      None
  """
  read_contexts = set(
      permissions.get('read', {}).
      get('Program', {}).
      get('contexts', []) +
      permissions.get('read', {}).
      get('Audit', {}).
      get('contexts', []))
  write_contexts = set(
      permissions.get('update', {}).
      get('Program', {}).
      get('contexts', []) +
      permissions.get('update', {}).
      get('Audit', {}).
      get('contexts', []))
  read_only_contexts = read_contexts - write_contexts

  read_objects = context_relationship_query(read_only_contexts)
  for res in read_objects:
    id_, type_, _ = res
    actions = ["read", "view_object_page"]
    for action in actions:
      permissions.setdefault(action, {})\
          .setdefault(type_, {})\
          .setdefault('resources', list())\
          .append(id_)

  write_objects = context_relationship_query(write_contexts)
  for res in write_objects:
    id_, type_, role_name = res
    actions = ["read", "view_object_page", "create", "update", "delete"]
    for action in actions:
      permissions.setdefault(action, {})\
          .setdefault(type_, {})\
          .setdefault('resources', list())\
          .append(id_)


def load_assignee_relationships(user, permissions):
  """Load assignee relationship permissions

  Args:
      user (Person): Person object
      permissions (dict): dict where the permissions will be stored
  Returns:
      None
  """
  for id_, type_, role_name in objects_via_assignable_query(user.id, False):
    actions = ["read", "view_object_page"]
    if role_name == "RUD":
      actions += ["update", "delete"]
    for action in actions:
      permissions.setdefault(action, {})\
          .setdefault(type_, {})\
          .setdefault('resources', list())\
          .append(id_)


def load_personal_context(user, permissions):
  """Load personal context for user

  Args:
      user (Person): Person object
      permissions (dict): dict where the permissions will be stored
  Returns:
      None
  """
  personal_context = _get_or_create_personal_context(user)

  permissions.setdefault('__GGRC_ADMIN__', {})\
      .setdefault('__GGRC_ALL__', dict())\
      .setdefault('contexts', list())\
      .append(personal_context.id)


def load_backlog_workflows(permissions):
  """Load permissions for backlog workflows

  Args:
      permissions (dict): dict where the permissions will be stored
  Returns:
      None
  """
  # add permissions for backlog workflows to everyone
  actions = ["read", "edit", "update"]
  _types = ["Workflow", "Cycle", "CycleTaskGroup",
            "CycleTaskGroupObjectTask", "TaskGroup", "CycleTaskEntry"]
  for _, _, wf_context_id in backlog_workflows().all():
    for _type in _types:
      if _type == "CycleTaskGroupObjectTask":
        actions += ["delete"]
      if _type == "CycleTaskEntry":
        actions += ["create"]
      for action in actions:
        permissions.setdefault(action, {})\
            .setdefault(_type, {})\
            .setdefault('contexts', list())\
            .append(wf_context_id)


def store_results_into_memcache(permissions, cache, key):
  """Load personal context for user

  Args:
      permissions (dict): dict where the permissions will be stored
      cache (cache_manager): Cache manager that should be used for storing
                             permissions
      key (string): key of under which permissions should be stored
  Returns:
      None
  """
  if cache is None:
    return

  cached_keys_set = cache.get('permissions:list') or set()
  if key in cached_keys_set:
    # We only add the permissions to the cache if the
    # key still exists in the permissions:list after
    # the query has executed.
    cache.set(key, permissions, PERMISSION_CACHE_TIMEOUT)


def load_permissions_for(user):
  """Permissions is dictionary that can be exported to json to share with
  clients. Structure is:
  ..

    permissions[action][resource_type][contexts]
                                      [conditions][context][context_conditions]

  'action' is one of 'create', 'read', 'update', 'delete'.
  'resource_type' is the name of a valid GGRC resource type.
  'contexts' is a list of context_id where the action is allowed.
  'conditions' is a dictionary of 'context_conditions' indexed by 'context'
    where 'context' is a context_id.
  'context_conditions' is a list of dictionaries with 'condition' and 'terms'
    keys.
  'condition' is the string name of a conditional operator, such as 'contains'.
  'terms' are the arguments to the 'condition'.
  """
  permissions = {}
  key = 'permissions:{}'.format(user.id)

  with benchmark("load_permissions > query memcache"):
    cache, result = query_memcache(key)
    if result:
      return result

  with benchmark("load_permissions > load default permissions"):
    load_default_permissions(permissions)

  with benchmark("load_permissions > load bootstrap admins"):
    load_bootstrap_admin(user, permissions)

  with benchmark("load_permissions > load user roles"):
    source_contexts_to_rolenames = load_user_roles(user, permissions)

  with benchmark("load_permissions > load context implications"):
    all_context_implications = load_all_context_implications(
        source_contexts_to_rolenames)

  with benchmark("load_permissions > load implied roles"):
    load_implied_roles(permissions, source_contexts_to_rolenames,
                       all_context_implications)

  with benchmark("load_permissions > load object owners"):
    load_object_owners(user, permissions)

  with benchmark("load_permissions > load context relationships"):
    load_context_relationships(permissions)

  with benchmark("load_permissions > load assignee relationships"):
    load_assignee_relationships(user, permissions)

  with benchmark("load_permissions > load personal context"):
    load_personal_context(user, permissions)

  with benchmark("load_permissions > load backlog workflows"):
    load_backlog_workflows(permissions)

  # If user has 'update' rights for 'Assessment' he should have the same
  # rights for linked 'Document'. In such case user have opportunity to
  # remove mapping from 'Assessment' to 'Document'.
  relationship_objs = db.session.query(all_models.Relationship).filter(
      and_(
          all_models.Relationship.source_type == "Assessment",
          all_models.Relationship.destination_type == "Document"
      )
  ).all()
  relationship_dict = {}
  for rel in relationship_objs:
    relationship_dict.setdefault(rel.source_id, [])
    relationship_dict[rel.source_id].append(rel.id)
  permissions.setdefault(
      "delete", {}).setdefault("Relationship", {}).setdefault("resources", [])
  for assess_id in permissions.get("update", {}).get(
          "Assessment", {}).get("resources", []):
    if assess_id in relationship_dict.keys():
      permissions["delete"]["Relationship"]["resources"].extend(
          relationship_dict[assess_id]
      )
  permissions["delete"]["Relationship"]["resources"] = list(
      set(permissions["delete"]["Relationship"]["resources"])
  )

  with benchmark("load_permissions > store results into memcache"):
    store_results_into_memcache(permissions, cache, key)

  return permissions


def backlog_workflows():
  """Creates a query that returns all backlog workflows which
  all users can access.

    Returns:
        db.session.query object that selects the following columns:
            | id | type | context_id |
  """
  _workflow = aliased(all_models.Workflow, name="wf")
  return db.session.query(_workflow.id,
                          literal("Workflow").label("type"),
                          _workflow.context_id)\
      .filter(_workflow.kind == "Backlog")


def _get_or_create_personal_context(user):
  personal_context = user.get_or_create_object_context(
      context=1,
      name='Personal Context for {0}'.format(user.id),
      description='')
  personal_context.modified_by = get_current_user()
  db.session.add(personal_context)
  db.session.flush()
  return personal_context


@Resource.model_posted.connect_via(Program)
def handle_program_post(sender, obj=None, src=None, service=None):
  db.session.flush()
  # get the personal context for this logged in user
  user = get_current_user()
  personal_context = _get_or_create_personal_context(user)
  context = obj.build_object_context(
      context=personal_context,
      name='{object_type} Context {timestamp}'.format(
          object_type=service.model.__name__,
          timestamp=datetime.datetime.now()),
      description='',
  )
  context.modified_by = get_current_user()

  db.session.add(obj)
  db.session.flush()
  db.session.add(context)
  db.session.flush()
  obj.contexts.append(context)
  obj.context = context

  # add a user_roles mapping assigning the user creating the program
  # the ProgramOwner role in the program's context.
  program_owner_role = basic_roles.program_owner()
  user_role = UserRole(
      person=get_current_user(),
      role=program_owner_role,
      context=context,
      modified_by=get_current_user())
  # pass along a temporary attribute for logging the events.
  user_role._display_related_title = obj.title
  db.session.add(user_role)
  db.session.flush()

  # Create the context implication for Program roles to default context
  db.session.add(ContextImplication(
      source_context=context,
      context=None,
      source_context_scope='Program',
      context_scope=None,
      modified_by=get_current_user()))

  if not src.get('private'):
    # Add role implication - all users can read a public program
    add_public_program_context_implication(context)


def add_public_program_context_implication(context, check_exists=False):
  if check_exists and db.session.query(ContextImplication)\
      .filter(
          and_(ContextImplication.context_id == context.id,
               ContextImplication.source_context_id.is_(None))).count() > 0:
    return
  db.session.add(ContextImplication(
      source_context=None,
      context=context,
      source_context_scope=None,
      context_scope='Program',
      modified_by=get_current_user(),
  ))


def create_audit_context(audit):
  # Create an audit context
  context = audit.build_object_context(
      context=audit.context,
      name='Audit Context {timestamp}'.format(
          timestamp=datetime.datetime.now()),
      description='',
  )
  context.modified_by = get_current_user()
  db.session.add(context)
  db.session.flush()

  # Create the program -> audit implication
  db.session.add(ContextImplication(
      source_context=audit.context,
      context=context,
      source_context_scope='Program',
      context_scope='Audit',
      modified_by=get_current_user(),
  ))

  # Create the audit -> program implication
  db.session.add(ContextImplication(
      source_context=context,
      context=audit.context,
      source_context_scope='Audit',
      context_scope='Program',
      modified_by=get_current_user(),
  ))

  db.session.add(audit)

  # Create the role implication for Auditor from Audit for default context
  db.session.add(ContextImplication(
      source_context=context,
      context=None,
      source_context_scope='Audit',
      context_scope=None,
      modified_by=get_current_user(),
  ))
  db.session.flush()

  # Place the audit in the audit context
  audit.context = context


@Resource.collection_posted.connect_via(Audit)
def handle_audit_post(sender, objects=None, sources=None):
  for obj, src in itertools.izip(objects, sources):
    if not src.get("operation", None):
      db.session.flush()
      create_audit_context(obj)


@Resource.model_deleted.connect
def handle_resource_deleted(sender, obj=None, service=None):
  if obj.context \
     and obj.context.related_object_id \
     and obj.id == obj.context.related_object_id \
     and obj.__class__.__name__ == obj.context.related_object_type:
    db.session.query(UserRole) \
        .filter(UserRole.context_id == obj.context_id) \
        .delete()
    db.session.query(ContextImplication) \
        .filter(
            or_(ContextImplication.context_id == obj.context_id,
                ContextImplication.source_context_id == obj.context_id))\
        .delete()
    # Deleting the context itself is problematic, because unattached objects
    #   may still exist and cause a database error.  Instead of implicitly
    #   cascading to delete those, just leave the `Context` object in place.
    #   It and its objects will be visible *only* to Admin users.
    # db.session.delete(obj.context)


# Removed because this is now handled purely client-side, but kept
# here as a reference for the next one.
# @BaseObjectView.extension_contributions.connect_via(Program)
def contribute_to_program_view(sender, obj=None, context=None):
  if obj.context_id is not None and \
     rbac_permissions.is_allowed_read('Role', None, 1) and \
     rbac_permissions.is_allowed_read('UserRole', None, obj.context_id) and \
     rbac_permissions.is_allowed_create('UserRole', None, obj.context_id) and \
     rbac_permissions.is_allowed_update('UserRole', None, obj.context_id) and \
     rbac_permissions.is_allowed_delete('UserRole', None, obj.context_id):
    return 'permissions/programs/_role_assignments.haml'
  return None


@app.context_processor
def authorized_users_for():
  return {'authorized_users_for': UserRole.role_assignments_for}


def contributed_services():
  """The list of all collections provided by this extension."""
  return [
      service('roles', Role),
      service('user_roles', UserRole),
  ]


def contributed_object_views():
  from ggrc.views.registry import object_view
  return [
      object_view(Role)
  ]


def contributed_column_handlers():
  return COLUMN_HANDLERS


ROLE_DECLARATIONS = BasicRoleDeclarations()
ROLE_IMPLICATIONS = BasicRoleImplications()

contributed_get_ids_related_to = get_ids_related_to
