/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, $) {
  can.Control('GGRC.Controllers.Modals', {
    BUTTON_VIEW_DONE: GGRC.mustache_path + '/modals/done_buttons.mustache',
    BUTTON_VIEW_CLOSE: GGRC.mustache_path + '/modals/close_buttons.mustache',
    BUTTON_VIEW_SAVE_CANCEL:
    GGRC.mustache_path + '/modals/save_cancel_buttons.mustache',
    BUTTON_VIEW_SAVE_CANCEL_DELETE:
    GGRC.mustache_path + '/modals/save_cancel_delete_buttons.mustache',
    BUTTON_VIEW_OK_CLOSE:
    GGRC.mustache_path + '/modals/confirm_cancel_buttons.mustache',

    defaults: {
      preload_view: GGRC.mustache_path + '/dashboard/modal_preload.mustache',
      content_view: GGRC.mustache_path + '/help/help_modal_content.mustache',
      header_view: GGRC.mustache_path + '/modals/modal_header.mustache',
      custom_attributes_view:
      GGRC.mustache_path + '/custom_attributes/modal_content.mustache',
      button_view: null,
      model: null,    // model class to use when finding or creating new
      instance: null, // model instance to use instead of finding/creating (e.g. for update)
      new_object_form: false,
      mapping: false,
      find_params: {},
      add_more: false,
      ui_array: [],
      reset_visible: false,
      extraCssClass: '',
      afterFetch: function () {},
      isSaving: false  // is there a save/map operation currently in progress
    },

    init: function () {
      this.defaults.button_view = this.BUTTON_VIEW_DONE;
    },

    confirm: function (options, success, dismiss) {
      var $target = $('<div class="modal hide ' +
                      options.extraCssClass +
                      '"></div>');
      $target
        .modal({backdrop: 'static'})
        .ggrc_controllers_modals(can.extend({
          new_object_form: false,
          button_view: GGRC.mustache_path + '/modals/confirm_buttons.mustache',
          modal_confirm: 'Confirm',
          modal_description: 'description',
          modal_title: 'Confirm',
          content_view: GGRC.mustache_path + '/modals/confirm.mustache'
        }, options))
        .on('click', 'a.btn[data-toggle=confirm]', function (e) {
          var params = $(e.target).closest('.modal').find('form')
            .serializeArray();
          $target.modal('hide').remove();
          if (success) {
            success(params, $(e.target).data('option'));
          }
        })
        .on('click.modal-form.close', '[data-dismiss="modal"]', function () {
          $target.modal('hide').remove();
          if (dismiss) {
            dismiss();
          }
        });
    }
  }, {
    init: function () {
      var currentUser;

      if (!(this.options instanceof can.Observe)) {
        this.options = new can.Observe(this.options);
      }

      if (!this.element.find('.modal-body').length) {
        can.view(this.options.preload_view, {}, this.proxy('after_preload'));
      } else {
        // Make sure that the current user object, if it exists, is fully
        // loaded before rendering the form, otherwise initial validation can
        // incorrectly fail for form fields whose values rely on current user's
        // attributes.
        if (GGRC.current_user) {
          currentUser = CMS.Models.Person.cache[GGRC.current_user.id].reify();
        }

        if (currentUser && !currentUser.email) {
          // If email - a required attribute - is missing, the user object is
          // not fully loaded and we need to force-fetch it first.
          currentUser.refresh().then(function () {
            this.after_preload();
          }.bind(this));
          return;
        }

        this.after_preload();
      }
    },

    after_preload: function (content) {
      var that = this;
      if (content) {
        this.element.html(content);
      }
      CMS.Models.DisplayPrefs.getSingleton().then(function (displayPrefs) {
        this.display_prefs = displayPrefs;

        this.options.attr('$header', this.element.find('.modal-header'));
        this.options.attr('$content', this.element.find('.modal-body'));
        this.options.attr('$footer', this.element.find('.modal-footer'));
        this.on();
        this.fetch_all()
          .then(this.proxy('apply_object_params'))
          .then(this.proxy('serialize_form'))
          .then(function () {
            // If the modal is closed early, the element no longer exists
            if (that.element) {
              that.element.trigger('preload');
            }
          })
          .then(this.proxy('autocomplete'))
          .then(function () {
            this.options.afterFetch(this.element);
          }.bind(this));
        this.restore_ui_status_from_storage();
      }.bind(this));
    },

    apply_object_params: function () {
      if (!this.options.object_params) {
        return;
      }
      this.options.object_params.each(function (value, key) {
        this.set_value({name: key, value: value});
      }, this);
    },

    'input[data-lookup] focus': function (el, ev) {
      this.autocomplete(el);
    },

    'input[data-lookup] keyup': function (el, ev) {
      // Set the transient field for validation
      var name;
      var instance;
      var value;

      // in some cases we want to disable automapping the selected item to the
      // modal's underlying object (e.g. we don't want to map the picked Persons
      // to an AssessmentTemplates object)
      if (el.data('no-automap')) {
        return;
      }

      name = el.attr('name').split('.');
      instance = this.options.instance;
      value = el.val();

      name.pop(); // set the owner to null, not the email

      if (!instance._transient) {
        instance.attr('_transient', new can.Observe({}));
      }

      can.reduce(name.slice(0, -1), function (current, next) {
        current = current + '.' + next;
        if (!instance.attr(current)) {
          instance.attr(current, new can.Observe({}));
        }
        return current;
      }, '_transient');

      if (name.length) {
        instance.attr(['_transient'].concat(name).join('.'), value);
      }
    },

    autocomplete: function (el) {
      $.cms_autocomplete.call(this, el);
    },

    autocomplete_select: function (el, event, ui) {
      var path;
      var instance;
      var index;
      var cb;
      $('#extended-info').trigger('mouseleave'); // Make sure the extra info tooltip closes

      path = el.attr('name').split('.');
      instance = this.options.instance;
      index = 0;
      path.pop(); // remove the prop
      cb = el.data('lookup-cb');

      if (cb) {
        cb = cb.split(' ');
        instance[cb[0]].apply(instance, cb.slice(1).concat([ui.item]));
        setTimeout(function () {
          el.val(ui.item.name || ui.item.email || ui.item.title, ui.item);
        }, 0);
        return;
      }

      if (/^\d+$/.test(path[path.length - 1])) {
        index = parseInt(path.pop(), 10);
        path = path.join('.');
        if (!instance.attr(path)) {
          instance.attr(path, []);
        }
        instance.attr(path).splice(index, 1, ui.item.stub());
      } else {
        path = path.join('.');
        setTimeout(function () {
          el.val(ui.item.name || ui.item.email || ui.item.title, ui.item);
        }, 0);

        instance.attr(path, null).attr(path, ui.item);
        if (!instance._transient) {
          instance.attr('_transient', can.Map());
        }
        instance.attr('_transient.' + path, ui.item);
      }
    },

    immediate_find_or_create: function (el, ev, data) {
      var that = this;
      var prop = el.data('drop');
      var model = CMS.Models[el.data('lookup')];
      var context = that.options.instance.context;
      var params = {
        context: context && context.serialize ? context.serialize() : context
      };

      setTimeout(function () {
        params[prop] = el.val();
        el.prop('disabled', true);
        model.findAll(params).then(function (list) {
          if (list.length) {
            that.autocomplete_select(el, ev, {item: list[0]});
          } else {
            new model(params).save().then(function (item) {
              that.autocomplete_select(el, ev, {item: item});
            });
          }
        })
          .always(function () {
            el.prop('disabled', false);
          });
      }, 100);
    },
    'input[data-lookup][data-drop] paste': 'immediate_find_or_create',
    'input[data-lookup][data-drop] drop': 'immediate_find_or_create',
    fetch_templates: function (dfd) {
      var that = this;
      dfd = dfd ? dfd.then(function () {
        return that.options;
      }) : $.when(this.options);
      return $.when(
        can.view(this.options.content_view, dfd),
        can.view(this.options.header_view, dfd),
        can.view(this.options.button_view, dfd),
        can.view(this.options.custom_attributes_view, dfd)
      ).done(this.proxy('draw'));
    },

    fetch_data: function (params) {
      var that = this;
      var dfd;
      var instance = this.options.attr('instance');

      params = params || this.find_params();
      params = params && params.serialize ? params.serialize() : params;

      if (this.options.skip_refresh && instance) {
        return new $.Deferred().resolve(instance);
      } else if (instance) {
        dfd = instance.refresh();
      } else if (this.options.model) {
        if (this.options.new_object_form) {
          dfd = $.when(this.options.attr(
            'instance',
            new this.options.model(params).attr('_suppress_errors', true)
          )).then(function () {
            instance = this.options.attr('instance');
          }.bind(this));
        } else {
          dfd = this.options.model.findAll(params).then(function (data) {
            if (data.length) {
              that.options.attr('instance', data[0]);
              return data[0].refresh(); // have to refresh (get ETag) to be editable.
            }
            that.options.attr('new_object_form', true);
            that.options.attr('instance', new that.options.model(params));
            return instance;
          }).done(function () {
            // Check if modal was closed
            if (that.element !== null) {
              that.on(); // listen to instance.
            }
          });
        }
      } else {
        this.options.attr('instance', new can.Observe(params));
        that.on();
        dfd = new $.Deferred().resolve(instance);
      }

      dfd.then(function () {
        if (instance &&
          _.exists(instance, 'class.is_custom_attributable') &&
          !(instance instanceof CMS.Models.Assessment)) {
          return $.when(
            instance.load_custom_attribute_definitions &&
            instance.load_custom_attribute_definitions(),
            instance.custom_attribute_values ?
              instance.refresh_all('custom_attribute_values') :
              []
          );
        }
      });

      return dfd.done(function () {
        this.reset_form(function () {
          if (instance) {
            // Make sure custom attr validations/values are reset
            if (instance.setup_custom_attributes &&
              !(instance instanceof CMS.Models.Assessment)) {
              instance.removeAttr('custom_attributes');
              instance.setup_custom_attributes();
            }
          }
        });
      }.bind(that));
    },

    reset_form: function (setFieldsCb) {
      var $textArea = $('#program_description');
      var editorData = $textArea.data('wysihtml5');

      // If the modal is closed early, the element no longer exists
      if (this.element) {
        // Do the fields (re-)setting
        if (_.isFunction(setFieldsCb)) {
          setFieldsCb();
        }
        // This is to trigger `focus_first_element` in modal_ajax handling
        this.element.trigger('loaded');
      }
      if (!this.options.instance._transient) {
        this.options.instance.attr('_transient', new can.Observe({}));
      }
      if (this.options.instance.form_preload) {
        this.options.instance.form_preload(this.options.new_object_form,
          this.options.object_params);
      }

      // The rich text editor's content is not a "normal" form field, thus
      // it needs to be reset manually (if it exists)
      if (editorData && editorData.editor) {
        editorData.editor.clear();
      }
    },

    fetch_all: function () {
      return this.fetch_templates(this.fetch_data(this.find_params()));
    },

    find_params: function () {
      var findParams = this.options.find_params;
      return findParams.serialize ? findParams.serialize() : findParams;
    },

    draw: function (content, header, footer, customAttributes) {
      var modalTitle = this.options.modal_title;
      var isObjectModal = modalTitle && (modalTitle.indexOf('Edit') === 0 ||
        modalTitle.indexOf('New') === 0);
      var $form;
      var tabList;
      var hidableTabs;
      var storableUI;
      var i;
      // Don't draw if this has been destroyed previously
      if (!this.element) {
        return;
      }
      if (can.isArray(content)) {
        content = content[0];
      }
      if (can.isArray(header)) {
        header = header[0];
      }
      if (can.isArray(footer)) {
        footer = footer[0];
      }
      if (can.isArray(customAttributes)) {
        customAttributes = customAttributes[0];
      }
      if (header != null) {
        this.options.$header.find('h2').html(header);
      }
      if (content != null) {
        this.options.$content.html(content).removeAttr('style');
      }
      if (footer != null) {
        this.options.$footer.html(footer);
      }

      if (customAttributes != null && isObjectModal) {
        this.options.$content.append(customAttributes);
      }
      this.setup_wysihtml5();

      // Update UI status array
      $form = $(this.element).find('form');
      tabList = $form.find('[tabindex]');
      hidableTabs = 0;
      for (i = 0; i < tabList.length; i++) {
        if ($(tabList[i]).attr('tabindex') > 0) {
          hidableTabs++;
        }
      }
      // ui_array index is used as the tab_order, Add extra space for skipped numbers
      storableUI = hidableTabs + 20;
      for (i = 0; i < storableUI; i++) {
        // When we start, all the ui elements are visible
        this.options.ui_array.push(0);
      }
    },

    setup_wysihtml5: function () {
      if (!this.element) {
        return;
      }
      this.element.find('.wysihtml5').each(function () {
        $(this).cms_wysihtml5();
      });
    },

    'input:not(isolate-form input), textarea:not(isolate-form textarea), select:not(isolate-form select) change':
      function (el, ev) {
        this.options.instance.removeAttr('_suppress_errors');
        // Set the value if it isn't a search field
        if (!el.hasClass('search-icon') ||
          el.is('[null-if-empty]') &&
          (!el.val() || !el.val().length)
        ) {
          this.set_value_from_element(el);
        }
      },

    'input:not([data-lookup], isolate-form *), textarea keyup':
      function (el, ev) {
        // TODO: If statement doesn't work properly. This is the right one:
        //       if (el.attr('value').length ||
        //          (typeof el.attr('value') !== 'undefined' && el.val().length)) {
        if (el.prop('value').length === 0 ||
          (typeof el.attr('value') !== 'undefined' &&
          !el.attr('value').length)) {
          this.set_value_from_element(el);
        }
      },

    /**
     * The onChange handler for the custom attribute type dropdown.
     *
     * This handler is specific to the Custom Attribute Edit modal.
     *
     * @param {jQuery} $el - the dropdown DOM element
     * @param {$.Event} ev - the event object
     */
    'dropdown[data-purpose="ca-type"] change': function ($el, ev) {
      var instance = this.options.instance;

      if (instance.attribute_type !== 'Dropdown') {
        instance.attr('multi_choice_options', undefined);
      }
    },

    serialize_form: function () {
      var $form = this.options.$content.find('form');
      var $elements = $form.find(':input:not(isolate-form *)');

      can.each($elements.toArray(), this.proxy('set_value_from_element'));
    },
    set_value_from_element: function (el) {
      var name;
      var value;
      var cb;
      var instance = this.options.instance;
      el = el instanceof jQuery ? el : $(el);
      name = el.attr('name');
      value = el.val();
      cb = el.data('lookup-cb');

      // If no model is specified, short circuit setting values
      // Used to support ad-hoc form elements in confirmation dialogs
      if (!this.options.model) {
        return;
      }
      // if data was populated in a callback, use that data from the instance
      // except if we are editing an instance and some fields are already populated
      if (!_.isUndefined(el.attr('data-populated-in-callback')) &&
        value === '') {
        if (!_.isUndefined(instance[name])) {
          if (typeof instance[name] === 'object' && instance[name] !== null) {
            this.set_value({name: name, value: instance[name].id});
          } else {
            this.set_value({name: name, value: instance[name]});
          }
          return;
        }
      }
      if (cb) {
        cb = cb.split(' ');
        instance[cb[0]].apply(instance, cb.slice(1).concat([value]));
      } else if (name) {
        this.set_value({name: name, value: value});
      }
      if (el.is('[data-also-set]')) {
        can.each(el.data('also-set').split(','), function (oname) {
          this.set_value({name: oname, value: value});
        }, this);
      }
    },
    set_value: function (item) {
      var instance = this.options.instance;
      var name = item.name.split('.');
      var $elem;
      var value;
      var model;
      var $other;
      var listPath;
      var cur;

      // Don't set `_wysihtml5_mode` on the instances
      if (item.name === '_wysihtml5_mode') {
        return;
      }

      if (!(instance instanceof this.options.model)) {
        instance = this.options.instance =
          new this.options.model(instance && instance.serialize ?
            instance.serialize() : instance);
      }
      $elem = this.options.$content
        .find("[name='" + item.name + "']:not(isolate-form *)");
      model = $elem.attr('model');

      if (model) {
        if (item.value instanceof Array) {
          value = can.map(item.value, function (id) {
            return CMS.Models.get_instance(model, id);
          });
        } else if (item.value instanceof Object) {
          value = CMS.Models.get_instance(model, item.value.id);
        } else {
          value = CMS.Models.get_instance(model, item.value);
        }
      } else if ($elem.is('[type=checkbox]')) {
        value = $elem.is(':checked');
      } else {
        value = item.value;
      }

      if ($elem.is('[null-if-empty]') && (!value || !value.length)) {
        value = null;
      }

      if ($elem.is('[data-binding]') && $elem.is('[type=checkbox]')) {
        can.map($elem, function (el) {
          if (el.value !== value.id) {
            return;
          }
          if ($(el).is(':checked')) {
            instance.mark_for_addition($elem.data('binding'), value);
          } else {
            instance.mark_for_deletion($elem.data('binding'), value);
          }
        });
        return;
      } else if ($elem.is('[data-binding]')) {
        can.each(can.makeArray($elem[0].options), function (opt) {
          instance.mark_for_deletion(
            $elem.data('binding'),
            CMS.Models.get_instance(model, opt.value));
        });
        if (value.push) {
          can.each(value, $.proxy(
            instance,
            'mark_for_addition',
            $elem.data('binding')));
        } else {
          instance.mark_for_addition($elem.data('binding'), value);
        }
      }

      if (name.length > 1) {
        if (can.isArray(value)) {
          value = new can.Observe.List(can.map(value, function (v) {
            return new can.Observe({}).attr(name.slice(1).join('.'), v);
          }));
        } else if ($elem.is('[data-lookup]')) {
          if (!value) {
            value = null;
          } else {
            // Setting a "lookup field is handled in the autocomplete() method"
            return;
          }
        } else if (name[name.length - 1] === 'date') {
          name.pop(); // date is a pseudoproperty of datetime objects
          if (!value) {
            value = null;
          } else {
            value = this.options.model.convert.date(value);
            $other = this.options.$content
              .find("[name='" + name.join('.') + ".time']:not(isolate-form *)");
            if ($other.length) {
              value = moment(value).add(parseInt($other.val(), 10)).toDate();
            }
          }
        } else if (name[name.length - 1] === 'time') {
          name.pop(); // time is a pseudoproperty of datetime objects
          value = moment(this.options.instance.attr(name.join('.')))
            .startOf('day').add(parseInt(value, 10)).toDate();
        } else {
          value = new can.Observe({}).attr(name.slice(1).join('.'), value);
        }
      }

      value = value && value.serialize ? value.serialize() : value;
      if ($elem.is('[data-list]')) {
        listPath = name.slice(0, name.length - 1).join('.');
        cur = instance.attr(listPath);
        if (!cur || !(cur instanceof can.Observe.List)) {
          instance.attr(listPath, []);
          cur = instance.attr(listPath);
        }
        value = value || [];
        cur.splice.apply(cur, [0, cur.length].concat(value));
      } else if (name[0] === 'custom_attributes') {
        instance.custom_attributes.attr(name[1], value[name[1]]);
      } else if (name[0] !== 'people') {
        instance.attr(name[0], value);
      }
      this.setup_wysihtml5(); // in case the changes in values caused a new wysi box to appear.
    },
    '[data-before], [data-after] change': function (el, ev) {
      var date;
      var data;
      var options;
      if (!el.data('datepicker')) {
        el.datepicker({changeMonth: true, changeYear: true});
      }
      date = el.datepicker('getDate');
      data = el.data();
      options = {
        before: 'maxDate',
        after: 'minDate'
      };

      _.each(options, function (val, key) {
        var targetEl;
        var isInput;
        var targetDate;
        var otherKey;
        if (!data[key]) {
          return;
        }
        targetEl = this.element.find('[name=' + data[key] + ']');
        isInput = targetEl.is('input');
        targetDate = isInput ? targetEl.val() : targetEl.text();

        el.datepicker('option', val, targetDate);
        if (targetEl) {
          otherKey = key === 'before' ? 'after' : 'before';
          targetEl.datepicker('option', options[otherKey], date);
        }
      }, this);
    },

    "{$footer} a.btn[data-toggle='modal-submit-addmore'] click":
      function (el, ev) {
        if (el.hasClass('disabled')) {
          return;
        }
        this.options.attr('add_more', true);
        this.save_ui_status();
        this.triggerSave(el, ev);
      },

    "{$footer} a.btn[data-toggle='modal-submit'] click": function (el, ev) {
      if (el.hasClass('disabled')) {
        return;
      }
      this.options.attr('add_more', false);
      this.triggerSave(el, ev);
    },

    '{$content} a.field-hide click': function (el, ev) { // field hide
      var $el = $(el);
      var $hidable = $el.closest('[class*="span"].hidable');
      var $showButton = $(this.element).find('#formRestore');
      var $hideButton = $(this.element).find('#formHide');
      var totalInner = $el.closest('.hide-wrap.hidable')
        .find('.inner-hide').length;
      var totalHidden;
      var uiUnit;
      var i;
      var tabValue;

      $el.closest('.inner-hide').addClass('inner-hidable');
      totalHidden = $el.closest('.hide-wrap.hidable')
        .find('.inner-hidable').length;
      // $hidable.hide();
      $hidable.addClass('hidden');
      this.options.reset_visible = true;
      // update ui array
      uiUnit = $hidable.find('[tabindex]');
      for (i = 0; i < uiUnit.length; i++) {
        tabValue = $(uiUnit[i]).attr('tabindex');
        if (tabValue > 0) {
          this.options.ui_array[tabValue - 1] = 1;
          $(uiUnit[i]).attr('tabindex', '-1');
          $(uiUnit[i]).attr('uiindex', tabValue);
        }
      }

      if (totalInner === totalHidden) {
        $el.closest('.inner-hide').parent('.hidable').addClass('hidden');
      }

      $hideButton.hide();
      $showButton.show();
      return false;
    },

    '{$content} #formHide click': function (el, ev) {
      var i;
      var uiArrLength = this.options.ui_array.length;
      var $showButton = this.element.find('#formRestore');
      var $hidables = this.element.find('.hidable');
      var hiddenElements = $hidables.find('[tabindex]');
      var $hiddenElement;
      var tabValue;
      for (i = 0; i < uiArrLength; i++) {
        this.options.ui_array[i] = 0;
      }

      this.options.reset_visible = true;

      $hidables.addClass('hidden');
      this.element.find('.inner-hide').addClass('inner-hidable');

      // Set up the hidden elements index to 1
      for (i = 0; i < hiddenElements.length; i++) {
        $hiddenElement = $(hiddenElements[i]);
        tabValue = $hiddenElement.attr('tabindex');
        // The UI array index start from 0, and tab-index/io-index is from 1
        if (tabValue > 0) {
          this.options.ui_array[tabValue - 1] = 1;
          $hiddenElement.attr({
            tabindex: '-1',
            uiindex: tabValue
          });
        }
      }

      el.hide();
      $showButton.show();
      return false;
    },

    '{$content} #formRestore click': function (el, ev) {
      // Update UI status array to initial state
      var i;
      var uiArrLength = this.options.ui_array.length;
      var $form = this.element.find('form');
      var $body = $form.closest('.modal-body');
      var uiElements = $body.find('[uiindex]');
      var $hideButton = this.element.find('#formHide');
      var $el;
      var tabVal;

      for (i = 0; i < uiArrLength; i++) {
        this.options.ui_array[i] = 0;
      }

      // Set up the correct tab index for tabbing
      // Get all the ui elements with 'uiindex' set to original tabindex
      // Restore the original tab index

      for (i = 0; i < uiElements.length; i++) {
        $el = $(uiElements[i]);
        tabVal = $el.attr('uiindex');
        $el.attr('tabindex', tabVal);
      }

      this.options.reset_visible = false;
      this.element.find('.hidden').removeClass('hidden');
      this.element.find('.inner-hide').removeClass('inner-hidable');
      el.hide();
      $hideButton.show();
      return false;
    },

    save_ui_status: function () {
      var modelName;
      var resetVisible;
      var uiArray;
      var displayState;
      if (!this.options.model) {
        return;
      }
      modelName = this.options.model.model_singular;
      resetVisible = this.options.reset_visible ?
        this.options.reset_visible : false;
      uiArray = this.options.ui_array ? this.options.ui_array : [];
      displayState = {
        reset_visible: resetVisible,
        ui_array: uiArray
      };

      this.display_prefs.setModalState(modelName, displayState);
      this.display_prefs.save();
    },

    restore_ui_status_from_storage: function () {
      var modelName;
      var displayState;
      if (!this.options.model) {
        return;
      }
      modelName = this.options.model.model_singular;
      displayState = this.display_prefs.getModalState(modelName);

      // set up reset_visible and ui_array
      if (displayState !== null) {
        if (displayState.reset_visible) {
          this.options.reset_visible = displayState.reset_visible;
        }
        if (displayState.ui_array) {
          this.options.ui_array = displayState.ui_array;
        }
      }
      this.restore_ui_status();
    },

    restore_ui_status: function () {
      var $selected;
      var str;
      var tabindex;
      var i;
      var $form;
      var $body;
      var $hideButton;
      var $showButton;
      // walk through the ui_array, for the one values,
      // select the element with tab index and hide it

      if (this.options.reset_visible) {// some elements are hidden
        $form = this.element.find('form');
        $body = $form.closest('.modal-body');
        $hideButton = $form.find('#formHide');
        $showButton = $form.find('#formRestore');

        for (i = 0; i < this.options.ui_array.length; i++) {
          if (this.options.ui_array[i] == 1) {
            tabindex = i + 1;
            str = '[tabindex=' + tabindex + ']';
            $selected = $body.find(str);

            if ($selected) {
              $selected.closest('.hidable').addClass('hidden');
              $selected.attr({
                uiindex: tabindex,
                tabindex: '-1'
              });
            }
          }
        }

        $hideButton.hide();
        $showButton.show();

        return false;
      }
    },

    // make buttons non-clickable when saving, make it disable afterwards
    bindXHRToButton_disable: function (xhr, el, newtext, disable) {
      // binding of an ajax to a click is something we do manually
      var $el = $(el);
      var oldtext = $el.text();

      if (newtext) {
        $el[0].innerHTML = newtext;
      }
      $el.addClass('disabled pending-ajax');
      if (disable !== false) {
        $el.attr('disabled', true);
      }
      xhr.fail(function () {
        if ($el.length) {
          $el.removeClass('disabled');
        }
      }).always(function () {
        // If .text(str) is used instead of innerHTML, the click event may not fire depending on timing
        if ($el.length) {
          $el.removeAttr('disabled')
            .removeClass('pending-ajax')[0].innerHTML = oldtext;
        }
      });
    },
    // make buttons non-clickable when saving
    bindXHRToBackdrop: function (xhr, el, newtext, disable) {
      // binding of an ajax to a click is something we do manually
      var $el = $(el);

      $el.addClass('disabled pending-ajax');
      if (disable !== false) {
        $el.attr('disabled', true);
      }
      xhr.always(function () {
        // If .text(str) is used instead of innerHTML, the click event may not fire depending on timing
        $el.removeAttr('disabled').removeClass('disabled pending-ajax');// [0].innerHTML = oldtext;
      });
    },

    triggerSave: function (el, ev) {
      var ajd;
      var saveCloseBtn = this.element.find('a.btn[data-toggle=modal-submit]');
      var saveAddmoreBtn = this.element.find(
        'a.btn[data-toggle=modal-submit-addmore]');
      var modalBackdrop = this.element.data('modal_form').$backdrop;

      // Normal saving process
      if (el.is(':not(.disabled)')) {
        ajd = this.save_instance(el, ev);

        if (!ajd) {
          return;
        }

        this.options.attr('isSaving', true);

        ajd.always(function () {
          this.options.attr('isSaving', false);
        }.bind(this));

        if (this.options.add_more) {
          this.bindXHRToButton_disable(ajd, saveCloseBtn);
          this.bindXHRToButton_disable(ajd, saveAddmoreBtn);
          this.bindXHRToBackdrop(ajd, modalBackdrop, 'Saving, please wait...');
        } else {
          this.bindXHRToButton(ajd, saveCloseBtn, 'Saving, please wait...');
          this.bindXHRToButton(ajd, saveAddmoreBtn);
        }
      } else if (this._email_check) {
        // Queue a save if clicked after verifying the email address
        this._email_check.done(function (data) {
          if (!_.isNull(data.length) && !_.isUndefined(data.length)) {
            data = data[0];
          }
          if (data) {
            setTimeout(function () {
              delete this._email_check;
              el.trigger('click');
            }.bind(this), 0);
          }
        });
      }
    },

    new_instance: function (data) {
      var newInstance = this.prepareInstance();

      this.resetCAFields(newInstance.attr('custom_attribute_definitions'));

      $.when(this.options.attr('instance', newInstance))
        .done(function () {
          this.reset_form(function () {
            var $form = $(this.element).find('form');
            $form.trigger('reset');
          });
        }.bind(this))
        .then(this.proxy('apply_object_params'))
        .then(this.proxy('serialize_form'))
        .then(this.proxy('autocomplete'));

      this.restore_ui_status();
    },

    /**
     * Reset custom attribute values manually
     * @param {Array} cad - Array with custom attribute definitions
     */
    resetCAFields: function (cad) {
      var wysihtml5;

      can.each(cad, function (definition) {
        var element = this.element
          .find('[name="custom_attributes.' + definition.id + '"]');
        if (definition.attribute_type === 'Checkbox') {
          element.attr('checked', false);
        } else if (definition.attribute_type === 'Rich Text') {
          // Check that wysihtml5 is still alive, otherwise just clean textarea
          wysihtml5 = element.data('wysihtml5');
          if (wysihtml5) {
            wysihtml5.editor.clear();
          } else {
            element.val('');
          }
        } else if (definition.attribute_type === 'Map:Person') {
          element = this.element.find('[name="_custom_attribute_mappings.' +
            definition.id + '.email"]');
          element.val('');
        } else {
          element.val('');
        }
      }, this);
    },

    prepareInstance: function () {
      var params = this.find_params();
      var instance = new this.options.model(params);
      var saveContactModels = ['TaskGroup', 'TaskGroupTask'];

      instance.attr('_suppress_errors', true)
        .attr('custom_attribute_definitions',
          this.options.instance.custom_attribute_definitions)
        .attr('custom_attributes', new can.Map());

      if (this.options.add_more &&
        _.includes(saveContactModels, this.options.model.shortName)) {
        instance.attr('contact', this.options.attr('instance.contact'));
      }

      return instance;
    },

    save_instance: function (el, ev) {
      var that = this;
      var instance = this.options.instance;
      var ajd;
      var instanceId = instance.id;
      var params;
      var type;
      var name;
      var msg;

      if (instance.errors()) {
        instance.removeAttr('_suppress_errors');
        return;
      }

      this.serialize_form();

      // Special case to handle context outside the form itself
      // - this avoids duplicated change events, and the API requires
      //   `context` to be present even if `null`, unlike other attributes
      if (!instance.context) {
        instance.attr('context', {id: null});
      }

      this.disable_hide = true;

      ajd = instance.save();
      ajd.fail(this.save_error.bind(this))
        .done(function (obj) {
          function finish() {
            delete that.disable_hide;
            if (that.options.add_more) {
              if (that.options.$trigger && that.options.$trigger.length) {
                that.options.$trigger.trigger('modal:added', [obj]);
              }
              that.new_instance();
            } else {
              that.element.trigger('modal:success', [
                obj,
                {
                  map_and_save: $('#map-and-save').is(':checked')
                }
              ]).modal_form('hide');
              that.update_hash_fragment();
            }
          }

          // If this was an Objective created directly from a Section, create a join
          params = that.options.object_params;
          if (obj instanceof CMS.Models.Objective &&
            params && params.section) {
            new CMS.Models.Relationship({
              source: obj,
              destination: CMS.Models.Section
                .findInCacheById(params.section.id),
              context: {id: null}
            }).save()
              .fail(that.save_error.bind(that))
              .done(function () {
                $(document.body).trigger('ajax:flash',
                  {success: 'Objective mapped successfully.'});
                finish();
              });
          } else {
            type = obj.type ? can.spaceCamelCase(obj.type) : '';
            name = obj.title ? obj.title : '';

            if (instanceId === undefined) { // new element
              if (obj.is_declining_review && obj.is_declining_review == '1') {
                msg = 'Review declined';
              } else if (name) {
                msg = 'New ' + type + ' ' + name + ' added successfully.';
              } else {
                msg = 'New ' + type + ' added successfully.';
              }
            } else {
              msg = name + ' modified successfully.';
            }
            $(document.body).trigger('ajax:flash', {success: msg});
            finish();
          }
        });
      this.save_ui_status();
      return ajd;
    },

    save_error: function (_, error) {
      $('html, body').animate({
        scrollTop: '0px'
      }, {
        duration: 200,
        complete: function () {
          if (error) {
            GGRC.Errors.notifier('error', error.responseText);
          }
          delete this.disable_hide;
        }.bind(this)
      });
    },

    '{instance} destroyed': ' hide',

    ' hide': function (el, ev) {
      var cad;
      if (this.disable_hide) {
        ev.stopImmediatePropagation();
        ev.stopPropagation();
        ev.preventDefault();
        return false;
      }
      if (this.options.instance instanceof can.Model &&
        // Ensure that this modal was hidden and not a child modal
        this.element && ev.target === this.element[0] &&
        !this.options.skip_refresh && !this.options.instance.isNew()) {
        if (this.options.instance.type === 'AssessmentTemplate') {
          cad = this.options.instance.attr('custom_attribute_definitions');
          cad = _.filter(cad, function (attr) {
            return attr.id;
          });
          this.options.instance.attr('custom_attribute_definitions', cad);
        }
        this.options.instance.refresh();
      }
    },

    destroy: function () {
      if (this.options.model && this.options.model.cache) {
        delete this.options.model.cache[undefined];
      }
      if (this._super) {
        this._super.apply(this, arguments);
      }
      if (this.options.instance && this.options.instance._transient) {
        this.options.instance.removeAttr('_transient');
      }
    },

    should_update_hash_fragment: function () {
      var $trigger = this.options.$trigger;

      if (!$trigger) {
        return false;
      }
      return !$trigger.closest('.modal, .cms_controllers_info_pin').length;
    },

    update_hash_fragment: function () {
      var hash;
      var treeController;
      if (!this.should_update_hash_fragment()) {
        return;
      }

      if (this.options.instance.getHashFragment) {
        hash = this.options.instance.getHashFragment();
        if (hash) {
          window.location.hash = hash;
          return;
        }
      }

      hash = window.location.hash.split('/')[0];
      treeController = this.options
        .$trigger
        .closest('.cms_controllers_tree_view_node')
        .control();

      hash += [treeController ? treeController.hash_fragment() : '',
        this.options.instance.hash_fragment()].join('/');

      hash = this.updateSummaryHash(hash, this.options.instance.type);
      window.location.hash = hash;
    },

    updateSummaryHash: function (hash, type) {
      var summary = 'Summary';
      var replacements = {
        Assessment: 'assessment'
      };
      var replacement = replacements[type];
      return replacement && hash.indexOf(summary) > 0 ?
        hash.replace(summary, replacement) :
        hash;
    }
  });
})(window.can, window.can.$);
