# -*- coding: utf-8 -*-

# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Notification handlers for object in the ggrc module.

This module contains all function needed for handling notification objects
needed by ggrc notifications.
"""

# pylint: disable=too-few-public-methods

from collections import namedtuple
from datetime import date
from functools import partial
from itertools import chain, izip
from operator import attrgetter

from enum import Enum

from sqlalchemy import inspect
from sqlalchemy import and_
from sqlalchemy.sql.expression import true

from ggrc import db
from ggrc.services import signals
from ggrc import models
from ggrc.models.mixins.statusable import Statusable


class Transitions(Enum):
  """Assesment state transitions names."""
  TO_STARTED = "assessment_started"
  TO_COMPLETED = "assessment_completed"
  TO_REVIEW = "assessment_ready_for_review"
  TO_VERIFIED = "assessment_verified"
  TO_REOPENED = "assessment_reopened"


IdValPair = namedtuple("IdValPair", ["id", "val"])


def _add_notification(obj, notif_type, when=None):
  """Add notification for an object.

  Args:
    obj (Model): an object for which we want te add a notification.
    notif_type (NotificationType): type of notification that we want to store.
    when (datetime): date and time when we want the notification to be sent.
      default value is now.
  """
  if not notif_type:
    return
  if not when:
    when = date.today()
  db.session.add(models.Notification(
      object=obj,
      send_on=when,
      notification_type=notif_type,
  ))


def _has_unsent_notifications(notif_type, obj):
  """Helper for searching unsent notifications.

  Args:
    notify_type (NotificationType): type of the notifications we're looking
      for.
    obj (sqlalchemy model): Object for which we're looking for notifications.

  Returns:
    True if there are any unsent notifications of notif_type for the given
    object, and False otherwise.
  """
  Notification = models.Notification  # pylint: disable=invalid-name

  return db.session.query(models.Notification).join(
      models.NotificationType).filter(and_(
          models.NotificationType.id == notif_type.id,
          Notification.object_id == obj.id,
          Notification.object_type == obj.type,
          (Notification.sent_at.is_(None) | (Notification.repeating == true()))
      )).count() > 0


def _add_assignable_declined_notif(obj):
  """Add entries for assignable declined notifications.

  Args:
    obj (Assignable): Any object with assignable mixin for which we want to add
      notifications.
  """
  # pylint: disable=protected-access
  name = "{}_declined".format(obj._inflector.table_singular)
  notif_type = models.NotificationType.query.filter_by(name=name).first()

  if not _has_unsent_notifications(notif_type, obj):
    _add_notification(obj, notif_type)


def _add_assessment_updated_notif(obj):
  """Add a notification record on the change of an object.

  If the same notification type for the object already exists and has not been
  sent yet, do not do anything. The same if there already exist unsent status
  change notifications for the object.

  Args:
    obj (models.mixins.Assignable): an object for which to add a notification
  """
  # If there already exists a status change notification, an assessment updated
  # notification should not be sent, and is thus not added.
  notif_type_names = ["assessment_declined"]
  notif_type_names.extend(item.value for item in Transitions)

  notif_types = models.NotificationType.query.filter(
      models.NotificationType.name.in_(notif_type_names)
  )
  notif_type_ids = [ntype.id for ntype in notif_types]

  has_status_change = models.Notification.query.filter(
      models.Notification.object_id == obj.id,
      models.Notification.object_type == obj.type,
      models.Notification.notification_type_id.in_(notif_type_ids),
      (
          models.Notification.sent_at.is_(None) |
          (models.Notification.repeating == true())
      )
  ).exists()

  if db.session.query(has_status_change).scalar():
    return

  notif_type = models.NotificationType.query.filter_by(
      name="assessment_updated").first()

  if not _has_unsent_notifications(notif_type, obj):
    _add_notification(obj, notif_type)


def _add_state_change_notif(obj, state_change, remove_existing=False):
  """Add a notification record on changing the given object's status.

  If the same notification type for the object already exists and has not been
  sent yet, do not do anything.

  Args:
    obj (models.mixins.Assignable): an object for which to add a notification
    state_change (Transitions): the state transition that has happened
    remove_existing (bool): whether or not to remove all exisiting state change
      notifications for `obj`
  """
  # Assessment updated notifications should not be sent if there is a state
  # change notification - we must thus delete the former.
  notif_type_names = ["assessment_updated"]

  if remove_existing:
    notif_type_names.extend(item.value for item in Transitions)
    notif_type_names.append("assessment_declined")

  notif_types = models.NotificationType.query.filter(
      models.NotificationType.name.in_(notif_type_names)
  )
  notif_type_ids = [ntype.id for ntype in notif_types]

  models.Notification.query.filter(
      models.Notification.object_id == obj.id,
      models.Notification.object_type == obj.type,
      models.Notification.notification_type_id.in_(notif_type_ids)
  ).delete(synchronize_session=False)

  notif_type = models.NotificationType.query.filter_by(
      name=state_change.value).first()

  if not _has_unsent_notifications(notif_type, obj):
    _add_notification(obj, notif_type)


def handle_assignable_modified(obj):  # noqa: ignore=C901
  """A handler for the Assignable object modified event.

  Args:
    obj (models.mixins.Assignable): an object that has been modified
  """
  state_change_occurred = False

  attrs = inspect(obj).attrs
  status_history = attrs["status"].history

  old_state = status_history.deleted[0] if status_history.deleted else None
  new_state = status_history.added[0] if status_history.added else None

  # The transition from "ready to review" to "in progress" happens when an
  # object is declined, so this is used as a triger for declined notifications.
  if (old_state == Statusable.DONE_STATE and
     new_state == Statusable.PROGRESS_STATE):
    _add_assignable_declined_notif(obj)

  transitions_map = {
      (Statusable.START_STATE, Statusable.PROGRESS_STATE):
          Transitions.TO_STARTED,
      (Statusable.START_STATE, Statusable.FINAL_STATE):
          Transitions.TO_COMPLETED,
      (Statusable.START_STATE, Statusable.DONE_STATE):
          Transitions.TO_REVIEW,
      (Statusable.PROGRESS_STATE, Statusable.FINAL_STATE):
          Transitions.TO_COMPLETED,
      (Statusable.PROGRESS_STATE, Statusable.DONE_STATE):
          Transitions.TO_REVIEW,
      (Statusable.DONE_STATE, Statusable.FINAL_STATE):
          Transitions.TO_VERIFIED,
      (Statusable.FINAL_STATE, Statusable.PROGRESS_STATE):
          Transitions.TO_REOPENED,
      (Statusable.DONE_STATE, Statusable.PROGRESS_STATE):
          Transitions.TO_REOPENED,
  }

  state_change = transitions_map.get((old_state, new_state))
  if state_change:
    _add_state_change_notif(obj, state_change, remove_existing=True)
    state_change_occurred = True

  # changes of some of the attributes are not considered as a modification of
  # the obj itself, e.g. metadata not editable by the end user, or changes
  # covered by other event types such as "comment created"
  # pylint: disable=invalid-name
  IGNORE_ATTRS = frozenset((
      u"_notifications", u"comments", u"context", u"context_id", u"created_at",
      u"custom_attribute_definitions", u"custom_attribute_values",
      u"_custom_attribute_values", u"finished_date", u"id", u"modified_by",
      u"modified_by_id", u"object_level_definitions", u"os_state",
      u"related_destinations", u"related_sources", u"status",
      u"task_group_objects", u"updated_at", u"verified_date",
  ))

  is_changed = False

  for attr_name, val in attrs.items():
    if attr_name in IGNORE_ATTRS:
      continue

    if val.history.has_changes():
      # the exact order of recipients in the string does not matter, hence the
      # need for an extra check
      if attr_name == u"recipients" and not _recipients_changed(val.history):
        continue
      is_changed = True
      break

  is_changed = is_changed or _ca_values_changed(obj)  # CA check only if needed

  if not is_changed:
    return  # no changes detected, nothing left to do

  # When modified, a done Assessment gets automatically reopened, but that is
  # not directly observable via status change history, thus an extra check.
  if obj.status in Statusable.DONE_STATES:
    _add_state_change_notif(obj, Transitions.TO_REOPENED, remove_existing=True)
    state_change_occurred = True
  elif obj.status == Statusable.START_STATE:
    _add_state_change_notif(obj, Transitions.TO_STARTED, remove_existing=True)
    state_change_occurred = True

  if not state_change_occurred:
    # explicit check needed, because state change notifications might not yet
    # be visible within the current transaction
    _add_assessment_updated_notif(obj)


def _ca_values_changed(obj):
  """Check if object's custom attribute values have been changed.

  The changes are determined by comparing the current object custom attributes
  with the CA values from object's last known revision. If the latter does not
  exist, it is considered that there are no changes - since the object has
  apparently just been created.

  Args:
    obj (models.mixins.Assignable): the object to check

  Returns:
    (bool) True if there is a change to any of the CA values, False otherwise.
  """
  requred_parents = [models.mixins.customattributable.CustomAttributable,
                     models.mixins.assignable.Assignable]
  if not all(isinstance(obj, p) for p in requred_parents):
    return False

  rev = db.session.query(
      models.Revision
  ).filter_by(
      resource_id=obj.id,
      resource_type=obj.type
  ).order_by(
      models.Revision.id.desc()
  ).first()
  content = rev.content if rev else {}
  return any([
      obj.global_attributes != (content.get("global_attributes") or []),
      obj.local_attributes != (content.get("local_attributes") or []),
  ])


def _align_by_ids(items, items2):
  """Generate pairs of items from both iterables, matching them by IDs.

  The items within each iterable must have a unique id attribute (with a value
  other than None). If an item from one iterable does not have a matching item
  in the other, None is used for the missing item.

  Args:
    items: The first iterable.
    items2: The second iterable.

  Yields:
    Pairs of items with matching IDs (one of the items can be None).
  """
  STOP = Ellipsis  # iteration sentinel alias  # pylint: disable=invalid-name

  sort_by_id = partial(sorted, key=attrgetter("id"))
  items = chain(sort_by_id(items), [STOP])
  items2 = chain(sort_by_id(items2), [STOP])

  first, second = next(items), next(items2)

  while first is not STOP or second is not STOP:
    min_id = min(pair.id for pair in (first, second) if pair is not STOP)
    id_one, id_two = getattr(first, "id", None), getattr(second, "id", None)

    yield (first if id_one == min_id else None,
           second if id_two == min_id else None)

    if id_one == min_id:
      first = next(items)
    if id_two == min_id:
      second = next(items2)


def _recipients_changed(history):
  """Check if the recipients attribute has been semantically modified.

  The recipients attribute is a comma-separated string, and the exact order of
  the items in it does not matter, i.e. it is not considered a change.

  Args:
    history (sqlalchemy.orm.attributes.History): recipients' value history

  Returns:
    True if there was a (semantic) change, False otherwise
  """
  old_val = history.deleted[0] if history.deleted else ""
  new_val = history.added[0] if history.added else ""

  if old_val is None:
    old_val = ""

  if new_val is None:
    new_val = ""

  return sorted(old_val.split(",")) != sorted(new_val.split(","))


def handle_assignable_created(obj):
  name = "{}_open".format(obj._inflector.table_singular)
  notif_type = models.NotificationType.query.filter_by(name=name).first()
  _add_notification(obj, notif_type)


def handle_assignable_deleted(obj):
  models.Notification.query.filter_by(
      object_id=obj.id,
      object_type=obj.type,
  ).delete()


def handle_reminder(obj, reminder_type):
  """Handles reminders for an object

  Args:
    obj: Object to process
    reminder_type: Reminder handler to use for processing event
    """
  if reminder_type in obj.REMINDERABLE_HANDLERS:
    reminder_settings = obj.REMINDERABLE_HANDLERS[reminder_type]
    handler = reminder_settings['handler']
    data = reminder_settings['data']
    handler(obj, data)


def handle_comment_created(obj, src):
  """Add notification entries for new comments.

  Args:
    obj (Comment): New comment.
    src (dict): Dictionary containing the comment post request data.
  """
  if src.get("send_notification"):
    notif_type = models.NotificationType.query.filter_by(
        name="comment_created").first()
    _add_notification(obj, notif_type)


def handle_relationship_altered(rel):
  """Handle creation or deletion of a relationship between two objects.

  Relationships not involving an Assessment are ignored. For others, if a
  Person or a Document is assigned/attached (or removed from) an Assessment,
  that is considered an Assessment modification and hence a notification is
  created (unless the Assessment has not been started yet, of course).

  Args:
    rel (Relationship): Created (or deleted) relationship instance.
  """
  if rel.source.type != u"Assessment" != rel.destination.type:
    return

  asmt, other = rel.source, rel.destination
  if asmt.type != u"Assessment":
    asmt, other = other, asmt

  if other.type not in (u"Document", u"Person"):
    return

  if asmt.status != Statusable.START_STATE:
    _add_assessment_updated_notif(asmt)

  # when modified, a done Assessment gets automatically reopened
  if asmt.status in Statusable.DONE_STATES:
    _add_state_change_notif(
        asmt, Transitions.TO_REOPENED, remove_existing=True)


def register_handlers():  # noqa: C901
  """Register listeners for notification handlers."""

  # Variables are used as listeners, and arguments are needed for callback
  # functions.
  #
  # pylint: disable=unused-argument,unused-variable

  @signals.Restful.model_deleted.connect_via(models.Assessment)
  def assignable_deleted_listener(sender, obj=None, src=None, service=None):
    handle_assignable_deleted(obj)

  @signals.Restful.model_put.connect_via(models.Assessment)
  def assignable_modified_listener(sender, obj=None, src=None, service=None):
    handle_assignable_modified(obj)

  @signals.Restful.collection_posted.connect_via(models.Assessment)
  def assignable_created_listener(sender, objects=None, **kwargs):
    for obj in objects:
      handle_assignable_created(obj)

  @signals.Restful.model_put.connect_via(models.Assessment)
  def assessment_send_reminder(sender, obj=None, src=None, service=None):
    reminder_type = src.get("reminderType", False)
    if reminder_type:
      handle_reminder(obj, reminder_type)

  @signals.Restful.collection_posted.connect_via(models.Comment)
  def comment_created_listener(sender, objects=None, sources=None, **kwargs):
    for obj, src in izip(objects, sources):
      handle_comment_created(obj, src)

  @signals.Restful.model_posted.connect_via(models.Relationship)
  def relationship_created_listener(sender, obj=None, src=None, service=None):
    handle_relationship_altered(obj)

  @signals.Restful.model_put.connect_via(models.Relationship)
  def relationship_updated_listener(sender, obj=None, src=None, service=None):
    handle_relationship_altered(obj)

  @signals.Restful.model_deleted.connect_via(models.Relationship)
  def relationship_deleted_listener(sender, obj=None, src=None, service=None):
    handle_relationship_altered(obj)
