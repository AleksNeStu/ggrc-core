/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

can.Model.Cacheable('CMS.Models.SystemOrProcess', {
  root_object: 'system_or_process',
  root_collection: 'systems_or_processes',
  title_plural: 'Systems/Processes',
  category: 'business',
  findAll: 'GET /api/systems_or_processes',
  model: function (params) {
    if (this.shortName !== 'SystemOrProcess') {
      return this._super(params);
    }
    if (!params) {
      return params;
    }
    params = this.object_from_resource(params);
    if (!params.selfLink) {
      if (params.type !== 'SystemOrProcess') {
        return CMS.Models[params.type].model(params);
      }
    } else if (params.is_biz_process) {
      return CMS.Models.Process.model(params);
    } else {
      return CMS.Models.System.model(params);
    }
  },
  mixins: ['ownable', 'contactable', 'unique_title', 'timeboxed'],
  attributes: {
    context: 'CMS.Models.Context.stub',
    owners: 'CMS.Models.Person.stubs',
    modified_by: 'CMS.Models.Person.stub',
    object_people: 'CMS.Models.ObjectPerson.stubs',
    people: 'CMS.Models.Person.stubs',
    related_sources: 'CMS.Models.Relationship.stubs',
    related_destinations: 'CMS.Models.Relationship.stubs',
    objectives: 'CMS.Models.Objective.stubs',
    controls: 'CMS.Models.Control.stubs',
    sections: 'CMS.Models.get_stubs',
    network_zone: 'CMS.Models.Option.stub',
    custom_attribute_values: 'CMS.Models.CustomAttributeValue.stubs'
  },
  tree_view_options: {
    attr_view: GGRC.mustache_path + '/base_objects/tree-item-attr.mustache',
    attr_list: can.Model.Cacheable.attr_list.concat([
      {
        attr_title: 'Network Zone',
        attr_name: 'network_zone',
        attr_sort_field: 'network_zone'
      },
      {attr_title: 'Effective Date', attr_name: 'start_date'},
      {attr_title: 'Stop Date', attr_name: 'end_date'},
      {attr_title: 'URL', attr_name: 'url'},
      {attr_title: 'Reference URL', attr_name: 'reference_url'}
    ]),
    add_item_view: GGRC.mustache_path + '/base_objects/tree_add_item.mustache',
    link_buttons: true
  },
  links_to: {
    System: {},
    Process: {},
    Control: {},
    Product: {},
    Facility: {},
    OrgGroup: {},
    Vendor: {},
    Project: {},
    DataAsset: {},
    AccessGroup: {},
    Program: {},
    Market: {},
    Regulation: {},
    Policy: {},
    Standard: {},
    Contract: {},
    Objective: {}
  }
}, {
  system_or_process: function () {
    var result;
    if (this.attr('is_biz_process')) {
      result = 'process';
    } else {
      result = 'system';
    }
    return result;
  },
  system_or_process_capitalized: function () {
    var str = this.system_or_process();
    return str.charAt(0).toUpperCase() + str.slice(1);
  }
});

CMS.Models.SystemOrProcess('CMS.Models.System', {
  root_object: 'system',
  root_collection: 'systems',
  findAll: 'GET /api/systems',
  findOne: 'GET /api/systems/{id}',
  create: 'POST /api/systems',
  update: 'PUT /api/systems/{id}',
  destroy: 'DELETE /api/systems/{id}',
  mixins: ['ca_update'],
  cache: can.getObject('cache', CMS.Models.SystemOrProcess, true),
  is_custom_attributable: true,
  attributes: {},
  defaults: {
    title: '',
    url: '',
    status: 'Draft'
  },
  statuses: ['Draft', 'Deprecated', 'Active'],
  init: function () {
    can.extend(this.attributes, CMS.Models.SystemOrProcess.attributes);
    this._super && this._super.apply(this, arguments);
    this.tree_view_options = $.extend({},
      CMS.Models.SystemOrProcess.tree_view_options, {
        // systems is a special case; can be imported to programs
        footer_view: GGRC.mustache_path + '/base_objects/tree_footer.mustache',
        add_item_view: GGRC.mustache_path +
        (GGRC.infer_object_type(GGRC.page_object) === CMS.Models.Program ?
          '/snapshots/tree_add_item.mustache' :
          '/base_objects/tree_add_item.mustache')
      });
    this.validateNonBlank('title');
  } // don't rebind the ObjectDocument/ObjectPerson events.
}, {
  init: function () {
    this._super && this._super.apply(this, arguments);
    this.attr('is_biz_process', false);
  }
});

CMS.Models.SystemOrProcess('CMS.Models.Process', {
  root_object: 'process',
  root_collection: 'processes',
  model_plural: 'Processes',
  table_plural: 'processes',
  title_plural: 'Processes',
  model_singular: 'Process',
  title_singular: 'Process',
  table_singular: 'process',
  findAll: 'GET /api/processes',
  findOne: 'GET /api/processes/{id}',
  create: 'POST /api/processes',
  update: 'PUT /api/processes/{id}',
  destroy: 'DELETE /api/processes/{id}',
  cache: can.getObject('cache', CMS.Models.SystemOrProcess, true),
  is_custom_attributable: true,
  attributes: {},
  defaults: {
    title: '',
    url: '',
    status: 'Draft'
  },
  mixins: ['ca_update'],
  statuses: ['Draft', 'Deprecated', 'Active'],
  init: function () {
    can.extend(this.attributes, CMS.Models.SystemOrProcess.attributes);
    this._super && this._super.apply(this, arguments);
    this.tree_view_options = $.extend({},
      CMS.Models.SystemOrProcess.tree_view_options);
    this.validateNonBlank('title');
  } // don't rebind the ObjectDocument/ObjectPerson events.
}, {
  init: function () {
    this._super && this._super.apply(this, arguments);
    this.attr('is_biz_process', true);
  }
});
