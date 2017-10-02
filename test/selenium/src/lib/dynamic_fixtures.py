# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"Logical model of dynamic fixtures creation."
# pylint: disable=invalid-name
# pylint: disable=global-variable-not-assigned
# pylint: disable=global-statement
# pylint: disable=no-else-return

import copy

from lib import factory
from lib.constants import element, objects, counters
from lib.entities.entities_factory import CustomAttributeDefinitionsFactory
from lib.entities.entity import Entity
from lib.page.widget import info_widget
from lib.service import rest_service
from lib.utils import conftest_utils, test_utils, string_utils

dict_executed_fixtures = {}


def _get_fixture_from_dict_fixtures(fixture):
  """Get value of fixture by key (fixture name) from dictionary of
  executed fixtures."""
  global dict_executed_fixtures
  # extend executed fixtures using exist fixture in snapshot representation
  if fixture.endswith("_snapshot"):
    origin_obj = _get_fixture_from_dict_fixtures(
        fixture.replace("_snapshot", ""))
    parent_obj = _get_fixture_from_dict_fixtures("new_audit_rest")[0]
    dict_executed_fixtures.update(
        {fixture: Entity.convert_objs_repr_to_snapshot(
            obj_or_objs=origin_obj, parent_obj=parent_obj)})
  return {k: v for k, v in dict_executed_fixtures.iteritems()
          if k == fixture}[fixture]


def _new_objs_rest(obj_name, obj_count,  # noqa: ignore=C901
                   has_cas=False, factory_params=None):
  """Create new objects via REST API according to object name (plural form),
  objects count and requirements for presence of Custom Attributes.
  Return: [lib.entities.entity.*Entity, ...]
  """
  # pylint: disable=unused-argument
  global dict_executed_fixtures
  _list_cas_types = element.AdminWidgetCustomAttributes.ALL_CA_TYPES

  def create_objs_rest(name, count, factory_params):
    """Create new objects via REST API according to object name (plural form)
    and objects count.
    Return: [lib.entities.entity.*Entity, ...]
    """
    return factory.get_cls_rest_service(
        object_name=name)().create_objs(count=count,
                                        factory_params=factory_params)

  def create_objs_rest_used_exta_arrts(name, extra_attrs, factory_params):
    """Create new objects via REST API according to object name (plural form)
    and list extra attributes.
    Return: [lib.entities.entity.*Entity, ...]
    """
    if extra_attrs[0].type == objects.get_singular(objects.CUSTOM_ATTRIBUTES):
      if name == objects.ASSESSMENT_TEMPLATES:
        return factory.get_cls_rest_service(object_name=name)().create_objs(
            count=1, factory_params=factory_params,
            custom_attribute_definitions=CustomAttributeDefinitionsFactory().
            generate_ca_defenitions_for_asmt_tmpls(
                list_ca_definitions=extra_attrs[:len(_list_cas_types)]),
            audit=extra_attrs[len(_list_cas_types):][0].__dict__)
      else:
        return factory.get_cls_rest_service(object_name=name)().create_objs(
            count=1, factory_params=factory_params,
            custom_attributes=CustomAttributeDefinitionsFactory().
            generate_ca_values(list_ca_def_objs=extra_attrs))
    else:
      return ([factory.get_cls_rest_service(object_name=name)().
              create_objs(count=1, factory_params=factory_params,
                          **{parent_obj.type.lower(): parent_obj.__dict__})[0]
               for parent_obj in extra_attrs])

  parent_obj_name = None
  if obj_name == objects.AUDITS:
    parent_obj_name = (objects.get_singular(objects.PROGRAMS) if obj_count == 1
                       else objects.PROGRAMS)
  if obj_name in (objects.ASSESSMENT_TEMPLATES, objects.ASSESSMENTS):
    parent_obj_name = objects.get_singular(objects.AUDITS)
  if (has_cas and obj_name in objects.ALL_OBJS and
          obj_name not in objects.ASSESSMENT_TEMPLATES):
    parent_obj_name = "cas_for_" + obj_name
  if parent_obj_name:
    parent_objs = _get_fixture_from_dict_fixtures(
        fixture="new_{}_rest".format(parent_obj_name))
    if "new_{}_rest".format(parent_obj_name) == "new_audit_rest":
      parent_objs *= obj_count
    if has_cas and obj_name in objects.ASSESSMENT_TEMPLATES:
      parent_objs = (
          [CustomAttributeDefinitionsFactory().create(
              attribute_type=ca_type, definition_type="") for
              ca_type in _list_cas_types] + parent_objs)
    objs = create_objs_rest_used_exta_arrts(
        name=obj_name, factory_params=factory_params, extra_attrs=parent_objs)
  else:
    objs = create_objs_rest(
        name=obj_name, count=obj_count, factory_params=factory_params)
  return objs


def generate_common_fixtures(*fixtures):  # noqa: ignore=C901
  """Generate, run and return of results for common dynamic fixtures according
  to tuple of fixtures names and used if exist 'web_driver' fixture for UI.
  Examples: fixtures = ('new_program_rest', 'new_controls_rest',
  'map_new_program_rest_to_new_controls_rest', 'new_audit_rest',
  'new_cas_for_controls').
  """
  global dict_executed_fixtures
  _list_cas_types = element.AdminWidgetCustomAttributes.ALL_CA_TYPES

  def new_rest_fixture(fixture, factory_params=None):
    """Extract arguments of 'new_rest_fixture' fixture from fixture name,
    create new objects via REST API and return created.
    """
    if "new_cas_for_" in fixture:
      fixture_params = fixture.replace("new_cas_for_", "").replace("_rest", "")
      obj_name = objects.CUSTOM_ATTRIBUTES
      factory_cas_for_objs = [CustomAttributeDefinitionsFactory().create(
          attribute_type=ca_type,
          definition_type=objects.get_singular(fixture_params))
          for ca_type in _list_cas_types]
      new_objs = [
          _new_objs_rest(obj_name=obj_name, obj_count=1, factory_params=dict(
              attribute_type=ca.attribute_type,
              definition_type=ca.definition_type,
              multi_choice_options=ca.multi_choice_options))[0]
          for ca in factory_cas_for_objs]
    else:
      fixture_params = fixture.replace("new_", "").replace("_rest", "")
      has_cas = False
      if "_with_cas" in fixture_params:
        has_cas = True
        fixture_params = fixture_params.replace("_with_cas", "")
      obj_name = fixture_params
      obj_count = counters.BATCH_COUNT
      if objects.get_plural(obj_name) in objects.ALL_OBJS:
        obj_name = objects.get_plural(obj_name)
        obj_count = 1
      new_objs = _new_objs_rest(obj_name=obj_name, obj_count=obj_count,
                                has_cas=has_cas, factory_params=factory_params)
    return new_objs

  def new_ui_fixture(web_driver, fixture):
    """Extract arguments of 'new_ui_fixture' fixture from fixture name,
    create new objects via UI (LHN) and return UI page object.
    """
    fixture_params = fixture.replace("new_", "").replace("_ui", "")
    obj_name = fixture_params
    obj_count = counters.BATCH_COUNT
    if (objects.get_plural(obj_name) in objects.ALL_OBJS and
            objects.get_plural(obj_name) != objects.PROGRAMS):
      obj_name = objects.get_plural(obj_name)
      obj_count = 1
      objs_info_pages = [conftest_utils.create_obj_via_lhn(
          web_driver,
          getattr(element.Lhn, obj_name.upper())) for _ in xrange(obj_count)]
      return objs_info_pages
    elif objects.get_plural(obj_name) == objects.PROGRAMS:
      modal = conftest_utils.get_lhn_accordion(
          web_driver,
          getattr(element.Lhn, objects.PROGRAMS.upper())).create_new()
      test_utils.ModalNewPrograms.enter_test_data(modal)
      modal.save_and_close()
      program_info_page = info_widget.Programs(web_driver)
      return modal, program_info_page

  def map_rest_fixture(fixture):
    """Extract arguments of 'map_rest_fixture' fixture from fixture name,
    find previously created source and destination objects,
    map them via REST API and return result of mapping.
    """
    fixture_params = fixture.replace("map_", "")
    _src_obj, _dest_objs = fixture_params.split("_to_")
    src_obj = _get_fixture_from_dict_fixtures(fixture=_src_obj)[0]
    dest_objs = _get_fixture_from_dict_fixtures(fixture=_dest_objs)
    mapped_objs = rest_service.RelationshipsService().map_objs(
        src_obj=src_obj, dest_objs=dest_objs)
    return mapped_objs

  def update_rest_fixture(fixture, factory_params=None):
    """Extract arguments of 'update_rest_fixture' fixture from fixture name,
    update existing objects via REST API and return updated.
    """
    parent_objs = None
    has_cas = False
    obj_name = fixture.replace("update_", "").replace("_rest", "")
    _objs_to_update = "new_{}_rest".format(obj_name)
    # e.g. need if: 'new_controls_rest' and 'update_control_rest'
    try:
      objs_to_update = _get_fixture_from_dict_fixtures(fixture=_objs_to_update)
    except KeyError:
      _objs_to_update = "new_{}_rest".format(objects.get_plural(obj_name))
      objs_to_update = _get_fixture_from_dict_fixtures(
          fixture=_objs_to_update)[0]
    if objects.get_plural(obj_name) in objects.ALL_OBJS:
      obj_name = objects.get_plural(obj_name)
    if "_with_cas" in obj_name:
      has_cas = True
      obj_name = objects.get_plural(obj_name.replace("_with_cas", ""))
      parent_objs = _get_fixture_from_dict_fixtures(
          fixture="new_{}_rest".format("cas_for_" + obj_name))
    if objs_to_update:
      if has_cas and parent_objs:
        updated_objs = (
            factory.get_cls_rest_service(object_name=obj_name)().update_objs(
                objs=objs_to_update, factory_params=factory_params,
                custom_attributes=CustomAttributeDefinitionsFactory().
                generate_ca_values(list_ca_def_objs=parent_objs)))
      else:
        updated_objs = factory.get_cls_rest_service(
            object_name=obj_name)().update_objs(objs=objs_to_update,
                                                factory_params=factory_params)
      return updated_objs

  def delete_rest_fixture(fixture):
    """Extract arguments of 'delete_rest_fixture' fixture from fixture name,
    delete existing objects via REST API.
    """
    obj_name = fixture.replace("delete_", "").replace("_rest", "")
    _objs_to_delete = "new_{}_rest".format(obj_name)
    # e.g. need if: 'new_controls_rest' and 'delete_control_rest'
    try:
      objs_to_delete = _get_fixture_from_dict_fixtures(fixture=_objs_to_delete)
    except KeyError:
      _objs_to_delete = "new_{}_rest".format(objects.get_plural(obj_name))
      objs_to_delete = _get_fixture_from_dict_fixtures(
          fixture=_objs_to_delete)[0]
    if objects.get_plural(obj_name) in objects.ALL_OBJS:
      obj_name = objects.get_plural(obj_name)
    if "_with_cas" in obj_name:
      obj_name = objects.get_plural(obj_name.replace("_with_cas", ""))
    if "cas_for_" in obj_name:
      obj_name = objects.CUSTOM_ATTRIBUTES
    if objs_to_delete:
      deleted_objs = factory.get_cls_rest_service(
          object_name=obj_name)().delete_objs(objs=objs_to_delete)
      return deleted_objs

  for fixture in fixtures:
    fixture_params = None
    if isinstance(fixture, tuple):
      fixture, fixture_params = fixture
    if isinstance(fixture, str):
      if (fixture.startswith("new_") and fixture.endswith("_ui") and
              dict_executed_fixtures.get("selenium")):
        new_objs = new_ui_fixture(
            web_driver=dict_executed_fixtures["selenium"], fixture=fixture)
        dict_executed_fixtures.update({fixture: new_objs})
      elif fixture.endswith(("_rest", "_snapshot")):
        if fixture.startswith("new_"):
          new_objs = new_rest_fixture(fixture=fixture,
                                      factory_params=fixture_params)
          dict_executed_fixtures.update({fixture: new_objs})
        elif fixture.startswith("map_") and "_to_" in fixture:
          mapped_objs = map_rest_fixture(fixture=fixture)
          dict_executed_fixtures.update({fixture: mapped_objs})
        elif fixture.startswith("update_"):
          updated_objs = update_rest_fixture(fixture=fixture,
                                             factory_params=fixture_params)
          dict_executed_fixtures.update({fixture: updated_objs})
        elif fixture.startswith("delete_"):
          deleted_objs = delete_rest_fixture(fixture=fixture)
          dict_executed_fixtures.update({fixture: deleted_objs})
  executed_fixtures_copy = (copy.deepcopy(dict_executed_fixtures) if
                            not dict_executed_fixtures.get("selenium") else
                            copy.copy(dict_executed_fixtures))
  return executed_fixtures_copy


def generate_snapshots_fixtures(fixture):
  """Generate, run and return of results for snapshots dynamic fixtures
  according to tuple of fixture name.
  Example: 'create_audit_with_control__risk_and_update_control'
           'create_audit_with_controls'
           'create_audit_with_controls_and_update_control'
           'create_audit_with_control__risk_and_update_control__risk
  """
  global dict_executed_fixtures
  if isinstance(fixture, str) and fixture.startswith("create_audit_with_"):
    _creation_params = None
    _action_params = None
    updating_params = []
    deleting_params = []
    fixture_params = fixture.replace("create_audit_with_", "")
    if "_and_" in fixture_params:
      _creation_params, _action_params = fixture_params.split("_and_")
    if "_and_" not in fixture_params:
      _creation_params = fixture_params
    creation_params = string_utils.convert_list_elements_to_list([
        "new_{}_rest".format(param) if "_with_cas" not in param else
        ["new_cas_for_{}_rest".format(objects.get_plural(param.split("_")[0])),
         "new_{}_rest".format(param)]
        for param in _creation_params.split("__")])
    mapping_params = [
        "map_new_program_rest_to_new_{}_rest".format(param) for param in
        _creation_params.split("__")]
    creation_part = (["new_program_rest"] + creation_params +
                     mapping_params + ["new_audit_rest"])
    if _action_params:
      if "update" in _action_params:
        updating_params = ["update_{}_rest".format(param) for param in
                           _action_params.replace("update_", "").split("__")]
      if "delete" in _action_params:
        deleting_params = ["delete_{}_rest".format(param) for param in
                           _action_params.replace("delete_", "").split("__")]
    action_part = (updating_params + deleting_params)
    all_manipulations = creation_part + action_part
    generate_common_fixtures(*all_manipulations)
    executed_snapshots_fixtures = copy.deepcopy(dict_executed_fixtures)
    return executed_snapshots_fixtures
