# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

scope = "Private Program Implied"
description = """
  A user with authorization to edit mapping objects related to a program. When
  a person has this role they can map and unmap objects to the Program but they
  are unable ble to edit the Program info, delete the Program, or assign roles
  for that Program.
  """
permissions = {
    "read": [],
    "create": [],
    "view_object_page": [],
    "update": [],
    "delete": []
}
