/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

can.Control('GGRC.Controllers.TreeFilter', {}, {
  init: function () {
    var filterExpression;
    var queryParams;  // just a parsed query string
    var queryString;
    var parentControl;

    if (this._super) {
      this._super.apply(this, arguments);
    }
    this.options.states = new can.Observe();
    parentControl = this.element.closest('.cms_controllers_dashboard_widgets')
      .find('.cms_controllers_tree_view').control();
    if (parentControl) {
      parentControl.options.attr('states', this.options.states);
    }

    this.$txtFilter = this.element.find('input[name=filter_query]');

    // determine the tree view filter and automatically apply it if it exists
    queryString = location.search.substr(1);  // remove the '?' prefix
    queryParams = can.route.deparam(queryString);
    filterExpression = queryParams.filter || '';

    if (filterExpression) {
      this.$txtFilter.val(filterExpression);

      // This is needed (?) for the old filter code, because setting the
      // input's value here does not fire the change event... but we should
      // delete this once we get rid of that legacy filter code.
      this.options.states.attr('filter_query', filterExpression);

      // NOTE: We must wait for the parent tree view controller (that does the
      // actual filtering heavy lifting) and it's DOM element to be present and
      // initialized. We should probably use some other event than window load,
      // but could not find a better candidate...
      $(window).on('load', function () {
        this.apply_filter(filterExpression);
      }.bind(this));
    }

    this.on();
  },
  toggle_indicator: function (currentFilter) {
    var isExpression =
      !!currentFilter && !!currentFilter.expression.op &&
      currentFilter.expression.op.name !== 'text_search' &&
      currentFilter.expression.op.name !== 'exclude_text_search';

    this.element.find('.tree-filter__expression-holder')
      .toggleClass('tree-filter__expression-holder--active', isExpression);
    this.element.find('.tree-filter__expression-holder span i')
      .toggleClass('fa-check-circle green', isExpression);
    this.element.find('.tree-filter__expression-holder span i')
      .toggleClass('fa-check-circle-o', !isExpression);
  },
  apply_filter: function (filterString) {
    var currentFilter = GGRC.query_parser.parse(filterString);
    var parentControl = this.element
      .closest('.cms_controllers_dashboard_widgets')
      .find('.cms_controllers_tree_view').control();

    this.toggle_indicator(currentFilter);
    parentControl.filter(filterString);
  },
  'input[type=reset] click': function (el, ev) {
    this.element.find('input[type=text]').val('');
    this.apply_filter('');
  },
  'input[type=submit] click': function (el, ev) {
    this.apply_filter(this.$txtFilter.val());
  },
  'input[type=checkbox] click': function (el, ev) {
    this.apply_filter(this.$txtFilter.val());
  },
  'input keyup': function (el, ev) {
    this.toggle_indicator(GGRC.query_parser.parse(el.val()));

    if (ev.keyCode === 13) {
      this.apply_filter(el.val());
    }
    ev.stopPropagation();
  },
  'input, select change': function (el, ev) {
    // this is left from the old filters and should eventually be replaced
    // Convert '.' to '__' ('.' will cause can.Observe to try to update a path instead of just a key)
    var name = el.attr('name').replace(/\./g, '__');
    if (el.is('.hasDatepicker')) {
      this.options.states.attr(name, moment(el.val(), 'MM/DD/YYYY'));
    } else if (el.is(':checkbox') && !el.is(':checked')) {
      this.options.states.removeAttr(name);
    } else {
      this.options.states.attr(name, el.val());
    }
    ev.stopPropagation();
  },
  'input[data-lookup] focus': function (el, ev) {
    this.autocomplete(el);
  },
  autocomplete: function (el) {
    $.cms_autocomplete.call(this, el);
  },
  autocomplete_select: function (el, event, ui) {
    setTimeout(function () {
      if (ui.item.title) {
        el.val(ui.item.title, ui.item);
      } else {
        el.val(ui.item.name ? ui.item.name : ui.item.email, ui.item);
      }
      el.trigger('change');
    }, 0);
  },
  '{states} change': function (states) {
    var that = this;
    this.element
      .closest('.tree-structure')
      .children(':has(> [data-model],:data(model))').each(function (i, el) {
        var model = $(el).children('[data-model],:data(model)').data('model');
        if (can.reduce(Object.keys(states._data), function (st, key) {
          var result;
          var val = states[key];
          var test = that.resolve_object(model, key.replace(/__/g, '.'));

          if (val && val.isAfter) {
            if (!test || moment(test).isBefore(val)) {
              result = false;
            } else {
              result = st;
            }
          } else if (val === '[empty]' && test === '') {
            result = st;
          } else if (val &&
            (!test || !~test.toUpperCase().indexOf(val.toUpperCase()))) {
            result = false;
          } else {
            result = st;
          }
          return result;
        }, true)) {
          $(el).show();
        } else {
          $(el).hide();
        }
      });
  },
  '[data-toggle="filter-reset"] click': function (el, ev) {
    var that = this;
    var filterResetTarget = 'input, select';
    var checked;

    this.element.find(filterResetTarget).each(function (i, elem) {
      var $elem = $(elem)
        ;

      that.options.states.removeAttr($elem.attr('name').replace(/\./g, '__'));
    });

    if (el.is(':checkbox')) {
      checked = el.prop('checked');
      // Manually reset the form
      el.closest('form')[0].reset();
      if (el.is(':checkbox')) {
        // But not the checkbox
        el.prop('checked', checked);
      }
    }
    can.trigger(this.options.states, 'change', '*');
  },
  resolve_object: function (obj, path) {
    path = path.split('.');
    can.each(path, function (prop) {
      // If the name is blank, use email
      if (prop === 'name' && obj.attr &&
        (!obj.attr(prop) || !obj.attr(prop).trim()) &&
        obj.attr('email') && obj.attr('email').trim()) {
        prop = 'email';
      }
      if (obj.instance) {
        obj = obj.instance;
      }
      obj = obj.attr ? obj.attr(prop) : obj.prop;
      obj = obj && obj.reify ? obj.reify() : obj;
      return !_.isEmpty(obj); // stop iterating in case of null/undefined.
    });
    return obj;
  }
});
