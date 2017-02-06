# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

import os
import jinja2

DEBUG = False
TESTING = False
PRODUCTION = False
GOOGLE_INTERNAL = False

# Flask-SQLAlchemy fix to be less than `wait_time` in /etc/mysql/my.cnf
SQLALCHEMY_POOL_RECYCLE = 120

# Settings in app.py
AUTOBUILD_ASSETS = False
ENABLE_JASMINE = False
DEBUG_ASSETS = False
FULLTEXT_INDEXER = None
USER_PERMISSIONS_PROVIDER = None
EXTENSIONS = []
exports = []

# Deployment-specific variables
COMPANY = "Company, Inc."
COMPANY_LOGO = "/static/images/ggrc-logo.png"
COMPANY_LOGO_TEXT = "Company GRC"
COPYRIGHT = u"Confidential. Copyright \u00A9"  # \u00A9 is the (c) symbol

# Construct build number
BUILD_NUMBER = ""
try:
  import build_number
  BUILD_NUMBER = " ({0})".format(build_number.BUILD_NUMBER[:7])
except (ImportError):
  pass

VERSION = "0.10.2-Raspberry" + BUILD_NUMBER

# Migration owner
MIGRATOR = os.environ.get(
    'GGRC_MIGRATOR',
    'Default Migrator <migrator@example.com>',
)

# Google Analytics variables
GOOGLE_ANALYTICS_ID = os.environ.get('GGRC_GOOGLE_ANALYTICS_ID', '')
GOOGLE_ANALYTICS_DOMAIN = os.environ.get('GGRC_GOOGLE_ANALYTICS_DOMAIN', '')

ANALYTICS_TEMPLATE = """
<script type="text/javascript">
(function (i,s,o,g,r,a,m) {i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
(i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
})(window,document,'script','https://www.google-analytics.com/analytics.js','ga');

ga('create', '%s', 'auto');
ga('send', 'pageview');
</script>
"""

if GOOGLE_ANALYTICS_ID:
  GOOGLE_ANALYTICS_SCRIPT = ANALYTICS_TEMPLATE % GOOGLE_ANALYTICS_ID
else:
  GOOGLE_ANALYTICS_SCRIPT = ""

# Initialize from environment if present
SQLALCHEMY_DATABASE_URI = os.environ.get('GGRC_DATABASE_URI', '')
SECRET_KEY = os.environ.get('GGRC_SECRET_KEY', 'Replace-with-something-secret')

MEMCACHE_MECHANISM = True

# AppEngine Email
APPENGINE_EMAIL = os.environ.get('APPENGINE_EMAIL', '')

CALENDAR_MECHANISM = False

MAX_INSTANCES = os.environ.get('MAX_INSTANCES', '3')

exports = ['VERSION', 'MAX_INSTANCES']

# Users with authorized domains will automatically get Creator role.
# After parsing, AUTHORIZED_DOMAINS must be set of strings.
AUTHORIZED_DOMAINS = {
    d.strip() for d in os.environ.get('AUTHORIZED_DOMAINS', "").split(",")}

JINJA2 = jinja2.Environment(loader=jinja2.PackageLoader('ggrc', 'templates'))
EMAIL_DIGEST = JINJA2.get_template("notifications/email_digest.html")
EMAIL_DAILY = JINJA2.get_template("notifications/view_daily_digest.html")
EMAIL_PENDING = JINJA2.get_template("notifications/view_pending_digest.html")

USE_APP_ENGINE_ASSETS_SUBDOMAIN = False

BACKGROUND_COLLECTION_POST_SLEEP = 0


LOGGING_HANDLER = {
    "class": "logging.StreamHandler",
    "stream": "ext://sys.stdout",
    "formatter": "default",
}
LOGGING_FORMATTER = {
    "format": "%(levelname)-8s %(asctime)s %(name)s %(message)s",
}
LOGGING_ROOT = "WARNING"
LOGGING_LOGGERS = {
    "ggrc": "INFO",

    "sqlalchemy": "WARNING",
    # WARNING - logs warnings and errors only
    # INFO    - logs SQL-queries
    # DEBUG   - logs SQL-queries + result sets

    "werkzeug": "INFO",
    # WARNING - logs warnings and errors only
    # INFO    - logs HTTP-queries
}


DEBUG_BENCHMARK = os.environ.get("GGRC_BENCHMARK")
