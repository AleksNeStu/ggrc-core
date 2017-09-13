/*!
  Copyright (C) 2017 Google Inc.
  Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

var url = can.route.deparam(window.location.search.substr(1));
var filterModel = can.Map({
  model_name: 'Program',
  value: '',
  filter: {}
});
var panelModel = can.Map({
  selected: {},
  models: null,
  type: 'Program',
  filter: '',
  relevant: can.compute(function () {
    return new can.List();
  }),
  columns: []
});
var panelsModel = can.Map({
  items: new can.List()
});
var exportModel = can.Map({
  panels: new panelsModel(),
  loading: false,
  url: '/_service/export_csv',
  type: url.model_type || 'Program',
  only_relevant: false,
  filename: 'export_objects.csv',
  format: 'gdrive'
});

GGRC.Components('csvTemplate', {
  tag: 'csv-template',
  template: '<content></content>',
  viewModel: {
    url: '/_service/export_csv',
    selected: [],
    importable: GGRC.Bootstrap.importable
  },
  events: {
    '#importSelect change': function (el, ev) {
      var $items = el.find(':selected');
      var selected = this.viewModel.attr('selected');

      $items.each(function () {
        var $item = $(this);
        if (_.findWhere(selected, {value: $item.val()})) {
          return;
        }
        return selected.push({
          name: $item.attr('label'),
          value: $item.val()
        });
      });
    },
    '.import-button click': function (el, ev) {
      var data;
      ev.preventDefault();
      data = _.map(this.viewModel.attr('selected'), function (el) {
        return {
          object_name: el.value,
          fields: 'all'
        };
      });
      if (!data.length) {
        return;
      }

      GGRC.Utils.export_request({
        data: data
      }).then(function (data) {
        GGRC.Utils.download('import_template.csv', data);
      })
      .fail(function (data) {
        if (data.responseJSON) {
          GGRC.Errors.notifier('error', data.responseJSON.message);
        }
      });
    },
    '.import-list a click': function (el, ev) {
      var index = el.data('index');
      var item = this.viewModel.attr('selected').splice(index, 1)[0];

      ev.preventDefault();

      this.element.find('#importSelect option:selected').each(function () {
        var $item = $(this);
        if ($item.val() === item.value) {
          $item.prop('selected', false);
        }
      });
    }
  }
});

GGRC.Components('csvExport', {
  tag: 'csv-export',
  template: '<content></content>',
  viewModel: {
    isFilterActive: false,
    'export': new exportModel()
  },
  events: {
    toggleIndicator: function (currentFilter) {
      var isExpression =
          !!currentFilter &&
          !!currentFilter.expression.op &&
          currentFilter.expression.op.name !== 'text_search' &&
          currentFilter.expression.op.name !== 'exclude_text_search';
      this.viewModel.attr('isFilterActive', isExpression);
    },
    '.tree-filter__expression-holder input keyup': function (el, ev) {
      this.toggleIndicator(GGRC.query_parser.parse(el.val()));
    },
    '.option-type-selector change': function (el, ev) {
      this.viewModel.attr('isFilterActive', false);
    },
    getObjectsForExport: function () {
      var panels = this.viewModel.attr('export.panels.items');

      return _.map(panels, function (panel, index) {
        var relevantFilter;
        var predicates;
        predicates = _.map(panel.attr('relevant'), function (el) {
          var id = el.model_name === '__previous__' ?
            index - 1 : el.filter.id;
          return id ? '#' + el.model_name + ',' + id + '#' : null;
        });
        if (panel.attr('snapshot_type')) {
          predicates.push(
            ' child_type = ' + panel.attr('snapshot_type') + ' '
          );
        }
        relevantFilter = _.reduce(predicates, function (p1, p2) {
          return p1 + ' AND ' + p2;
        });
        return {
          object_name: panel.type,
          fields: _.compact(_.map(panel.columns(),
            function (item, index) {
              if (panel.selected[index]) {
                return item.key;
              }
            })),
          filters: GGRC.query_parser.join_queries(
            GGRC.query_parser.parse(relevantFilter || ''),
            GGRC.query_parser.parse(panel.filter || '')
          )
        };
      });
    },
    '#export-csv-button click': function (el, ev) {
      this.viewModel.attr('export.loading', true);

      GGRC.Utils.export_request({
        data: {
          objects: this.getObjectsForExport(),
          export_to: this.viewModel.attr('export.chosenFormat')
        }
      }).then(function (data) {
        var link;

        if (this.viewModel.attr('export.chosenFormat') === 'gdrive') {
          data = JSON.parse(data);
          link = 'https://docs.google.com/spreadsheets/d/' + data.id;

          GGRC.Controllers.Modals.confirm({
            modal_title: 'Export Completed',
            modal_description: 'File is exported successfully. ' +
            'You can view the file here: ' +
            '<a href="' + link + '" target="_blank">' + link + '</a>',
            button_view: GGRC.mustache_path + '/modals/close_buttons.mustache'
          });
        } else {
          GGRC.Utils.download(this.viewModel.attr('export.filename'), data);
        }
      }.bind(this))
      .fail(function (data) {
        if (data.responseJSON) {
          GGRC.Errors.notifier('error', data.responseJSON.message);
        }
      })
      .always(function () {
        this.viewModel.attr('export.loading', false);
      }.bind(this));
    },
    '#addAnotherObjectType click': function (el, ev) {
      ev.preventDefault();
      this.viewModel.attr('export').dispatch('addPanel');
    }
  }
});

GGRC.Components('exportGroup', {
  tag: 'export-group',
  template: '<content></content>',
  viewModel: {
    index: 0,
    'export': '@'
  },
  events: {
    inserted: function () {
      this.addPanel({
        type: url.model_type || 'Program',
        isSnapshots: url.isSnapshots
      });
    },
    addPanel: function (data) {
      var index = this.viewModel.attr('index') + 1;
      var pm;

      data = data || {};
      if (!data.type) {
        data.type = 'Program';
      } else if (data.isSnapshots === 'true') {
        data.snapshot_type = data.type;
        data.type = 'Snapshot';
      }

      this.viewModel.attr('index', index);
      pm = new panelModel(data);
      pm.attr('columns', can.compute(function () {
        var definitions = GGRC.model_attr_defs[pm.attr('type')];
        return _.filter(definitions, function (el) {
          return (!el.import_only) &&
                 (el.display_name.indexOf('unmap:') === -1);
        });
      }));
      return this.viewModel.attr('panels.items').push(pm);
    },
    getIndex: function (el) {
      return Number($(el.closest('export-panel'))
        .viewModel().attr('panel_number'));
    },
    '.remove_filter_group click': function (el, ev) {
      var index = this.getIndex(el);

      ev.preventDefault();
      this.viewModel.attr('panels.items').splice(index, 1);
    },
    '{viewModel.export} addPanel': function () {
      this.addPanel();
    }
  }
});

GGRC.Components('exportPanel', {
  tag: 'export-panel',
  template: '<content></content>',
  viewModel: {
    exportable: GGRC.Bootstrap.exportable,
    snapshotable_objects: GGRC.config.snapshotable_objects,
    panel_number: '@',
    has_parent: false,
    fetch_relevant_data: function (id, type) {
      var dfd = CMS.Models[type].findOne({id: id});
      dfd.then(function (result) {
        this.attr('item.relevant').push(new filterModel({
          model_name: url.relevant_type,
          value: url.relevant_id,
          filter: result
        }));
      }.bind(this));
    }
  },
  events: {
    inserted: function () {
      var panelNumber = Number(this.viewModel.attr('panel_number'));

      if (!panelNumber && url.relevant_id && url.relevant_type) {
        this.viewModel.fetch_relevant_data(url.relevant_id, url.relevant_type);
      }
      this.setSelected();
    },
    '[data-action=attribute_select_toggle] click': function (el, ev) {
      var items = GGRC.model_attr_defs[this.viewModel.attr('item.type')];
      var isMapping = el.data('type') === 'mappings';
      var value = el.data('value');

      _.each(items, function (item, index) {
        if (isMapping && item.type === 'mapping') {
          this.viewModel.attr('item.selected.' + index, value);
        }
        if (!isMapping && item.type !== 'mapping') {
          this.viewModel.attr('item.selected.' + index, value);
        }
      }.bind(this));
    },
    setSelected: function () {
      var selected = _.reduce(this.viewModel.attr('item').columns(),
        function (memo, data, index) {
          memo[index] = true;
          return memo;
        }, {});
      this.viewModel.attr('item.selected', selected);
    },
    '{viewModel.item} type': function () {
      this.viewModel.attr('item.selected', {});
      this.viewModel.attr('item.relevant', []);
      this.viewModel.attr('item.filter', '');
      this.viewModel.attr('item.snapshot_type', '');
      this.viewModel.attr('item.has_parent', false);

      if (this.viewModel.attr('item.type') === 'Snapshot') {
        this.viewModel.attr('item.snapshot_type', 'Control');
      }

      this.setSelected();
    }
  },
  helpers: {
    if_first_panel: function (options) {
      if (Number(this.attr('panel_number')) > 0) {
        return options.inverse();
      }
      return options.fn();
    }
  }
});
