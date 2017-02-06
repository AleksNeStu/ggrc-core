# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""A mixin for objects with statuses"""

from ggrc import db


class Statusable(object):

  """Mixin with default labels for status field"""

  # pylint: disable=too-few-public-methods

  START_STATE = u"Not Started"
  PROGRESS_STATE = u"In Progress"
  DONE_STATE = u"Ready for Review"
  VERIFIED_STATE = u"Verified"
  FINAL_STATE = u"Completed"
  END_STATES = {VERIFIED_STATE, FINAL_STATE}

  NOT_DONE_STATES = {START_STATE, PROGRESS_STATE}
  DONE_STATES = {DONE_STATE} | END_STATES
  VALID_STATES = tuple(NOT_DONE_STATES | DONE_STATES)

  status = db.Column(
      db.Enum(*VALID_STATES),
      nullable=False,
      default=START_STATE)

  @classmethod
  def default_status(cls):
    return "Not Started"
