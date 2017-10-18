# Copyright (C) 2017 Google Inc.
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
# assessment roles
ASSESSOR = "Assessor"
VERIFIER = "Verifier"
# program roles
PROGRAM_EDITOR = "Program Editor"
PROGRAM_MANAGER = "Program Manager"
PROGRAM_READER = "Program Reader"
# workflow roles
WORKFLOW_MEMBER = "Workflow Member"
WORKFLOW_MANAGER = "Workflow Manager"
# other roles
OBJECT_OWNERS = "Object Owners"
AUDIT_LEAD = "Audit Lead"
AUDITORS = "Auditors"
PRINCIPAL_ASSIGNEE = "Principal Assignee"
SECONDARY_ASSIGNEE = "Secondary Assignee"
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

# todo: implement service to get actual ACL's info via api/access_control_roles
# Access control role ID
CONTROL_ADMIN_ID = 49
CONTROL_PRIMARY_CONTACT_ID = 9
ISSUE_ADMIN_ID = 53
ISSUE_PRIMARY_CONTACT_ID = 17
