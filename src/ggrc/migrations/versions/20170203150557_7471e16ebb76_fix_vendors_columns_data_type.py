# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""
Bring vendors' start_date and end_date columns into conformity with the model

Create Date: 2017-02-03 15:05:57.538217
"""
# disable Invalid constant name pylint warning for mandatory Alembic variables.
# pylint: disable=invalid-name

from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '6e9a3ed063d2'
down_revision = '24b94ce0860c'


def upgrade():
  """Upgrade database schema and/or data, creating a new revision."""
  op.alter_column('vendors', 'start_date', type_=mysql.DATE(),
                  existing_type=mysql.DATETIME(), nullable=True)
  op.alter_column('vendors', 'end_date', type_=mysql.DATE(),
                  existing_type=mysql.DATETIME(), nullable=True)


def downgrade():
  """Downgrade database schema and/or data back to the previous revision."""
  op.alter_column('vendors', 'start_date', type_=mysql.DATETIME(),
                  existing_type=mysql.DATE(), nullable=True)
  op.alter_column('vendors', 'end_date', type_=mysql.DATETIME(),
                  existing_type=mysql.DATE(), nullable=True)
