/*
    Copyright (C) 2017 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

export default can.Model.Cacheable('CMS.Models.Proposal', {
  root_object: 'proposal',
  root_collection: 'proposals',
  table_singular: 'proposal',
  table_plural: 'proposals',

  category: 'governance',
  findOne: 'GET /api/proposals/{id}',
  findAll: 'GET /api/proposals',
  update: 'PUT /api/proposals/{id}',
  destroy: 'DELETE /api/proposals/{id}',
  create: 'POST /api/proposals',
}, {});
