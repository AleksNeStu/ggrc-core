# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Handlers columns dealing with user roles."""


from sqlalchemy import and_

from ggrc import db
from ggrc.converters import errors
from ggrc.converters.handlers.handlers import UserColumnHandler
from ggrc.login import get_current_user
from ggrc.models import Context
from ggrc.models import Person
from ggrc_basic_permissions.models import Role
from ggrc_basic_permissions.models import UserRole


class ObjectRoleColumnHandler(UserColumnHandler):
  """Basic User role handler"""

  role = -1
  owner_columns = ("program_owner")

  def parse_item(self):
    """Parse new line separated list of emails

    Returns:
      list of User models.
    """
    users = self.get_users_list()
    if not users and self.key in self.owner_columns:
      self.add_warning(errors.OWNER_MISSING, column_name=self.display_name)
      users.append(get_current_user())

    if self.row_converter.is_new and self.mandatory and not users:
      self.add_error(errors.MISSING_VALUE_ERROR,
                     column_name=self.display_name)
    return list(users)

  def set_obj_attr(self):
    pass

  def get_value(self):
    user_role_ids = db.session.query(UserRole.person_id).filter_by(
        role=self.role,
        context_id=self.row_converter.obj.context_id)
    users = Person.query.filter(Person.id.in_(user_role_ids))
    emails = [user.email for user in users]
    return "\n".join(emails)

  def remove_current_roles(self):
    UserRole.query.filter_by(
        role=self.role,
        context_id=self.row_converter.obj.context_id).delete()

  def insert_object(self):
    if self.dry_run or not self.value:
      return
    self.remove_current_roles()
    for owner in self.value:
      user_role = UserRole(
          role=self.role,
          context=self.row_converter.obj.context,
          person=owner
      )
      db.session.add(user_role)
    self.dry_run = True


class ProgramOwnerColumnHandler(ObjectRoleColumnHandler):

  def __init__(self, row_converter, key, **options):
    self.role = Role.query.filter_by(name="ProgramOwner").one()
    super(ProgramOwnerColumnHandler, self).__init__(
        row_converter, key, **options)


class ProgramEditorColumnHandler(ObjectRoleColumnHandler):

  def __init__(self, row_converter, key, **options):
    self.role = Role.query.filter_by(name="ProgramEditor").one()
    super(ProgramEditorColumnHandler, self).__init__(
        row_converter, key, **options)


class ProgramReaderColumnHandler(ObjectRoleColumnHandler):

  def __init__(self, row_converter, key, **options):
    self.role = Role.query.filter_by(name="ProgramReader").one()
    super(ProgramReaderColumnHandler, self).__init__(
        row_converter, key, **options)


class WorkflowOwnerColumnHandler(ObjectRoleColumnHandler):

  def __init__(self, row_converter, key, **options):
    self.role = Role.query.filter_by(name="WorkflowOwner").one()
    super(WorkflowOwnerColumnHandler, self).__init__(
        row_converter, key, **options)


class WorkflowMemberColumnHandler(ObjectRoleColumnHandler):

  def __init__(self, row_converter, key, **options):
    self.role = Role.query.filter_by(name="WorkflowMember").one()
    super(WorkflowMemberColumnHandler, self).__init__(
        row_converter, key, **options)


class AuditAuditorColumnHandler(ObjectRoleColumnHandler):

  def __init__(self, row_converter, key, **options):
    self.role = Role.query.filter_by(name="Auditor").one()
    self.reader = Role.query.filter_by(name="ProgramReader").one()
    super(AuditAuditorColumnHandler, self).__init__(
        row_converter, key, **options)

  def insert_object(self):
    if self.dry_run or not self.value:
      return
    super(AuditAuditorColumnHandler, self).insert_object()
    user_roles = set(map(lambda ur: ur.person_id, self.get_program_roles()))
    context = self.row_converter.obj.program.context
    for auditor in self.value:
      # Check if the role already exists in the database or in the session:
      if auditor.id in user_roles or any(o for o in db.session.new if
                                         isinstance(o, UserRole) and
                                         o.context.id == context.id and
                                         o.person.id == auditor.id):
        continue
      user_role = UserRole(
          role=self.reader,
          context=context,
          person=auditor
      )
      db.session.add(user_role)

  def get_program_roles(self):
    context_id = self.row_converter.obj.program.context.id
    return db.session.query(UserRole).filter(
        UserRole.context_id == context_id).all()


class UserRoleColumnHandler(UserColumnHandler):

  _role_map = {
      "admin": "administrator",
      "ggrc admin": "administrator",
  }

  _allowed_roles = [
      "Administrator",
      "Creator",
      "Editor",
      "Reader",
      ""
  ]

  def parse_item(self):
    value = self.raw_value.lower()
    if value.title() not in self._allowed_roles:
      self.add_error(errors.WRONG_VALUE, column_name=self.display_name)
    name = self._role_map.get(value, value)
    return Role.query.filter_by(name=name).first()

  def set_obj_attr(self):
    pass

  def get_value(self):
    return self.row_converter.obj.system_wide_role

  def remove_current_roles(self):
    allowed_role_ids = db.session.query(Role.id).filter(
        Role.name.in_(self._allowed_roles))
    UserRole.query.filter(and_(
        UserRole.role_id.in_(allowed_role_ids),
        UserRole.person_id == self.row_converter.obj.id)
    ).delete(synchronize_session="fetch")

  def insert_object(self):
    if self.dry_run or not self.value:
      return
    self.remove_current_roles()
    context = None
    if self.value.name == "Administrator":
      context = Context.query.filter_by(name="System Administration").first()
    user_role = UserRole(
        role=self.value,
        person=self.row_converter.obj,
        context=context,
    )
    db.session.add(user_role)
    self.dry_run = True

COLUMN_HANDLERS = {
    "program_editor": ProgramEditorColumnHandler,
    "program_owner": ProgramOwnerColumnHandler,
    "program_reader": ProgramReaderColumnHandler,
    "user_role": UserRoleColumnHandler,
    "user_role:Auditor": AuditAuditorColumnHandler,
    "workflow_member": WorkflowMemberColumnHandler,
    "workflow_owner": WorkflowOwnerColumnHandler,
}
