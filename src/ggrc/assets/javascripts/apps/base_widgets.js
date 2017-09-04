/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (GGRC, _) {
  'use strict';
  /**
   * Tree View Widgets Configuration module
   */
  var allCoreTypes = [
    'AccessGroup',
    'Assessment',
    'AssessmentTemplate',
    'Audit',
    'Clause',
    'Contract',
    'Control',
    'DataAsset',
    'Facility',
    'Issue',
    'Market',
    'Objective',
    'OrgGroup',
    'Person',
    'Policy',
    'Process',
    'Product',
    'Program',
    'Project',
    'Regulation',
    'Risk',
    'Section',
    'Standard',
    'System',
    'Threat',
    'Vendor'
  ];
  // NOTE: Widgets that have the order value are sorted by an increase values,
  // the rest of widgets are sorted alphabetically
  var defaultOrderTypes = {
    Standard: 10,
    Regulation: 20,
    Section: 30,
    Objective: 40,
    Control: 50,
    Product: 60,
    System: 70,
    Process: 80,
    Audit: 90,
    Person: 100
  };
  // Items allowed for mapping via snapshot.
  var snapshotWidgetsConfig = GGRC.config.snapshotable_objects || [];
  var objectVersions = _.map(snapshotWidgetsConfig, function (obj) {
    return obj + '_versions';
  });

  // Items allowed for relationship mapping
  var excludeMappingConfig = [
    'AssessmentTemplate'
  ];
  // Extra Tree View Widgets require to be rendered on Audit View
  var auditInclusion = [
    'Assessment',
    'Person',
    'Program',
    'Issue'
  ];
  var baseWidgetsByType;

  var filteredTypes = _.difference(allCoreTypes, excludeMappingConfig);
  // Audit is excluded and created a separate logic for it

  var objectVersionWidgets = {};
  snapshotWidgetsConfig.forEach(function (model) {
    objectVersionWidgets[model + '_versions'] = [model];
  });

  baseWidgetsByType = {
    AccessGroup: _.difference(filteredTypes, ['AccessGroup']),
    Audit: [].concat(snapshotWidgetsConfig, excludeMappingConfig,
      auditInclusion).sort(),
    Clause: _.difference(filteredTypes, ['Clause']),
    Contract: _.difference(filteredTypes,
      ['Contract', 'Policy', 'Regulation', 'Standard']),
    Control: filteredTypes,
    Assessment: snapshotWidgetsConfig.concat(['Audit', 'Issue']).sort(),
    AssessmentTemplate: ['Audit'],
    DataAsset: filteredTypes,
    Facility: filteredTypes,
    Issue: objectVersions.concat(_.difference(filteredTypes, ['Person'])),
    Market: filteredTypes,
    Objective: filteredTypes,
    OrgGroup: filteredTypes,
    Person: ['Issue'].concat(_.difference(filteredTypes, ['Person'])),
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
    Risk: filteredTypes,
    Threat: filteredTypes,
    Vendor: filteredTypes
  };

  baseWidgetsByType = _.extend(baseWidgetsByType, objectVersionWidgets);

  GGRC.tree_view = GGRC.tree_view || new can.Map();
  GGRC.tree_view.attr('base_widgets_by_type', baseWidgetsByType);
  GGRC.tree_view.attr('defaultOrderTypes', defaultOrderTypes);
})(window.GGRC, window._);
