/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

'use strict';

describe('GGRC.Errors module', function () {
  var notifier;
  var $fake;
  var _originalMessages;

  beforeAll(function () {
    _originalMessages = _.assign({}, GGRC.Errors.messages);

    GGRC.Errors.messages = {
      'default': 'Some error!',
      '401': 'Mock auth invalid message'
    };

    $fake = {
      trigger: jasmine.createSpy()
    };
  });

  afterAll(function () {
    GGRC.Errors.messages = _originalMessages;
  });

  beforeEach(function () {
    spyOn(window, '$').and.returnValue($fake);
  });

  afterEach(function () {
    expect(window.$).toHaveBeenCalledWith('body');
    expect($fake.trigger.calls.count()).toEqual(1);
    $fake.trigger.calls.reset();
  });

  describe('notifier method', function () {
    beforeAll(function () {
      notifier = GGRC.Errors.notifier;
    });

    describe('returns default message', function () {
      describe('and warning type', function () {
        it('if all parameters empty', function () {
          notifier();
          expect($fake.trigger).toHaveBeenCalledWith('ajax:flash',
            {warning: 'Some error!'});
        });
      });

      describe('and error type', function () {
        it('and error type', function () {
          notifier('error');

          expect($fake.trigger).toHaveBeenCalledWith('ajax:flash',
            {error: 'Some error!'});
        });
      });
    });
  });

  describe('notifierXHR method', function () {
    beforeAll(function () {
      notifier = GGRC.Errors.notifierXHR;
    });

    describe('returns default message', function () {
      describe('and warning type', function () {
        it('for unknown errors', function () {
          notifier()({status: 666});

          expect($fake.trigger).toHaveBeenCalledWith('ajax:flash',
            {warning: 'Some error!'});
        });
      });

      describe('and error type', function () {
        it('for unknown errors', function () {
          notifier('error')({status: 666});

          expect($fake.trigger).toHaveBeenCalledWith('ajax:flash',
            {error: 'Some error!'});
        });
      });
    });

    describe('returns standard message by error code', function () {
      it('for 401 status', function () {
        notifier('error')({status: 401});

        expect($fake.trigger).toHaveBeenCalledWith('ajax:flash',
          {error: 'Mock auth invalid message'});
      });
    });

    describe('returns passed message', function () {
      it('for defined error statuses', function () {
        notifier('error', 'Fake message')({status: 403});

        expect($fake.trigger).toHaveBeenCalledWith('ajax:flash',
          {error: 'Fake message'});
      });
    });
  });
});
