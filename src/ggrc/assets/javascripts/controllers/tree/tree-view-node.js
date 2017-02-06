/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, $) {
  function _firstElementChild(el) {
    var i;
    if (el.nodeType === Node.DOCUMENT_FRAGMENT_NODE) {
      for (i = 0; i < el.childNodes.length; i++) {
        if (el.childNodes[i].nodeType !== Node.TEXT_NODE) {
          return el.childNodes[i];
        }
      }
    } else {
      return el;
    }
  }

  can.Control.extend('CMS.Controllers.TreeViewNode', {
    defaults: {
      model: null,
      parent: null,
      instance: null,
      options_property: 'tree_view_options',
      show_view: null,
      expanded: false,
      subTreeLoading: false,
      draw_children: true,
      child_options: []
    }
  }, {
    setup: function (el, opts) {
      var that = this;
      if (typeof this._super === 'function') {
        this._super(el);
      }
      if (opts instanceof can.Map) {
        this.options = opts;
        if (typeof (this.options.model) === 'string') {
          this.options.attr('model', CMS.Models[this.options.model]);
        }
        can.each(this.constructor.defaults, function (v, k) {
          if (!that.options.hasOwnProperty(k)) {
            that.options.attr(k, v);
          }
        });
      } else {
        if (typeof (opts.model) === 'string') {
          opts.model = CMS.Models[opts.model];
        }
        this.options = new CMS.Models.TreeViewOptions(this.constructor.defaults)
          .attr(opts.model ? opts.model[opts.options_property ||
            this.constructor.defaults.options_property] : {})
          .attr(opts);
      }
    },

    init: function (el, opts) {
      var parent = opts.parent_instance || {};
      var options = this.options;
      if (options.instance && !options.show_view) {
        options.show_view =
          options.instance.constructor[options.options_property].show_view ||
          options.model[options.options_property].show_view ||
          GGRC.mustache_path + '/base_objects/tree.mustache';
      }
      this._draw_node_deferred = can.Deferred();

      if (this.options.child_options) {
        this.options.child_options.each(function (option) {
          option.attr({
            parent: this,
            parent_instance: this.options.instance,
            is_snapshotable:
              GGRC.Utils.Snapshots.isSnapshotScope(parent),
            snapshot_scope_id: parent.id,
            snapshot_scope_type: parent.type
          });
        }.bind(this));
      }

      // this timeout is required because the invoker will access the control via
      // the element synchronously so we must not replace the element just yet
      setTimeout(function () {
        if (this.options.disable_lazy_loading) {
          this.draw_node();
        } else {
          this.draw_placeholder();
        }
      }.bind(this), 0);
    },

    '{instance} custom_attribute_values':
      function (object, ev, newVal, oldVal) {
        function getValues(cav) {
          return _.pluck(cav.reify(), 'attribute_value');
        }
        if ((!oldVal || !newVal) || (oldVal.length === newVal.length &&
          _.difference(getValues(oldVal), getValues(newVal)).length)) {
          this.draw_node(true);
        }
      },

    markNotRelatedItem: function () {
      var instance = this.options.instance;
      var relatedInstances = GGRC.Utils.CurrentPage.related
        .attr(instance.type);

      if (!relatedInstances || relatedInstances &&
        !relatedInstances[instance.id]) {
        this.element.addClass('parent-related');
      } else {
        this.element.addClass('current-instance-related');
      }
    },

    /**
     * Trigger rendering the tree node in the DOM.
     * @param {Boolean} force - indicates redraw is/is not mandatory
     */
    draw_node: function (force) {
      var isActive;
      var isPlaceholder;
      var lazyLoading = this.options.disable_lazy_loading;

      if (!this.element) {
        return;
      }
      isPlaceholder = this.element.hasClass('tree-item-placeholder');

      if (this._draw_node_in_progress ||
        !force && (!lazyLoading && !isPlaceholder)) {
        return;
      }

      this._draw_node_in_progress = true;

      // the node's isActive state is not stored anywhere, thus we need to
      // determine it from the presemce of the corresponding CSS class
      isActive = this.element.hasClass('active');

      can.view(
        this.options.show_view,
        this.options,
        this._ifNotRemoved(function (frag) {
          this.replace_element(frag);

          if (isActive) {
            this.element.addClass('active');
          }

          this._draw_node_deferred.resolve();
        }.bind(this))
      );

      this.options.attr('isPlaceholder', false);
      this._draw_node_in_progress = false;
    },

    draw_placeholder: function () {
      can.view(
        GGRC.mustache_path + '/base_objects/tree_placeholder.mustache',
        this.options,
        this._ifNotRemoved(function (frag) {
          this.replace_element(frag);
          this._draw_node_deferred.resolve();
          this.options.expanded = false;
          delete this._expand_deferred;
        }.bind(this))
      );
      this.options.attr('isPlaceholder', true);
    },

    should_draw_children: function () {
      var drawChildren = this.options.draw_children;
      if (can.isFunction(drawChildren)) {
        return drawChildren.apply(this.options);
      }
      return drawChildren;
    },

    // add all child options to one TreeViewOptions object
    add_child_lists_to_child: function () {
      var originalChildList = this.options.child_options;
      var newChildList = [];

      if (this.options.attr('_added_child_list')) {
        return;
      }
      this.options.attr('child_options', new can.Observe.List());

      if (originalChildList.length === null) {
        originalChildList = [originalChildList];
      }

      if (this.should_draw_children()) {
        can.each(originalChildList, function (data, i) {
          var options = new can.Map();
          data.each(function (v, k) {
            options.attr(k, v);
          });
          this.add_child_list(this.options, options);
          options.attr({
            options_property: this.options.options_property,
            single_object: false,
            parent: this,
            parent_instance: this.options.instance
          });
          newChildList.push(options);
        }.bind(this));

        this.options.attr('child_options', newChildList);
        this.options.attr('_added_child_list', true);
      }
    },

    // data is an entry from child options.  if child options is an array, run once for each.
    add_child_list: function (item, data) {
      var findParams;
      data.attr({start_expanded: false});
      if (can.isFunction(item.instance[data.property])) {
        // Special case for handling mappings which are functions until
        // first requested, then set their name via .attr('...')
        findParams = function () {
          return item.instance[data.property]();
        };
        data.attr('find_params', findParams);
      } else if (data.property) {
        findParams = item.instance[data.property];
        if (findParams && findParams.isComputed) {
          data.attr('original_list', findParams);
          findParams = findParams();
        } else if (findParams && findParams.length) {
          data.attr('original_list', findParams);
          findParams = findParams.slice(0);
        }
        data.attr('list', findParams);
      } else {
        findParams = data.attr('find_params');
        if (findParams) {
          findParams = findParams.serialize();
        } else {
          findParams = {};
        }
        if (data.parent_find_param) {
          findParams[data.parent_find_param] = item.instance.id;
        } else {
          findParams['parent.id'] = item.instance.id;
        }
        data.attr('find_params', new can.Map(findParams));
      }
      // $subtree.cms_controllers_tree_view(opts);
    },

    replace_element: function (el) {
      var oldEl = this.element;
      var oldData;
      var firstchild;

      if (!this.element) {
        return;
      }

      oldData = $.extend({}, oldEl.data());

      firstchild = $(_firstElementChild(el));

      oldData.controls = oldData.controls.slice(0);
      oldEl.data('controls', []);
      this.off();
      oldEl.replaceWith(el);
      this.element = firstchild.addClass(this.constructor._fullName)
        .data(oldData);

      if (this.options.is_subtree) {
        this.markNotRelatedItem();
      }
      this.on();
    },

    display: function () {
      return this.trigger_expand();
    },

    display_path: function (path) {
      return this.display().then(this._ifNotRemoved(function () {
        return GGRC.Utils._display_tree_subpath(this.element, path);
      }.bind(this)));
    },

    display_subtrees: function (refetch) {
      var childTreeDfds = [];
      var that = this;
      var parentCtrl = this.element.closest('section')
        .find('.cms_controllers_tree_view').control();

      refetch = refetch || parentCtrl.options.showMappedToAllParents;

      this.element.find('.' + CMS.Controllers.TreeView._fullName)
        .each(function (_, el) {
          var $el = $(el);
          var childTreeControl;

          //  Ensure this targets only direct child trees, not sub-tree trees
          if ($el.closest('.' + that.constructor._fullName).is(that.element)) {
            childTreeControl = $el.control();
            if (childTreeControl) {
              that.options.attr('subTreeLoading', true);
              childTreeDfds.push(childTreeControl.display(refetch)
                .then(function () {
                  that.options.attr('subTreeLoading', false);
                }));
            }
          }
        });

      return $.when.apply($, childTreeDfds);
    },

    /**
     * Expand the tree node to make its subnodes visible.
     *
     * @return {can.Deferred} - a deferred object resolved when all the child
     *   nodes have been loaded and displayed
     */
    expand: function () {
      var $el = this.element;

      this.add_child_lists_to_child();
      if (this._expand_deferred && $el.find('.openclose').is('.active')) {
        // If we have already expanded and are currently still expanded, then
        // short-circuit the call. However, we still need to toggle `expanded`,
        // but if it's the first time expanding, `this.add_child_lists_to_child`
        // *must* be called first.
        this.options.attr('expanded', true);
        return this._expand_deferred;
      }

      this.options.attr('expanded', true);

      this._expand_deferred = can.Deferred();
      setTimeout(this._ifNotRemoved(function () {
        this.display_subtrees()
          .then(this._ifNotRemoved(function () {
            this.element.trigger('subtree_loaded');
            this.element.trigger('loaded');
            if (this._expand_deferred) {
              this._expand_deferred.resolve();
            }
          }.bind(this)));
      }.bind(this)), 0);
      return this._expand_deferred;
    },

    '.openclose:not(.active) click': function (el, ev) {
      // Ignore unless it's a direct child
      if (el.closest('.' + this.constructor._fullName).is(this.element)) {
        this.expand();
      }
    },

    '.select:not(.disabled) click': function (el, ev) {
      var tree = el.closest('.cms_controllers_tree_view_node');
      var node = tree.control();
      if (node) {
        node.select();
      }
    },

    /**
     * Mark the tree node as active (and all other tree nodes as inactive).
     * @param {Boolean} maximizeInfoPane - Info pane maximized state
     */
    select: function (maximizeInfoPane) {
      var $tree = this.element;
      var treeHasMaximizedClass = $tree.hasClass('maximized-info-pane');
      if (typeof maximizeInfoPane === 'undefined') {
        if (treeHasMaximizedClass) {
          maximizeInfoPane = true;
        } else {
          maximizeInfoPane = false;
        }
      }

      if ($tree.hasClass('active') &&
        ((maximizeInfoPane && treeHasMaximizedClass) ||
        (!maximizeInfoPane && !treeHasMaximizedClass))) {
        return;  // tree node already selected, no need to activate it again
      }

      $tree.closest('section')
        .find('.cms_controllers_tree_view_node')
        .removeClass('active');

      $tree
        .addClass('active');

      if (maximizeInfoPane) {
        $tree
          .addClass('maximized-info-pane');
      } else {
        $tree
          .removeClass('maximized-info-pane');
      }

      this.update_hash_fragment();
      $('.pin-content').control()
        .setInstance(this.options, $tree, maximizeInfoPane);
    },

    'input,select click': function (el, ev) {
      // Don't toggle accordion when clicking on input/select fields
      ev.stopPropagation();
    },

    trigger_expand: function () {
      var $expandEl = this.element.find('.openclose').first();
      if (!$expandEl.hasClass('active')) {
        $expandEl.trigger('click');
      }
      return this.expand();
    },

    hash_fragment: function () {
      var parentFragment = '';

      if (this.options.parent) {
        parentFragment = this.options.parent.hash_fragment();
      }

      return [parentFragment,
        this.options.instance.hash_fragment()].join('/');
    },

    update_hash_fragment: function () {
      var hash = window.location.hash.split('/')[0];

      window.location.hash = [hash,
        this.hash_fragment()].join('');
    }
  });
})(window.can, window.$);
