/*!
  Copyright (C) 2017 Google Inc.
  Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

import helpers from './../tree-item-custom-attribute';

describe('helpers.get_custom_attr_value', function () {
  'use strict';

  var helper;
  var fakeAttr;
  var fakeInstance;
  var fakeOptions;
  var fakeCustomAttrDefs;
  var origValue;
  var setCustomAttrItem;
  var getCustomAttrItem;
  var actual;
  var customAttrItem;

  beforeAll(function () {
    helper = helpers.get_custom_attr_value;

    fakeCustomAttrDefs = [{
      definition_type: 'control',
      id: 3,
      attribute_type: '',
      title: 'Type',
    },
    {
      definition_type: 'control',
      title: 'CheckBox',
      attribute_type: 'Checkbox',
      id: 4,
    },
    {
      definition_type: 'control',
      title: 'Start Date',
      attribute_type: 'Date',
      id: 5,
    },
    {
      definition_type: 'control',
      title: 'Text',
      attribute_type: 'Text',
      id: 6,
    },
    {
      definition_type: 'control',
      title: 'Rich Text',
      attribute_type: 'Rich Text',
      id: 7,
    },
    {
      definition_type: 'control',
      title: 'Date',
      attribute_type: 'Date',
      id: 9,
    },
    {
      definition_type: 'control',
      title: 'Dropdown',
      attribute_type: 'Dropdown',
      id: 10,
    }];

    origValue = GGRC.custom_attr_defs;
    GGRC.custom_attr_defs = fakeCustomAttrDefs;
    fakeInstance = new can.Map({
      custom_attribute_values: [],
    });

    getCustomAttrItem = function (attrValue, attrId, attrType) {
      return new can.Map({
        attribute_value: attrValue,
        custom_attribute_id: attrId || 3,
        attributeType: attrType,
      });
    };

    setCustomAttrItem = function (attrValue, attrId, attrType) {
      customAttrItem = getCustomAttrItem(attrValue, attrId, attrType);
      fakeInstance.attr('custom_attribute_values.0', customAttrItem);

      spyOn(customAttrItem, 'reify')
        .and.returnValue(customAttrItem);
    };
  });

  afterAll(function () {
    GGRC.custom_attr_defs = origValue;
  });

  beforeEach(function () {
    fakeAttr = {};
    fakeOptions = {};
    fakeInstance.class = {table_singular: 'control'};

    fakeAttr.attr_name = 'Type';
  });

  it('reify() is exec if instance is not an Assessment', function () {
    setCustomAttrItem();
    helper(fakeAttr, fakeInstance, fakeOptions);

    expect(customAttrItem.reify).toHaveBeenCalled();
  });

  it('return correct value if customAttrItem is not undefined',
    function () {
      setCustomAttrItem('correctValue');

      actual = helper(fakeAttr, fakeInstance, fakeOptions);

      expect(actual).toEqual('correctValue');
    });

  it('return an empty string if customAttrItem is undefined', function () {
    setCustomAttrItem();

    actual = helper(fakeAttr, fakeInstance, fakeOptions);

    expect(actual).toEqual('');
  });

  describe('for CA of Checkbox type', function () {
    var attr = {};

    it('returns empty string when CAD wasn\'t found', function () {
      setCustomAttrItem('10', 3, 'Checkbox');

      actual = helper(attr, fakeInstance, fakeOptions);

      expect(actual).toEqual('');
    });

    it('returns "Yes" for CA of type checkbox with value "1"',
      function () {
        attr.attr_name = 'CheckBox';
        setCustomAttrItem('1', 4, 'checkbox');

        actual = helper(attr, fakeInstance, fakeOptions);

        expect(actual).toEqual('Yes');
      });

    it('returns "No" for CA of type checkbox with value "0"',
      function () {
        attr.attr_name = 'CheckBox';
        setCustomAttrItem(0, 4, 'checkbox');

        actual = helper(attr, fakeInstance, fakeOptions);

        expect(actual).toEqual('No');
      });

    it('returns empty string for CA of type checkbox without value',
      function () {
        attr.attr_name = 'CheckBox';
        setCustomAttrItem(undefined, 4, 'checkbox');

        actual = helper(attr, fakeInstance, fakeOptions);

        expect(actual).toEqual('');
      });
  });

  describe('for CA of Date type', function () {
    var attr = {
    };

    it('returns empty string when CAD wasn\'t found', function () {
      setCustomAttrItem('10', 3, 'Date');

      actual = helper(attr, fakeInstance, fakeOptions);

      expect(actual).toEqual('');
    });

    it('returns formatted date when CAD was found', function () {
      var expected = 'expected date';
      var attrValue = '2017-09-30';
      attr.attr_name = 'Date';
      setCustomAttrItem(attrValue, 9, 'Date');
      spyOn(GGRC.Utils, 'formatDate')
        .and.returnValue(expected);

      actual = helper(attr, fakeInstance, fakeOptions);

      expect(actual).toEqual(expected);
      expect(GGRC.Utils.formatDate)
        .toHaveBeenCalledWith(attrValue, true);
    });

    it('tries to format date for existing CAD and undefined value',
      function () {
        var expected = 'expected date';
        var attrValue = undefined;
        attr.attr_name = 'Date';
        setCustomAttrItem(attrValue, 9, 'Date');
        spyOn(GGRC.Utils, 'formatDate')
          .and.returnValue(expected);

        actual = helper(attr, fakeInstance, fakeOptions);

        expect(actual).toEqual(expected);
        expect(GGRC.Utils.formatDate)
          .toHaveBeenCalledWith(attrValue, true);
      });
  });

  describe('for CA of Dropdown type', function () {
    var attr = {
    };

    it('returns empty string when CAD wasn\'t found', function () {
      setCustomAttrItem('10', 3, 'Dropdown');

      actual = helper(attr, fakeInstance, fakeOptions);

      expect(actual).toEqual('');
    });

    it('returns attribute value when CAD was found', function () {
      attr.attr_name = 'Dropdown';
      setCustomAttrItem('10', 10, 'Dropdown');

      actual = helper(attr, fakeInstance, fakeOptions);

      expect(actual).toEqual('10');
    });

    it('returns empty string for existing CAD and undefined value',
      function () {
        attr.attr_name = 'Dropdown';
        setCustomAttrItem(undefined, 10, 'Dropdown');

        actual = helper(attr, fakeInstance, fakeOptions);

        expect(actual).toEqual('');
      });
  });

  describe('for CA of Text type', function () {
    var attr = {
    };

    it('returns empty string when CAD wasn\'t found', function () {
      setCustomAttrItem('10', 3, 'Text');

      actual = helper(attr, fakeInstance, fakeOptions);

      expect(actual).toEqual('');
    });

    it('returns attribute value when CAD was found', function () {
      attr.attr_name = 'Text';
      setCustomAttrItem('10', 6, 'Text');

      actual = helper(attr, fakeInstance, fakeOptions);

      expect(actual).toEqual('10');
    });

    it('returns empty string for existing CAD and undefined value',
      function () {
        attr.attr_name = 'Text';
        setCustomAttrItem(undefined, 6, 'Text');

        actual = helper(attr, fakeInstance, fakeOptions);

        expect(actual).toEqual('');
      });
  });

  describe('for CA of Rich Text type', function () {
    var attr = {
    };

    it('returns empty string when CAD wasn\'t found', function () {
      setCustomAttrItem('10', 3, 'Rich Text');

      actual = helper(attr, fakeInstance, fakeOptions);

      expect(actual).toEqual('');
    });

    it('returns attribute value when CAD was found', function () {
      attr.attr_name = 'Rich Text';
      setCustomAttrItem('10', 7, 'Rich Text');

      actual = helper(attr, fakeInstance, fakeOptions);

      expect(actual).toEqual('10');
    });

    it('returns empty string for existing CAD and undefined value',
      function () {
        attr.attr_name = 'Rich Text';
        setCustomAttrItem(undefined, 7, 'Rich Text');

        actual = helper(attr, fakeInstance, fakeOptions);

        expect(actual).toEqual('');
      });
  });
});
