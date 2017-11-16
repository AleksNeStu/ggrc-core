# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""
Migrate audit roles to ACL

Create Date: 2017-11-16 11:54:34.683066
"""
# disable Invalid constant name pylint warning for mandatory Alembic variables.
# pylint: disable=invalid-name

from collections import namedtuple
from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '1035f388d822'
down_revision = '5a7fd43e43ae'

AC_TABLE = namedtuple("AC_TABLE", "type table role parent_role")
AC_PERMISSIONS = namedtuple(
    "AC_PERMISSIONS", "read update delete mandatory my_work")
ROLES = {
    "Auditors": AC_PERMISSIONS(1, 0, 0, 0, 1),
    "Audit Captains": AC_PERMISSIONS(1, 1, 1, 1, 1),
}
MAPPED_ROLES = {
    "Audit Captains Mapped": AC_PERMISSIONS(1, 1, 1, 0, 0),
    "Auditors Mapped": AC_PERMISSIONS(1, 0, 0, 0, 0),
    "Auditors Assessment Mapped": AC_PERMISSIONS(1, 1, 0, 0, 0),
    "Auditors Document Mapped": AC_PERMISSIONS(1, 1, 0, 0, 0),
    "Auditors Snapshot Mapped": AC_PERMISSIONS(1, 1, 0, 0, 0),
    "Auditors Issue Mapped": AC_PERMISSIONS(1, 1, 0, 0, 0),
}
ALL_ROLES = dict(ROLES, **MAPPED_ROLES)

connection = op.get_bind()


def _check_new_role_names():
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


def _create_new_roles():
  """Inserts new roles based on ALL_ROLES list"""
  for role, permissions in ALL_ROLES.items():
    connection.execute(
        text("""
            INSERT INTO access_control_roles(
                name, object_type, created_at, updated_at, `read`, `update`,
                `delete`, mandatory, non_editable, internal, my_work
            )
            VALUES(
                :role, :object_type, NOW(), NOW(), :read, :update,
                :delete, :mandatory, :non_editable, :internal, :my_work
            );
        """),
        role=role,
        object_type="Audit",
        read=permissions.read,
        update=permissions.update,
        delete=permissions.delete,
        mandatory=permissions.mandatory,
        my_work=permissions.my_work,
        non_editable="1",
        internal="1" if role in MAPPED_ROLES else "0",
    )


def _migrate_auditors():
  """Migrate Auditors from user roles to access_control_list"""
  # 1. Migrate user_roles to Auditors acr
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
  JOIN access_control_roles as acr on acr.name = 'Auditors'
  WHERE r.name = 'Auditor';
  """))
  # 2. Migrate Audit context objects using context_id
  # snapshots, assessments, documents, issues, assessment templates, snapshots
  _insert_acl_from_mapped([
      AC_TABLE("Snapshot", "snapshots", "Auditors Snapshot Mapped",
               "Auditors"),
      AC_TABLE("Assessment", "assessments", "Auditors Assessment Mapped",
               "Auditors"),
      AC_TABLE("Document", "documents", "Auditors Document Mapped",
               "Auditors"),
      AC_TABLE("Issue", "issues", "Auditors Issue Mapped",
               "Auditors"),
      AC_TABLE("AssessmentTemplate", "assessment_templates", "Auditors Mapped",
               "Auditors"),
  ])


def _migrate_captains():
  """Migrate Audit Captain from audit field to access_control_list"""
  # 1. Migrate audit captains to access_control_list
  connection.execute(
      text("""
  INSERT INTO access_control_list(
      person_id, ac_role_id, object_id, object_type,
      created_at, updated_at, context_id)
  SELECT a.contact_id, acr.id, a.id, 'Audit',
         a.created_at, a.updated_at, a.context_id
  FROM audits AS a
  JOIN access_control_roles AS acr ON acr.name = 'Audit Captains'
  JOIN people AS p ON a.contact_id = p.id;
  """))
  # 2. Migrate Audit context objects using context_id
  # snapshots, assessments, documents, issues, assessment templates, snapshots
  _insert_acl_from_mapped([
      AC_TABLE("Snapshot", "snapshots", "Audit Captains Mapped",
               "Audit Captains"),
      AC_TABLE("Assessment", "assessments", "Audit Captains Mapped",
               "Audit Captains"),
      AC_TABLE("Document", "documents", "Audit Captains Mapped",
               "Audit Captains"),
      AC_TABLE("Issue", "issues", "Audit Captains Mapped",
               "Audit Captains"),
      AC_TABLE("AssessmentTemplate", "assessment_templates",
               "Audit Captains Mapped", "Audit Captains"),
  ])


def _insert_acl_from_mapped(tables):
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
    JOIN access_control_roles AS acr ON acl.ac_role_id = acr.id
    JOIN access_control_roles AS nacr ON nacr.name = '{role}'
    WHERE acr.name = '{parent_role}';
    """.format(**table._asdict())))


def upgrade():
  """Upgrade database schema and/or data, creating a new revision."""
  _check_new_role_names()
  _create_new_roles()
  _migrate_auditors()
  _migrate_captains()


def downgrade():
  """Downgrade database schema and/or data back to the previous revision."""
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
