# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

import inspect
import sqlalchemy as sa

from ggrc import db
from ggrc import settings
from ggrc.models import inflector
from ggrc.models.reflection import SanitizeHtmlInfo
from ggrc.models.all_models import *  # noqa
from ggrc.utils import html_cleaner

"""All GGRC model objects and associated utilities."""


def create_db_with_create_all():
  import ggrc.models.all_models  # noqa

  db.create_all()


def create_db_with_migrations(quiet=False):
  from ggrc.migrate import upgradeall
  import logging

  if quiet:
    logging.disable(logging.INFO)
  upgradeall()

  if quiet:
    logging.disable(logging.NOTSET)


def drop_db_with_drop_all():
  import ggrc.models.all_models  # noqa

  if 'mysql' in settings.SQLALCHEMY_DATABASE_URI:
    db.engine.execute('SET FOREIGN_KEY_CHECKS = 0')

  db.drop_all()


def drop_db_with_migrations(quiet=False):
  from ggrc.migrate import downgradeall
  import ggrc.models.all_models  # noqa
  import logging

  if quiet:
    logging.disable(logging.INFO)
  if 'mysql' in settings.SQLALCHEMY_DATABASE_URI:
    db.engine.execute('SET FOREIGN_KEY_CHECKS = 0')
  downgradeall(drop_versions_table=True)
  if quiet:
    logging.disable(logging.NOTSET)
  if 'mysql' in settings.SQLALCHEMY_DATABASE_URI:
    db.engine.execute('SET FOREIGN_KEY_CHECKS = 1')


def create_db(use_migrations=False, quiet=False):
  if 'mysql' in settings.SQLALCHEMY_DATABASE_URI:
    db.engine.execute('SET FOREIGN_KEY_CHECKS = 0')

  if use_migrations:
    create_db_with_migrations(quiet)
  else:
    create_db_with_create_all()

  if 'mysql' in settings.SQLALCHEMY_DATABASE_URI:
    db.engine.execute('SET FOREIGN_KEY_CHECKS = 1')


def drop_db(use_migrations=False, quiet=False):
  if use_migrations:
    drop_db_with_migrations(quiet)
  else:
    drop_db_with_drop_all()


def init_models(app):
  from ggrc.models.all_models import all_models  # noqa
  for model in all_models:
    inflector.register_inflections(model._inflector)


def init_hooks():
  from ggrc.models import hooks
  hooks.init_hooks()


def init_all_models(app):
  """Register all GGRC models services with the Flask application ``app``."""

  from ggrc.extensions import get_extension_modules

  # Usually importing the module is enough, but just in case, also invoke
  # ``init_models``
  init_models(app)
  for extension_module in get_extension_modules():
    ext_init_models = getattr(extension_module, 'init_models', None)
    if ext_init_models:
      ext_init_models(app)
  init_hooks()


def init_lazy_mixins():
  """Lazy mixins initialisation

  Mixins with `__lazy__init__` property set to True will wait with their
  initialization until after the models have been fully initialized. This is
  useful in cases where we need full model class, e.g. to hook up signaling
  logic.
  """
  from ggrc.models import all_models
  for model in all_models.all_models:
    # MRO chain includes base model that we don't want to include here
    mixins = (mixin for mixin in inspect.getmro(model) if mixin != model)
    for mixin in mixins:
      if getattr(mixin, '__lazy_init__', False):
        mixin.init(model)


def init_session_monitor_cache():
  from sqlalchemy.orm.session import Session
  from sqlalchemy import event
  from ggrc.services.common import get_cache

  def update_cache_before_flush(session, flush_context, objects):
    cache = get_cache(create=True)
    if cache:
      cache.update_before_flush(session, flush_context)

  def update_cache_after_flush(session, flush_context):
    cache = get_cache(create=False)
    if cache:
      cache.update_after_flush(session, flush_context)

  def clear_cache(session):
    cache = get_cache()
    if cache:
      cache.clear()

  event.listen(Session, 'before_flush', update_cache_before_flush)
  event.listen(Session, 'after_flush', update_cache_after_flush)
  event.listen(Session, 'after_commit', clear_cache)
  event.listen(Session, 'after_rollback', clear_cache)


def init_sanitization_hooks():
  # Register event listener on all String and Text attributes to sanitize them.
  for model in all_models.all_models:  # noqa
    attr_info = SanitizeHtmlInfo(model)
    for attr_name in attr_info._sanitize_html:
      attr = getattr(model, attr_name)
      sa.event.listen(attr, 'set', html_cleaner.cleaner, retval=True)


def init_app(app):
  init_all_models(app)
  init_lazy_mixins()
  init_session_monitor_cache()
  init_sanitization_hooks()

from ggrc.models.inflector import get_model  # noqa
