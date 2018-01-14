# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Constants for roles."""

# global roles
NO_ROLE = "No role"
NO_ROLE_UI = "(Inactive user)"
ADMIN = "Admin"
CREATOR = "Creator"
READER = "Reader"
EDITOR = "Editor"
ADMINISTRATOR = "Administrator"
GLOBAL_ROLES = (CREATOR, EDITOR, ADMINISTRATOR)
# assessment roles
ASSIGNEES = "Assignees"
VERIFIERS = "Verifiers"
# program roles
PROGRAM_EDITOR = "Program Editor"
PROGRAM_MANAGER = "Program Manager"
PROGRAM_READER = "Program Reader"
# workflow roles
WORKFLOW_MEMBER = "Workflow Member"
WORKFLOW_MANAGER = "Workflow Manager"
# other roles
OTHER = "other"
CREATORS = CREATOR + "s"
OBJECT_OWNERS = "Object Owners"
AUDIT_LEAD = "Audit Lead"
AUDITORS = "Auditors"
PRINCIPAL_ASSIGNEES = "Principal " + ASSIGNEES
SECONDARY_ASSIGNEES = "Secondary " + ASSIGNEES
PRIMARY_CONTACTS = "Primary Contacts"
SECONDARY_CONTACTS = "Secondary Contacts"

# user names
DEFAULT_USER = "Example User"

# user emails
DEFAULT_USER_EMAIL = "user@example.com"

# role scopes
SYSTEM = "System"
PRIVATE_PROGRAM = "Private Program"
WORKFLOW = "Workflow"
SUPERUSER = "Superuser"
NO_ACCESS = "No Access"
