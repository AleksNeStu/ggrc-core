/*
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

describe('GGRC.Components.unmapButton', function () {
  'use strict';
  var events;
  var viewModel;

  beforeAll(function () {
    var Component = GGRC.Components.get('unmapButton');
    events = Component.prototype.events;
  });

  beforeEach(function () {
    viewModel = GGRC.Components.getViewModel('unmapButton');
  });

  describe('"click" event handler', function () {
    var handler;
    beforeEach(function () {
      handler = events.click;
    });

    it('calls "unmapInstance"', function () {
      spyOn(viewModel, 'unmapInstance');

      handler.call({viewModel: viewModel});

      expect(viewModel.unmapInstance).toHaveBeenCalled();
    });

    it('does not call "unmapInstance" when "preventClick" is ON', function () {
      viewModel.attr('preventClick', true);
      spyOn(viewModel, 'unmapInstance');

      handler.call({viewModel: viewModel});

      expect(viewModel.unmapInstance).not.toHaveBeenCalled();
    });
  });
});
