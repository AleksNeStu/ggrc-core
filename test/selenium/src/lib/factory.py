# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"Factory for modules, classes, methods, functions."
from lib import base, cache, constants, exception
from lib.constants import objects, element, locator
from lib.element import tree_view, widget_info, tree_view_item


def _filter_out_underscore(object_name):
  """Since class names don't allow underscore in names, we're parsing them
 out"""
  return object_name if "_" not in object_name \
      else object_name.replace("_", "")


def _all_subclasses(cls):
  """Return all subclassses for parent"""
  return cls.__subclasses__() + \
      [g for s in cls.__subclasses__() for g in _all_subclasses(s)]


def _factory(cls_name, parent_cls, search_nested_subclasses=False):
  """Return subclass from parent
 Args:
    cls_name (basestring)
    parent_cls (cls)
    search_nested_subclasses (bool)
 Return:
    cls
 """
  member_cls = None
  subcls_name = _filter_out_underscore(cls_name.lower())
  members = _all_subclasses(parent_cls) \
      if search_nested_subclasses \
      else parent_cls.__subclasses__()
  for member_cls in members:
    if member_cls.__name__.lower() == subcls_name:
      break
  else:
    raise exception.NoClassFound(
        "%s for parent %s" % (subcls_name, parent_cls))
  return member_cls


def get_method_lhn_select(object_name):
  """Return method of LHN class
 Args:
    object_name (basestring)
 """
  return constants.method.SELECT_PREFIX \
      + cache.LHN_SECTION_MEMBERS[object_name]


def get_method_select(object_name):
  """Return method of LHN class
 Args:
    object_name (basestring)
 """
  return constants.method.SELECT_PREFIX + object_name


def get_fields_to_set(object_name):
  """Get and return of constant DEFAULT_SET_FIELDS (tuple of default visible
  fields to setup) from lib.constants.element module.
  """
  cls_name = objects.get_singular(object_name) + "ModalSetVisibleFields"
  base_cls = element.CommonModalSetVisibleFields
  set_fields_modal_cls = _factory(cls_name=cls_name, parent_cls=base_cls)
  return set_fields_modal_cls().DEFAULT_SET_FIELDS


def get_cls_test_utils(object_name):
  """Return test utils class based on object name
 Args:
    object_name (basestring)
 """
  cls_name = constants.cls_name.TEST_MODAL_NEW_PREFIX + object_name
  return _factory(cls_name=cls_name, parent_cls=base.TestUtil,
                  search_nested_subclasses=True)


def get_cls_widget(object_name, is_info=False, is_admin=False):
  """Get and return class of widget. If is_info is True then class
  info_widget.'obj_name', if is_admin is True then class
  admin_widget.'tab_element', else class generic_widget.'obj_name'.
  """
  from lib.page.widget import admin_widget, generic_widget, info_widget
  base_cls = None
  if is_info:
    if object_name not in objects.ALL_SNAPSHOTABLE_OBJS:
      base_cls = info_widget.InfoPanel
    elif object_name in objects.ALL_SNAPSHOTABLE_OBJS:
      base_cls = info_widget.SnapshotableInfoPanel
    elif object_name == objects.PEOPLE:
      base_cls = info_widget.base.Widget
  elif is_admin:
    base_cls = admin_widget.Widget
  else:
    base_cls = generic_widget.Widget
  return _factory(cls_name=object_name, parent_cls=base_cls)


def get_cls_locators_generic_widget(object_name):
  """Get and return class of locators for object generic widget."""
  cls_name = constants.cls_name.WIDGET + object_name
  base_cls = locator.BaseWidgetGeneric
  return _factory(cls_name=cls_name, parent_cls=base_cls)


def get_cls_entity_factory(object_name):
  """Get and return class of entity factory."""
  from lib.entities import entities_factory
  cls_name = object_name + constants.cls_name.FACTORY
  base_cls = entities_factory.EntitiesFactory
  return _factory(cls_name=cls_name, parent_cls=base_cls)


def get_cls_rest_service(object_name):
  """Get and return class of rest service."""
  from lib.service import rest_service
  cls_name = object_name + constants.cls_name.SERVICE
  base_cls = rest_service.BaseRestService
  return _factory(cls_name=cls_name, parent_cls=base_cls)


def get_cls_create_obj(object_name):
  """Get and return class of create object."""
  from lib.page.modal import create_new_object
  cls_name = object_name + constants.cls_name.CREATE
  base_cls = create_new_object.CreateNewObjectModal
  return _factory(cls_name=cls_name, parent_cls=base_cls)


def get_cls_3bbs_dropdown_settings(object_name, is_tree_view_not_info):
  """Get and return class of 3BBS dropdown settings for Tree View or
  Info widget (Info page or Info panel). As default for Info widget, if
  is_tree_view_not_info is True then for Tree View.
  """
  base_cls = widget_info.CommonInfoDropdownSettings
  if is_tree_view_not_info:
    base_cls = tree_view.CommonDropdownSettings
  return _factory(cls_name=object_name, parent_cls=base_cls)


def get_cls_dropdown_tree_view_item(object_name):
  """Get and return class of TreeViewItem Dropdown object according to
  snapshotability
  """
  base_cls = tree_view_item.CommonDropdownTreeViewItem
  if object_name in objects.ALL_SNAPSHOTABLE_OBJS:
    base_cls = tree_view_item.SnapshotsDropdownTreeViewItem
  return _factory(cls_name=object_name, parent_cls=base_cls)


def get_locator_widget(widget_name):
  """Return locator for widget tab in widget bar"""
  # todo: unittests
  return getattr(constants.locator.WidgetBar, widget_name.upper())


def get_locator_add_widget(widget_name):
  """Return locator for selected widget from add widget button
 dropdown in widget bar"""
  # todo: unittests
  return getattr(
      constants.locator.WidgetBarButtonAddDropdown, widget_name.upper())


def get_ui_service(object_name):
  """Get and return class of UI service according to name of object
  Returns:
    class of ui service by object_name
  """
  service_name = objects.get_plural(object_name, title=True)
  from lib.service import webui_service
  service_classname = service_name + constants.cls_name.SERVICE
  return getattr(webui_service, service_classname)
