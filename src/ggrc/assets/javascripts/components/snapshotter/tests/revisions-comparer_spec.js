/*!
  Copyright (C) 2017 Google Inc.
  Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

describe('GGRC.Components.revisionsComparer', function () {
  'use strict';

  var Component;  // the component under test

  beforeAll(function () {
    Component = GGRC.Components.get('RevisionsComparer');
  });

  describe('prepareInstances() method', function () {
    var fakeData;
    var method;  // the method under test

    beforeEach(function () {
      method = Component.prototype.scope.prepareInstances;
      fakeData = {
        Revision: {
          values: [{
            id: 1,
            content: {id: 1},
            resource_type: 'Control'
          }, {
            id: 2,
            content: {id: 1},
            resource_type: 'Control'
          }]
        }
      };
    });

    it('returns instances of necessary type and with isRevision', function () {
      var result = method(fakeData);
      result.forEach(function (item) {
        expect(item.instance instanceof CMS.Models.Control).toBeTruthy();
        expect(item.instance.type).toBe('Control');
        expect(item.instance.isRevision).toBe(true);
      });
    });

    it('returns the same length of instances as passed', function () {
      var result = method(fakeData);
      expect(result.length).toBe(fakeData.Revision.values.length);
    });

    it('returns the same data as passed with extra properties', function () {
      var result = method(fakeData);
      var data = fakeData.Revision.values;
      result.forEach(function (item, index) {
        expect(item.instance.id).toEqual(data[index].content.id);
      });
    });
  });

  describe('getInfopanes() method', function () {
    var fakeHTML;
    var method;  // the method under test

    beforeEach(function () {
      method = Component.prototype.scope.getInfopanes;
      fakeHTML = $('<div>' +
                      '<div class="info">' +
                        '<div class="tier-content"></div>' +
                      '</div>' +
                      '<div class="info">' +
                        '<div class="tier-content"></div>' +
                      '</div>' +
                    '</div>');
    });

    it('returns all info panes under the given element', function () {
      var result = method(fakeHTML);
      expect(result.length).toBe(2);
    });
  });

  describe('getCAPanes() method', function () {
    var fakeHTML;
    var method;  // the method under test

    beforeEach(function () {
      method = Component.prototype.scope.getCAPanes;
      fakeHTML = $('<div>' +
                      '<div class="info">' +
                        '<custom-attributes></custom-attributes>' +
                      '</div>' +
                      '<div class="info">' +
                        '<custom-attributes></custom-attributes>' +
                      '</div>' +
                    '</div>');
    });

    it('returns all panes with custom attributes', function () {
      var result = method(fakeHTML);
      expect(result.length).toBe(2);
    });
  });
});
