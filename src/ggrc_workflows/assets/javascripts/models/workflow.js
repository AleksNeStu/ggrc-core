/*!
    Copyright (C) 2017 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/


(function(can) {

  can.Model.Cacheable("CMS.Models.Workflow", {
    root_object: "workflow",
    root_collection: "workflows",
    category: "workflow",
    mixins: ['ca_update', 'timeboxed'],
    findAll: "GET /api/workflows",
    findOne: "GET /api/workflows/{id}",
    create: "POST /api/workflows",
    update: "PUT /api/workflows/{id}",
    destroy: "DELETE /api/workflows/{id}",
    is_custom_attributable: true,

    defaults: {
      frequency_options: [
        {title: 'One time', value: 'one_time'},
        {title: 'Weekly', value: 'weekly'},
        {title: 'Monthly', value: 'monthly'},
        {title: 'Quarterly', value: 'quarterly'},
        {title: 'Annually', value: 'annually'}
      ],
      frequency: 'one_time' // default value
    },

    attributes: {
      people: "CMS.Models.Person.stubs",
      workflow_people: "CMS.Models.WorkflowPerson.stubs",
      task_groups: "CMS.Models.TaskGroup.stubs",
      cycles: "CMS.Models.Cycle.stubs",
      //workflow_task_groups: "CMS.Models.WorkflowTaskGroup.stubs"
      modified_by: "CMS.Models.Person.stub",
      context: "CMS.Models.Context.stub",
      custom_attribute_values: "CMS.Models.CustomAttributeValue.stubs",
      default_lhn_filters: {
        Workflow: {status: 'Active'},
        Workflow_All: {},
        Workflow_Active: {status: 'Active'},
        Workflow_Inactive: {status: 'Inactive'},
        Workflow_Draft: {status: 'Draft'}
      }
    },
    obj_nav_options: {
      show_all_tabs: true,
    },
    tree_view_options: {
      attr_view: GGRC.mustache_path + '/workflows/tree-item-attr.mustache',
      attr_list : [
        {attr_title: 'Title', attr_name: 'title'},
        {attr_title: 'Manager', attr_name: 'owner', attr_sort_field: ''},
        {attr_title: 'Code', attr_name: 'slug'},
        {attr_title: 'State', attr_name: 'status'},
        {attr_title: 'Frequency', attr_name: 'frequency'},
        {attr_title: 'Last Updated', attr_name: 'updated_at'}
      ]
    },

    init: function() {
      this._super && this._super.apply(this, arguments);
      this.validateNonBlank("title");
      this.bind("destroyed", function(ev, inst) {
        if(inst instanceof CMS.Models.Workflow) {
          can.each(inst.cycles, function(cycle) {
            if (!cycle) {
              return;
            }
            cycle = cycle.reify()
            can.trigger(cycle, "destroyed");
            can.trigger(cycle.constructor, "destroyed", cycle);
          });
          can.each(inst.task_groups, function(tg) {
            if (!tg) {
              return;
            }
            tg = tg.reify();
            can.trigger(tg, "destroyed");
            can.trigger(tg.constructor, "destroyed", tg);
          });
        }
      });
    }
  }, {
    save: function () {
      var taskGroupTitle = this.task_group_title;
      var redirectLink;
      var taskGroup;
      var dfd;

      dfd = this._super.apply(this, arguments);
      dfd.then(function (instance) {
        redirectLink = instance.viewLink + '#task_group_widget';
        instance.attr('_redirect', redirectLink);
        if (!taskGroupTitle) {
          return instance;
        }
        taskGroup = new CMS.Models.TaskGroup({
          title: taskGroupTitle,
          workflow: instance,
          contact: instance.people && instance.people[0] || instance.modified_by,
          context: instance.context
        });
        return taskGroup.save()
          .then(function (tg) {
            // Prevent the redirect form workflow_page.js
            taskGroup.attr('_no_redirect', true);
            instance.attr('_redirect', redirectLink + '/task_group/' + tg.id);
            return this;
          }.bind(this));
      }.bind(this));
      return dfd;
    },
    // Check if task groups are slated to start
    //   in the current week/month/quarter/year
    is_mid_frequency: function() {
      var dfd = new $.Deferred(),
          self = this;

      function _afterOrSame(d1, d2) {
        return d1.isAfter(d2, 'day') || d1.isSame(d2, 'day');
      }
      function _beforeOrSame(d1, d2) {
        return d1.isBefore(d2, 'day') || d1.isSame(d2, 'day');
      }
      function _currentQuarter() {
        return moment().dayOfYear(1).quarter(moment().quarter());
      }
      function _check_all_tasks(tasks) {
        tasks.each(function(task) {
          var start, end, current = moment();
          task = task.reify();
          switch(self.frequency) {
            case "weekly":
              start = moment().isoWeekday(task.relative_start_day);
              end = moment().isoWeekday(task.relative_end_day);
              if (_afterOrSame(start, end)) {
                end.add(1, 'w');
              }
              break;
            case "monthly":
              start = moment().date(task.relative_start_day);
              end = moment().date(task.relative_end_day);
              if (_afterOrSame(start, end)) {
                end.add(1, 'M');
              }
              break;
            case "quarterly":
              start = _currentQuarter().date(task.relative_start_day).add(task.relative_start_month-1, 'M');
              end = _currentQuarter().date(task.relative_end_day).add(task.relative_end_month-1, 'M');
              if (_afterOrSame(start, end)) {
                end.add(1, 'q');
              }
              break;
            case "annually":
              start = moment().date(task.relative_start_day).month(task.relative_start_month-1);
              end = moment().date(task.relative_end_day).month(task.relative_end_month-1);
              if (_afterOrSame(start, end)) {
                end.add(1, 'y');
              }
              break;
          }
          if (_afterOrSame(current, start) && _beforeOrSame(current, end)) {
            dfd.resolve(true);
          }
        });
        dfd.resolve(false);
      }

      if (!this.frequency_duration || this.frequency === 'one_time') {
        return dfd.resolve(false);
      }

      // Check each task in the workflow:
      this.refresh_all('task_groups', 'task_group_tasks').then(function(s) {
        var tasks = new can.List();
        self.task_groups.each(function(task_group) {
          task_group.reify().task_group_tasks.each(function(task) {
            tasks.push(task.reify());
          });
        });
        _check_all_tasks(tasks);
      });
      return dfd;
    },

    // Get duration from frequency or false for one_time or continuous wfs.
    frequency_duration: function() {
      switch (this.frequency) {
        case "weekly": return "week";
        case "monthly": return "month";
        case "quarterly": return "quarter";
        case "annually": return "year";
        default: return false;
      }
    },
    // start day of month, affects start_date.
    //  Use when month number doesn't matter or is
    //  selectable.
    start_day_of_month: function(val) {
      var newdate;
      if(val) {
        while(val.isComputed) {
          val = val();
        }
        if(val > 31) {
          val = 31;
        }
        newdate = new Date(this.start_date || null);
        while(moment(newdate).daysInMonth() < val) {
          newdate.setMonth((newdate.getMonth() + 1) % 12);
        }
        newdate.setDate(val);
        this.attr("start_date", newdate);
      } else {
        newdate = this.attr("start_date");
        if(newdate) {
          return newdate.getDate();
        } else {
          return null;
        }
      }
    },

    // end day of month, affects end_date.
    //  Use when month number doesn't matter or is
    //  selectable.
    end_day_of_month: function(val) {
      var newdate;
      if(val) {
        while(val.isComputed) {
          val = val();
        }
        if(val > 31) {
          val = 31;
        }
        newdate = new Date(this.end_date || null);
        while(moment(newdate).daysInMonth() < val) {
          newdate.setMonth((newdate.getMonth() + 1) % 12);
        }
        newdate.setDate(val);
        this.attr("end_date", newdate);
      } else {
        newdate = this.attr("end_date");
        if(newdate) {
          return newdate.getDate();
        } else {
          return null;
        }
      }
    },

    // start month of quarter, affects start_date.
    //  Sets month to be a 31-day month in the chosen quarterly cycle:
    //  1 for Jan-Apr-Jul-Oct, 2 for Feb-May-Aug-Nov, 3 for Mar-Jun-Sep-Dec
    start_month_of_quarter: function(val) {
      var newdate;
      var month_lookup = [0, 4, 2]; //31-day months in quarter cycles: January, May, March

      if(val) {
        newdate = new Date(this.start_date || null);
        newdate.setMonth(month_lookup[(val - 1) % 3]);
        this.attr("start_date", newdate);
      } else {
        newdate = this.attr("start_date");
        if(newdate) {
          return newdate.getMonth() % 3 + 1;
        } else {
          return null;
        }
      }
    },

    // end month of quarter, affects end_date.
    //  Sets month to be a 31-day month in the chosen quarterly cycle:
    //  1 for Jan-Apr-Jul-Oct, 2 for Feb-May-Aug-Nov, 3 for Mar-Jun-Sep-Dec
    end_month_of_quarter: function(val) {
      var newdate;
      var month_lookup = [0, 7, 2]; //31-day months in quarter cycles: January, May, March

      if(val) {
        newdate = new Date(this.end_date || null);
        newdate.setMonth(month_lookup[(val - 1) % 3]);
        this.attr("end_date", newdate);
      } else {
        newdate = this.attr("end_date");
        if(newdate) {
          return newdate.getMonth() % 3 + 1;
        } else {
          return null;
        }
      }
    },

    // start month of yesr, affects start_date.
    //  Sets month to the chosen month, and adjusts
    //  day of month to be within chosen month
    start_month_of_year: function(val) {
      var newdate;
      if(val) {
        if(val > 12) {
          val = 12;
        }
        newdate = new Date(this.start_date || null);
        if(moment(newdate).date(1).month(val - 1).daysInMonth() < newdate.getDate()) {
          newdate.setDate(moment(newdate).date(1).month(val - 1).daysInMonth());
        }
        newdate.setMonth(val - 1);
        this.attr("start_date", newdate);
      } else {
        newdate = this.attr("start_date");
        if(newdate) {
          return newdate.getMonth() + 1;
        } else {
          return null;
        }
      }
    },

    // end month of yesr, affects end_date.
    //  Sets month to the chosen month, and adjusts
    //  day of month to be within chosen month
    end_month_of_year: function(val) {
      var newdate;
      if(val) {
        if(val > 12) {
          val = 12;
        }
        newdate = new Date(this.end_date || null);
        if(moment(newdate).date(1).month(val - 1).daysInMonth() < newdate.getDate()) {
          newdate.setDate(moment(newdate).date(1).month(val - 1).daysInMonth());
        }
        newdate.setMonth(val - 1);
        this.attr("end_date", newdate);
      } else {
        newdate = this.attr("end_date");
        if(newdate) {
          return newdate.getMonth() + 1;
        } else {
          return null;
        }
      }
    },

    // start day of week, affects start_date.
    //  Sets day of month to the first day of the
    //  month that is the selected day of the week
    //  Sunday is 0, Saturday is 6
    start_day_of_week: function(val) {
      var newdate;
      if(val) {
        val = +val;
        newdate = new Date(this.start_date || null);
        newdate.setDate((newdate.getDate() + 7 - newdate.getDay() + val - 1) % 7 + 1);
        this.attr("start_date", newdate);
      } else {
        newdate = this.attr("start_date");
        if(newdate) {
          return newdate.getDay();
        } else {
          return null;
        }
      }
    },

    // end day of week, affects end_date.
    //  Sets day of month to the first day of the
    //  month that is the selected day of the week
    //  Sunday is 0, Saturday is 6
    end_day_of_week: function(val) {
      var newdate;
      if(val) {
        val = +val;
        newdate = new Date(this.end_date || null);
        newdate.setDate((newdate.getDate() + 7 - newdate.getDay() + val - 1) % 7 + 1);
        this.attr("end_date", newdate);
      } else {
        newdate = this.attr("end_date");
        if(newdate) {
          return newdate.getDay();
        } else {
          return null;
        }
      }
    }
  });

})(window.can);
