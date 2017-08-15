/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

describe('GGRC.VM.ObjectOperationsBaseVM', function () {
  'use strict';

  var baseVM;

  beforeEach(function () {
    baseVM = GGRC.VM.ObjectOperationsBaseVM();
  });

  describe('availableTypes() method', function () {
    var originalInScopeModels;
    beforeAll(function () {
      originalInScopeModels = GGRC.Utils.Snapshots.inScopeModels;
      GGRC.Utils.Snapshots.inScopeModels = ['test1', 'test2'];
    });
    afterAll(function () {
      GGRC.Utils.Snapshots.inScopeModels = originalInScopeModels;
    });

    it('correctly calls getMappingTypes', function () {
      var result;
      spyOn(GGRC.Mappings, 'getMappingTypes').and.returnValue('types');
      baseVM.attr('object', 'testObject');

      result = baseVM.availableTypes();
      expect(GGRC.Mappings.getMappingTypes).toHaveBeenCalledWith('testObject',
        [], ['test1', 'test2']);
      expect(result).toEqual('types');
    });
  });

  describe('get() for baseVM.parentInstance', function () {
    beforeEach(function () {
      spyOn(CMS.Models, 'get_instance')
        .and.returnValue('parentInstance');
    });

    it('returns parentInstance', function () {
      var result = baseVM.attr('parentInstance');
      expect(result).toEqual('parentInstance');
    });
  });

  describe('modelFromType() method', function () {
    it('returns undefined if no models', function () {
      var result = baseVM.modelFromType('program');
      expect(result).toEqual(undefined);
    });

    it('returns model config by model value', function () {
      var result;
      var types = {
        governance: {
          items: [{
            value: 'v1'
          }, {
            value: 'v2'
          }, {
            value: 'v3'
          }]
        }
      };

      spyOn(GGRC.Mappings, 'getMappingTypes')
        .and.returnValue(types);

      result = baseVM.modelFromType('v2');
      expect(result).toEqual(types.governance.items[1]);
    });
  });
});
