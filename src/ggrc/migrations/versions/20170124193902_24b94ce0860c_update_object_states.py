# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""
Update object states

Create Date: 2017-01-24 19:39:02.339637
"""
# disable Invalid constant name pylint warning for mandatory Alembic variables.
# pylint: disable=invalid-name

import sqlalchemy as sa
from sqlalchemy.dialects import mysql
from alembic import op


# revision identifiers, used by Alembic.
revision = '24b94ce0860c'
down_revision = '421b2179c02e'
tables = {'access_groups', 'clauses', 'controls', 'data_assets', 'directives',
          'facilities', 'issues', 'markets', 'objectives', 'org_groups',
          'products', 'programs', 'projects', 'sections', 'systems',
          'vendors'}


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
  # Handle audits which are a special case
  op.alter_column(
      'audits', 'status',
      nullable=False,
      server_default='Planned',
      existing_nullable=True,
      existing_server_default=None,
      existing_type=mysql.VARCHAR(length=250)
  )

  # Update other status:
  op.alter_column(
      'background_tasks', 'status',
      existing_type=mysql.VARCHAR(length=250),
      nullable=False,
      server_default='Pending',
      existing_server_default=None)
  op.drop_column('object_documents', 'status')
  op.drop_column('object_owners', 'status')
  op.drop_column('object_people', 'status')
  op.drop_column('relationships', 'status')


def downgrade():
  """Downgrade database schema and/or data back to the previous revision."""
  op.add_column('relationships', sa.Column(
      'status', mysql.VARCHAR(length=250), nullable=True))
  op.add_column('object_people', sa.Column(
      'status', mysql.VARCHAR(length=250), nullable=True))
  op.add_column('object_owners', sa.Column(
      'status', mysql.VARCHAR(length=250), nullable=True))
  op.add_column('object_documents', sa.Column(
      'status', mysql.VARCHAR(length=250), nullable=True))
  op.alter_column(
      'background_tasks', 'status',
      existing_type=mysql.VARCHAR(length=250),
      nullable=True,
      server_default=None)
  op.alter_column(
      'audits', 'status',
      nullable=True,
      server_default=None,
      existing_type=mysql.VARCHAR(length=250)
  )
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
