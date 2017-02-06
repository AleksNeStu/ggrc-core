# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""A module with configuration of the Reader role's permissions."""

# pylint: disable=invalid-name


from ggrc_basic_permissions.roles.Creator import owner_update


scope = "System"
description = """
  This role grants a user basic, read-only, access permission to a GGRC
  instance.
  """
permissions = {
    "read": [
        "Audit",
        "Snapshot",
        "Categorization",
        "Category",
        "ControlCategory",
        "ControlAssertion",
        "Control",
        "Comment",
        "Assessment",
        "AssessmentTemplate",
        "CustomAttributeDefinition",
        "CustomAttributeValue",
        "Issue",
        "ControlControl",
        "DataAsset",
        "AccessGroup",
        "Directive",
        "Contract",
        "Policy",
        "Regulation",
        "Standard",
        "Document",
        "Facility",
        "Help",
        "Market",
        "Objective",
        "ObjectControl",
        "ObjectDocument",
        "ObjectObjective",
        "ObjectPerson",
        "Option",
        "OrgGroup",
        "Vendor",
        "PopulationSample",
        "Product",
        "ProgramControl",
        "ProgramDirective",
        "Project",
        "Relationship",
        "Section",
        "Clause",
        "SystemOrProcess",
        "System",
        "Process",
        "SystemControl",
        "SystemSystem",
        "ObjectOwner",
        "Person",
        "Program",
        "Revision",
        "Role",
        "UserRole",
        "Context",
        {
            "type": "BackgroundTask",
            "terms": {
                "property_name": "modified_by",
                "value": "$current_user"
            },
            "condition": "is"
        },
    ],
    "create": [
        "Workflow"
        "Categorization",
        "Category",
        "ControlCategory",
        "ControlAssertion",
        "Control",
        "Comment",
        "Assessment",
        "AssessmentTemplate",
        "Issue",
        "DataAsset",
        "AccessGroup",
        "Directive",
        "Contract",
        "Policy",
        "Regulation",
        "Standard",
        "Document",
        "Facility",
        "Help",
        "Market",
        "Objective",
        {
            "type": "ObjectDocument",
            "terms": {
                "property_name": "documentable",
                "action": "update",
            },
            "condition": "relationship",
        },
        "ObjectPerson",
        "Option",
        "OrgGroup",
        "Vendor",
        "PopulationSample",
        "Product",
        "Project",
        {
            "type": "Relationship",
            "terms": {
                "property_name": "source,destination",
                "action": "update"
            },
            "condition": "relationship",
        },
        "Section",
        "Clause",
        "SystemOrProcess",
        "System",
        "Process",
        {
            "type": "ObjectOwner",
            "terms": {
                "property_name": "ownable.modified_by",
                "value": "$current_user"
            },
            "condition": "is"
        },
        "Person",
        "Program",
        "Role",
        "Context",
        "BackgroundTask",
    ],
    "view_object_page": [
        "__GGRC_ALL__"
    ],
    "update": owner_update,
    "delete": owner_update,
}
