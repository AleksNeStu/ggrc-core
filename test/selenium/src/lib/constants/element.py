# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Module containing elements' labels and properties for GGRC's objects."""
# pylint: disable=too-few-public-methods
# pylint: disable=invalid-name

from lib.constants import objects, roles


class Lhn(object):
  """Elements' labels and properties for the LHN menu."""
  class __metaclass__(type):
    def __init__(cls, *args):
      for object_ in objects.ALL_PLURAL:
        setattr(cls, object_, object_.lower())
      cls.DIRECTIVES_MEMBERS = (
          cls.REGULATIONS,
          cls.POLICIES,
          cls.STANDARDS,
          cls.CONTRACTS,
          cls.CLAUSES,
          cls.SECTIONS)
      cls.CONTROLS_OR_OBJECTIVES_MEMBERS = (
          cls.CONTROLS,
          cls.OBJECTIVES)
      cls.PEOPLE_OR_GROUPS_MEMBERS = (
          cls.PEOPLE,
          cls.ORG_GROUPS,
          cls.VENDORS,
          cls.ACCESS_GROUPS)
      cls.ASSETS_OR_BUSINESS_MEMBERS = (
          cls.SYSTEMS,
          cls.PROCESSES,
          cls.DATA_ASSETS,
          cls.PRODUCTS,
          cls.PROJECTS,
          cls.FACILITIES,
          cls.MARKETS)
      cls.RISKS_OR_THREATS_MEMBERS = (
          cls.RISKS,
          cls.THREATS)
  CONTROLS_OR_OBJECTIVES = "controls_or_objectives"
  PEOPLE_OR_GROUPS = "people_or_groups"
  ASSETS_OR_BUSINESS = "assets_or_business"
  RISKS_OR_THREATS = "risks_or_threats"


class WidgetBar(object):
  """Elements' labels and properties for the generic widget bar."""
  INFO = "Info"

  class __metaclass__(type):
    def __init__(cls, *args):
      for object_ in objects.ALL_PLURAL:
        setattr(cls, object_, object_.lower())


class AdminWidgetRoles(object):
  """Elements' labels (role scopes) and properties for the Roles widget
  at Admin dashboard.
  """
  _ADMIN_SCOPE = roles.ADMIN.upper()
  _SYS_SCOPE = roles.SYSTEM.upper()
  _PRG_SCOPE = roles.PRIVATE_PROGRAM.upper()
  _WF_SCOPE = roles.WORKFLOW.upper()

  ROLE_SCOPE_ADMINISTRATOR = (roles.ADMINISTRATOR, _ADMIN_SCOPE)
  ROLE_SCOPE_CREATOR = (roles.CREATOR, _SYS_SCOPE)
  ROLE_SCOPE_EDITOR = (roles.EDITOR, _SYS_SCOPE)
  ROLE_SCOPE_READER = (roles.READER, _SYS_SCOPE)
  ROLE_SCOPE_PROGRAM_EDITOR = (roles.PROGRAM_EDITOR, _PRG_SCOPE)
  ROLE_SCOPE_PROGRAM_MANAGER = (roles.PROGRAM_MANAGER, _PRG_SCOPE)
  ROLE_SCOPE_PROGRAM_READER = (roles.PROGRAM_READER, _PRG_SCOPE)
  ROLE_SCOPE_WORKFLOW_MEMBER = (roles.WORKFLOW_MEMBER, _WF_SCOPE)
  ROLE_SCOPE_WORKFLOW_MANAGER = (roles.WORKFLOW_MANAGER, _WF_SCOPE)
  ROLE_SCOPES_LIST = [ROLE_SCOPE_ADMINISTRATOR,
                      ROLE_SCOPE_CREATOR,
                      ROLE_SCOPE_EDITOR,
                      ROLE_SCOPE_PROGRAM_EDITOR,
                      ROLE_SCOPE_PROGRAM_MANAGER,
                      ROLE_SCOPE_PROGRAM_READER,
                      ROLE_SCOPE_READER,
                      ROLE_SCOPE_WORKFLOW_MEMBER,
                      ROLE_SCOPE_WORKFLOW_MANAGER]
  ROLE_SCOPES_DICT = dict(ROLE_SCOPES_LIST)


class AdminWidgetEvents(object):
  """Elements' labels and properties (regular expression) for the Event widget
  at Admin dashboard.
  """
  TREE_VIEW_HEADER = "Events"
  TREE_VIEW_ROW_REGEXP = r"^.+\s(by.+)\son\s" + \
      r"(\d{2}/\d{2}/\d{4}\s\d{2}:\d{2}:\d{2}\s[A,P]M)"


class AdminWidgetCustomAttrs(object):
  """Elements' labels (custom attributes scopes) for the Custom Attributes
  widget at Admin dashboard.
  """
  # possible types of custom attributes
  TREE_VIEW_HEADER = "Custom Attributes"
  TEXT = "Text"
  RICH_TEXT = "Rich Text"
  DATE = "Date"
  CHECKBOX = "Checkbox"
  DROPDOWN = "Dropdown"
  PERSON = "Map:Person"

  ALL_ATTRS_TYPES = (TEXT, RICH_TEXT, DATE, CHECKBOX, DROPDOWN, PERSON)


class Common(object):
  """Common elements' labels and properties for the object."""
  TITLE = "Title"
  DESCRIPTION = "Description"
  CODE = "Code"
  TRUE = "true"
  FALSE = "false"


class CommonModalCreate(object):
  """Common elements' labels and properties for the Modal to create the object.
  """
  def __init__(self):
    super(CommonModalCreate, self).__init__()
    self._HIDE_ALL_OPT_FIELDS = "Hide all optional fields"
    self._SHOW_ALL_OPT_FIELDS = "Show all optional fields"
    self.SAVE_AND_CLOSE = "Save & Close"


class CommonModalSetVisibleFields(object):
  """Common labels for modal widow that select visible fields for tree view."""
  MODAL_HEADER_FORMAT = "Set visible fields for {}"
  TITLE = Common.TITLE
  CODE = Common.CODE
  STATE = "State"
  LAST_UPDATED = "Last Updated"
  SET_FIELDS = "Set Fields"


class TransformationSetVisibleFields(CommonModalSetVisibleFields):
  """To transformation elements' labels and properties for the Modal to set
  visible fields for object as tree view headers.
  """
  OWNER = "Owner"
  VERIFIED = "Verified"


class CommonProgram(object):
  """Common elements' labels and properties for the Program object."""
  # pylint: disable=too-many-instance-attributes
  def __init__(self):
    super(CommonProgram, self).__init__()
    self.MANAGER = "Manager"
    self.PROGRAM_URL = "Program URL"
    self.REFERENCE_URL = "Reference URL"
    self.PRIMARY_CONTACT = "Primary Contact"
    self.SECONDARY_CONTACT = "Secondary Contact"
    self.NOTES = "Notes"
    self.EFFECTIVE_DATE = "Effective Date"
    self.STOP_DATE = "Stop Date"
    self.STATE = "State"


class ObjectStates(object):
  """Elements' labels and properties for objects' states."""
  DRAFT = "Draft"
  FINAL = "Final"
  EFFECTIVE = "Effective"
  INEFFECTIVE = "Ineffective"
  LAUNCHED = "Launched"
  NOT_LAUNCHED = "Not Launched"
  IN_SCOPE = "In Scope"
  NOT_IN_SCOPE = "Not in Scope"
  DEPRECATED = "Deprecated"


class BaseStates(object):
  """Common states for Audit and Assessment"""
  IN_PROGRESS = "In progress"
  COMPLETED = "Completed"


class AuditStates(BaseStates):
  """Elements' labels and properties for Audit's states."""
  PLANNED = "Planned"
  MANAGER_REVIEW = "Manager Review"
  READY_FOR_EXT_REVIEW = "Ready for External Review"


class AsmtStates(BaseStates):
  """Elements' labels and properties for Assessment's states."""
  NOT_STARTED = "Not Started"


class ProgramWidgetInfo(CommonProgram):
  """Elements' labels and properties for the Program Info Widget."""
  TREE_VIEW_HEADER = "Program Info"


class AsmtTmplModalSetVisibleFields(CommonModalSetVisibleFields):
  """Common elements' labels and properties for the Modal to set visible
  fields for Assessment Template.
  """
  OWNER = "Owner"
  PRIMARY_CONTACT = "Primary Contact"
  SECONDARY_CONTACT = "Secondary Contact"

  MODAL_HEADER = CommonModalSetVisibleFields.MODAL_HEADER_FORMAT.format(
      "Assessment Template")
  DEFAULT_SET_FIELDS = (
      CommonModalSetVisibleFields.TITLE,
      CommonModalSetVisibleFields.CODE,
      CommonModalSetVisibleFields.LAST_UPDATED)


class AsmtModalSetVisibleFields(CommonModalSetVisibleFields):
  """Common elements' labels and properties for the Modal to set visible
  fields for Assessment.
  """
  MODAL_HEADER = CommonModalSetVisibleFields.MODAL_HEADER_FORMAT.format(
      "Assessment")
  VERIFIED = "Verified"
  CONCLUSION_DESIGN = "Conclusion: Design"
  CONCLUSION_OPERATION = "Conclusion: Operation"
  FINISHED_DATE = "Finished Date"
  VERIFIED_DATE = "Verified Date"
  URL = "URL"
  REFERENCE_URL = "Reference URL"
  TYPE = "Type"
  DEFAULT_SET_FIELDS = (
      CommonModalSetVisibleFields.TITLE, CommonModalSetVisibleFields.CODE,
      CommonModalSetVisibleFields.STATE, VERIFIED,
      CommonModalSetVisibleFields.LAST_UPDATED)
