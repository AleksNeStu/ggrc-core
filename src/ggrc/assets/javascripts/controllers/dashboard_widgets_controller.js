/*!
    Copyright (C) 2017 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

import './filterable_controller';

CMS.Controllers.Filterable('CMS.Controllers.DashboardWidgets', {
  defaults: {
    model: null,
    widget_id: '',
    widget_name: '',
    widget_icon: '',
    widget_view: '/static/mustache/dashboard/object_widget.mustache',
    widget_guard: null,
    widget_initial_content: '',
    show_filter: false,
    object_category: null,
    content_selector: '.content',
    content_controller: null,
    content_controller_options: {},
    content_controller_selector: null
  }
}, {
  init: function () {
    if (!this.options.model && GGRC.page_model) {
      this.options.model = GGRC.infer_object_type(GGRC.page_object);
    }

    if (!this.options.widget_icon && this.options.model) {
      this.options.widget_icon = this.options.model.table_singular;
    }

    if (!this.options.object_category && this.options.model) {
      this.options.object_category = this.options.model.category;
    }

    this.options.widget_count = new can.Observe();

    this.element
      .addClass('widget')
      .addClass(this.options.object_category)
      .attr('id', this.options.widget_id + '_widget');

    if (this.options.widgetType && this.options.widgetType === 'treeview') {
      var counts = GGRC.Utils.CurrentPage.getCounts();

      var countsName = this.options.countsName ||
      this.options.model.shortName;
    
      if (this.options.objectVersion) {
        countsName = GGRC.Utils.ObjectVersions
          .getWidgetConfig(countsName, true)
          .widgetId;
      }

      this.options.widget_count.attr('count', '' + counts.attr(countsName));

      counts.on(countsName, function (ev, newVal, oldVal) {
        can.trigger(this.element, 'updateCount', [newVal]);
      }.bind(this));
    }
  },
  prepare: function () {
    if (this._prepare_deferred)
      return this._prepare_deferred;

    this._prepare_deferred = $.when(
      can.view(this.options.widget_view, $.when(this.options))
      , CMS.Models.DisplayPrefs.getSingleton()
    ).then(this.proxy('draw_widget'));

    return this._prepare_deferred;
  },
  draw_widget: function (frag, prefs) {

    this.element.html(frag[0]);

    var content = this.element
      , controller_content = null;

    if (prefs.getCollapsed(window.getPageToken(), this.element.attr("id"))) {

      this.element
        .find('.widget-showhide > a')
        .showhide('hide');

      content.add(this.element).css('height', '');
      if (content.is('.ui-resizable')) {
        content.resizable('destroy');
      }
    } else {
      content.trigger('min_size');
    }

    if (this.options.content_controller) {
      controller_content = this.element.find(this.options.content_selector);
      if (this.options.content_controller_selector)
        controller_content =
          controller_content.find(this.options.content_controller_selector);

      if (this.options.content_controller_options.init) {
        this.options.content_controller_options.init();
      }

      this.options.content_controller_options.show_header = true;
      this.content_controller = new this.options.content_controller(
        controller_content
        , this.options.content_controller_options
      );

      if (this.content_controller.prepare) {
        return this.content_controller.prepare();
      }
      else {
        return new $.Deferred().resolve();
      }
    }
  },
  display: function (refetch) {
    var that = this;
    var tracker_stop = GGRC.Tracker.start(
      'DashboardWidget', 'display', this.options.model.shortName
    );

    this._display_deferred = this.prepare().then(function () {
      var dfd;
      var $containerVM = that.element
        .find('tree-widget-container')
        .viewModel();
      var FORCE_REFRESH = true;

      if (!that.content_controller && $containerVM.needToRefresh()) {
        dfd = $containerVM.display(FORCE_REFRESH);
      } else if (that.options.widgetType === 'treeview') {
        dfd = $containerVM.display(refetch);
      } else if (that.content_controller && that.content_controller.display) {
        dfd = that.content_controller.display();
      } else {
        dfd = new $.Deferred().resolve();
      }

      return dfd;
    }).done(tracker_stop);

    return this._display_deferred;
  },
  'updateCount': function (el, ev, count, updateCount) {
    this.options.widget_count.attr('count', '' + count);
  },
  display_path: function (path, refetch) {
    var that = this;
    if (!that.content_controller) {
      return this.display(refetch);
    }
    return this.display().then(function () {
      if (that.content_controller && that.content_controller.display_path)
        return that.content_controller.display_path(path, refetch);
    });
  }
});
