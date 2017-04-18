/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, GGRC) {
  'use strict';

  var template = can.view(GGRC.mustache_path +
    '/components/tree/tree-item.mustache');
  var BaseTreeItemVM = GGRC.VM.BaseTreeItemVM;
  var viewModel = BaseTreeItemVM.extend({
    define: {
      extraClasses: {
        type: String,
        get: function () {
          var classes = [];
          var instance = this.attr('instance');

          if (instance.snapshot) {
            classes.push('snapshot');
          }

          if (instance.workflow_state) {
            classes.push('t-' + instance.workflow_state);
          }

          if (this.attr('expanded')) {
            classes.push('open-item');
          }

          return classes.join(' ');
        }
      },
      selectableSize: {
        type: Number,
        get: function () {
          var attrCount = this.attr('selectedColumns').length;
          var result = 3;

          if (attrCount < 4) {
            result = 1;
          } else if (attrCount < 7) {
            result = 2;
          }

          return result;
        }
      }
    },
    selectedColumns: [],
    mandatory: [],
    disableConfiguration: null,
    itemSelector: '.tree-item-content'
  });

  /**
   *
   */
  GGRC.Components('treeItem', {
    tag: 'tree-item',
    template: template,
    viewModel: viewModel,
    events: {
      inserted: function () {
        var viewModel = this.viewModel;
        var instance = viewModel.attr('instance');
        var resultDfd;

        if (instance instanceof CMS.Models.Person) {
          resultDfd = viewModel.makeResult(instance).then(function (result) {
            viewModel.attr('result', result);
          });

          viewModel.attr('resultDfd', resultDfd);
        }

        viewModel.initChildTreeDisplay();
      },
      ' childModelsChange': function (el, ev, selectedModels) {
        ev.stopPropagation();
        this.viewModel.setChildModels(selectedModels);
      }
    }
  });
})(window.can, window.GGRC);
