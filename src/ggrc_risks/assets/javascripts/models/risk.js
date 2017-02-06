/*
 * Copyright (C) 2017 Google Inc.
 * Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */


(function(can) {

  can.Model.Cacheable("CMS.Models.Risk", {
    root_object: "risk",
    root_collection: "risks",
    category: "risk",
    findAll: "GET /api/risks",
    findOne: "GET /api/risks/{id}",
    create: "POST /api/risks",
    update: "PUT /api/risks/{id}",
    destroy: "DELETE /api/risks/{id}",
    mixins: ['ownable', 'contactable', 'unique_title', 'ca_update'],
    is_custom_attributable: true,
    attributes : {
      context : "CMS.Models.Context.stub",
      contact : "CMS.Models.Person.stub",
      owners : "CMS.Models.Person.stubs",
      modified_by : "CMS.Models.Person.stub",
      objects : "CMS.Models.get_stubs",
      risk_objects: "CMS.Models.RiskObject.stubs"
    },
    tree_view_options: {
      add_item_view : GGRC.mustache_path + "/base_objects/tree_add_item.mustache"
    },
    defaults: {
      status: 'Draft'
    },
    statuses: ['Draft', 'Deprecated', 'Active'],
    init: function () {
      this._super && this._super.apply(this, arguments);
      var req_fields = ["title", "description", "contact"];
      for (var i = 0; i < req_fields.length; i++) {
        this.validatePresenceOf(req_fields[i]);
      }
    }
  }, {});

})(window.can);
