/*!
  Copyright (C) 2017 Google Inc.
  Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

describe('GGRC.Components.exportGroup', function () {
  'use strict';

  var Component;  // the component under test

  beforeAll(function () {
    Component = GGRC.Components.get('exportGroup');
  });

  describe('events', function () {
    describe('inserted() method', function () {
      var method;  // the method under test
      var that;

      beforeEach(function () {
        that = {
          addPanel: jasmine.createSpy()
        };
        method = Component.prototype.events.inserted.bind(that);
      });
      it('calls addPanel with proper arguments', function () {
        method();
        expect(that.addPanel).toHaveBeenCalledWith(jasmine.objectContaining({
          type: 'Program',
          isSnapshots: undefined
        }));
      });
    });
    describe('addPanel() method', function () {
      var method;  // the method under test
      var data;
      var viewModel;

      beforeEach(function () {
        viewModel = new can.Map({
          _index: 0,
          panels: {
            items: []
          }
        });
        method = Component.prototype.events.addPanel.bind({
          viewModel: viewModel
        });
      });
      it('adds panel with "Program" type if data.type is undefined',
        function () {
          data = {};
          method(data);
          expect(viewModel.attr('panels.items')[0].type).toEqual('Program');
        });
      it('adds panel with type from data if it is defined',
        function () {
          data = {type: 'Audit'};
          method(data);
          expect(viewModel.attr('panels.items')[0].type).toEqual('Audit');
        });
      it('adds panel with snapshot_type equal to data.type and' +
      ' type equal to "Snapshot" if it is snapshot', function () {
        data = {
          type: 'Control',
          isSnapshots: 'true'
        };
        method(data);
        expect(viewModel.attr('panels.items')[0].type).toEqual('Snapshot');
        expect(viewModel.attr('panels.items')[0].snapshot_type)
          .toEqual('Control');
      });
    });
  });
});
