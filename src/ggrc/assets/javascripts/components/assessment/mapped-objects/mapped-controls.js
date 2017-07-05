/*!
 Copyright (C) 2017 Google Inc., authors, and contributors
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, GGRC, _) {
  'use strict';

  var tpl = can.view(GGRC.mustache_path +
    '/components/assessment/mapped-objects/' +
    'mapped-controls.mustache');
  var tag = 'assessment-mapped-controls';

  /*
   Default Response Object
   */
  var defaultResponseArr = [{
    Snapshot: {
      values: []
    }
  }, {
    Snapshot: {
      values: []
    }
  }];
  /**
   * ViewModel for Assessment Mapped Controls Popover.
   * @type {can.Map}
   */
  var viewModel = can.Map.extend({
    define: {
      /**
       * Private Attribute defining array of requested Objects, Types and Fields of Objects
       * @type {Array}
       * @private
       */
      queries: {
        type: '*',
        value: [
          {
            type: 'objectives',
            objName: 'Objective',
            fields: ['child_type', 'revision', 'parent']
          },
          {
            type: 'regulations',
            objName: 'Regulation',
            fields: ['child_type', 'revision', 'parent']
          }
        ]
      },
      /**
       * Attribute to indicate loading state
       * @private
       */
      isLoading: {
        type: 'boolean',
        value: false
      },
      objectives: {
        value: []
      },
      regulations: {
        value: []
      },
      customAttributes: {
        value: []
      },
      state: {
        value: {}
      },
      mappedItems: {
        set: function (newArr) {
          return newArr.map(function (item) {
            return {
              isSelected: false,
              instance: item
            };
          });
        }
      }
    },
    titleText: '@',
    mapping: '@',
    mappingType: '@',
    selectedItem: {},
    snapshot: {},
    /**
     * Generate params required for Query API
     * @param {Number} id - Id of Control's Snapshot
     * @return {Object} request query object
     */
    getParams: function (id) {
      var params = {};
      // Right now we load only Snapshots of related Objectives and Regulations
      var relevant = {
        type: 'Snapshot',
        id: id,
        operation: 'relevant'
      };
      params.data = this.attr('queries')
        .map(function (query) {
          var resultingQuery = GGRC.Utils.QueryAPI
            .buildParam(query.objName, {}, relevant, query.fields);
          return GGRC.Utils.Snapshots.transformQuery(resultingQuery);
        });
      return params;
    },
    /**
     * Parse raw response data from Query API and set appropriate properties
     * @param {Array} responseArr - Raw Array of Data requested from Query API
     */
    setItems: function (responseArr) {
      responseArr.forEach(function (item, i) {
        // Order of items in Queries Object is the same as order of Requested Queries
        var type = this.attr('queries')[i].type;
        this.attr(type).replace(item.Snapshot.values
          .map(function (item) {
            return GGRC.Utils.Snapshots.toObject(item);
          }));
      }.bind(this));
    },
    loadItems: function () {
      var id = this.attr('selectedItem.data.id');
      var params;

      if (!id) {
        this.setItems(defaultResponseArr);
        return;
      }
      params = this.getParams(id);

      this.attr('isLoading', true);

      GGRC.Utils.QueryAPI
        .makeRequest(params)
        .done(this.setItems.bind(this))
        .fail(function () {
          $(document.body).trigger('ajax:flash',
            {
              error: 'Failed to fetch related objects.'
            });
          this.setItems(defaultResponseArr);
        }.bind(this))
        .always(function () {
          this.attr('isLoading', false);
        }.bind(this));
    },
    attributesToFormFields: function (snapshot) {
      var attributes;
      attributes = GGRC.Utils.CustomAttributes.prepareCustomAttributes(
        snapshot.custom_attribute_definitions,
        snapshot.custom_attribute_values)
        .map(GGRC.Utils.CustomAttributes.convertToFormViewField);
      return attributes;
    }
  });
  /**
   * Assessment specific mapped controls view component
   */
  GGRC.Components('assessmentMappedControl', {
    tag: tag,
    template: tpl,
    viewModel: viewModel,
    events: {
      '{viewModel} selectedItem.data': function () {
        var item = this.viewModel.attr('selectedItem.data');
        var attributes;
        if (item) {
          this.viewModel.loadItems();
          attributes = this.viewModel.attributesToFormFields(
            item.attr('revision.content'));
          this.viewModel.attr('customAttributes', attributes);
          this.viewModel.attr('snapshot',
            GGRC.Utils.Snapshots.toObject(item));
          this.viewModel.attr('state.open', true);
        }
      }
    }
  });
})(window.can, window.GGRC, window._);
