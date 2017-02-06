# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Move cycle objects to relationships table

Revision ID: 1263c1ab4642
Revises: 4ff4b445852c
Create Date: 2016-02-25 08:56:35.200703

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '1263c1ab4642'
down_revision = '4ff4b445852c'


def upgrade():

  op.add_column(u'workflows', sa.Column(u'is_old_workflow',
                                        sa.Boolean(), nullable=True))

  # if the cycle object exists, but the related object was deleted it won't
  # be transferred to the relationship table. If this data will still
  # be required somehow, it is accessible in the revisions table, and we are
  # also not removing the cycle_task_group_objects table yet
  sql = """
    INSERT INTO relationships(
        created_at, updated_at, source_id, source_type, destination_id,
        destination_type, context_id
    )
    SELECT
        ctgot.created_at,
        ctgot.updated_at,
        ctgot.id,
        "CycleTaskGroupObjectTask" AS task_type,
        ctgo.object_id,
        ctgo.object_type,
        ctgot.context_id
    FROM cycle_task_group_object_tasks AS ctgot
        LEFT JOIN cycle_task_group_objects AS ctgo
        ON ctgot.cycle_task_group_object_id=ctgo.id
    WHERE ctgot.cycle_task_group_object_id IS NOT NULL AND
        ctgo.object_id != 0
  """
  op.execute(sql)

  # existing workflows will be marked with this bool, so we know that we need
  # to create new cycles the old way, with a cartesian product between tasks
  # and objects
  sql = """
    UPDATE workflows
    SET is_old_workflow = 1
  """
  op.execute(sql)


def downgrade():
  op.drop_column(u'workflows', u'is_old_workflow')
