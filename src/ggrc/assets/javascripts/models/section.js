/*!
    Copyright (C) 2017 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/


// this model doesn't exist anymore, can we get rid of it?
can.Model.Cacheable('CMS.Models.Section', {
  root_object: 'section',
  root_collection: 'sections',
  model_plural: 'Sections',
  table_plural: 'sections',
  title_plural: 'Sections',
  model_singular: 'Section',
  title_singular: 'Section',
  table_singular: 'section',
  category: 'governance',
  root_model: 'Section',
  findAll: 'GET /api/sections',
  findOne: 'GET /api/sections/{id}',
  create: 'POST /api/sections',
  update: 'PUT /api/sections/{id}',
  destroy: 'DELETE /api/sections/{id}',
  is_custom_attributable: true,
  isRoleable: true,
  mixins: ['unique_title', 'ca_update'],
  attributes: {
    context: 'CMS.Models.Context.stub',
    modified_by: 'CMS.Models.Person.stub',
    object_people: 'CMS.Models.ObjectPerson.stubs',
    people: 'CMS.Models.Person.stubs',
    directive: 'CMS.Models.get_stub',
    children: 'CMS.Models.get_stubs',
    directive_sections: 'CMS.Models.DirectiveSection.stubs',
    directives: 'CMS.Models.get_stubs',
    objectives: 'CMS.Models.Objective.stubs',
    custom_attribute_values: 'CMS.Models.CustomAttributeValue.stubs'
  },
  tree_view_options: {
    attr_view: '/static/mustache/sections/tree-item-attr.mustache',
    attr_list: can.Model.Cacheable.attr_list.concat([
      {attr_title: 'URL', attr_name: 'url'},
      {attr_title: 'Reference URL', attr_name: 'reference_url'}
    ]),
    add_item_view: GGRC.mustache_path + '/snapshots/tree_add_item.mustache'
  },
  defaults: {
    status: 'Draft'
  },
  statuses: ['Draft', 'Deprecated', 'Active'],
  init: function () {
    this._super.apply(this, arguments);
    this.validateNonBlank('title');
  }
}, {
});

can.Model.Cacheable('CMS.Models.Clause', {
  root_object: 'clause',
  root_collection: 'clauses',
  model_plural: 'Clauses',
  table_plural: 'clauses',
  title_plural: 'Clauses',
  model_singular: 'Clause',
  title_singular: 'Clause',
  table_singular: 'clause',
  category: 'governance',
  root_model: 'Clause',
  findAll: 'GET /api/clauses',
  findOne: 'GET /api/clauses/{id}',
  create: 'POST /api/clauses',
  update: 'PUT /api/clauses/{id}',
  destroy: 'DELETE /api/clauses/{id}',
  is_custom_attributable: true,
  isRoleable: true,
  mixins: ['unique_title', 'ca_update'],
  attributes: {
    context: 'CMS.Models.Context.stub',
    modified_by: 'CMS.Models.Person.stub',
    object_people: 'CMS.Models.ObjectPerson.stubs',
    people: 'CMS.Models.Person.stubs',
    directive: 'CMS.Models.get_stub',
    children: 'CMS.Models.get_stubs',
    directive_sections: 'CMS.Models.DirectiveSection.stubs',
    directives: 'CMS.Models.get_stubs',
    objectives: 'CMS.Models.Objective.stubs',
    custom_attribute_values: 'CMS.Models.CustomAttributeValue.stubs'
  },
  tree_view_options: {
    attr_view: '/static/mustache/sections/tree-item-attr.mustache',
    attr_list: can.Model.Cacheable.attr_list.concat([
      {attr_title: 'Clause URL', attr_name: 'url'},
      {attr_title: 'Reference URL', attr_name: 'reference_url'}
    ]),
    add_item_view: GGRC.mustache_path + '/snapshots/tree_add_item.mustache'
  },
  defaults: {
    status: 'Draft'
  },
  statuses: ['Draft', 'Deprecated', 'Active'],
  init: function () {
    this._super.apply(this, arguments);
    this.validateNonBlank('title');
  }
}, {});
