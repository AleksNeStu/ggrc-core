/*!
    Copyright (C) 2017 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

(function (can, GGRC, moment) {
  'use strict';

  GGRC.Components('datepicker', {
    tag: 'datepicker',
    template: can.view(
      GGRC.mustache_path +
      '/components/datepicker/datepicker.mustache'
    ),
    scope: {
      date: null,
      format: '@',
      helptext: '@',
      setMinDate: null,
      setMaxDate: null,
      _date: null,  // the internal value of the text input field
      define: {
        required: {
          type: 'boolean',
          'default': false
        },
        label: {
          type: 'string'
        },
        persistent: {
          type: 'boolean',
          'default': false
        },
        isShown: {
          type: 'boolean',
          'default': false
        }
      },
      onSelect: function (val, ev) {
        this.attr('date', val);
        this.attr('isShown', false);
      },
      onFocus: function (el, ev) {
        this.attr('showTop', false);
        this.attr('isShown', true);

        if (!GGRC.Utils.inViewport(this.picker)) {
          this.attr('showTop', true);
        }
      },

      // Date formats for the actual selected value, and for the date as
      // displayed to the user. The Moment.js library and the jQuery datepicker
      // use different format notation, thus separate settings for each.
      // IMPORTANT: The pair of settings for each "type" of value (i.e. actual
      // value / display value) must be consistent across both libraries!
      MOMENT_ISO_DATE: 'YYYY-MM-DD',
      MOMENT_DISPLAY_FMT: 'MM/DD/YYYY',
      PICKER_ISO_DATE: 'yy-mm-dd',
      PICKER_DISPLAY_FMT: 'mm/dd/yy'
    },

    events: {
      inserted: function () {
        var scope = this.scope;
        var element = this.element.find('.datepicker__calendar');
        var minDate;
        var maxDate;
        var date;

        element.datepicker({
          dateFormat: scope.PICKER_ISO_DATE,
          altField: this.element.find('.datepicker__input'),
          altFormat: scope.PICKER_DISPLAY_FMT,
          onSelect: this.scope.onSelect.bind(this.scope)
        });
        scope.attr('picker', element);

        date = this.getDate(scope.date);
        scope.picker.datepicker('setDate', date);

        // set the boundaries of the dates that user is allowed to select
        minDate = this.getDate(scope.setMinDate);
        maxDate = this.getDate(scope.setMaxDate);
        scope.attr('setMinDate', minDate);
        scope.attr('setMaxDate', maxDate);

        if (scope.setMinDate) {
          this.updateDate('minDate', scope.setMinDate);
        }
        if (scope.setMaxDate) {
          this.updateDate('maxDate', scope.setMaxDate);
        }
      },

      /**
       * Convert given date to an ISO date string.
       *
       * @param {Date|string|null} date - the date to convert
       * @return {string|null} - date in ISO format or null if empty or invalid
       */
      getDate: function (date) {
        var scope = this.scope;

        if (date instanceof Date) {
          // NOTE: Not using moment.utc(), because if a Date instance is given,
          // it is in the browser's local timezone, thus we need to take that
          // into account to not end up with a different date. Ideally this
          // should never happen, but that would require refactoring the way
          // Date objects are created throughout the app.
          return moment(date).format(scope.MOMENT_ISO_DATE);
        } else if (this.isValidDate(date)) {
          return date;
        }

        return null;
      },

      isValidDate: function (date) {
        var scope = this.scope;
        return moment(date, scope.MOMENT_ISO_DATE, true).isValid();
      },

      /**
       * Change the min/max date allowed to be picked.
       *
       * @param {string} type - the setting to change ("minDate" or "maxDate").
       *   The value given is automatically adjusted for a day as business
       *   rules dictate.
       * @param {Date|string|null} date - the new value of the `type` setting.
       *   If given as string, it must be in ISO date format.
       * @return {Date|null} - the new date value
       */
      updateDate: function (type, date) {
        var scope = this.scope;

        var types = {
          minDate: function () {
            date.add(1, 'day');
          },
          maxDate: function () {
            date.subtract(1, 'day');
          }
        };

        if (!date) {
          scope.picker.datepicker('option', type, null);
          return null;
        }

        if (date instanceof Date) {
          // NOTE: Not using moment.utc(), because if a Date instance is given,
          // it is in the browser's local timezone, thus we need to take that
          // into account to not end up with a different date. Ideally this
          // should never happen, but that would require refactoring the way
          // Date objects are created throughout the app.
          date = moment(date).format(scope.MOMENT_ISO_DATE);
        }
        date = moment.utc(date);

        if (types[type]) {
          types[type]();
        }
        date = date.toDate();
        scope.picker.datepicker('option', type, date);
        return date;
      },

      /**
       * Prepeare date to ISO format.
       *
       * @param {Object} scope - scope of the Component
       * @param {string|null} val - the new value of the date setting.
       *   If given as string, it must be in ISO date format.
       * @return {string|null} - the new date value
       */
      prepareDate: function (scope, val) {
        var valISO = null;
        var valF = null;

        if (val) {
          val = val.trim();
          valF = moment.utc(val, scope.MOMENT_DISPLAY_FMT, true);
          valISO = valF.isValid() ? valF.format(scope.MOMENT_ISO_DATE) : null;
        }
        return valISO;
      },

      '{scope} setMinDate': function (scope, ev, date) {
        var currentDateObj = null;
        var updated = this.updateDate('minDate', date);

        if (scope.date) {
          currentDateObj = moment.utc(scope.date).toDate();
          if (currentDateObj < updated) {
            this.scope.attr(
              '_date',
              moment.utc(updated).format(scope.MOMENT_DISPLAY_FMT));
          }
        }
      },

      '{scope} setMaxDate': function (scope, ev, date) {
        this.updateDate('maxDate', date);
      },

      '{scope} _date': function (scope, ev, val) {
        var valISO = this.prepareDate(scope, val);
        scope.attr('date', valISO);
        scope.picker.datepicker('setDate', valISO);
      },

      '{window} mousedown': function (el, ev) {
        var isInside;

        if (this.scope.attr('persistent')) {
          return;
        }
        isInside = GGRC.Utils.events.isInnerClick(this.element, ev.target);

        if (this.scope.isShown && !isInside) {
          this.scope.attr('isShown', false);
        }
      }
    },
    helpers: {
      isHidden: function (opts) {
        if (this.attr('isShown') || this.attr('persistent')) {
          return opts.inverse();
        }
        return opts.fn();
      }
    }
  });
})(window.can, window.GGRC, window.moment);
