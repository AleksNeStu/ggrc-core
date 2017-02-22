# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

from flask import Blueprint

from ggrc.services.registry import service
from ggrc.models import all_models
from ggrc_basic_permissions.contributed_roles import RoleContributions
from ggrc_risks.converters import IMPORTABLE
import ggrc_risks.models as models
from ggrc_risks import utils
import ggrc_risks.views

# Initialize signal handler for status changes
from blinker import Namespace
signals = Namespace()
status_change = signals.signal(
    'Status Changed',
    """
    This is used to signal any listeners of any changes in model object status
    attribute
    """)

# Initialize Flask Blueprint for extension
blueprint = Blueprint(
    'ggrc_risks',
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/static/ggrc_risks',
)


_risk_object_types = [
    "Program",
    "Regulation", "Standard", "Policy", "Contract",
    "Objective", "Control", "Section", "Clause",
    "System", "Process",
    "DataAsset", "Facility", "Market", "Product", "Project"
]

for type_ in _risk_object_types:
  model = getattr(all_models, type_)
  model.__bases__ = (
      models.risk_object.Riskable,
  ) + model.__bases__
  model.late_init_riskable()


def get_public_config(current_user):
  """Expose additional permissions-dependent config to client.
  """
  return {}


def contributed_services():
  return [
      service('risks', models.Risk),
      service('risk_objects', models.RiskObject),
      service('threats', models.Threat),
  ]


def contributed_object_views():
  from . import models
  from ggrc.views.registry import object_view
  return [
      object_view(models.Risk),
      object_view(models.Threat),
  ]


# Initialize non-RESTful views
def init_extra_views(app):
  ggrc_risks.views.init_extra_views(app)


class RiskRoleContributions(RoleContributions):
  contributions = {
      'Creator': {
          'read': [],
          'create': ['Threat', 'Risk'],
      },
      'Editor': {
          'read': ['Threat', 'Risk'],
          'create': ['Threat', 'Risk'],
      },
      'Reader': {
          'read': ['Threat', 'Risk'],
          'create': ['Threat', 'Risk'],
      },
  }

ROLE_CONTRIBUTIONS = RiskRoleContributions()

contributed_importables = IMPORTABLE
MAPPING_VALIDATION_WHITELIST = [utils.get_mapping_validation_rules()]
