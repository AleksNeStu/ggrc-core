/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, $, utils) {
  'use strict';

  var DEFAULT_OBJECT_MAP = {
    Assessment: 'Control',
    Objective: 'Control',
    Section: 'Objective',
    Regulation: 'Section',
    Product: 'System',
    Standard: 'Section',
    Contract: 'Clause',
    Control: 'Objective',
    System: 'Product',
    Process: 'Risk',
    AccessGroup: 'System',
    Clause: 'Contract',
    DataAsset: 'Policy',
    Facility: 'Program',
    Issue: 'Control',
    Market: 'Program',
    OrgGroup: 'Program',
    Policy: 'DataAsset',
    Program: 'Standard',
    Project: 'Program',
    Risk: 'Control',
    TaskGroupTask: 'Control',
    Threat: 'Risk',
    Vendor: 'Program',
    Audit: 'Product',
    RiskAssessment: 'Program',
    TaskGroup: 'Control'
  };

  var getDefaultType = function (type, object) {
    var treeView = GGRC.tree_view.sub_tree_for[object];
    var defaultType =
      (CMS.Models[type] && type) ||
      DEFAULT_OBJECT_MAP[object] ||
      (treeView ? treeView.display_list[0] : 'Control');
    return defaultType;
  };

  /**
   * A component implementing a modal for mapping objects to other objects,
   * taking the object type mapping constraints into account.
   */
  GGRC.Components('objectMapper', {
    tag: 'object-mapper',
    template: can.view(GGRC.mustache_path +
      '/components/object-mapper/object-mapper.mustache'),
    viewModel: function (attrs, parentViewModel) {
      var config = {
        general: parentViewModel.attr('generalConfig'),
        special: parentViewModel.attr('specialConfigs')
      };

      return GGRC.VM.ObjectOperationsBaseVM.extend({
        join_object_id: config.general['join-object-id'] ||
          (GGRC.page_instance() && GGRC.page_instance().id),
        object: config.general.object,
        type: getDefaultType(config.general.type, config.general.object),
        config: config,
        pendingConfigQueue: [],
        useSnapshots: config.general.useSnapshots,
        isLoadingOrSaving: function () {
          return this.attr('is_saving') ||
          //  disable changing of object type while loading
          //  to prevent errors while speedily selecting different types
          this.attr('is_loading');
        },
        deferred_to: parentViewModel.attr('deferred_to'),
        deferred_list: [],
        deferred: false,
        allowedToCreate: function () {
          // Don't allow to create new instances for "In Scope" Objects
          var isInScopeModel =
            GGRC.Utils.Snapshots.isInScopeModel(this.attr('object'));
          return !isInScopeModel;
        },
        showWarning: function () {
          // Never show warning for In Scope Objects
          if (GGRC.Utils.Snapshots.isInScopeModel(this.attr('object'))) {
            return false;
          }
          return GGRC.Utils.Snapshots.isSnapshotParent(this.attr('object')) ||
            GGRC.Utils.Snapshots.isSnapshotParent(this.attr('type'));
        },
        prepareConfig: function (config) {
          /**
           * We don't want to apply config immediately
           * (Because CanJs will be rerender mustache template immediately).
           * For the reason we add config in pending queue.
           */
          this.pendingConfigQueue.push(config);

          // But we want to render mapping immediately
          this.update({
            relevantTo: config.relevantTo
          });
        },
        onSubmit: function () {
          var queue = can.makeArray(
            this.attr('pendingConfigQueue')
          ).map(function (config) {
            return config.serialize();
          });

          var resolvedConfigQueue = utils.resolveQueue(queue, true);

          this.update(resolvedConfigQueue);
          // calls base version
          this._super.apply(this, arguments);
        }
      });
    },

    events: {
      '.create-control modal:success': function (el, ev, model) {
        this.viewModel.attr('newEntries').push(model);
        this.mapObjects(this.viewModel.attr('newEntries'));
      },
      '.create-control modal:added': function (el, ev, model) {
        this.viewModel.attr('newEntries').push(model);
      },
      '.create-control click': function () {
        // reset new entries
        this.viewModel.attr('newEntries', []);
        this.element.trigger('hideModal');
      },
      '{window} modal:dismiss': function (el, ev, options) {
        var joinObjectId = this.viewModel.attr('join_object_id');
        $('body').trigger('closeMapper');

        // mapper sets uniqueId for modal-ajax.
        // we can check using unique id which modal-ajax is closing
        if (options.uniqueId &&
          joinObjectId === options.uniqueId &&
          this.viewModel.attr('newEntries').length > 0) {
          this.mapObjects(this.viewModel.attr('newEntries'));
        } else {
          this.element.trigger('showModal');
        }
      },
      inserted: function () {
        var self = this;
        var deferredToList;
        this.viewModel.attr('selected').replace([]);
        this.viewModel.attr('entries').replace([]);

        if (this.viewModel.attr('deferred_to.list')) {
          deferredToList = this.viewModel.attr('deferred_to.list')
            .map(function (item) {
              return {
                id: item.id,
                type: item.type
              };
            });
          this.viewModel.attr('deferred_list', deferredToList);
        }

        self.viewModel.attr('submitCbs').fire();
      },
      closeModal: function () {
        $('body').trigger('closeMapper');
        this.viewModel.attr('is_saving', false);

        // TODO: Find proper way to dismiss the modal
        if (this.element) {
          this.element.find('.modal-dismiss').trigger('click');
        }
      },
      deferredSave: function () {
        var source = this.viewModel.attr('deferred_to').instance ||
          this.viewModel.attr('object');
        var data = {};

        data = {
          multi_map: true,
          arr: _.compact(_.map(
            this.viewModel.attr('selected'),
            function (desination) {
              if (GGRC.Utils.allowed_to_map(source, desination)) {
                desination.isNeedRefresh = true;
                return desination;
              }
            }
          ))
        };

        this.viewModel.attr('deferred_to').controller.element.trigger(
          'defer:add', [data, {map_and_save: true}]);
        this.closeModal();
      },
      '.modal-footer .btn-map click': function (el, ev) {
        ev.preventDefault();
        if (el.hasClass('disabled') ||
          this.viewModel.attr('is_saving')) {
          return;
        }

        // TODO: Figure out nicer / proper way to handle deferred save
        if (this.viewModel.attr('deferred')) {
          return this.deferredSave();
        }
        this.viewModel.attr('is_saving', true);
        this.mapObjects(this.viewModel.attr('selected'));
      },
      mapObjects: function (objects) {
        var type = this.viewModel.attr('type');
        var object = this.viewModel.attr('object');
        var instance = CMS.Models[object].findInCacheById(
          this.viewModel.attr('join_object_id'));
        var mapping;
        var Model;
        var data = {};
        var defer = [];
        var que = new RefreshQueue();

        que.enqueue(instance).trigger().done(function (inst) {
          data.context = instance.context || null;
          objects.forEach(function (destination) {
            var modelInstance;
            var isMapped;
            var isAllowed;
            var isPersonMapping = type === 'Person';
            // Use simple Relationship Model to map Snapshot
            if (this.viewModel.attr('useSnapshots')) {
              modelInstance = new CMS.Models.Relationship({
                context: data.context,
                source: instance,
                destination: {
                  href: '/api/snapshots/' + destination.id,
                  type: 'Snapshot',
                  id: destination.id
                }
              });

              return defer.push(modelInstance.save());
            }

            isMapped = GGRC.Utils.is_mapped(instance, destination);
            isAllowed = GGRC.Utils.allowed_to_map(instance, destination);

            if ((!isPersonMapping && isMapped) || !isAllowed) {
              return;
            }
            mapping = GGRC.Mappings.get_canonical_mapping(object, type);
            Model = CMS.Models[mapping.model_name];
            data[mapping.object_attr] = {
              href: instance.href,
              type: instance.type,
              id: instance.id
            };
            data[mapping.option_attr] = destination;
            modelInstance = new Model(data);
            defer.push(modelInstance.save());
          }.bind(this));

          $.when.apply($, defer)
            .fail(function (response, message) {
              $('body').trigger('ajax:flash', {error: message});
            })
            .always(function () {
              this.viewModel.attr('is_saving', false);
              this.closeModal();
            }.bind(this))
            .done(function () {
              if (instance && instance.dispatch) {
                instance.dispatch('refreshInstance');
                instance.dispatch('refreshMapping');
              }
              // This Method should be modified to event
              GGRC.Utils.CurrentPage.refreshCounts();

              _.each($('sub-tree-wrapper'), function (wrapper) {
                var vm = $(wrapper).viewModel();

                if (vm.attr('parent') === instance) {
                  if (vm.attr('isOpen') && vm.attr('dataIsReady')) {
                    vm.loadItems();
                  } else {
                    // remove old data
                    // new data will be loaded after sub-tree is expanded
                    vm.attr('dataIsReady', null);
                  }

                  return false;
                }
              });
            });
        }.bind(this));
      }
    },

    helpers: {
      get_title: function (options) {
        var instance = this.attr('parentInstance');
        return (
          (instance && instance.title) ?
            instance.title :
            this.attr('object')
        );
      },
      get_object: function (options) {
        var type = CMS.Models[this.attr('type')];
        if (type && type.title_plural) {
          return type.title_plural;
        }
        return 'Objects';
      }
    }
  });
})(window.can, window.can.$, GGRC.Utils);
