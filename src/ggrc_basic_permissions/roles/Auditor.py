# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

scope = "Audit"
description = """
  The permissions required by an auditor to access relevant resources for the
  program being audited.
  """
permissions = {
    "read": [
        "Audit",
        "Assessment",
        "Issue",
        "Meeting",
        "ObjectDocument",
        "ObjectPerson",
        "Relationship",
        "Document",
        "Meeting",
        "UserRole",
        "Comment",
        "Context",
    ],
    "create": [
        "Assessment",
        "Issue",
        "Relationship",
        "Comment",
    ],
    "view_object_page": [
        "__GGRC_ALL__"
    ],
    "update": [
        "Assessment",
        "Issue",
        "Audit",
    ],
    "delete": [
        "Assessment",
        "Issue"
    ],
}
