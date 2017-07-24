# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Contains WithAction mixin.

A mixin for processing actions on an object in the scope of put request .
"""

from collections import namedtuple, defaultdict

from ggrc import db
from ggrc.login import get_current_user
from ggrc.models.comment import Comment
from ggrc.models.document import Document
from ggrc.models.snapshot import Snapshot
from ggrc.models.exceptions import ValidationError
from ggrc.models.relationship import Relationship
from ggrc.models.relationship import RelationshipAttr


class WithAction(object):
  """Mixin for add/remove map/unmap actions processing"""

  _update_attrs = ["actions"]
  _operation_order = ["add_related",
                      "remove_related"]
  _object_list = {"Document": Document,
                  "Comment": Comment,
                  "Snapshot": Snapshot}
  _actions = None
  _added = None  # collect added objects for signals sending
  _deleted = None  # collect deleted objects fro signals sending

  def actions(self, value):
    """Save actions for further processing"""
    if value:
      self._actions = value.get("actions", None)

  def _validate_actions(self):
    """Validate operation types"""
    for operation in self._actions:
      if operation not in self._operation_order:
        raise ValueError('Invalid action: {type}'.format(type=operation))

  def _process_operation(self, operation):
    """Process operation actions"""
    for action in self._actions[operation]:
      # get object class
      obj_type = action.get("type", None)
      if not obj_type:
        raise ValidationError('type is not defined')

      obj_class = self._object_list.get(obj_type, None)
      if not obj_class:
        raise ValueError('Invalid action type: {type}'.format(type=obj_type))

      # get handler class
      action_type = '{type}Action'.format(type=obj_type)
      action_class = getattr(self, action_type)
      if not action_class:
        raise ValueError('Invalid action type: {type}'.format(type=obj_type))

      # process action
      added, deleted = getattr(action_class(), operation)(self, action)

      # collect added/deleted objects
      self._added.extend(added)
      self._deleted.extend(deleted)

  def process_actions(self):
    """Process actions"""
    if not self._actions:
      return {}, []

    self._validate_actions()

    self._added = []
    self._deleted = []

    for operation in self._operation_order:
      if operation not in self._actions:
        continue

      if not self._actions[operation]:
        raise ValueError('Empty actions list')

      self._process_operation(operation)

    # collect added/deleted objects for signals sending
    added = defaultdict(list)
    for obj in self._added:
      added[obj.__class__].append(obj)

    return added, self._deleted

  class BaseAction(object):
    """Base action"""

    AddRelated = namedtuple("AddRelated", ["id", "type"])
    MapRelated = namedtuple("MapRelated", ["id", "type"])
    RemoveRelated = namedtuple("RemoveRelated", ["id", "type"])

    def add_related(self, parent, _action):
      """Add/map object to parent"""
      added = []
      if _action.get("id", None):
        action = self._validate(_action, self.MapRelated)
        obj = self._get(action)
      else:
        action = self._validate(_action, self.AddRelated)
        obj = self._create(action, parent)
        added.append(obj)

      rel = Relationship(source=parent,
                         destination=obj,
                         context=parent.context)
      added.append(rel)
      return added, []

    @staticmethod
    def _validate(_action, ntuple):
      try:
        return ntuple(**_action)
      except TypeError:
        raise ValidationError("Missed action parameters")

    # pylint: disable=unused-argument,no-self-use
    def _create(self, action, parent):
      raise ValidationError("Can't create {type} object".format(
          type=action.type))

    def _get(self, action):
      """Get object specified in action"""
      if not action.id:
        raise ValueError("id is not defined")
      # pylint: disable=protected-access
      obj_class = WithAction._object_list[action.type]
      obj = obj_class.query. get(action.id)
      if not obj:
        raise ValueError(
            'Object not found: {type} {id}'.format(type=action.type,
                                                   id=action.id))
      return obj

    def remove_related(self, parent, _action):
      """Remove relationship"""
      action = self._validate(_action, self.RemoveRelated)
      deleted = []
      obj = self._get(action)
      rel = Relationship.get_related_query(parent, obj).first()
      if rel:
        rel = Relationship.query.get(rel.id)
        db.session.delete(rel)
        deleted.append(rel)
      return [], deleted

  class DocumentAction(BaseAction):
    """Document action"""

    AddRelated = namedtuple("AddRelated", ["id",
                                           "type",
                                           "document_type",
                                           "link",
                                           "title"])

    def _create(self, action, parent):
      if action.document_type not in Document.VALID_DOCUMENT_TYPES:
        raise ValueError('Unknown document_type: {type}'.format(
            type=action.document_type))
      obj = Document(link=action.link,
                     title=action.title,
                     document_type=action.document_type,
                     context=parent.context)
      return obj

  class CommentAction(BaseAction):
    """Comment action"""

    AddRelated = namedtuple("AddRelated", ["id",
                                           "type",
                                           "description",
                                           "custom_attribute_definition_id"])

    def _create(self, action, parent):
      # get assignee type
      rel = Relationship.get_related_query(
          parent, get_current_user()
      ).join(RelationshipAttr).filter(
          RelationshipAttr.attr_name == "AssigneeType"
      ).first()
      if rel:
        assignee_type = rel.attrs["AssigneeType"]
      else:
        assignee_type = None
      # create object
      cad_id = action.custom_attribute_definition_id
      if not cad_id:
        obj = Comment(description=action.description,
                      assignee_type=assignee_type,
                      context=parent.context)
      else:
        obj = Comment(description=action.description,
                      custom_attribute_definition_id=cad_id,
                      assignee_type=assignee_type,
                      context=parent.context)

      return obj

  class SnapshotAction(BaseAction):
    """Snapshot action"""
