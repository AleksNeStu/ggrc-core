# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""A module with configuration of the ProgramAuditOwner role's permissions."""

# pylint: disable=invalid-name


scope = "Audit Implied"
description = """
  A user with the ProgramOwner role for a private program will also have this
  role in the audit context for any audit created for that program.
  """
permissions = {
    "read": [],
    "create": [],
    "view_object_page": [],
    "update": [],
    "delete": []
}
