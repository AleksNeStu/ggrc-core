/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

'use strict';

describe('GGRC.Utils.CustomAttributes ', function () {
  describe('.isEmptyCustomAttribute() method', function () {
    var isEmptyCA;

    beforeAll(function () {
      isEmptyCA = GGRC.Utils.CustomAttributes.isEmptyCustomAttribute;
    });

    describe('check undefined value', function () {
      it('returns true for undefined', function () {
        var result = isEmptyCA(undefined);
        expect(result).toBe(true);
      });
    });

    describe('check Rich Text value', function () {
      it('returns true for empty div', function () {
        var result = isEmptyCA('<div></div>', 'Rich Text');
        expect(result).toBe(true);
      });

      it('returns true for div with a line break', function () {
        var result = isEmptyCA('<div><br></div>', 'Rich Text');
        expect(result).toBe(true);
      });

      it('returns true for div with a empty list', function () {
        var result = isEmptyCA('<div><ul><li></li></ul></div>', 'Rich Text');
        expect(result).toBe(true);
      });

      it('returns true for div with a empty paragraph', function () {
        var result = isEmptyCA('<div><p></p></div>', 'Rich Text');
        expect(result).toBe(true);
      });

      it('returns false for div with the text', function () {
        var result = isEmptyCA('<div>Very important text!</div>', 'Rich Text');
        expect(result).toBe(false);
      });

      it('returns false for not empty list', function () {
        var result = isEmptyCA('<div><ul><li>One</li><li>Two</li></ul></div>',
          'Rich Text');
        expect(result).toBe(false);
      });
    });

    describe('check Checkbox value', function () {
      it('returns false for unchecked', function () {
        var result = isEmptyCA('0', 'Checkbox');
        expect(result).toBe(true);
      });

      it('returns true for checked', function () {
        var result = isEmptyCA('1', 'Checkbox');
        expect(result).toBe(false);
      });
    });

    describe('check Text value', function () {
      it('returns false for not empty', function () {
        var result = isEmptyCA('some text', 'Text');
        expect(result).toBe(false);
      });

      it('returns true for empty', function () {
        var result = isEmptyCA('', 'Text');
        expect(result).toBe(true);
      });
    });

    describe('check Map:Person type', function () {
      it('returns false for selected', function () {
        var result = isEmptyCA('Person', 'Map:Person');
        expect(result).toBe(false);
      });

      it('returns true for not selected', function () {
        var result = isEmptyCA('', 'Map:Person');
        expect(result).toBe(true);
      });

      it('returns true for not selected cav', function () {
        var result = isEmptyCA('', 'Map:Person', {attribute_object: null});
        expect(result).toBe(true);
      });

      it('returns false for selected cav', function () {
        var result = isEmptyCA('', 'Map:Person', {attribute_object: 'Person'});
        expect(result).toBe(false);
      });
    });

    describe('check Date type', function () {
      it('returns false for selected', function () {
        var result = isEmptyCA('01/01/2016', 'Date');
        expect(result).toBe(false);
      });

      it('returns true for not selected', function () {
        var result = isEmptyCA('', 'Date');
        expect(result).toBe(true);
      });
    });

    describe('check Dropdown type', function () {
      it('returns false for selected', function () {
        var result = isEmptyCA('value', 'Dropdown');
        expect(result).toBe(false);
      });

      it('returns true for not selected', function () {
        var result = isEmptyCA('', 'Dropdown');
        expect(result).toBe(true);
      });
    });

    describe('check invalid type', function () {
      it('returns false for invalid type', function () {
        var result = isEmptyCA('some value', 'Invalid');
        expect(result).toBe(false);
      });
    });
  });
  describe('.prepareLocalAttribute() method', function () {
    var prepareAttr;
    beforeAll(function () {
      prepareAttr = GGRC.Utils.CustomAttributes.prepareLocalAttribute;
    });

    it('should be defined', function () {
      expect(prepareAttr).toBeDefined();
    });

    it('should return empty Object if no attribute is provided', function () {
      var result = prepareAttr();
      expect(result).toEqual({});
    });
  });
});
