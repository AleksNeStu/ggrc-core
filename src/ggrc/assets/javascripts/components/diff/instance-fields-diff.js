/*
 Copyright (C) 2017 Google Inc., authors, and contributors
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

import DiffBaseVM from './diff-base-vm';
const tag = 'instance-fields-diff';

const viewModel = DiffBaseVM.extend({
  modifiedFields: {},
  buildDiffObject() {
    const instance = this.attr('currentInstance');
    const modifiedFields = this.attr('modifiedFields');
    const fieldsKeys = can.Map.keys(modifiedFields);

    const diff = fieldsKeys.map((key) => {
      const modifiedVal = modifiedFields[key];
      const currentVal = instance.attr(key);

      const diffObject = {
        attrName: this.getAttrDisplayName(key),
        modifiedVal: this.getValueOrEmpty(modifiedVal),
        currentVal: this.getValueOrEmpty(currentVal),
      };

      return diffObject;
    });

    this.attr('diff', diff);
  },
  getValueOrEmpty(value) {
    const emptyValue = this.attr('emptyValue');
    return value === null || value === undefined || value === '' ?
      emptyValue :
      value;
  },
});

export default can.Component.extend({
  tag,
  viewModel: viewModel,
  events: {
    inserted() {
      const instance = this.viewModel.attr('currentInstance');
      const modifiedFields = this.viewModel.attr('modifiedFields');

      if (!instance || !modifiedFields) {
        return;
      }
      this.viewModel.buildDiffObject();
    },
  },
});
