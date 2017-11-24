/*!
    Copyright (C) 2017 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

(function (can, $) {
  /* Role Assignment Modal Selector
   *
   * parameters:
   *   Templates:
   *     base_modal_view:
   *     option_column_view:
   *     active_column_view:
   *     option_object_view:
   *     active_object_view:
   *     option_detail_view:
   *
   *   Models and Queries:
   *     option_model: The model being "selected" (the "many")
   *     option_query:
   *       Any additional parameters needed to restrict valid options
   *     active_query:
   *       Any additional parameters needed to restrict active options
   *     join_model: The model representing the join table
   *     extra_join_query:
   *       Any additional parameters needed to restrict the join results
   *     extra_join_params:
   *       And additional parameters to be POSTed in the join object
   *
   *   Customizable text components:
   *     modal_title:
   *     option_list_title:
   *     active_list_title:
   *     new_object_title:
   */
  can.Control('GGRC.Controllers.UserRolesModalSelector', {
    _templates: [
      'base_modal_view',
      'option_column_view',
      'active_column_view',
      'option_object_view',
      'active_object_view',
      'option_detail_view'
    ],

    defaults: {
      base_modal_view:
        GGRC.mustache_path + '/selectors/base_modal.mustache',
      option_column_view:
        GGRC.mustache_path + '/selectors/option_column.mustache',
      active_column_view:
        GGRC.mustache_path + '/selectors/active_column.mustache',
      option_object_view: null,
      active_object_view: null,
      option_detail_view:
        GGRC.mustache_path + '/selectors/option_detail.mustache',

      option_model: null,
      option_query: {},
      active_query: {},
      join_model: null,
      join_query: {},
      join_object: null,

      selected_id: null,

      modal_title: null,
      option_list_title: null,
      active_list_title: null,
      new_object_title: null
    },

    launch: function ($trigger, options) {
      // Extract parameters from data attributes
      var href = $trigger.attr('data-href') || $trigger.attr('href');
      var modalId =
        'ajax-modal-' + href.replace(/[\/\?=\&#%]/g, '-').replace(/^-/, '');
      var $target = $(
        '<div id="' + modalId + '" class="modal modal-selector hide"></div>'
      );
      var scope = $trigger.attr('data-modal-scope') || null;

      options.scope = scope;
      $target.modal_form({}, $trigger);
      this.newInstance($target[0], $.extend({$trigger: $trigger}, options));
      return $target;
    }
  }, {
    init: function () {
      this.object_list = new can.Observe.List();
      this.option_list = new can.Observe.List();
      this.join_list = new can.Observe.List();
      this.active_list = new can.Observe.List();

      this.init_context();
      this.init_bindings();
      this.init_view();
      this.init_data();
    },

    '.object_column li click': 'select_object',
    '.option_column li click': 'select_option',
    '.confirm-buttons a.btn:not(.disabled) click': 'change_option',

    init_bindings: function () {
      this.join_list.bind('change', this.proxy('update_active_list'));
      this.context.bind('selected_object', this.proxy('refresh_join_list'));
      this.option_list.bind('change', this.proxy('update_option_radios'));
    },

    init_view: function () {
      var self = this;
      var deferred = $.Deferred();

      can.view(
        this.options.base_modal_view,
        this.context,
        function (frag) {
          $(self.element).html(frag);
          deferred.resolve();
          self.element.trigger('loaded');
        });

      this.on();  // Start listening for events

      return deferred;
    },

    init_data: function () {
      return $.when(
        this.refresh_object_list(),
        this.refresh_option_list(),
        this.refresh_join_list()
      );
    },

    init_context: function () {
      if (!this.context) {
        this.context = new can.Observe($.extend({
          objects: this.object_list,
          options: this.option_list,
          joins: this.join_list,
          actives: this.active_list,
          selected_object: null,
          selected_option: null,
          page_model: GGRC.page_model
        }, this.options));
      }
      return this.context;
    },

    update_active_list: function () {
      var self = this;

      self.active_list.replace(
        can.map(self.join_list, function (join) {
          return new can.Observe({
            option: CMS.Models.get_instance(
              CMS.Models.get_link_type(join, self.options.option_attr),
              join[self.options.option_attr].id
            ),
            join: join
          });
        }));
    },

    refresh_object_list: function () {
      var self = this;

      return this.options.object_model.findAll(
        $.extend({}, this.options.object_query),
        function (objects) {
          self.object_list.replace(objects);
          if (self.object_list.length === 1) {
            self.context.attr('selected_object', self.object_list[0]);
          }
        });
    },

    refresh_option_list: function () {
      var self = this;
      var instance = GGRC.page_instance();
      var params = {};

      // If this is a private model, set the scope
      if (self.options.scope) {
        params.scope = self.options.scope;
      } else if (
        instance &&
        instance.constructor.shortName === 'Workflow' &&
        instance.context
      ) {
        params.scope = 'Workflow';
      } else if (
        instance &&
        instance.constructor.shortName === 'Program' &&
        instance.context
      ) {
        params.scope = 'Private Program';
      } else if (/admin/.test(window.location)) {
        params.scope__in = 'System,Admin';
      } else if (instance) {
        params.scope = instance.constructor.shortName;
      }

      return this.options.option_model.findAll(
        $.extend(params, this.option_query),
        function (options) {
          var description;

          options = can.makeArray(_.sortBy(options, 'role_order'));

          if (params.scope === 'Private Program') {
            description =
              'A person with no role will not be able to see the program, ' +
              'unless they have a system wide role (Reader, Editor, Admin) ' +
              'that allows it.';
          } else if (params.scope === 'Workflow') {
            description =
              'A person with the No Role role will not be able to update ' +
              'or contribute to this Workflow.';
          } else {
            description =
              'This role allows a user access to the MyWork dashboard and ' +
              'applications Help files.';
          }
          options.unshift({
            name: 'No role',
            id: 0,
            description: description,
            scope: params.scope || 'System'
          });
          self.option_list.replace(options);
        });
    },

    refresh_join_list: function () {
      var self = this;
      var joinObject = this.get_join_object();
      var joinQuery;

      if (joinObject) {
        joinQuery = can.extend({}, this.options.extra_join_query);
        joinQuery[this.options.join_id_field] = this.get_join_object_id();
        if (this.options.join_type_field) {
          joinQuery[this.options.join_type_field] =
            this.get_join_object_type();
        }

        return this.options.join_model.findAll(
          $.extend({}, joinQuery),
          function (joins) {
            self.join_list.replace(joins);
            self.update_option_radios();
          });
      }

      return $.Deferred().resolve();
    },

    update_option_radios: function () {
      var allowedIds = can.map(this.context.options, function (join) {
        return join.id;
      });
      if (!allowedIds.length) {
        return;
      }
      if (!this.join_list.length) {
        this.context.attr('selected_id', 0);
      }
      this.join_list.forEach(function (join) {
        var id = join[this.options.option_attr].id;
        if (allowedIds.indexOf(id) >= 0) {
          this.context.attr('selected_id', id);
        }
      }.bind(this));
    },

    select_object: function (el) {
      el.closest('.object_column').find('li').removeClass('selected');
      el.addClass('selected');
      this.context.attr('selected_object', el.data('object'));
    },

    select_option: function (el) {
      el.closest('.option_column').find('li').removeClass('selected');
      el.addClass('selected');
      this.context.attr('selected_option', el.data('option'));
    },

    change_option: function (el_, ev) {
      var self = this;
      var el = $('.people-selector').find('input[type=radio]:checked');
      var li = el.closest('li');
      var clickedOption = li.data('option') || {};
      var join;
      var deleteDfds;
      var alreadyExists = false;

      // Look for and remove the existing join.
      deleteDfds = $.map(li.parent().children(), function (el) {
        var $el = $(el);
        var option = $el.closest('li').data('option');
        var join = self.find_join(option.id);

        if (join && join.role.id === clickedOption.id) {
          // Don't delete the role we marked to add.
          alreadyExists = true;
          return;
        }
        if (join) {
          return join.refresh().then(function () {
            return join.destroy();
          }).then(function () {
            self.refresh_object_list();
            self.element.trigger('relationshipdestroyed', join);
          });
        }
      });

      // Create the new join (skipping "No Role" role, with id == 0)
      if (clickedOption.id > 0 && !alreadyExists) {
        $.when.apply($, deleteDfds).then(function () {
          join = self.get_new_join(
            clickedOption.id,
            clickedOption.scope,
            clickedOption.constructor.shortName
          );
          join.save().then(function () {
            self.join_list.push(join);
            self.refresh_option_list();
            self.refresh_object_list();
            self.element.trigger('relationshipcreated', join);
          });
        });
      } else {
        $.when.apply($, deleteDfds).then(function () {
          $('body').trigger('treeupdate');
        });
      }
    },

    // HELPERS

    find_join: function (optionId) {
      var self = this
        ;

      return can.reduce(
        this.join_list,
        function (result, join) {
          if (result) {
            return result;
          }
          if (self.match_join(optionId, join)) {
            return join;
          }
        },
        null
      );
    },

    match_join: function (optionId, join) {
      return (
        join[this.options.option_attr] &&
        join[this.options.option_attr].id == optionId
      );
    },

    get_new_join: function (optionId, optionScope, optionType) {
      var joinParams = {};
      joinParams[this.options.option_attr] = {};
      joinParams[this.options.option_attr].id = optionId;
      joinParams[this.options.option_attr].type = optionType;
      joinParams[this.options.join_attr] = {};
      joinParams[this.options.join_attr].id = this.get_join_object_id();
      joinParams[this.options.join_attr].type = this.get_join_object_type();

      $.extend(joinParams, this.options.extra_join_fields);
      if (optionScope === 'Admin') {
        joinParams.context = {id: 0, type: 'Context'};
      }
      return new (this.options.join_model)(joinParams);
    },

    get_join_object: function () {
      return this.context.attr('selected_object');
    },

    get_join_object_id: function () {
      return this.get_join_object().id;
    },

    get_join_object_type: function () {
      var joinObject = this.get_join_object();
      return (joinObject ? joinObject.constructor.shortName : null);
    }
  });

  function getOptionSet(name, data) {
    // Construct options for Authorizations selector
    var context;
    var objectQuery = {};
    var baseModalView;
    var extraJoinQuery;

    // Set object-specific context if requested (for Audits)
    if (data.params && data.params.context) {
      context = data.params.context;
      extraJoinQuery = {context_id: context.id};
    } else if (GGRC.page_object && !GGRC.page_object.person) {
      // Otherwise use the page context
      context = GGRC.make_model_instance(GGRC.page_object).context;
      if (!context) {
        throw new Error('`context` is required for Assignments model');
      }
      context = context.stub();
      extraJoinQuery = {context_id: context.id};
    } else {
      context = {id: null};
      extraJoinQuery = {context_id__in: [context.id, 0]};
    }

    if (data.person_id) {
      objectQuery = {id: data.person_id};
    }

    baseModalView =
        '/ggrc_basic_permissions/people_roles/base_modal.mustache';

    return {
      base_modal_view: GGRC.mustache_path + baseModalView,
      option_column_view:
        GGRC.mustache_path +
        '/ggrc_basic_permissions/people_roles/option_column.mustache',
      option_detail_view:
        GGRC.mustache_path +
        '/ggrc_basic_permissions/people_roles/option_detail.mustache',
      active_column_view:
        GGRC.mustache_path +
        '/ggrc_basic_permissions/people_roles/active_column.mustache',

      object_column_view:
        GGRC.mustache_path +
        '/ggrc_basic_permissions/people_roles/object_column.mustache',
      object_detail_view:
        GGRC.mustache_path +
        '/ggrc_basic_permissions/people_roles/object_detail.mustache',

      new_object_title: 'Person',
      modal_title: data.modal_title || 'User Role Assignments',

      related_model_singular: 'Person',
      related_table_plural: 'people',
      related_title_singular: 'Person',
      related_title_plural: 'People',

      object_model: CMS.Models.Person,
      option_model: CMS.Models.Role,
      join_model: CMS.Models.UserRole,

      object_query: objectQuery,

      // join_object_attr
      option_attr: 'role',
      // join_option_attr
      join_attr: 'person',
      // join_option_id_field
      option_id_field: 'role_id',
      option_type_field: null,
      // join_object_id_field
      join_id_field: 'person_id',
      join_type_field: null,

      extra_join_fields: {
        context: context
      },
      extra_join_query: extraJoinQuery
    };
  }

  $(function () {
    $('body').on(
      'click',
      '[data-toggle="user-roles-modal-selector"]',
      function (ev) {
        var $this = $(this);
        var options = $this.data('modal-selector-options');
        var dataSet = can.extend({}, $this.data());
        var objectParams = $this.attr('data-object-params');

        dataSet.params = objectParams && JSON.parse(
          objectParams.replace(/\\n/g, '\\n')
        );

        can.each($this.data(), function (v, k) {
          //  This is just a mapping of keys to underscored keys
          var newKey = k.replace(
              /[A-Z]/g,
              function (str) {
                return '_' + str.toLowerCase();
              }
          );

          dataSet[newKey] = v;
          //  If we changed the key at all, delete the original
          if (newKey !== k) {
            delete dataSet[k];
          }
        });

        if (typeof options === 'string') {
          options = getOptionSet(options, dataSet);
        }

        ev.preventDefault();
        ev.stopPropagation();

        // Trigger the controller
        GGRC.Controllers.UserRolesModalSelector.launch($this, options)
          .on('relationshipcreated relationshipdestroyed', function (ev, data) {
            // $this.trigger("modal:" + ev.type, data);
          });
      });
  });
})(window.can, window.can.$);
