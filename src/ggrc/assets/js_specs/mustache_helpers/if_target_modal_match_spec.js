/*!
  Copyright (C) 2017 Google Inc.
  Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

describe('can.mustache.helper.if_target_modal_match', function () {
  'use strict';

  var fakeOptions;  // fake mustache options object passed to the helper
  var helper;
  var fakeWindow;
  var origWinObject;
  var templateContext;

  beforeAll(function () {
    helper = can.Mustache._helpers.if_target_modal_match.fn;

    fakeWindow = {
      location: {
        pathname: '/foo'
      }
    };

    origWinObject = GGRC.Utils.win;
    GGRC.Utils.win = fakeWindow;
  });

  afterAll(function () {
    GGRC.Utils.win = origWinObject;
  });

  beforeEach(function () {
    templateContext = {foo: 'bar'};

    fakeOptions = {
      fn: jasmine.createSpy(),
      inverse: jasmine.createSpy(),
      contexts: templateContext
    };
  });

  it('matches the "create new" modal for Audit on Program page', function () {
    var callArgs;
    var expectedArgs = [templateContext];

    fakeWindow.location.pathname = '/programs/123';
    helper('Audit', 'modal-ajax-form', fakeOptions);

    expect(fakeOptions.fn.calls.count()).toEqual(1);
    callArgs = fakeOptions.fn.calls.mostRecent().args;
    expect(callArgs).toEqual(expectedArgs);
  });

  it('matches the "create new" modal for Section on Contract page',
    function () {
      var callArgs;
      var expectedArgs = [templateContext];

      fakeWindow.location.pathname = '/contracts/123';
      helper('Section', 'modal-ajax-form', fakeOptions);

      expect(fakeOptions.fn.calls.count()).toEqual(1);
      callArgs = fakeOptions.fn.calls.mostRecent().args;
      expect(callArgs).toEqual(expectedArgs);
    }
  );

  it('does not match the "create new" modal for Section on Program page',
    function () {
      var callArgs;
      var expectedArgs = [templateContext];

      fakeWindow.location.pathname = '/programs/123';
      helper('Section', 'modal-ajax-form', fakeOptions);

      expect(fakeOptions.inverse.calls.count()).toEqual(1);
      callArgs = fakeOptions.inverse.calls.mostRecent().args;
      expect(callArgs).toEqual(expectedArgs);
    }
  );

  it('matches the "create new" modal for Section on Policy page',
    function () {
      var callArgs;
      var expectedArgs = [templateContext];

      fakeWindow.location.pathname = '/policies/123';
      helper('Section', 'modal-ajax-form', fakeOptions);

      expect(fakeOptions.fn.calls.count()).toEqual(1);
      callArgs = fakeOptions.fn.calls.mostRecent().args;
      expect(callArgs).toEqual(expectedArgs);
    }
  );

  it('matches the "create new" modal for Section on Regulation page',
    function () {
      var callArgs;
      var expectedArgs = [templateContext];

      fakeWindow.location.pathname = '/regulations/123';
      helper('Section', 'modal-ajax-form', fakeOptions);

      expect(fakeOptions.fn.calls.count()).toEqual(1);
      callArgs = fakeOptions.fn.calls.mostRecent().args;
      expect(callArgs).toEqual(expectedArgs);
    }
  );

  it('matches the "create new" modal for Section on Standard page',
    function () {
      var callArgs;
      var expectedArgs = [templateContext];

      fakeWindow.location.pathname = '/standards/123';
      helper('Section', 'modal-ajax-form', fakeOptions);

      expect(fakeOptions.fn.calls.count()).toEqual(1);
      callArgs = fakeOptions.fn.calls.mostRecent().args;
      expect(callArgs).toEqual(expectedArgs);
    }
  );

  it('does not match the "create new" modal for Audit on non-Program page',
    function () {
      var callArgs;
      var expectedArgs = [templateContext];

      fakeWindow.location.pathname = '/assessments/123';
      helper('Audit', 'modal-ajax-form', fakeOptions);

      expect(fakeOptions.inverse.calls.count()).toEqual(1);
      callArgs = fakeOptions.inverse.calls.mostRecent().args;
      expect(callArgs).toEqual(expectedArgs);
    }
  );
});
