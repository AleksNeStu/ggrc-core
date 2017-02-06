# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

from flask import Blueprint

from ggrc import db             # noqa
from ggrc import settings       # noqa
from ggrc.app import app        # noqa
from ggrc.models import Audit
from ggrc.models import Document
from ggrc.models import Meeting
from ggrc.models import Program
from ggrc.services.registry import service
from ggrc_basic_permissions.contributed_roles import RoleContributions
from ggrc_workflows.models import Workflow
import ggrc_gdrive_integration.models as models
from ggrc_gdrive_integration.models.object_folder import Folderable
from ggrc_gdrive_integration.models.object_file import Fileable
from ggrc_gdrive_integration.models.object_event import Eventable
import ggrc_gdrive_integration.views


blueprint = Blueprint(
    'gdrive',
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/static/ggrc_gdrive_integration',
)


Program.__bases__ = (Folderable,) + Program.__bases__
Program.late_init_folderable()
Audit.__bases__ = (Folderable,) + Audit.__bases__
Audit.late_init_folderable()
Document.__bases__ = (Fileable,) + Document.__bases__
Document.late_init_fileable()
Meeting.__bases__ = (Eventable,) + Meeting.__bases__
Meeting.late_init_eventable()
# TODO: now the Gdrive module is dependant on the Workflows module. it used to
# be the other way around but none of them are actually okay
Workflow.__bases__ = (Folderable,) + Workflow.__bases__
Workflow.late_init_folderable()

'''
Some other spitballs from Dan here:

Folderable.extend_class(Program)
class ExtendableMixin(object):
  _publish_attrs = [..]

  def extend_class(cls, target_cls):
    pass

class ProgramWithGDrive(registry.get_model("Program")):
  @declared_attr
  def object_folders(cls):
    pass

ggrc.services.registry["Program"] = ProgramWithGDrive
/api/blah
/api/ggrc_basic_permissions/Program

@Resource.model_get.connect_via(Program)
def augment_program(programs):
  for p in programs:
    p["object_folders"] =
'''


# Initialize views
def init_extra_views(application):
  ggrc_gdrive_integration.views.init_extra_views(application)


contributed_services = [
    service('object_folders', models.ObjectFolder),
    service('object_files', models.ObjectFile),
    service('object_events', models.ObjectEvent)
]


class GDriveRoleContributions(RoleContributions):
  contributions = {
      'Auditor': {
          'read': ['ObjectFolder', 'ObjectFile', 'ObjectEvent'],
      },
      'ProgramAuditEditor': {
          'read': ['ObjectFolder', 'ObjectFile', 'ObjectEvent'],
          'create': ['ObjectFolder', 'ObjectFile', 'ObjectEvent'],
          'update': ['ObjectFolder', 'ObjectFile', 'ObjectEvent'],
          'delete': ['ObjectFolder', 'ObjectFile', 'ObjectEvent'],
      },
      'ProgramAuditOwner': {
          'read': ['ObjectFolder', 'ObjectFile', 'ObjectEvent'],
          'create': ['ObjectFolder', 'ObjectFile', 'ObjectEvent'],
          'update': ['ObjectFolder', 'ObjectFile', 'ObjectEvent'],
          'delete': ['ObjectFolder', 'ObjectFile', 'ObjectEvent'],
      },
      'ProgramAuditReader': {
          'read': ['ObjectFolder', 'ObjectFile', 'ObjectEvent'],
          'create': ['ObjectFolder', 'ObjectFile', 'ObjectEvent'],
          'delete': ['ObjectFolder', 'ObjectFile', 'ObjectEvent'],
      },
      'ProgramOwner': {
          'read': ['ObjectFolder'],
          'create': ['ObjectFolder'],
          'update': ['ObjectFolder'],
          'delete': ['ObjectFolder'],
      },
      'Editor': {
          'read': ['ObjectFolder', 'ObjectFile', 'ObjectEvent'],
          'create': ['ObjectFolder', 'ObjectFile', 'ObjectEvent'],
          'update': ['ObjectFolder', 'ObjectFile', 'ObjectEvent'],
          'delete': ['ObjectFolder', 'ObjectFile', 'ObjectEvent'],
      },

  }

ROLE_CONTRIBUTIONS = GDriveRoleContributions()
