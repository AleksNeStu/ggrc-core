# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""The module provides service creating and manipulating GGRC's business
objects via Web UI."""

from lib.constants import element
from lib.entities.entities_factory import (
    AsmtTmplFactory, AsmtFactory, EntitiesFactory)
from lib.page.widget.generic_widget import AsmtTmpls, Asmts


class BaseWebUiService(object):
  """Base class for business layer's services objects."""
  def __init__(self, driver):
    self.driver = driver

  @staticmethod
  def dict_map_ui_elements_to_obj_attrs():
    """Get transformation dictionary {OLD KEY: NEW KEY}, where
    'OLD KEY' - UI elements correspond to the 'NEW KEY' - objects attributes.
    """
    fields = element.AsmtModalSetVisibleFields()
    return {
        fields.TITLE.upper(): "title", fields.CODE.upper(): "code",
        fields.STATE.upper(): "state", fields.VERIFIED.upper(): "is_verified",
        fields.LAST_UPDATED.upper(): "last_update"
    }

  @staticmethod
  def remap_keys_for_list_dicts(transform_dict, list_old_dicts):
    """Remap keys names for old list of dictionaries according the
    transformation dictionary {OLD KEY: NEW KEY} and return the new updated
    list of dictionaries.
    """
    return [{transform_dict[key]: value for key, value in dic.iteritems()} for
            dic in list_old_dicts]

  def create_objs(self, factory, list_of_scopes):
    """Create business objects used entities factories and Web UI
    (list of text scopes (list of dicts) got from Web UI).
    Return list of objects.
    """
    objs = [factory.create() for _ in xrange(len(list_of_scopes))]
    list_of_scopes_remaped = self.remap_keys_for_list_dicts(
        transform_dict=self.dict_map_ui_elements_to_obj_attrs(),
        list_old_dicts=list_of_scopes)
    return [EntitiesFactory.update_obj_attrs_values(
        obj=obj, **scope_remaped) for
            scope_remaped, obj in zip(list_of_scopes_remaped, objs)]


class AuditService(BaseWebUiService):
  """Service for working with business entity Audit."""
  def __init__(self, driver):
    super(AuditService, self).__init__(driver)

  def create_obj_via_modal(self, audit, obj, gen_widget):
    """Navigate to objects widget, open modal, fill data and create new object.
    """
    self.driver.get(gen_widget.URL.format(audit.id))
    modal_page = gen_widget(self.driver).create()
    modal_page.fill_minimal_data(obj.title)
    modal_page.save_and_close()

  def generate_objs_via_modal(self, audit, obj, objs_under, gen_widget):
    """Navigate to objects widget, open modal, fill data and generate new
    object(s).
    """
    objs_under_titles = [obj_under.title for obj_under in objs_under]
    self.driver.get(gen_widget.URL.format(audit.id))
    modal_page = gen_widget(self.driver).generate()
    modal_page.fill_minimal_data(obj.title, objs_under_titles)
    modal_page.generate_and_close()

  def get_count_of_objs_from_tab(self, audit, gen_widget):
    """Navigate to objects widget and get count of objects from tab
    navigation bar.
    """
    gen_widget(self.driver).navigate_to(gen_widget.URL.format(audit.id))
    return gen_widget(self.driver).member_count

  def get_list_of_scopes_from_tree_view(self, audit, gen_widget):
    """Navigate to objects widget, set visible fields and get list of objects
    scopes as dicts from header (keys) and items (values) that displayed
    in tree view.
    """
    gen_widget(self.driver).navigate_to(gen_widget.URL.format(audit.id))
    return gen_widget(self.driver).get_list_of_objs_scopes()


class AsmtTmplService(AuditService):
  """Service for working with business entity assessment template."""
  def __init__(self, driver):
    super(AsmtTmplService, self).__init__(driver)

  def create(self, audit, asmt_tmpl):
    """Create new assessment template via modal."""
    self.create_obj_via_modal(audit=audit, obj=asmt_tmpl, gen_widget=AsmtTmpls)

  def get_count(self, audit):
    """Return count of assessment templates from tab navigation bar."""
    return self.get_count_of_objs_from_tab(audit=audit, gen_widget=AsmtTmpls)

  def get_list_of_objs(self, audit):
    """Get list of assessment templates objects from list of scopes
    (list of dicts) which was got from tree view."""
    list_of_scopes = self.get_list_of_scopes_from_tree_view(
        audit=audit, gen_widget=AsmtTmpls)
    return self.create_objs(
        factory=AsmtTmplFactory(), list_of_scopes=list_of_scopes)


class AsmtService(AuditService):
  """Service for working with business entity assessment."""
  def __init__(self, driver):
    super(AsmtService, self).__init__(driver)

  def create(self, audit, asmt):
    """Create new assessment template via modal."""
    self.create_obj_via_modal(audit=audit, obj=asmt, gen_widget=Asmts)

  def generate(self, audit, asmt_tmpl, objs_under):
    """Generate new assessment(s) via modal."""
    self.generate_objs_via_modal(
        audit=audit, obj=asmt_tmpl, objs_under=objs_under, gen_widget=Asmts)

  def get_count(self, audit):
    """Return count of assessments from tab navigation bar."""
    return self.get_count_of_objs_from_tab(audit=audit, gen_widget=Asmts)

  def get_list_of_objs(self, audit):
    """Get list of assessments objects from list of scopes (list of dicts)
    which was got from tree view."""
    list_of_scopes = self.get_list_of_scopes_from_tree_view(
        audit=audit, gen_widget=Asmts)
    return self.create_objs(
        factory=AsmtFactory(), list_of_scopes=list_of_scopes)
