/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, $) {
  CMS.Controllers.TreeLoader.extend('CMS.Controllers.TreeView', {
    // static properties
    defaults: {
      model: null,
      header_view: GGRC.mustache_path + '/base_objects/tree_header.mustache',
      show_view: null,
      show_header: false,
      footer_view: null,
      add_item_view: null,
      parent: null,
      list: null,
      filteredList: [],
      single_object: false,
      find_params: {},
      paging: {
        current: 1,
        total: null,
        pageSize: 10,
        count: null,
        pageSizeSelect: [10, 25, 50],
        filter: null,
        sortDirection: null,
        sortBy: null,
        disabled: false
      },
      fields: [],
      filter_states: [],
      sortable: true,
      start_expanded: false, // true
      draw_children: true,
      find_function: null,
      options_property: 'tree_view_options',
      allow_reading: true,
      allow_mapping: true,
      allow_creating: true,
      child_options: [], // this is how we can make nested configs. if you want to use an existing
      // example child option:
      // { property: "controls", model: CMS.Models.Control, }
      // { parent_find_param: "system_id" ... }
      scroll_page_count: 1, // pages above and below viewport
      is_subtree: false,
      subTreeElementsLimit: 20,
      limitDeepOfTree: 2
    },
    do_not_propagate: [
      'header_view',
      'footer_view',
      'add_item_view',
      'list',
      'original_list',
      'single_object',
      'find_function',
      'find_all_deferred'
    ]
  }, {
    // prototype properties
    setup: function (el, opts) {
      var defaultOptions;
      var optionsProperty;
      var defaults = this.constructor.defaults;
      if (typeof this._super === 'function') {
        this._super(el);
      }

      if (typeof (opts.model) === 'string') {
        opts.model = CMS.Models[opts.model];
      }
      optionsProperty = opts.options_property || defaults.options_property;
      defaultOptions = opts.model[optionsProperty] || {};

      this.options = new can.Map(defaults).attr(defaultOptions).attr(opts);
      if (opts instanceof can.Map) {
        this.options = can.extend(this.options, opts);
      }
    },
    deselect: function () {
      var active = this.element.find('.cms_controllers_tree_view_node.active');
      active
        .removeClass('active')
        .removeClass('maximized-info-pane');
      this.update_hash_fragment(active.length);
    },
    update_hash_fragment: function (status) {
      var hash;
      if (!status) {
        return;
      }
      hash = window.location.hash.split('/');
      hash.pop();
      window.location.hash = hash.join('/');
    },
    // Total display with is set to be span12.
    // Default: title: span4
    //          middle selectable: span4, by default 2 attributes are selected
    //          action: span4
    // When user selects 3 middle selectable attribute, title width is reduced to span3
    // and when user selects 4 attributes, the action column is also reduced to span3
    setup_column_width: function () {
      // Special case when import and export buttons should not be wisible for snapshots
      var snapshots = GGRC.Utils.Snapshots;
      var hideImportExport =
        snapshots.isSnapshotScope(this.options.parent_instance) &&
        snapshots.isSnapshotModel(this.options.model.model_singular);
      var displayOptions;
      var displayWidth = 12;
      var attrCount = this.options.display_attr_list.length;
      var nested = this.options.parent !== null;
      var widths = {
        defaults: [4, 4, 4],
        '0': [7, 1, 4],
        '3': [3, 5, 4],
        '4': [3, 6, 3],
        nested: [4, 0, 8]
      };
      var selectedWidths = widths[attrCount] || widths.defaults;

      if (nested) {
        selectedWidths = widths.nested;
      }

      displayOptions = {
        title_width: selectedWidths[0],
        selectable_width: selectedWidths[1],
        action_width: selectedWidths[2],
        selectable_attr_width: displayWidth / Math.max(attrCount, 1),
        hideImportExport: hideImportExport
      };
      this.options.attr('display_options', displayOptions);
    },

    init_child_tree_display: function (model) {
      var modelName;
      var childTreeModelList;
      var validModels;
      var wList;
      var subTree;
      if (!GGRC.page_object) { // Admin dashboard
        return;
      }

      // Set child tree options
      modelName = model.model_singular;
      childTreeModelList = [];
      validModels = can.Map.keys(GGRC.tree_view.base_widgets_by_type);

      wList = GGRC.tree_view.base_widgets_by_type[modelName]; // possible widget/mapped model_list
      if (wList === undefined) {
        childTreeModelList = GGRC.tree_view.basic_model_list;
        GGRC.tree_view.sub_tree_for.attr(modelName, {
          model_list: childTreeModelList,
          display_list: validModels
        });
      }

      subTree = GGRC.tree_view.sub_tree_for[modelName];
      this.options.attr('child_tree_model_list', subTree.model_list);
      this.options.attr('selected_child_tree_model_list', subTree.model_list);
      this.options.attr('select_model_list', GGRC.tree_view.basic_model_list);
      this.options.attr('selected_model_name', modelName);
    },

    // Displays attribute list for tree-header, Select attribute list drop down
    // Gets default and custom attribute list for each model, and sets upthe display-list
    init_display_options: function (opts) {
      var i;
      var savedAttrList;
      var selectAttrList = [];
      var displayAttrList = [];
      var model = opts.model;
      var modelName = model.model_singular;
      var modelDefinition = model().class.root_object;
      var mandatoryAttrNames;
      var displayAttrNames;
      var attr;

      // get standard attrs for each model
      can.each(model.tree_view_options.attr_list ||
        can.Model.Cacheable.attr_list, function (item) {
        if (!item.attr_sort_field) {
          item.attr_sort_field = item.attr_name;
        }
        selectAttrList.push(item);
      });

      selectAttrList.sort(function (a, b) {
        if (a.order && !b.order) {
          return -1;
        } else if (!a.order && b.order) {
          return 1;
        }
        return a.order - b.order;
      });
      // Get mandatory_attr_names
      mandatoryAttrNames = model.tree_view_options.mandatory_attr_names ?
        model.tree_view_options.mandatory_attr_names :
        can.Model.Cacheable.tree_view_options.mandatory_attr_names;

      // get custom attrs
      can.each(GGRC.custom_attr_defs, function (def, i) {
        var obj;
        if (def.definition_type === modelDefinition &&
          def.attribute_type !== 'Rich Text') {
          obj = {};
          obj.attr_title = obj.attr_name = def.title;
          obj.display_status = false;
          obj.attr_type = 'custom';
          obj.attr_sort_field = obj.attr_name;
          selectAttrList.push(obj);
        }
      });

      // Get the display attr_list from local storage
      savedAttrList = this.display_prefs.getTreeViewHeaders(modelName);

      this.loadTreeStates(modelName);
      this.options.attr('statusFilterVisible',
        GGRC.Utils.State.hasFilter(modelName));

      if (!savedAttrList.length) {
        // Initialize the display status, Get display_attr_names for model
        displayAttrNames = model.tree_view_options.display_attr_names ?
          model.tree_view_options.display_attr_names :
          can.Model.Cacheable.tree_view_options.display_attr_names;

        if (GGRC.Utils.CurrentPage.isMyAssessments()) {
          displayAttrNames.push('updated_at');
        }

        for (i = 0; i < selectAttrList.length; i++) {
          attr = selectAttrList[i];

          attr.display_status = displayAttrNames.indexOf(attr.attr_name) !== -1;
          attr.mandatory = mandatoryAttrNames.indexOf(attr.attr_name) !== -1;
        }
      } else {
        // Mandatory attr should be always displayed in tree view
        can.each(mandatoryAttrNames, function (attrName) {
          savedAttrList.push(attrName);
        });

        for (i = 0; i < selectAttrList.length; i++) {
          attr = selectAttrList[i];
          attr.display_status = savedAttrList.indexOf(attr.attr_name) !== -1;
          attr.mandatory = mandatoryAttrNames.indexOf(attr.attr_name) !== -1;
        }
      }

      // Create display list
      can.each(selectAttrList, function (item) {
        if (!item.mandatory && item.display_status) {
          displayAttrList.push(item);
        }
      });

      this.options.attr('select_attr_list', selectAttrList);
      this.options.attr('display_attr_list', displayAttrList);
      this.setup_column_width();
      this.init_child_tree_display(model);
    },

    init: function (el, opts) {
      var setAllowMapping;
      var self = this;
      var states = GGRC.Utils.State
        .getStatesForModel(this.options.model.shortName);

      var filterStates = states.map(function (state) {
        return {value: state};
      });

      this.options.attr('filter_states', filterStates);

      this.element.closest('.widget')
        .on('widget_hidden', this.widget_hidden.bind(this));
      this.element.closest('.widget')
        .on('widget_shown', this.widget_shown.bind(this));
      CMS.Models.DisplayPrefs.getSingleton().then(function (displayPrefs) {
        var allowed;
        // TODO: Currently Query API doesn't support CustomAttributable.
        var isCustomAttr = /CustomAttr/.test(this.options.model.shortName);

        this.display_prefs = displayPrefs;

        this.element.uniqueId();

        this.options.attr('is_subtree',
          this.element && this.element.closest('.inner-tree').length > 0);

        if (!this.options.attr('is_subtree') && !isCustomAttr) {
          this.page_loader = new GGRC.ListLoaders.TreePageLoader(
            this.options.model, this.options.parent_instance,
            this.options.mapping);
        } else if (this.options.attr('is_subtree')) {
          if (GGRC.Utils.CurrentPage.isObjectContextPage() &&
            GGRC.page_instance().type !== 'Workflow') {
            this.options.attr('drawSubTreeExpander', true);
          }
          this.page_loader = new GGRC.ListLoaders.SubTreeLoader(
            this.options.model, this.options.parent_instance,
            this.options.mapping);
        }

        if ('parent_instance' in opts && 'status' in opts.parent_instance) {
          setAllowMapping = function () {
            var isAccepted = opts.parent_instance.attr('status') === 'Accepted';
            var admin = Permission.is_allowed('__GGRC_ADMIN__');
            this.options.attr('allow_mapping_or_creating',
              (admin || !isAccepted) &&
              (this.options.allow_mapping || this.options.allow_creating));
          }.bind(this);
          setAllowMapping();
          opts.parent_instance.bind('change', setAllowMapping);
        } else {
          this.options.attr('allow_mapping_or_creating',
            this.options.allow_mapping || this.options.allow_creating);
        }

        if (this.element.parent().length === 0 || // element not attached
          this.element.data('disable-lazy-loading')) { // comment list
          this.options.disable_lazy_loading = true;
        }

        this.options.update_count =
          _.isBoolean(this.element.data('update-count')) ?
            this.element.data('update-count') :
            true;

        if (!this.options.scroll_element) {
          this.options.attr('scroll_element', $('.object-area'));

          $('.object-area').on('change', function () {
            self.update_header();
          });
        }

        // Override nested child options for allow_* properties
        allowed = {};
        this.options.each(function (item, prop) {
          if (prop.indexOf('allow') === 0 && item === false) {
            allowed[prop] = item;
          }
        });
        this.options.attr('child_options', this.options.child_options.slice(0));
        can.each(this.options.child_options, function (options, i) {
          this.options.child_options.attr(i,
            new can.Map(can.extend(options.attr(), allowed)));
        }.bind(this));

        this._attached_deferred = can.Deferred();
        if (this.element && this.element.closest('body').length) {
          this._attached_deferred.resolve();
        }
        this.init_display_options(opts);
      }.bind(this));
      // Make sure the parent_instance is not a computable
      if (typeof this.options.parent_instance === 'function') {
        this.options.attr('parent_instance', this.options.parent_instance());
      }
    },

    ' inserted': function () { // eslint-disable-line quote-props
      this._attached_deferred.resolve();
    },

    initNoResultsMessage: function () {
      var self = this;
      var context = new can.Map({
        text: 'No results, please check your filter criteria'
      });
      var html = can.mustache('<tree-no-results/>')(context);

      this.options.bind('paging.total', function () {
        context.attr('show', !self.options.attr('paging.total'));
      });

      this.element.after(html);
    },

    init_view: function () {
      var self = this;
      var dfds = [];
      var optionsDfd;
      var statusControl;

      if (this.options.header_view && this.options.show_header) {
        optionsDfd = $.when(this.options).then(function (options) {
          options.onChildModelsChange = self.set_tree_display_list.bind(self);
          return options;
        });
        dfds.push(
          can.view(this.options.header_view, optionsDfd).then(
            this._ifNotRemoved(function (frag) {
              this.element.before(frag);
              this.initNoResultsMessage();
              can.bind.call(this.element.parent()
                  .find('.widget-col-title[data-field]'),
                'click',
                this.sort.bind(this)
              );
              can.bind.call(this.element.parent().find('.set-tree-attrs'),
                'click',
                this.set_tree_attrs.bind(this)
              );

              can.bind.call(this.element.parent()
                .find('.tview-dropdown-toggle'),
                  'click',
                  function () {
                    this.init_display_options(this.options);
                  }.bind(this)
              );

              statusControl = this.element.parent()
                .find('.tree-filter__status-wrap');
              // set state filter (checkboxes)
              can.bind.call(statusControl.ready(function () {
                var selectStateList = self.options.attr('selectStateList');

                self.options.attr('filter_states').forEach(function (item) {
                  if (selectStateList.indexOf(item.value) > -1) {
                    item.attr('checked', true);
                  }
                });
              }));
            }.bind(this))));
      }

      this.init_count();

      if (this.options.footer_view) {
        dfds.push(
          can.view(this.options.footer_view, this.options,
            this._ifNotRemoved(function (frag) {
              this.element.after(frag);
            }.bind(this))
          ));
      }

      this._init_view_deferred = $.when.apply($.when, dfds);
      this.update_header();
      return this._init_view_deferred;
    },

    init_count: function () {
      var self = this;
      var options = this.options;
      var counts;
      var countsName = options.countsName || options.model.shortName;

      if (this.options.parent_instance && this.options.mapping) {
        counts = GGRC.Utils.CurrentPage.getCounts();

        if (self.element) {
          can.trigger(self.element, 'updateCount',
            [counts.attr(countsName), self.options.update_count]);
        }

        counts.on(countsName, function (ev, newVal, oldVal) {
          can.trigger(self.element, 'updateCount',
            [newVal, self.options.update_count]);
        });
      } else if (this.options.list_loader) {
        this.options.list_loader(this.options.parent_instance)
          .then(function (list) {
            return can.compute(function () {
              return list.attr('length');
            });
          })
          .then(function (count) {
            if (self.element) {
              can.trigger(self.element, 'updateCount', [count(),
                self.options.update_count]);
            }
            count.bind('change', self._ifNotRemoved(function () {
              can.trigger(self.element, 'updateCount', [count(),
                self.options.update_count]);
            }));
          });
      }
    },

    fetch_list: function () {
      if (this.find_all_deferred) {
        //  Skip, because already done, e.g., display() already called
        return this.find_all_deferred;
      }
      if (can.isEmptyObject(this.options.find_params.serialize())) {
        this.options.find_params.attr(
          'id', this.options.parent_instance ?
            this.options.parent_instance.id : undefined);
      }

      if (this.options.mapping) {
        if (this.options.parent_instance === undefined) {
          // TODO investigate why is this method sometimes called twice
          return undefined; // not ready, will try again
        }
        this.find_all_deferred =
          this.options.parent_instance.get_list_loader(this.options.mapping);
      } else if (this.options.list_loader) {
        this.find_all_deferred =
          this.options.list_loader(this.options.parent_instance);
      } else {
        console.debug('Unexpected code path', this);
      }

      return this.find_all_deferred;
    },

    display_path: function (path, refetch) {
      return this.display(refetch).then(this._ifNotRemoved(function () {
        return GGRC.Utils.TreeView.displayTreeSubpath(this.element, path);
      }.bind(this)));
    },

    prepare_child_options: function (v, forceReload) {
      //  v may be any of:
      //    <model_instance>
      //    { instance: <model instance>, mappings: [...] }
      //    <TreeOptions>
      var tmp;
      var that = this;
      var original = v;
      if (v._child_options_prepared && !forceReload) {
        return v._child_options_prepared;
      }
      if (!(v instanceof CMS.Models.TreeViewOptions)) {
        tmp = v;
        v = new CMS.Models.TreeViewOptions();
        v.attr('instance', tmp);
        this.options.each(function (val, k) {
          if (can.inArray(k, that.constructor.do_not_propagate) === -1) {
            v.attr(k, val);
          }
        });
      }
      if (!(v.instance instanceof can.Model)) {
        if (v.instance.instance instanceof can.Model) {
          v.attr('result', v.instance);
          v.attr('mappings', v.instance.mappings_compute());
          v.attr('instance', v.instance.instance);
        } else {
          v.attr('instance', this.options.model.model(v.instance));
        }
      }
      v.attr('child_count', can.compute(function () {
        var totalChildren = 0;
        if (v.attr('child_options')) {
          can.each(v.attr('child_options'), function (childCptions) {
            var list = childCptions.attr('list');
            if (list) {
              totalChildren += list.attr('length');
            }
          });
        }
        return totalChildren;
      }));
      original._child_options_prepared = v;
      return v;
    },
    el_position: function (el) {
      var se = this.options.scroll_element;
      var seO = se.offset().top;
      var seH = se.outerHeight();
      var elO;
      var elH;
      var aboveTop;
      var belowBottom;
      if (!(el instanceof jQuery)) {
        el = $(el);
      }
      if (!el.offset()) {
        return 0;
      }
      elO = el.offset().top;
      elH = el.outerHeight();
      aboveTop = (elO + elH - seO) / seH;
      belowBottom = (elO - seO) / seH - 1;
      if (aboveTop < 0) {
        return aboveTop;
      } else if (belowBottom > 0) {
        return belowBottom;
      }
      return 0;
    },
    draw_visible_call_count: 0,
    draw_visible: _.debounce(function () {
      var MAX_STEPS = 100;
      var elPosition;
      var children;
      var lo;
      var hi;
      var max;
      var steps;
      var visible;
      var alreadyVisible;
      var toRender;
      var i;
      var control;
      var index;
      var pageCount;
      var mid;
      var pos;
      var options = this.options;

      if (options.disable_lazy_loading ||
        !this.element ||
        options.attr('drawingItems')) {
        return;
      }

      elPosition = this.el_position.bind(this);
      children = options.attr('filteredList') || [];

      if (!children.length || !children[0].element) {
        return;
      }

      lo = 0;
      hi = children.length - 1;
      max = hi;
      steps = 0;
      visible = [];
      toRender = [];

      alreadyVisible = _.filter(children, function (child) {
        return !child.options.attr('isPlaceholder');
      });

      while (steps < MAX_STEPS && lo < hi) {
        steps += 1;
        mid = (lo + hi) / 2 | 0;
        pos = elPosition(children[mid].element);
        if (pos < 0) {
          lo = mid;
          continue;
        }
        if (pos > 0) {
          hi = mid;
          continue;
        }
        lo = mid;
        hi = mid;
      }
      pageCount = options.scroll_page_count;
      while (lo > 0 && elPosition(children[lo - 1].element) >= (-pageCount)) {
        lo -= 1;
      }
      while (hi < max && elPosition(children[hi + 1].element) <= pageCount) {
        hi += 1;
      }

      _.each(alreadyVisible, function (control) {
        if (!control) {
          return;
        }
        if (Math.abs(elPosition(control.element)) <= pageCount) {
          visible.push(control);
        } else {
          control.draw_placeholder();
        }
      });

      for (i = lo; i <= hi; i++) {
        index = this._is_scrolling_up ? (hi - (i - lo)) : i;
        control = children[index];
        if (!control) {
          // TODO this should not be necessary
          // draw_visible is called too soon when controllers are not yet
          // available and then again when they are. Remove the too soon
          // invocation and this continue can be dropped too.
          continue;
        }
        if (!_.contains(visible, control)) {
          visible.push(control);
          toRender.push(control);
        }
      }
      this.renderStep(toRender, ++this.draw_visible_call_count);
    }, 100, {leading: true}),
    renderStep: function renderStep(toRender, count) {
      // If there is nothing left to render or if draw_visible was run while
      // rendering we simply terminate.
      if (toRender.length === 0 || this.draw_visible_call_count > count) {
        return;
      }
      toRender[0].draw_node();
      setTimeout(function () {
        renderStep(toRender.slice(1), count);
      }, 0);
    },
    _last_scroll_top: 0,

    _is_scrolling_up: false,

    '{scroll_element} scroll': function (el, ev) {
      this._is_scrolling_up = this._last_scroll_top > el.scrollTop();
      this._last_scroll_top = el.scrollTop();
      this.draw_visible();
    },

    '{scroll_element} resize': function (el, ev) {
      setTimeout(this.draw_visible.bind(this), 0);
    },

    '.tree-item-placeholder click': function (el, ev) {
      var node = el.control();
      node.draw_node();
      node.select();
    },

    '{original_list} add': function (list, ev, newVals, index) {
      var that = this;
      var realAdd = [];

      can.each(newVals, function (newVal) {
        var _newVal = newVal.instance ? newVal.instance : newVal;
        if (that.oldList && ~can.inArray(_newVal, that.oldList)) {
          that.oldList.splice(can.inArray(_newVal, that.oldList), 1);
        } else if (that.element) {
          realAdd.push(newVal);
        }
      });
      this.enqueue_items(realAdd);
    },

    '{original_list} remove': function (list, ev, oldVals, index) {
      var removeMarker = {}; // Empty object used as unique marker
      var removedObjectType;
      var skipInfoPinRefresh = false;

      //  FIXME: This assumes we're replacing the entire list, and corrects for
      //    instances being removed and immediately re-added.  This should be
      //    changed to support exact mirroring of the order of
      //    `this.options.list`.
      if (!this.oldList) {
        this.oldList = [];
      }
      this.oldList.push.apply(
        this.oldList,
        can.map(oldVals, function (v) {
          return v.instance ? v.instance : v;
        }));

      // If a removed object is a Document or a Person, it is likely that it
      // was removed from the info pin, thus refreshing the latter is not needed.
      // The check will fail, though, if the info pane was displaying a person
      // located in a subtree, and we unmapped that person from the object
      // displayed in the parent tree view node.
      if (oldVals.length === 1 && oldVals[0].instance) {
        removedObjectType = oldVals[0].instance.type;
        if (removedObjectType === 'Person' ||
          removedObjectType === 'Document') {
          skipInfoPinRefresh = true;
        }
      }

      // `remove_marker` is to ensure that removals are not attempted until 20ms
      //   after the *last* removal (e.g. for a series of removals)
      this._remove_marker = removeMarker;
      setTimeout(this._ifNotRemoved(function () {
        if (this._remove_marker === removeMarker) {
          can.each(this.oldList, function (v) {
            this.element.trigger('removeChildNode', v);
          }.bind(this));
          this.oldList = null;
          this._remove_marker = null;

          if (skipInfoPinRefresh) {
            return;
          }

          // TODO: This is a workaround. We need to update communication between
          //       info-pin and tree views through Observer
          if (!this.element.closest('.cms_controllers_info_pin').length) {
            $('.cms_controllers_info_pin').control().unsetInstance();
          }
          this.show_info_pin();
        }
      }.bind(this)), 200);
    },

    '.tree-structure subtree_loaded': function (el, ev) {
      var instanceId;
      var parent;
      ev.stopPropagation();
      instanceId = el.closest('.tree-item').data('object-id');
      parent = can.reduce(this.options.list, function (a, b) {
        switch (true) {
          case !!a : return a;
          case b.instance.id === instanceId: return b;
          default: return null;
        }
      }, null);
      if (parent && !parent.children_drawn) {
        parent.attr('children_drawn', true);
      }
    },
    // add child options to every item (TreeViewOptions instance) in the drawing list at this level of the tree.
    add_child_lists: function (list) {
      var that = this;
      var currentList = can.makeArray(list);
      var listWindow = [];
      var finalDfd;
      var queue = [];
      var BATCH = 200;
      var opId = this._add_child_lists_id = (this._add_child_lists_id || 0) + 1;

      can.each(currentList, function (item) {
        listWindow.push(item);
        if (listWindow.length >= BATCH) {
          queue.push(listWindow);
          listWindow = [];
        }
      });
      if (listWindow.length > 0) {
        queue.push(listWindow);
      }
      this.options.attr('filter_shown', 0);
      this.options.attr('filteredList', []);
      finalDfd = _.foldl(queue, function (dfd, listWindow) {
        return dfd.then(function () {
          var res = can.Deferred();
          if (that._add_child_lists_id !== opId) {
            return dfd;
          }
          setTimeout(function () {
            var draw;
            var drawDfd;
            if (that._add_child_lists_id !== opId) {
              return;
            }
            draw = that._ifNotRemoved(that.draw_items.bind(that));

            drawDfd = draw(listWindow);

            if (drawDfd) {
              drawDfd.then(res.resolve);
            } else {
              res.resolve();
            }
          }, 0);
          return res;
        });
      }, can.Deferred().resolve());

      finalDfd.done(this._ifNotRemoved(function () {
        var shown = this.element[0].children.length;
        var count = this.options.list.length;
        // We need to hide `of` in case the numbers are same
        if (shown === count && shown > 0) {
          shown = false;
        } else {
          shown = shown.toString();
        }
        this.options.attr('filter_shown', shown);
        this.options.attr('filter_count', count.toString());

        this.update_header();
      }.bind(this)));
      return finalDfd;
    },
    update_header: function () {
      var treeFilter;
      var headerContentHeight;
      var elementParent;

      if (!this.element || !this.element.parent) {
        return;
      }

      elementParent = this.element.parent();
      treeFilter = elementParent.find('.tree-header-content');

      if (treeFilter.length === 0) {
        return;
      }

      headerContentHeight = treeFilter.height();

      this.element.css('margin-top', headerContentHeight);
    },
    draw_items: function (optionsList) {
      var items;
      var $footer = this.element.children('.tree-item-add').first();
      var drawItemsDfds = [];
      var filteredItems = this.options.attr('filteredList') || [];
      var res;

      items = can.makeArray(optionsList);

      items = _.map(items, function (options) {
        var control;
        var elem = document.createElement('li');
        if (this.options.disable_lazy_loading) {
          options.disable_lazy_loading = true;
        }
        control = new CMS.Controllers.TreeViewNode(elem, options);
        drawItemsDfds.push(control._draw_node_deferred);
        filteredItems.push(control);
        return control.element[0];
      }.bind(this));

      if ($footer.length) {
        $(items).insertBefore($footer);
      } else {
        this.element.append(items);
      }
      if (this.options.sortable) {
        $(this.element).sortable({element: 'li.tree-item', handle: '.drag'});
      }
      this.options.attr('filteredList', filteredItems);
      res = $.when.apply($, drawItemsDfds);

      res.then(function () {
        _.defer(this.draw_visible.bind(this));
      }.bind(this)).always(function () {
        if (this.options.is_subtree) {
          if (this.options.attr('showAllRelated')) {
            this.addSubTreeShowRelated();
          }

          if (this.options.drawSubTreeExpander) {
            this.addSubTreeExpander(items);
          }
        }
      }.bind(this));
      return res;
    },

    insertSubTreeLink: function (view, element) {
      if (element.length) {
        $(view).insertBefore(element);
      } else {
        this.element.append(view);
      }
    },

    addSubTreeShowRelated: function () {
      var treeOptions = this.options;
      var options = {
        showAllRelated: treeOptions.attr('showAllRelated'),
        showAllRelatedLink: treeOptions.parent_instance ?
          treeOptions.parent_instance.viewLink :
          ''
      };
      var relatedLink = can.view(GGRC.mustache_path +
       '/base_objects/sub_tree_all_related_link.mustache', options);
      var element = this.element.find('.not-directly-related:first');

      this.insertSubTreeLink(relatedLink, element);
    },

    addSubTreeExpander: function () {
      var element;
      var options;
      var expander;
      var self = this;

      if (this.element.find('.sub-tree-expander').length) {
        return;
      }

      this.element.addClass('not-directly-related-hide');

      element = this.element.find('.not-directly-related:first');
      options = {
        expanded: false,
        disabled: !element.length,
        onChangeState: self.showNotDirectlyMappedObjects.bind(self)
      };
      expander = can.view(GGRC.mustache_path +
        '/base_objects/sub_tree_expand.mustache', options);

      this.insertSubTreeLink(expander, element);
    },

    ' removeChildNode': function (el, ev, data) { // eslint-disable-line quote-props
      var that = this;
      var instance;

      if (data.instance && data.instance instanceof this.options.model) {
        instance = data.instance;
      } else {
        instance = data;
      }

      //  FIXME: This should be done using indices, when the order of elements
      //    is guaranteed to mirror the order of `this.options.list`.

      //  Replace the list with the list sans the removed instance
      that.options.list.replace(
        can.map(this.options.list, function (options, i) {
          if (options.instance !== instance) {
            return options;
          }
        }));

      //  Remove items by data attributes
      that.element.children([
        '[data-object-id=' + instance.id + ']',
        '[data-object-type=' + instance.constructor.table_singular + ']'
      ].join('')).remove();
      ev.stopPropagation();
    },

    ' updateCount': function (el, ev) { // eslint-disable-line quote-props
      // Suppress events from sub-trees
      if (!($(ev.target)
          .closest('.' + this.constructor._fullName).is(this.element))) {
        ev.stopPropagation();
      }
    },

    widget_hidden: function (event) {
      if (this.options.original_list) {
        this.clearList();
      }
      if (this._add_child_lists_id) {
        this._add_child_lists_id += 1;
      }

      this.triggerListeners(true);

      return false;
    },

    widget_shown: function (event) {
      if (this.options.original_list) {
        setTimeout(this.reload_list.bind(this), 0);
      }

      this.triggerListeners();

      $('body').on('treeupdate', this.refreshList.bind(this));
      this.update_header();
      return false;
    },

    _verifyRelationship: function (instance, shortName) {
      if (!(instance instanceof CMS.Models.Relationship)) {
        return false;
      }
      if (instance.destination &&
        (instance.destination.type === shortName ||
         instance.destination.type === 'Snapshot')) {
        return true;
      }
      if (instance.source &&
        (instance.source.type === shortName ||
         instance.source.type === 'Snapshot')) {
        return true;
      }
      return false;
    },

    triggerListeners: (function () {
      var activeTabModel;
      var self;

      function onCreated(ev, instance) {
        var parentInstance = self.options.parent_instance;

        function callback() {
          parentInstance.unbind('change', callback);
          _refresh(true);
        }

        if (self._verifyRelationship(instance, activeTabModel)) {
          parentInstance.on('change', callback);
        } else if (activeTabModel === instance.type) {
          _refresh(true);
        } else if (activeTabModel === 'Person' &&
          _.includes(['ObjectPerson', 'WorkflowPerson', 'UserRole'],
            instance.type)) {
          _refresh();
        }
      }

      function onDestroyed(ev, instance) {
        var current;
        var destType;
        var srcType;

        if (self._verifyRelationship(instance, activeTabModel) ||
          instance instanceof CMS.Models[activeTabModel]) {
          if (self.options.attr('original_list').length === 1) {
            current = self.options.attr('paging.current');
            self.options.attr('paging.current',
              current > 1 ? current - 1 : 1);
          }

          // if unmapping e.g. an URL (a "Document") or an assignee from
          // the info pin, refreshing the latter is not needed
          if (instance instanceof CMS.Models.Relationship) {
            srcType = instance.source ?
              instance.source.type : null;
            destType = instance.destination ?
              instance.destination.type : null;
            if (srcType === 'Person' || destType === 'Person' ||
              srcType === 'Document' || destType === 'Document') {
              return;
            }
          }

          _refresh();

          // TODO: This is a workaround.We need to update communication between
          //       info-pin and tree views through Observer
          if (!self.element.closest('.cms_controllers_info_pin').length) {
            $('.cms_controllers_info_pin').control().unsetInstance();
          }
          self.show_info_pin();
        }
      }

      function _refresh(sortByUpdatedAt) {
        if (sortByUpdatedAt) {
          self.options.attr('paging.sortDirection', 'desc');
          self.options.attr('paging.sortBy', 'updated_at');
          self.options.attr('paging.current', 1);
        }
        self.refreshList();
      }

      return function (needDestroy) {
        activeTabModel = this.options.model.shortName;
        self = this;
        if (needDestroy) {
          // Remove listeners for inactive tabs
          can.Model.Cacheable.unbind('created', onCreated);
          can.Model.Cacheable.unbind('destroyed', onDestroyed);
        } else {
          // Add listeners on creations instance or mappings objects for current tab
          // and refresh page after that.
          can.Model.Cacheable.bind('created', onCreated);
          can.Model.Cacheable.bind('destroyed', onDestroyed);
        }
      };
    })(),

    '.edit-object modal:success': function (el, ev, data) {
      var model = el.closest('[data-model]').data('model');
      model.attr(data[model.constructor.root_object] || data);
      ev.stopPropagation();
    },

    reload_list: function (forceReload) {
      if (this.options.list === undefined || this.options.list === null) {
        return;
      }
      this._draw_list_deferred = false;
      this._is_scrolling_up = false;
      this.find_all_deferred = false;
      this.options.list.replace([]);
      this.draw_list(this.options.original_list, true, forceReload);
      this.init_count();
    },

    '[custom-event] click': function (el, ev) {
      var eventName = el.attr('custom-event');
      if (this.options.events &&
        typeof this.options.events[eventName] === 'function') {
        this.options.events[eventName].apply(this, arguments);
      }
    },

    loadTreeStates: function (modelName) {
      // Get the status list from local storage
      var savedStateList;
      savedStateList = this.display_prefs.getTreeViewStates(modelName);

      if (savedStateList.length === 0) {
        savedStateList = GGRC.Utils
          .State.getDefaultStatesForModel(this.options.model.shortName);
      }

      this.options.attr('selectStateList', savedStateList);
    },
    saveTreeStates: function (selectedStates) {
      var stateToSave = [];

      // in this case we save previous states
      if (!selectedStates) {
        return;
      }

      stateToSave = selectedStates.map(function (state) {
        return state.value;
      });

      this.options.attr('selectStateList', stateToSave);
      this.display_prefs.setTreeViewStates(this.options.model.model_singular,
        stateToSave);
    },
    /* Update the tree attributes as selected by the user CORE-1546
     */
    set_tree_attrs: function (event) {
      // update the display attrbute list and re-draw
      // 1: find checked items
      // 2. update
      var target = $(event.target);
      var attrToSave = [];
      var $check = target.parent().find('.attr-checkbox');
      var $selected = $check.filter(':checked');
      var selectedItems = [];

      $selected.each(function (index) {
        selectedItems.push(this.value);
      });

      can.each(this.options.select_attr_list, function (item) {
        item.display_status = selectedItems.indexOf(item.attr_name) !== -1;
      });

      this.options.attr('select_attr_list', this.options.select_attr_list);
      this.options.display_attr_list = [];

      can.each(this.options.select_attr_list, function (item) {
        if (!item.mandatory && item.display_status) {
          this.options.display_attr_list.push(item);
        }
      }, this);
      this.options.attr('display_attr_list', this.options.display_attr_list);
      this.setup_column_width();

      this.reload_list(true);
      // set user preferences for next time
      can.each(this.options.display_attr_list, function (item) {
        attrToSave.push(item.attr_name);
      });
      this.display_prefs.setTreeViewHeaders(this.options.model.model_singular,
        attrToSave);
      this.display_prefs.save();

      can.bind.call(this.element.parent().find('.widget-col-title[data-field]'),
        'click', this.sort.bind(this));
    },

    set_tree_display_list: function (modelName, selectedItems) {
      var i;
      var el;
      var openItems;
      var control;
      var tviewEl;

      if (!modelName) {
        return;
      }

      // update GGRC.tree_view
      GGRC.tree_view.sub_tree_for.attr(modelName + '.display_list',
        selectedItems);

      // save in local storage
      this.display_prefs.setChildTreeDisplayList(modelName, selectedItems);

      // check if any inner tree is open
      el = this.element;
      if (el.hasClass('tree-open')) {
        // find the inner tree and reload it
        openItems = el.find('.item-open .cms_controllers_tree_view');

        for (i = 0; i < openItems.length; i++) {
          tviewEl = $(openItems[i]);
          control = tviewEl.control();
          if (control) {
            control.reload_list();
          }
        }
      }
    },

    sort: function (event) {
      var $el = $(event.currentTarget);
      var key = $el.data('field');
      var order;

      if (key !== this.options.attr('paging.sortBy')) {
        this.options.attr('paging.sortDirection', null);
      }

      order =
        this.options.attr('paging.sortDirection') === 'asc' ? 'desc' : 'asc';

      this.options.attr('paging.sortDirection', order);
      this.options.attr('paging.sortBy', key);

      $el.closest('.tree-header')
        .find('.widget-col-title')
        .removeClass('asc')
        .removeClass('desc');

      $el.addClass(order);

      this.options.attr('paging.current', 1);
      this.refreshList();
    },

    filter: function (filterString, selectedStates) {
      this.saveTreeStates(selectedStates);
      this.options.attr('paging.filter', filterString);
      this.options.attr('paging.current', 1);
      this.refreshList();
    },

    buildSubTreeCountMap: function (originalOrder, relevant, elementsLimit) {
      var self = this;
      var queryAPI = GGRC.Utils.QueryAPI;
      var currentElementsCount = 0;
      var countQuery = queryAPI.buildCountParams(originalOrder, relevant);

      return queryAPI.makeRequest({data: countQuery}).then(function (response) {
        var countMap = [];

        response.forEach(function (item) {
          var count;
          var propertyName = originalOrder.find(function (type) {
            return item[type];
          });

          var obj = {
            type: propertyName,
            count: item[propertyName].total
          };

          self.options.attr('showAllRelated',
            currentElementsCount >= elementsLimit);

          if (self.options.attr('showAllRelated') || obj.count === 0) {
            return;
          }

          if (elementsLimit - currentElementsCount >= obj.count) {
            count = obj.count;
          } else {
            count = elementsLimit - currentElementsCount;
            self.options.attr('showAllRelated', true);
          }

          currentElementsCount += count;

          countMap.push({
            type: obj.type,
            count: count
          });
        });

        return countMap;
      });
    },

    loadSubTree: function () {
      var parent = this.options.parent_instance;
      var parentCtrl = this.element.closest('section')
        .find('.cms_controllers_tree_view').control();
      var snapshots = GGRC.Utils.Snapshots;
      var relevant = {
        type: parent.type,
        id: snapshots.isSnapshot(parent) ? parent.snapshot.child_id : parent.id,
        operation: 'relevant'
      };
      var originalOrder = GGRC.Utils.TreeView.getModelsForSubTier(parent.type);
      var limit = this.options.subTreeElementsLimit;
      var typeModels;
      var fields = [
        'child_id',
        'child_type',
        'context',
        'email',
        'id',
        'is_latest_revision',
        'name',
        'revision',
        'revisions',
        'selfLink',
        'slug',
        'status',
        'title',
        'type',
        'viewLink',
        'workflow_state',
        // labels for assessment templates
        'DEFAULT_PEOPLE_LABELS'
      ];

      if (!originalOrder.length) {
        originalOrder = GGRC.Mappings.getMappingList(parent.type);
      }

      if (GGRC.Utils.CurrentPage.getPageType() === 'Workflow') {
        typeModels = originalOrder.map(function (item) {
          var typeModels = {
            type: item,
            fields: [],
            page: parent.type === 'CycleTaskGroup' ?
              {sortBy: 'task due date'} :
              {}
          };
          var rootFilter = parentCtrl.options.attr('paging.filter');
          if (rootFilter) {
            typeModels.filter = GGRC.query_parser.parse(rootFilter);
          }

          return typeModels;
        });

        return this.loadSubTreeData(typeModels, relevant);
      }

      return this.buildSubTreeCountMap(originalOrder, relevant, limit)
        .then(function (countMap) {
          countMap.forEach(function (item) {
            item.fields = fields;
            item.page = {current: 1, pageSize: item.count};
          });

          return this.loadSubTreeData(countMap, relevant);
        }.bind(this));
    },

    loadSubTreeData: function (typeModels, relevant) {
      var queryAPI = GGRC.Utils.QueryAPI;
      var reqParams = typeModels.map(function (model) {
        return queryAPI.buildParam(
          model.type, model.page, relevant, model.fields, model.filter);
      });

      return this.page_loader.load({data: reqParams},
        typeModels.map(function (item) {
          return item.type;
        }));
    },

    loadPage: function () {
      var options = this.options;
      var queryAPI = GGRC.Utils.QueryAPI;
      var modelName = options.model.shortName;
      var states = options.attr('selectStateList');
      var statesFilter = GGRC.Utils.State.statusFilter(states, '', modelName);
      var isStateQuery = statesFilter !== '';
      var additionalFilter = options.additional_filter ?
        [options.additional_filter, statesFilter] :
        statesFilter;
      var filter = !GGRC.Utils.State.hasState(modelName) ?
        options.additional_filter :
        GGRC.query_parser.parse(additionalFilter);
      var params = queryAPI.buildParam(
        modelName,
        options.paging,
        GGRC.Utils.TreeView.makeRelevantExpression(modelName,
          options.parent_instance.type, options.parent_instance.id),
        undefined,
        filter
      );

      this._draw_list_deferred = false;
      return this.page_loader.load({data: [params]})
        .then(function (data) {
          var total = data.total;
          var countsName = this.options.countsName || modelName;
          var currentPageUtils = GGRC.Utils.CurrentPage;

          this.options.attr('paging.total', total);
          this.options.attr('paging.count',
            Math.ceil(data.total / this.options.paging.pageSize));

          if (!this.options.paging.filter && !isStateQuery &&
            total !== currentPageUtils.getCounts().attr(countsName)) {
            currentPageUtils.getCounts().attr(countsName, total);
          }
          if (isStateQuery) {
            currentPageUtils.initCounts([modelName],
                options.parent_instance.type, options.parent_instance.id);
          }

          return data.values;
        }.bind(this));
    },

    clearList: function () {
      this.element.children('.tree-item, .tree-item-placeholder').remove();
    },

    refreshList: function () {
      if (this.options.attr('paging.disabled')) {
        return;
      }
      this.options.attr('paging.disabled', true);
      this._loading_started();
      this.loadPage()
        .then(function (data) {
          this.clearList();
          return data;
        }.bind(this))
        .then(this._ifNotRemoved(this.proxy('draw_list')))
        .then(function () {
          this.options.attr('paging.disabled', false);
        }.bind(this))
        .fail(function () {
          this.options.attr('paging.disabled', false);
          this.options.attr('original_list', []);
          this.clearList();
          this._loading_finished();
          GGRC.Errors.notifier('warning',
            'Filter format is incorrect, data cannot be filtered.');
        }.bind(this));
    },
    showNotDirectlyMappedObjects: function (isVisible) {
      if (_.isBoolean(isVisible)) {
        this.element.toggleClass('not-directly-related-hide', !isVisible);
      }
    },
    '{paging} change': _.debounce(
      function (object, event, type, action, newVal, oldVal) {
        if (oldVal !== newVal && _.contains(['current', 'pageSize'], type)) {
          this.refreshList();
        }
      })
  });
})(window.can, window.$);
