/*
 Copyright (C) 2017 Google Inc., authors, and contributors
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

export default can.Map({
  currentInstance: {},
  diff: [],
  emptyValue: '—',
  getAttrDisplayName(name) {
    const instanceType = this.attr('currentInstance.type');
    const attrDefs = GGRC.model_attr_defs[instanceType];
    let displayName;

    if (!attrDefs) {
      return name;
    }

    displayName = (_.find(attrDefs, (attr) => attr.attr_name === name) || {})
      .display_name;

    return displayName || name;
  },
});
