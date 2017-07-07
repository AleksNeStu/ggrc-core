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
                var attachmentsDfds =
                  that.isContainsAttachments(that.instance) ?
                  that.getAttachmentsDfds(revisions) :
                  [];
                fragLeft.appendChild(fragRight);

                target.find('.modal-body').html(fragLeft);
                that.highlightDifference(target);

                if (attachmentsDfds.length) {
                  $.when.apply($, attachmentsDfds).then(function () {
                    that.highlightDifference(target);
                  });
                }
              });
          }
        }, this.updateRevision.bind(this));
      },
      buildAttachmentsDfd: function (instance, bindingName) {
        var dfd = new can.Deferred();
        instance.bind(bindingName, function (target, isLoaded) {
          if (isLoaded) {
            dfd.resolve();
          } else {
            dfd.reject();
          }

          instance.unbind(bindingName);
        });

        return dfd;
      },
      getAttachmentsDfds: function (revisions) {
        var dfds = [];
        var that = this;

        if (!revisions) {
          return [];
        }

        revisions.forEach(function (revision) {
          var instance = revision.attr('instance');

          if (instance.folders && instance.folders.length) {
            dfds.push(
              that.buildAttachmentsDfd(instance, 'isRevisionFolderLoaded'));
          }
        });

        return dfds;
      },
      isContainsAttachments: function (instance) {
        return instance.type === 'Control';
      },
      getRevisions: function (currentRevisionID, newRevisionID) {
        var Revision = CMS.Models.Revision;
        var notCached = [];
        var cached = [currentRevisionID, newRevisionID].map(function (id) {
          var cache = Revision.store ? Revision.store[id] : undefined;
          if (!cache) {
            notCached.push(id);
          }
          return cache;
        }).filter(function (revision) {
          return !!revision;
        });
        var result;

        if (cached.length === 2) {
          result = can.when(cached);
        } else if (cached.length === 1) {
          result = can.when(cached[0], Revision.findOne({id: notCached[0]}))
            .then(function () {
              return can.makeArray(arguments);
            });
        } else {
          result = Revision.findAll({
            id__in: notCached.join(',')
          });
        }

        return result.then(function (revisions) {
          return new can.List(_.sortBy(revisions, 'id'));
        });
      },
      prepareInstances: function (data) {
        return data.map(function (value) {
          var content = value.content;
          var model = CMS.Models[value.resource_type];
          content.attr('isRevision', true);
          content.attr('type', value.resource_type);
          content.attr('isRevisionFolderLoaded', false);

          if (content.access_control_list) {
            content.access_control_list.forEach(function (item) {
              var stub = new CMS.Models.Person({id: item.person_id}).stub();
              item.attr('person', stub);
            });
          }

          return {instance: new model(content), isSnapshot: true};
        });
      },
      updateRevision: function () {
        var instance = new CMS.Models.Snapshot(this.instance.snapshot);
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
        var selector = '.row-fluid h6 + *, .row-fluid .state-value' +
          ', related-documents';
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
        this.highlightCustomRoles($target);
      },

      /**
       * Highlight difference in attributes
       *
       * @param {jQuery} $target - the root DOM element containing the
       *   revision diff comparison
       */
      highlightAttributes: function ($target) {
        var emptySelector = '.empty-message';
        var highlightClass = 'diff-highlighted';
        var listSelector = 'ul li, .object-list-item';
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
       *
       * @param {jQuery} $target - the root DOM element containing the
       *   revision diff comparison
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
              highlightProperty('titleText', $sameCA, $caOld, titleSelector);
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
          var firstProp = caFirstScope[name].id || caFirstScope[name];
          var lastProp = caLastScope[name].id || caLastScope[name];
          if (firstProp !== lastProp) {
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
      },

      /**
       * Highlight the differences in custom roles assignments between the
       * old and the new revision of an object.
       *
       * @param {jQuery} $target - the root DOM element containing the
       *   revision diff comparison pane
       */
      highlightCustomRoles: function ($target) {
        var HIGHLIGHT_CLASS = 'diff-highlighted';

        var $rolesPanes = $target
          .find('related-people-access-control');
        var $roleBlocksOld = $rolesPanes.eq(0)
          .find('related-people-access-control-group');
        var $roleBlocksNew = $rolesPanes.eq(1)
          .find('related-people-access-control-group');

        $roleBlocksOld.each(function (i) {
          var $blockOld = $roleBlocksOld.eq(i);
          var $blockNew = $roleBlocksNew.eq(i);  // the block count is the same
          compareRoleBlocks($blockOld, $blockNew);
          equalizeHeights($blockOld, $blockNew);
        });

        /**
         * Compare two blocks of grants of a particular custom role and mark
         * the differences between them.
         *
         * @param {jQuery} $blockOld - a DOM element containing a list of
         *   people that had a particular custom role granted at a particular
         *   moment in the past
         * @param {jQuery} $blockNew - a DOM element containing a list of
         *   people that have a particular custom role granted at a newer point
         *   in time
         */
        function compareRoleBlocks($blockOld, $blockNew) {
          var oldUserIds = {};
          var newUserIds = {};

          var $oldGrantees = $blockOld.find('person-list-item');
          var $newGrantees = $blockNew.find('person-list-item');

          oldUserIds = extractPeopleIds($oldGrantees);
          newUserIds = extractPeopleIds($newGrantees);

          // now we have a list of old and new person IDs
          highlightChanges($oldGrantees, newUserIds);
          highlightChanges($newGrantees, oldUserIds);
        }

        /**
         * Extract the IDs of the people that have a particular custom role
         * granted to them.
         *
         * @param {jQuery} $grantees - a list of DOM elements representing the
         *   grants of a particular custom role to people
         * @return {Object} - the list of people IDs as object keys
         */
        function extractPeopleIds($grantees) {
          var peopleIds = {};
          $grantees.each(function (i, personInfo) {
            var personId = $(personInfo)
              .viewModel().attr('person.id');
            peopleIds[personId] = true;
          });
          return peopleIds;
        }

        /**
         * Highlight the changes in role assignments.
         *
         * @param {jQuery} $grantees - a list of DOM elements representing the
         *   grants of a particular custom role to people
         * @param {Object} comparisonIds - a set of people IDs representing a
         *   referential list of grants of a particular custom role. The changes
         *   in role assignments are calculated against this list.
         */
        function highlightChanges($grantees, comparisonIds) {
          $grantees.each(function (i, grantee) {
            var $grantee = $(grantee);
            var personId = $grantee.viewModel().attr('person.id');

            if (!(personId in comparisonIds)) {
              $grantee.addClass(HIGHLIGHT_CLASS);
            }
          });
        }

        /**
         * Adjust the heights of two DOM elements to the higher one's height.
         *
         * @param {jQuery} $block - the first block element
         * @param {jQuery} $block2 - the second block element
         */
        function equalizeHeights($block, $block2) {
          var height = $block.outerHeight();
          var height2 = $block2.outerHeight();

          $block.css('max-width', 'none');
          $block2.css('max-width', 'none');
          $block.css('margin-right', '0');
          $block2.css('margin-right', '0');

          if (height > height2) {
            $block2.outerHeight(height);
          } else if (height < height2) {
            $block.outerHeight(height2);
          }
        }
      }
    }
  });
})(window.can, window.can.$);
