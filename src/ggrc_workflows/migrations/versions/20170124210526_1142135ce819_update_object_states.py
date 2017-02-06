# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""
Update object states

Create Date: 2017-01-24 21:05:26.781499
"""
# disable Invalid constant name pylint warning for mandatory Alembic variables.
# pylint: disable=invalid-name
import sqlalchemy as sa
from sqlalchemy.dialects import mysql
from alembic import op

# revision identifiers, used by Alembic.
revision = '1142135ce819'
down_revision = '216e496dabe'


def upgrade():
  """Upgrade database schema and/or data, creating a new revision."""
  op.alter_column('cycle_task_group_object_tasks', 'status',
                  existing_type=mysql.VARCHAR(length=250),
                  nullable=False)
  op.alter_column('cycle_task_groups', 'status',
                  existing_type=mysql.VARCHAR(length=250),
                  nullable=False)
  op.alter_column('cycles', 'status',
                  existing_type=mysql.VARCHAR(length=250),
                  nullable=False)
  op.alter_column('workflows', 'status',
                  existing_type=mysql.VARCHAR(length=250),
                  nullable=False)
  op.drop_column('task_group_objects', 'status')
  op.drop_column('workflow_people', 'status')


def downgrade():
  """Downgrade database schema and/or data back to the previous revision."""
  op.add_column('workflow_people', sa.Column(
      'status', mysql.VARCHAR(length=250), nullable=True))
  op.add_column('task_group_objects', sa.Column(
      'status', mysql.VARCHAR(length=250), nullable=True))
  op.alter_column('workflows', 'status',
                  existing_type=mysql.VARCHAR(length=250),
                  nullable=True)
  op.alter_column('cycles', 'status',
                  existing_type=mysql.VARCHAR(length=250),
                  nullable=True)
  op.alter_column('cycle_task_groups', 'status',
                  existing_type=mysql.VARCHAR(length=250),
                  nullable=True)
  op.alter_column('cycle_task_group_object_tasks', 'status',
                  existing_type=mysql.VARCHAR(length=250),
                  nullable=True)
