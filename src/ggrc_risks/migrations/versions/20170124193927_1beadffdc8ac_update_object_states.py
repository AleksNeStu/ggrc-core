# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""
Update object states

Create Date: 2017-01-24 19:39:27.764152
"""
# disable Invalid constant name pylint warning for mandatory Alembic variables.
# pylint: disable=invalid-name
import sqlalchemy as sa
from sqlalchemy.dialects import mysql
from alembic import op

# revision identifiers, used by Alembic.
revision = '1beadffdc8ac'
down_revision = '440149c856a2'

tables = {'risks', 'threats'}


def upgrade():
  """Upgrade database schema and/or data, creating a new revision."""

  for table in tables:
    sql = """UPDATE {} SET status =
               CASE status
                 WHEN 'Active' THEN 'Active'
                 WHEN 'Deprecated' THEN 'Deprecated'
                 WHEN 'Draft' THEN 'Draft'
                 WHEN 'Effective' THEN 'Active'
                 WHEN 'Final' THEN 'Active'
                 WHEN 'In Scope' THEN 'Active'
                 WHEN 'Ineffective' THEN 'Active'
                 WHEN 'Launched' THEN 'Active'
                 WHEN 'Not in Scope' THEN 'Draft'
                 WHEN 'Not Launched' THEN 'Draft'
                 ELSE 'Draft'
               END,
               os_state =
               CASE os_state
                 WHEN 'Approved' THEN 'Reviewed'
                 ELSE 'Unreviewed'
               END;""".format(table)
    op.execute(sql)
    op.alter_column(
        table,
        'status',
        nullable=False,
        server_default='Draft',
        existing_type=mysql.VARCHAR(length=250)
    )
    op.alter_column(
        table,
        'os_state',
        server_default='Unreviewed',
        existing_type=mysql.VARCHAR(length=250)
    )
  op.drop_column('risk_objects', 'status')


def downgrade():
  """Downgrade database schema and/or data back to the previous revision."""
  op.add_column('risk_objects', sa.Column(
      'status', mysql.VARCHAR(length=250), nullable=True))
  for table in tables:
    op.alter_column(
        table,
        'os_state',
        server_default=None,
        existing_type=mysql.VARCHAR(length=250)
    )
    op.alter_column(
        table,
        'status',
        nullable=True,
        server_default=None,
        existing_type=mysql.VARCHAR(length=250)
    )
