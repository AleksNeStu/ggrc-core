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
  GGRC.Components('modalConnector', {
    tag: 'ggrc-modal-connector',
    // <content> in a component template will be replaced with whatever is contained
    //  within the component tag.  Since the views for the original uses of these components
    //  were already created with content, we just used <content> instead of making
    //  new view template files.
    template: '<isolate-form><content/></isolate-form>',
    viewModel: {
      define: {
        fromQueryApi: {
          type: Boolean,
          value: false
        }
      },
      parent_instance: null,
      instance: null,
      instance_attr: '@',
      source_mapping: '@',
      source_mapping_source: '@',
      default_mappings: [], // expects array of objects
      mapping: '@',
      deferred: '@',
      attributes: {},
      newInstance: false,
      list: [],
      // the following are just for the case when we have no object to start with,
      changes: []
    },
    events: {
      init: function () {
        var that = this;
        var key;
        var sourceMappingSource;
        this.viewModel.attr('controller', this);
        if (!this.viewModel.instance) {
          this.viewModel.attr('deferred', true);
        } else if (this.viewModel.instance.reify) {
          this.viewModel.attr('instance', this.viewModel.instance.reify());
        }

        this.viewModel.default_mappings.forEach(function (defaultMapping) {
          var model;
          var objectToAdd;
          if (defaultMapping.id && defaultMapping.type) {
            model = CMS.Models[defaultMapping.type];
            objectToAdd = model.findInCacheById(defaultMapping.id);
            that.viewModel.instance
              .mark_for_addition('related_objects_as_source', objectToAdd, {});
            that.addListItem(objectToAdd);
          }
        });

        if (!this.viewModel.source_mapping) {
          this.viewModel.attr('source_mapping', this.viewModel.mapping);
        }
        if (!this.viewModel.source_mapping_source) {
          this.viewModel.source_mapping_source = 'instance';
        }

        sourceMappingSource =
          this.viewModel[this.viewModel.source_mapping_source];

        if (sourceMappingSource) {
          if (this.viewModel.attr('fromQueryApi')) {
            if (!this.viewModel.attr('newInstance')) {
              this.getMappedObjects().then(function (list) {
                this.setListItems(list);
              }.bind(this));
            }
          } else {
            sourceMappingSource.get_binding(this.viewModel.source_mapping)
              .refresh_instances()
              .then(function (list) {
                this.setListItems(list);
              }.bind(this));
          }
          // this.viewModel.instance.attr("_transient." + this.viewModel.mapping, this.viewModel.list);
        } else {
          key = this.viewModel.instance_attr + '_' +
            (this.viewModel.mapping || this.viewModel.source_mapping);
          if (!this.viewModel.parent_instance._transient[key]) {
            this.viewModel.attr('list', []);
            this.viewModel.parent_instance.attr('_transient.' + key,
              this.viewModel.list);
          } else {
            this.viewModel.attr('list',
              this.viewModel.parent_instance._transient[key]);
          }
        }

        this.options.parent_instance = this.viewModel.parent_instance;
        this.options.instance = this.viewModel.instance;
        this.on();
      },
      destroy: function () {
        this.viewModel.parent_instance.removeAttr('_changes');
      },
      setListItems: function (list) {
        var currentList = this.viewModel.attr('list');
        this.viewModel.attr('list', currentList.concat(can.map(list,
          function (binding) {
            return binding.instance || binding;
          })));
      },
      '{viewModel} list': function () {
        var person;
        // Workaround so we render pre-defined users.
        if (~['owners'].indexOf(this.viewModel.mapping) &&
          this.viewModel.list && !this.viewModel.list.length) {
          person = CMS.Models.Person.findInCacheById(GGRC.current_user.id);
          this.viewModel.instance
            .mark_for_addition(this.viewModel.mapping, person, {});
          this.addListItem(person);
        }
      },
      deferred_update: function () {
        var changes = this.viewModel.changes;
        var instance = this.viewModel.instance;

        if (!changes.length) {
          if (instance && instance._pending_joins &&
            instance._pending_joins.length) {
            instance.delay_resolving_save_until(instance.constructor
              .resolve_deferred_bindings(instance));
          }
          return;
        }
        this.viewModel.attr('instance', this.viewModel.attr('parent_instance')
          .attr(this.viewModel.instance_attr).reify());
        // Add pending operations
        can.each(changes, function (item) {
          var mapping = this.viewModel.mapping ||
              GGRC.Mappings.get_canonical_mapping_name(
                this.viewModel.instance.constructor.shortName,
                item.what.constructor.shortName);
          if (item.how === 'add') {
            this.viewModel.instance
              .mark_for_addition(mapping, item.what, item.extra);
          } else {
            this.viewModel.instance.mark_for_deletion(mapping, item.what);
          }
        }.bind(this)
        );
        this.viewModel.instance
          .delay_resolving_save_until(
            this.viewModel.instance.constructor
              .resolve_deferred_bindings(this.viewModel.instance));
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
        if (this.viewModel.attr('deferred')) {
          this.viewModel.changes.push({
            what: ui.item,
            how: 'add',
            extra: extraAttrs
          });
          this.viewModel.parent_instance.attr('_changes',
            this.viewModel.changes);
        } else {
          mapping = this.viewModel.mapping ||
            GGRC.Mappings.get_canonical_mapping_name(
              this.viewModel.instance.constructor.shortName,
              ui.item.constructor.shortName);
          this.viewModel.instance
            .mark_for_addition(mapping, ui.item, extraAttrs);
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
        if (!(~['owners'].indexOf(this.viewModel.mapping) &&
          doesExist(this.viewModel.list, ui.item))) {
          this.addListItem(ui.item);
        }
        this.viewModel.attr('show_new_object_form', false);
      },
      '[data-toggle=unmap] click': function (el, ev) {
        ev.stopPropagation();

        can.map(el.find('.result'), function (resultEl) {
          var obj = $(resultEl).data('result');
          var len = this.viewModel.list.length;
          var mapping;

          if (this.viewModel.attr('deferred')) {
            this.viewModel.changes.push({what: obj, how: 'remove'});
            this.viewModel.parent_instance.attr('_changes',
              this.viewModel.changes);
          } else {
            mapping = this.viewModel.mapping ||
              GGRC.Mappings.get_canonical_mapping_name(
                this.viewModel.instance.constructor.shortName,
                obj.constructor.shortName);
            this.viewModel.instance.mark_for_deletion(mapping, obj);
          }
          for (; len >= 0; len--) {
            if (this.viewModel.list[len] === obj) {
              this.viewModel.list.splice(len, 1);
            }
          }
        }.bind(this));
      },
      'input[null-if-empty] change': function (el) {
        if (!el.val()) {
          this.viewModel.attributes.attr(el.attr('name'), null);
        }
      },
      'input keyup': function (el, ev) {
        ev.stopPropagation();
      },
      'input, textarea, select change': function (el, ev) {
        this.viewModel.attributes.attr(el.attr('name'), el.val());
      },

      'input:not([data-lookup], [data-mapping]), textarea keyup':
        function (el, ev) {
          if (el.prop('value').length === 0 ||
            (typeof el.attr('value') !== 'undefined' &&
            el.attr('value').length === 0)) {
            this.viewModel.attributes.attr(el.attr('name'), el.val());
          }
        },
      'a[data-toggle=submit]:not(.disabled) click': function (el, ev) {
        var obj;
        var mapping;
        var that = this;
        var binding = this.viewModel.instance
          .get_binding(this.viewModel.mapping);
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

        extraAttrs[binding.loader.object_attr] = this.viewModel.instance;
        if (binding.loader instanceof GGRC.ListLoaders.DirectListLoader) {
          obj = new CMS.Models[binding.loader.model_name](extraAttrs);
        } else {
          obj = new CMS.Models[binding.loader.option_model_name](extraAttrs);
        }

        if (that.viewModel.attr('deferred')) {
          that.viewModel.changes
            .push({what: obj, how: 'add', extra: extraAttrs});
        } else {
          mapping = that.viewModel.mapping ||
            GGRC.Mappings.get_canonical_mapping_name(
              that.viewModel.instance.constructor.shortName,
              obj.constructor.shortName);
          that.viewModel.instance.mark_for_addition(mapping, obj, extraAttrs);
        }
        that.addListItem(obj);
        that.viewModel.attr('attributes', {});
      },
      'a[data-object-source] modal:success': 'addMapings',
      'defer:add': 'addMapings',
      addMapings: function (el, ev, data) {
        var mapping;
        ev.stopPropagation();

        can.each(data.arr || [data], function (obj) {
          if (this.viewModel.attr('deferred')) {
            this.viewModel.changes.push({what: obj, how: 'add'});
            this.viewModel.parent_instance.attr('_changes',
              this.viewModel.changes);
          } else {
            mapping = this.viewModel.mapping ||
              GGRC.Mappings.get_canonical_mapping_name(
                this.viewModel.instance.constructor.shortName,
                obj.constructor.shortName);
            this.viewModel.instance.mark_for_addition(mapping, obj);
          }
          this.addListItem(obj);
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
          if (that.viewModel.attr('deferred')) {
            that.viewModel.changes
              .push({what: obj, how: 'add', extra: extraAttrs});
          } else {
            mapping = that.viewModel.mapping ||
              GGRC.Mappings.get_canonical_mapping_name(
                that.viewModel.instance.constructor.shortName,
                obj.constructor.shortName);
            that.viewModel.instance.mark_for_addition(mapping, obj, extraAttrs);
          }
          that.addListItem(obj);
          that.viewModel.attr('attributes', {});
        });
      },
      addListItem: function (item) {
        var snapshotObject;
        if (GGRC.Utils.Snapshots.isSnapshotType(item) &&
          item.snapshotObject) {
          snapshotObject = item.snapshotObject;
          item.attr('title', snapshotObject.title);
          item.attr('description', snapshotObject.description);
          item.attr('class', snapshotObject.class);
          item.attr('snapshot_object_class', 'snapshot-object');
          item.attr('viewLink', snapshotObject.originalLink);
        }

        this.viewModel.list.push(item);
      },
      buildQuery: function (type) {
        return GGRC.Utils.QueryAPI.buildParams(
          type,
          {},
          {
            type: this.viewModel.attr('instance.type'),
            operation: 'relevant',
            id: this.viewModel.attr('instance.id')
          }
        );
      },
      getMappedObjects: function () {
        var dfd = can.Deferred();
        var auditQuery = this.buildQuery('Audit')[0];
        var issueQuery = this.buildQuery('Issue')[0];
        var snapshotQuery = this.buildQuery('Snapshot')[0];

        GGRC.Utils.QueryAPI
          .makeRequest({data: [auditQuery, issueQuery, snapshotQuery]})
          .then(function (response) {
            var snapshots;
            var list;

            snapshots = response[2].Snapshot.values;
            snapshots.forEach(function (snapshot) {
              var object = GGRC.Utils.Snapshots.toObject(snapshot);

              snapshot.class = object.class;
              snapshot.snapshot_object_class = 'snapshot-object';
              snapshot.title = object.title;
              snapshot.description = object.description;
              snapshot.viewLink = object.originalLink;
            });

            list = response[0].Audit.values
              .concat(response[1].Issue.values)
              .concat(snapshots);

            dfd.resolve(list);
          }
        );

        return dfd;
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
