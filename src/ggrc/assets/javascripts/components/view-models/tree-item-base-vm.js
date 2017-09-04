/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, GGRC) {
  'use strict';

  var TreeViewUtils = GGRC.Utils.TreeView;

  can.Map.extend('GGRC.VM.BaseTreeItemVM', {
    define: {
      expanded: {
        type: Boolean,
        value: false
      }
    },
    instance: null,
    /**
     * Result from mapping
     */
    result: null,
    resultDfd: null,
    limitDepthTree: 0,
    itemSelector: '',
    childModelsList: [],
    /**
     * List of models for show in sub-level for current item.
     */
    selectedChildModels: [],
    initChildTreeDisplay: function () {
      var modelName = this.attr('instance').type;
      var modelsList = TreeViewUtils.getModelsForSubTier(modelName);
      var displayList = modelsList.map(function (model) {
        return {
          widgetName: GGRC.Utils.ObjectVersions
            .getWidgetConfig(model).widgetName,
          name: model,
          display: true
        };
      });

      this.attr('childModelsList', displayList);
      this.attr('selectedChildModels', modelsList);
    },
    setChildModels: function (selected) {
      this.attr('selectedChildModels', selected);
    },
    onExpand: function (event) {
      var isExpanded = this.attr('expanded');

      if (event && isExpanded !== event.state) {
        if (isExpanded !== event.state) {
          this.attr('expanded', event.state);
        }
      } else {
        this.attr('expanded', !isExpanded);
      }
    },
    onPreview: function (event) {
      this.select(event.element);
    },
    select: function ($element) {
      var instance = this.attr('instance');
      var itemSelector = this.attr('itemSelector');

      $element = $element.closest(itemSelector);

      if (instance instanceof CMS.Models.Person && !this.attr('result')) {
        // for Person instances we need to build ResultMapping object before open the info panel
        this.attr('resultDfd').then(function () {
          can.trigger($element, 'selectTreeItem', [$element, instance]);
        });
      } else {
        can.trigger($element, 'selectTreeItem', [$element, instance]);
      }
    }
  });
})(window.can, window.GGRC);
