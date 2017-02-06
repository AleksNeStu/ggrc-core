# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

scope = "Admin"
description = """
  GGRC System Administrator with super-user privileges.
  """
permissions = {
    "read": [],
    "create": [],
    "delete": [],
    "__GGRC_ADMIN__": [
        {
            "type": "__GGRC_ALL__",
            "condition": "forbid",
            "terms": {
                "blacklist": {
                    "delete": ["Cycle", "Person"]
                }
            },
        },
    ],
    "update": []
}
