/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, GGRC) {
  'use strict';

  var template = can.view(GGRC.mustache_path +
    '/components/cycle-task-actions/cycle-task-actions.mustache');
  var viewModel = can.Map.extend({
    define: {
      cycle: {
        get: function () {
          return this.attr('instance').cycle;
        }
      },
      workflow: {
        get: function () {
          return this.attr('instance.cycle.workflow');
        }
      },
      cssClasses: {
        type: String,
        get: function () {
          var classes = [];

          if (this.attr('disabled')) {
            classes.push('disabled');
          }

          return classes.join(' ');
        }
      }
    },
    instance: null,
    disabled: false,
    oldValues: [],
    isBacklog: function () {
      var result = false;
      var cycle;

      if (this.attr('instance') instanceof CMS.Models.CycleTaskGroup) {
        cycle = this.attr('instance').cycle.reify();
        result = cycle.workflow.reify().kind === 'Backlog';
      }

      return result;
    },
    isCurrent: function () {
      return this.attr('cycle').reify().is_current;
    },
    changeStatus: function (ctx, el, ev) {
      var status = el.data('value');
      var openclose = el.data('openclose');
      var instance = this.attr('instance');
      var oldValue = {
        status: instance.attr('status')
      };
      var expanded;

      ev.stopPropagation();
      this.attr('oldValues').unshift(oldValue);

      if (openclose) {
        if (openclose === 'open') {
          expanded = true;
        } else if (openclose === 'close') {
          expanded = false;
        }
        this.dispatch({
          type: 'expand',
          state: expanded
        });
      }

      this.setStatus(status);
    },
    undo: function (ctx, el, ev) {
      var newValue = this.attr('oldValues').shift();
      ev.stopPropagation();

      this.setStatus(newValue.status);
    },
    setStatus: function (status) {
      var instance = this.attr('instance');

      this.attr('disabled', true);
      instance.refresh().then(function (refreshed) {
        refreshed.attr('status', status);

        return refreshed.save();
      }).then(function () {
        this.attr('disabled', false);
      }.bind(this));
    }
  });

  /**
   *
   */
  GGRC.Components('cycleTaskActions', {
    tag: 'cycle-task-actions',
    template: template,
    viewModel: viewModel,
    events: {
      inserted: function () {
      }
    }
  });
})(window.can, window.GGRC);
