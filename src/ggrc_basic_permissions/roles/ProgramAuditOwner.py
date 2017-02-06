# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""A module with configuration of the ProgramAuditOwner role's permissions."""

# pylint: disable=invalid-name


scope = "Audit Implied"
description = """
  A user with the ProgramOwner role for a private program will also have this
  role in the audit context for any audit created for that program.
  """
permissions = {
    "read": [
        "Assessment",
        "AssessmentTemplate",
        "Issue",
        "UserRole",
        "Audit",
        "Snapshot",
        "AuditObject",
        "Meeting",
        "ObjectControl",
        "ObjectDocument",
        "ObjectPerson",
        "Relationship",
        "Document",
        "Meeting",
        "Context",
    ],
    "create": [
        "Assessment",
        "AssessmentTemplate",
        "Issue",
        "UserRole",
        "Audit",
        "Snapshot",
        "AuditObject",
        "Meeting",
        "ObjectControl",
        "ObjectDocument",
        "ObjectPerson",
        "Relationship",
        "Document",
        "Meeting",
    ],
    "view_object_page": [
        "__GGRC_ALL__"
    ],
    "update": [
        "Assessment",
        "AssessmentTemplate",
        "Issue",
        "UserRole",
        "Audit",
        "Snapshot",
        "AuditObject",
        "Meeting",
        "ObjectControl",
        "ObjectDocument",
        "ObjectPerson",
        "Relationship",
        "Document",
        "Meeting",
    ],
    "delete": [
        "UserRole",
        "Assessment",
        "AssessmentTemplate",
        "Issue",
        "ObjectControl",
        "ObjectDocument",
        "ObjectPerson",
        "Relationship",
        "Document",
        "Meeting"
        "AuditObject",
        "Audit",
    ]
}
