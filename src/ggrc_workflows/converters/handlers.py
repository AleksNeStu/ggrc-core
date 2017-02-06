# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>


""" Module for all special column handlers for workflow objects """

import datetime

from ggrc import db
from ggrc import models
from ggrc.converters import errors
from ggrc.converters.handlers import boolean
from ggrc.converters.handlers import handlers
from ggrc.converters.handlers import multi_object
from ggrc_basic_permissions import models as bp_models
from ggrc_workflows import models as wf_models


class FrequencyColumnHandler(handlers.ColumnHandler):

  """ Handler for workflow frequency column """

  frequency_map = {
      "one time": "one_time"
  }

  def parse_item(self):
    """ parse frequency value

    Returning None will set the default frequency to one_time.
    """
    if not self.raw_value:
      self.add_error(errors.MISSING_COLUMN, s="",
                     column_names=self.display_name)
      return None
    value = self.raw_value.lower()
    frequency = self.frequency_map.get(value, value)
    if frequency not in self.row_converter.object_class.VALID_FREQUENCIES:
      self.add_error(errors.WRONG_VALUE_ERROR, column_name=self.display_name)
    return frequency

  def get_value(self):
    reverse_map = {v: k for k, v in self.frequency_map.items()}
    value = getattr(self.row_converter.obj, self.key, self.value)
    return reverse_map.get(value, value)


class WorkflowColumnHandler(handlers.ParentColumnHandler):

  """ handler for workflow column in task groups """

  def __init__(self, row_converter, key, **options):
    """ init workflow handler """
    self.parent = wf_models.Workflow
    super(WorkflowColumnHandler, self).__init__(row_converter, key, **options)


class TaskGroupColumnHandler(handlers.ParentColumnHandler):

  """ handler for task group column in task group tasks """

  def __init__(self, row_converter, key, **options):
    """ init task group handler """
    self.parent = wf_models.TaskGroup
    super(TaskGroupColumnHandler, self).__init__(row_converter, key, **options)


class CycleTaskGroupColumnHandler(handlers.ParentColumnHandler):

  """ handler for task group column in task group tasks """

  def __init__(self, row_converter, key, **options):
    """ init task group handler """
    self.parent = wf_models.CycleTaskGroup
    super(CycleTaskGroupColumnHandler, self) \
        .__init__(row_converter, key, **options)


class TaskDateColumnHandler(handlers.ColumnHandler):

  """ handler for start and end columns in task group tasks """

  quarterly_names = {
      1: "Jan/Apr/Jul/Oct",
      2: "Feb/May/Aug/Nov",
      3: "Mar/Jun/Sep/Dec",
  }

  def add_error(self, template, **kwargs):
    """Add row error.

    This function adds a row error for the current task group task and removes
    it from any task groups that it might belong to.
    """
    if self.row_converter.obj.task_group:
      self.row_converter.obj.task_group = None
    super(TaskDateColumnHandler, self).add_error(template, **kwargs)

  def parse_item(self):
    """ parse start and end columns fow workflow tasks
    """
    if not self.raw_value.strip():
      if self.row_converter.is_new:
        self.add_error(errors.MISSING_VALUE_ERROR,
                       column_name=self.display_name)
      return None
    raw_parts = self.raw_value.lower().split(" ")
    try:
      if len(raw_parts) == 2:
        quarter_name, day = raw_parts
        for month, quarter in self.quarterly_names.items():
          if quarter.lower() == quarter_name:
            return [month, int(day)]
      raw_parts = self.raw_value.split("/")
      return map(int, raw_parts)
    except ValueError:
      self.add_error(errors.WRONG_VALUE_ERROR,
                     column_name=self.display_name)
      return None

  def get_value(self):
    freq = self.row_converter.obj.task_group.workflow.frequency
    date = self._get_obj_attr("{}_date")
    day = self._get_obj_attr("relative_{}_day")
    month = self._get_obj_attr("relative_{}_month")
    if freq == "one_time":
      return "" if date is None else "{}/{}/{}".format(
          date.month,
          date.day,
          date.year
      )
    elif freq in ["weekly", "monthly"]:
      return "" if day is None else str(day)
    elif freq == "quarterly":
      quarter = self.quarterly_names.get(month, None)
      return "" if None in [day, quarter] else "{} {}".format(quarter, day)
    elif freq == "annually":
      return "" if None in [day, month] else "{}/{}".format(month, day)
    else:
      return ""

  def set_obj_attr(self):
    if not self.value or self.row_converter.ignore:
      return
    freq = self.row_converter.obj.task_group.workflow.frequency
    handler_map = {
        "one_time": (
            lambda v: v,
            lambda v: len(v) == 3,
            self._set_obj_date,
        ),
        "weekly": (
            lambda v: v,
            lambda v: len(v) == 1 and 1 <= v[0] <= 5,
            self._set_obj_relative_day,
        ),
        "monthly": (
            lambda v: v,
            lambda v: len(v) == 1 and 1 <= v[0] <= 31,
            self._set_obj_relative_day,
        ),
        "quarterly": (
            self._prepare_month_day,
            lambda v: len(v) == 2 and 1 <= v[0] <= 3 and 1 <= v[1] <= 31,
            self._set_obj_relative_month_day,
        ),
        "annually": (
            self._prepare_month_day,
            lambda v: len(v) == 2 and 1 <= v[0] <= 12 and 1 <= v[1] <= 31,
            self._set_obj_relative_month_day,
        ),
    }
    prepare, validate, set_obj_attr = handler_map[freq]
    self.value = prepare(self.value)
    if not validate(self.value):
      self.add_error(errors.WRONG_VALUE_ERROR, column_name=self.display_name)
    set_obj_attr(self.value)

  def _prepare_month_day(self, value):
    if len(value) == 3:
      self.add_warning(errors.WRONG_DATE_FORMAT, column_name=self.display_name)
      value = value[:2]
    return value

  def _set_obj_date(self, value):
    month, day, year = value
    try:
      self._set_obj_attr("{}_date", datetime.date(year, month, day))
    except ValueError as error:
      if error.message == "Start date can not be after end date.":
        self.add_error(errors.INVALID_START_END_DATES,
                       start_date="Start date",
                       end_date="End date")
      else:
        self.add_error(errors.WRONG_VALUE_ERROR, column_name=self.display_name)

  def _set_obj_relative_day(self, value):
    self._set_obj_attr("relative_{}_day", value[0])

  def _set_obj_relative_month_day(self, value):
    self._set_obj_attr("relative_{}_month", value[0])
    self._set_obj_attr("relative_{}_day", value[1])

  def _obj_attr_name(self, template):
    key = "start" if "start" in self.key else "end"
    return template.format(key)

  def _get_obj_attr(self, attr):
    return getattr(self.row_converter.obj, self._obj_attr_name(attr), None)

  def _set_obj_attr(self, attr, value):
    setattr(self.row_converter.obj, self._obj_attr_name(attr), value)


class TaskTypeColumnHandler(handlers.ColumnHandler):

  """Handler for task type column in task group tasks."""

  type_map = {
      "rich text": "text",
      "dropdown": "menu",
      "drop down": "menu",
      "checkboxes": "checkbox",
      "checkbox": "checkbox",
  }

  reverse_map = {
      "text": "rich text",
      "menu": "dropdown",
      "checkbox": "checkbox"
  }

  def parse_item(self):
    """Parse task type column value."""
    value = self.type_map.get(self.raw_value.lower())
    if value is None:
      if self.raw_value.lower() in self.type_map.values():
        value = self.raw_value.lower()
    if value is None:
      value = self.row_converter.obj.default_task_type()
      default_value = self.reverse_map.get(value).title()
      if self.raw_value:
        self.add_warning(errors.WRONG_REQUIRED_VALUE,
                         value=self.raw_value,
                         column_name=self.display_name)
      else:
        self.add_warning(errors.MISSING_VALUE_WARNING,
                         default_value=default_value,
                         column_name=self.display_name)
    return value

  def get_value(self):
    """Get titled user readable value for taks type."""
    return self.reverse_map.get(self.row_converter.obj.task_type,
                                "rich text").title()


class WorkflowPersonColumnHandler(handlers.UserColumnHandler):

  def parse_item(self):
    return self.get_users_list()

  def set_obj_attr(self):
    pass

  def get_value(self):
    workflow_person = db.session.query(wf_models.WorkflowPerson.person_id)\
        .filter_by(workflow_id=self.row_converter.obj.id,)
    workflow_roles = db.session.query(bp_models.UserRole.person_id)\
        .filter_by(context_id=self.row_converter.obj.context_id)
    users = models.Person.query.filter(
        models.Person.id.in_(workflow_person) &
        models.Person.id.notin_(workflow_roles)
    )
    emails = [user.email for user in users]
    return "\n".join(emails)

  def remove_current_people(self):
    wf_models.WorkflowPerson.query.filter_by(
        workflow_id=self.row_converter.obj.id).delete()

  def insert_object(self):
    if self.dry_run or not self.value:
      return
    self.remove_current_people()
    for owner in self.value:
      workflow_person = wf_models.WorkflowPerson(
          workflow=self.row_converter.obj,
          person=owner,
          context=self.row_converter.obj.context
      )
      db.session.add(workflow_person)
    self.dry_run = True


class ObjectsColumnHandler(multi_object.ObjectsColumnHandler):

  def get_value(self):
    task_group_objects = wf_models.TaskGroupObject.query.filter_by(
        task_group_id=self.row_converter.obj.id).all()
    lines = ["{}: {}".format(t.object._inflector.title_singular.title(),
                             t.object.slug)
             for t in task_group_objects if t.object is not None]
    return "\n".join(lines)

  def insert_object(self):
    obj = self.row_converter.obj
    existing = set((t.object_type, t.object_id)
                   for t in obj.task_group_objects)
    for object_ in self.value:
      if (object_.type, object_.id) in existing:
        continue
      tgo = wf_models.TaskGroupObject(
          task_group=obj,
          object=object_,
          context=obj.context,
      )
      db.session.add(tgo)
    db.session.flush()


class CycleWorkflowColumnHandler(handlers.ExportOnlyColumnHandler):

  def get_value(self):
    return self.row_converter.obj.workflow.slug


class CycleColumnHandler(handlers.ExportOnlyColumnHandler):

  def get_value(self):
    return self.row_converter.obj.cycle.slug


class TaskDescriptionColumnHandler(handlers.TextareaColumnHandler):

  def set_obj_attr(self):
    """ Set task attribute based on task type """
    if not self.value or self.row_converter.ignore:
      return
    if self.row_converter.obj.task_type == "text":
      self.row_converter.obj.description = self.value
    else:
      options = [v.strip() for v in self.value.split(",")]
      self.row_converter.obj.response_options = options

  def get_value(self):
    if self.row_converter.obj.task_type == "text":
      return self.row_converter.obj.description
    else:
      return ", ".join(self.row_converter.obj.response_options)


COLUMN_HANDLERS = {
    "cycle": CycleColumnHandler,
    "cycle_task_group": CycleTaskGroupColumnHandler,
    "cycle_workflow": CycleWorkflowColumnHandler,
    "frequency": FrequencyColumnHandler,
    "notify_on_change": boolean.CheckboxColumnHandler,
    "relative_end_date": TaskDateColumnHandler,
    "relative_start_date": TaskDateColumnHandler,
    "task_description": TaskDescriptionColumnHandler,
    "task_group": TaskGroupColumnHandler,
    "task_group_objects": ObjectsColumnHandler,
    "task_type": TaskTypeColumnHandler,
    "workflow": WorkflowColumnHandler,
    "finished_date": handlers.DateColumnHandler,
    "verified_date": handlers.DateColumnHandler,
}
