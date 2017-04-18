/*!
    Copyright (C) 2017 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

(function ($, CMS, GGRC) {
  /*
    WidgetList - an extensions-ready repository for widget descriptor configs.
    Create a new widget list with new GGRC.WidgetList(list_name, widget_descriptions)
      where widget_descriptions is an object with the structure:
      { <page_name> :
        { <widget_id> :
          { <widget descriptor-ready properties> },
        ...},
      ...}

    See the comments for GGRC.WidgetDescriptor for details in what is necessary to define
    a widget descriptor.
  */
  can.Construct.extend('GGRC.WidgetList', {
    modules: {},
    /*
      get_widget_list_for: return a keyed object of widget descriptors for the specified page type.

      pageType - one of a GGRC object model's shortName, or "admin"

      The widget descriptors are built on the first call of this function; subsequently they are retrieved from the
       widget descriptor cache.
    */
    get_widget_list_for: function (pageType) {
      var widgets = {};
      var descriptors = {};

      can.each(this.modules, function (module) {
        can.each(module[pageType], function (descriptor, id) {
          if (!widgets[id]) {
            widgets[id] = descriptor;
          } else {
            can.extend(true, widgets[id], descriptor);
          }
        });
      });

      can.each(widgets, function (widget, widgetId) {
        switch (widget.content_controller) {
          case GGRC.Controllers.InfoWidget:
            descriptors[widgetId] = GGRC.WidgetDescriptor.make_info_widget(
              widget.content_controller_options && widget.content_controller_options.instance || widget.instance,
              widget.content_controller_options && widget.content_controller_options.widget_view || widget.widget_view
            );
            break;
          case GGRC.Controllers.SummaryWidget:
            descriptors[widgetId] = GGRC.WidgetDescriptor.make_summary_widget(
              widget.content_controller_options &&
              widget.content_controller_options.instance ||
              widget.instance,
              widget.content_controller_options &&
              widget.content_controller_options.widget_view ||
              widget.widget_view
            );
            break;
          case CMS.Controllers.TreeView:
            descriptors[widgetId] = GGRC.WidgetDescriptor.make_tree_view(
              widget.content_controller_options && (widget.content_controller_options.instance || widget.content_controller_options.parent_instance) || widget.instance,
              widget.content_controller_options && widget.content_controller_options.model || widget.far_model || widget.model,
              widget.content_controller_options && widget.content_controller_options.mapping || widget.mapping,
              widget
            );
            break;
          default:
            descriptors[widgetId] = new GGRC.WidgetDescriptor(
                pageType + ':' + widgetId, widget);
        }
      });

      can.each(descriptors, function (descriptor, id) {
        if (!descriptor || descriptor.suppressed) {
          delete descriptors[id];
        }
      });

      return descriptors;
    },
    /*
      returns a keyed object of widget descriptors that represents the current page.
    */
    get_current_page_widgets: function () {
      return this.get_widget_list_for(
        GGRC.page_instance().constructor.shortName);
    },
    get_default_widget_sort: function () {
      return this.sort;
    }
  }, {
    init: function (name, opts, sort) {
      this.constructor.modules[name] = this;
      can.extend(this, opts);
      if (sort && sort.length) {
        this.constructor.sort = sort;
      }
    },
    /*
      Here instead of using the object format described in the class comments, you may instead
      add widgets to the WidgetList by using add_widget.

      pageType - the shortName of a GGRC object class, or "admin"
      id - the desired widget's id.
      descriptor - a widget descriptor appropriate for the widget type. FIXME - the descriptor's
        widget_id value must match the value passed as "id"
    */
    add_widget: function (pageType, id, descriptor) {
      this[pageType] = this[pageType] || {};
      if (this[pageType][id]) {
        can.extend(true, this[pageType][id], descriptor);
      } else {
        this[pageType][id] = descriptor;
      }
    },
    suppress_widget: function (pageType, id) {
      this[pageType] = this[pageType] || {};
      if (this[pageType][id]) {
        can.extend(true, this[pageType][id], {
          suppressed: true
        });
      } else {
        this[pageType][id] = {
          suppressed: true
        };
      }
    }
  });
})(window.can.$, window.CMS, window.GGRC);
