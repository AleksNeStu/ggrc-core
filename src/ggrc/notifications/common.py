# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>


"""
 GGRC email notification module hook to prepares email, email digest, notify
 email to recipients
"""


from collections import defaultdict
from datetime import date
from datetime import datetime
from logging import getLogger

from sqlalchemy import and_
from sqlalchemy.orm import joinedload
from werkzeug.exceptions import Forbidden
from google.appengine.api import mail

from ggrc import db
from ggrc import extensions
from ggrc import settings
from ggrc.models import Person
from ggrc.models import Notification
from ggrc.rbac import permissions
from ggrc.utils import merge_dict


# pylint: disable=invalid-name
logger = getLogger(__name__)


class Services(object):
  """Helper class for notification services.

  This class is a helper class for calling a notification service for a given
  object. The first call get_service_function must be done after all modules
  have been initialized.
  """

  services = []

  @classmethod
  def get_service_function(cls, name):
    """Get callback function for an object.

    This returns a service function which is a registered callback for an
    object that has a notification.

    Args:
      name: Name of an object for which we want to get a service function, such
        as "CycleTask", "Assessment", etc.

    Returns:
      callable: A function that takes a notification and returns a data dict
        with all the data for that notification.
    """
    if not cls.services:
      cls.services = extensions.get_module_contributions(
          "contributed_notifications")
    if name not in cls.services:
      raise ValueError("unknown service name: %s" % name)
    return cls.services[name]

  @classmethod
  def call_service(cls, notif):
    """Call data handler service for the object in the notification.

    Args:
      notif (Notification): Notification object for which we want to get the
        notification data dict.

    Returns:
      dict: Result of the data handler for the object in the notification.
    """
    service = cls.get_service_function(notif.object_type)
    return service(notif)


def get_filter_data(notification, people_cache):
  """Get filtered notification data.

  This function gets notification data for all users who should receive it. A
  single notification can be for multiple users (such as all assignees) but
  only some should receive it depending on if it's an instant notification or
  a daily digest and the specific users notification settings.

  Args:
    notification (Notification): Notification object for which we want to get
      data.

  Returns:
    dict: dictionary containing notification data for all users who should
      receive it, according to their notification settings.
  """
  result = {}
  data = Services.call_service(notification)

  for user, user_data in data.iteritems():
    if should_receive(notification, user_data, people_cache):
      result[user] = user_data
  return result


def get_notification_data(notifications):
  """Get notification data for all notifications.

  This function returns a filtered data for all notifications for the users
  that should receive it.

  Args:
    notifications (list of Notification): List of notification for which we
      want to get notification data.

  Returns:
    dict: Filtered dictionary containing all the data that should be sent for
      the given notification list.
  """
  if not notifications:
    return {}
  aggregate_data = {}
  people_cache = {}

  for notification in notifications:
    filtered_data = get_filter_data(notification, people_cache)
    aggregate_data = merge_dict(aggregate_data, filtered_data)

  # Remove notifications for objects without a contact (such as task groups)
  aggregate_data.pop("", None)

  return aggregate_data


def get_pending_notifications():
  """Get notification data for all future notifications.

  The data dict that get's returned here contains notification data grouped by
  dates on which the notifications should be received.

  Returns
    list of Notifications, data: a tuple of notifications that were handled
      and corresponding data for those notifications.
  """
  notifications = db.session.query(Notification).filter(
      Notification.sent_at.is_(None)).all()

  notif_by_day = defaultdict(list)
  for notification in notifications:
    notif_by_day[notification.send_on.date()].append(notification)

  data = defaultdict(dict)
  today = date.today()
  for day, notif in notif_by_day.iteritems():
    current_day = max(day, today)
    data[current_day] = merge_dict(data[current_day],
                                   get_notification_data(notif))

  return notifications, data


def get_daily_notifications():
  """Get notification data for all future notifications.

  Returns
    list of Notifications, data: a tuple of notifications that were handled
      and corresponding data for those notifications.
  """
  notifications = db.session.query(Notification).filter(
      and_(Notification.send_on <= datetime.today(),
           Notification.sent_at.is_(None)
           )).all()
  return notifications, get_notification_data(notifications)


def should_receive(notif, user_data, people_cache):
  """Check if a user should receive a notification or not.

  Args:
    notif (Notification): A notification entry that we are checking.
    user_data (dict): A dictionary containing data about user notifications.

  Returns:
    True if user should receive the given notification, or False otherwise.
  """
  force_notif = user_data.get("force_notifications", {}).get(notif.id, False)
  person_id = user_data["user"]["id"]
  # The person does not exist
  if person_id == -1:
    return False
  if person_id in people_cache:
    person = people_cache[person_id]
  else:
    person = db.session.query(Person).options(
        joinedload('user_roles').joinedload('role'),
        joinedload('notification_configs')
    ).filter(Person.id == person_id).first()
    people_cache[person_id] = person

  # If the user has no access we should not send any emails
  if person.system_wide_role == "No Access":
    return False

  def is_enabled(notif_type, person):
    """Check user notification settings.

    Args:
      notif_type (string): can be "Email_Digest" or "Email_Now" based on what
        we wish to check.

    Returns:
      Boolean based on what settings users has stored or what the default
      setting is for the given notification.
    """

    notification_configs = [nc for nc in person.notification_configs
                            if nc.notif_type == notif_type]
    if not notification_configs:
      # If we have no results, we need to use the default value, which is
      # true for digest emails.
      return notif_type == "Email_Digest"
    return notification_configs[0].enable_flag

  has_digest = force_notif or is_enabled("Email_Digest", person)

  return has_digest


def send_daily_digest_notifications():
  """Send emails for today's or overdue notifications.

  Returns:
    str: String containing a simple list of who received the notification.
  """
  # pylint: disable=invalid-name
  notif_list, notif_data = get_daily_notifications()
  sent_emails = []
  subject = "GGRC daily digest for {}".format(date.today().strftime("%b %d"))
  for user_email, data in notif_data.iteritems():
    data = modify_data(data)
    email_body = settings.EMAIL_DIGEST.render(digest=data)
    send_email(user_email, subject, email_body)
    sent_emails.append(user_email)
  set_notification_sent_time(notif_list)
  return "emails sent to: <br> {}".format("<br>".join(sent_emails))


def set_notification_sent_time(notif_list):
  """Set sent time to now for all notifications in the list.

  Args:
    notif_list (list of Notification): List of notification for which we want
      to modify sent_at field.
  """
  for notif in notif_list:
    notif.sent_at = datetime.now()
  db.session.commit()


def show_pending_notifications():
  """Get notification html for all future notifications.

  The data shown here is grouped by dates on which notifications should be
  sent.

  Note that the dates for all future notifications will be wrong since they are
  based on the current date which will be different when the notification is
  actually sent.

  Returns:
    str: Html containing all future notifications.
  """
  if not permissions.is_admin():
    raise Forbidden()
  _, notif_data = get_pending_notifications()

  for day_notif in notif_data.itervalues():
    for data in day_notif.itervalues():
      data = modify_data(data)
  return settings.EMAIL_PENDING.render(data=sorted(notif_data.iteritems()))


def show_daily_digest_notifications():
  """Get notification html for today's notifications.

  Returns:
    str: Html containing all today's notifications.
  """
  # pylint: disable=invalid-name
  if not permissions.is_admin():
    raise Forbidden()
  _, notif_data = get_daily_notifications()
  for data in notif_data.itervalues():
    data = modify_data(data)
  return settings.EMAIL_DAILY.render(data=notif_data)


def get_app_engine_email():
  """Get notification sender email.

  Return the email of the user that will be set as sender. This email should be
  authorized to send emails from the server. For more details, see Application
  Settings for email api authorized senders.

  Returns:
    Valid email address if it's set in the app settings.
  """
  email = getattr(settings, 'APPENGINE_EMAIL')
  return email if mail.is_email_valid(email) else None


def send_email(user_email, subject, body):
  """Helper function for sending emails.

  Args:
    user_email (string): Email of the recipient.
    subject (string): Email subject.
    body (basestring): Html body of the email. it can contain unicode
      characters and will be sent as a html mime type.
  """
  sender = get_app_engine_email()
  if not mail.is_email_valid(user_email):
    logger.error("Invalid email recipient: %s", user_email)
    return
  if not sender:
    logger.error("APPENGINE_EMAIL setting is invalid.")
    return

  message = mail.EmailMessage(sender=sender, subject=subject)

  message.to = user_email
  message.body = "TODO: add email in text mode."
  message.html = body

  message.send()


def modify_data(data):
  """Modify notification data dictionary.

  For easier use in templates, it joins the due_in and due today fields
  together.

  Args:
    data (dict): notification data.

  Returns:
    dict: the received dict with some additional fields for easier traversal
      in the notification template.
  """

  data["due_soon"] = {}
  if "due_in" in data:
    data["due_soon"].update(data["due_in"])
  if "due_today" in data:
    data["due_soon"].update(data["due_today"])

  # combine "my_tasks" from multiple cycles
  data["cycle_started_tasks"] = {}
  if "cycle_data" in data:
    for cycle in data["cycle_data"].values():
      if "my_tasks" in cycle:
        data["cycle_started_tasks"].update(cycle["my_tasks"])

  return data
