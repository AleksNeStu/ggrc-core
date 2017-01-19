# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Module containing elements' labels and properties for GGRC's objects."""
# pylint: disable=too-few-public-methods
# pylint: disable=invalid-name

from lib.constants import objects
from lib.constants import roles


class Lhn(object):
  """Elements' labels and properties for the LHN menu."""
  class __metaclass__(type):
    def __init__(self, *args):
      for object_ in objects.ALL_PLURAL:
        setattr(self, object_, object_.lower())
      self.DIRECTIVES_MEMBERS = (
          self.REGULATIONS,
          self.POLICIES,
          self.STANDARDS,
          self.CONTRACTS,
          self.CLAUSES,
          self.SECTIONS)
      self.CONTROLS_OR_OBJECTIVES_MEMBERS = (
          self.CONTROLS,
          self.OBJECTIVES)
      self.PEOPLE_OR_GROUPS_MEMBERS = (
          self.PEOPLE,
          self.ORG_GROUPS,
          self.VENDORS,
          self.ACCESS_GROUPS)
      self.ASSETS_OR_BUSINESS_MEMBERS = (
          self.SYSTEMS,
          self.PROCESSES,
          self.DATA_ASSETS,
          self.PRODUCTS,
          self.PROJECTS,
          self.FACILITIES,
          self.MARKETS)
      self.RISKS_OR_THREATS_MEMBERS = (
          self.RISKS,
          self.THREATS)
  CONTROLS_OR_OBJECTIVES = "controls_or_objectives"
  PEOPLE_OR_GROUPS = "people_or_groups"
  ASSETS_OR_BUSINESS = "assets_or_business"
  RISKS_OR_THREATS = "risks_or_threats"


class WidgetBar(object):
  """Elements' labels and properties for the generic widget bar."""
  INFO = "Info"

  class __metaclass__(type):
    def __init__(self, *args):
      for object_ in objects.ALL_PLURAL:
        setattr(self, object_, object_.lower())


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
  def __init__(self):
    super(Common, self).__init__()
    self.TITLE = "Title"
    self.DESCRIPTION = "Description"
    self.CODE = "Code"
    self.TRUE = "true"
    self.FALSE = "false"


class CommonModalCreate(object):
  """Common elements' labels and properties for the Modal to create the object.
  """
  def __init__(self):
    super(CommonModalCreate, self).__init__()
    self._HIDE_ALL_OPT_FIELDS = "Hide all optional fields"
    self._SHOW_ALL_OPT_FIELDS = "Show all optional fields"
    self.OPT_HIDE_FIELDS = {"HIDE_ALL_OPT_FIELDS": self._HIDE_ALL_OPT_FIELDS,
                            "SHOW_ALL_OPT_FIELDS": self._SHOW_ALL_OPT_FIELDS}
    self.SAVE_AND_CLOSE = "Save & Close"


class CommonModalSetVisibleFields(object):
  """Common elements' labels and properties for the Modal to set visible
  fields for object.
  """
  def __init__(self):
    super(CommonModalSetVisibleFields, self).__init__()
    self.TITLE = Common().TITLE
    self.CODE = Common().CODE
    self.LAST_UPDATED = "Last Updated"
    self.SET_FIELDS = "Set Fields"


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
    self.OPT_STATE = CommonStates().OPT_OBJ_STATE


class CommonStates(object):
  """Elements' labels and properties for objects' states."""
  # pylint: disable=too-many-instance-attributes
  def __init__(self):
    super(CommonStates, self).__init__()
    self._DRAFT = "Draft"
    self._FINAL = "Final"
    self._EFFECTIVE = "Effective"
    self._INEFFECTIVE = "Ineffective"
    self._LAUNCHED = "Launched"
    self._NOT_LAUNCHED = "Not Launched"
    self._IN_SCOPE = "In Scope"
    self._NOT_IN_SCOPE = "Not in Scope"
    self._DEPRECATED = "Deprecated"
    self.OPT_OBJ_STATE = {
        "DRAFT": self._DRAFT, "FINAL": self._FINAL,
        "EFFECTIVE": self._EFFECTIVE, "INEFFECTIVE": self._INEFFECTIVE,
        "LAUNCHED": self._LAUNCHED, "NOT_LAUNCHED": self._NOT_LAUNCHED,
        "IN_SCOPE": self._IN_SCOPE, "NOT_IN_SCOPE": self._NOT_IN_SCOPE,
        "DEPRECATED": self._DEPRECATED
    }


class AuditStates(object):
  """Elements' labels and properties for Audit's states."""
  def __init__(self):
    super(AuditStates, self).__init__()
    self._PLANNED = "Planned"
    self._IN_PROGRESS = "In progress"
    self._MANAGER_REVIEW = "Manager Review"
    self._READY_FOR_EXT_REVIEW = "Ready for External Review"
    self._COMPLETED = "Completed"


class AsmtStates(object):
  """Elements' labels and properties for Assessment's states."""
  def __init__(self):
    super(AsmtStates, self).__init__()
    self.NOT_STARTED = "Not Started"
    self.IN_PROGRESS = "In progress"
    self.COMPLETED = "Completed"


class ProgramModalCreate(CommonProgram, CommonModalCreate):
  """Elements' labels and properties for the Modal to create the Program."""
  def __init__(self):
    super(ProgramModalCreate, self).__init__()
    self.MODAL_HEADER = "New Program"
    self.SAVE_AND_ADD_ANOTHER = "Save & Add Another"


class ProgramWidgetInfo(CommonProgram):
  """Elements' labels and properties for the Program Info Widget."""
  def __init__(self):
    super(ProgramWidgetInfo, self).__init__()
    self.TREE_VIEW_HEADER = "Program Info"
    self.OBJECT_REVIEW = "OBJECT REVIEW"
    self.OPT_OBJECT_REVIEW = "Submit For Review"
    self._SHOW_ADVANCED = "Show Advanced"
    self._HIDE_ADVANCED = "Hide Advanced"
    self.OPT_ADVANCED = {"SHOW_ADVANCED": self._SHOW_ADVANCED,
                         "HIDE_ADVANCED": self._HIDE_ADVANCED}


class AsmtTmplModalSetVisibleFields(CommonModalSetVisibleFields):
  """Common elements' labels and properties for the Modal to set visible
  fields for Assessment Template.
  """
  # pylint: disable=too-many-instance-attributes
  def __init__(self):
    super(AsmtTmplModalSetVisibleFields, self).__init__()
    self.MODAL_HEADER = "Set visible fields for Assessment Template"
    self.OWNER = "Owner"
    self.STATE = "State"
    self.PRIMARY_CONTACT = "Primary Contact"
    self.SECONDARY_CONTACT = "Secondary Contact"
    self.OPT_SET_FIELDS = {
        "TITLE": self.TITLE, "OWNER": self.OWNER, "CODE": self.CODE,
        "STATE": self.STATE, "PRIMARY_CONTACT": self.PRIMARY_CONTACT,
        "SECONDARY_CONTACT": self.SECONDARY_CONTACT,
        "LAST_UPDATED": self.LAST_UPDATED
    }
    self.DEFAULT_SET_FIELDS = (self.TITLE, self.CODE, self.LAST_UPDATED)


class AsmtModalSetVisibleFields(CommonModalSetVisibleFields):
  """Common elements' labels and properties for the Modal to set visible
  fields for Assessment.
  """
  # pylint: disable=too-many-instance-attributes
  def __init__(self):
    super(AsmtModalSetVisibleFields, self).__init__()
    self.MODAL_HEADER = "Set visible fields for Assessment"
    self.STATE = "State"
    self.VERIFIED = "Verified"
    self.CONCLUSION_DESIGN = "Conclusion: Design"
    self.CONCLUSION_OPERATION = "Conclusion: Operation"
    self.FINISHED_DATE = "Finished Date"
    self.VERIFIED_DATE = "Verified Date"
    self.URL = "URL"
    self.REFERENCE_URL = "Reference URL"
    self.TYPE = "Type"
    self.OPT_SET_FIELDS = {
        "TITLE": self.TITLE, "CODE": self.CODE, "STATE": self.STATE,
        "VERIFIED": self.VERIFIED, "LAST_UPDATED": self.LAST_UPDATED,
        "CONCLUSION_DESIGN": self.CONCLUSION_DESIGN,
        "CONCLUSION_OPERATION": self.CONCLUSION_OPERATION,
        "FINISHED_DATE": self.FINISHED_DATE,
        "VERIFIED_DATE": self.VERIFIED_DATE, "URL": self.URL,
        "REFERENCE_URL": self.REFERENCE_URL, "TYPE": self.TYPE
    }
    self.DEFAULT_SET_FIELDS = (self.TITLE, self.CODE, self.STATE,
                               self.VERIFIED, self.LAST_UPDATED)
