# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

import factory
from datetime import date


from ggrc_workflows import models
from integration.ggrc.models.factories import ModelFactory
from integration.ggrc.models.factories import TitledFactory


class WorkflowFactory(TitledFactory):

  class Meta:
    model = models.Workflow

  frequency = "one_time"


class TaskGroupFactory(TitledFactory):

  class Meta:
    model = models.TaskGroup

  workflow = factory.SubFactory(WorkflowFactory)


class TaskGroupObjectFactory(ModelFactory):

  class Meta:
    model = models.TaskGroupObject

  task_group = factory.SubFactory(TaskGroupFactory)
  object_id = 0
  object_type = ""


class TaskGroupTaskFactory(TitledFactory):

  class Meta:
    model = models.TaskGroupTask

  task_group = factory.SubFactory(TaskGroupFactory)
  task_type = "text"


class CycleFactory(TitledFactory):

  class Meta:
    model = models.Cycle

  workflow = factory.SubFactory(WorkflowFactory)


class CycleTaskGroupFactory(TitledFactory):

  class Meta:
    model = models.CycleTaskGroup

  cycle = factory.SubFactory(CycleFactory)


class CycleTaskFactory(TitledFactory):

  class Meta:
    model = models.CycleTaskGroupObjectTask

  cycle = factory.SubFactory(CycleFactory)
  cycle_task_group = factory.SubFactory(CycleTaskGroupFactory)
  task_group_task = factory.SubFactory(TaskGroupTaskFactory)
  status = "Assigned"
  task_type = "text"
  start_date = date(2015, 12, 4)
  end_date = date(2015, 12, 27)
