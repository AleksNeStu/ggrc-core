/*!
    Copyright (C) 2017 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

(function (can, $) {
  'use strict';

  GGRC.Components('mapperResults', {
    tag: 'mapper-results',
    template: can.view(
      GGRC.mustache_path +
      '/components/unified_mapper/mapper_results.mustache'
    ),
    scope: {
      'items-per-page': '@',
      page: 0,
      page_loading: false,
      select_state: false,
      loading_or_saving: function () {
        return this.attr('page_loading') || this.attr('mapper.is_saving');
      },
      unselectAll: function (scope, el, ev) {
        ev.preventDefault();

        this.attr('mapper.all_selected', false);
        this.attr('select_state', false);
        scope.attr('selected').replace([]);
      },
      selectAll: function (scope, el, ev) {
        var entries;
        var que;

        ev.preventDefault();

        if (el.hasClass('disabled')) {
          return;
        }

        que = new RefreshQueue();
        entries = this.attr('entries');

        this.attr('select_state', true);
        this.attr('mapper.all_selected', true);
        this.attr('is_loading', true);

        que.enqueue(entries)
          .trigger()
          .then(function (models) {
            this.attr('is_loading', false);
            this.attr('selected', _.map(models, function (model) {
              return {
                id: model.id,
                type: model.type,
                href: model.href
              };
            }));
          }.bind(this));
      }
    },
    events: {
      inserted: function () {
        this.scope.attr('entries', []);
        this.scope.attr('options', []);
        this.element.find('.results-wrap').cms_controllers_infinite_scroll();
      },
      '.modalSearchButton click': 'getResults',
      '.results-wrap scrollNext': 'drawPage',
      '{mapper.newEntries} length': function () {
        var newEntries = this.scope.attr('mapper.newEntries');
        var newSelected;
        var entries;
        var clonedSelected;
        var selected = this.scope.attr('selected');

        // newEntries should be contain only one element
        if (newEntries.length === 0) {
          return;
        }

        entries = this.scope.attr('entries');

        // add new entry as first element (should be displayed on top of list)
        entries.unshift(newEntries[0]);

        this.drawNewEntries(newEntries);

        // get selected object from new entry
        newSelected = _.map(newEntries, function (model) {
          return {
            id: model.id,
            type: model.type,
            href: model.href
          };
        });

        // clone 'selected' and then update 'selected' attr (it triggers checkboxes)
        clonedSelected = selected.slice();
        clonedSelected.push.apply(clonedSelected, newSelected);
        this.scope.attr('selected', clonedSelected);
      },
      drawNewEntries: function (newEntries) {
        var options = this.scope.attr('options');

        if (!newEntries.length) {
          return undefined;
        }

        // set first page for correct render of pages
        this.scope.attr('page', 1);

        // should be displayed on top of list
        options.unshift.apply(options,
          can.map(newEntries, this.getItem.bind(this))
        );
      },
      getItem: function (model) {
        var selected;
        var mapper;
        var binding;
        var bindings;
        if (!model.type) {
          return undefined;
        }

        if (this.scope.attr('mapper.search_only')) {
          return {
            instance: model,
            selected_object: false,
            binding: {},
            mappings: []
          };
        }

        selected = this.scope.attr('mapper.parentInstance');
        mapper = this.scope.mapper.modelFromType(model.type);
        bindings = this.scope.attr('mapper.bindings');

        if (bindings[model.id]) {
          return _.extend(bindings[model.id], {
            selected_object: selected
          });
        }
        if (selected.has_binding(mapper.plural.toLowerCase())) {
          binding = selected.get_binding(mapper.plural.toLowerCase());
        }
        return {
          instance: model,
          selected_object: selected,
          binding: binding,
          mappings: []
        };
      },
      drawPage: function () {
        var page = this.scope.attr('page');
        var nextPage = page + 1;
        var perPage = Number(this.scope.attr('items-per-page'));
        var pageItems = this.scope.attr('entries').slice(
          page * perPage,
          nextPage * perPage
        );
        var options = this.scope.attr('options');
        var que = new RefreshQueue();

        if (this.scope.attr('mapper.page_loading') || !pageItems.length) {
          return undefined;
        }

        this.scope.attr('mapper.page_loading', true);

        return que.enqueue(pageItems)
          .trigger()
          .then(function (models) {
            this.scope.attr('mapper.page_loading', false);
            this.scope.attr('page', nextPage);
            options.push.apply(options,
                can.map(models, this.getItem.bind(this))
            );
          }.bind(this));
      },
      searchFor: function (data) {
        var joinModel;
        var params = [];
        var param = {};
        var relevantObjects = data.options.relevant_objects;

        data.options = data.options || {};

        joinModel = GGRC.Mappings.join_model_name_for(
          this.scope.attr('mapper.object'), data.model_name);
        if (joinModel !== 'TaskGroupObject' && data.model_name === 'Program') {
          data.options.permission_parms = {
            __permission_model: joinModel
          };
        }

        if (!_.includes(['ObjectPerson', 'WorkflowPerson'], joinModel) &&
            !this.options.scope.attr('mapper.search_only')) {
          data.options.__permission_type =
            data.options.__permission_type || 'update';
        }
        data.model_name = _.isString(data.model_name) ?
          [data.model_name] :
          data.model_name;

        data.model_name.forEach(function (modelName) {
          if (modelName !== 'MultitypeSearch') {
            param = GGRC.Utils.QueryAPI.buildParam(modelName, {
              filter: data.term
            }, relevantObjects, {});
            param.permissions = data.options.__permission_type;
            param.type = 'ids';
            params.push(param);
          }
        });

        return can.Model.Cacheable.queryAll({data: params});
      },

      getResults: function () {
        var contact = this.scope.attr('contact');
        var contactEmail = this.scope.attr('mapper.contactEmail');
        var filters;
        var modelName = this.scope.attr('type');
        var params = {};
        var relevantList = this.scope.attr('mapper.relevant');
        var term = this.scope.attr('term');

        if (this.scope.attr('mapper.page_loading') ||
            this.scope.attr('mapper.is_saving')) {
          return;
        }
        this.scope.attr('page', 0);
        this.scope.attr('entries', []);
        this.scope.attr('selected', []);
        this.scope.attr('options', []);
        this.scope.attr('select_state', false);
        this.scope.attr('mapper.all_selected', false);

        filters = _.compact(_.map(relevantList, function (relevant) {
          if (!relevant.value || !relevant.filter) {
            return undefined;
          }
          return {
            type: relevant.filter.type,
            id: relevant.filter.id
          };
        }));
        if (contact && contactEmail) {
          params.contact_id = contact.id;
        }

        if (!_.isEmpty(filters)) {
          params.relevant_objects = filters;
        }

        this.scope.attr('mapper.page_loading', true);

        this.searchFor({
          term: term,
          model_name: modelName,
          options: params
        }).then(function (mappings) {
          var list = [];
          can.each(mappings, function (entry, i) {
            var _class = (can.getObject('CMS.Models.' + entry.type) ||
            can.getObject('GGRC.Models.' + entry.type));
            list.push(new _class({id: entry.id}));
          });
          this.scope.attr('mapper.page_loading', false);
          this.scope.attr('entries', list);
          this.drawPage();
        }.bind(this));
      }
    },
    helpers: {
      inProgress: function (options) {
        if (this.attr('mapper.page_loading') || this.attr('mapper.is_saving')) {
          return options.fn();
        }
        return options.inverse();
      },
      allSelected: function (options) {
        if (this.attr('mapper.page_loading') ||
            this.attr('mapper.is_saving') ||
            this.attr('mapper.all_selected')) {
          return options.fn();
        }
        return options.inverse();
      }
    }
  });
})(window.can, window.can.$);
