/*
 * Copyright (C) 2017 Google Inc.
 * Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function ($, CMS, GGRC) {
  var RisksExtension = {};

  // Insert risk mappings to all gov/business object types
  var riskObjectTypes = [
    'AccessGroup',
    'Assessment',
    'Clause',
    'Contract',
    'Control',
    'DataAsset',
    'Facility',
    'Issue',
    'Market',
    'MultitypeSearch',
    'Objective',
    'OrgGroup',
    'Person',
    'Policy',
    'Process',
    'Product',
    'Program',
    'Project',
    'Regulation',
    'Section',
    'Standard',
    'System',
    'Vendor'
  ];
  var relatedObjectDescriptors = {};
  var threatDescriptor;
  var riskDescriptor;

  // Register `risks` extension with GGRC
  GGRC.extensions.push(RisksExtension);

  RisksExtension.name = 'risks';

  // Register Risk Assessment models for use with `infer_object_type`
  RisksExtension.object_type_decision_tree = function () {
    return {
      risk: CMS.Models.Risk,
      threat: CMS.Models.Threat
    };
  };

  // Configure mapping extensions for ggrc_risks
  RisksExtension.init_mappings = function () {
    var Proxy = GGRC.MapperHelpers.Proxy;
    var Search = GGRC.MapperHelpers.Search;
    var TypeFilter = GGRC.MapperHelpers.TypeFilter;
    var Multi = GGRC.MapperHelpers.Multi;

    // Add mappings for risk objects
    var mappings = {
      related: {
        related_objects_as_source: Proxy(null, 'destination', 'Relationship',
          'source', 'related_destinations'),
        related_objects_as_destination: Proxy(
          null, 'source', 'Relationship', 'destination', 'related_sources'),
        related_objects:
          Multi(['related_objects_as_source', 'related_objects_as_destination'])
      },
      related_objects: {
        _canonical: {
          related_objects_as_source: riskObjectTypes
        },
        related_programs: TypeFilter('related_objects', 'Program'),
        related_data_assets: TypeFilter('related_objects', 'DataAsset'),
        related_access_groups: TypeFilter('related_objects', 'AccessGroup'),
        related_facilities: TypeFilter('related_objects', 'Facility'),
        related_markets: TypeFilter('related_objects', 'Market'),
        related_processes: TypeFilter('related_objects', 'Process'),
        related_products: TypeFilter('related_objects', 'Product'),
        related_projects: TypeFilter('related_objects', 'Project'),
        related_systems: TypeFilter('related_objects', 'System'),
        related_controls: TypeFilter('related_objects', 'Control'),
        related_clauses: TypeFilter('related_objects', 'Clause'),
        related_sections: TypeFilter('related_objects', 'Section'),
        related_regulations: TypeFilter('related_objects', 'Regulation'),
        related_contracts: TypeFilter('related_objects', 'Contract'),
        related_policies: TypeFilter('related_objects', 'Policy'),
        related_standards: TypeFilter('related_objects', 'Standard'),
        related_objectives: TypeFilter('related_objects', 'Objective'),
        related_issues: TypeFilter('related_objects', 'Issue'),
        related_assessments: TypeFilter('related_objects', 'Assessment'),
        related_people: TypeFilter('related_objects', 'Person'),
        related_org_groups: TypeFilter('related_objects', 'OrgGroup'),
        related_vendors: TypeFilter('related_objects', 'Vendor')

      },
      related_risk: {
        _canonical: {
          related_objects_as_source: ['Risk'].concat(riskObjectTypes)
        },
        related_risks: TypeFilter('related_objects', 'Risk')
      },
      related_threat: {
        _canonical: {
          related_objects_as_source: ['Threat'].concat(riskObjectTypes)
        },
        related_threats: TypeFilter('related_objects', 'Threat')
      },
      Risk: {
        _mixins: ['related', 'related_objects', 'related_threat'],
        orphaned_objects: Multi([])
      },
      Threat: {
        _mixins: ['related', 'related_objects', 'related_risk'],
        orphaned_objects: Multi([])
      },
      Person: {
        owned_risks: TypeFilter('related_objects_via_search', 'Risk'),
        owned_threats: TypeFilter('related_objects_via_search', 'Threat'),
        all_risks: Search(function (binding) {
          return CMS.Models.Risk.findAll({});
        }),
        all_threats: Search(function (binding) {
          return CMS.Models.Threat.findAll({});
        })
      }
    };

    // patch Person to extend query for dashboard
    GGRC.Mappings.modules.ggrc_core
      .Person.related_objects_via_search
      .observe_types.push('Risk', 'Threat');

    can.each(riskObjectTypes, function (type) {
      mappings[type] = _.extend(mappings[type] || {}, {
        _canonical: {
          related_objects_as_source: ['Risk', 'Threat']
        },
        _mixins: ['related', 'related_risk', 'related_threat']
      });
    });
    new GGRC.Mappings('ggrc_risks', mappings);
  };

  // Override GGRC.extra_widget_descriptors and GGRC.extra_default_widgets
  // Initialize widgets for risk page
  RisksExtension.init_widgets = function () {
    var pageInstance = GGRC.page_instance();
    var isMyWork = function () {
      return pageInstance && pageInstance.type === 'Person';
    };

    var relatedOrOwned = isMyWork() ? 'owned_' : 'related_';
    var sortedWidgetTypes = _.sortBy(riskObjectTypes, function (type) {
      var model = CMS.Models[type] || {};
      return model.title_plural || type;
    });
    var baseWidgetsByType = GGRC.tree_view.base_widgets_by_type;
    var moduleObjectNames = ['Risk', 'Threat'];
    var extendedModuleTypes = riskObjectTypes.concat(moduleObjectNames);
    var subTrees = GGRC.tree_view.sub_tree_for;

    if (/^\/objectBrowser\/?$/.test(window.location.pathname)) {
      relatedOrOwned = 'all_';
    }
    // Init widget descriptors:
    can.each(sortedWidgetTypes, function (modelName) {
      var model;

      if (modelName === 'MultitypeSearch' || !baseWidgetsByType[modelName]) {
        return;
      }
      model = CMS.Models[modelName];

      // First we add Risk and Threat to other object's maps
      baseWidgetsByType[modelName] = baseWidgetsByType[modelName].concat(
        moduleObjectNames);

      relatedObjectDescriptors[modelName] = {
        widgetType: 'treeview',
        treeViewDepth: 2,
        widget_id: model.table_singular,
        widget_name: model.model_plural,
        widget_icon: model.table_singular,
        content_controller_options: {
          add_item_view: GGRC.mustache_path +
          '/base_objects/tree_add_item.mustache',
          draw_children: true,
          parent_instance: pageInstance,
          model: model,
          mapping: 'related_' + model.table_plural
        }
      };
    });

    // Add risk and Threat to base widget types and set up
    // tree_view.basic_model_list and tree_view.sub_tree_for for risk module
    // objects
    can.each(moduleObjectNames, function (name) {
      var widgetList = baseWidgetsByType[name];
      var childModelList = [];

      baseWidgetsByType[name] = extendedModuleTypes;

      GGRC.tree_view.basic_model_list.push({
        model_name: name,
        display_name: CMS.Models[name].title_singular
      });

      can.each(widgetList, function (item) {
        if (extendedModuleTypes.indexOf(item) !== -1) {
          childModelList.push({
            model_name: item,
            display_name: CMS.Models[item].title_singular
          });
        }
      });

      if (!_.isEmpty(subTrees.serialize())) {
        subTrees.attr(name, {
          model_list: childModelList,
          display_list:
          CMS.Models[name].tree_view_options.child_tree_display_list ||
          widgetList
        });
      }
    });

    threatDescriptor = {
      widgetType: 'treeview',
      treeViewDepth: 2,
      widget_id: CMS.Models.Threat.table_singular,
      widget_name: CMS.Models.Threat.title_plural,
      widget_icon: CMS.Models.Threat.table_singular,
      content_controller_options: {
        draw_children: true,
        parent_instance: pageInstance,
        model: CMS.Models.Threat,
        mapping: relatedOrOwned + CMS.Models.Threat.table_plural
      }
    };
    riskDescriptor = {
      widgetType: 'treeview',
      treeViewDepth: 2,
      widget_id: CMS.Models.Risk.table_singular,
      widget_name: CMS.Models.Risk.title_plural,
      widget_icon: CMS.Models.Risk.table_singular,
      order: 45, // between default Objective (40) and Control (50)
      content_controller_options: {
        draw_children: true,
        parent_instance: pageInstance,
        model: CMS.Models.Risk,
        mapping: relatedOrOwned + CMS.Models.Risk.table_plural
      }
    };

    if (pageInstance instanceof CMS.Models.Risk) {
      RisksExtension.init_widgets_for_risk_page();
    } else if (pageInstance instanceof CMS.Models.Threat) {
      RisksExtension.init_widgets_for_threat_page();
    } else if (pageInstance instanceof CMS.Models.Person) {
      RisksExtension.init_widgets_for_person_page();
    } else {
      RisksExtension.init_widgets_for_other_pages();
    }
  };

  RisksExtension.init_widgets_for_risk_page = function () {
    var riskDescriptors = $.extend({},
      relatedObjectDescriptors, {
        Threat: threatDescriptor
      }
    );
    new GGRC.WidgetList('ggrc_risks', {
      Risk: riskDescriptors
    });
  };

  RisksExtension.init_widgets_for_threat_page = function () {
    var threatDescriptors = $.extend({},
      relatedObjectDescriptors, {
        Risk: riskDescriptor
      }
    );
    new GGRC.WidgetList('ggrc_risks', {
      Threat: threatDescriptors
    });
  };

  RisksExtension.init_widgets_for_person_page = function () {
    var peopleWidgets = $.extend({}, {
      Threat: threatDescriptor
    }, {
      Risk: riskDescriptor
    });

    new GGRC.WidgetList('ggrc_risks', {
      Person: peopleWidgets
    });
  };

  RisksExtension.init_widgets_for_other_pages = function () {
    var descriptor = {};
    var pageInstance = GGRC.page_instance();
    if (pageInstance &&
      ~can.inArray(pageInstance.constructor.shortName, riskObjectTypes)) {
      descriptor[pageInstance.constructor.shortName] = {
        risk: riskDescriptor,
        threat: threatDescriptor
      };
    }
    new GGRC.WidgetList('ggrc_risks', descriptor);
  };

  GGRC.register_hook('LHN.Sections_risk',
    GGRC.mustache_path + '/dashboard/lhn_risks');

  RisksExtension.init_mappings();
})(window.can.$, window.CMS, window.GGRC);
