/*
 Copyright (C) 2018 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

import './advanced-search-mapping-group';
import './advanced-search-mapping-criteria';
import './advanced-search-filter-operator';
import AdvancedSearchContainer from '../view-models/advanced-search-container-vm';
import * as AdvancedSearch from '../../plugins/utils/advanced-search-utils';
import template from './advanced-search-mapping-container.mustache';

/**
 * Mapping Container view model.
 * Contains logic used in Mapping Container component
 * @constructor
 */
let viewModel = AdvancedSearchContainer.extend({
  /**
   * Contains specific model name.
   * @type {string}
   * @example
   * Section
   * Regulation
   */
  modelName: null,
  /**
   * Adds Mapping Criteria and Operator to the collection.
   * Adds only Mapping Criteria if collection is empty.
   */
  addMappingCriteria: function () {
    let items = this.attr('items');
    if (items.length) {
      items.push(AdvancedSearch.create.operator('AND'));
    }
    items.push(AdvancedSearch.create.mappingCriteria());
  },
  /**
   * Transforms Mapping Criteria to Mapping Group.
   * @param {can.Map} criteria - Mapping Criteria.
   */
  createGroup: function (criteria) {
    let items = this.attr('items');
    let index = items.indexOf(criteria);
    items.attr(index, AdvancedSearch.create.group([
      criteria,
      AdvancedSearch.create.operator('AND'),
      AdvancedSearch.create.mappingCriteria(),
    ]));
  },
  /**
   * Indicates whether 'Add' button should be displayed.
   */
  showAddButton: {
    type: 'boolean',
    value: true,
  },
  /**
   * Indicates that it is in assessment-template-clone-modal
   * @type {boolean}
   */
  isClone: false,
});

/**
 * Mapping Container is a component allowing to compose Mapping Criteria, Groups and Operators.
 */
export default can.Component.extend({
  tag: 'advanced-search-mapping-container',
  template: template,
  viewModel: viewModel,
});
