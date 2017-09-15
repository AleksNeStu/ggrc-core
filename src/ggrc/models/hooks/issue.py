# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Issue creation/modification hooks."""

from itertools import izip

from ggrc.services import signals
from ggrc.models import all_models
from ggrc.models.hooks import common


def init_hook():
  """Initialize Issue-related hooks."""
  # pylint: disable=unused-variable
  @signals.Restful.model_put.connect_via(all_models.Issue)
  def handle_issue_put(sender, obj=None, src=None, service=None):
    # pylint: disable=unused-argument
    common.ensure_field_not_changed(obj, "audit")

  @signals.Restful.collection_posted.connect_via(all_models.Issue)
  def handle_issue_post(sender, objects=None, sources=None):
    # pylint: disable=unused-argument
    """Map issue to audit. This makes sure an auditor is able to create
    an issue on the audit without having permissions to create Relationships
    in the context"""

    for obj, src in izip(objects, sources):
      audit = src.get("audit")
      assessment = src.get("assessment")
      if assessment:
        common.map_objects(obj, assessment)
      else:
        common.map_objects(obj, audit)
