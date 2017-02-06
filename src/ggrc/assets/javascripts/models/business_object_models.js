/*!
    Copyright (C) 2017 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

(function(can) {

can.Model.Cacheable("CMS.Models.OrgGroup", {
  root_object : "org_group",
  root_collection : "org_groups",
  category : "entities",
  findAll : "GET /api/org_groups",
  findOne : "GET /api/org_groups/{id}",
  create : "POST /api/org_groups",
  update : "PUT /api/org_groups/{id}",
  destroy : "DELETE /api/org_groups/{id}",
  mixins : ['ownable', 'contactable', 'unique_title', 'ca_update',
            'timeboxed'],
  is_custom_attributable: true,
  attributes : {
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
      custom_attribute_values: 'CMS.Models.CustomAttributeValue.stubs'
  },
  tree_view_options : {
    show_view : GGRC.mustache_path + "/base_objects/tree.mustache",
    footer_view : GGRC.mustache_path + "/base_objects/tree_footer.mustache",
    add_item_view : GGRC.mustache_path + "/base_objects/tree_add_item.mustache",
    attr_list : can.Model.Cacheable.attr_list.concat([
      {attr_title: 'URL', attr_name: 'url'},
      {attr_title: 'Reference URL', attr_name: 'reference_url'},
      {attr_title: 'Effective Date', attr_name: 'start_date'},
      {attr_title: 'Stop Date', attr_name: 'end_date'}
    ]),
    child_options : [{
      model : null,
      find_params : {
        "destination_type" : "Process",
        "source_type" : "OrgGroup",
        relationship_type_id : "org_group_has_process"
      },
      parent_find_param : "source_id",
      draw_children : true,
      find_function : "findRelated",
      related_side : "source",
      create_link : true
    }, {
      model : null,
      find_params : {
        "destination_type" : "OrgGroup",
        "source_type" : "OrgGroup",
        relationship_type_id: "org_group_relies_upon_org_group"
      },
      parent_find_param : "destination_id",
      draw_children : true,
      start_expanded : false,
      find_function : "findRelatedSource",
      related_side : "destination",
      single_object : false,
      create_link : true
    }]},
  links_to : {
    "System" : {},
    "Process" : {},
    "Program" : {},
    "Product" : {},
    "Facility" : {},
    "OrgGroup" : {},
    "Vendor" : {},
    "Project" : {},
    "DataAsset" : {},
    "AccessGroup" : {},
    "Market" : {}
    },
  defaults: {
    status: 'Draft'
  },
  statuses: ['Draft', 'Deprecated', 'Active'],
  init: function () {
    var that = this;
    this._super && this._super.apply(this, arguments);
    $(function(){
      that.tree_view_options.child_options[0].model = CMS.Models.Process;
    });
    this.tree_view_options.child_options[1].model = this;

    this.validateNonBlank("title");
  }
}, {});

can.Model.Cacheable("CMS.Models.Project", {
  root_object : "project",
  root_collection : "projects",
  category : "business",
  findAll : "GET /api/projects",
  findOne : "GET /api/projects/{id}",
  create : "POST /api/projects",
  update : "PUT /api/projects/{id}",
  destroy : "DELETE /api/projects/{id}",
  mixins : ['ownable', 'contactable', 'unique_title', 'ca_update', 'timeboxed'],
  is_custom_attributable: true,
  attributes : {
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
      custom_attribute_values: 'CMS.Models.CustomAttributeValue.stubs'
  },
  tree_view_options : {
    show_view : GGRC.mustache_path + "/base_objects/tree.mustache",
    footer_view : GGRC.mustache_path + "/base_objects/tree_footer.mustache",
    attr_list : can.Model.Cacheable.attr_list.concat([
      {attr_title: 'URL', attr_name: 'url'},
      {attr_title: 'Reference URL', attr_name: 'reference_url'},
      {attr_title: 'Effective Date', attr_name: 'start_date'},
      {attr_title: 'Stop Date', attr_name: 'end_date'}
    ]),
    add_item_view : GGRC.mustache_path + "/base_objects/tree_add_item.mustache",
    child_options : [{
      model : null,
      find_params : {
        "destination_type" : "Process",
        "source_type" : "Project",
        relationship_type_id : "project_has_process"
      },
      parent_find_param : "source_id",
      draw_children : true,
      find_function : "findRelated",
      related_side : "source",
      create_link : true
    }]},
  links_to : {
    "System" : {},
    "Process" : {},
    "Program" : {},
    "Product" : {},
    "Facility" : {},
    "OrgGroup" : {},
    "Vendor" : {},
    "Project" : {},
    "DataAsset" : {},
    "AccessGroup" : {},
    "Market" : {}
    },
  defaults: {
    status: 'Draft'
  },
  statuses: ['Draft', 'Deprecated', 'Active'],
  init: function () {
    var that = this;
    this._super && this._super.apply(this, arguments);
    $(function(){
      that.tree_view_options.child_options[0].model = CMS.Models.Process;
    });

    this.validateNonBlank("title");
  }
}, {});

can.Model.Cacheable("CMS.Models.Facility", {
  root_object : "facility",
  root_collection : "facilities",
  category : "business",
  findAll : "GET /api/facilities",
  findOne : "GET /api/facilities/{id}",
  create : "POST /api/facilities",
  update : "PUT /api/facilities/{id}",
  destroy : "DELETE /api/facilities/{id}",
  mixins : ['ownable', 'contactable', 'unique_title', 'ca_update', 'timeboxed'],
  is_custom_attributable: true,
  attributes : {
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
      custom_attribute_values: 'CMS.Models.CustomAttributeValue.stubs'
  },
  tree_view_options : {
    show_view : GGRC.mustache_path + "/base_objects/tree.mustache",
    footer_view : GGRC.mustache_path + "/base_objects/tree_footer.mustache",
    attr_list : can.Model.Cacheable.attr_list.concat([
      {attr_title: 'URL', attr_name: 'url'},
      {attr_title: 'Reference URL', attr_name: 'reference_url'},
      {attr_title: 'Effective Date', attr_name: 'start_date'},
      {attr_title: 'Stop Date', attr_name: 'end_date'}
    ]),
    add_item_view : GGRC.mustache_path + "/base_objects/tree_add_item.mustache",
    child_options : [{
      model : null,
      find_params : {
        "destination_type" : "Process",
        "source_type" : "Facility",
        relationship_type_id : "facility_has_process"
      },
      parent_find_param : "source_id",
      draw_children : true,
      find_function : "findRelated",
      related_side : "source",
      create_link : true
    }, {
      model : null,
      find_params : {
        "destination_type" : "Facility",
        "source_type" : "Facility",
        relationship_type_id: "facility_relies_upon_facility"
      },
      parent_find_param : "destination_id",
      draw_children : true,
      start_expanded : false,
      find_function : "findRelatedSource",
      related_side : "destination",
      single_object : false,
      create_link : true
    }]},
  links_to : {
    "System" : {},
    "Process" : {},
    "Program" : {},
    "Product" : {},
    "Facility" : {},
    "OrgGroup" : {},
    "Vendor" : {},
    "Project" : {},
    "DataAsset" : {},
    "AccessGroup" : {},
    "Market" : {}
    },
  defaults: {
    status: 'Draft'
  },
  statuses: ['Draft', 'Deprecated', 'Active'],
  init: function () {
    var that = this;
    this._super && this._super.apply(this, arguments);
    $(function(){
      that.tree_view_options.child_options[0].model = CMS.Models.Process;
    });
    this.tree_view_options.child_options[1].model = this;

    this.validateNonBlank("title");
  }
}, {});

can.Model.Cacheable("CMS.Models.Product", {
  root_object : "product",
  root_collection : "products",
  category : "business",
  findAll : "GET /api/products",
  findOne : "GET /api/products/{id}",
  create : "POST /api/products",
  update : "PUT /api/products/{id}",
  destroy : "DELETE /api/products/{id}",
  mixins : ['ownable', 'contactable', 'unique_title', 'ca_update', 'timeboxed'],
  is_custom_attributable: true,
  attributes : {
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
      kind: 'CMS.Models.Option.stub',
      custom_attribute_values: 'CMS.Models.CustomAttributeValue.stubs'
  },
  defaults : {
    kind : null
  },
  tree_view_options : {
    show_view : GGRC.mustache_path + "/base_objects/tree.mustache",
    footer_view : GGRC.mustache_path + "/base_objects/tree_footer.mustache",
    attr_list : can.Model.Cacheable.attr_list.concat([
      {attr_title: 'Type', attr_name: 'type'},
      {attr_title: 'URL', attr_name: 'url'},
      {attr_title: 'Reference URL', attr_name: 'reference_url'}
    ]),
    add_item_view : GGRC.mustache_path + "/base_objects/tree_add_item.mustache",
    child_options : [{
      model : null,
      find_params : {
        "destination_type" : "Process",
        "source_type" : "Product",
        relationship_type_id : "product_has_process"
      },
      parent_find_param : "source_id",
      draw_children : true,
      find_function : "findRelated",
      related_side : "source",
      create_link : true
    }, {
      model : null,
      find_params : {
        "destination_type" : "Product",
        "source_type" : "Product",
        relationship_type_id: "product_relies_upon_product"
      },
      parent_find_param : "destination_id",
      draw_children : true,
      start_expanded : false,
      find_function : "findRelatedSource",
      related_side : "destination",
      single_object : false,
      create_link : true
    }]},
  links_to : {
    "System" : {},
    "Process" : {},
    "Program" : {},
    "Product" : {},
    "Facility" : {},
    "OrgGroup" : {},
    "Vendor" : {},
    "Project" : {},
    "DataAsset" : {},
    "AccessGroup" : {},
    "Market" : {}
    },
  defaults: {
    status: 'Draft'
  },
  statuses: ['Draft', 'Deprecated', 'Active'],
  init: function () {
    var that = this;
    this._super && this._super.apply(this, arguments);
    $(function(){
      that.tree_view_options.child_options[0].model = CMS.Models.Process;
    });
    this.tree_view_options.child_options[1].model = this;

    this.validateNonBlank("title");
  }
}, {
});

can.Model.Cacheable("CMS.Models.DataAsset", {
  root_object : "data_asset",
  root_collection : "data_assets",
  category : "business",
  findAll : "GET /api/data_assets",
  findOne : "GET /api/data_assets/{id}",
  create : "POST /api/data_assets",
  update : "PUT /api/data_assets/{id}",
  destroy : "DELETE /api/data_assets/{id}",
  mixins : ['ownable', 'contactable', 'unique_title', 'ca_update', 'timeboxed'],
  is_custom_attributable: true,
  attributes : {
      context: 'CMS.Models.Context.stub',
      owners: 'CMS.Models.Person.stubs',
      modified_by: 'CMS.Models.Person.stub',
      object_people: 'CMS.Models.ObjectPerson.stubs',
      people: 'CMS.Models.Person.stubs',
      related_sources: 'CMS.Models.Relationship.stubs',
      related_destinations: 'CMS.Models.Relationship.stubs',
      objectives: 'CMS.Models.Objective.stubs',
      controls: 'CMS.Models.Control.stubs',
      sections:'CMS.Models.get_stubs',
      custom_attribute_values: 'CMS.Models.CustomAttributeValue.stubs'
  },
  tree_view_options : {
    show_view : GGRC.mustache_path + "/base_objects/tree.mustache",
    footer_view : GGRC.mustache_path + "/base_objects/tree_footer.mustache",
    attr_list : can.Model.Cacheable.attr_list.concat([
      {attr_title: 'URL', attr_name: 'url'},
      {attr_title: 'Reference URL', attr_name: 'reference_url'},
      {attr_title: 'Effective Date', attr_name: 'start_date'},
      {attr_title: 'Stop Date', attr_name: 'end_date'}
    ]),
    add_item_view : GGRC.mustache_path + "/base_objects/tree_add_item.mustache",
    child_options : [{
      model : null,
      find_params : {
        "destination_type" : "Process",
        "source_type" : "DataAsset",
        relationship_type_id : "data_asset_has_process"
      },
      parent_find_param : "source_id",
      draw_children : true,
      find_function : "findRelated",
      related_side : "source",
      create_link : true
    }, {
      model : null,
      find_params : {
        "destination_type" : "DataAsset",
        "source_type" : "DataAsset",
        relationship_type_id: "data_asset_relies_upon_data_asset"
      },
      parent_find_param : "destination_id",
      draw_children : true,
      start_expanded : false,
      find_function : "findRelatedSource",
      related_side : "destination",
      single_object : false,
      create_link : true
    }]},
  links_to : {
    "System" : {},
    "Process" : {},
    "Program" : {},
    "Product" : {},
    "Facility" : {},
    "OrgGroup" : {},
    "Vendor" : {},
    "Project" : {},
    "DataAsset" : {},
    "AccessGroup" : {},
    "Market" : {}
    },
  defaults: {
    status: 'Draft'
  },
  statuses: ['Draft', 'Deprecated', 'Active'],
  init: function () {
    var that = this;
    this._super && this._super.apply(this, arguments);
    $(function(){
      that.tree_view_options.child_options[0].model = CMS.Models.Process;
    });
    this.tree_view_options.child_options[1].model = this;

    this.validateNonBlank("title");
  }
}, {});

can.Model.Cacheable("CMS.Models.AccessGroup", {
  root_object : "access_group",
  root_collection : "access_groups",
  category : "entities",
  findAll : "GET /api/access_groups",
  findOne : "GET /api/access_groups/{id}",
  create : "POST /api/access_groups",
  update : "PUT /api/access_groups/{id}",
  destroy : "DELETE /api/access_groups/{id}",
  mixins : ['ownable', 'contactable', 'unique_title', 'ca_update'],
  is_custom_attributable: true,
  attributes : {
    context : "CMS.Models.Context.stub",
    owners : "CMS.Models.Person.stubs",
    modified_by : "CMS.Models.Person.stub",
    object_people : "CMS.Models.ObjectPerson.stubs",
    people : "CMS.Models.Person.stubs",
    related_sources : "CMS.Models.Relationship.stubs",
    related_destinations : "CMS.Models.Relationship.stubs",
    objectives : "CMS.Models.Objective.stubs",
    controls : "CMS.Models.Control.stubs",
    sections : "CMS.Models.get_stubs",
    custom_attribute_values : "CMS.Models.CustomAttributeValue.stubs"
  },
  tree_view_options : {
    show_view : GGRC.mustache_path + "/base_objects/tree.mustache",
    footer_view : GGRC.mustache_path + "/base_objects/tree_footer.mustache",
    attr_list : can.Model.Cacheable.attr_list.concat([
      {attr_title: 'URL', attr_name: 'url'},
      {attr_title: 'Reference URL', attr_name: 'reference_url'},
      {attr_title: 'Effective Date', attr_name: 'start_date'},
      {attr_title: 'Stop Date', attr_name: 'end_date'}
    ]),
    add_item_view : GGRC.mustache_path + "/base_objects/tree_add_item.mustache",
    child_options : [{
      model : null,
      find_params : {
        "destination_type" : "Process",
        "source_type" : "AccessGroup",
        relationship_type_id : "access_group_has_process"
      },
      parent_find_param : "source_id",
      draw_children : true,
      find_function : "findRelated",
      related_side : "source",
      create_link : true
    }, {
      model : null,
      find_params : {
        "destination_type" : "AccessGroup",
        "source_type" : "AccessGroup",
        relationship_type_id: "access_group_relies_upon_access_group"
      },
      parent_find_param : "destination_id",
      draw_children : true,
      start_expanded : false,
      find_function : "findRelatedSource",
      related_side : "destination",
      single_object : false,
      create_link : true
    }]},
  links_to : {
    "System" : {},
    "Process" : {},
    "Program" : {},
    "Product" : {},
    "Facility" : {},
    "OrgGroup" : {},
    "Vendor" : {},
    "Project" : {},
    "DataAsset" : {},
    "AccessGroup" : {},
    "Market" : {}
    },
  defaults: {
    status: 'Draft'
  },
  statuses: ['Draft', 'Deprecated', 'Active'],
  init: function () {
    var that = this;
    this._super && this._super.apply(this, arguments);
    $(function(){
      that.tree_view_options.child_options[0].model = CMS.Models.Process;
    });
    this.tree_view_options.child_options[1].model = this;

    this.validateNonBlank("title");
  }
}, {});

  can.Model.Cacheable("CMS.Models.Market", {
    root_object: 'market',
    root_collection: 'markets',
    category: 'business',
    findAll: 'GET /api/markets',
    findOne: 'GET /api/markets/{id}',
    create: 'POST /api/markets',
    update: 'PUT /api/markets/{id}',
    destroy: 'DELETE /api/markets/{id}',
    mixins: ['ownable', 'contactable', 'unique_title', 'ca_update',
             'timeboxed'],
    is_custom_attributable: true,
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
      custom_attribute_values: 'CMS.Models.CustomAttributeValue.stubs'
    },
    tree_view_options: {
      show_view: GGRC.mustache_path + '/base_objects/tree.mustache',
      footer_view: GGRC.mustache_path + '/base_objects/tree_footer.mustache',
      attr_list: can.Model.Cacheable.attr_list.concat([
        {attr_title: 'URL', attr_name: 'url'},
        {attr_title: 'Reference URL', attr_name: 'reference_url'},
        {attr_title: 'Effective Date', attr_name: 'start_date'},
        {attr_title: 'Stop Date', attr_name: 'end_date'}
      ]),
      add_item_view: GGRC.mustache_path + '/base_objects/tree_add_item.mustache',
      child_options: [{
        model: null,
        find_params: {
          destination_type: 'Process',
          source_type: 'Market',
          relationship_type_id: 'market_has_process'
        },
        parent_find_param: 'source_id',
        draw_children: true,
        find_function: 'findRelated',
        related_side: 'source',
        create_link: true
      }]
    },
    links_to: {
      System: {},
      Process: {},
      Program: {},
      Product: {},
      Facility: {},
      OrgGroup: {},
      Vendor: {},
      Project: {},
      DataAsset: {},
      AccessGroup: {},
      Market: {}
    },
    defaults: {
      status: 'Draft'
    },
    statuses: ['Draft', 'Deprecated', 'Active'],
    init: function () {
      var that = this;
      if (this._super) {
        this._super.apply(this, arguments);
      }
      $(function () {
        that.tree_view_options.child_options[0].model = CMS.Models.Process;
      });

      this.validateNonBlank('title');
    }
  }, {});

can.Model.Cacheable("CMS.Models.Vendor", {
  root_object : "vendor",
  root_collection : "vendors",
  category : "entities",
  findAll : "GET /api/vendors",
  findOne : "GET /api/vendors/{id}",
  create : "POST /api/vendors",
  update : "PUT /api/vendors/{id}",
  destroy : "DELETE /api/vendors/{id}",
  mixins : ['ownable', 'contactable', 'unique_title', 'ca_update', 'timeboxed'],
  is_custom_attributable: true,
  attributes : {
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
      custom_attribute_values: 'CMS.Models.CustomAttributeValue.stubs'
  },
  tree_view_options : {
    show_view : GGRC.mustache_path + "/base_objects/tree.mustache",
    footer_view : GGRC.mustache_path + "/base_objects/tree_footer.mustache",
    attr_list : can.Model.Cacheable.attr_list.concat([
      {attr_title: 'URL', attr_name: 'url'},
      {attr_title: 'Reference URL', attr_name: 'reference_url'},
      {attr_title: 'Effective Date', attr_name: 'start_date'},
      {attr_title: 'Stop Date', attr_name: 'end_date'}
    ]),
    add_item_view : GGRC.mustache_path + "/base_objects/tree_add_item.mustache",
    child_options : [{
      model : null,
      find_params : {
        "destination_type" : "Process",
        "source_type" : "Vendor",
        relationship_type_id : "vendor_has_process"
      },
      parent_find_param : "source_id",
      draw_children : true,
      find_function : "findRelated",
      related_side : "source",
      create_link : true
    }, {
      model : null,
      find_params : {
        "destination_type" : "Vendor",
        "source_type" : "Vendor",
        relationship_type_id: "vendor_relies_upon_vendor"
      },
      parent_find_param : "destination_id",
      draw_children : true,
      start_expanded : false,
      find_function : "findRelatedSource",
      related_side : "destination",
      single_object : false,
      create_link : true
    }]},
  links_to : {
    "System" : {},
    "Process" : {},
    "Program" : {},
    "Product" : {},
    "Facility" : {},
    "OrgGroup" : {},
    "Vendor" : {},
    "Project" : {},
    "DataAsset" : {},
    "AccessGroup" : {},
    "Market" : {}
    },
  defaults: {
    status: 'Draft'
  },
  statuses: ['Draft', 'Deprecated', 'Active'],
  init: function () {
    var that = this;
    this._super && this._super.apply(this, arguments);
    $(function(){
      that.tree_view_options.child_options[0].model = CMS.Models.Process;
    });
    this.tree_view_options.child_options[1].model = this;

    this.validateNonBlank("title");
  }
}, {});

})(this.can);
