/*
  Copyright (C) 2017 Google Inc.
  Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

import Component from '../editable-people-group';

describe('GGRC.Components.editablePeopleGroup', function () {
  'use strict';

  var viewModel;
  var peopleItems = [
    {id: 1}, {id: 2}, {id: 3}, {id: 4}, {id: 5}, {id: 6}
  ];

  beforeAll(function () {
    viewModel = new Component.prototype.viewModel;
    console.error(viewModel);
  });

  beforeEach(function () {
    viewModel.attr('editableMode', false);
  });

  describe('"showSeeMoreLink" property', function () {
    it('"showSeeMoreLink" should be FALSE. edit mode', function () {
      viewModel.attr('people', peopleItems);
      viewModel.attr('editableMode', true);
      expect(viewModel.attr('showSeeMoreLink')).toBe(false);
    });

    it('"showSeeMoreLink" should be TRUE. edit mode is false', function () {
      viewModel.attr('people', peopleItems);
      expect(viewModel.attr('showSeeMoreLink')).toBe(true);
    });

    it('"showSeeMoreLink" should be FALSE. People length less than 5',
      function () {
        // get 4 persons
        var people = peopleItems.slice(0, 4);
        viewModel.attr('people', people);

        expect(viewModel.attr('showSeeMoreLink')).toBe(false);
      }
    );
  });

  describe('"showPeopleGroupModal" property', function () {
    it('"showPeopleGroupModal" should be FALSE. People length less than 5',
      function () {
        // get 4 persons
        var people = peopleItems.slice(0, 4);
        viewModel.attr('people', people);

        // trigger editableMode setter
        viewModel.attr('editableMode', true);

        expect(viewModel.attr('showPeopleGroupModal')).toBe(false);
      }
    );

    it('"showPeopleGroupModal" should be TRUE',
      function () {
        viewModel.attr('people', peopleItems);

        // trigger editableMode setter
        viewModel.attr('editableMode', true);

        expect(viewModel.attr('showPeopleGroupModal')).toBe(true);
      }
    );
  });
});
