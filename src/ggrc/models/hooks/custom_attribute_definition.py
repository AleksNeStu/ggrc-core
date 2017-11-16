# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""
  Custom Attribute Definition delete hook

  The following hooks make sure created new revision
  after deleting CAD from admin panel
"""

import datetime

from ggrc import db
from ggrc.models import all_models
from ggrc.services import signals


def init_hook():
  """Init CAD delete hooks"""
  # pylint: disable=unused-variable
  @signals.Restful.model_deleted.connect_via(
      all_models.CustomAttributeDefinition)
  def handle_cad_delete(sender, obj, src=None, service=None):
    """Make sure create revision after deleting CAD from admin panel"""
    # pylint: disable=unused-argument
    for item in obj.attribute_values:
      modified_object = db.session.query(
          getattr(all_models, item.attributable_type)
      ).get(item.attributable_id)
      modified_object.updated_at = datetime.datetime.now()
