/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, GGRC) {
  'use strict';

  var tpl = can.view(GGRC.mustache_path +
    '/components/reusable-objects/reusable-objects-item.mustache');

  can.Component.extend({
    tag: 'reusable-objects-item',
    template: tpl,
    scope: {
      isSaving: false,
      instance: null,
      checkReusedStatus: false,
      selectedList: [],
      disabled: false,
      mapping: null,
      isChecked: false,
      isDisabled: function () {
        return this.attr('disabled');
      },
      setDisabled: function () {
        var isDisabled = this.attr('instance.isMapped') ||
          GGRC.Utils.is_mapped(
            this.attr('baseInstance'),
            this.attr('instance'),
            this.attr('mapping'));
        this.attr('disabled', isDisabled);
      },
      isSelected: function () {
        var instanceId = this.attr('instance.id');

        return _.some(this.attr('selectedList'), function (item) {
          return item.id === instanceId;
        });
      },
      toggleSelection: function (isChecked) {
        var list = this.attr('selectedList');
        var index = -1;
        if (isChecked && !this.isSelected()) {
          list.push({
            id: this.attr('instance.id'),
            type: this.attr('instance.type')
          });
        } else if (!isChecked) {
          list.forEach(function (item, i) {
            var type = this.attr('instance.snapshot') ?
              'Snapshot' :
              this.attr('instance.type');
            if (this.attr('instance.id') === item.attr('id') &&
              type === item.attr('type')) {
              index = i;
            }
          }.bind(this));
          if (index >= 0) {
            list.splice(index, 1);
          }
        }
      }
    },
    init: function () {
      this.scope.setDisabled();
      if (this.scope.isSelected()) {
        this.scope.attr('isChecked', true);
      }
    },
    events: {
      '{scope} isChecked': function (scope, ev, isChecked) {
        this.scope.toggleSelection(isChecked);
      },
      '{scope} checkReusedStatus': function (scope, ev, performCheck) {
        if (performCheck) {
          this.scope.setDisabled();
        }
      }
    }
  });
})(window.can, window.GGRC);
