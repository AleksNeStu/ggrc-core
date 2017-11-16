# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Import GGRC model hooks."""

from ggrc.models.hooks import assessment
from ggrc.models.hooks import audit
from ggrc.models.hooks import comment
from ggrc.models.hooks import issue
from ggrc.models.hooks import relationship
from ggrc.models.hooks import access_control_list
from ggrc.models.hooks import custom_attribute_definition


ALL_HOOKS = [
    assessment,
    audit,
    comment,
    issue,
    relationship,
    access_control_list,
    custom_attribute_definition,
]


def init_hooks():
  for hook in ALL_HOOKS:
    hook.init_hook()
