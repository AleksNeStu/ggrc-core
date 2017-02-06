# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Data handlers for notifications for objects in ggrc module.

Main contributed functions are:
  get_assignable_data,
"""

import datetime
import urlparse
from logging import getLogger

from ggrc import models
from ggrc import utils


# pylint: disable=invalid-name
logger = getLogger(__name__)


def get_object_url(obj):
  """Get url for the object info page.

  Args:
    obj (db.Model): Object for which we want to info page url.

  Returns:
    string: Url for the object info page.
  """
  # pylint: disable=protected-access
  url = "{}/{}".format(obj._inflector.table_plural, obj.id)
  return urlparse.urljoin(utils.get_url_root(), url)


def _get_assignable_dict(people, notif):
  """Get dict data for assignable object in notification.

  Args:
    people (List[Person]): List o people objects who should receive the
      notification.
    notif (Notification): Notification that should be sent.
  Returns:
    dict: dictionary containing notification data for all people in the given
      list.
  """
  obj = get_notification_object(notif)
  data = {}
  for person in people:
    # We should default to today() if no start date is found on the object.
    start_date = getattr(obj, "start_date", datetime.date.today())
    data[person.email] = {
        "user": get_person_dict(person),
        notif.notification_type.name: {
            obj.id: {
                "title": obj.title,
                "start_date_statement": utils.get_digest_date_statement(
                    start_date, "start", True),
                "url": get_object_url(obj),
            }
        }
    }
  return data


def assignable_open_data(notif):
  """Get data for open assignable object.

  Args:
    notif (Notification): Notification entry for an open assignable object.

  Returns:
    A dict containing all notification data for the given notification.
  """
  obj = get_notification_object(notif)
  if not obj:
    logger.warning(
        '%s for notification %s not found.',
        notif.object_type, notif.id,
    )
    return {}
  people = [person for person, _ in obj.assignees]

  return _get_assignable_dict(people, notif)


def _get_declined_people(obj):
  """Get a list of people for declined notifications.

  Args:
    obj (Model): An assignable model

  Returns:
    A list of people that should receive a declined notification according to
    the given object type.
  """
  if obj.type == "Assessment":
    return [person for person, role in obj.assignees
            if "Assessor" in role]
  return []


def assignable_declined_data(notif):
  """Get data for declined assignable object.

  Args:
    notif (Notification): Notification entry for a declined assignable object.

  Returns:
    A dict containing all notification data for the given notification.
  """
  obj = get_notification_object(notif)
  people = _get_declined_people(obj)
  return _get_assignable_dict(people, notif)


def get_assessment_url(assessment):
  return urlparse.urljoin(
      utils.get_url_root(),
      "assessments/{}".format(assessment.id))


def assignable_reminder(notif):
  """Get data for assignable object for reminders"""
  obj = get_notification_object(notif)
  reminder = next((attrs for attrs in obj.REMINDERABLE_HANDLERS.values()
                   if notif.notification_type.name in attrs['reminders']),
                  False)

  notif_data = {}
  if reminder:
    data = reminder['data']
    if obj.status not in data:
      # In case object already moved out of targeted state
      return notif_data
    assignee_group = data[obj.status]
    people = [a for a, roles in obj.assignees if assignee_group in roles]

    for person in people:
      notif_data[person.email] = {
          "user": get_person_dict(person),
          notif.notification_type.name: {
              obj.id: {
                  "title": obj.title,
                  "end_date": obj.end_date.strftime("%m/%d/%Y")
                  if obj.end_date else None,
                  "url": get_assessment_url(obj)
              }
          }
      }
  return notif_data


def get_person_dict(person):
  """Return dictionary with basic person info.

  Args:
    person (Person): Person object for which we want to get a dictionary.

  Returns:
    dict: dictionary with persons email, name and id.
  """
  if person:
    return {
        "email": person.email,
        "name": person.name,
        "id": person.id,
    }

  return {"email": "", "name": "", "id": -1}


def get_notification_object(notif):
  """Get an object for which the notification entry was made.

  Args:
    notif (Notifications): Notification entry for the given object

  Returns:
    A model based on notif.object_id and notif.object_type.
  """
  model = getattr(models, notif.object_type, None)
  if model:
    return model.query.get(notif.object_id)
  return None


def get_assignable_data(notif):
  """Return data for assignable object notifications.

  Args:
    notif (Notification): notification with an Assignable object_type.

  Returns:
    Dict with all data for the assignable notification or an empty dict if the
    notification is not for a valid assignable object.
  """
  if notif.object_type not in {"Assessment"}:
    return {}
  elif notif.notification_type.name.endswith("_open"):
    return assignable_open_data(notif)
  elif notif.notification_type.name.endswith("_declined"):
    return assignable_declined_data(notif)
  elif notif.notification_type.name.endswith("_reminder"):
    return assignable_reminder(notif)
  return {}


def generate_comment_notification(obj, comment, person):
  return {
      "user": get_person_dict(person),
      "comment_created": {
          comment.id: {
              "description": comment.description,
              "commentator": get_person_dict(comment.modified_by),
              "parent_type": obj._inflector.title_singular.title(),
              "parent_id": obj.id,
              "parent_url": get_object_url(obj),
              "parent_title": obj.title
          }
      }
  }


def get_comment_data(notif):
  """Return data for comment notifications.

  This functions checks who should receive the notification and who not, with
  the Commentable mixin that must be added on the object which has the current
  comment. If the object on which the comment was made is not Commentable, the
  function will return an empty dict.

  Args:
    notif (Notification): notification with a Comment object_type.

  Returns:
    Dict with all data needed for sending comment notifications.
  """
  data = {}
  recipients = set()
  comment = get_notification_object(notif)
  comment_obj = None
  rel = models.Relationship.find_related(comment, models.Assessment())

  if rel:
    comment_obj = rel.Assessment_destination or rel.Assessment_source
  if not comment_obj:
    logger.warning('Comment object not found for notification %s', notif.id)
    return {}

  if comment_obj.recipients:
    recipients = set(comment_obj.recipients.split(","))

  for person, assignee_type in comment_obj.assignees:
    if not recipients or recipients.intersection(set(assignee_type)):
      data[person.email] = generate_comment_notification(
          comment_obj, comment, person)
  return data
