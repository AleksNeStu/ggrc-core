# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""
Move object owners to ACL

Create Date: 2017-05-25 14:43:37.605749
"""
# disable Invalid constant name pylint warning for mandatory Alembic variables.
# pylint: disable=invalid-name
from sqlalchemy.sql import text

from alembic import op

from ggrc import db

revision = '281fea549981'
down_revision = '47d3cb39bad7'

OWNER_ROLE_NAME = 'Admin'
OBJECT_OWNERS = 'Object Owners'
OWNABLE_MODELS = [
    'AccessGroup',
    'Clause',
    'Comment',
    'Contract',
    'Control',
    'DataAsset',
    'Document',
    'Facility',
    'Issue',
    'Market',
    'Objective',
    'OrgGroup',
    'Policy',
    'Process',
    'Product',
    'Project',
    'Regulation',
    'Risk',
    'Section',
    'Standard',
    'System',
    'Threat',
    'Vendor',
]


def create_acr_admins():
  """Create Admin role in ACR for each ownable model"""

  connection = op.get_bind()
  for model in OWNABLE_MODELS:
    connection.execute(
        text("""
             INSERT INTO access_control_roles
                 (name, object_type, created_at, updated_at, mandatory)
             SELECT :role, :type, NOW(), NOW(), :mandatory
             FROM access_control_roles
             WHERE NOT EXISTS(
                 SELECT id
                 FROM access_control_roles
                 WHERE name = :role AND object_type = :type
             )
             LIMIT 1
        """),
        role=OWNER_ROLE_NAME,
        type=model,
        mandatory=u"1"
    )


def migrate_owners(type_):
  """Move object owners into ACL table. Clean object owners table

  Args:
    type_(str): Type of objects that should be migrated
  """
  # Fetch id for AC Admin role
  connection = op.get_bind()
  acr_id = connection.execute(
      text("""
          SELECT id
          FROM access_control_roles
          WHERE name = :role AND object_type = :type
      """), role=OWNER_ROLE_NAME, type=type_).fetchone()
  db.session.commit()

  # Migrate each object owner to access_control_list
  connection.execute(
      text("""
           INSERT INTO access_control_list(person_id, ac_role_id,
              object_id, object_type, modified_by_id, created_at,
              updated_at, context_id)
           SELECT person_id, :role_id, ownable_id, :type,
              modified_by_id, NOW(), NOW(), context_id
           FROM object_owners
           WHERE ownable_type = :type
      """),
      role_id=acr_id[0],
      type=type_
  )


def update_assessment_templates(downgrade=False):
  """Update assigned people categaries for asessment template"""
  connection = op.get_bind()
  old_name, new_name = OBJECT_OWNERS, OWNER_ROLE_NAME
  if downgrade:
    old_name, new_name = new_name, old_name
  connection.execute(text("""
      UPDATE assessment_templates
      SET default_people = REPLACE(default_people, :old_name, :new_name)
      WHERE default_people LIKE CONCAT("%", :old_name, "%")
  """), old_name=old_name, new_name=new_name)


def upgrade():
  """Upgrade database schema and/or data, creating a new revision."""
  # Need to create Admin role for all ownable models to enable import of
  # "Admin" field
  create_acr_admins()

  connection = op.get_bind()
  ownable_objects = connection.execute("""
      SELECT DISTINCT ownable_type
      FROM object_owners
  """).fetchall()

  for obj in ownable_objects:
    if obj[0] in OWNABLE_MODELS:
      migrate_owners(obj[0])

  update_assessment_templates()


def downgrade():
  """Downgrade database schema and/or data back to the previous revision."""
  # Remove all ACL rows linked with Admin role
  connection = op.get_bind()
  connection.execute(
      text("""
           DELETE acl FROM access_control_list acl
           JOIN access_control_roles acr ON acr.id = acl.ac_role_id
           WHERE acr.name = :role
      """), role=OWNER_ROLE_NAME
  )

  # Remove all Admin roles
  connection.execute(
      text("""
           DELETE FROM access_control_roles
           WHERE name = :role_
      """), role_=OWNER_ROLE_NAME
  )

  # Return Object Owners group for assessment templates
  update_assessment_templates(downgrade=True)
