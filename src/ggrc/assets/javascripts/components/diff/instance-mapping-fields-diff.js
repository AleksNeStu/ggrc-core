/*
 Copyright (C) 2017 Google Inc., authors, and contributors
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

import DiffBaseVM from './diff-base-vm';
const tag = 'instance-mapping-fields-diff';

const viewModel = DiffBaseVM.extend({
  modifiedFields: {},

  buildDiffObject() {
    const fieldsKeys = can.Map.keys(this.attr('modifiedFields'));
    const diffPromises = fieldsKeys.map(async (key) => {
      return await this.buildFieldDiff(key);
    });

    Promise.all(diffPromises).then((data) => {
      const notEmptyDiffs = data.filter((item) => !!item);
      this.attr('diff', notEmptyDiffs);
    });
  },
  async buildFieldDiff(key) {
    const modifiedValueStub = this.attr('modifiedFields').attr(key);
    const currentValueStub = this.attr('currentInstance').attr(key);
    let modifiedField;
    let currentValue;
    let modifiedDisplayName;
    let currentDisplayName;

    if (!currentValueStub && !modifiedValueStub) {
      return;
    }

    modifiedField = await this.getModifiedValue(modifiedValueStub);

    currentValue = this.getCurrentValue(currentValueStub);

    modifiedDisplayName = this.getDisplayName(modifiedField);
    currentDisplayName = this.getDisplayName(currentValue);

    return {
      attrName: this.getAttrDisplayName(key),
      currentVal: currentDisplayName,
      modifiedVal: modifiedDisplayName,
    };
  },
  getCurrentValue(currentValueStub) {
    // current value should be in cache
    return currentValueStub ? currentValueStub.reify() : null;
  },
  async getModifiedValue(modifiedValueStub) {
    let id;
    let type;
    if (!modifiedValueStub) {
      return;
    }

    id = modifiedValueStub.id;
    type = modifiedValueStub.type;
    return await this.getObjectData(id, type, 'title');
  },
});

export default can.Component.extend({
  tag,
  viewModel: viewModel,
  events: {
    inserted() {
      const instance = this.viewModel.attr('currentInstance');
      const modifiedFields = this.viewModel.attr('modifiedFields');
      if (!modifiedFields || !instance) {
        return;
      }
      this.viewModel.buildDiffObject();
    },
  },
});
