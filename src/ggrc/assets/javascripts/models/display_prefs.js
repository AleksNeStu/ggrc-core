/*!
    Copyright (C) 2017 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

//= require can.jquery-all
//= require models/local_storage

(function(can, $){

var COLLAPSE = "collapse",
  LHN_SIZE = "lhn_size",
  OBJ_SIZE = "obj_size",
  SORTS = "sorts",
  HEIGHTS = "heights",
  COLUMNS = "columns",
  PBC_LISTS = "pbc_lists",
  GLOBAL = "global",
  LHN_STATE = "lhn_state",
  TOP_NAV = "top_nav",
  FILTER_WIDGET = "filter_widget",
  TREE_VIEW_HEADERS = "tree_view_headers",
  TREE_VIEW_STATES = "tree_view_states",
  TREE_VIEW = "tree_view",
  CHILD_TREE_DISPLAY_LIST = "child_tree_display_list",
  MODAL_STATE = "modal_state",
  path = window.location.pathname.replace(/\./g, "/");

can.Model.LocalStorage("CMS.Models.DisplayPrefs", {
  autoupdate: true,
  version: 20150129, // Last updated to add 2 accessors

  findAll: function () {
    var that = this;
    var objs_dfd = this._super.apply(this, arguments)
    .then(function (objs) {
      var i;
      for (i = objs.length; i--;) {
        if (!objs[i].version || objs[i].version < that.version) {
          objs[i].destroy();
          objs.splice(i, 1);
        }
      }
      return objs;
    });
    return objs_dfd;
  },

  findOne: function () {
    var that = this;
    var obj_dfd = this._super.apply(this, arguments)
    .then(function (obj) {
      var dfd, p;
      if (!obj.version || obj.version < that.version) {
        obj.destroy();
        dfd = new $.Deferred();
        p = dfd.promise();
        p.status = 404;
        return dfd.reject(p, "error", "Object expired");
      } else {
        return obj;
      }
    });
    return obj_dfd;
  },

  create: function (opts) {
    opts.version = this.version;
    return this._super(opts);
  },

  update: function (id, opts) {
    opts.version = this.version;
    return this._super(id, opts);
  },

  getSingleton: function () {
    var deferred,
        prefs;
    if (this.cache) {
      return $.when(this.cache);
    }

    this.findAll().then(function (d) {
      if (d.length > 0) {
        prefs = d[0];
      } else {
        prefs = new CMS.Models.DisplayPrefs();
        prefs.save();
      }
    });
    this.cache = prefs;
    return $.when(prefs);
  }
}, {
  init: function () {
    this.autoupdate = this.constructor.autoupdate;
  },

  makeObject: function () {
    var retval = this;
    var args = can.makeArray(arguments);
    can.each(args, function (arg) {
      var tval = can.getObject(arg, retval);
      if (!tval || !(tval instanceof can.Observe)) {
        tval = new can.Observe(tval);
        retval.attr(arg, tval);
      }
      retval = tval;
    });
    return retval;
  },

  getObject: function () {
    var args = can.makeArray(arguments);
    args[0] === null && args.splice(0,1);
    return can.getObject(args.join("."), this);
  },

  // collapsed state
  // widgets on a page may be collapsed such that only the title bar is visible.
  // if page_id === null, this is a global value
  setCollapsed: function (page_id, widget_id, is_collapsed) {
    this.makeObject(page_id === null ? page_id : path, COLLAPSE).attr(widget_id, is_collapsed);

    this.autoupdate && this.save();
    return this;
  },

  getCollapsed: function (page_id, widget_id) {
    var collapsed = this.getObject(page_id === null ? page_id : path, COLLAPSE);
    if (!collapsed) {
      collapsed = this.makeObject(page_id === null ? page_id : path, COLLAPSE).attr(this.makeObject(COLLAPSE, page_id).serialize());
    }

    return widget_id ? collapsed.attr(widget_id) : collapsed;
  },

  setTopNavHidden: function (page_id, is_hidden) {
    this.makeObject(page_id === null ? page_id : path, TOP_NAV).attr("is_hidden", !!is_hidden);

    this.autoupdate && this.save();
    return this;
  },

  getTopNavHidden: function (page_id) {
    var value = this.getObject(page_id === null ? page_id : path, TOP_NAV);

    if (typeof value === "undefined") {
      this.setTopNavHidden("", false);
      return false;
    }

    return !!value.is_hidden;
  },

  setTopNavWidgets: function (page_id, widget_list) {
    this.makeObject(page_id === null ? page_id : path, TOP_NAV).attr("widget_list", widget_list);

    this.autoupdate && this.save();
    return this;
  },

  getTopNavWidgets: function (page_id) {
    var value = this.getObject(page_id === null ? page_id : path, TOP_NAV);

    if (typeof value === "undefined") {
      this.setTopNavWidgets(page_id, {});
      return this.getTopNavWidgets(page_id);
    }

    return value.widget_list && value.widget_list.serialize() || {};
  },

  setFilterHidden: function (is_hidden) {
    this.makeObject(path, FILTER_WIDGET).attr("is_hidden", is_hidden);

    this.autoupdate && this.save();
    return this;
  },

  getFilterHidden: function () {
    var value = this.getObject(path, FILTER_WIDGET);

    if (typeof value === "undefined") {
      this.setFilterHidden(false);
      return false;
    }

    return value.is_hidden;
  },

  setTreeViewHeaders: function (model_name, display_list) {
    var hdr = this.getObject(path, TREE_VIEW_HEADERS), obj = {};
    if (!hdr) {
      hdr = this.makeObject(path, TREE_VIEW_HEADERS);
    }

    obj.display_list = display_list;
    hdr.attr(model_name, obj);

    this.autoupdate && this.save();
    return this;
  },

  getTreeViewHeaders: function (model_name) {
    var value = this.getObject(path, TREE_VIEW_HEADERS);

    if (!value || !value[model_name]) {
      return [];
    }

    return value[model_name].display_list;
  },

  setTreeViewStates: function (model_name, status_list) {
    var hdr = this.getObject(path, TREE_VIEW_STATES), obj = {};
    if (!hdr) {
      hdr = this.makeObject(path, TREE_VIEW_STATES);
    }
    obj.status_list = status_list;
    hdr.attr(model_name, obj);

    this.autoupdate && this.save();
    return this;
  },

  getTreeViewStates: function (model_name) {
    var value = this.getObject(path, TREE_VIEW_STATES);

    if (!value || !value[model_name]) {
      return ['Active'];
    }

    return value[model_name].status_list;
  },

  setModalState: function (model_name, display_state) {
    var path = null, modal_state = this.getObject(path, MODAL_STATE), obj = {};

    if (!modal_state) {
      modal_state = this.makeObject(path, MODAL_STATE);
    }

    obj.display_state = display_state;
    modal_state.attr(model_name, obj);

    this.autoupdate && this.save();
    return this;
  },

  getModalState: function (model_name) {
    var modal_state = this.getObject(null, MODAL_STATE);

    if (!modal_state || !modal_state[model_name]) {
      return null;
    }

    return modal_state[model_name].display_state;
  },

  setChildTreeDisplayList: function (model_name, display_list) {
    var hdr = this.getObject(TREE_VIEW, CHILD_TREE_DISPLAY_LIST), obj = {};
    if (!hdr) {
      hdr = this.makeObject(TREE_VIEW, CHILD_TREE_DISPLAY_LIST);
    }

    obj.display_list = display_list;
    hdr.attr(model_name, obj);

    this.autoupdate && this.save();
    return this;
  },

  getChildTreeDisplayList: function (model_name) {
    var value = this.getObject(TREE_VIEW, CHILD_TREE_DISPLAY_LIST);

    if (!value || !value[model_name]) {
      return null; //in this case user should use default list an empty list, [], is different  than null
    }

    return value[model_name].display_list;
  },

  setLHNavSize: function (page_id, widget_id, size) {
    this.makeObject(page_id === null ? page_id : path, LHN_SIZE).attr(widget_id, size);
    this.autoupdate && this.save();
    return this;
  },

  getLHNavSize: function (page_id, widget_id) {
    var size = this.getObject(page_id === null ? page_id : path, LHN_SIZE);
    if (!size) {
      size = this.makeObject(page_id === null ? page_id : path, LHN_SIZE).attr(this.makeObject(LHN_SIZE, page_id).serialize());
    }

    return widget_id ? size.attr(widget_id) : size;
  },

  setGlobal: function (widget_id, attrs) {
    var global = this.getObject(null, GLOBAL) && this.getObject(null, GLOBAL).attr(widget_id);
    if (!global) {
      global = this.makeObject(null, GLOBAL).attr(widget_id, new can.Observe(attrs));
    } else {
      global.attr(attrs);
    }
    this.autoupdate && this.save();
    return this;
  },

  getGlobal: function (widget_id) {
    return this.getObject(null, GLOBAL) && this.getObject(null, GLOBAL).attr(widget_id);
  },

  // sorts = position of widgets in each column on a page
  // This is also use at page load to determine which widgets need to be
  // generated client-side.
  getSorts: function (page_id, column_id) {
    var sorts = this.getObject(path, SORTS);
    if (!sorts) {
      sorts = this.makeObject(path, SORTS).attr(this.makeObject(SORTS, page_id).serialize());
      this.autoupdate && this.save();
    }

    return column_id ? sorts.attr(column_id) : sorts;
  },

  setSorts: function (page_id, widget_id, sorts) {
    if (typeof sorts === "undefined" && typeof widget_id === "object") {
      sorts = widget_id;
      widget_id = undefined;
    }
    var page_sorts = this.makeObject(path, SORTS);

    page_sorts.attr(widget_id ? widget_id : sorts, widget_id ? sorts : undefined);

    this.autoupdate && this.save();
    return this;
  },

  // heights : height of widgets to restore on page start.
  // Is set by jQuery-UI resize functions in ResizeWidgetsController
  getWidgetHeights: function (page_id) {
    var heights = this.getObject(path, HEIGHTS);
    if (!heights) {
      heights = this.makeObject(path, HEIGHTS).attr(this.makeObject(HEIGHTS, page_id).serialize());
      this.autoupdate && this.save();
    }
    return heights;
  },

  getWidgetHeight: function (page_id, widget_id) {
    return this.getWidgetHeights(page_id)[widget_id];
  },

  setWidgetHeight: function (page_id, widget_id, height) {
    var page_heights = this.makeObject(path, HEIGHTS);

    page_heights.attr(widget_id, height);

    this.autoupdate && this.save();
    return this;
  },

  // columns : the relative width of columns on each page.
  //  should add up to 12 since we're using row-fluid from Bootstrap
  getColumnWidths: function (page_id, content_id) {
    var widths = this.getObject(path, COLUMNS);
    if (!widths) {
      widths = this.makeObject(path, COLUMNS).attr(this.makeObject(COLUMNS, page_id).serialize());
      this.autoupdate && this.save();
    }
    return widths[content_id];
  },

  getColumnWidthsForSelector: function (page_id, sel) {
    return this.getColumnWidths(page_id, $(sel).attr("id"));
  },

  setColumnWidths: function (page_id, widget_id, widths) {
    var csp = this.makeObject(path, COLUMNS);
    csp.attr(widget_id, widths);
    this.autoupdate && this.save();
    return this;
  },

  // reset function currently resets all layout for a page type (first element in URL path)
  resetPagePrefs: function () {
    this.removeAttr(path);
    return this.save();
  },

  setPageAsDefault: function (page_id) {
    var that = this;
    can.each([COLLAPSE, LHN_SIZE, OBJ_SIZE, SORTS, HEIGHTS, COLUMNS], function(key) {
      that.makeObject(key).attr(page_id, new can.Observe(that.makeObject(path, key).serialize()));
    });
    this.save();
    return this;
  },

  getPbcListPrefs: function (pbc_id) {
    return this.makeObject(PBC_LISTS, pbc_id);
  },

  setPbcListPrefs: function (pbc_id, prefs) {
    this.makeObject(PBC_LISTS).attr(pbc_id, prefs instanceof can.Observe ? prefs : new can.Observe(prefs));
    this.autoupdate && this.save();
  },

  getPbcResponseOpen: function (pbc_id, response_id) {
    return this.makeObject(PBC_LISTS, pbc_id, "responses").attr(response_id);
  },

  getPbcRequestOpen: function (pbc_id, request_id) {
    return this.makeObject(PBC_LISTS, pbc_id, "requests").attr(request_id);
  },

  setPbcResponseOpen: function (pbc_id, response_id, is_open) {
    var prefs = this.makeObject(PBC_LISTS, pbc_id, "responses").attr(response_id, is_open);

    this.autoupdate && this.save();
    return this;
  },

  setPbcRequestOpen: function (pbc_id, request_id, is_open) {
    var prefs = this.makeObject(PBC_LISTS, pbc_id, "requests").attr(request_id, is_open);

    this.autoupdate && this.save();
    return this;
  },

  getLHNState: function () {
    return this.makeObject(LHN_STATE);
  },

  setLHNState: function (new_prefs, val) {
    var prefs = this.makeObject(LHN_STATE);
    can.each(
      ["open_category", "panel_scroll", "category_scroll", "search_text", "my_work", "filter_params", "is_open", "is_pinned"]
      , function (token) {
        if (typeof new_prefs[token] !== "undefined") {
          prefs.attr(token, new_prefs[token]);
        } else if (new_prefs === token && typeof val !== "undefined") {
          prefs.attr(token, val);
        }
      }
    );

    this.autoupdate && this.save();
    return this;
  }

});

  if (typeof jasmine !== "undefined") {
    CMS.Models.DisplayPrefs.exports = {
      COLLAPSE: COLLAPSE,
      SORTS: SORTS,
      HEIGHTS: HEIGHTS,
      COLUMNS: COLUMNS,
      GLOBAL: GLOBAL,
      PBC_LISTS: PBC_LISTS,
      path: path
    };
  }

})(this.can, this.can.$);
