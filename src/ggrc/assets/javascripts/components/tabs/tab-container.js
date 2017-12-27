/*!
 Copyright (C) 2017 Google Inc., authors, and contributors
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

import {NAVIGATE_TO_TAB} from '../../events/eventTypes';
import './tab-panel';
import template from './tab-container.mustache';

export default GGRC.Components('tabContainer', {
  tag: 'tab-container',
  template: template,
  viewModel: {
    lastErrorTab: null,
    define: {
      showTabs: {
        type: 'boolean',
        get: function () {
          return !(this.attr('hideOneTab') &&
            this.attr('panels.length') === 1);
        },
      },
    },
    hideOneTab: true,
    selectedTabIndex: 0,
    panels: [],
    /**
     * Activate currently selected panel
     *
     * @param {Object} scope - current item value from `viewModel.panels`
     * @param {jQuery.Element} el - clicked element
     * @param {Object} ev - click event handler
     */
    setActive: function (scope, el, ev) {
      ev.preventDefault();
      this.setActivePanel(scope.attr('tabIndex'));
    },
    /**
     * Update Panels List setting all panels except selected to inactive state
     * @param {Number} tabIndex - id of activated panel
     */
    setActivePanel: function (tabIndex) {
      this.attr('selectedTabIndex', tabIndex);
      if (this.instance) {
        this.attr('instance.selectedTabIndex', tabIndex);
      }
      this.attr('panels').forEach(function (panel) {
        var isActive = (panel.attr('tabIndex') === tabIndex);
        panel.attr('active', isActive);
        panel.dispatch('updateActiveTab');
      });
    },
    /**
     * Update selected item and set it to the fist item if no previous selection is available
     */
    setDefaultActivePanel: function () {
      var tabIndex = this.attr('selectedTabIndex');
      var panels = this.attr('panels');
      // Select the first panel if tabIndex is not defined
      if (!tabIndex && panels.length) {
        tabIndex = panels[0].attr('tabIndex');
      }
      this.setActivePanel(tabIndex);
    },
    setLastErrorTab: function (tabIndex) {
      this.attr('lastErrorTab', tabIndex);
    },
    navigate(tabId) {
      const panels = this.attr('panels');
      const panel = _.find(panels, (panel) => panel.tabId === tabId);

      if (panel) {
        this.setActivePanel(panel.tabIndex);
      }
    },
  },
  events: {
    /**
     * Update Currently selected Tab on each add of Panels
     */
    '{viewModel.panels} panelAdded': function () {
      this.viewModel.setDefaultActivePanel();
    },
    /**
     * Update Currently selected Tab on each remove of Panels
     */
    '{viewModel.panels} panelRemoved': function () {
      this.viewModel.setDefaultActivePanel();
    },
    /**
     * Activate lastErrorTab.
     */
    '{viewModel.instance} switchToErrorPanel': function () {
      this.viewModel.setActivePanel(this.viewModel.lastErrorTab);
    },
    [`{viewModel.instance} ${NAVIGATE_TO_TAB.type}`](el, ev) {
      this.viewModel.navigate(ev.tabId);
    },
  },
});
