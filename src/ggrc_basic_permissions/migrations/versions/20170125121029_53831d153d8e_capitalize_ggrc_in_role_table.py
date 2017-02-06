# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""
Capitalize ggrc in role table

The only place in the database where re-branding routines are required is
"roles" table - "Reader" role description field.

Create Date: 2017-01-25 12:10:29.650127
"""
# disable Invalid constant name pylint warning for mandatory Alembic variables.
# pylint: disable=invalid-name

from alembic import op


# revision identifiers, used by Alembic.
revision = '53831d153d8e'
down_revision = '89d8ca4c1267'


def upgrade():
  """Upgrade database schema and/or data, creating a new revision."""
  op.execute(
      "UPDATE roles "
      "SET description='This role grants a user basic, read-only, "
      "access permission to a GGRC instance.' "
      "WHERE name='Reader'"
  )


def downgrade():
  """Downgrade database schema and/or data back to the previous revision."""
  op.execute(
      "UPDATE roles "
      "SET description='This role grants a user basic, read-only, "
      "access permission to a gGRC instance.' "
      "WHERE name='Reader'"
  )
