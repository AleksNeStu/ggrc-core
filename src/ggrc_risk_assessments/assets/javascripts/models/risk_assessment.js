/*
 * Copyright (C) 2017 Google Inc.
 * Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

/*
 */

(function (can) {
  var path = GGRC.mustache_path + "/risk_assessments";

  can.Model.Cacheable("CMS.Models.RiskAssessment", {
    root_object: "risk_assessment",
    root_collection: "risk_assessments",
    category: "risk_assessment",
    mixins: ['ca_update', 'timeboxed'],
    findAll: "GET /api/risk_assessments",
    findOne: "GET /api/risk_assessments/{id}",
    create: "POST /api/risk_assessments",
    update: "PUT /api/risk_assessments/{id}",
    destroy: "DELETE /api/risk_assessments/{id}",
    is_custom_attributable: true,
    attributes: {
      ra_manager: "CMS.Models.Person.stub",
      ra_counsel: "CMS.Models.Person.stub",
      context: "CMS.Models.Context.stub",
      documents: "CMS.Models.Document.stubs",
      program: "CMS.Models.Program.stub",
      modified_by: "CMS.Models.Person.stub",
      object_documents: "CMS.Models.ObjectDocument.stubs",
      custom_attribute_values : "CMS.Models.CustomAttributeValue.stubs"
    },
    tree_view_options: {
      attr_list: [
        {attr_title: 'Title', attr_name: 'title'},
        {attr_title: 'Code', attr_name: 'slug'},
        {attr_title: 'Start Date', attr_name: 'start_date'},
        {attr_title: 'Stop Date', attr_name: 'end_date'},
        {
          attr_title: 'Risk Manager',
          attr_name: 'ra_manager',
          attr_sort_field: 'ra_manager'
        },
        {
          attr_title: 'Risk Counsel',
          attr_name: 'ra_counsel',
          attr_sort_field: 'ra_counsel'
        }
      ],
      add_item_view: path + '/tree_add_item.mustache'
    },
    init: function () {
      this._super && this._super.apply(this, arguments);
      this.validateNonBlank("title");
      this.validateNonBlank("start_date");
      this.validateNonBlank("end_date");
    }
  }, {
    save: function () {
      // Make sure the context is always set to the parent program
      if (!this.context || !this.context.id) {
        this.attr('context', this.program.reify().context);
      }
      return this._super.apply(this, arguments);
    }
  });

})(window.can);
