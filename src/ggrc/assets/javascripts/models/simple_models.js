/*!
    Copyright (C) 2017 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

//require can.jquery-all

(function(can) {

can.Model.Cacheable("CMS.Models.Context", {
    root_object : "context"
  , root_collection : "contexts"
  , category : "contexts"
  , findAll : "/api/contexts"
  , findOne : "/api/contexts/{id}"
  , create : "POST /api/contexts"
  , update : "PUT /api/contexts/{id}"
  , destroy : "DELETE /api/contexts/{id}"
  , attributes : {
      context : "CMS.Models.Context.stub"
    , related_object: "CMS.Models.get_stub"
    , user_roles: "CMS.Models.UserRole.stubs"
    }
}, {
});

can.Model.Cacheable("CMS.Models.Program", {
  root_object : "program"
  , root_collection : "programs"
  , category : "programs"
  , findAll : "/api/programs"
  , findOne : "/api/programs/{id}"
  , create : "POST /api/programs"
  , update : "PUT /api/programs/{id}"
  , destroy : "DELETE /api/programs/{id}"
  , mixins : ['contactable', 'unique_title', 'ca_update', 'timeboxed']
  , is_custom_attributable: true
  , attributes : {
      context: 'CMS.Models.Context.stub',
      owners: 'CMS.Models.Person.stubs',
      modified_by: 'CMS.Models.Person.stub',
      object_people: 'CMS.Models.ObjectPerson.stubs',
      people: 'CMS.Models.Person.stubs',
      related_sources: 'CMS.Models.Relationship.stubs',
      related_destinations: 'CMS.Models.Relationship.stubs',
      objectives: 'CMS.Models.Objective.stubs',
      sections: 'CMS.Models.get_stubs',
      directives: 'CMS.Models.Directive.stubs',
      controls: 'CMS.Models.Control.stubs',
      audits: 'CMS.Models.Audit.stubs',
      custom_attribute_values: 'CMS.Models.CustomAttributeValue.stubs'
  }
  , tree_view_options : {
      show_view : GGRC.mustache_path + "/programs/tree.mustache"
    , footer_view : GGRC.mustache_path + "/base_objects/tree_footer.mustache"
    , attr_list : [
      {attr_title: 'Manager', attr_name: 'owner', attr_sort_field: 'authorizations.0.person.name|email'}
    ].concat(can.Model.Cacheable.attr_list.filter(function (d) {
      return d.attr_name != 'owner';
    })).concat([
      {attr_title: 'URL', attr_name: 'url'},
      {attr_title: 'Reference URL', attr_name: 'reference_url'},
      {attr_title: 'Effective Date', attr_name: 'start_date'},
      {attr_title: 'Stop Date', attr_name: 'end_date'}
    ])
    , add_item_view : GGRC.mustache_path + "/base_objects/tree_add_item.mustache"
    }
  , links_to : {
    "System" : {}
    , "Process" : {}
    , "Product" : {}
    , "Facility" : {}
    , "OrgGroup" : {}
    , "Vendor" : {}
    , "Project" : {}
    , "DataAsset" : {}
    , "AccessGroup" : {}
    , "Product" : {}
    , "Market" : {}
  },
  defaults: {
    status: 'Draft'
  },
  statuses: ['Draft', 'Deprecated', 'Active'],
  init: function () {
    this.validateNonBlank("title");
    this._super.apply(this, arguments);
  }
}, {
});

can.Model.Cacheable("CMS.Models.Option", {
  root_object : "option"
  , findAll : "GET /api/options"
  , findOne : "GET /api/options/{id}"
  , create : "POST /api/options"
  , update : "PUT /api/options/{id}"
  , destroy : "DELETE /api/options/{id}"
  , root_collection : "options"
  , cache_by_role: {}
  , for_role: function(role) {
      var self = this;

      if (!this.cache_by_role[role])
        this.cache_by_role[role] =
          this.findAll({ role: role }).then(function(options) {
            self.cache_by_role[role] = options;
            return options;
          });
      return $.when(this.cache_by_role[role]);
    }
}, {});

can.Model.Cacheable("CMS.Models.Objective", {
  root_object : "objective"
  , root_collection : "objectives"
  , category : "objectives"
  , title_singular : "Objective"
  , title_plural : "Objectives"
  , findAll : "GET /api/objectives"
  , findOne : "GET /api/objectives/{id}"
  , create : "POST /api/objectives"
  , update : "PUT /api/objectives/{id}"
  , destroy : "DELETE /api/objectives/{id}"
  , mixins : ['ownable', 'contactable', 'unique_title', 'ca_update']
  , is_custom_attributable: true
  , attributes : {
      context : "CMS.Models.Context.stub"
    , owners : "CMS.Models.Person.stubs"
    , modified_by : "CMS.Models.Person.stub"
    , sections : "CMS.Models.get_stubs"
    , controls : "CMS.Models.Control.stubs"
    , object_people : "CMS.Models.ObjectPerson.stubs"
    , related_sources : "CMS.Models.Relationship.stubs"
    , related_destinations : "CMS.Models.Relationship.stubs"
    , objective_objects : "CMS.Models.ObjectObjective.stubs"
    , custom_attribute_values : "CMS.Models.CustomAttributeValue.stubs"
  }
  , tree_view_options : {
      show_view : GGRC.mustache_path + "/objectives/tree.mustache"
    , footer_view : GGRC.mustache_path + "/base_objects/tree_footer.mustache"
    , attr_list : can.Model.Cacheable.attr_list.concat([
      {attr_title: 'URL', attr_name: 'url'},
      {attr_title: 'Reference URL', attr_name: 'reference_url'}
    ])
    , add_item_view : GGRC.mustache_path + "/snapshots/tree_add_item.mustache"
    , create_link : true
    //, draw_children : true
    , start_expanded : false
    , child_options : [{
        model : can.Model.Cacheable
      , mapping : "related_objects" //"related_and_able_objects"
      , footer_view : GGRC.mustache_path + "/base_objects/tree_footer.mustache"
      , add_item_view : GGRC.mustache_path + "/base_objects/tree_add_item.mustache"
      , title_plural : "Business Objects"
      , draw_children : false
    }]
  },
  defaults: {
    status: 'Draft'
  },
  statuses: ['Draft', 'Deprecated', 'Active'],
  init: function () {
    this.validateNonBlank("title");
    this._super.apply(this, arguments);
  }
}, {
});

can.Model.Cacheable("CMS.Models.Help", {
  root_object : "help"
  , root_collection : "helps"
  , findAll : "GET /api/help"
  , findOne : "GET /api/help/{id}"
  , update : "PUT /api/help/{id}"
  , destroy : "DELETE /api/help/{id}"
  , create : "POST /api/help"
}, {});

can.Model.Cacheable("CMS.Models.Event", {
  root_object : "event"
  , root_collection : "events"
  , findAll : "GET /api/events"
  , list_view_options : { find_params: { __include: "revisions" } }
  , attributes : {
      modified_by : "CMS.Models.Person.stub"
    }
}, {});

can.Model.Cacheable('CMS.Models.Role', {
  root_object: 'role',
  root_collection: 'roles',
  findAll: 'GET /api/roles',
  findOne: 'GET /api/roles/{id}',
  update: 'PUT /api/roles/{id}',
  destroy: 'DELETE /api/roles/{id}',
  create: 'POST /api/roles',
  scopes: [
    'Private Program',
    'Workflow',
    'System'
  ],
  defaults: {
    permissions: {
      read: [],
      update: [],
      create: [],
      delete: []
    }
  }
}, {

  allowed : function(operation, object_or_class) {
    var cls = typeof object_or_class === "function" ? object_or_class : object_or_class.constructor;
    return !!~can.inArray(cls.model_singular, this.permissions[operation]);
  }

  , not_system_role : function() {
    return this.attr('scope') !== "System";
  }

  , permission_summary : function() {
    if (this.name == "ProgramOwner") return "Owner";
    if (this.name == "ProgramEditor") return "Can Edit";
    if (this.name == "ProgramReader") return "View Only";
    return this.name;
  }

});

can.Model.Cacheable("CMS.Models.MultitypeSearch", {}, {});

can.Model.Cacheable("CMS.Models.BackgroundTask", {
  root_object : "background_task"
  , root_collection : "background_tasks"
  , findAll : "GET /api/background_tasks"
  , findOne : "GET /api/background_tasks/{id}"
  , update : "PUT /api/background_tasks/{id}"
  , destroy : "DELETE /api/background_tasks/{id}"
  , create : "POST /api/background_tasks"
  , scopes : []
  , defaults : {}
}, {
  poll: function() {
    var dfd = new $.Deferred(),
        self = this,
        wait = 2000,
        interval;

    function _poll(){
      self.refresh().then(function(task) {
        // Poll until we either get a success or a failure:
        if (['Success', 'Failure'].indexOf(task.status) < 0) {
          setTimeout(_poll, wait);
        } else {
          dfd.resolve(task);
        }
      });
    }
    _poll();
    return dfd;
  }
});

CMS.Models.get_instance = function(object_type, object_id, params_or_object) {
  var model, params = {}, instance = null, href;

  if(typeof object_type === "object" || object_type instanceof can.Stub) {
    //assume we only passed in params_or_object
    params_or_object = object_type;
    if (!params_or_object)
      return null;
    if (params_or_object instanceof can.Model)
      object_type = params_or_object.constructor.shortName;
    else if (params_or_object instanceof can.Stub)
      object_type = params_or_object.type;
    else if (!params_or_object.selfLink && params_or_object.type)
      object_type = params_or_object.type;
    else {
      href = params_or_object.selfLink || params_or_object.href;
      object_type = can.map(
          window.cms_singularize(/^\/api\/(\w+)\//.exec(href)[1]).split("_"),
          can.capitalize
        ).join("");
    }
    object_id = params_or_object.id;
  }

  model = CMS.Models[object_type];

  if (!model)
    return null;

  if (!object_id)
    return null;

  if (!!params_or_object) {
    if ($.isFunction(params_or_object.serialize))
      $.extend(params, params_or_object.serialize());
    else
      $.extend(params, params_or_object || {});
  }

  instance = model.findInCacheById(object_id);
  if (!instance) {
    if (params.selfLink) {
      params.id = object_id;
      instance = new model(params);
    } else
      instance = new model({
          id: object_id
        , href: (params_or_object || {}).href
        });
  }
  return instance;
};

CMS.Models.get_stub = function (object) {
  var instance = CMS.Models.get_instance(object);
  if (!instance) {
    return;
  }
  return instance.stub();
};

CMS.Models.get_stubs = function (objects) {
  return new can.Stub.List(can.map(CMS.Models.get_instances(objects), function (o) {
    if (!o || !o.stub) {
      console.warn("`Models.get_stubs` instance has no stubs ", arguments);
      return;
    }
    return o.stub();
  }));
};

CMS.Models.get_instances = function (objects) {
  var i, instances = [];
  if (!objects)
    return [];
  for (i=0; i<objects.length; i++) {
    instances[i] = CMS.Models.get_instance(objects[i]);
  }
  return instances;
};

CMS.Models.get_link_type = function(instance, attr) {
  var type
    , model
    ;

  type = instance[attr + "_type"];
  if (!type) {
    model = instance[attr] && instance[attr].constructor;
    if (model)
      type = model.shortName;
    else if (instance[attr])
      type = instance[attr].type;
  }
  return type;
};

})(this.can);
