# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Generic handlers for imports and exports."""

import re
from logging import getLogger
from datetime import date
from dateutil.parser import parse

from sqlalchemy import and_
from sqlalchemy import or_

from ggrc import db
from ggrc.converters import errors
from ggrc.converters import get_exportables
from ggrc.login import get_current_user
from ggrc.models import Audit
from ggrc.models import CategoryBase
from ggrc.models import Contract
from ggrc.models import Assessment
from ggrc.models import ObjectPerson
from ggrc.models import Option
from ggrc.models import Person
from ggrc.models import Policy
from ggrc.models import Program
from ggrc.models import Regulation
from ggrc.models import Relationship
from ggrc.models import Standard
from ggrc.models import all_models
from ggrc.models.reflection import AttributeInfo
from ggrc.rbac import permissions


# pylint: disable=invalid-name
logger = getLogger(__name__)

MAPPING_PREFIX = "__mapping__:"
CUSTOM_ATTR_PREFIX = "__custom__:"


class ColumnHandler(object):
  """Default column handler.

  This handler can be used on any model attribute that can accept normal text
  value.
  """

  def __init__(self, row_converter, key, **options):
    self.row_converter = row_converter
    self.key = key
    self.value = None
    self.set_empty = False
    self.raw_value = options.get("raw_value", "").strip()
    self.validator = options.get("validator")
    self.mandatory = options.get("mandatory", False)
    self.view_only = options.get("view_only", False)
    self.default = options.get("default")
    self.description = options.get("description", "")
    self.display_name = options.get("display_name", "")
    self.dry_run = row_converter.block_converter.converter.dry_run
    self.new_objects = self.row_converter.block_converter.converter.new_objects
    self.unique = options.get("unique", False)
    if options.get("parse"):
      self.set_value()

  def check_unique_consistency(self):
    """Returns true if no object exists with the same unique field."""
    if not self.unique:
      return
    if not self.value:
      return
    if not self.row_converter.obj:
      return
    nr_duplicates = self.row_converter.object_class.query.filter(and_(
        getattr(self.row_converter.object_class, self.key) == self.value,
        self.row_converter.object_class.id != self.row_converter.obj.id
    )).count()
    if nr_duplicates > 0:
      self.add_error(errors.DUPLICATE_VALUE,
                     column_name=self.key,
                     value=self.value)
      self.row_converter.set_ignore()

  def set_value(self):
    "set value for current culumn after parsing"
    self.value = self.parse_item()

  def get_value(self):
    "get value for current column from instance"
    return getattr(self.row_converter.obj, self.key, self.value)

  def add_error(self, template, **kwargs):
    "add error to current row"
    self.row_converter.add_error(template, **kwargs)

  def add_warning(self, template, **kwargs):
    "add warning to current row"
    self.row_converter.add_warning(template, **kwargs)

  def parse_item(self):
    "Parse item default handler"
    return self.raw_value

  def set_obj_attr(self):
    "Set attribute value to object"
    if not self.set_empty and not self.value:
      return
    try:
      if getattr(self.row_converter.obj, self.key, None) != self.value:
        setattr(self.row_converter.obj, self.key, self.value)
    except ValueError as e:
      self.add_error(errors.VALIDATION_ERROR, column_name=self.display_name,
                     message=e.message)
    except:  # pylint: disable=bare-except
      self.add_error(errors.UNKNOWN_ERROR)
      logger.exception(
          "Import failed with setattr(%r, %r, %r)",
          self.row_converter.obj, self.key, self.value,
      )

  def get_default(self):
    "Get default value to column"
    if callable(self.default):
      return self.default()
    return self.default

  def insert_object(self):
    """ For inserting fields such as custom attributes and mappings """
    pass


class DeleteColumnHandler(ColumnHandler):
  """Column handler for deleting objects."""

  # this is a white list of objects that can be deleted in a cascade
  # e.g. deleting a Market can delete the associated Relationship object too
  DELETE_WHITELIST = {"Relationship", "AccessControlList", "ObjectPerson"}
  ALLOWED_VALUES = {"", "no", "false", "true", "yes", "force"}
  TRUE_VALUES = {"true", "yes", "force"}

  def __init__(self, *args, **kwargs):
    self._allow_cascade = False
    super(DeleteColumnHandler, self).__init__(*args, **kwargs)

  def get_value(self):
    return ""

  def parse_item(self):
    if self.raw_value.lower() not in self.ALLOWED_VALUES:
      self.add_error(errors.WRONG_VALUE_ERROR, column_name=self.display_name)
      return False
    is_delete = self.raw_value.lower() in self.TRUE_VALUES
    self._allow_cascade = self.raw_value.lower() == "force"
    self.row_converter.is_delete = is_delete
    return is_delete

  def set_obj_attr(self):
    if not self.value:
      return
    obj = self.row_converter.obj
    if self.row_converter.is_new:
      self.add_error(errors.DELETE_NEW_OBJECT_ERROR,
                     object_type=obj.type,
                     slug=obj.slug)
      return
    if self.row_converter.ignore:
      return
    tr = db.session.begin_nested()
    try:
      tr.session.delete(obj)
      deleted = len([o for o in tr.session.deleted
                     if o.type not in self.DELETE_WHITELIST])
      if deleted > 1 and not self._allow_cascade:
        self.add_error(errors.DELETE_CASCADE_ERROR,
                       object_type=obj.type, slug=obj.slug)
    finally:
      if self.dry_run or self.row_converter.ignore:
        tr.rollback()
      else:
        indexer = self.row_converter.block_converter.converter.indexer
        if indexer is not None:
          for o in tr.session.deleted:
            indexer.delete_record(o.id, o.__class__.__name__, commit=False)
        tr.commit()


class StatusColumnHandler(ColumnHandler):

  def __init__(self, row_converter, key, **options):
    self.key = key
    self.valid_states = row_converter.object_class.VALID_STATES
    self.state_mappings = {str(s).lower(): s for s in self.valid_states}
    super(StatusColumnHandler, self).__init__(row_converter, key, **options)

  def parse_item(self):
    value = self.raw_value.lower()
    status = self.state_mappings.get(value)
    if status is None:
      self.add_warning(
          errors.WRONG_VALUE_DEFAULT, column_name=self.display_name)
      status = self.row_converter.object_class.default_status()
    return status


class UserColumnHandler(ColumnHandler):
  """Handler for a single user fields.

  Used for primary and secondary contacts.
  """

  def get_users_list(self):
    users = set()
    email_lines = self.raw_value.splitlines()
    owner_emails = filter(unicode.strip, email_lines)  # noqa
    for raw_line in owner_emails:
      email = raw_line.strip().lower()
      person = self.get_person(email)
      if person:
        users.add(person)
      else:
        self.add_warning(errors.UNKNOWN_USER_WARNING, email=email)
    return list(users)

  def get_person(self, email):
    new_objects = self.row_converter.block_converter.converter.new_objects
    if email not in new_objects[Person]:
      new_objects[Person][email] = Person.query.filter_by(email=email).first()
    return new_objects[Person].get(email)

  def parse_item(self):
    email = self.raw_value.lower()
    person = self.get_person(email)
    if not person:
      if email != "":
        self.add_warning(errors.UNKNOWN_USER_WARNING, email=email)
      elif self.mandatory:
        self.add_error(errors.MISSING_VALUE_ERROR,
                       column_name=self.display_name)
    return person

  def get_value(self):
    person = getattr(self.row_converter.obj, self.key)
    if person:
      return person.email
    return self.value


class UsersColumnHandler(UserColumnHandler):
  """Handler for multi user fields."""

  def parse_item(self):
    people = set()
    email_lines = self.raw_value.splitlines()
    owner_emails = filter(unicode.strip, email_lines)  # noqa
    for raw_line in owner_emails:
      email = raw_line.strip().lower()
      person = self.get_person(email)
      if person:
        people.add(person)
      else:
        self.add_warning(errors.UNKNOWN_USER_WARNING, email=email)

    if not people and self.mandatory:
      self.add_warning(errors.OWNER_MISSING, column_name=self.display_name)
      people.add(get_current_user())

    return list(people)


class SlugColumnHandler(ColumnHandler):

  def parse_item(self):
    if self.raw_value:
      return self.raw_value
    return ""


class DateColumnHandler(ColumnHandler):

  def parse_item(self):
    value = self.raw_value.strip()
    if value and not re.match(r"[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}|"
                              r"[0-9]{1,2}/[0-9]{1,2}/[0-9]{4}",
                              self.raw_value.strip()):
      self.add_error(errors.UNKNOWN_DATE_FORMAT, column_name=self.display_name)
      return

    # TODO: change all importable date columns' type from 'DateTime'
    # to 'Date' type. Remove if statement after it.
    try:
      if not value:
        return
      parsed_value = parse(value)
      if self.key == "last_assessment_date":
        self.check_last_asmnt_date(parsed_value)
      if type(getattr(self.row_converter.obj, self.key, None)) is date:
        return parsed_value.date()
      else:
        return parsed_value
    except:
      self.add_error(errors.WRONG_VALUE_ERROR, column_name=self.display_name)

  def get_value(self):
    value = getattr(self.row_converter.obj, self.key)
    if value:
      return value.strftime("%m/%d/%Y")
    return ""

  def check_last_asmnt_date(self, new_last_asmnt_date):
    """Check if the new object don't contain changed Last Assessment Date."""
    old_last_asmnt_date = getattr(
        self.row_converter.obj, "last_assessment_date", None
    )
    date_modified = old_last_asmnt_date and new_last_asmnt_date and \
        old_last_asmnt_date.date() != new_last_asmnt_date.date()
    if date_modified:
      self.add_warning(
          errors.UNMODIFIABLE_COLUMN,
          column_name=self.display_name,
      )


class EmailColumnHandler(ColumnHandler):

  def parse_item(self):
    """ emails are case insensitive """
    email = self.raw_value.lower()
    if not email:
      self.add_error(errors.MISSING_VALUE_ERROR, column_name="Email")
    elif not Person.is_valid_email(email):
      self.add_error(errors.WRONG_VALUE_ERROR, column_name=self.display_name)
      return ""
    return email


class TextColumnHandler(ColumnHandler):

  """ Single line text field handler """

  def parse_item(self):
    """ Remove multiple spaces and new lines from text """
    if not self.raw_value:
      return ""

    return self.clean_whitespaces(self.raw_value)

  @staticmethod
  def clean_whitespaces(value):
    return re.sub(r'\s+', " ", value)


class RequiredTextColumnHandler(TextColumnHandler):

  def parse_item(self):
    value = self.raw_value or ""
    clean_value = self.clean_whitespaces(value)
    if not clean_value:
      self.add_error(errors.MISSING_VALUE_ERROR, column_name=self.display_name)
    return clean_value


class TextareaColumnHandler(ColumnHandler):

  """ Multi line text field handler """

  def parse_item(self):
    """ Remove multiple spaces and new lines from text """
    if not self.raw_value:
      if self.mandatory:
        self.add_error(errors.MISSING_VALUE_ERROR,
                       column_name=self.display_name)
      return ""

    return re.sub(r'\s+', " ", self.raw_value).strip()


class MappingColumnHandler(ColumnHandler):

  """ Handler for mapped objects """

  def __init__(self, row_converter, key, **options):
    self.key = key
    exportable = get_exportables()
    self.attr_name = options.get("attr_name", "")
    self.mapping_object = exportable.get(self.attr_name)
    self.new_slugs = row_converter.block_converter.converter.new_objects[
        self.mapping_object]
    self.unmap = self.key.startswith(AttributeInfo.UNMAPPING_PREFIX)
    super(MappingColumnHandler, self).__init__(row_converter, key, **options)

  def parse_item(self):
    """Parse a list of slugs to be mapped.

    Parse a new line separated list of slugs and check if they are valid
    objects.

    Returns:
      list of objects. During dry_run, the list can contain a slug instead of
      an actual object if that object will be generated in the current import.
    """
    # pylint: disable=protected-access
    class_ = self.mapping_object
    lines = set(self.raw_value.splitlines())
    slugs = set([slug.lower() for slug in lines if slug.strip()])
    objects = []
    for slug in slugs:
      obj = class_.query.filter_by(slug=slug).first()
      if obj:
        if permissions.is_allowed_update_for(obj):
          objects.append(obj)
        else:
          self.add_warning(
              errors.MAPPING_PERMISSION_ERROR,
              object_type=class_._inflector.human_singular.title(),
              slug=slug,
          )
      elif slug in self.new_slugs and not self.dry_run:
        objects.append(self.new_slugs[slug])
      elif slug in self.new_slugs and self.dry_run:
        objects.append(slug)
      else:
        self.add_warning(errors.UNKNOWN_OBJECT,
                         object_type=class_._inflector.human_singular.title(),
                         slug=slug)
    if self.mandatory and not objects and self.row_converter.is_new:
      self.add_error(errors.MISSING_VALUE_ERROR, column_name=self.display_name)
    return objects

  def set_obj_attr(self):
    self.value = self.parse_item()

  def insert_object(self):
    """ Create a new mapping object """
    if self.dry_run or not self.value:
      return
    current_obj = self.row_converter.obj
    relationships = []
    mapping = None
    for obj in self.value:
      if current_obj.id:
        mapping = Relationship.find_related(current_obj, obj)
      if not self.unmap and not mapping:
        if not (self.mapping_object.__name__ == "Audit" and
                not getattr(current_obj, "allow_map_to_audit", True)):
          mapping = Relationship(source=current_obj, destination=obj)
          relationships.append(mapping)
          db.session.add(mapping)
        else:
          self.add_warning(errors.SINGLE_AUDIT_RESTRICTION,
                           mapped_type=obj.type,
                           object_type=current_obj.type)
      elif self.unmap and mapping:
        db.session.delete(mapping)
    db.session.flush()
    self.dry_run = True

  def get_value(self):
    if self.unmap or not self.mapping_object:
      return ""
    cache = self.row_converter.block_converter.get_mapping_cache()
    slugs = cache[self.row_converter.obj.id][self.mapping_object.__name__]
    return "\n".join(slugs)

  def set_value(self):
    pass


class ConclusionColumnHandler(ColumnHandler):

  """ Handler for design and operationally columns in ControlAssesments """

  CONCLUSION_MAP = {i.lower(): i for i in Assessment.VALID_CONCLUSIONS}

  def parse_item(self):
    """Parse conclusion design and operational values."""

    value = self.CONCLUSION_MAP.get(self.raw_value.lower(), "")
    if self.raw_value and not value:
      self.add_warning(errors.WRONG_VALUE, column_name=self.display_name)
    return value


class OptionColumnHandler(ColumnHandler):
  """Column handler for option fields.

  This column handler is used only for option fields that have their values
  stored in the Options table. Hardcoded options and boolean options should
  not be handled by this class.
  """

  def parse_item(self):
    if not self.mandatory and self.raw_value in {"--", "---"}:
      self.set_empty = True
      return None
    prefixed_key = "{}_{}".format(
        self.row_converter.object_class._inflector.table_singular, self.key)
    item = Option.query.filter(
        and_(Option.title == self.raw_value.strip(),
             or_(Option.role == self.key,
                 Option.role == prefixed_key))).first()
    return item

  def get_value(self):
    option = getattr(self.row_converter.obj, self.key, None)
    if option is None:
      return "--"
    if callable(option.title):
      return option.title()
    return option.title


class ParentColumnHandler(ColumnHandler):

  """ handler for directly mapped columns """

  parent = None

  def __init__(self, row_converter, key, **options):
    super(ParentColumnHandler, self).__init__(row_converter, key, **options)

  def parse_item(self):
    """ get parent object """
    # pylint: disable=protected-access
    if self.raw_value == "":
      self.add_error(errors.MISSING_VALUE_ERROR, column_name=self.display_name)
      return None
    slug = self.raw_value
    obj = self.new_objects.get(self.parent, {}).get(slug)
    if obj is None:
      obj = self.parent.query.filter(self.parent.slug == slug).first()
    if obj is None:
      self.add_error(errors.UNKNOWN_OBJECT,
                     object_type=self.parent._inflector.human_singular.title(),
                     slug=slug)
      return None
    context_id = None
    if hasattr(obj, "context_id") and \
       hasattr(self.row_converter.obj, "context_id"):
      context_id = obj.context_id
      if context_id is not None:
        name = self.row_converter.obj.__class__.__name__
        if not permissions.is_allowed_create(name, None, context_id) \
           and not permissions.has_conditions('create', name):
          self.add_error(errors.MAPPING_PERMISSION_ERROR,
                         object_type=obj.type, slug=slug)
          return None
    return obj

  def set_obj_attr(self):
    super(ParentColumnHandler, self).set_obj_attr()
    # inherit context
    obj = self.row_converter.obj
    parent = getattr(obj, self.key, None)
    if parent is not None and \
       hasattr(obj, "context") and \
       hasattr(parent, "context") and \
       parent.context is not None:
      obj.context = parent.context

  def get_value(self):
    value = getattr(self.row_converter.obj, self.key, self.value)
    if not value:
      return None
    return value.slug


class ProgramColumnHandler(ParentColumnHandler):
  """Handler for program column on audit imports."""

  def __init__(self, row_converter, key, **options):
    self.parent = Program
    super(ProgramColumnHandler, self).__init__(row_converter, key, **options)

  def set_obj_attr(self):
    if self.row_converter.is_new:
      super(ProgramColumnHandler, self).set_obj_attr()


class SectionDirectiveColumnHandler(MappingColumnHandler):

  def get_directive_from_slug(self, directive_class, slug):
    if slug in self.new_objects[directive_class]:
      return self.new_objects[directive_class][slug]
    return directive_class.query.filter_by(slug=slug).first()

  def parse_item(self):
    """ get a directive from slug """
    allowed_directives = [Policy, Regulation, Standard, Contract]
    if self.raw_value == "":
      return None
    slug = self.raw_value
    for directive_class in allowed_directives:
      directive = self.get_directive_from_slug(directive_class, slug)
      if directive is not None:
        return [directive]
    self.add_error(errors.UNKNOWN_OBJECT, object_type="Program", slug=slug)
    return None

  def get_value(self):
    # Legacy field. With the new mapping system it is not possible to determine
    # which was the primary directive that has been mapped
    return ""


class AuditColumnHandler(MappingColumnHandler):
  """Handler for mandatory Audit mappings on Assessments."""

  def __init__(self, row_converter, key, **options):
    key = "{}audit".format(MAPPING_PREFIX)
    super(AuditColumnHandler, self).__init__(row_converter, key, **options)

  def set_obj_attr(self):
    """Set values to be saved.

    This saves the value for creating the relationships, and if the dry_run
    flag is not set, it will also set the correct context to the parent object.
    """
    self.value = self.parse_item()
    if not self.value:
      # If there is no mandatory value, the parse item will already mark the
      # error, so there is no need to do anything here.
      return

    audit = self.value[0]

    if isinstance(audit, Audit):
      if not self.row_converter.is_new and \
              audit.slug != self.row_converter.obj.audit.slug:
        self.add_warning(errors.UNMODIFIABLE_COLUMN,
                         column_name=self.display_name)
        self.value = []
      else:
        self.row_converter.obj.context = audit.context
        self.row_converter.obj.audit = audit


class ObjectPersonColumnHandler(UserColumnHandler):

  """
  ObjectPerson handler for all specific columns such as "owner" or any other
  role. This handler will remove all people not listed in the value and will
  add people that are missing.
  """

  def parse_item(self):
    return self.get_users_list()

  def set_obj_attr(self):
    pass

  def get_value(self):
    object_person = db.session.query(ObjectPerson.person_id).filter_by(
        personable_id=self.row_converter.obj.id,
        personable_type=self.row_converter.obj.__class__.__name__)
    users = Person.query.filter(Person.id.in_(object_person))
    emails = [user.email for user in users]
    return "\n".join(emails)

  def remove_current_people(self):
    ObjectPerson.query.filter_by(
        personable_id=self.row_converter.obj.id,
        personable_type=self.row_converter.obj.__class__.__name__).delete()

  def insert_object(self):
    if self.dry_run or not self.value:
      return
    self.remove_current_people()
    for person in self.value:
      object_person = ObjectPerson(
          personable=self.row_converter.obj,
          person=person,
          context=self.row_converter.obj.context
      )
      db.session.add(object_person)
      db.session.flush()
    self.dry_run = True


class PersonMappingColumnHandler(ObjectPersonColumnHandler):

  """
  This handler will only add people listed in self.value if they are not yet
  connected to the current object.
  """

  def remove_current_people(self):
    obj = self.row_converter.obj
    self.value = [person for person in self.value
                  if not ObjectPerson.query.filter_by(
                      personable_id=obj.id,
                      personable_type=obj.__class__.__name__,
                      person=person).count()
                  ]


class PersonUnmappingColumnHandler(ObjectPersonColumnHandler):

  """
  This handler will only remove people listed in self.value if they are already
  connected to the current object.
  """

  def insert_object(self):
    if self.dry_run or not self.value:
      return
    obj = self.row_converter.obj
    context = getattr(obj, 'context', None)
    user_role = getattr(all_models, 'UserRole', None)
    for person in self.value:
      ObjectPerson.query.filter_by(
          personable_id=obj.id,
          personable_type=obj.__class__.__name__,
          person=person
      ).delete()
      if context and user_role:
        # The fix is a bit hackish, because it uses ``UserRole`` model
        # from ``ggrc_basic_permissions``. But it is the only way I found to
        # fix the issue, without massive refactoring.
        user_role.query.filter_by(person=person, context=context).delete()
    self.dry_run = True


class CategoryColumnHandler(ColumnHandler):

  def parse_item(self):
    names = [v.strip() for v in self.raw_value.split("\n")]
    names = [name for name in names if name != ""]
    if not names:
      return None
    categories = CategoryBase.query.filter(and_(
        CategoryBase.name.in_(names),
        CategoryBase.type == self.category_base_type
    )).all()
    category_names = set([c.name.strip() for c in categories])
    for name in names:
      if name not in category_names:
        self.add_warning(errors.WRONG_MULTI_VALUE,
                         column_name=self.display_name,
                         value=name)
    return categories

  def set_obj_attr(self):
    if self.value is None:
      return
    setattr(self.row_converter.obj, self.key, self.value)

  def get_value(self):
    categories = getattr(self.row_converter.obj, self.key, self.value)
    categorie_names = [c.name for c in categories]
    return "\n".join(categorie_names)


class ControlCategoryColumnHandler(CategoryColumnHandler):

  def __init__(self, row_converter, key, **options):
    self.category_base_type = "ControlCategory"
    super(ControlCategoryColumnHandler, self).__init__(
        row_converter, key, **options)


class ControlAssertionColumnHandler(CategoryColumnHandler):

  def __init__(self, row_converter, key, **options):
    self.category_base_type = "ControlAssertion"
    super(ControlAssertionColumnHandler, self).__init__(
        row_converter, key, **options)


class DocumentsColumnHandler(ColumnHandler):

  def get_value(self):
    lines = [u"{} {}".format(d.title, d.link)
             for d in self.row_converter.obj.documents]
    return u"\n".join(lines)

  def parse_item(self):
    lines = [line.rsplit(" ", 1) for line in self.raw_value.splitlines()]
    documents = []
    for line in lines:
      if len(line) != 2:
        self.add_warning(errors.WRONG_VALUE, column_name=self.display_name)
        continue
      title, link = line
      documents.append(
          all_models.Document(title=title.strip(), link=link.strip()))
    return documents

  def set_obj_attr(self):
    pass

  def insert_object(self):
    if self.dry_run or not self.value:
      return
    self.row_converter.obj.documents = self.value
    self.dry_run = True


class ExportOnlyColumnHandler(ColumnHandler):

  def __init__(self, *args, **kwargs):
    kwargs["view_only"] = True
    kwargs["mandatory"] = False
    super(ExportOnlyColumnHandler, self).__init__(*args, **kwargs)

  def parse_item(self):
    pass

  def set_obj_attr(self):
    pass

  def get_value(self):
    return super(ExportOnlyColumnHandler, self).get_value()

  def insert_object(self):
    pass

  def set_value(self):
    pass


ExportOnlyDateColumnHandler = type(
    "ExportOnlyDateColumnHandler",
    (ExportOnlyColumnHandler, DateColumnHandler),
    {}
)


ExportOnlyUserColumnHandler = type(
    "ExportOnlyUserColumnHandler",
    (ExportOnlyColumnHandler, UserColumnHandler),
    {}
)
