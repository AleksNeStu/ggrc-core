# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Class model and methods for roles."""



class RolesID(object):
  """sdad."""


class SystemWideRoles(RolesID):
  """System Wide Roles components."""
  SUPERUSER = "Superuser"
  NO_ACCESS = "No Access"
  CREATOR = "Creator"
  READER = "Reader"
  EDITOR = "Editor"
  ADMINISTRATOR = "Administrator"


class ProgramRoles(RolesID):
  """States for Audits objects."""
  PRIVATE_PROGRAM = "Private Program"


class WorkflowRoles(object):
  """States for Audits objects."""
  WORKFLOW = "Workflow"


class AssessmentRoles(object):
  """States for Aud objects."""
  WORKFLOW = "Workflow"

# assessment roles
ASMT_CREATOR = "Creators"
ASSIGNEE = "Assignees"
VERIFIER = "Verifiers"


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
DEFAULT_EMAIL_DOMAIN = "example.com"
DEFAULT_USER_EMAIL = "user@" + DEFAULT_EMAIL_DOMAIN






# todo: implement service to get actual ACL's info via api/access_control_roles
# Access control role ID
CONTROL_ADMIN_ID = 49
CONTROL_PRIMARY_CONTACTS_ID = 9

ISSUE_ADMIN_ID = 53
ISSUE_PRIMARY_CONTACTS_ID = 17
ISSUE_SECONDARY_CONTACTS_ID = 18

ASMT_CREATOR_ID = 76
ASMT_ASSIGNEE_ID = 72
ASMT_VERIFIER_ID = 73
