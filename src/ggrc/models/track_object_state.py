# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Track Object State module"""

from sqlalchemy import event


from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm.session import Session
from ggrc import db
from ggrc.models.deferred import deferred
from ggrc.models.reflection import PublishOnly


class HasObjectState(object):
  """Has Object State Mixin"""
  _publish_attrs = [
      PublishOnly('os_state'),
  ]
  _aliases = {
      "os_state": {
          "display_name": "Review State",
          "mandatory": False
      }
  }

  def __init__(self, *args, **kwargs):
    self._skip_os_state_update = False
    super(HasObjectState, self).__init__(*args, **kwargs)

  @declared_attr
  def os_state(cls):
    """os_state attribute is used to track object review status"""
    return deferred(db.Column(db.String, nullable=False,
                              default='Unreviewed'), cls.__name__)

  def validate_os_state(self):
    """os_state needs to reset to Unreviewed on any object edit, except
       if set_reviewed_state was called before session flush"""
    if getattr(self, '_set_reviewed_state', False):
      self.os_state = 'Reviewed'
    elif self.os_state != 'Unreviewed':
      self.os_state = 'Unreviewed'

  def set_reviewed_state(self):
    """Prevent resetting os_state in this session, used to set the os_state
       to Reviewed"""
    self.os_state = 'Reviewed'  # Mark the object as dirty
    self._set_reviewed_state = True


def before_flush_handler(session, flush_context, instances):
  """We listen to before_flush so that we can reset os_state on any object
     update"""
  for obj in session.dirty:
    if isinstance(obj, HasObjectState):
      obj.validate_os_state()

event.listen(Session, 'before_flush', before_flush_handler)
