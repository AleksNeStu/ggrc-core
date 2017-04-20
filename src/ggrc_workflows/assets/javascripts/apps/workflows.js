/*
 * Copyright (C) 2017 Google Inc.
 * Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function ($, CMS, GGRC) {
  var WorkflowExtension = {};
  var _workflowObjectTypes = Array.prototype.concat.call(
    [],
    'Program Regulation Policy Standard Contract Clause Section'.split(' '),
    'Request Control Objective OrgGroup Vendor AccessGroup'.split(' '),
    'System Process DataAsset Product Project Facility Market'.split(' '),
    'Issue Assessment Risk Threat'.split(' ')
  );
  var _taskSortFunction = function (a, b) {
    var dateA = Number(new Date(a.end_date));
    var dateB = Number(new Date(b.end_date));

    if (dateA === dateB) {
      if (a.id < b.id) {
        return -1;
      } else if (a.id > b.id) {
        return 1;
      }
      return 0;
    }
    if (dateA < dateB) {
      return -1;
    }
    return 1;
  };

  var draftOnUpdateMixin;

  var historyWidgetCountsName = 'cycles:history';
  var currentWidgetCountsName = 'cycles:active';

  var historyWidgetFilter = 'is_current = 0';
  var currentWidgetFilter = 'is_current = 1';

  // Register `workflows` extension with GGRC
  GGRC.extensions.push(WorkflowExtension);

  WorkflowExtension.name = 'workflows';

  WorkflowExtension.countsMap = {
    history: {
      name: 'Cycle',
      countsName: historyWidgetCountsName,
      additionalFilter: historyWidgetFilter
    },
    activeCycles: {
      name: 'Cycle',
      countsName: currentWidgetCountsName,
      additionalFilter: currentWidgetFilter
    },
    person: 'Person',
    taskGroup: 'TaskGroup'
  };

  // Register Workflow models for use with `infer_object_type`
  WorkflowExtension.object_type_decision_tree = function () {
    return {
      cycle: CMS.Models.Cycle,
      cycle_task_entry: CMS.Models.CycleTaskEntry,
      cycle_task_group: CMS.Models.CycleTaskGroup,
      cycle_task_group_object_task: CMS.Models.CycleTaskGroupObjectTask,
      task_group: CMS.Models.TaskGroup,
      workflow: CMS.Models.Workflow
    };
  };

  // Configure mapping extensions for ggrc_workflows
  WorkflowExtension.init_mappings = function () {
    var Proxy = GGRC.MapperHelpers.Proxy;
    var Direct = GGRC.MapperHelpers.Direct;
    var Cross = GGRC.MapperHelpers.Cross;
    var Multi = GGRC.MapperHelpers.Multi;
    var CustomFilter = GGRC.MapperHelpers.CustomFilter;
    var Reify = GGRC.MapperHelpers.Reify;
    var Search = GGRC.MapperHelpers.Search;
    var TypeFilter = GGRC.MapperHelpers.TypeFilter;

    // Add mappings for basic workflow objects
    var mappings = {
      TaskGroup: {
        _canonical: {
          objects: _workflowObjectTypes.concat(['Cacheable'])
        },
        task_group_tasks: Direct(
          'TaskGroupTask', 'task_group', 'task_group_tasks'),
        objects: Proxy(
          null, 'object', 'TaskGroupObject', 'task_group',
          'task_group_objects'),
        workflow: Direct(
          'Workflow', 'task_groups', 'workflow')
      },

      Workflow: {
        _canonical: {
          task_groups: 'TaskGroup',
          people: 'Person',
          context: 'Context'
        },
        task_groups: Direct(
          'TaskGroup', 'workflow', 'task_groups'),
        tasks: Cross(
          'task_groups', 'task_group_tasks'),
        cycles: Direct(
          'Cycle', 'workflow', 'cycles'),
        previous_cycles: CustomFilter('cycles', function (result) {
          return !result.instance.attr('is_current');
        }),
        current_cycle: CustomFilter('cycles', function (result) {
          return result.instance.attr('is_current');
        }),
        current_task_groups: Cross('current_cycle', 'cycle_task_groups'),
        current_tasks: Cross(
          'current_task_groups', 'cycle_task_group_object_tasks'
        ),
        current_all_tasks: Cross(
          'current_task_groups', 'cycle_task_group_tasks'
        ),

        people: Proxy(
          'Person',
          'person', 'WorkflowPerson',
          'workflow', 'workflow_people'
        ),
        context: Direct(
          'Context', 'related_object', 'context'),
        authorization_contexts: Multi(['context']),
        authorizations: Cross(
          'authorization_contexts', 'user_roles'),
        authorized_people: Cross(
          'authorization_contexts', 'authorized_people'),
        mapped_and_or_authorized_people: Multi([
          'people', 'authorized_people']),
        roles: Cross('authorizations', 'role'),

        // This is a dummy mapping that ensures the WorkflowOwner role is loaded
        //  before we do the custom filter for owner_authorizations.
        authorizations_and_roles: Multi(['authorizations', 'roles']),
        owner_authorizations: CustomFilter(
          'authorizations_and_roles',
          function (binding) {
            return binding.instance instanceof CMS.Models.UserRole &&
                binding.instance.attr('role') &&
                binding.instance.role.reify().attr('name') === 'WorkflowOwner';
          }
        ),
        owners: Cross('owner_authorizations', 'person'),
        orphaned_objects: Multi([
          'cycles',
          'task_groups',
          'tasks',
          'current_task_groups',
          'current_tasks'
        ])
      },

      Cycle: {
        cycle_task_groups: Direct(
          'CycleTaskGroup', 'cycle', 'cycle_task_groups'),
        reify_cycle_task_groups: Reify('cycle_task_groups'),
        workflow: Direct('Workflow', 'cycles', 'workflow')
      },

      CycleTaskGroup: {
        cycle: Direct(
          'Cycle', 'cycle_task_groups', 'cycle'),
        cycle_task_group_tasks: Direct(
          'CycleTaskGroupObjectTask',
          'cycle_task_group',
          'cycle_task_group_tasks'),

        // effectively an alias for 'cycle_task_group_tasks', specifying just
        // the latter's name as a string does not work for some reason
        cycle_task_group_object_tasks: Direct(
          'CycleTaskGroupObjectTask',
          'cycle_task_group',
          'cycle_task_group_tasks')
      },

      CycleTaskGroupObjectTask: {
        _canonical: {
          related_objects_as_source: [
            'DataAsset', 'Facility', 'Market', 'OrgGroup', 'Vendor', 'Process',
            'Product', 'Project', 'System', 'Regulation', 'Policy', 'Contract',
            'Standard', 'Program', 'Issue', 'Control', 'Section', 'Clause',
            'Objective', 'Audit', 'Assessment', 'AccessGroup',
            'Document', 'Risk', 'Threat'
          ]
        },
        related_objects_as_source: Proxy(
          null,
          'destination', 'Relationship',
          'source', 'related_destinations'
        ),
        related_objects_as_destination: Proxy(
          null,
          'source', 'Relationship',
          'destination', 'related_sources'
        ),
        related_objects: Multi(
          ['related_objects_as_source', 'related_objects_as_destination']
        ),
        destinations: Direct('Relationship', 'source', 'related_destinations'),
        sources: Direct('Relationship', 'destination', 'related_sources'),
        relationships: Multi(['sources', 'destinations']),
        related_access_groups: TypeFilter('related_objects', 'AccessGroup'),
        related_data_assets: TypeFilter('related_objects', 'DataAsset'),
        related_facilities: TypeFilter('related_objects', 'Facility'),
        related_markets: TypeFilter('related_objects', 'Market'),
        related_org_groups: TypeFilter('related_objects', 'OrgGroup'),
        related_vendors: TypeFilter('related_objects', 'Vendor'),
        related_processes: TypeFilter('related_objects', 'Process'),
        related_products: TypeFilter('related_objects', 'Product'),
        related_projects: TypeFilter('related_objects', 'Project'),
        related_systems: TypeFilter('related_objects', 'System'),
        related_issues: TypeFilter('related_objects', 'Issue'),
        related_audits: TypeFilter('related_objects', 'Audit'),
        related_controls: TypeFilter('related_objects', 'Control'),
        related_documents: TypeFilter('related_objects', 'Document'),
        related_assessments: TypeFilter('related_objects', 'Assessment'),
        regulations: TypeFilter('related_objects', 'Regulation'),
        contracts: TypeFilter('related_objects', 'Contract'),
        policies: TypeFilter('related_objects', 'Policy'),
        standards: TypeFilter('related_objects', 'Standard'),
        programs: TypeFilter('related_objects', 'Program'),
        controls: TypeFilter('related_objects', 'Control'),
        sections: TypeFilter('related_objects', 'Section'),
        clauses: TypeFilter('related_objects', 'Clause'),
        objectives: TypeFilter('related_objects', 'Objective'),
        cycle: Direct(
          'Cycle', 'cycle_task_group_object_tasks', 'cycle'),
        cycle_task_group: Direct(
          'CycleTaskGroup',
          'cycle_task_group_object_tasks',
          'cycle_task_group'),
        cycle_task_entries: Direct(
          'CycleTaskEntry',
          'cycle_task_group_object_task',
          'cycle_task_entries'),

        info_related_objects: CustomFilter(
          'related_objects',
          function (relatedObjects) {
            return !_.includes(
              ['Comment', 'Document', 'Person'],
              relatedObjects.instance.type
            );
          }
        ),

        // This code needs to be reworked to figure out how to return the single
        // most recent task entry with is_declining_review = true.
        declining_cycle_task_entries: Search(function (binding) {
          return CMS.Models.CycleTaskEntry.findAll({
            cycle_task_group_object_task_id: binding.instance.id,
            is_declining_review: 1
          });
        }, 'Cycle')
      },

      CycleTaskEntry: {
        documents: Proxy(
          'Document',
          'document', 'ObjectDocument',
          'documentable', 'object_documents'
        ),
        cycle: Direct(
          'Cycle', 'cycle_task_entries', 'cycle'),
        cycle_task_group_object_task: Direct(
          'CycleTaskGroupObjectTask',
          'cycle_task_entries',
          'cycle_task_group_object_task'),
        workflow: Cross('cycle', 'workflow')
      },

      People: {
        _canonical: {
          workflows: 'Workflow'
        },
        workflows: Proxy(
          'Workflow', 'workflow', 'WorkflowPerson', 'person', 'workflow_people'
        )

      },
      Person: {
        assigned_tasks: Search(function (binding) {
          return CMS.Models.CycleTaskGroupObjectTask.findAll({
            contact_id: binding.instance.id,
            'cycle.is_current': true,
            status__in: 'Assigned,InProgress,Finished,Declined'
          });
        }, 'Cycle'),
        assigned_tasks_with_history: Search(function (binding) {
          return CMS.Models.CycleTaskGroupObjectTask.findAll({
            contact_id: binding.instance.id
          });
        }, 'Cycle')
      }
    };

    // Insert `workflows` mappings to all business object types
    can.each(_workflowObjectTypes, function (type) {
      var model = CMS.Models[type];
      if (model === undefined || model === null) {
        return;
      }
      mappings[type] = {
        task_groups:
          new GGRC.ListLoaders.ProxyListLoader(
            'TaskGroupObject',
            'object',
            'task_group',
            'task_group_objects',
            null
          ),
        object_tasks: TypeFilter('related_objects', 'CycleTaskGroupObjectTask'),
        approval_tasks: CustomFilter('object_tasks', function (object) {
          return object.instance.attr('object_approval');
        }),
        workflows: Cross('task_groups', 'workflow'),
        approval_workflows: CustomFilter('workflows', function (binding) {
          return binding.instance.attr('object_approval');
        }),
        current_approval_cycles: Cross('approval_workflows', 'current_cycle'),
        _canonical: {
          workflows: 'Workflow',
          task_groups: 'TaskGroup'
        }
      };
      mappings[type].orphaned_objects = Multi([
        GGRC.Mappings.get_mappings_for(type).orphaned_objects,
        mappings[type].workflows
      ]);

      CMS.Models[type].attributes.task_group_objects =
        'CMS.Models.TaskGroupObject.stubs';

      // Also register a render hook for object approval
      GGRC.register_hook(
        type + '.info_widget_actions',
        GGRC.mustache_path + '/base_objects/approval_link.mustache'
        );
    });
    new GGRC.Mappings('ggrc_workflows', mappings);
  };

  // Override GGRC.extra_widget_descriptors and GGRC.extra_default_widgets
  // Initialize widgets for workflow page
  WorkflowExtension.init_widgets = function () {
    var pageInstance = GGRC.page_instance();
    var treeWidgets = GGRC.tree_view.base_widgets_by_type;
    var subTrees = GGRC.tree_view.sub_tree_for;
    var subTreeItems = ['Cycle'];
    var models = ['TaskGroup', 'Workflow', 'CycleTaskEntry',
      'CycleTaskGroupObjectTask', 'CycleTaskGroupObject', 'CycleTaskGroup'];
    _.each(_workflowObjectTypes, function (type) {
      var widget;
      if (!type || !treeWidgets[type]) {
        return;
      }

      widget = subTrees[type];

      treeWidgets[type] = treeWidgets[type].concat(models);
      if (!_.isEmpty(subTrees.serialize)) {
        widget.attr({
          display_list: widget.display_list
            .concat(['CycleTaskGroupObjectTask']),
          model_list: widget.model_list
            .concat({
              display_name: CMS.Models.CycleTaskGroupObjectTask.title_singular,
              display_status: true,
              model_name: 'CycleTaskGroupObjectTask'
            })
        });
      }
    });
    subTreeItems.concat(models).forEach(function (item) {
      var defaults = {
        model_list: GGRC.tree_view.basic_model_list,
        display_list: can.Map.keys(GGRC.tree_view.base_widgets_by_type)
      };
      defaults.display_list.concat(models);

      treeWidgets.attr(item,
        can.Map.keys(GGRC.tree_view.base_widgets_by_type).concat(models));
      subTrees.attr(item, {
        display_list: defaults.display_list
          .concat(models),
        model_list: defaults.model_list
      });
    });

    if (pageInstance instanceof CMS.Models.Workflow) {
      WorkflowExtension.init_widgets_for_workflow_page();
    } else if (pageInstance instanceof CMS.Models.Person) {
      WorkflowExtension.init_widgets_for_person_page();
    } else {
      WorkflowExtension.init_widgets_for_other_pages();
    }
  };

  WorkflowExtension.init_widgets_for_other_pages = function () {
    var descriptor = {};
    var pageInstance = GGRC.page_instance();

    if (
      pageInstance &&
      ~can.inArray(pageInstance.constructor.shortName, _workflowObjectTypes)
    ) {
      descriptor[pageInstance.constructor.shortName] = {
        workflow: {
          widget_id: 'workflow',
          widget_name: 'Workflows',
          widgetType: 'treeview',
          treeViewDepth: 0,
          content_controller_options: {
            mapping: 'workflows',
            parent_instance: pageInstance,
            model: CMS.Models.Workflow
          }
        },
        task: {
          widget_id: 'task',
          widget_name: 'Workflow Tasks',
          widgetType: 'treeview',
          treeViewDepth: 1,
          content_controller_options: {
            mapping: 'object_tasks',
            parent_instance: pageInstance,
            model: CMS.Models.CycleTaskGroupObjectTask,
            add_item_view:
              GGRC.mustache_path +
              '/cycle_task_group_object_tasks/tree_add_item.mustache',
            sort_property: null,
            sort_function: _taskSortFunction,
            draw_children: true,
            events: {
              'show-history': function (el, ev) {
                this.options.attr('mapping', el.attr('mapping'));
                this.reload_list();
              }
            }
          }
        }
      };
    }

    new GGRC.WidgetList('ggrc_workflows', descriptor, [
      'info_widget',
      'task_widget'
    ]);
  };

  WorkflowExtension.init_widgets_for_workflow_page = function () {
    var newWidgetDescriptors = {};
    var newDefaultWidgets = [
      'info', 'person', 'task_group', 'current', 'history'
    ];
    var historyWidgetDescriptor;
    var currentWidgetDescriptor;
    var object = GGRC.page_instance();

    can.each(
      GGRC.WidgetList.get_current_page_widgets(),
      function (descriptor, name) {
        if (~newDefaultWidgets.indexOf(name)) {
          newWidgetDescriptors[name] = descriptor;
        }
      }
    );

    // Initialize controller -- probably this should go in a separate
    // initialization area
    $(document.body).ggrc_controllers_workflow_page();

    GGRC.register_hook(
        'ObjectNav.Actions',
        GGRC.mustache_path + '/dashboard/object_nav_actions');

    $.extend(
      true,
      newWidgetDescriptors,
      {
        info: {
          content_controller: GGRC.Controllers.InfoWidget,
          content_controller_options: {
            widget_view: GGRC.mustache_path + '/workflows/info.mustache'
          }
        },
        person: {
          widget_id: 'person',
          widget_name: 'People',
          widget_icon: 'person',
          widgetType: 'treeview',
          treeViewDepth: 3,
          model: CMS.Models.Person,
          content_controller_options: {
            parent_instance: object,
            model: CMS.Models.Person,
            mapping: 'mapped_and_or_authorized_people',
            add_item_view:
              GGRC.mustache_path + '/wf_people/tree_add_item.mustache'
          }
        },
        task_group: {
          widget_id: 'task_group',
          widget_name: 'Setup',
          widget_icon: 'task_group',
          widgetType: 'treeview',
          treeViewDepth: 0,
          model: CMS.Models.TaskGroup,
          content_controller_options: {
            parent_instance: object,
            model: CMS.Models.TaskGroup,
            sortable: true,
            sort_property: 'sort_index',
            mapping: 'task_groups',
            draw_children: true
          }
        }
      }
    );

    historyWidgetDescriptor = {
      widgetType: 'treeview',
      treeViewDepth: 3,
      widget_id: 'history',
      widget_name: 'History',
      widget_icon: 'history',
      model: CMS.Models.Cycle,
      content_controller_options: {
        draw_children: true,
        parent_instance: object,
        model: CMS.Models.Cycle,
        countsName: historyWidgetCountsName,
        mapping: 'previous_cycles',
        additional_filter: historyWidgetFilter
      }
    };

    currentWidgetDescriptor = {
      widgetType: 'treeview',
      treeViewDepth: 3,
      widget_id: 'current',
      widget_name: 'Active Cycles',
      widget_icon: 'cycle',
      model: CMS.Models.Cycle,
      content_controller_options: {
        draw_children: true,
        parent_instance: object,
        model: CMS.Models.Cycle,
        countsName: currentWidgetCountsName,
        mapping: 'current_cycle',
        additional_filter: currentWidgetFilter,
        header_view: GGRC.mustache_path + '/cycles/tree_header.mustache',
        add_item_view:
          GGRC.mustache_path +
          '/cycle_task_group_object_tasks/tree_add_item.mustache'
      }
    };

    newWidgetDescriptors.history = historyWidgetDescriptor;
    newWidgetDescriptors.current = currentWidgetDescriptor;

    GGRC.Utils.CurrentPage
      .initCounts([
        WorkflowExtension.countsMap.history,
        WorkflowExtension.countsMap.activeCycles,
        WorkflowExtension.countsMap.person,
        WorkflowExtension.countsMap.taskGroup
      ],
        object.type,
        object.id);

    new GGRC.WidgetList(
      'ggrc_workflows',
      {Workflow: newWidgetDescriptors}
    );

    // Setup extra refresh required due to automatic creation of permissions
    // on creation of WorkflowPerson
    CMS.Models.WorkflowPerson.bind('created', function (ev, instance) {
      if (instance instanceof CMS.Models.WorkflowPerson) {
        if (instance.context) {
          instance.context.reify().refresh();
        }
      }
    });
  };

  WorkflowExtension.init_widgets_for_person_page = function () {
    var descriptor = {};
    var pageInstance = GGRC.page_instance();

    descriptor[pageInstance.constructor.shortName] = {
      task: {
        widget_id: 'task',
        widget_name: 'My Tasks',
        model: CMS.Models.CycleTaskGroupObjectTask,
        content_controller_options: {
          parent_instance: GGRC.page_instance(),
          model: CMS.Models.CycleTaskGroupObjectTask,
          add_item_view:
            GGRC.mustache_path +
            '/cycle_task_group_object_tasks/tree_add_item.mustache',
          mapping: 'assigned_tasks',
          sort_property: null,
          sort_function: _taskSortFunction,
          draw_children: true,
          events: {
            'show-history': function (el, ev) {
              this.options.attr('mapping', el.attr('mapping'));
              this.reload_list();
            }
          }
        }
      }
    };
    new GGRC.WidgetList('ggrc_workflows', descriptor, [
      'info_widget',
      'task_widget'
    ]);
  };

  GGRC.register_hook(
      'Dashboard.Widgets', GGRC.mustache_path + '/dashboard/widgets');

  GGRC.register_hook(
      'Dashboard.Errors', GGRC.mustache_path + '/dashboard/info/errors');

  WorkflowExtension.init_mappings();

  draftOnUpdateMixin = can.Model.Mixin({
  }, {
    before_update: function () {
      if (this.status && this.os_state === 'Approved') {
        this.attr('status', 'Draft');
      }
    }
  });
  can.each(_workflowObjectTypes, function (modelName) {
    var model = CMS.Models[modelName];
    if (model === undefined || model === null) {
      return;
    }
    draftOnUpdateMixin.add_to(model);
  });
})(this.can.$, this.CMS, this.GGRC);
