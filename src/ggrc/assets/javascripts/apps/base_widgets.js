/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (GGRC, _) {
  'use strict';
  /**
   * Tree View Widgets Configuration module
   */
    // NOTE: By default, widgets are sorted alphabetically (the value of
    // the order 100+), but the objects with higher importance that should
    // be  prioritized use order values below 100. An order value of 0 is
    // reserved for the "info" widget which always comes first.
  var defaultOrderTypes = {
    Assessment: 8,
    Regulation: 20,
    Contract: 30,
    Section: 40,
    Objective: 50,
    Control: 60,
    AccessGroup: 100,
    Audit: 120,
    Clause: 130,
    DataAsset: 140,
    Facility: 160,
    Issue: 170,
    Market: 180,
    OrgGroup: 190,
    Person: 200,
    Policy: 210,
    Process: 220,
    Product: 230,
    Program: 240,
    Project: 250,
    Standard: 260,
    System: 270,
    Vendor: 280
  };
  var allTypes = Object.keys(defaultOrderTypes).sort();
  // Items allowed for mapping via snapshot.
  var snapshotWidgetsConfig = GGRC.config.snapshotable_objects || [];
  // Items allowed for relationship mapping
  var excludeMappingConfig = [
    'Assessment',
    'AssessmentTemplate',
    'Issue'
  ];
  // Extra Tree View Widgets require to be rendered on Audit View
  var auditInclusion = [
    'Person',
    'Program'
  ];
  var baseWidgetsByType;
  var orderedWidgetsByType = {};

  var filteredTypes = _.difference(allTypes, excludeMappingConfig);
  // Audit is excluded and created a separate logic for it
  baseWidgetsByType = {
    AccessGroup: _.difference(filteredTypes, ['AccessGroup']),
    Audit: [].concat(snapshotWidgetsConfig, excludeMappingConfig,
      auditInclusion).sort(),
    Clause: _.difference(filteredTypes, ['Clause']),
    Contract: _.difference(filteredTypes,
      ['Contract', 'Policy', 'Regulation', 'Standard']),
    Control: filteredTypes,
    Assessment: snapshotWidgetsConfig.concat('Audit').sort(),
    DataAsset: filteredTypes,
    Facility: filteredTypes,
    Issue: snapshotWidgetsConfig.concat('Audit').sort(),
    Market: filteredTypes,
    Objective: filteredTypes,
    OrgGroup: filteredTypes,
    Person: _.difference(filteredTypes, ['Person']),
    Policy: _.difference(filteredTypes,
      ['Contract', 'Policy', 'Regulation', 'Standard']),
    Process: filteredTypes,
    Product: filteredTypes,
    Program: _.difference(filteredTypes, ['Program']),
    Project: filteredTypes,
    Regulation: _.difference(filteredTypes,
      ['Contract', 'Policy', 'Regulation', 'Standard']),
    Section: filteredTypes,
    Standard: _.difference(filteredTypes,
      ['Contract', 'Policy', 'Regulation', 'Standard']),
    System: filteredTypes,
    Vendor: filteredTypes
  };

  allTypes.forEach(function (type) {
    var related = baseWidgetsByType[type].slice(0);
    orderedWidgetsByType[type] = related.sort(function (a, b) {
      return defaultOrderTypes[a] - defaultOrderTypes[b];
    });
  });

  GGRC.tree_view = GGRC.tree_view || new can.Map();
  GGRC.tree_view.attr('base_widgets_by_type', baseWidgetsByType);
  GGRC.tree_view.attr('orderedWidgetsByType', orderedWidgetsByType);
  GGRC.tree_view.attr('defaultOrderTypes', defaultOrderTypes);
})(window.GGRC, window._);
