/*!
  Copyright (C) 2017 Google Inc.
  Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

(function ($, can, CMS, GGRC) {
  var $area = $('.area').first();
  var defaults;
  var extraPageOptions;
  var instance;
  var location = window.location.pathname;
  var isAssessmentsView;
  var isObjectBrowser;
  var modelName;
  var widgetList;

  var sortByNameEmail = function (list) {
    return new list.constructor(can.makeArray(list).sort(function (a, b) {
      a = a.person || a;
      b = b.person || b;
      a = (can.trim(a.name) || can.trim(a.email)).toLowerCase();
      b = (can.trim(b.name) || can.trim(b.email)).toLowerCase();
      if (a > b) {
        return 1;
      }
      if (a < b) {
        return -1;
      }
      return 0;
    }));
  };

  var initWidgets = function () {
    // Ensure each extension has had a chance to initialize widgets
    can.each(GGRC.extensions, function (extension) {
      if (extension.init_widgets) {
        extension.init_widgets();
      }
    });
  };

  var adminListDescriptors = {
    people: {
      model: CMS.Models.Person,
      roles: new can.List(),
      init: function () {
        var self = this;
        CMS.Models.Role
          .findAll({scope__in: 'System,Admin'})
          .done(function (roles) {
            self.roles.replace(sortByNameEmail(roles));
          });
      },
      object_display: 'People',
      tooltip_view: '/static/mustache/people/object_tooltip.mustache',
      header_view:
        // includes only the filter, not the column headers
        '/static/mustache/people/filters.mustache',
      list_view: '/static/mustache/people/object_list.mustache',
      draw_children: true,
      fetch_post_process: sortByNameEmail
    },
    roles: {
      model: CMS.Models.Role,
      extra_params: {scope__in: 'System,Admin,Private Program,Workflow'},
      object_category: 'governance',
      object_display: 'Roles',
      list_view: '/static/mustache/roles/object_list.mustache',
      fetch_post_process: sortByNameEmail
    },
    events: {
      model: CMS.Models.Event,
      object_category: 'governance',
      object_display: 'Events',
      list_view: '/static/mustache/events/object_list.mustache'
    },
    custom_attributes: {
      parent_instance: CMS.Models.CustomAttributable,
      model: CMS.Models.CustomAttributable,
      header_view:
        GGRC.mustache_path +
        '/custom_attribute_definitions/tree_header.mustache',
      show_view:
        GGRC.mustache_path + '/custom_attribute_definitions/tree.mustache',
      sortable: false,
      list_loader: function () {
        return CMS.Models.CustomAttributable.findAll();
      },
      draw_children: true,
      child_options: [{
        model: CMS.Models.CustomAttributeDefinition,
        mapping: 'custom_attribute_definitions',
        show_view:
          GGRC.mustache_path +
          '/custom_attribute_definitions/subtree.mustache',
        footer_view: null,
        add_item_view: null
      }]
    }
  };

  new GGRC.WidgetList('ggrc_admin', {
    admin: {
      people: {
        model: CMS.Models.Person,
        content_controller: GGRC.Controllers.ListView,
        content_controller_options: adminListDescriptors.people,
        widget_id: 'people_list',
        widget_icon: 'person',
        show_filter: false,
        widget_name: function () {
          return 'People';
        },
        widget_info: function () {
          return '';
        }
      },
      roles: {
        model: CMS.Models.Role,
        content_controller: GGRC.Controllers.ListView,
        content_controller_options: adminListDescriptors.roles,
        widget_id: 'roles_list',
        widget_icon: 'role',
        show_filter: false,
        widget_name: function () {
          return 'Roles';
        },
        widget_info: function () {
          return '';
        }
      },
      events: {
        model: CMS.Models.Event,
        content_controller: GGRC.Controllers.ListView,
        content_controller_options: adminListDescriptors.events,
        widget_id: 'events_list',
        widget_icon: 'event',
        widget_name: function () {
          return 'Events';
        },
        widget_info: function () {
          return '';
        }
      },
      custom_attributes: {
        widget_id: 'custom_attribute',
        widget_name: 'Custom Attributes',
        widget_icon: 'workflow',
        content_controller: CMS.Controllers.TreeView,
        content_controller_selector: 'ul',
        model: CMS.Models.CustomAttributable,
        widget_initial_content:
          '<ul' +
          '  class="tree-structure new-tree colored-list"' +
          '  data-no-pin="true"' +
          '></ul>',
        content_controller_options: adminListDescriptors.custom_attributes
      }
    }
  });

  extraPageOptions = {
    Program: {
      header_view: GGRC.mustache_path + '/base_objects/page_header.mustache',
      page_title: function (controller) {
        return 'GRC Program: ' + controller.options.instance.title;
      }
    },
    Person: {
      header_view: GGRC.mustache_path + '/base_objects/page_header.mustache',
      page_title: function (controller) {
        var instance = controller.options.instance;
        return /dashboard/.test(window.location) ?
          'GRC: My Work' :
          'GRC Profile: ' +
              (instance.name && instance.name.trim()) ||
              (instance.email && instance.email.trim());
      }
    }
  };

  isAssessmentsView = /^\/assessments_view/.test(location);
  isObjectBrowser = /^\/objectBrowser\/?$/.test(location);

  if (/^\/\w+\/\d+($|\?|\#)/.test(location) || /^\/dashboard/.test(location) ||
      isAssessmentsView || isObjectBrowser) {
    instance = GGRC.page_instance();
    modelName = instance.constructor.shortName;

    if (GGRC.tree_view.base_widgets_by_type[modelName]) {
      GGRC.Utils.CurrentPage
        .initCounts(GGRC.tree_view.base_widgets_by_type[modelName], {
          type: instance.type,
          id: instance.id
        });
    }

    initWidgets();

    widgetList = GGRC.WidgetList.get_widget_list_for(modelName);

    // the assessments_view only needs the Assessments widget
    if (isAssessmentsView) {
      widgetList = {assessment: widgetList.assessment};
    }

    defaults = Object.keys(widgetList);

    // Remove info and task tabs from object-browser list of tabs
    if (isObjectBrowser) {
      defaults.splice(defaults.indexOf('info'), 1);
      defaults.splice(defaults.indexOf('task'), 1);
    }

    $area.cms_controllers_page_object(can.extend({
      widget_descriptors: widgetList,
      default_widgets: defaults || GGRC.default_widgets || [],
      instance: GGRC.page_instance(),
      header_view: GGRC.mustache_path + '/base_objects/page_header.mustache',
      GGRC: GGRC,  // make the global object available in Mustache templates
      page_title: function (controller) {
        return controller.options.instance.title;
      },
      page_help: function (controller) {
        return controller.options.instance.constructor.table_singular;
      },
      current_user: GGRC.current_user
    }, extraPageOptions[modelName]));
  } else if (/^\/admin\/?$/.test(location)) {
    $area.cms_controllers_dashboard({
      widget_descriptors: GGRC.WidgetList.get_widget_list_for('admin'),
      menu_tree_spec: GGRC.admin_menu_spec,
      default_widgets: ['people', 'roles', 'events', 'custom_attributes']
    });
    initWidgets();
  } else if (/^\/import|export/i.test(location)) {
    initWidgets();
  } else {
    $area.cms_controllers_dashboard({
      widget_descriptors: GGRC.widget_descriptors,
      default_widgets: GGRC.default_widgets
    });
  }

  $('body').on('click', '.note-trigger, .edit-notes', function (ev) {
    var $object = $(ev.target).closest('[data-object-id]');
    var type = $object.data('object-type');
    var notesModel = GGRC.widget_descriptors[type].model;

    ev.stopPropagation();

    $(ev.target).closest('.note').cms_controllers_section_notes({
      section_id: $object.data('object-id') ||
                  (/\d+$/.exec(window.location.pathname) || [null])[0],
      model_class: notesModel
    });
  });

  // We remove loading class
  $(window).on('load', function () {
    $('html').removeClass('no-js');
  });
})(window.can.$, window.can, window.CMS, window.GGRC);
