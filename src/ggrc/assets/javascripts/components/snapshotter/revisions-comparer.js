/*!
 Copyright (C) 2016 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

import {confirm} from '../../plugins/utils/modals';
import {prepareCustomAttributes} from '../../plugins/utils/ca-utils';
import RefreshQueue from '../../models/refresh_queue';

export default can.Component.extend({
  tag: 'revisions-comparer',
  template: '<content/>',
  viewModel: {
    instance: null,
    leftRevisionId: null,
    rightRevision: null,
    buttonView: null,
    modalConfirm: null,
    modalTitle: null,
    compareIt: function () {
      const view = this.attr('instance.view');
      const that = this;
      const currentRevisionID = this.attr('leftRevisionId');
      const rightRevision = this.attr('rightRevision');
      const newRevisionID = rightRevision.id;
      confirm({
        modal_title: this.attr('modalTitle'),
        modal_description: 'Loading...',
        header_view: GGRC.mustache_path +
                      '/modals/modal_compare_header.mustache',
        modal_confirm: this.attr('modalConfirm'),
        skip_refresh: true,
        extraCssClass: 'compare-modal',
        button_view: this.attr('buttonView'),
        instance: this.attr('instance'),
        rightRevision: rightRevision,
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

              // people should be preloaded before highlighting differences
              // to avoid breaking UI markup as highlightDifference
              // sets block's height
              that.loadACLPeople(revisions[1].instance)
                .then(() => {
                  fragLeft.appendChild(fragRight);
                  target.find('.modal-body').html(fragLeft);

                  that.highlightDifference(target);
                  that.highlightCustomAttributes(target, revisions);
                })
                .then(() => {
                  if (attachmentsDfds.length) {
                    $.when(...attachmentsDfds).then(() => {
                      that.highlightDifference(target);
                    });
                  }
                });
            });
        },
      }, this.updateRevision.bind(this));
    },
    /**
     * Loads to cache people from access control list
     *
     * @param {Object} instance - revision
     * @return {Promise}
     */
    loadACLPeople: function (instance) {
      let refreshQueue = new RefreshQueue();

      instance.attr('access_control_list').forEach((acl) => {
        let person = CMS.Models.Person.findInCacheById(acl.person.id) || {};
        if (!person.email) {
          refreshQueue.enqueue(acl.person);
        }
      });

      if (refreshQueue.objects.length) {
        return refreshQueue.trigger();
      }
      return can.Deferred().resolve();
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

        if (instance.folder) {
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
        var cache = Revision.findInCacheById(id);
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

      // close info-pane
      $('info-pin-buttons:visible [data-trigger="close"]')
        .first()
        .trigger('click');

      instance.refresh()
      .then(function () {
        instance.attr('update_revision', 'latest');
        return instance.save();
      })
      .then(function () {
        var forceRefresh = true;

        return $('tree-widget-container:visible')
          .first()
          .viewModel()
          .display(forceRefresh);
      })
      .then(function () {
        var message = instance.child_type +
        ' was refreshed successfully.';
        GGRC.Errors.notifier('success', [message]);
      });
    },

    /**
     * Highlight difference
     * @param {Object} $target - jQuery object
     */
    highlightDifference: function ($target) {
      this.highlightAttributes($target);
      this.highlightCustomRoles($target);
    },

    /**
     * Highlight difference in attributes
     *
     * @param {jQuery} $target - the root DOM element containing the
     *   revision diff comparison
     */
    highlightAttributes: function ($target) {
      const emptySelector = '.empty-message';
      const highlightClass = 'diff-highlighted';
      const listSelector = 'ul li, .object-list-item';
      const attributesSelector = '.row-fluid h6 + *, .row-fluid .state-value' +
        ', related-documents';
      var infoPanes = $target.find('.info .tier-content');
      var valuesOld = infoPanes.eq(0).find(attributesSelector);
      var valuesNew = infoPanes.eq(1).find(attributesSelector);

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
     * Highlights difference in custom attributes
     *
     * @param {jQuery} $target - the root DOM element containing the
     *   revision diff comparison
     * @param {can.List} revisions - revisions for comparing
     */
    highlightCustomAttributes($target, revisions) {
      const titleSelector = '.info-pane__section-title';
      const valueSelector = '.inline__content';
      const highlightClass = 'diff-highlighted';

      let that = this;
      let $caPanes = $target.find('.info global-custom-attributes');
      let $oldCAs = $caPanes.eq(0).find('.ggrc-form-item');
      let $newCAs = $caPanes.eq(1).find('.ggrc-form-item');

      let oldCAs = getCAs(revisions[0]);
      let newCAs = getCAs(revisions[1]);

      compareCAs($oldCAs, $newCAs, oldCAs, newCAs);

      /**
       * Prepares instance's custom attributes
       * @param {Object} revision - revision
       * @return {can.List} custom attributes list
       */
      function getCAs(revision) {
        let instance = revision.instance;
        return prepareCustomAttributes(
          instance.attr('custom_attribute_definitions'),
          instance.attr('custom_attributes'));
      }

      /**
       * Compares two lists of custom attributes
       * @param {Object} $ca0s - list of jQuery objects for custom attributes
       * @param {Object} $ca1s - list of jQuery objects for custom attributes
       * @param {can.List} ca0s - list of custom attributes (should be sorted by id)
       * @param {can.List} ca1s - list of custom attributes (should be sorted by id)
       */
      function compareCAs($ca0s, $ca1s, ca0s, ca1s) {
        let i = 0;
        let j = 0;
        while (i < ca0s.length || j < ca1s.length) {
          let ca0 = ca0s[i] || {};
          let ca1 = ca1s[j] || {};
          let $ca0 = $ca0s.eq(i);
          let $ca1 = $ca1s.eq(j);

          if (ca0.custom_attribute_id === ca1.custom_attribute_id) {
            // same attribute
            highlightTitle($ca0, ca0, $ca1, ca1);
            highlightValue($ca0, ca0, $ca1, ca1);
            i++;
            j++;
          } else if (ca0.custom_attribute_id < ca1.custom_attribute_id ||
            !ca1.custom_attribute_id) {
            // attribute removed
            $ca1 = fillEmptyCA($ca1); // add empty block to the right panel
            highlightTitle($ca0, ca0);
            highlightValue($ca0, ca0);
            i++;
          } else {
            // attribute added
            $ca0 = fillEmptyCA($ca0); // add empty block to the left panel
            highlightTitle($ca1, ca1);
            highlightValue($ca1, ca1);
            j++;
          }
          that.equalizeHeights($ca0, $ca1);
        }
      }

      /**
       * Highlights title in custom attributes
       * @param {Object} $ca0 - JQuery object
       * @param {Object} ca0 - custom attribute object
       * @param {Object} $ca1 - jQuery object
       * @param {Object} ca1 - custom attribute object
       */
      function highlightTitle($ca0, ca0, $ca1, ca1) {
        let title0 = ca0.def.title;
        let title1 = ca1 && ca1.def ? ca1.def.title : null;
        if (title0 !== title1) {
          $ca0.find(titleSelector).addClass(highlightClass);

          if ($ca1) {
            $ca1.find(titleSelector).addClass(highlightClass);
          }
        }
      }

      /**
       * Highlights value in custom attributes
       * @param {Object} $ca0 - JQuery object
       * @param {Object} ca0 - custom attribute object
       * @param {Object} $ca1 - jQuery object
       * @param {Object} ca1 - custom attribute object
       */
      function highlightValue($ca0, ca0, $ca1, ca1) {
        let value0 = ca0.attribute_value;
        let objectId0 = ca0.attribute_object_id; // for Person attr type
        let value1 = ca1 ? ca1.attribute_value : null;
        let objectId1 = ca1 ? ca1.attribute_object_id : null;
        if (value0 !== value1 || objectId0 !== objectId1) {
          $ca0.find(valueSelector).addClass(highlightClass);

          if ($ca1) {
            $ca1.find(valueSelector).addClass(highlightClass);
          }
        }
      }

      /**
       * Fills empty space when CA is not existing
       * @param {Object} $ca - jQuery object of previous the same attribute
       * @return {Object} new empty jQuery object
       */
      function fillEmptyCA($ca) {
        let $empty = $('<div class="ggrc-form-item"/>');
        $empty.insertBefore($ca);
        return $empty;
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

      $roleBlocksOld.each((i) => {
        var $blockOld = $roleBlocksOld.eq(i);
        var $blockNew = $roleBlocksNew.eq(i); // the block count is the same
        compareRoleBlocks($blockOld, $blockNew);
        this.equalizeHeights($blockOld, $blockNew);
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
    },
    /**
     * Adjust the heights of two DOM elements to the higher one's height.
     *
     * @param {jQuery} $block - the first block element
     * @param {jQuery} $block2 - the second block element
     */
    equalizeHeights($block, $block2) {
      var height;
      var height2;

      $block.css('max-width', 'none');
      $block2.css('max-width', 'none');
      $block.css('margin-right', '0');
      $block2.css('margin-right', '0');

      height = $block.outerHeight();
      height2 = $block2.outerHeight();

      if (height > height2) {
        $block2.outerHeight(height);
      } else if (height < height2) {
        $block.outerHeight(height2);
      }
    },
  },
});
