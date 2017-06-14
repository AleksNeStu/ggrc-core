# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Services for create and manipulate objects via UI."""

from lib import factory
from lib.constants import element, objects, url
from lib.entities.entities_factory import EntitiesFactory
from lib.page.widget.info_widget import SnapshotableInfoPanel
from lib.utils import selenium_utils, string_utils


class BaseWebUiService(object):
  """Base class for business layer's services objects."""
  # pylint: disable=too-many-instance-attributes
  # pylint: disable=too-many-public-methods
  def __init__(self, driver, obj_name):
    self.driver = driver
    self.obj_name = obj_name
    self.generic_widget_cls = factory.get_cls_widget(object_name=self.obj_name)
    self.info_widget_cls = factory.get_cls_widget(
        object_name=self.obj_name, is_info=True)
    self.entities_factory_cls = factory.get_cls_entity_factory(
        object_name=self.obj_name)
    # URLs
    self.url_mapped_objs = (
        "{src_obj_url}" + url.get_widget_name_of_mapped_objs(self.obj_name))
    self.url_obj_info_page = "{obj_url}" + url.Widget.INFO
    self._unified_mapper = None

  def create_list_objs(self, entity_factory, list_scopes):
    """Create and return list of objects used entity factory and UI data
    (list of scopes UI text elements {"header": "item", ...} remapped to
    list of dicts {"attr": "value", ...}).
    Return list of created objects.
    """
    list_factory_objs = [
        entity_factory.create_empty() for _ in xrange(len(list_scopes))]
    list_scopes_remapped = string_utils.remap_keys_for_list_dicts(
        dict_transformation_keys=self.ui_elements_to_obj_attrs(),
        list_dicts=list_scopes)
    return [
        EntitiesFactory.update_obj_attrs_values(
            obj=factory_obj, **scope_remapped) for
        scope_remapped, factory_obj in zip(list_scopes_remapped,
                                           list_factory_objs)]

  @staticmethod
  def ui_elements_to_obj_attrs():
    """Get transformation dictionary {"OLD KEY": "NEW KEY"}, where
    "OLD KEY" - UI elements correspond to "NEW KEY" - objects attributes.
    """
    fields = element.TransformationSetVisibleFields
    return {
        fields.TITLE.upper(): "title", fields.MANAGER.upper(): "manager",
        fields.CODE.upper(): "slug", fields.VERIFIED.upper(): "verified",
        fields.STATE.upper(): "status", fields.STATUS.upper(): "status",
        fields.LAST_UPDATED.upper(): "updated_at",
        fields.AUDIT_LEAD.upper(): "contact",
        fields.ADMIN.upper(): "owners", fields.CREATORS.upper(): "owners",
        fields.CAS_HEADERS.upper(): "custom_attribute_definitions",
        fields.CAS_VALUES.upper(): "custom_attribute_values",
        fields.MAPPED_OBJECTS.upper(): "objects_under_assessment"
    }

  def open_widget_of_mapped_objs(self, src_obj):
    """Navigate to generic widget URL of mapped objects according to URL of
    source object and return generic widget class of mapped objects.
    """
    generic_widget_url = self.url_mapped_objs.format(src_obj_url=src_obj.url)
    selenium_utils.open_url(self.driver, generic_widget_url)
    return self.generic_widget_cls(self.driver, self.obj_name)

  def open_info_page_of_obj(self, obj):
    """Navigate to info page URL of object according to URL of object and
    return info widget class of object.
    """
    info_page_url = self.url_obj_info_page.format(
        obj_url=obj.url)
    selenium_utils.open_url(self.driver, info_page_url)
    return self.info_widget_cls(self.driver)

  def open_info_panel_of_obj_by_id(self, src_obj, obj):
    """Navigate to info panel URL of object according to URL of source object
    and URL of mapped object used id of object,
    return info widget class of object.
    """
    info_panel_url = (
        self.url_mapped_objs.format(src_obj_url=src_obj.url) + "/" + obj.id)
    selenium_utils.open_url(self.driver, info_panel_url)
    obj_info_panel = self.info_widget_cls(self.driver)
    return obj_info_panel

  def open_info_panel_of_obj_by_title(self, src_obj, obj):
    """Navigate to info panel URL of object according to URL of source object
    and URL of mapped object return generic widget class of mapped objects.
    """
    objs_widget = self.open_widget_of_mapped_objs(src_obj)
    obj_info_panel = (objs_widget.tree_view.
                      select_member_by_title(title=obj.title))
    return obj_info_panel

  def get_list_objs_from_tree_view(self, src_obj):
    """Get and return list of objects from Tree View."""
    self.set_list_objs_scopes_representation_on_tree_view(src_obj)
    list_objs_scopes = self.get_list_objs_scopes_from_tree_view(src_obj)
    return self.create_list_objs(entity_factory=self.entities_factory_cls,
                                 list_scopes=list_objs_scopes)

  def get_list_objs_from_mapper(self, src_obj, dest_objs):
    """Get and return list of objects from Unified Mapper Tree View and
     list of MappingStatusAttrs - namedtuples for mapping representation."""
    self._set_list_objs_scopes_repr_on_mapper_tree_view(src_obj)
    list_objs_scopes, mapping_statuses = (
        self._search_objs_via_tree_view(src_obj, dest_objs))
    return self.create_list_objs(
        entity_factory=self.entities_factory_cls,
        list_scopes=list_objs_scopes), mapping_statuses

  def get_obj_from_info_page(self, obj):
    """Get and return object from Info page."""
    scope = self.get_scope_from_info_page(obj)
    return self.create_list_objs(
        entity_factory=self.entities_factory_cls, list_scopes=[scope])[0]

  def get_obj_from_info_panel(self, src_obj, obj, navigate_by_title=True):
    """Get and return object from Info panel navigate by object title
    as default or by object id if navigate_by_title is False.
    """
    scope = self.get_scope_from_info_panel(src_obj, obj, navigate_by_title)
    return self.create_list_objs(
        entity_factory=self.entities_factory_cls, list_scopes=[scope])[0]

  def create_obj_via_tree_view(self, src_obj, obj):
    """Open generic widget of mapped objects, open creation modal from
    Tree View, fill data according to object attributes and create new object.
    """
    objs_widget = self.open_widget_of_mapped_objs(src_obj)
    (objs_widget.tree_view.open_create().
     fill_minimal_data(title=obj.title, code=obj.slug).save_and_close())

  def _get_unified_mapper(self, src_obj):
    """Open generic widget of mapped objects, open unified mapper modal from
    Tree View.
    Return unified_mapper.MapObjectsModal"""
    if self._unified_mapper is None:
      self._unified_mapper = (self.open_widget_of_mapped_objs(src_obj)
                              .tree_view.open_map())
    return self._unified_mapper

  def map_objs_via_tree_view(self, src_obj, dest_objs):
    """Open generic widget of mapped objects, open unified mapper modal from
    Tree View, fill data according to destination objects, search by them
    titles and then map to source object.
    """
    dest_objs_titles = [dest_obj.title for dest_obj in dest_objs]
    dest_objs_widget = self.open_widget_of_mapped_objs(src_obj)
    (dest_objs_widget.tree_view.open_map().
     map_dest_objs(dest_objs_type=dest_objs[0].type.title(),
                   dest_objs_titles=dest_objs_titles))

  def _search_objs_via_tree_view(self, src_obj, dest_objs):
    """Open generic widget of mapped objects, open unified mapper modal from
    Tree View, fill data according to destination objects and search them.
    Return list of scopes (dicts) from members (text scopes) which displayed on
    Tree View according to current set of visible fields
    And list of MappingStatusAttrs namedtuples for mapping representation.
    """
    dest_objs_titles = [dest_obj.title for dest_obj in dest_objs]
    mapper = self._get_unified_mapper(src_obj)
    return mapper.search_dest_objs(
        dest_objs_type=dest_objs[0].type.title(),
        dest_objs_titles=dest_objs_titles), mapper.get_mapping_statuses()

  def get_count_objs_from_tab(self, src_obj):
    """Open generic widget of mapped objects, get count of objects from Tab
    navigation bar and return got count.
    """
    objs_widget = self.open_widget_of_mapped_objs(src_obj)
    return objs_widget.member_count

  def set_list_objs_scopes_representation_on_tree_view(self, src_obj):
    """Open generic widget of mapped objects, set visible fields for objects
    scopes representation on Tree View.
    """
    # pylint: disable=invalid-name
    objs_widget = self.open_widget_of_mapped_objs(src_obj)
    (objs_widget.tree_view.open_set_visible_fields().
     select_and_set_visible_fields())

  def _set_list_objs_scopes_repr_on_mapper_tree_view(self, src_obj):
    """Open generic widget of mapped objects, set visible fields for objects
    scopes representation on Unified Mapper Tree View.
    """
    # pylint: disable=invalid-name
    mapper = self._get_unified_mapper(src_obj)
    mapper.tree_view.open_set_visible_fields().select_and_set_visible_fields()

  def get_list_objs_scopes_from_tree_view(self, src_obj):
    """Open generic widget of mapped objects and get list of objects scopes as
    dicts from header (keys) and items (values) that displayed on Tree View.
    """
    # pylint: disable=invalid-name
    objs_widget = self.open_widget_of_mapped_objs(src_obj)
    return objs_widget.tree_view.get_list_members_as_list_scopes()

  def get_scope_from_info_page(self, obj):
    """Open Info page of obj and get object scope as dict with titles (keys)
    and entered_titles (values) that displayed on Info widget.
    """
    obj_info_page = self.open_info_page_of_obj(obj)
    return obj_info_page.get_info_widget_obj_scope()

  def get_scope_from_info_panel(self, src_obj, obj, navigate_by_title=True):
    """Open Info panel of obj navigate by object title as default or by
    object id if navigate_by_title is False, maximize it and get object scope
    as dict with titles (keys) and entered_titles (values) that displayed on
    Info panel.
    """
    obj_info_panel = (
        self.open_info_panel_of_obj_by_title(src_obj, obj) if navigate_by_title
        else self.open_info_panel_of_obj_by_id(src_obj, obj))
    return obj_info_panel.get_info_widget_obj_scope()

  def is_obj_editable_via_info_panel(self, src_obj, obj):
    """Open generic widget of mapped objects, select object from Tree View
    by title and check via Info panel that object is editable.
    """
    dropdown_on_info_panel = (
        self.open_info_panel_of_obj_by_title(src_obj, obj).open_info_3bbs())
    element_to_verify = element.DropdownMenuItemTypes.EDIT
    return dropdown_on_info_panel.is_item_exists(element_to_verify)

  def is_obj_unmappable_via_info_panel(self, src_obj, obj):
    """""Open generic widget of mapped objects, select object from Tree View
    by title open dropdown on Info Panel and check that object is unmappable.
    """
    dropdown_on_info_panel = (
        self.open_info_panel_of_obj_by_title(src_obj, obj).open_info_3bbs())
    element_to_verify = element.DropdownMenuItemTypes.UNMAP
    return dropdown_on_info_panel.is_item_exists(element_to_verify)

  def is_obj_page_exist_via_info_panel(self, src_obj, obj):
    """Open generic widget of mapped objects, select object from Tree View
    by title and check via Info panel that object page is exist.
    """
    # pylint: disable=invalid-name
    dropdown_on_info_panel = (
        self.open_info_panel_of_obj_by_title(src_obj, obj).open_info_3bbs())
    element_to_verify = element.DropdownMenuItemTypes.OPEN
    return dropdown_on_info_panel.is_item_enabled(element_to_verify)

  def filter_list_objs_from_tree_view(self, src_obj, filter_exp):
    """Filter by specified criteria and return list of objects from Tree
    View."""
    objs_widget = self.open_widget_of_mapped_objs(src_obj)
    objs_widget.filter.perform_query(filter_exp)
    self.set_list_objs_scopes_representation_on_tree_view(src_obj)
    list_objs_scopes = self.get_list_objs_scopes_from_tree_view(src_obj)
    return self.create_list_objs(entity_factory=self.entities_factory_cls,
                                 list_scopes=list_objs_scopes)

  def is_obj_mappable_via_tree_view(self, src_obj, obj):
    """""Open dropdown of Tree View Item  by title, an check is object
    mappable.
    """
    objs_widget = self.open_widget_of_mapped_objs(src_obj)
    dropdown_on_tree_view_item = (objs_widget.tree_view.
                                  open_tree_actions_dropdown_by_title
                                  (title=obj.title))
    element_to_verify = element.DropdownMenuItemTypes.MAP
    return dropdown_on_tree_view_item.is_item_exists(element_to_verify)


class SnapshotsWebUiService(BaseWebUiService):
  """Class for snapshots business layer's services objects."""

  def update_obj_ver_via_info_panel(self, src_obj, obj):
    """Open generic widget of mapped objects, select snapshotable object from
    Tree View by title and update object to latest version via Info panel.
    """
    objs_widget = self.open_widget_of_mapped_objs(src_obj)
    obj_info_panel = (objs_widget.tree_view.
                      select_member_by_title(title=obj.title))
    obj_info_panel.open_link_get_latest_ver().confirm_update()
    objs_widget.tree_view.wait_loading_after_actions()
    selenium_utils.get_when_invisible(
        self.driver, SnapshotableInfoPanel.locator_link_get_latest_ver)

  def is_obj_updateble_via_info_panel(self, src_obj, obj):
    """Open generic widget of mapped objects, select snapshotable object from
    Tree View by title and check via Info panel that object is updateble.
    """
    obj_info_panel = self.open_info_panel_of_obj_by_title(src_obj, obj)
    return obj_info_panel.is_link_get_latest_ver_exist()


class AuditsService(BaseWebUiService):
  """Class for Audits business layer's services objects."""
  def __init__(self, driver):
    super(AuditsService, self).__init__(driver, objects.AUDITS)

  def clone_via_info_page_and_get_obj(self, audit_obj):
    """Open Info page of Audit object and clone it including Assessment
    Templates via Info widget. Redirect to cloned Audit, get and return Audit
    object from Info page.
    """
    audit_info_page = self.open_info_page_of_obj(audit_obj)
    (audit_info_page.
     open_info_3bbs().select_clone().confirm_clone(is_full=True))
    cloned_audit_obj = self.entities_factory_cls().create_empty()
    cloned_audit_obj.url = self.driver.current_url
    actual_cloned_audit_obj = self.get_obj_from_info_page(obj=cloned_audit_obj)
    actual_cloned_audit_obj.url = cloned_audit_obj.url
    return actual_cloned_audit_obj

  def bulk_update_via_info_page(self, audit_obj):
    """Open Info page of Audit object and bulk update objects to
    latest version.
    """
    audit_info_page = self.open_info_page_of_obj(audit_obj)
    audit_info_page.open_info_3bbs().select_update_objs().confirm_update()


class AssessmentTemplatesService(BaseWebUiService):
  """Class for AssessmentTemplates business layer's services objects."""
  def __init__(self, driver):
    super(AssessmentTemplatesService, self).__init__(
        driver, objects.ASSESSMENT_TEMPLATES)


class AssessmentsService(BaseWebUiService):
  """Class for Assessments business layer's services objects."""
  def __init__(self, driver):
    super(AssessmentsService, self).__init__(
        driver, objects.ASSESSMENTS)

  def generate_objs_via_tree_view(self, src_obj, objs_under_asmt,
                                  asmt_tmpl_obj=None):
    """Open generic widget of mapped objects, open Generation modal from
    Tree View, fill data according to objects under Assessment
    and if 'asmt_tmpl_obj' then to Assessment Template title, generate
    new Assessment(s).
    """
    objs_under_asmt_titles = [obj_under.title for obj_under in
                              objs_under_asmt]
    objs_widget = self.open_widget_of_mapped_objs(src_obj)
    asmt_tmpl_title = asmt_tmpl_obj.title if asmt_tmpl_obj else None
    (objs_widget.tree_view.open_3bbs().select_generate().
     generate_asmts(asmt_tmpl_title=asmt_tmpl_title,
                    objs_under_asmt_titles=objs_under_asmt_titles))


class ControlsService(SnapshotsWebUiService):
  """Class for Controls business layer's services objects."""
  def __init__(self, driver):
    super(ControlsService, self).__init__(driver, objects.CONTROLS)


class IssuesService(BaseWebUiService):
  """Class for Issues business layer's services objects."""
  def __init__(self, driver):
    super(IssuesService, self).__init__(driver, objects.ISSUES)


class ProgramsService(BaseWebUiService):
  """Class for Programs business layer's services objects."""
  def __init__(self, driver):
    super(ProgramsService, self).__init__(driver, objects.PROGRAMS)
