# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Constants for roles."""

class GlobalRoles(object):
  """Global roles."""
  ADMIN = "Admin"
  CREATOR = "Creator"
  READER = "Reader"
  EDITOR = "Editor"
  ADMINISTRATOR = "Administrator"
  ALL_W_PERMISSIONS = (CREATOR, READER, EDITOR, ADMINISTRATOR)


class OtherRoles(object):
  """Other roles."""
  NO_ROLE = "No role"
  NO_ROLE_UI = "(Inactive user)"
  OTHER = "other"


class CustomRoles(object):
  """Common custom roles."""
  PRIMARY_CONTACTS = "Primary Contacts"
  SECONDARY_CONTACTS = "Secondary Contacts"


class AssessmentRoles(CustomRoles):
  """Assessment's specific roles."""
  CREATORS = GlobalRoles.CREATOR + "s"
  ASSIGNEES = "Assignees"
  VERIFIERS = "Verifiers"


class AssessmentTemplateRoles(object):
  """Assessment Template's specific roles."""


class ControlRoles(CustomRoles):
  """Control's specific roles."""
  PRINCIPAL_ASSIGNEES = "Principal Assignees"
  SECONDARY_ASSIGNEES = "Secondary Assignees"

class ProgramRoles(CustomRoles):
  """Program's specific roles."""
  MANAGER = "Program Manager"
  READER = "Program Reader"
  EDITOR = "Program Editor"


class AuditRoles(CustomRoles):
  """Audit's specific roles."""
  AUDIT_LEAD = "Audit Lead"
  AUDITORS = "Auditors"
  AUDIT_CAPTAINS = "Audit Captains"


class WorkflowRoles(object):
  """Workflow's specific roles."""
  MEMBER = "Workflow Member"
  MANAGER = "Workflow Manager"


class DefaultSuperuser(object):
  """Default system user w/ superuser permissions."""
  from lib.constants import url
  from lib.constants import objects
  ID = 1
  NAME = "Example User"
  EMAIL = "user@example.com"
  HREF = "/".join([url.Parts.API, objects.Names.PEOPLE, str(ID)])

class RoleScopes(object):
  """Role scopes."""
  SYSTEM = "System"
  PRIVATE_PROGRAM = "Private Program"
  WORKFLOW = "Workflow"
  SUPERUSER = "Superuser"
  NO_ACCESS = "No Access"
