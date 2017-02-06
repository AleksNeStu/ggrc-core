#!/usr/bin/env bash

APPENGINE_INSTANCE=local
SETTINGS_MODULE="development app_engine ggrc_basic_permissions.settings.development ggrc_risks.settings.development ggrc_risk_assessments.settings.development ggrc_workflows.settings.development"
DATABASE_URI="mysql+mysqldb://root:root@${GGRC_DATABASE_HOST:-localhost}/ggrcdev?charset=utf8"
SECRET_KEY='Something-secret'
GOOGLE_ANALYTICS_ID=""
GOOGLE_ANALYTICS_DOMAIN=""
GAPI_KEY='<Google Browser Key>'
GAPI_CLIENT_ID='<Google OAuth Client ID>'
GAPI_CLIENT_SECRET='<Google OAuth Client Secret>'
GAPI_ADMIN_GROUP='<Google Group Email Address>'
BOOTSTRAP_ADMIN_USERS='user@example.com'
MIGRATOR='Default Migrator <migrator@example.com>'
RISK_ASSESSMENT_URL='http://localhost:8080'
CUSTOM_URL_ROOT=''
ABOUT_URL='#'
ABOUT_TEXT='About GGRC'
EXTERNAL_HELP_URL='#set_GGRC_EXTERNAL_HELP_URL_env_var'
INSTANCE_CLASS='B4'
MAX_INSTANCES='4'
