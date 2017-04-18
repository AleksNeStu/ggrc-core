/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, GGRC) {
  'use strict';

  var template = can.view(GGRC.mustache_path +
    '/components/tree/tree-item-extra-info.mustache');
  var statusClasses = {
    Verified: 'state-verified',
    Assigned: 'state-assigned',
    Finished: 'state-finished',
    InProgress: 'state-inprogress',
    Overdue: 'state-overdue'
  };

  var viewModel = can.Map.extend({
    define: {
      isActive: {
        type: Boolean,
        get: function () {
          return this.attr('drawStatuses') ||
            this.attr('isDirective') ||
            this.attr('isCycleTasks') ||
            this.attr('isSection');
        }
      },
      isDirective: {
        type: Boolean,
        get: function () {
          return this.attr('instance') instanceof CMS.Models.Directive;
        }
      },
      isSection: {
        type: Boolean,
        get: function () {
          return this.attr('instance') instanceof CMS.Models.Section;
        }
      },
      isCycleTaskGroupObjectTask: {
        type: Boolean,
        get: function () {
          return this.attr('instance') instanceof
            CMS.Models.CycleTaskGroupObjectTask;
        }
      },
      isCycleTaskGroup: {
        type: Boolean,
        get: function () {
          return this.attr('instance') instanceof CMS.Models.CycleTaskGroup;
        }
      },
      isCycleTasks: {
        type: Boolean,
        get: function () {
          return this.attr('isCycleTaskGroup') ||
            this.attr('isCycleTaskGroupObjectTask') ||
            this.attr('instance') instanceof CMS.Models.Cycle;
        }
      },
      disablePopover: {
        type: Boolean,
        get: function () {
          return this.attr('instance') instanceof CMS.Models.Cycle;
        }
      },
      drawStatuses: {
        type: Boolean,
        get: function () {
          return !!this.attr('instance.workflow_state');
        }
      },
      cssClasses: {
        type: String,
        get: function () {
          var classes = [];
          var instance = this.attr('instance');
          if (this.attr('drawStatuses')) {
            classes.push(statusClasses[instance.workflow_state]);
          }

          if (this.attr('isCycleTasks') && this.isOverdue()) {
            classes.push(statusClasses.Overdue);
          }

          if (this.attr('spin')) {
            classes.push('fa-spinner');
            classes.push('fa-spin');
          } else {
            classes.push('fa-info-circle');
          }
          return classes.join(' ');
        }
      }
    },
    onEnter: function () {
      this.attr('spin', true);
    },
    onLeave: function () {
      this.attr('spin', false);
    },
    isOverdue: function () {
      var task = this.attr('instance');
      var endDate = new Date(task.end_date || null);
      var status = task.status;
      var today = new Date();

      if (status === "Finished" || status === "Verified")
        return false;
      else if (endDate.getTime() < today.getTime())
        return true;
    },
    classes: [],
    instance: null
  });

  GGRC.Components('treeItemExtraInfo', {
    tag: 'tree-item-extra-info',
    template: template,
    viewModel: viewModel,
    events: {}
  });
})(window.can, window.GGRC);
