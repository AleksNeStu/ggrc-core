/*
 * Copyright (C) 2017 Google Inc.
 * Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can) {
  'use strict';

  can.Model.Cacheable('CMS.Models.Threat', {
    root_object: 'threat',
    root_collection: 'threats',
    category: 'risk',
    findAll: 'GET /api/threats',
    findOne: 'GET /api/threats/{id}',
    create: 'POST /api/threats',
    update: 'PUT /api/threats/{id}',
    destroy: 'DELETE /api/threats/{id}',
    mixins: ['unique_title', 'ca_update'],
    is_custom_attributable: true,
    isRoleable: true,
    attributes: {
      context: 'CMS.Models.Context.stub',
      modified_by: 'CMS.Models.Person.stub',
      object_people: 'CMS.Models.ObjectPerson.stubs',
      people: 'CMS.Models.Person.stubs',
      related_sources: 'CMS.Models.Relationship.stubs',
      related_destinations: 'CMS.Models.Relationship.stubs',
      object_objectives: 'CMS.Models.ObjectObjective.stubs',
      objectives: 'CMS.Models.Objective.stubs',
      object_controls: 'CMS.Models.ObjectControl.stubs',
      controls: 'CMS.Models.Control.stubs',
      object_sections: 'CMS.Models.ObjectSection.stubs',
      sections: 'CMS.Models.get_stubs'
    },
    tree_view_options: {
      add_item_view: GGRC.mustache_path +
      '/base_objects/tree_add_item.mustache',
      attr_view: GGRC.mustache_path + '/base_objects/tree-item-attr.mustache',
      attr_list: can.Model.Cacheable.attr_list.concat([
        {attr_title: 'Threat URL', attr_name: 'url'},
        {attr_title: 'Reference URL', attr_name: 'reference_url'}
      ])
    },
    defaults: {
      status: 'Draft'
    },
    statuses: ['Draft', 'Deprecated', 'Active'],
    init: function () {
      if (this._super) {
        this._super.apply(this, arguments);
      }
      this.validatePresenceOf('title');
    }
  }, {});
})(window.can);
