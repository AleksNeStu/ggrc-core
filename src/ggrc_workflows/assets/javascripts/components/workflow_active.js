  /*!
  Copyright (C) 2017 Google Inc.
  Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

(function (GGRC, can) {
  'use strict';

  function _generate_cycle() {
    var workflow = GGRC.page_instance();
    var dfd = new $.Deferred();
    var cycle;

    GGRC.Controllers.Modals.confirm({
      modal_title: 'Confirm',
      modal_confirm: 'Proceed',
      skip_refresh: true,
      button_view: GGRC.mustache_path + '/workflows/confirm_start_buttons.mustache',
      content_view: GGRC.mustache_path + '/workflows/confirm_start.mustache',
      instance: workflow
    }, function (params, option) {
      var data = {};

      can.each(params, function (item) {
        data[item.name] = item.value;
      });

      cycle = new CMS.Models.Cycle({
        context: workflow.context.stub(),
        workflow: {id: workflow.id, type: 'Workflow'},
        autogenerate: true
      });

      cycle.save().then(function (cycle) {
        // Cycle created. Workflow started.
        setTimeout(function () {
          dfd.resolve();
          window.location.hash = 'current_widget/cycle/' + cycle.id;
        }, 250);
      });
    }, function () {
      dfd.reject();
    });
    return dfd;
  }

  can.Component.extend({
    tag: 'workflow-start-cycle',
    content: '<content/>',
    events: {
      click: _generate_cycle
    }
  });

  can.Component.extend({
    tag: 'workflow-activate',
    template: '<content/>',
    init: function () {
      this.scope._can_activate_def();
    },
    scope: {
      waiting: true,
      can_activate: false,
      _can_activate_def: function () {
        var self = this;
        var workflow = GGRC.page_instance();

        self.attr('waiting', true);
        $.when(
          workflow.refresh_all('task_groups', 'task_group_objects'),
          workflow.refresh_all('task_groups', 'task_group_tasks')
        )
        .always(function () {
          self.attr('waiting', false);
        })
        .done(function () {
          var task_groups = workflow.task_groups.reify();
          var can_activate = task_groups.length;

          task_groups.each(function (task_group) {
            if (!task_group.task_group_tasks.length) {
              can_activate = false;
            }
          });
          self.attr('can_activate', can_activate);
        })
        .fail(function (error) {
          console.warn('Workflow activate error', error.message);
        });
      },
      _handle_refresh: function (model) {
        var models = ['TaskGroup', 'TaskGroupTask', 'TaskGroupObject'];
        if (models.indexOf(model.shortName) > -1) {
          this._can_activate_def();
        }
      },
      _restore_button: function () {
        this.attr('waiting', false);
      },
      _activate: function () {
        var workflow = GGRC.page_instance();
        var scope = this;
        var restore_button = scope._restore_button.bind(scope);

        scope.attr('waiting', true);
        if (workflow.frequency !== 'one_time') {
          workflow.refresh().then(function () {
            workflow.attr('recurrences', true);
            workflow.attr('status', 'Active');
            return workflow.save();
          }, restore_button).then(function (workflow) {
            if (moment(workflow.next_cycle_start_date)
                .isSame(moment(), 'day')) {
              return new CMS.Models.Cycle({
                context: workflow.context.stub(),
                workflow: {id: workflow.id, type: 'Workflow'},
                autogenerate: true
              }).save();
            }
          }, restore_button).then(function () {
            var WorkflowExtension =
              GGRC.extensions.find(function (extension) {
                return extension.name === 'workflows';
              });

            $('body').trigger('treeupdate');
            return GGRC.Utils.CurrentPage
              .initCounts([
                WorkflowExtension.countsMap.activeCycles
              ], {
                type: workflow.type,
                id: workflow.id
              });
          }, restore_button).then(restore_button);
        } else {
          _generate_cycle().then(function () {
            return workflow.refresh();
          }, restore_button).then(function (workflow) {
            return workflow.attr('status', 'Active').save();
          }, restore_button).then(restore_button);
        }
      }
    },
    events: {
      '{can.Model.Cacheable} created': function (model) {
        this.scope._handle_refresh(model);
      },
      '{can.Model.Cacheable} destroyed': function (model) {
        this.scope._handle_refresh(model);
      },
      'button click': function () {
        this.scope._activate();
      }
    }
  });
})(window.GGRC, window.can);
