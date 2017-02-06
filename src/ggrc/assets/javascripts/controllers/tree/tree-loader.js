/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, $) {
  if (!GGRC.tree_view) {
    GGRC.tree_view = new can.Map();
  }
  GGRC.tree_view.attr('basic_model_list', []);
  GGRC.tree_view.attr('sub_tree_for', {});

  can.Map.extend('CMS.Models.TreeViewOptions', {
    defaults: {
      instance: undefined,
      parent: null,
      children_drawn: false
    }
  }, {});

  can.Control.extend('CMS.Controllers.TreeLoader', {
    defaults: {}
  }, {
    init_spinner: function () {
      var renderer;
      var spinner;
      var $footer;
      var $wrapper;

      if (this.element) {
        $footer = this.element.children('.tree-item-add').first();

        if (this.options.is_subtree) {
          $wrapper = $('<li class="tree-item tree-spinner"/>');
        } else {
          $wrapper = $('<div class="tree-spinner"/>');
        }

        if (!this.options.is_subtree && !this.element.next().length) {
          $wrapper.css('height', '40px');
        }

        spinner = [
          '<spinner toggle="showMe"',
          '  size="large"',
          '  extra-css-class="tree-items"',
          '>',
          '</spinner>'
        ].join('');
        renderer = can.view.mustache(spinner);
        spinner = renderer({showMe: true});

        // Admin dashboard
        if ($footer.length === 0 &&
          this.element.children('.tree-structure').length > 0) {
          this.element.children('.tree-structure')
            .addClass('new-tree_loading').append($wrapper);
        } else if ($footer.length === 0) {  // My work
          this.element.addClass('new-tree_loading').append($wrapper);
        } else {
          $footer.before($wrapper);
        }

        $wrapper.append(spinner);
      }
    },
    prepare: function () {
      if (this._prepare_deferred) {
        return this._prepare_deferred;
      }

      this._prepare_deferred = can.Deferred();
      this._prepare_deferred.resolve();

      this._attached_deferred.then(function () {
        if (!this.element) {
          return;
        }
        can.trigger(this.element, 'updateCount',
          [0, this.options.update_count]);
        this.init_count();
      }.bind(this));

      return this._prepare_deferred;
    },

    show_info_pin: function () {
      var children;
      var controller;
      if (this.element && !this.element.data('no-pin')) {
        children = this.element.children();
        controller = children && children.find('.select:visible')
            .first()
            .closest('.cms_controllers_tree_view_node')
            .control();

        if (controller) {
          controller.select();
        }
      }
    },

    display: function (refetch) {
      var that = this;
      var trackerStop = GGRC.Tracker.start(
        'TreeView', 'display', this.options.model.shortName);
      // TODO: Currently Query API doesn't support CustomAttributable.
      var isCustomAttr = /CustomAttr/.test(this.options.model.shortName);
      var isTreeView = this instanceof CMS.Controllers.TreeView;
      var isSubTree = this.options.is_subtree;
      var pageInstance = GGRC.page_instance();
      var loader;
      if (!isTreeView || isCustomAttr ||
        (isSubTree && pageInstance.type === 'Workflow')) {
        loader = this.fetch_list.bind(this);
      } else if (isSubTree) {
        loader = this.loadSubTree.bind(this, refetch);
      } else {
        loader = this.loadPage.bind(this);
      }

      if (refetch) {
        this._draw_list_deferred = null;
        this._display_deferred = null;
        this.element.slideUp('fast').empty().slideDown();
      }

      if (this._display_deferred) {
        return this._display_deferred;
      }

      this._display_deferred = $.when(this._attached_deferred, this.prepare());

      this._display_deferred = this._display_deferred
        .then(this._ifNotRemoved(function () {
          var dfds = [loader()];
          if (that._init_view_deferred) {
            dfds.push(that._init_view_deferred);
          } else {
            dfds.push(that.init_view());
          }
          return $.when.apply($, dfds);
        }))
        .then(that._ifNotRemoved(that.proxy('draw_list')))
        .done(trackerStop);

      return this._display_deferred;
    },

    draw_list: function (list, isReload, forcePrepareChildren) {
      isReload = isReload === true;
      // TODO figure out why this happens and fix the root of the problem
      if (!list && !this.options.list) {
        return undefined;
      }
      if (this._draw_list_deferred) {
        return this._draw_list_deferred;
      }
      this._draw_list_deferred = can.Deferred();
      if (this.element && !this.element.closest('body').length) {
        return undefined;
      }

      if (list) {
        list = list.length === null ? new can.List([list]) : list;
      } else {
        list = this.options.list;
      }

      if (!this.element) {
        return undefined;  // controller has been destroyed
      }

      this.clearList();

      this.options.attr('original_list', list);
      this.options.attr('list', []);
      this.on();

      this._draw_list_deferred =
        this.enqueue_items(list, isReload, forcePrepareChildren);
      return this._draw_list_deferred;
    },

    _loading_started: function () {
      var $contentContainer;

      if (!this._loading_deferred) {
        this._loading_deferred = can.Deferred();

        // for some reason, .closest(<selector>) does not work, thus need to use
        // using a bit less roboust .parent()
        $contentContainer = this.element.parent();
        $contentContainer
          .find('spinner[extra-css-class="initial-spinner"]')
          .remove();

        this.init_spinner();  // the tree view's own items loading spinner
        this.element.trigger('loading');
      }
    },

    _loading_finished: function () {
      var loadingDeferred;

      if (this._loading_deferred) {
        this.element.trigger('loaded');
        this.element.find('.tree-spinner').remove();

        if (this.element.hasClass('new-tree_loading')) {
          this.element.removeClass('new-tree_loading');
        } else {
          this.element.find('.new-tree_loading')
            .removeClass('new-tree_loading');
        }

        loadingDeferred = this._loading_deferred;
        this._loading_deferred = null;
        loadingDeferred.resolve();
      }
    },

    enqueue_items: function (items, isReload, forcePrepareChildren) {
      var childTreeDisplayList = [];
      var filteredItems = [];
      var i;
      var refreshedDeferred;
      var that = this;
      var parentModelName;
      var parentInstanceType;
      isReload = isReload === true;

      // find current widget model and check if first layer tree
      if (GGRC.page_object && this.options.parent) { // this is a second label tree
        parentModelName = this.options.parent.options.model.shortName;
        parentInstanceType = this.options.parent.options.instance.type;
        childTreeDisplayList =
          (GGRC.tree_view.sub_tree_for[parentModelName] ||
            GGRC.tree_view.sub_tree_for[parentInstanceType] ||
            {} // all hope is lost, skip filtering
          ).display_list;

        // check if no objects selected, then skip filter
        if (!childTreeDisplayList) {
          // skip filter
          filteredItems = items;
        } else if (childTreeDisplayList.length === 0) { // no item is selected to filter, so just return
          return can.Deferred().resolve();
        } else {
          for (i = 0; i < items.length; i++) {
            if (childTreeDisplayList
                .indexOf(items[i].instance.class.model_singular) !== -1) {
              filteredItems.push(items[i]);
            }
          }
        }
      } else {
        filteredItems = items;
      }

      if (!this._pending_items) {
        this._pending_items = [];
        this._loading_started();
      }

      if (!isReload) {
        refreshedDeferred = $.when.apply($,
          can.map(filteredItems, function (item) {
            var instance = item.instance || item;
            if (instance.custom_attribute_values &&
              !GGRC.Utils.Snapshots.isSnapshot(instance)) {
              return instance.refresh_all('custom_attribute_values')
                .then(function (values) {
                  var rq = new RefreshQueue();
                  _.each(values, function (value) {
                    if (value.attribute_object) {
                      rq.enqueue(value.attribute_object);
                    }
                  });
                  return rq.trigger().then(function () {
                    return values;
                  });
                });
            }
          }));
      } else {
        refreshedDeferred = can.Deferred().resolve();
      }
      refreshedDeferred
        .then(function () {
          return that.insert_items(filteredItems, forcePrepareChildren);
        })
        .then(this._ifNotRemoved(this.proxy('_loading_finished')));

      return this._loading_deferred;
    },

    insert_items: function (items, forcePrepareChildren) {
      var that = this;
      var preppedItems = [];
      var idMap = {};
      var toInsert;
      var dfd;

      if (this.options.attr('is_subtree')) {
        // Check the list of items to be inserted for any duplicate items.
        can.each(this.options.list || [], function (item) {
          idMap[item.instance.type + item.instance.id] = true;
        });
        toInsert = _.filter(items, function (item) {
          return !idMap[item.instance.type + item.instance.id];
        });
      } else {
        toInsert = items;
      }

      can.each(toInsert, function (item) {
        var prepped = that.prepare_child_options(item, forcePrepareChildren);
        // Should we skip items without selfLink?
        if (prepped.instance.selfLink) {
          preppedItems.push(prepped);
        }
      });

      if (preppedItems.length > 0) {
        this.options.list.push.apply(this.options.list, preppedItems);
        dfd = this.add_child_lists(preppedItems);
      } else {
        if (this.options.is_subtree) {
          this.addSubTreeExpander(items);
        }
        dfd = can.Deferred().resolve();
      }

      return dfd;
    }
  });
})(window.can, window.$);
