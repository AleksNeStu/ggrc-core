/*!
    Copyright (C) 2017 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

(function (can, $) {
  can.Control('GGRC.Controllers.SummaryWidget', {
    defaults: {
      model: null,
      instance: null,
      widget_view: GGRC.mustache_path + '/base_objects/summary.mustache',
      isLoading: true,
      colorsMap: {
        Completed: '#8bc34a',
        'In Progress': '#ffab40',
        'Not Started': '#bdbdbd',
        'Ready for Review': '#1378bb'
      },
      chartOptions: {
        pieSliceText: 'value-and-percentage',
        chartArea: {
          width: '100%',
          height: '90%'
        },
        height: 300,
        legend: {
          position: 'none'
        }
      }
    },
    init: function () {
      var that = this;
      $(function () {
        if (GGRC.page_object) {
          $.extend(that.defaults, {
            model: GGRC.infer_object_type(GGRC.page_object),
            instance: GGRC.page_instance()
          });
        }
      });
    }
  }, {
    init: function () {
      var that = this;
      if (this.element.data('widget-view')) {
        this.options.widget_view = GGRC.mustache_path +
          this.element.data('widget-view');
      }
      this.element.closest('.widget')
        .on('widget_shown', this.widget_shown.bind(this));
      this.element.closest('.widget')
        .on('widget_hidden', this.widget_hidden.bind(this));
      this.options.context = new can.Map({
        model: this.options.model,
        instance: this.options.instance,
        error_msg: '',
        error: true,
        charts: {
          Assessment: {
            legend: []
          }
        }
      });
      can.view(this.get_widget_view(this.element),
        this.options.context, function (frag) {
          that.element.html(frag);
        });
      return 0;
    },
    get_widget_view: function (el) {
      var widgetView = $(el)
        .closest('[data-widget-view]')
        .attr('data-widget-view');
      return (widgetView && widgetView.length > 0) ?
          GGRC.mustache_path + widgetView :
          this.options.widget_view;
    },
    widget_shown: function (event) {
      setTimeout(this.reloadSummary.bind(this), 0);
      return false;
    },
    widget_hidden: function (event) {
      this.setState('Assessment', {total: 0, statuses: { }}, true);
      return false;
    },
    reloadSummary: function () {
      var that = this;
      this.loadChartLibrary(function () {
        that.reloadChart('Assessment', 'piechart_audit_assessments_chart');
      });
    },
    reloadChart: function (type, elementId) {
      var that = this;
      that.setState(type, {total: 0, statuses: { }}, true);
      that.getStatuses(type, that.options.instance.id).then(function (raw) {
        var data = that.parseStatuses(raw[0][type]);
        var chart = that.drawChart(elementId, data);

        that.prepareLegend(type, chart, data);
        that.setState(type, data, false);
      });
    },
    drawChart: function (elementId, raw) {
      var chart;
      var options = this.getChartOptions(raw);
      var data = new google.visualization.DataTable();

      data.addColumn('string', 'Status');
      data.addColumn('number', 'Count');
      data.addRows(raw.statuses);

      chart = new google.visualization.PieChart(
        document.getElementById(elementId));
      chart.draw(data, options);
      this.resizeChart(chart, data, options);

      return chart;
    },
    prepareLegend: function (type, chart, data) {
      var legendData = [];
      var statuses = CMS.Models[type].statuses;
      var chartOptions = this.options.context.charts[type];
      var colorsMap = this.options.colorsMap;

      statuses.forEach(function (status) {
        var rowIndex = _.findIndex(data.statuses, function (row) {
          return row[0] === status;
        });
        var statusData;

        if (rowIndex > -1) {
          statusData = data.statuses[rowIndex];
        }
        if (statusData) {
          legendData.push({
            title: statusData[0],
            count: statusData[1],
            percent: (statusData[1] / data.total * 100).toFixed(1),
            rowIndex: rowIndex,
            color: colorsMap[status]
          });
        } else {
          legendData.push({
            title: status,
            count: 0,
            percent: 0,
            color: colorsMap[status]
          });
        }
      });

      chartOptions.attr('legend', legendData);

      this.element.find('#piechart_audit_assessments_chart-legend')
        .on('mouseenter', 'li', function () {
          var $el = $(this);
          var rowIndex = $el.data('row-index');

          if (_.isNumber(rowIndex)) {
            chart.setSelection([{row: rowIndex, column: null}]);
          }
        })
        .on('mouseleave', 'li', function () {
          chart.setSelection(null);
        });
    },
    getChartOptions: function (raw) {
      var options = Object.assign({}, this.options.chartOptions);
      var colorMaps = this.options.colorsMap;
      options.colors = raw.statuses.map(function (e) {
        return colorMaps[e[0]];
      });

      return options;
    },
    resizeChart: function (chart, data, options) {
      $(window).resize(function () {
        chart.draw(data, options);
      });
      setTimeout(function () {
        $(window).trigger('resize');
      }, 0);
    },
    setState: function (type, data, isLoading) {
      var chartOptions = this.options.context.charts[type];
      chartOptions.attr('total', data.total);
      chartOptions.attr('any', data.total > 0);
      chartOptions.attr('none', isLoading || data.total === 0);
      chartOptions.attr('isLoading', isLoading);
      chartOptions.attr('isLoaded', !isLoading);
      if (isLoading) {
        chartOptions.attr('legend', []);
      }
    },
    parseStatuses: function (data) {
      var groups = _.groupBy(data.values, 'status');
      var pairs = _.pairs(groups);
      var sorted = _.sortBy(pairs, function (e) {
        return e[0];
      });
      var result = sorted.map(function (e) {
        var name = e[0];
        var count = e[1].length;
        return [name, count];
      });
      return {
        total: data.total,
        statuses: result
      };
    },
    getStatuses: function (type, auditId) {
      var query = GGRC.Utils.QueryAPI.buildParam(
        type,
        {},
        {id: auditId, type: 'Audit'},
        ['status']);
      return GGRC.Utils.QueryAPI.makeRequest({data: [query]});
    },
    loadChartLibrary: function (callback) {
      if (typeof google !== 'undefined' &&
          typeof google.charts !== 'undefined') {
        callback();
        return;
      }
      GGRC.Utils.loadScript('https://www.gstatic.com/charts/loader.js', function () {
        google.charts.load('45', {packages: ['corechart']});
        google.charts.setOnLoadCallback(callback);
      });
    }
  });
})(this.can, this.can.$);
