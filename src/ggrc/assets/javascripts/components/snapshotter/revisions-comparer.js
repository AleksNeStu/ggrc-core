/*!
 Copyright (C) 2016 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */
(function (can, $) {
  'use strict';

  GGRC.Components('RevisionsComparer', {
    tag: 'revisions-comparer',
    template: '<content/>',
    scope: {
      instance: null,
      leftRevisionId: null,
      rightRevisions: [],
      compareIt: function (scope, el, ev) {
        var view = scope.instance.view;
        var that = this;
        var currentRevisionID = scope.leftRevisionId;
        var rightRevisions = scope.rightRevisions;
        var revisionsLength = rightRevisions.length;
        var newRevisionID;
        if (!currentRevisionID || !rightRevisions || !revisionsLength) {
          scope.instance.snapshot = scope.instance.snapshot.reify();
          currentRevisionID = scope.instance.snapshot.revision_id;
          rightRevisions = scope.instance.snapshot.revisions;
          revisionsLength = rightRevisions.length;
        }
        newRevisionID = rightRevisions[revisionsLength - 1].id;
        GGRC.Controllers.Modals.confirm({
          modal_title: 'Compare with the latest version',
          modal_description: 'Loading...',
          header_view: GGRC.mustache_path +
                        '/modals/modal_compare_header.mustache',
          modal_confirm: 'Update',
          skip_refresh: true,
          extraCssClass: 'compare-modal',
          button_view: GGRC.mustache_path +
                        '/modals/prompt_buttons.mustache',
          afterFetch: function (target) {
            that.getRevisions(currentRevisionID, newRevisionID)
              .then(function (data) {
                var revisions = that.prepareInstances(data);
                var fragLeft = can.view(view, revisions[0]);
                var fragRight = can.view(view, revisions[1]);
                fragLeft.appendChild(fragRight);
                target.find('.modal-body').html(fragLeft);
                that.highlightDifference(target);
              });
          }
        }, this.updateRevision.bind(this));
      },
      getRevisions: function (currentRevisionID, newRevisionID) {
        var additionalFilter = {
          expression: {
            op: {name: 'OR'},
            left: {
              op: {name: '='},
              left: 'id',
              right: currentRevisionID
            },
            right: {
              op: {name: '='},
              left: 'id',
              right: newRevisionID
            }
          }
        };
        var params = GGRC.Utils.QueryAPI.buildParam(
          'Revision',
          {},
          undefined,
          undefined,
          additionalFilter
        );
        return can.Model.Cacheable.query({data: [params]});
      },
      prepareInstances: function (data) {
        return data.Revision.values.map(function (value) {
          var content = value.content;
          var model = CMS.Models[value.resource_type];
          content.isRevision = true;
          content.type = value.resource_type;
          return {instance: new model(content)};
        });
      },
      updateRevision: function () {
        var instance = this.instance.snapshot;
        instance.refresh().then(function () {
          instance.attr('update_revision', 'latest');
          return instance.save();
        }).then(function () {
          GGRC.Utils.Browser.refreshPage(true);
        });
      },

      /**
       * Get Infopanes from modal
       * @param {Object} $target - jQuery object
       * @return {Object} - jQuery object
       */
      getInfopanes: function ($target) {
        return $target.find('.info .tier-content');
      },

      /**
       * Get Attributes from infopanes
       * @param {Object} $infoPanes - jQuery object of infopanes
       * @param {Number} index - index of infopane
       * @return {Object} - jQuery object
       */
      getAttributes: function ($infoPanes, index) {
        var selector = '.row-fluid h6 + *, .row-fluid .state-value';
        return $($infoPanes[index]).find(selector);
      },

      /**
       * Get Custom Attribute panes from modal
       * @param {Object} $target - jQuery object
       * @return {Object} - jQuery object
       */
      getCAPanes: function ($target) {
        return $target.find('.info custom-attributes');
      },

      /**
       * Get Custom Attributes from infopanes
       * @param {Object} CAPanes - jQuery object of CA panes
       * @param {Number} index - index of CA pane
       * @return {Object} - jQuery object
       */
      getCAs: function (CAPanes, index) {
        return $(CAPanes[index]).find('[data-custom-attribute] inline-edit');
      },

      /**
       * Highlight difference
       * @param {Object} $target - jQuery object
       */
      highlightDifference: function ($target) {
        this.highlightAttributes($target);
        this.highlightCustomAttributes($target);
      },

      /**
       * Highlight difference in attributes
       * @param {Object} $target - jQuery object
       */
      highlightAttributes: function ($target) {
        var emptySelector = '.empty-message';
        var highlightClass = 'diff-highlighted';
        var listSelector = 'ul li';
        var infoPanes = this.getInfopanes($target);
        var valuesOld = this.getAttributes(infoPanes, 0);
        var valuesNew = this.getAttributes(infoPanes, 1);

        valuesOld.each(function (index, valueOld) {
          var $valueNew = $(valuesNew[index]);
          var $valueOld = $(valueOld);
          var listOld = [];
          var listNew = [];
          if ($valueOld.html() !== $valueNew.html()) {
            listOld = $valueOld.find(listSelector);
            listNew = $valueNew.find(listSelector);
            if (listOld.length) {
              highlightLists(listOld, listNew);
            } else {
              highlightValues($valueOld);
              highlightValues($valueNew);
            }
            equalValuesHeight($valueOld, $valueNew);
          }
        });

        /**
         * Highlight difference in two DOM lists
         * @param {Object} listFirst - DOM object
         * @param {Object} listLast - DOM object
         */
        function highlightLists(listFirst, listLast) {
          compareLists(listFirst, listLast);
          compareLists(listLast, listFirst);
        }

        /**
         * Compare DOM lists
         * @param {Object} liFirst - DOM object
         * @param {Object} liLast - DOM object
         */
        function compareLists(liFirst, liLast) {
          liFirst.each(function (i, li) {
            var atLeastOneIsEqual = false;
            liLast.each(function (j, li2) {
              if (li.innerHTML === li2.innerHTML) {
                atLeastOneIsEqual = true;
              }
            });
            if (!atLeastOneIsEqual) {
              $(li).addClass(highlightClass);
            }
          });
        }

        /**
         * Highlight difference in simple values
         * @param {Object} $value - jQuery object
         */
        function highlightValues($value) {
          if ($value.html() && !$value.find(emptySelector).length) {
            $value.addClass(highlightClass);
          }
        }

        /**
         * Set max height between two jQuery objects
         * @param {Object} $firstItem - jQuery object
         * @param {Object} $secondItem - jQuery object
         */
        function equalValuesHeight($firstItem, $secondItem) {
          var firstItemHeight = $firstItem.outerHeight();
          var secondItemHeight = $secondItem.outerHeight();
          if (firstItemHeight > secondItemHeight) {
            $secondItem.outerHeight(firstItemHeight);
          } else if (firstItemHeight < secondItemHeight) {
            $firstItem.outerHeight(secondItemHeight);
          }
        }
      },

      /**
       * Highlight difference in custom attributes
       * @param {Object} $target - jQuery object
       */
      highlightCustomAttributes: function ($target) {
        var titleSelector = '.inline-edit__title';
        var valueSelector = '.inline-edit__content';
        var highlightClass = 'diff-highlighted';
        var caSelector = '[data-custom-attribute]';
        var caWrapperSelector = '.span6';
        var cas = this.getCAPanes($target);
        var ca0s = this.getCAs(cas, 0);
        var ca1s = this.getCAs(cas, 1);
        compareCA(ca0s, ca1s);
        compareCA(ca1s, ca0s);

        /**
         * Compare two lists of custom attributes
         * @param {Object} caFirst - jQuery object
         * @param {Object} caLast - jQuery object
         */
        function compareCA(caFirst, caLast) {
          var prevIndex = -1;
          caFirst.each(function (i, caOld) {
            var $sameCA = [];
            var $caOld = $(caOld);
            var caOldScope = $caOld.viewModel();
            caLast.each(function (j, caNew) {
              var $caNew = $(caNew);
              var caNewScope = $caNew.viewModel();
              if (caNewScope.caId === caOldScope.caId) {
                $sameCA = $caNew;
                prevIndex = j;
              }
            });
            if ($sameCA.length) {
              highlightProperty('title', $sameCA, $caOld, titleSelector);
              highlightProperty('value', $sameCA, $caOld, valueSelector);
              equalCAHeight($caOld, $sameCA);
            } else {
              fillEmptyCA(caLast, $caOld, prevIndex);
            }
          });
        }

        /**
         * Highlight specific property in custom attributes
         * @param {String} name - Property name
         * @param {Object} $caFirst - jQuery object
         * @param {Object} $caLast - jQuery object
         * @param {String} selector - child selector to add class
         */
        function highlightProperty(name, $caFirst, $caLast, selector) {
          var caFirstScope = $caFirst.viewModel();
          var caLastScope = $caLast.viewModel();
          if (caFirstScope[name] !== caLastScope[name]) {
            if (caFirstScope[name]) {
              $caFirst.find(selector).addClass(highlightClass);
            }
            if (caLastScope[name]) {
              $caLast.find(selector).addClass(highlightClass);
            }
          }
        }

        /**
         * Set max height between two custom attributes
         * @param {Object} $caFirst - jQuery object
         * @param {Object} $caLast - jQuery object
         */
        function equalCAHeight($caFirst, $caLast) {
          var caFirstHeight = $caFirst.closest(caSelector).outerHeight();
          var caLastHeight = $caLast.closest(caSelector).outerHeight();
          if (caFirstHeight > caLastHeight) {
            $caLast.closest(caSelector).outerHeight(caFirstHeight);
          } else if (caFirstHeight < caLastHeight) {
            $caFirst.closest(caSelector).outerHeight(caLastHeight);
          }
        }

        /**
         * Fill empty space when CA is not existing
         * @param {Object} caList - List of CA
         * @param {Object} $ca - jQuery object Current attribute
         * @param {Number} index - Index of previous the same attribute
         */
        function fillEmptyCA(caList, $ca, index) {
          var caOldHeight;
          caOldHeight = $ca
                          .closest(caWrapperSelector)
                          .outerHeight(true);
          if (index === -1) {
            $(caList.context).css('padding-top', '+=' + caOldHeight);
          } else {
            $(caList[index])
                    .closest(caWrapperSelector)
                    .css('margin-bottom', '+=' + caOldHeight);
          }
          $ca.closest(caSelector).addClass(highlightClass);
        }
      }
    }
  });
})(window.can, window.can.$);
