/*!
    Copyright (C) 2017 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

(function (_, can, GGRC, CMS) {
  can.Control('GGRC.Controllers.InfoWidget', {
    defaults: {
      model: null,
      instance: null,
      widget_view: GGRC.mustache_path + '/base_objects/info.mustache'
    },
    init: function () {
      var that = this;
      can.$(function () {
        if (GGRC.page_object) {
          can.extend(that.defaults, {
            model: GGRC.infer_object_type(GGRC.page_object),
            instance: GGRC.page_instance()
          });
        }
      });
    }
  }, {
    init: function () {
      this.init_menu();

      if (this.element.data('widget-view')) {
        this.options.widget_view = GGRC.mustache_path +
          this.element.data('widget-view');
      }
      if (this.options.instance.info_pane_preload) {
        this.options.instance.info_pane_preload();
      }
      this.options.context = new can.Observe({
        model: this.options.model,
        instance: this.options.instance,
        start_menu: this.options.start_menu,
        object_menu: this.options.object_menu,
        error_msg: '',
        error: true
      });
      can.view(this.get_widget_view(this.element),
        this.options.context, function (frag) {
          this.element.html(frag);
        }.bind(this));
    },

    get_widget_view: function (el) {
      var widgetView = can.$(el)
          .closest('[data-widget-view]').attr('data-widget-view');
      if (widgetView && widgetView.length > 0) {
        return GGRC.mustache_path + widgetView;
      }
      return this.options.widget_view;
    },

    generate_menu_items: function (itemNames, displayPrefix) {
      displayPrefix = displayPrefix || '';
      return _.filter(_.map(itemNames, function (name) {
        if (name in CMS.Models) {
          return {
            model_name: CMS.Models[name].model_singular,
            model_lowercase: CMS.Models[name].table_singular,
            model_plural: CMS.Models[name].table_plural,
            display_name: displayPrefix + CMS.Models[name].title_singular
          };
        }
      }));
    },

    init_menu: function () {
      var names;
      if (!this.options.start_menu) {
        names = [
          'Program',
          'Audit',
          'Workflow'
        ];
        this.options.start_menu = this.generate_menu_items(names, 'Start new ');
      }
      if (!this.options.object_menu) {
        names = [
          'AccessGroup',
          'Clause',
          'Contract',
          'Control',
          'DataAsset',
          'Facility',
          'Issue',
          'Market',
          'Objective',
          'OrgGroup',
          'Person',
          'Policy',
          'Process',
          'Product',
          'Project',
          'Regulation',
          'Risk',
          'Section',
          'Standard',
          'System',
          'Threat',
          'Vendor'
        ];
        this.options.object_menu = this.generate_menu_items(names);
      }
    }
  });
})(window._, window.can, window.GGRC, window.CMS);
