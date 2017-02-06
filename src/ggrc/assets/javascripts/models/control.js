/*!
    Copyright (C) 2017 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

(function (namespace, $) {
  can.Model.Cacheable('CMS.Models.Control', {
  // static properties
    root_object: 'control',
    root_collection: 'controls',
    category: 'governance',
    findAll: 'GET /api/controls',
    findOne: 'GET /api/controls/{id}',
    create: 'POST /api/controls',
    update: 'PUT /api/controls/{id}',
    destroy: 'DELETE /api/controls/{id}',
    mixins: ['ownable', 'contactable', 'unique_title', 'ca_update',
             'timeboxed'],
    is_custom_attributable: true,
    attributes: {
      context: 'CMS.Models.Context.stub',
      owners: 'CMS.Models.Person.stubs',
      modified_by: 'CMS.Models.Person.stub',
      object_people: 'CMS.Models.ObjectPerson.stubs',
      people: 'CMS.Models.Person.stubs',
      categories: 'CMS.Models.ControlCategory.stubs',
      assertions: 'CMS.Models.ControlAssertion.stubs',
      objectives: 'CMS.Models.Objective.stubs',
      directive: 'CMS.Models.Directive.stub',
      audit_objects: 'CMS.Models.AuditObject.stubs',
      sections: 'CMS.Models.get_stubs',
      programs: 'CMS.Models.Program.stubs',
      kind: 'CMS.Models.Option.stub',
      means: 'CMS.Models.Option.stub',
      verify_frequency: 'CMS.Models.Option.stub',
      principal_assessor: 'CMS.Models.Person.stub',
      secondary_assessor: 'CMS.Models.Person.stub',
      custom_attribute_values: 'CMS.Models.CustomAttributeValue.stubs'
    },
    links_to: {},
    defaults: {
      selected: false,
      title: '',
      slug: '',
      description: '',
      url: '',
      status: 'Draft'
    },
    tree_view_options: {
      show_view: GGRC.mustache_path + '/controls/tree.mustache',
      footer_view: GGRC.mustache_path + '/base_objects/tree_footer.mustache',
      attr_list: can.Model.Cacheable.attr_list.concat([
        {attr_title: 'URL', attr_name: 'url'},
        {attr_title: 'Reference URL', attr_name: 'reference_url'},
        {attr_title: 'Effective Date', attr_name: 'start_date'},
        {attr_title: 'Stop Date', attr_name: 'end_date'},
        {attr_title: 'Kind/Nature', attr_name: 'kind',
          attr_sort_field: 'kind.title'},
        {attr_title: 'Fraud Related ', attr_name: 'fraud_related'},
        {attr_title: 'Significance', attr_name: 'significance'},
        {attr_title: 'Type/Means', attr_name: 'means',
          attr_sort_field: 'means.title'},
        {attr_title: 'Frequency', attr_name: 'frequency',
          attr_sort_field: 'frequency.title'},
        {attr_title: 'Assertions', attr_name: 'assertions'},
        {attr_title: 'Categories', attr_name: 'categories'},
        {attr_title: 'Principal Assignee', attr_name: 'principal_assessor',
          attr_sort_field: 'principal_assessor.name|email'},
        {attr_title: 'Secondary Assignee', attr_name: 'secondary_assessor',
          attr_sort_field: 'secondary_assessor.name|email'}
      ]),
      add_item_view: GGRC.mustache_path + '/controls/tree_add_item.mustache',
      draw_children: true,
      child_options: [{
        model: can.Model.Cacheable,
        mapping: 'related_objects', // 'related_and_able_objects'
        footer_view: GGRC.mustache_path + '/base_objects/tree_footer.mustache',
        add_item_view: GGRC.mustache_path +
        '/base_objects/tree_add_item.mustache',
        title_plural: 'Business Objects',
        draw_children: false
      }]
    },
    statuses: ['Draft', 'Deprecated', 'Active'],
    init: function () {
      this.validateNonBlank('title');
      this._super.apply(this, arguments);
    }
  }, {
    init: function () {
      var that = this;
      this._super.apply(this, arguments);
      this.bind('change', function (ev, attr, how, newVal, oldVal) {
        // Emit the 'orphaned' event when the directive attribute is removed
        if (attr === 'directive' && how === 'remove' && oldVal &&
          newVal === undefined) {
          // It is necessary to temporarily add the attribute back for orphaned
          // processing to work properly.
          that.directive = oldVal;
          can.trigger(that.constructor, 'orphaned', that);
          delete that.directive;
        }
      });
    }
  });
})(this, can.$);
