# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""
Migrate program roles to ACL

Create Date: 2018-01-08 14:10:43.140028

The Program role propagation:

Program
- Mapped objects (through relationships)
  - Comments & Documents
- Audit
  - Assessment Templates
  - Snapshots
  - Assessments
    - Comments & Documents
  - Issues
    - Comments & Documents
"""
# disable Invalid constant name pylint warning for mandatory Alembic variables.
# pylint: disable=invalid-name

from collections import namedtuple
from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '242b8dc8493b'
down_revision = '1035f388d822'

AC_TABLE = namedtuple("AC_TABLE", "type table role parent_role")
AC_PERMISSIONS = namedtuple(
    "AC_PERMISSIONS",
    "read update delete mandatory my_work default_to_current_user object_type")
ROLES = {
    "Program Readers": AC_PERMISSIONS(1, 0, 0, 0, 1, 0, "Program"),
    "Program Editors": AC_PERMISSIONS(1, 1, 1, 0, 1, 0, "Program"),
    "Program Managers": AC_PERMISSIONS(1, 1, 1, 1, 1, 1, "Program"),
}
MAPPED_ROLES = {
    "Program Readers Mapped": AC_PERMISSIONS(1, 0, 0, 0, 0, 0, "Program"),
    "Program Editors Mapped": AC_PERMISSIONS(1, 1, 1, 0, 0, 0, "Program"),
    "Program Managers Mapped": AC_PERMISSIONS(1, 1, 1, 0, 0, 0, "Program"),
}
ALL_ROLES = dict(ROLES, **MAPPED_ROLES)

ROLE_MIGRATION = {
    "ProgramOwner": "Program Managers",
    "ProgramEditor": "Program Editors",
    "ProgramReader": "Program Readers"
}

ROLE_PROPAGATION = {
    "Program Managers": "Program Manager Mapped",
    "Program Editors": "Program Editor Mapped",
    "Program Readers": "Program Reader Mapped"
}


def _check_new_role_names(connection):
  """Check if new role names already exist in the acr table.
     Throws an exception and stops the migratoin if they do"""
  res = connection.execute(
      text("""
          SELECT name
          FROM access_control_roles
          WHERE name IN :assignee_roles
      """),
      assignee_roles=ALL_ROLES.keys()
  ).fetchone()

  if res:
    raise Exception(
        "Custom Role with name '{}' already exists in db. "
        "Migration will be stopped".format(res[0])
    )


def _create_new_roles(connection):
  """Inserts new roles based on ALL_ROLES list"""
  for role in (
      "Program Managers",
      "Program Editors",
      "Program Readers",
      "Program Managers Mapped",
      "Program Editors Mapped",
      "Program Readers Mapped",
  ):
    permissions = ALL_ROLES[role]
    connection.execute(
        text("""
            INSERT INTO access_control_roles(
                name, object_type, created_at, updated_at, `read`, `update`,
                `delete`, mandatory, non_editable, internal, my_work,
                default_to_current_user
            )
            VALUES(
                :role, :object_type, NOW(), NOW(), :read, :update,
                :delete, :mandatory, :non_editable, :internal, :my_work,
                :default_to_current_user
            );
        """),
        role=role,
        object_type=permissions.object_type,
        read=permissions.read,
        update=permissions.update,
        delete=permissions.delete,
        mandatory=permissions.mandatory,
        my_work=permissions.my_work,
        default_to_current_user=permissions.default_to_current_user,
        non_editable="1",
        internal="1" if role in MAPPED_ROLES else "0",
    )


def _migrate_program_roles(connection):
  """Migrate Auditors from user roles to access_control_list"""
  # 1. Migrate user_roles for all program roles
  for old_role, new_role in ROLE_MIGRATION.items():
    connection.execute(
        text("""
    INSERT INTO access_control_list(
        person_id, ac_role_id, object_id, object_type,
        created_at, updated_at, context_id)
    SELECT ur.person_id, acr.id, c.related_object_id, c.related_object_type,
           ur.created_at, ur.updated_at, ur.context_id
    FROM user_roles AS ur
    JOIN roles AS r ON ur.role_id = r.id
    JOIN contexts as c on ur.context_id = c.id
    JOIN access_control_roles as acr on acr.name = '{}'
    WHERE r.name = '{}' AND c.related_object_id is not NULL;
    """.format(new_role, old_role)))


def _insert_acl_from_mapped(tables, connection):
  """Insert access_control_list rows from multiple tables"""
  for table in tables:
    connection.execute(
        text("""
    INSERT INTO access_control_list(
        person_id, ac_role_id, object_id, object_type,
        created_at, updated_at, context_id, parent_id)
    SELECT acl.person_id, nacr.id, s.id, '{type}',
           acl.created_at, acl.updated_at, acl.context_id, acl.id
    FROM {table} AS s
    JOIN access_control_list AS acl ON acl.context_id = s.context_id
     AND acl.object_type = 'Audit'
    JOIN access_control_roles AS acr ON acl.ac_role_id = acr.id
    JOIN access_control_roles AS nacr ON nacr.name = '{role}'
    WHERE acr.name = '{parent_role}';
    """.format(**table._asdict())))


def _insert_acl_from_second_level(tables, connection):
  """Add acls for second level objects (Documents & Comments)"""
  for table in tables:

    # Mapped through source:
    connection.execute(
        text("""
    INSERT INTO access_control_list(
        person_id, ac_role_id, object_id, object_type,
        created_at, updated_at, context_id, parent_id)
    SELECT acl.person_id, acrn.id, r.destination_id, r.destination_type,
           acl.created_at, acl.updated_at, acl.context_id, acl.id
    FROM access_control_list AS acl
    JOIN access_control_roles AS acr ON acr.id = acl.ac_role_id
    JOIN access_control_roles AS acrn ON acrn.name = '{role}'
    JOIN relationships AS r on r.source_id = acl.object_id
     AND r.source_type = acl.object_type
    WHERE acl.object_type = '{table}'
      AND acr.name = '{parent_role}'
      AND (r.destination_type = '{type}');
    """.format(**table._asdict())))

    # Mapped through destination:
    connection.execute(
        text("""
    INSERT INTO access_control_list(
        person_id, ac_role_id, object_id, object_type,
        created_at, updated_at, context_id, parent_id)
    SELECT acl.person_id, acrn.id, r.source_id, r.source_type,
           acl.created_at, acl.updated_at, acl.context_id, acl.id
    FROM access_control_list AS acl
    JOIN access_control_roles AS acr ON acr.id = acl.ac_role_id
    JOIN access_control_roles AS acrn ON acrn.name = '{role}'
    JOIN relationships AS r on r.destination_id = acl.object_id
     AND r.destination_type = acl.object_type
    WHERE acl.object_type = '{table}'
      AND acr.name = '{parent_role}'
      AND (r.source_type = '{type}');
    """.format(**table._asdict())))


def _propagate_to_mapped(connection):
  """Propagate Program Roles to mapped objects

     - Mapped objects (through relationships)
       - Comments & Documents
  """

  for _, new_role in ROLE_MIGRATION.items():
    # Mapped through source:
    connection.execute(
        text("""
    INSERT INTO access_control_list(
        person_id, ac_role_id, object_id, object_type,
        created_at, updated_at, context_id, parent_id)
    SELECT acl.person_id, acrn.id, r.destination_id, r.destination_type,
           acl.created_at, acl.updated_at, acl.context_id, acl.id
    FROM access_control_list AS acl
    JOIN access_control_roles AS acr ON acr.id = acl.ac_role_id
     AND acr.name = '{}'
    JOIN access_control_roles as acrn ON acrn.name = '{}'
    JOIN relationships AS r
      ON r.source_id = acl.object_id AND r.source_type = acl.object_type;
    """.format(new_role, ROLE_PROPAGATION[new_role])))

    # Mapped through destination:
    connection.execute(
        text("""
    INSERT INTO access_control_list(
        person_id, ac_role_id, object_id, object_type,
        created_at, updated_at, context_id, parent_id)
    SELECT acl.person_id, acrn.id, r.source_id, r.source_type,
           acl.created_at, acl.updated_at, acl.context_id, acl.id
    FROM access_control_list AS acl
    JOIN access_control_roles AS acr ON acr.id = acl.ac_role_id
     AND acr.name = '{}'
    JOIN access_control_roles as acrn ON acrn.name = '{}'
    JOIN relationships AS r
      ON r.destination_id = acl.object_id
     AND r.destination_type = acl.object_type;
    """.format(new_role, ROLE_PROPAGATION[new_role])))

    # Documents/Comments of mapped objects:
    for table in ('Document', 'Comment'):
      # Mapped through source:
      connection.execute(
          text("""
      INSERT INTO access_control_list(
          person_id, ac_role_id, object_id, object_type,
          created_at, updated_at, context_id, parent_id)
      SELECT acl.person_id, acrn.id, r.destination_id, r.destination_type,
             acl.created_at, acl.updated_at, acl.context_id, acl.id
      FROM access_control_list AS acl
      JOIN access_control_roles AS acr ON acr.id = acl.ac_role_id
      JOIN access_control_roles AS acrn ON acrn.name = '{role}'
      JOIN relationships AS r on r.source_id = acl.object_id
       AND r.source_type = acl.object_type
      WHERE acr.name = '{role}'
        AND (r.destination_type = '{table}');
      """.format(role=ROLE_PROPAGATION[new_role], table=table)))

      # Mapped through destination:
      connection.execute(
          text("""
      INSERT INTO access_control_list(
          person_id, ac_role_id, object_id, object_type,
          created_at, updated_at, context_id, parent_id)
      SELECT acl.person_id, acrn.id, r.source_id, r.source_type,
             acl.created_at, acl.updated_at, acl.context_id, acl.id
      FROM access_control_list AS acl
      JOIN access_control_roles AS acr ON acr.id = acl.ac_role_id
      JOIN access_control_roles AS acrn ON acrn.name = '{role}'
      JOIN relationships AS r on r.destination_id = acl.object_id
       AND r.destination_type = acl.object_type
      WHERE acr.name = '{role}'
        AND (r.source_type = '{table}');
      """.format(role=ROLE_PROPAGATION[new_role], table=table)))


def _propagate_to_audit(connection):
  """Propagates the audit part

     - Audit
       - Assessment Templates
       - Snapshots
       - Assessments
         - Comments & Documents
       - Issues
         - Comments & Documents
  """
  for _, new_role in ROLE_MIGRATION.items():
    # Program Roles -> Audit
    connection.execute(
        text("""
    INSERT INTO access_control_list(
        person_id, ac_role_id, object_id, object_type,
        created_at, updated_at, context_id, parent_id)
    SELECT acl.person_id, acrn.id, a.id, 'Audit',
           acl.created_at, acl.updated_at, a.context_id, acl.id
    FROM access_control_list AS acl
    JOIN access_control_roles AS acr ON acr.id = acl.ac_role_id
     AND acr.name = '{}'
    JOIN access_control_roles as acrn ON acrn.name = '{}'
    JOIN audits AS a
      ON a.program_id = acl.object_id AND acl.object_type = 'Program';
    """.format(new_role, ROLE_PROPAGATION[new_role])))

  # Program Audit Roles -> Snapshots, Assessments, Issues, Assessment Templates
  for role in ROLE_PROPAGATION.values():
    _insert_acl_from_mapped([
        AC_TABLE("Snapshot", "snapshots", role,
                 role),
        AC_TABLE("Assessment", "assessments", role,
                 role),
        AC_TABLE("Issue", "issues", role,
                 role),
        AC_TABLE("AssessmentTemplate", "assessment_templates", role,
                 role),
    ], connection)

  # Program Assessment & Issues Roles -> Documents and Comments
  for role in ROLE_PROPAGATION.values():
    _insert_acl_from_second_level([
        AC_TABLE("Document", "Assessment", role,
                 role),
        AC_TABLE("Comment", "Assessment", role,
                 role),
        AC_TABLE("Document", "Issue", role,
                 role),
        AC_TABLE("Comment", "Issue", role,
                 role)
    ], connection)


def upgrade():
  """Upgrade database schema and/or data, creating a new revision."""
  connection = op.get_bind()
  _check_new_role_names(connection)
  _create_new_roles(connection)
  _migrate_program_roles(connection)
  _propagate_to_mapped(connection)
  _propagate_to_audit(connection)


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
      assignee_types=ALL_ROLES.keys()
  )
  connection.execute(
      text("""
          DELETE FROM access_control_roles
          WHERE name IN :assignee_types
      """),
      assignee_types=ALL_ROLES.keys()
  )
