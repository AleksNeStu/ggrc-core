# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""
Migrate Assignees to ACL

Create Date: 2017-10-05 14:55:16.487208
"""
# disable Invalid constant name pylint warning for mandatory Alembic variables.
# pylint: disable=invalid-name

import sqlalchemy as sa

from alembic import op

from collections import namedtuple
from sqlalchemy import text

from ggrc.migrations.utils.resolve_duplicates import create_new_table

revision = '33d043d8ba29'
down_revision = '356f329cda52'

AC_PERMISSIONS = namedtuple("AC_PERMISSIONS", "read update delete mandatory")
ASSIGNEE_ROLES = {
    "Creators": AC_PERMISSIONS(1, 1, 0, 1),
    "Assignees": AC_PERMISSIONS(1, 1, 0, 1),
    "Verifiers": AC_PERMISSIONS(1, 1, 0, 0),
}
MAPPED_ROLES = {
    "Creators Mapped": AC_PERMISSIONS(1, 0, 0, 0),
    "Assignees Mapped": AC_PERMISSIONS(1, 0, 0, 0),
    "Verifiers Mapped": AC_PERMISSIONS(1, 0, 0, 0),
    # Mapped Document has another set of permissions
    "Creators Document Mapped": AC_PERMISSIONS(1, 1, 1, 0),
    "Assignees Document Mapped": AC_PERMISSIONS(1, 1, 1, 0),
    "Verifiers Document Mapped": AC_PERMISSIONS(1, 1, 1, 0),
}
ASSIGNEE_MAPPED_ROLES = dict(ASSIGNEE_ROLES, **MAPPED_ROLES)
ROLES_TRANSLATION = [
    ("Creator", "Creators"),
    ("Assessor", "Assignees"),
    ("Verifier", "Verifiers"),
]


def create_translation_table(table_name, translation_data):
  """Create table to translate one names to anothers"""
  roles_translation_tbl = create_new_table(
      table_name,
      sa.Column("new_name", sa.String(length=100)),
      sa.Column("old_name", sa.String(length=100)),
  )
  op.bulk_insert(
      roles_translation_tbl,
      [{"old_name": old, "new_name": new} for old, new in translation_data]
  )


def update_comments():
  """Update recipients for assessment and assignee_type for old comments"""
  # Update recipients in assessments
  op.execute("""
        UPDATE assessments a
        JOIN (
          SELECT a.id, group_concat(art.new_name SEPARATOR ',') recipients
          FROM assessments a
          JOIN ac_roles_translation art
            ON LOCATE(art.old_name, a.recipients) > 0
          GROUP BY a.id
        ) temp ON temp.id = a.id
        SET a.recipients = temp.recipients;
    """)
  # Update assignee_type in comments
  op.execute("""
      UPDATE comments a
      JOIN (
        SELECT a.id, group_concat(art.new_name SEPARATOR ',') assignee_type
        FROM comments a
        JOIN ac_roles_translation art
          ON LOCATE(art.old_name, a.assignee_type) > 0
        GROUP BY a.id
      ) temp ON temp.id = a.id
      SET a.assignee_type = temp.assignee_type;
  """)


def upgrade():
  """Upgrade database schema and/or data, creating a new revision."""
  connection = op.get_bind()
  # We suppose that there are no custom roles with names from
  # ASSIGNEE_MAPPED_ROLES. If such roles exist need to raise error
  # and remove they manually
  res = connection.execute(
      text("""
          SELECT name
          FROM access_control_roles
          WHERE object_type = 'Assessment' and name IN :assignee_roles
      """),
      assignee_roles=ASSIGNEE_MAPPED_ROLES.keys()
  ).fetchone()

  if res:
    raise Exception(
        "Custom Role with name '{}' already exists in db. "
        "Migration will be stopped".format(res[0])
    )

  op.add_column(
      "access_control_list",
      sa.Column("parent_id", sa.Integer(), nullable=True)
  )
  op.create_foreign_key(
      "fk_access_control_list_parent_id",
      "access_control_list", "access_control_list",
      ["parent_id"], ["id"],
      ondelete="CASCADE"
  )
  op.add_column(
      "access_control_roles",
      sa.Column("internal", sa.Boolean(), nullable=False, server_default="0")
  )
  create_translation_table("ac_roles_translation", ROLES_TRANSLATION)

  # Create new AC roles for assignees
  for assignee_role, permissions in ASSIGNEE_MAPPED_ROLES.items():
    connection.execute(
        text("""
            INSERT INTO access_control_roles(
                name, object_type, created_at, updated_at, `read`, `update`,
                `delete`, mandatory, non_editable, internal
            )
            VALUES(
                :role, :object_type, NOW(), NOW(), :read, :update,
                :delete, :mandatory, :non_editable, :internal
            );
        """),
        role=assignee_role,
        object_type="Assessment",
        read=permissions.read,
        update=permissions.update,
        delete=permissions.delete,
        mandatory=permissions.mandatory,
        non_editable="1",
        internal="1" if assignee_role in MAPPED_ROLES else "0",
    )

  # Enable creation of temp tables
  op.execute("SET AUTOCOMMIT = 1;")
  op.execute("""
      CREATE TEMPORARY TABLE temp_assigned_objects (
          assignable_id int(11),
          assignable_type varchar(250),
          person_id int(11),
          role_id int(11),
          role_name varchar(250),
          context_id int(11),
          created_at datetime,
          updated_at datetime
      );
  """)
  # Migrate existing assignees to access_control_list
  connection.execute(
      text("""
          INSERT INTO temp_assigned_objects(
              assignable_id, assignable_type, person_id,
              role_id, role_name, context_id, created_at, updated_at
          )
          SELECT r.destination_id, r.destination_type, r.source_id,
              acr.id, acr.name, r.context_id, r.created_at, r.updated_at
          FROM relationships r
          JOIN relationship_attrs ra ON r.id = ra.relationship_id
          JOIN access_control_roles acr ON acr.name IN :assignee_types AND
            acr.object_type = r.destination_type
          JOIN ac_roles_translation art ON art.new_name = acr.name
          WHERE source_type = 'Person' AND
            LOCATE(art.old_name, ra.attr_value) > 0

          UNION

          SELECT r.source_id, r.source_type, r.destination_id,
              acr.id, acr.name, r.context_id, r.created_at, r.updated_at
          FROM relationships r
          JOIN relationship_attrs ra ON r.id = ra.relationship_id
          JOIN access_control_roles acr ON acr.name IN :assignee_types AND
            acr.object_type = r.source_type
          JOIN ac_roles_translation art ON art.new_name = acr.name
          WHERE destination_type = 'Person' AND
            LOCATE(art.old_name, ra.attr_value) > 0;
      """),
      assignee_types=ASSIGNEE_ROLES.keys()
  )
  op.execute("""
      INSERT INTO access_control_list(
          person_id, ac_role_id, object_id, object_type,
          created_at, updated_at, context_id
      )
      SELECT person_id, role_id, assignable_id, assignable_type,
          created_at, updated_at, context_id
      FROM temp_assigned_objects;
  """)

  op.execute("""
        CREATE TEMPORARY TABLE temp_mapped_objects (
            mapped_id int(11),
            mapped_type varchar(250),
            person_id int(11),
            role varchar(250),
            context_id int(11),
            parent_id int(11),
            created_at datetime,
            updated_at datetime
        );
    """)
  op.execute("""
      INSERT INTO temp_mapped_objects(
          mapped_id, mapped_type, person_id,
          role, context_id, parent_id, created_at, updated_at
      )
      SELECT r.source_id,
          r.source_type,
          tao.person_id,
          CONCAT(tao.role_name,
                CASE
                  WHEN r.source_type = 'Document' THEN ' Document'
                  ELSE ''
                END,
                ' Mapped'),
          r.context_id,
          acl.id,
          r.created_at,
          r.updated_at
      FROM relationships r
      JOIN temp_assigned_objects tao ON
        tao.assignable_id = r.destination_id AND
        tao.assignable_type = r.destination_type AND
        r.source_type != 'Person'
      JOIN access_control_list acl ON
        acl.object_type = tao.assignable_type AND
        acl.object_id = tao.assignable_id AND
        acl.person_id = tao.person_id;
  """)
  op.execute("""
      INSERT INTO temp_mapped_objects(
          mapped_id, mapped_type, person_id,
          role, context_id, parent_id, created_at, updated_at
      )
      SELECT r.destination_id,
          r.destination_type,
          tao.person_id,
          CONCAT(tao.role_name,
                CASE
                  WHEN r.destination_type = 'Document' THEN ' Document'
                  ELSE ''
                END,
                ' Mapped'),
          r.context_id,
          acl.id,
          r.created_at,
          r.updated_at
      FROM relationships r
      JOIN temp_assigned_objects tao ON
        tao.assignable_id = r.source_id AND
        tao.assignable_type = r.source_type AND
        r.destination_type != 'Person'
      JOIN access_control_list acl ON
        acl.object_type = tao.assignable_type AND
        acl.object_id = tao.assignable_id AND
        acl.person_id = tao.person_id
  """)
  op.execute("""
      INSERT INTO access_control_list(
          person_id, ac_role_id, object_id, object_type,
          created_at, updated_at, context_id, parent_id
      )
      SELECT tmo.person_id, acr.id, tmo.mapped_id, tmo.mapped_type,
          max(tmo.created_at), max(tmo.updated_at), max(tmo.context_id),
          max(tmo.parent_id)
      FROM temp_mapped_objects tmo
      JOIN access_control_roles acr ON
          acr.object_type = "Assessment" AND
          acr.name = tmo.role
      GROUP BY tmo.person_id, acr.id, tmo.mapped_id, tmo.mapped_type;
  """)
  op.execute("""
      DROP TABLE IF EXISTS temp_assigned_objects;
  """)
  op.execute("""
      DROP TABLE IF EXISTS temp_mapped_objects;
  """)

  update_comments()
  op.execute("""
      DROP TABLE IF EXISTS ac_roles_translation;
  """)
  op.execute("SET AUTOCOMMIT = 0;")
  op.execute("""
      UPDATE notification_types
      SET name = 'assessment_assignees_reminder'
      WHERE name = 'assessment_assessor_reminder';
  """)


def downgrade():
  """Downgrade database schema and/or data back to the previous revision."""
  connection = op.get_bind()
  connection.execute(
      text("""
          DELETE acl
          FROM access_control_list acl
          JOIN access_control_roles acr ON acr.id = acl.ac_role_id
          WHERE acr.name IN :assignee_types
      """),
      assignee_types=ASSIGNEE_MAPPED_ROLES.keys()
  )
  connection.execute(
      text("""
          DELETE FROM access_control_roles
          WHERE name IN :assignee_types
      """),
      assignee_types=ASSIGNEE_MAPPED_ROLES.keys()
  )
  op.drop_constraint(
      "fk_access_control_list_parent_id",
      "access_control_list",
      "foreignkey",
  )
  op.drop_column("access_control_list", "parent_id")
  op.drop_column("access_control_roles", "internal")

  create_translation_table(
      "ac_roles_translation",
      [(new, old) for old, new in ROLES_TRANSLATION]
  )
  update_comments()
  op.execute("""
      DROP TABLE IF EXISTS ac_roles_translation;
  """)

  op.execute("""
      UPDATE notification_types
      SET name = 'assessment_assessor_reminder'
      WHERE name = 'assessment_assignees_reminder';
  """)
