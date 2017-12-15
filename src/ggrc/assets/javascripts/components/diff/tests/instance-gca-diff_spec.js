/*
 Copyright (C) 2017 Google Inc., authors, and contributors
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

import Component from '../instance-gca-diff';

describe('instance-gca-diff component', () => {
  let viewModel;
  let emptyValue;
  const EXPECTED_CA_TITLE = 'Attr title...';

  beforeAll(() => {
    viewModel = getComponentVM(Component);
    emptyValue = viewModel.attr('emptyValue');
  });

  describe('"buildAttributeDiff" method', () => {
    let buildAttributeDiff;

    beforeAll(() => {
      buildAttributeDiff = viewModel.buildAttributeDiff.bind(viewModel);
    });

    function buildCurrentAttrObject(value) {
      const currentAttr = {
        def: {
          title: EXPECTED_CA_TITLE,
        },
        value: {
          attribute_value: value,
        },
      };

      return currentAttr;
    }

    it('should return diff with empty currentVal', () => {
      const expectedValue = 'simple text';
      const modifiedAttr = {
        attribute_value: expectedValue,
      };
      const currentAttr = buildCurrentAttrObject();
      const result = buildAttributeDiff(modifiedAttr, currentAttr);

      expect(result.attrName).toEqual(EXPECTED_CA_TITLE);
      expect(result.currentVal[0]).toEqual(emptyValue);
      expect(result.modifiedVal[0]).toEqual(expectedValue);
    });

    it('should return diff with empty modifiedVal', () => {
      const expectedValue = 'simple text';
      const modifiedAttr = {
        attribute_value: '',
      };
      const currentAttr = buildCurrentAttrObject(expectedValue);
      const result = buildAttributeDiff(modifiedAttr, currentAttr);

      expect(result.attrName).toEqual(EXPECTED_CA_TITLE);
      expect(result.modifiedVal[0]).toEqual(emptyValue);
      expect(result.currentVal[0]).toEqual(expectedValue);
    });

    it('should return diff with filled fields', () => {
      const expectedValue = 'simple text';
      const expectedCurrentValue = 'simple';
      const modifiedAttr = {
        attribute_value: expectedValue,
      };
      const currentAttr = buildCurrentAttrObject(expectedCurrentValue);
      const result = buildAttributeDiff(modifiedAttr, currentAttr);

      expect(result.attrName).toEqual(EXPECTED_CA_TITLE);
      expect(result.modifiedVal[0]).toEqual(expectedValue);
      expect(result.currentVal[0]).toEqual(expectedCurrentValue);
    });
  });

  describe('"convertValue" function', () => {
    const CHECKBOX_TRUE_VALUE = '✓';
    const CHECKOBX_TYPE = 'Checkbox';
    let convertValue;

    beforeAll(() => {
      convertValue = viewModel.convertValue.bind(viewModel);
    });

    it('should return emptyValue. Empty string', () => {
      const result = convertValue('', 'Text');
      expect(result).toEqual(emptyValue);
    });

    it('should return true. Checkbox type. Value is string', () => {
      const result = convertValue('1', CHECKOBX_TYPE);
      expect(result).toEqual(CHECKBOX_TRUE_VALUE);
    });

    it('should return true. Checkbox type. Value is boolean (true)', () => {
      const result = convertValue(true, CHECKOBX_TYPE);
      expect(result).toEqual(CHECKBOX_TRUE_VALUE);
    });

    it('should return true. Checkbox type. Value is boolean (false)', () => {
      const result = convertValue(false, CHECKOBX_TYPE);
      expect(result).toEqual(emptyValue);
    });

    it('should return emptyValue. Checkbox type. Wrong string', () => {
      const result = convertValue('11', CHECKOBX_TYPE);
      expect(result).toEqual(emptyValue);
    });
  });
});
