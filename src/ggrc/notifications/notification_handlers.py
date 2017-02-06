# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Notification handlers for object in the ggrc module.

This module contains all function needed for handling notification objects
needed by ggrc notifications.
"""

from datetime import date
from itertools import izip

from sqlalchemy import inspect
from sqlalchemy import and_

from ggrc import db
from ggrc.services.common import Resource
from ggrc import models


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
  return db.session.query(models.Notification).join(
      models.NotificationType).filter(and_(
          models.NotificationType.id == notif_type.id,
          models.Notification.object_id == obj.id,
          models.Notification.object_type == obj.type,
          models.Notification.sent_at.is_(None),
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


def handle_assignable_modified(obj):
  history = inspect(obj).attrs["status"].history

  # The transition from "finished" to "in progress" only happens when a task is
  # declined. So this is used as a triger for declined notifications.
  if (history.deleted == [obj.DONE_STATE] and
     history.added == [obj.PROGRESS_STATE]):
    _add_assignable_declined_notif(obj)


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
  """Add notification etries for new comments.

  Args:
    obj (Comment): New comment.
    src (dict): Dictionary containing the coment post request data.
  """
  if src.get("send_notification"):
    notif_type = models.NotificationType.query.filter_by(
        name="comment_created").first()
    _add_notification(obj, notif_type)


def register_handlers():
  """Register listeners for notification handlers."""

  # Variables are used as listeners, and arguments are needed for callback
  # functions.
  # pylint: disable=unused-argument,unused-variable

  @Resource.model_deleted.connect_via(models.Assessment)
  def assignable_deleted_listener(sender, obj=None, src=None, service=None):
    handle_assignable_deleted(obj)

  @Resource.model_put.connect_via(models.Assessment)
  def assignable_modified_listener(sender, obj=None, src=None, service=None):
    handle_assignable_modified(obj)

  @Resource.collection_posted.connect_via(models.Assessment)
  def assignable_created_listener(sender, objects=None, **kwargs):
    for obj in objects:
      handle_assignable_created(obj)

  @Resource.model_put.connect_via(models.Assessment)
  def assessment_send_reminder(sender, obj=None, src=None, service=None):
    reminder_type = src.get("reminderType", False)
    if reminder_type:
      handle_reminder(obj, reminder_type)

  @Resource.collection_posted.connect_via(models.Comment)
  def comment_created_listener(sender, objects=None, sources=None, **kwargs):
    for obj, src in izip(objects, sources):
      handle_comment_created(obj, src)
