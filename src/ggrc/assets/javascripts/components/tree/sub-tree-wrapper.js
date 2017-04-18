/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, GGRC) {
  'use strict';

  var template = can.view(GGRC.mustache_path +
    '/components/tree/sub-tree-wrapper.mustache');
  var TreeViewUtils = GGRC.Utils.TreeView;
  var CurrentPage = GGRC.Utils.CurrentPage;

  var viewModel = can.Map.extend({
    define: {
      parentModel: {
        type: String,
        get: function () {
          return this.attr('parent').type
        }
      },
      parentId: {
        type: Number,
        get: function () {
          return this.attr('parent').id;
        }
      },
      showAllRelatedLink: {
        type: String,
        get: function () {
          return this.attr('parent') ? this.attr('parent').viewLink : '';
        }
      },
      loading: {
        type: Boolean,
        value: false
      },
      notDirectlyExpanded: {
        type: Boolean,
        value: false
      },
      needToSplit: {
        type: Boolean,
        get: function () {
          return CurrentPage.isObjectContextPage() &&
            CurrentPage.getPageType() !== 'Workflow';
        }
      },
      notResult: {
        type: Boolean,
        value: false
      },
      drawRelated: {
        type: Boolean,
        value: false
      },
      /**
       *
       */
      showMore: {
        type: Boolean,
        value: false
      },
      isOpen: {
        type: Boolean,
        set: function (newValue, setValue) {
          var isReady = this.attr('dataIsReady');

          if (!isReady && newValue) {
            this.loadItems().then(function () {
              setValue(newValue);
            });
          } else {
            setValue(newValue);
          }
        }
      },
      childModels: {
        type: '*',
        set: function (models, setResult) {
          if (!this.attr('dataIsReady')) {
            setResult(models);
          } else if (this.attr('dataIsReady') && !this.attr('isOpen')) {
            this.attr('dataIsReady', false);
            setResult(models);
          } else {
            this.loadItems(models).then(function () {
              setResult(models);
            })
          }
        }
      },
      cssClasses: {
        type: String,
        get: function () {
          var classes = [];

          if (this.attr('loading')) {
            classes.push('loading');
          }

          return classes.join(' ');
        }
      }
    },
    dataIsReady: false,
    limitDepthTree: 0,
    depthFilter: '',
    parent: null,
    directlyItems: [],
    notDirectlyItems: [],
    _loader: null,
    expandNotDirectlyRelated: function () {
      var isExpanded = this.attr('notDirectlyExpanded');
      this.attr('notDirectlyExpanded', !isExpanded);
    },
    /**
     *
     * @param {Array} [models] -
     * @return {*}
     */
    loadItems: function (models) {
      var parentType = this.attr('parentModel');
      var parentId = this.attr('parentId');
      var filter = this.getDepthFilter();

      models = models || this.attr('childModels') || [];
      models = can.makeArray(models);

      if (!models.length) {
        return can.Deferred().resolve();
      }

      this.attr('loading', true);

      return TreeViewUtils
        .loadItemsForSubTier(models, parentType, parentId, filter)
        .then(function (result) {
          this.attr('loading', false);
          this.attr('directlyItems', result.directlyItems);
          this.attr('notDirectlyItems', result.notDirectlyItems);
          this.attr('dataIsReady', true);
          this.attr('showMore', result.showMore);

          if (!result.directlyItems.length && !result.notDirectlyItems.length) {
            this.attr('notResult', true);
          }
        }.bind(this));
    },
    makeResult: function (instance) {
      return this.attr('_loader').getResultFromMapping(instance);
    }
  });

  /**
   *
   */
  GGRC.Components('subTreeWrapper', {
    tag: 'sub-tree-wrapper',
    template: template,
    viewModel: viewModel,
    events: {
      inserted: function () {
        var parent = this.viewModel.attr('parent');

        this.viewModel.attr('_loader',
          new GGRC.ListLoaders.TreeBaseLoader(null, parent));
      }
    }
  });
})(window.can, window.GGRC);
