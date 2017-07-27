# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Mixin for automatic status changes"""

import datetime

from sqlalchemy import event
from sqlalchemy import inspect
from sqlalchemy.orm.session import Session

from ggrc import db
from ggrc.models import relationship
from ggrc.services import signals
from ggrc.models.mixins import statusable


class AutoStatusChangeable(object):
  """A mixin for automatic status changes.

  Enables automatic transitioning of objects on any edit in cases when an
  object is in one of the DONE states, or in the START state.
  """

  __lazy_init__ = True
  _tracked_attrs = set()

  FIRST_CLASS_EDIT = ({statusable.Statusable.START_STATE} |
                      statusable.Statusable.DONE_STATES)
  ASSIGNABLE_EDIT = statusable.Statusable.DONE_STATES

  @staticmethod
  def _date_has_changes(attr):
    """Detect if date attribute changed.

    Date fields are always interpreted as changed because incoming data is
    of type datetime.datetime, while database field has type datetime.date.

    This function normalizes this and performs the correct check.

    Args:
      attr: (datetime.date|datetime.datetime) Attribute value
    Returns:
      A boolean representing if models date attribute really changed.
    """
    if not attr.history.added or not attr.history.deleted:
      return False
    added, deleted = attr.history.added[0], attr.history.deleted[0]
    if isinstance(added, datetime.datetime):
      added = added.date()
    return added != deleted

  @classmethod
  def _has_changes(cls, obj, attr):
    """Detects if object attribute has changes

    Args:
      obj: (db.Model instance) Object on which to perform attribute inspection.
      attr: (string) Attribute to inspect
    Returns:
      A boolean representing if models attribute changed.
    """
    attr = getattr(inspect(obj).attrs, attr)
    if (isinstance(attr.value, datetime.date) or
       isinstance(attr.value, datetime.datetime)):
      return cls._date_has_changes(attr)
    return attr.history.has_changes()

  @classmethod
  def _get_object_from_relationship(cls, model, rel):
    """Get instance of an model object from relationship.

    Args:
      model: (db.Model class) Class whose instance we want to retrieve from
        relationship.
      rel: (Relationship) Instance of relationship object.
    Returns:
      An instance of class model.
    """
    if rel.source.type == model.__name__:
      return rel.source
    return rel.destination

  @classmethod
  def init(cls, model):
    """Initialisation method to run after models have been initialized.

    Args:
      model: (db.Model class) Class on which to run set_handlers method.
    """
    cls.set_handlers(model)

  @staticmethod
  def adjust_status(model, obj):
    """Switches state on object to the PROGRESS_STATE

    Args:
      model: (db.Model class) Class from which to read PROGRESS_STATE value.
      obj: (db.Model instance) object on which to perform status transition
        operation.
    """
    obj.status = model.PROGRESS_STATE
    db.session.add(obj)

  @classmethod
  def handle_first_class_edit(cls, model, obj, rel=None, method=None):
    """Handles first class edit

    Performs check whether object received first class edit (ordinary edit)
    that should transition object to PROGRESS_STATE from either: START_STATE
    or one of END_STATES and sets obj._need_status_reset to True if the state
    transition is needed.

    Args:
      model: (db.Model class) Class from which to read FIRST_CLASS_EDIT
        property.
      obj: (db.Model instance) Object on which to perform operations.
      rel: (Relationship) Relationship object, needed here to maintain equal
        type signature with handle_person_edit.
      method: (string) HTTP method used that triggered signal
    """

    # pylint: disable=unused-argument,protected-access

    if obj.status in model.FIRST_CLASS_EDIT:
      obj._need_status_reset = True

  @classmethod
  def adjust_status_before_flush(cls, session, flush_context, instances):
    """Reset status of AutoStatusChangeable objects with _need_status_reset.

    Is registered to listen for 'before_flush' events on a later stage.
    """

    # pylint: disable=unused-argument

    for obj in session.identity_map.values():
      if (isinstance(obj, AutoStatusChangeable) and
              getattr(obj, '_need_status_reset', False)):
        cls.adjust_status(type(obj), obj)
        delattr(obj, '_need_status_reset')

  @classmethod
  def handle_person_edit(cls, model, obj, rel, method):
    """Handles person edit

    Args:
      model: (db.Model class) Class from which to read ASSIGNABLE_EDIT
        property.
      obj: (db.Model instance) Object on which to perform operations.
      rel: (Relationship) Relationship whose attribute have to be inspected for
        changes.
      method: (string) HTTP method used that triggered signal
    """
    adjust_state = False

    if method == "POST":
      # On relationship creation inspect(rel) sometime shows relationship
      # attributes as unchanged and sometimes as added.
      # But because POST can only ever be issued for creation, we can use this
      # as a guarantee that this was an editable event that should adjust
      # status.
      unchanged = inspect(rel).attrs.relationship_attrs.history.unchanged
      added = inspect(rel).attrs.relationship_attrs.history.added
      attr_changed = ({ra.attr_name for ra in unchanged} |
                      {ra.attr_name for ra in added})
    else:
      # Ensures that we only adjust status for AssigneeType relationship
      # attribute.
      added = inspect(rel).attrs.relationship_attrs.history.added
      deleted = inspect(rel).attrs.relationship_attrs.history.deleted
      attr_changed = ({ra.attr_name for ra in deleted} |
                      {ra.attr_name for ra in added})

    if obj.status in model.ASSIGNABLE_EDIT:
      # When object attributes are added or edited, adjust. If user still has
      # some other role, operation is considered edit.
      if "AssigneeType" in attr_changed:
        adjust_state = True

      # When user has no more roles on an object, relationship is deleted.
      if method == "DELETE":
        adjust_state = True

    if adjust_state:
      cls.adjust_status(model, obj)

  @staticmethod
  def _has_custom_attr_changes(obj):
    """Check if an object had any of its custom attribute values changed.

    Initially setting a custom attribue's value to a falsy value, i.e. when
    there was no old value deleted, is *not* considered a change.

    If given None or if the object does not have any custom attributes, False
    is returned.

    Args:
      obj: (db.Model instance) An object to check

    Returns:
      True or False depending whether any of the obejct's custom attribute
      values have been modified.
    """
    if not getattr(obj, "custom_attribute_values", None):
      return False  # also exits if obj itself is None

    histories = (
        inspect(value).attrs.get(attr_name).history
        for value in obj.custom_attribute_values
        for attr_name in ("attribute_value", "attribute_object_id")
    )
    for attr_history in histories:
      added, _, deleted = attr_history
      if attr_history.has_changes() and (any(added) or deleted):
        return True
    return False

  @classmethod  # noqa: C901  # ignore flake8 method too complex warning
  def set_handlers(cls, model):
    """Sets up handlers of various events

    Args:
      model: Class on which handlers will be set up.
    """
    @signals.Restful.model_put.connect_via(model)
    def handle_object_put(sender, obj=None, src=None, service=None):
      """Handles object PUT operation

      Handles edit operation submitted to object.

      See blinker library documentation for other parameters (all necessary).

      Args:
        obj: (db.Model instance) Object on which we will perform manipulation.
      """
      # pylint: disable=unused-argument,unused-variable,protected-access

      # this needs to be imported here (and not on the top of the file) due to
      # a circular dependency between Assessment and AutoStatusChangeable
      from ggrc.models.assessment import Assessment

      has_attr_changes = any(
          cls._has_changes(obj, attr)
          for attr in model._tracked_attrs
      )

      # At the time of writing (2016-09-29) only Assessment objects use a new
      # Custom Attribute API, thus detecting CA changes for other object types
      # does not work correctly. For the latter, we simply assume there were no
      # CA changes, effectively disabling that check.
      if sender is Assessment:
        has_ca_changes = cls._has_custom_attr_changes(obj)
      else:
        has_ca_changes = False

      if (has_attr_changes or has_ca_changes) and model.FIRST_CLASS_EDIT:
        cls.handle_first_class_edit(model, obj)

    @signals.Signals.custom_attribute_changed.connect_via(model)
    def handle_custom_attribute_save(sender, obj=None, src=None, service=None):
      """Handles custom attribute save operation

      Handles INSERT or UPDATE(ish, because custom attributes are hackish)
      operations performed on custom attributes.

      See blinker library documentation for other parameters (all necessary).

      Args:
        obj: (db.Model instance) Object on which we will perform manipulation.
      """
      # pylint: disable=unused-argument,unused-variable

      cls.handle_first_class_edit(model, obj)

    @signals.Restful.model_posted.connect_via(relationship.Relationship)
    @signals.Restful.model_put.connect_via(relationship.Relationship)
    @signals.Restful.model_deleted.connect_via(relationship.Relationship)
    def handle_relationship(sender, obj=None, src=None, service=None):
      """Handle creation of relationships that can change object status.

      Adding or removing assigable persons (Assignees, Creators, Verifiers,
      etc.) moves object back to PROGRESS_STATE.

      Adding evidence moves object back to to PROGRESS_STATE.

      See blinker library documentation for other parameters (all necessary).

      Args:
        obj: (db.Model instance) Object on which we will perform manipulation.
      """
      # pylint: disable=unused-argument,unused-variable

      endpoints = {obj.source.type, obj.destination.type}
      if model.__name__ in endpoints:
        target_object = cls._get_object_from_relationship(model, obj)

        handlers = {
            "Document": cls.handle_first_class_edit,
            "Person": cls.handle_person_edit
        }
        for k in handlers.keys():
          if k in endpoints:
            handlers[k](model, target_object, obj,
                        method=service.request.method)


# pylint: disable=fixme
# TODO: find a way to listen for updates only for classes that use
# AutoStatusChangeable, not for every flush event for every session
event.listen(Session, 'before_flush',
             AutoStatusChangeable.adjust_status_before_flush)
