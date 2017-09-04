/*!
    Copyright (C) 2017 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

(function ($, CMS, GGRC) {
  // A widget descriptor has the minimum five properties:
  // widget_id:  the unique ID string for the widget
  // widget_name: the display title for the widget in the UI
  // widget_icon: the CSS class for the widget in the UI
  // content_controller: The controller class for the widget's content section
  // content_controller_options: options passed directly to the content controller; the
  //   precise options depend on the controller itself.  They usually require instance
  //   and/or model and some view.
  can.Construct('GGRC.WidgetDescriptor', {
    /*
      make an info widget descriptor for a GGRC object
      You must provide:
      instance - an instance that is a subclass of can.Model.Cacheable
      widgetView [optional] - a template for rendering the info.
    */
    make_info_widget: function (instance, widgetView) {
      var defaultInfoWidgetView = GGRC.mustache_path +
                                     '/base_objects/info.mustache';
      return new this(
        instance.constructor.shortName + ':info', {
          widget_id: 'info',
          widget_name: function () {
            if (instance.constructor.title_singular === 'Person') {
              return 'Info';
            }
            return instance.constructor.title_singular + ' Info';
          },
          widget_icon: 'info-circle',
          content_controller: GGRC.Controllers.InfoWidget,
          content_controller_options: {
            instance: instance,
            model: instance.constructor,
            widget_view: widgetView || defaultInfoWidgetView
          },
          order: 5
        });
    },
    /*
      make an summary widget descriptor for a GGRC object
      You must provide:
      instance - an instance that is a subclass of can.Model.Cacheable
      widgetView [optional] - a template for rendering the info.
    */
    make_summary_widget: function (instance, widgetView) {
      var defaultView = GGRC.mustache_path +
        '/base_objects/summary.mustache';
      return new this(
        instance.constructor.shortName + ':summary', {
          widget_id: 'Summary',
          widget_name: function () {
            return instance.constructor.title_singular + ' Summary';
          },
          widget_icon: 'pie-chart',
          content_controller: GGRC.Controllers.SummaryWidget,
          content_controller_options: {
            instance: instance,
            model: instance.constructor,
            widget_view: widgetView || defaultView
          },
          order: 3
        });
    },
    make_dashboard_widget: function (instance, widgetView) {
      var defaultView = GGRC.mustache_path +
        '/base_objects/dashboard.mustache';
      return new this(
        instance.constructor.shortName + ':dashboard', {
          widget_id: 'dashboard',
          widget_name: function () {
            if (instance.constructor.title_singular === 'Person') {
              return 'Dashboard';
            }
            return instance.constructor.title_singular + ' Dashboard';
          },
          widget_icon: 'tachometer',
          content_controller: GGRC.Controllers.DashboardWidget,
          content_controller_options: {
            instance: instance,
            model: instance.constructor,
            widget_view: widgetView || defaultView
          },
          order: 6
        });
    },
    /*
      make a tree view widget descriptor with mostly default-for-GGRC settings.
      You must provide:
      instance - an instance that is a subclass of can.Model.Cacheable
      farModel - a can.Model.Cacheable class
      extenders [optional] - an array of objects that will extend the default widget config.
    */
    make_tree_view: function (instance, farModel, extenders, id) {
      var descriptor;
      var objectVersionConfig = GGRC.Utils.ObjectVersions
        .getWidgetConfig(id);
      // Should not even try to create descriptor if configuration options are missing
      if (!instance || !farModel) {
        console
          .debug('Arguments are missing or have incorrect format', arguments);
        return null;
      }
      descriptor = {
        widgetType: 'treeview',
        treeViewDepth: 2,
        widget_id: objectVersionConfig.isObjectVersion ?
          objectVersionConfig.widgetId :
          farModel.table_singular,
        widget_guard: function () {
          if (
            farModel.title_plural === 'Audits' &&
            instance instanceof CMS.Models.Program
          ) {
            return 'context' in instance && !!(instance.context.id);
          }
          return true;
        },
        widget_name: function () {
          var farModelName = objectVersionConfig.isObjectVersion ?
            objectVersionConfig.widgetName :
            farModel.title_plural;
          var $objectArea = $('.object-area');
          if (
            $objectArea.hasClass('dashboard-area') ||
            instance.constructor.title_singular === 'Person'
          ) {
            if (/dashboard/.test(window.location)) {
              return 'My ' + farModelName;
            }
            return farModelName;
          } else if (farModel.title_plural === 'Audits') {
            return 'Mapped Audits';
          }
          return (
            farModel.title_plural === 'References' ?
                                         'Linked ' : 'Mapped '
          ) + farModelName;
        },
        widget_icon: farModel.table_singular,
        object_category: farModel.category || 'default',
        model: farModel,
        objectVersion: objectVersionConfig.isObjectVersion,
        content_controller_options: {
          draw_children: true,
          parent_instance: instance,
          model: farModel,
          objectVersion: objectVersionConfig.isObjectVersion
        }
      };

      $.extend.apply($, [true, descriptor].concat(extenders || []));

      return new this(
        instance.constructor.shortName + ':' +
        id || instance.constructor.shortName,
        descriptor
      );
    },
    newInstance: function (id, opts) {
      var ret;
      if (!opts && typeof id === 'object') {
        opts = id;
        id = opts.widget_id;
      }

      if (GGRC.widget_descriptors[id]) {
        if (GGRC.widget_descriptors[id] instanceof this) {
          $.extend(GGRC.widget_descriptors[id], opts);
        } else {
          ret = this._super.apply(this);
          $.extend(ret, GGRC.widget_descriptors[id], opts);
          GGRC.widget_descriptors[id] = ret;
        }
        return GGRC.widget_descriptors[id];
      }

      ret = this._super.apply(this, arguments);
      $.extend(ret, opts);
      GGRC.widget_descriptors[id] = ret;
      return ret;
    }
  }, {});
})(window.can.$, window.CMS, window.GGRC);
