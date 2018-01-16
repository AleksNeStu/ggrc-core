# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

scope = "Private Program"
description = """
  User with authorization to peform administrative tasks such as associating
  users to roles within the scope of of a program.<br/><br/>When a person
  creates a program they are automatically given the ProgramOwner role. This
  allows them to Edit, Delete, or Map objects to the Program. It also allows
  them to add people and assign them roles when their programs are private.
  ProgramOwner is the most powerful role.
  """
permissions = {
    "read": [],
    "create": [],
    "view_object_page": [],
    "update": [],
    "delete": []
}
