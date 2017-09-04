/*!
    Copyright (C) 2017 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

(function (can, $) {
  var CoreExtension = {};

  CoreExtension.name = 'core"';
  GGRC.extensions.push(CoreExtension);
  _.extend(CoreExtension, {
    object_type_decision_tree: function () {
      return {
        program: CMS.Models.Program,
        audit: CMS.Models.Audit,
        contract: CMS.Models.Contract,
        policy: CMS.Models.Policy,
        standard: CMS.Models.Standard,
        regulation: CMS.Models.Regulation,
        org_group: CMS.Models.OrgGroup,
        vendor: CMS.Models.Vendor,
        project: CMS.Models.Project,
        facility: CMS.Models.Facility,
        product: CMS.Models.Product,
        data_asset: CMS.Models.DataAsset,
        access_group: CMS.Models.AccessGroup,
        market: CMS.Models.Market,
        system_or_process: {
          _discriminator: function (data) {
            if (data.is_biz_process) {
              return CMS.Models.Process;
            }
            return CMS.Models.System;
          }
        },
        system: CMS.Models.System,
        process: CMS.Models.Process,
        control: CMS.Models.Control,
        assessment: CMS.Models.Assessment,
        assessment_template: CMS.Models.AssessmentTemplate,
        issue: CMS.Models.Issue,
        objective: CMS.Models.Objective,
        section: CMS.Models.Section,
        clause: CMS.Models.Clause,
        person: CMS.Models.Person,
        role: CMS.Models.Role,
        threat: CMS.Models.Threat,
        risk: CMS.Models.Risk,
        vulnerability: CMS.Models.Vulnerability,
        template: CMS.Models.Template
      };
    },
    init_widgets: function () {
      var baseWidgetsByType = GGRC.tree_view.base_widgets_by_type;
      var widgetList = new GGRC.WidgetList('ggrc_core');
      var objectClass = GGRC.infer_object_type(GGRC.page_object);
      var objectTable = objectClass && objectClass.table_plural;
      var object = GGRC.page_instance();
      var path = GGRC.mustache_path;
      var infoWidgetViews;
      var summaryWidgetViews;
      var modelNames;
      var possibleModelType;
      var farModels;
      var extraDescriptorOptions;
      var overriddenModels;
      var extraContentControllerOptions;

      // TODO: Really ugly way to avoid executing IIFE - needs cleanup
      if (!GGRC.page_object) {
        return;
      }
      // Info and summary widgets display the object information instead of listing
      // connected objects.
      summaryWidgetViews = {
        audits: path + '/audits/summary.mustache'
      };
      if (summaryWidgetViews[objectTable]) {
        widgetList.add_widget(object.constructor.shortName, 'summary', {
          widget_id: 'summary',
          content_controller: GGRC.Controllers.SummaryWidget,
          instance: object,
          widget_view: summaryWidgetViews[objectTable],
          order: 3
        });
      }
      if (GGRC.Utils.Dashboards.isDashboardEnabled(object)) {
        widgetList.add_widget(object.constructor.shortName, 'dashboard', {
          widget_id: 'dashboard',
          content_controller: GGRC.Controllers.DashboardWidget,
          instance: object,
          widget_view: path + '/base_objects/dashboard_widget.mustache',
          order: 6
        });
      }
      infoWidgetViews = {
        programs: path + '/programs/info.mustache',
        audits: path + '/audits/info.mustache',
        people: path + '/people/info.mustache',
        policies: path + '/policies/info.mustache',
        objectives: path + '/objectives/info.mustache',
        controls: path + '/controls/info.mustache',
        systems: path + '/systems/info.mustache',
        processes: path + '/processes/info.mustache',
        products: path + '/products/info.mustache',
        assessments: path + '/assessments/info.mustache',
        assessment_templates:
          path + '/assessment_templates/info.mustache',
        issues: path + '/issues/info.mustache'
      };
      widgetList.add_widget(object.constructor.shortName, 'info', {
        widget_id: 'info',
        content_controller: GGRC.Controllers.InfoWidget,
        instance: object,
        widget_view: infoWidgetViews[objectTable],
        order: 5
      });
      modelNames = can.Map.keys(baseWidgetsByType);
      modelNames.sort();
      possibleModelType = modelNames.slice();
      can.each(modelNames, function (name) {
        var w_list;
        var child_model_list = [];
        var objectVersionUtils = GGRC.Utils.ObjectVersions;
        var widgetConfig = objectVersionUtils.getWidgetConfig(name);
        name = widgetConfig.name;
        GGRC.tree_view.basic_model_list.push({
          model_name: name,
          display_name: widgetConfig.widgetName
        });

        // Initialize child_model_list, and child_display_list each model_type
        w_list = baseWidgetsByType[name];

        can.each(w_list, function (item) {
          var childConfig;
          if (possibleModelType.indexOf(item) !== -1) {
            childConfig = objectVersionUtils.getWidgetConfig(name);
            child_model_list.push({
              model_name: childConfig.name,
              display_name: childConfig.widgetName
            });
          }
        });
        GGRC.tree_view.sub_tree_for.attr(name, {
          model_list: child_model_list,
          display_list: CMS.Models[name].tree_view_options.child_tree_display_list || w_list
        });
      });

      function sort_sections(sections) {
        return can.makeArray(sections).sort(window.natural_comparator);
      }

      function apply_mixins(definitions) {
        var mappings = {};

        // Recursively handle mixins
        function reify_mixins(definition) {
          var final_definition = {};
          if (definition._mixins) {
            can.each(definition._mixins, function (mixin) {
              if (typeof (mixin) === 'string') {
                // If string, recursive lookup
                if (!definitions[mixin]) {
                  console.debug('Undefined mixin: ' + mixin, definitions);
                } else {
                  can.extend(
                    final_definition,
                    reify_mixins(definitions[mixin])
                  );
                }
              } else if (can.isFunction(mixin)) {
                // If function, call with current definition state
                mixin(final_definition);
              } else {
                // Otherwise, assume object and extend
                can.extend(final_definition, mixin);
              }
            });
          }
          can.extend(final_definition, definition);
          delete final_definition._mixins;
          return final_definition;
        }

        can.each(definitions, function (definition, name) {
          // Only output the mappings if it's a model, e.g., uppercase first letter
          if (name[0] === name[0].toUpperCase())
            mappings[name] = reify_mixins(definition);
        });

        return mappings;
      }

      // the assessments_view only needs the Assessments widget
      if (/^\/assessments_view/.test(window.location.pathname)) {
        farModels = ['Assessment'];
      } else {
        farModels = baseWidgetsByType[object.constructor.shortName];
      }

        // here we are going to define extra descriptor options, meaning that
        //  these will be used as extra options to create widgets on top of

      extraDescriptorOptions = {
        all: (function () {
          var defOrder = GGRC.tree_view.attr('defaultOrderTypes');
          var all = {};
          Object.keys(defOrder).forEach(function (type) {
            all[type] = {
              order: defOrder[type]
            };
          });

          all.Document = {
            widget_icon: 'fa fa-link!',
            order: 150
          };
          all.Person.widget_icon = 'person';
          return all;
        })(),
        Contract: {
          Clause: {
            widget_name: function () {
              var $objectArea = $('.object-area');
              return $objectArea.hasClass('dashboard-area') ?
                'Clauses' : 'Mapped Clauses';
            }
          }
        },
        Program: {
          Person: {
            widget_id: 'person',
            widget_name: 'People',
            widget_icon: 'person'
          }
        },

        // An Audit has a different set of object that are more relevant to it,
        // thus these objects have a customized priority. On the other hand,
        // the object otherwise prioritized by default (e.g. Regulation) have
        // their priority lowered so that they fit nicely into the alphabetical
        // order among the non-prioritized object types.
        Audit: {
          Assessment: {
            order: 7
          },
          Issue: {
            order: 8
          },
          Program: {
            order: 9
          },
          program: {
            widget_id: 'program',
            widget_name: 'Program',
            widget_icon: 'program'
          },
          Person: {
            widget_id: 'person',
            widget_name: 'People',
            widget_icon: 'person',
            // NOTE: "order" not overridden
            content_controller_options: {
              mapping: 'authorized_people',
              allow_mapping: false,
              allow_creating: false
            }
          }
        }
      };
      // Prevent widget creation with <model_name>: false
      // e.g. to prevent ever creating People widget:
      //     { all : { Person: false }}
      // or to prevent creating People widget on Objective page:
      //     { Objective: { Person: false } }
      overriddenModels = {
        Program: {
        },
        all: {
          Document: false
        }
      };

      extraContentControllerOptions = apply_mixins({
        objectives: {
          Objective: {
            draw_children: true,
            add_item_view: path + '/snapshots/tree_add_item.mustache'
          }
        },
        controls: {
          Control: {
            draw_children: true,
            add_item_view: path + '/snapshots/tree_add_item.mustache'
          }
        },
        business_objects: {
          Audit: {
            mapping: 'related_audits',
            draw_children: true,
            allow_mapping: true,
            add_item_view: path + '/audits/tree_add_item.mustache'
          },
          AccessGroup: {
            mapping: 'related_access_groups',
            draw_children: true
          },
          DataAsset: {
            mapping: 'related_data_assets',
            draw_children: true
          },
          Facility: {
            mapping: 'related_facilities',
            draw_children: true
          },
          Market: {
            mapping: 'related_markets',
            draw_children: true
          },
          OrgGroup: {
            mapping: 'related_org_groups',
            draw_children: true
          },
          Vendor: {
            mapping: 'related_vendors',
            draw_children: true
          },
          Process: {
            mapping: 'related_processes',
            draw_children: true
          },
          Product: {
            mapping: 'related_products',
            draw_children: true
          },
          Project: {
            mapping: 'related_projects',
            draw_children: true
          },
          System: {
            mapping: 'related_systems',
            draw_children: true
          },
          Assessment: {
            mapping: 'related_assessments',
            draw_children: true
          },
          Document: {
            mapping: 'documents',
            draw_children: true
          },
          Person: {
            mapping: 'people',
            draw_children: true
          },
          Program: {
            mapping: 'programs',
            draw_children: true
          },
          Risk: {
            mapping: 'risks',
            draw_children: true
          },
          Threat: {
            mapping: 'threats',
            draw_children: true
          }
        },
        issues: {
          Issue: {
            mapping: 'related_issues',
            add_item_view: GGRC.mustache_path +
              '/issues/tree_add_item.mustache',
            draw_children: true
          }
        },
        governance_objects: {
          Regulation: {
            draw_children: true,
            fetch_post_process: sort_sections,
            add_item_view: path + '/snapshots/tree_add_item.mustache'
          },
          Contract: {
            draw_children: true,
            fetch_post_process: sort_sections,
          },
          Policy: {
            draw_children: true,
            fetch_post_process: sort_sections,
            add_item_view: path + '/snapshots/tree_add_item.mustache'
          },
          Standard: {
            draw_children: true,
            fetch_post_process: sort_sections,
            add_item_view: path + '/snapshots/tree_add_item.mustache'
          },
          Control: {
            mapping: 'controls',
            draw_children: true
          },
          Objective: {
            mapping: 'objectives',
            draw_children: true
          },
          Section: {
            mapping: 'sections',
            draw_children: true
          },
          Clause: {
            mapping: 'clauses',
            draw_children: true
          }
        },
        Program: {
          _mixins: [
            'governance_objects', 'objectives', 'controls',
            'business_objects', 'issues'
          ],
          Audit: {
            allow_mapping: true,
            draw_children: true,
            add_item_view: path + '/audits/tree_add_item.mustache'
          },
          Person: {
            parent_instance: GGRC.page_instance(),
            allow_reading: true,
            allow_mapping: true,
            allow_creating: true,
            model: CMS.Models.Person,
            mapping: 'mapped_and_or_authorized_people',
            draw_children: true
          }
        },
        Audit: {
          _mixins: ['issues', 'governance_objects', 'business_objects'],
          Program: {
            parent_instance: GGRC.page_instance(),
            draw_children: true,
            model: CMS.Models.Program,
            allow_mapping: false,
            allow_creating: false
          },
          Section: {
            mapping: 'sections',
            draw_children: true
          },
          Clause: {
            mapping: 'clauses',
            draw_children: true
          },
          Threat: {
            mapping: 'threats',
            draw_children: true
          },
          Risk: {
            mapping: 'risks',
            draw_children: true
          },
          Assessment: {
            mapping: 'related_assessments',
            parent_instance: GGRC.page_instance(),
            allow_mapping: true,
            draw_children: true,
            model: CMS.Models.Assessment,
            add_item_view: path + '/assessments/tree_add_item.mustache'
          },
          AssessmentTemplate: {
            mapping: 'related_assessment_templates',
            draw_children: false,
            allow_mapping: false,
            add_item_view: GGRC.mustache_path +
              '/assessment_templates/tree_add_item.mustache'
          },
          Person: {
            widget_id: 'person',
            widget_name: 'People',
            widget_icon: 'person',
            draw_children: true,
            content_controller_options: {
              mapping: 'authorized_people',
              allow_mapping: false,
              allow_creating: false
            }
          }
        },
        directive: {
          _mixins: [
            'objectives', 'controls', 'business_objects'
          ],
          Section: {
            mapping: 'sections',
            draw_children: true
          },
          Clause: {
            mapping: 'clauses',
            draw_children: true
          },
          Audit: {
            mapping: 'related_audits',
            draw_children: true
          }
        },
        Regulation: {
          _mixins: ['directive', 'issues']
        },
        Standard: {
          _mixins: ['directive', 'issues']
        },
        Policy: {
          _mixins: ['directive', 'issues']
        },
        Contract: {
          _mixins: ['directive', 'issues']
        },
        Clause: {
          _mixins: ['governance_objects', 'business_objects', 'issues'],
          Audit: {
            mapping: 'related_audits',
            draw_children: true
          }
        },
        Section: {
          _mixins: ['governance_objects', 'business_objects', 'issues'],
          Audit: {
            mapping: 'related_audits',
            draw_children: true
          }
        },
        Objective: {
          _mixins: ['governance_objects', 'business_objects', 'issues'],
          Audit: {
            mapping: 'related_audits',
            draw_children: true
          }
        },
        Control: {
          _mixins: ['governance_objects', 'business_objects', 'issues'],
          Audit: {
            mapping: 'related_audits',
            draw_children: true
          }
        },
        Assessment: {
          _mixins: ['governance_objects', 'business_objects', 'issues'],
          Audit: {
            draw_children: true,
            allow_creating: false,
            allow_mapping: true,
            add_item_view: path + '/audits/tree_add_item.mustache'
          },
          Section: {
            mapping: 'sections',
            draw_children: true
          },
          Clause: {
            mapping: 'clauses',
            draw_children: true
          }
        },
        AssessmentTemplate: {
          Audit: {
            mapping: 'related_audits',
            draw_children: true,
            allow_creating: false,
            allow_mapping: true
          }
        },
        Risk: {
          _mixins: ['governance_objects', 'business_objects', 'issues'],
          Threat: {
            mapping: 'threats',
            draw_children: true
          }
        },
        Threat: {
          _mixins: ['governance_objects', 'business_objects', 'issues'],
          Risk: {
            mapping: 'risks',
            draw_children: true
          }
        },
        Issue: {
          _mixins: ['governance_objects', 'business_objects'],
          Control: {
            draw_children: true,
            add_item_view: path + '/base_objects/tree_add_item.mustache'
          },
          Issue: {
            mapping: 'related_issues',
            add_item_view: path + '/issues/tree_add_item.mustache'
          },
          Audit: {
            draw_children: true,
            add_item_view:
              GGRC.mustache_path + '/base_objects/tree_add_item.mustache'
          }
        },
        AccessGroup: {
          _mixins: ['governance_objects', 'business_objects', 'issues']
        },
        DataAsset: {
          _mixins: ['governance_objects', 'business_objects', 'issues']
        },
        Facility: {
          _mixins: ['governance_objects', 'business_objects', 'issues']
        },
        Market: {
          _mixins: ['governance_objects', 'business_objects', 'issues']
        },
        OrgGroup: {
          _mixins: ['governance_objects', 'business_objects', 'issues']
        },
        Vendor: {
          _mixins: ['governance_objects', 'business_objects', 'issues']
        },
        Process: {
          _mixins: ['governance_objects', 'business_objects', 'issues']
        },
        Product: {
          _mixins: ['governance_objects', 'business_objects', 'issues']
        },
        Project: {
          _mixins: ['governance_objects', 'business_objects', 'issues']
        },
        System: {
          _mixins: ['governance_objects', 'business_objects', 'issues']
        },
        Document: {
          _mixins: ['governance_objects', 'business_objects', 'issues']
        },
        Person: {
          _mixins: ['issues'],
          Program: {
            mapping: 'extended_related_programs_via_search',
            draw_children: true,
            fetch_post_process: sort_sections
          },
          Regulation: {
            draw_children: true,
            fetch_post_process: sort_sections
          },
          Contract: {
            draw_children: true,
            fetch_post_process: sort_sections
          },
          Standard: {
            draw_children: true,
            fetch_post_process: sort_sections
          },
          Policy: {
            draw_children: true,
            fetch_post_process: sort_sections
          },
          Audit: {
            draw_children: true
          },
          Section: {
            add_item_view:
              GGRC.mustache_path + '/base_objects/tree_add_item.mustache',
            draw_children: true
          },
          Clause: {
            add_item_view:
              GGRC.mustache_path + '/base_objects/tree_add_item.mustache',
            draw_children: true
          },
          Objective: {
            draw_children: true,
            add_item_view: path + '/base_objects/tree_add_item.mustache'
          },
          Control: {
            draw_children: true,
            add_item_view: path + '/base_objects/tree_add_item.mustache'
          },
          Issue: {
            mapping: 'extended_related_issues_via_search',
            draw_children: true
          },
          AccessGroup: {
            mapping: 'extended_related_access_groups_via_search',
            draw_children: true
          },
          DataAsset: {
            mapping: 'extended_related_data_assets_via_search',
            draw_children: true
          },
          Facility: {
            mapping: 'extended_related_facilities_via_search',
            draw_children: true
          },
          Market: {
            mapping: 'extended_related_markets_via_search',
            draw_children: true
          },
          OrgGroup: {
            mapping: 'extended_related_org_groups_via_search',
            draw_children: true
          },
          Vendor: {
            mapping: 'extended_related_vendors_via_search',
            draw_children: true
          },
          Process: {
            mapping: 'extended_related_processes_via_search',
            draw_children: true
          },
          Product: {
            mapping: 'extended_related_products_via_search',
            draw_children: true
          },
          Project: {
            mapping: 'extended_related_projects_via_search',
            draw_children: true
          },
          System: {
            mapping: 'extended_related_systems_via_search',
            draw_children: true
          },
          Document: {
            mapping: 'extended_related_documents_via_search'
          },
          Assessment: {
            mapping: 'extended_related_assessment_via_search',
            draw_children: true,
            add_item_view: null
          },
          Risk: {
            mapping: 'extended_related_risks_via_search',
            draw_children: true
          },
          Threat: {
            mapping: 'extended_related_threats_via_search',
            draw_children: true
          }
        }
      });

      // Disable editing on profile pages, as long as it isn't audits on the dashboard
      if (GGRC.page_instance() instanceof CMS.Models.Person) {
        var person_options = extraContentControllerOptions.Person;
        can.each(person_options, function (options, model_name) {
          if (model_name !== 'Audit' || !/dashboard/.test(window.location)) {
            can.extend(options, {
              allow_creating: false,
              allow_mapping: true
            });
          }
        });
      }

      can.each(farModels, function (model_name) {
        var widgetConfig =  GGRC.Utils.ObjectVersions
          .getWidgetConfig(model_name);
        model_name = widgetConfig.name;

        if ((overriddenModels.all && overriddenModels.all.hasOwnProperty(model_name) && !overriddenModels[model_name]) || (overriddenModels[object.constructor.shortName] && overriddenModels[object.constructor.shortName].hasOwnProperty(model_name) && !overriddenModels[object.constructor.shortName][model_name]))
          return;
        var sources = [],
          far_model, descriptor = {},
          widget_id;

        far_model = CMS.Models[model_name];
        if (far_model) {
          widget_id = widgetConfig.widgetId;
          descriptor = {
            instance: object,
            far_model: far_model,
            mapping: GGRC.Mappings.get_canonical_mapping(object.constructor.shortName, far_model.shortName)
          };
        } else {
          widget_id = model_name;
        }

        // Custom overrides
        if (extraDescriptorOptions.all && extraDescriptorOptions.all[model_name]) {
          $.extend(descriptor, extraDescriptorOptions.all[model_name]);
        }

        if (extraDescriptorOptions[object.constructor.shortName] && extraDescriptorOptions[object.constructor.shortName][model_name]) {
          $.extend(descriptor, extraDescriptorOptions[object.constructor.shortName][model_name]);
        }

        if (extraContentControllerOptions.all && extraContentControllerOptions.all[model_name]) {
          $.extend(true, descriptor, {
            content_controller_options: extraContentControllerOptions.all[model_name]
          });
        }

        if (extraContentControllerOptions[object.constructor.shortName] && extraContentControllerOptions[object.constructor.shortName][model_name]) {
          $.extend(true, descriptor, {
            content_controller_options: extraContentControllerOptions[object.constructor.shortName][model_name]
          });
        }
        descriptor.widgetType = 'treeview';
        widgetList.add_widget(object.constructor.shortName, widget_id, descriptor);
      });
    }
  });
})(window.can, window.can.$);
