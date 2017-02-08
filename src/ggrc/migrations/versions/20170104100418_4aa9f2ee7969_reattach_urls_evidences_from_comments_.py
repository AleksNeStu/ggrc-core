# Copyright (C) 2016 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""
Reattach URLs/Evidences from Comments to Assessments

Create Date: 2017-01-04 10:04:18.770087
"""
# disable Invalid constant name pylint warning for mandatory Alembic variables.
# pylint: disable=invalid-name

from alembic import op

# revision identifiers, used by Alembic.
revision = '4aa9f2ee7969'
down_revision = '6e9a3ed063d2'


def upgrade():
  """Upgrade database schema and/or data, creating a new revision."""
  op.execute("""
      update ignore object_documents as od join
             relationships as r on od.documentable_type = r.source_type and
                                   od.documentable_id = r.source_id
      set od.documentable_type = r.destination_type,
          od.documentable_id = r.destination_id
      where od.documentable_type = 'Comment' and
            r.destination_type = 'Assessment'
  """)
  op.execute("""
      update ignore object_documents as od join
            relationships as r on od.documentable_type = r.destination_type and
                                  od.documentable_id = r.destination_id
      set od.documentable_type = r.source_type,
          od.documentable_id = r.source_id
      where od.documentable_type = 'Comment' and
            r.source_type = 'Assessment'
  """)

  relationship_update_skeleton = """
      update ignore relationships as rel1 join
             relationships as rel2 on
                 {rel1_comment}_type = 'Comment' and
                 {rel2_comment}_type = 'Comment' and
                 {rel1_comment}_id = {rel2_comment}_id
      set {rel1_comment}_type = {assessment}_type,
          {rel1_comment}_id = {assessment}_id
      where {assessment}_type = 'Assessment' and
            {document}_type = 'Document'
  """

  # (rel1.src_type <-> rel1.dst_type & rel2.src_type <-> rel2.dst_type)
  # Comment <-> Document & Comment <-> Assessment
  # Comment <-> Document & Assessment <-> Comment
  # Document <-> Comment & Comment <-> Assessment
  # Document <-> Comment & Assessment <-> Comment
  for rel1_comment, rel2_comment, document, assessment in (
      ("rel1.source", "rel2.source", "rel1.destination", "rel2.destination"),
      ("rel1.source", "rel2.destination", "rel1.destination", "rel2.source"),
      ("rel1.destination", "rel2.source", "rel1.source", "rel2.destination"),
      ("rel1.destination", "rel2.destination", "rel1.source", "rel2.source"),
  ):
    op.execute(relationship_update_skeleton.format(
        rel1_comment=rel1_comment, rel2_comment=rel2_comment,
        document=document, assessment=assessment,
    ))

  # Every remaining Comment<->Document mapping relates to orphaned Comments
  op.execute("""
      delete from object_documents
      where documentable_type = 'Comment'
  """)

  # Remove Comment<->NotAssessment mappings: only Assessment is Commentable
  op.execute("""
      delete from relationships
      where source_type = 'Comment' and destination_type != 'Assessment'
  """)
  op.execute("""
      delete from relationships
      where source_type != 'Assessment' and destination_type = 'Comment'
  """)

  # Remove unmapped Documents
  op.execute("""
      delete d from documents as d left join
                    object_documents as od on od.document_id = d.id left join
                    relationships as r on r.source_type = 'Document' and
                                          r.source_id = d.id or
                                          r.destination_type = 'Document' and
                                          r.destination_id = d.id
      where od.id is NULL and r.id is NULL
  """)

  # Remove unmapped Comments
  op.execute("""
      delete c from comments as c left join
                    relationships as r on r.source_type = 'Comment' and
                                          r.source_id = c.id or
                                          r.destination_type = 'Comment' and
                                          r.destination_id = c.id
      where r.id is NULL
  """)

  # Remove orphaned ObjectOwners
  models_tables = (
      ("Comment", "comments"),
      ("Document", "documents"),
  )
  for model, table in models_tables:
    op.execute("""
        delete object_owners
        from object_owners left join
             {table} on object_owners.ownable_id = {table}.id and
                        object_owners.ownable_type = '{model}'
        where object_owners.ownable_type = '{model}' and {table}.id is NULL
    """.format(table=table, model=model))


def downgrade():
  """Downgrade database schema and/or data back to the previous revision."""
  pass
