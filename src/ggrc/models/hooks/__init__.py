# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Import GGRC model hooks."""

from ggrc.models.hooks import assessment
from ggrc.models.hooks import comment


ALL_HOOKS = [
    assessment,
    comment,
]


def init_hooks():
  for hook in ALL_HOOKS:
    hook.init_hook()
