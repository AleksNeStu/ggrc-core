# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

import flask

from flask import Blueprint

from ggrc import db             # noqa
from ggrc import settings       # noqa
from ggrc.app import app        # noqa
from ggrc.models import Audit
from ggrc.models import Control
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

from oauth2client import client


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
Control.__bases__ = (Folderable,) + Control.__bases__
Control.late_init_folderable()
Document.__bases__ = (Fileable,) + Document.__bases__
Document.late_init_fileable()
Meeting.__bases__ = (Eventable,) + Meeting.__bases__
Meeting.late_init_eventable()
# TODO: now the Gdrive module is dependant on the Workflows module. it used to
# be the other way around but none of them are actually okay
Workflow.__bases__ = (Folderable,) + Workflow.__bases__
Workflow.late_init_folderable()


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


def get_credentials():
  """Gets valid user credentials from storage.

  If nothing has been stored, or if the stored credentials are invalid,
  the OAuth2 flow is completed to obtain the new credentials.

  Returns:
      Credentials, the obtained credential.
  """
  credentials = client.OAuth2Credentials.from_json(
      flask.session['credentials'])
  return credentials


def verify_credentials():
  """Verify credentials to gdrive for the current user"""
  if 'credentials' not in flask.session:
    return flask.redirect(flask.url_for('authorize_app', _external=True))
  credentials = client.OAuth2Credentials.from_json(
      flask.session['credentials'])
  if credentials.access_token_expired:
    return flask.redirect(flask.url_for('authorize_app', _external=True))
  return None


@app.route("/authorize")
def authorize_app():
  """Redirect to Google API auth page to authorize"""
  constructor_kwargs = {
      'redirect_uri': flask.url_for('authorize_app', _external=True),
      'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
      'token_uri': 'https://accounts.google.com/o/oauth2/token',
  }
  flow = client.OAuth2WebServerFlow(
      settings.GAPI_CLIENT_ID,
      settings.GAPI_CLIENT_SECRET,
      scope='https://www.googleapis.com/auth/drive',
      **constructor_kwargs)
  if 'code' not in flask.request.args:
    auth_uri = flow.step1_get_authorize_url()
    return flask.redirect(auth_uri)
  else:
    auth_code = flask.request.args.get('code')
    credentials = flow.step2_exchange(auth_code)
  # store credentials
  flask.session['credentials'] = credentials.to_json()
  return flask.redirect(flask.url_for('export_view', _external=True))
