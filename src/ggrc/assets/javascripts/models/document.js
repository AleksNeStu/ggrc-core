/*!
    Copyright (C) 2017 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

(function (ns, can) {
  can.Model.Cacheable('CMS.Models.Document', {
    root_object: 'document',
    root_collection: 'documents',
    title_singular: 'Reference',
    title_plural: 'References',
    category: 'business',
    findAll: 'GET /api/documents',
    findOne: 'GET /api/documents/{id}',
    create: 'POST /api/documents',
    update: 'PUT /api/documents/{id}',
    destroy: 'DELETE /api/documents/{id}',
    EVIDENCE: 'EVIDENCE',
    URL: 'URL',
    search: function (request, response) {
      return $.ajax({
        type: 'get',
        url: '/api/documents',
        dataType: 'json',
        data: {s: request.term},
        success: function (data) {
          response($.map(data, function (item) {
            return can.extend({}, item.document, {
              label: item.document.title ?
                     item.document.title + (
                        item.document.link_url ?
                        ' (' + item.document.link_url + ')' : '') :
                     item.document.link_url,
              value: item.document.id
            });
          }));
        }
      });
    },
    attributes: {
      context: 'CMS.Models.Context.stub',
      kind: 'CMS.Models.Option.stub',
      year: 'CMS.Models.Option.stub'
    },
    defaults: {
      document_type: 'EVIDENCE'
    },
    tree_view_options: {
      show_view: GGRC.mustache_path + '/documents/tree.mustache',
      add_item_view: GGRC.mustache_path + '/documents/tree_add_item.mustache'
    },
    init: function () {
      this.validateNonBlank('link');
      this._super.apply(this, arguments);
    }
  }, {
    display_type: function () {
      if (_.isEmpty(this.object_documents)) {
        return 'URL';
      }
      return 'Evidence';
    }
  });
})(this, can);
