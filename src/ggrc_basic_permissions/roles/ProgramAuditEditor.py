# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

scope = "Audit Implied"
description = """
  A user with the ProgramEditor role for a private program will also have this
  role in the audit context for any audit created for that program.
  """
permissions = {
    "read": [
        "Comment",
        "Assessment",
        "Issue",
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
        "UserRole",
        "Context",
    ],
    "create": [
        "Snapshot",
        "Comment",
        "Assessment",
        "Issue",
        "Meeting",
        "ObjectControl",
        "ObjectDocument",
        "ObjectPerson",
        "Relationship",
        "Document",
        "Meeting",
        "AuditObject"
    ],
    "view_object_page": [
        "__GGRC_ALL__"
    ],
    "update": [
        {
            "type": "Assessment",
            "terms": {
                "list_property": "owners",
                "value": "$current_user"
            },
            "condition": "contains"
        },
        {
            "type": "Issue",
            "terms": {
                "list_property": "owners",
                "value": "$current_user"
            },
            "condition": "contains"
        },
        "Snapshot",
        "Audit",
        "AuditObject",
        "Meeting",
        "ObjectControl",
        "ObjectDocument",
        "ObjectPerson",
        "Relationship",
        "Document",
        "Meeting"
    ],
    "delete": [
        "ObjectControl",
        "ObjectDocument",
        "ObjectPerson",
        "Relationship",
        "Document",
        "Meeting",
        "Audit",
        "AuditObject"
    ]
}
