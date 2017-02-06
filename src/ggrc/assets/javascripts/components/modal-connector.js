/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, $) {
  /*
   Below this line we're defining a can.Component, which is in this file
   because it works in tandem with the modals form controller.

   The purpose of this component is to allow for pending adds/removes of connected
   objects while the modal is visible.  On save, the actual pending actions will
   be resolved and we won't worry about the transient state we use anymore.
   */
  can.Component.extend({
    tag: 'ggrc-modal-connector',
    // <content> in a component template will be replaced with whatever is contained
    //  within the component tag.  Since the views for the original uses of these components
    //  were already created with content, we just used <content> instead of making
    //  new view template files.
    template: '<isolate-form><content/></isolate-form>',
    scope: {
      parent_instance: null,
      instance: null,
      instance_attr: '@',
      source_mapping: '@',
      source_mapping_source: '@',
      default_mappings: [], // expects array of objects
      mapping: '@',
      deferred: '@',
      attributes: {},
      list: [],
      // the following are just for the case when we have no object to start with,
      changes: []
    },
    events: {
      init: function () {
        var that = this;
        var key;
        this.scope.attr('controller', this);
        if (!this.scope.instance) {
          this.scope.attr('deferred', true);
        } else if (this.scope.instance.reify) {
          this.scope.attr('instance', this.scope.instance.reify());
        }

        this.scope.default_mappings.forEach(function (defaultMapping) {
          var model;
          var objectToAdd;
          if (defaultMapping.id && defaultMapping.type) {
            model = CMS.Models[defaultMapping.type];
            objectToAdd = model.findInCacheById(defaultMapping.id);
            that.scope.instance
              .mark_for_addition('related_objects_as_source', objectToAdd, {});
            that.scope.list.push(objectToAdd);
          }
        });

        if (!this.scope.source_mapping) {
          this.scope.attr('source_mapping', this.scope.mapping);
        }
        if (!this.scope.source_mapping_source) {
          this.scope.source_mapping_source = 'instance';
        }
        if (this.scope[this.scope.source_mapping_source]) {
          this.scope[this.scope.source_mapping_source]
            .get_binding(this.scope.source_mapping)
            .refresh_instances()
            .then(function (list) {
              var currentList = this.scope.attr('list');
              this.scope.attr('list', currentList.concat(can.map(list,
                function (binding) {
                  return binding.instance;
                })));
            }.bind(this));
          // this.scope.instance.attr("_transient." + this.scope.mapping, this.scope.list);
        } else {
          key = this.scope.instance_attr + '_' +
            (this.scope.mapping || this.scope.source_mapping);
          if (!this.scope.parent_instance._transient[key]) {
            this.scope.attr('list', []);
            this.scope.parent_instance.attr('_transient.' + key,
              this.scope.list);
          } else {
            this.scope.attr('list', this.scope.parent_instance._transient[key]);
          }
        }

        this.options.parent_instance = this.scope.parent_instance;
        this.options.instance = this.scope.instance;
        this.on();
      },
      '{scope} list': function () {
        var person;
        // Workaround so we render pre-defined users.
        if (~['owners'].indexOf(this.scope.mapping) &&
          this.scope.list && !this.scope.list.length) {
          person = CMS.Models.Person.findInCacheById(GGRC.current_user.id);
          this.scope.instance
            .mark_for_addition(this.scope.mapping, person, {});
          this.scope.list.push(person);
        }
      },
      deferred_update: function () {
        var changes = this.scope.changes;
        var instance = this.scope.instance;

        if (!changes.length) {
          if (instance && instance._pending_joins &&
            instance._pending_joins.length) {
            instance.delay_resolving_save_until(instance.constructor
              .resolve_deferred_bindings(instance));
          }
          return;
        }
        this.scope.attr('instance', this.scope.attr('parent_instance')
          .attr(this.scope.instance_attr).reify());
        // Add pending operations
        can.each(changes, function (item) {
          var mapping = this.scope.mapping ||
              GGRC.Mappings.get_canonical_mapping_name(
                this.scope.instance.constructor.shortName,
                item.what.constructor.shortName);
          if (item.how === 'add') {
            this.scope.instance
              .mark_for_addition(mapping, item.what, item.extra);
          } else {
            this.scope.instance.mark_for_deletion(mapping, item.what);
          }
        }.bind(this)
        );
        this.scope.instance
          .delay_resolving_save_until(
            this.scope.instance.constructor
              .resolve_deferred_bindings(this.scope.instance));
      },
      '{parent_instance} updated': 'deferred_update',
      '{parent_instance} created': 'deferred_update',

      // this works like autocomplete_select on all modal forms and
      // descendant class objects.
      autocomplete_select: function (el, event, ui) {
        var mapping;
        var extraAttrs;
        if (!this.element) {
          return;
        }
        extraAttrs = can.reduce(
          this.element.find('input:not([data-mapping], [data-lookup])').get(),
          function (attrs, el) {
            attrs[$(el).attr('name')] = $(el).val();
            return attrs;
          }, {});
        if (this.scope.attr('deferred')) {
          this.scope.changes.push({
            what: ui.item,
            how: 'add',
            extra: extraAttrs
          });
        } else {
          mapping = this.scope.mapping ||
            GGRC.Mappings.get_canonical_mapping_name(
              this.scope.instance.constructor.shortName,
              ui.item.constructor.shortName);
          this.scope.instance.mark_for_addition(mapping, ui.item, extraAttrs);
        }
        function doesExist(arr, owner) {
          if (!arr || !arr.length) {
            return false;
          }
          return !!~can.inArray(owner.id, $.map(arr, function (item) {
            return item.id;
          }));
        }

        // If it's owners and user isn't pre-added
        if (!(~['owners'].indexOf(this.scope.mapping) &&
          doesExist(this.scope.list, ui.item))) {
          this.scope.list.push(ui.item);
        }
        this.scope.attr('show_new_object_form', false);
      },
      '[data-toggle=unmap] click': function (el, ev) {
        ev.stopPropagation();
        can.map(el.find('.result'), function (resultEl) {
          var obj = $(resultEl).data('result');
          var len = this.scope.list.length;
          var mapping;

          if (this.scope.attr('deferred')) {
            this.scope.changes.push({what: obj, how: 'remove'});
          } else {
            mapping = this.scope.mapping ||
              GGRC.Mappings.get_canonical_mapping_name(
                this.scope.instance.constructor.shortName,
                obj.constructor.shortName);
            this.scope.instance.mark_for_deletion(mapping, obj);
          }
          for (; len >= 0; len--) {
            if (this.scope.list[len] === obj) {
              this.scope.list.splice(len, 1);
            }
          }
        }.bind(this));
      },
      'input[null-if-empty] change': function (el) {
        if (!el.val()) {
          this.scope.attributes.attr(el.attr('name'), null);
        }
      },
      'input keyup': function (el, ev) {
        ev.stopPropagation();
      },
      'input, textarea, select change': function (el, ev) {
        this.scope.attributes.attr(el.attr('name'), el.val());
      },

      'input:not([data-lookup], [data-mapping]), textarea keyup':
        function (el, ev) {
          if (el.prop('value').length === 0 ||
            (typeof el.attr('value') !== 'undefined' &&
            el.attr('value').length === 0)) {
            this.scope.attributes.attr(el.attr('name'), el.val());
          }
        },
      'a[data-toggle=submit]:not(.disabled) click': function (el, ev) {
        var obj;
        var mapping;
        var that = this;
        var binding = this.scope.instance.get_binding(this.scope.mapping);
        var extraAttrs = can.reduce(
          this.element.find('input:not([data-mapping], [data-lookup])').get(),
          function (attrs, el) {
            if ($(el).attr('model')) {
              attrs[$(el).attr('name')] =
                CMS.Models[$(el).attr('model')].findInCacheById($(el).val());
            } else {
              attrs[$(el).attr('name')] = $(el).val();
            }
            return attrs;
          }, {});

        ev.stopPropagation();

        extraAttrs[binding.loader.object_attr] = this.scope.instance;
        if (binding.loader instanceof GGRC.ListLoaders.DirectListLoader) {
          obj = new CMS.Models[binding.loader.model_name](extraAttrs);
        } else {
          obj = new CMS.Models[binding.loader.option_model_name](extraAttrs);
        }

        if (that.scope.attr('deferred')) {
          that.scope.changes.push({what: obj, how: 'add', extra: extraAttrs});
        } else {
          mapping = that.scope.mapping ||
            GGRC.Mappings.get_canonical_mapping_name(
              that.scope.instance.constructor.shortName,
              obj.constructor.shortName);
          that.scope.instance.mark_for_addition(mapping, obj, extraAttrs);
        }
        that.scope.list.push(obj);
        that.scope.attr('attributes', {});
      },
      'a[data-object-source] modal:success': 'addMapings',
      'defer:add': 'addMapings',
      addMapings: function (el, ev, data) {
        var mapping;
        ev.stopPropagation();

        can.each(data.arr || [data], function (obj) {
          if (this.scope.attr('deferred')) {
            this.scope.changes.push({what: obj, how: 'add'});
          } else {
            mapping = this.scope.mapping ||
              GGRC.Mappings.get_canonical_mapping_name(
                this.scope.instance.constructor.shortName,
                obj.constructor.shortName);
            this.scope.instance.mark_for_addition(mapping, obj);
          }
          this.scope.list.push(obj);
        }, this);
      },
      '.ui-autocomplete-input modal:success': function (el, ev, data, options) {
        var that = this;
        var extraAttrs = can.reduce(this.element
            .find('input:not([data-mapping], [data-lookup])').get(),
          function (attrs, el) {
            if ($(el).attr('model')) {
              attrs[$(el).attr('name')] = CMS.Models[$(el).attr('model')]
                .findInCacheById($(el).val());
            } else {
              attrs[$(el).attr('name')] = $(el).val();
            }
            return attrs;
          }, {});

        can.each(data.arr || [data], function (obj) {
          var mapping;
          if (that.scope.attr('deferred')) {
            that.scope.changes.push({what: obj, how: 'add', extra: extraAttrs});
          } else {
            mapping = that.scope.mapping ||
              GGRC.Mappings.get_canonical_mapping_name(
                that.scope.instance.constructor.shortName,
                obj.constructor.shortName);
            that.scope.instance.mark_for_addition(mapping, obj, extraAttrs);
          }
          that.scope.list.push(obj);
          that.scope.attr('attributes', {});
        });
      }
    },
    helpers: {
      // Mapping-based autocomplete selectors use this helper to
      //  attach the mapping autocomplete ui widget.  These elements should
      //  be decorated with data-mapping attributes.
      mapping_autocomplete: function (options) {
        return function (el) {
          var $el = $(el);
          $el.ggrc_mapping_autocomplete({
            controller: options.contexts.attr('controller'),
            model: $el.data('model'),
            mapping: false
          });
        };
      }
    }
  });
})(window.can, window.can.$);
