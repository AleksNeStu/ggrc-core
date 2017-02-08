/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

describe('GGRC.Utils.CurrentPage', function () {
  var module = GGRC.Utils.CurrentPage;

  describe('activeTabObject() method', function () {
    var fakeWindow;
    var method;  // the method under test
    var origUtilsWin;
    var result;

    beforeAll(function () {
      method = module.activeTabObject;

      fakeWindow = {
        location: {}
      };

      origUtilsWin = GGRC.Utils.win;
      GGRC.Utils.win = fakeWindow;
    });

    afterAll(function () {
      GGRC.Utils.win = origUtilsWin;
    });

    it('returns null if no HNB tab is active', function () {
      fakeWindow.location.href = 'http://www.foo.bar/baz/123' +
                                 '?aaa=bbb#audit_widget123';
      fakeWindow.location.hash = '';

      result = method();

      expect(result).toBe(null);
    });

    it('returns null if the active tab is not associated with any object tab',
      function () {
        var hash = '#info_widget?aaa=bbb#audit_widget123';
        fakeWindow.location.href = 'http://www.foo.bar/baz/123' + hash;
        fakeWindow.location.hash = hash;

        result = method();

        expect(result).toBe(null);
      }
    );

    it('returns spaced and capitalized object type associated with the ' +
      'currently active HNB tab',
      function () {
        var hash = '#assessment_template_widget?aaa=bbb#audit_widget123';
        fakeWindow.location.href = 'http://www.foo.bar/baz/123' + hash;
        fakeWindow.location.hash = hash;

        result = method();

        expect(result).toEqual('Assessment Template');
      }
    );

    it('returns spaced and capitalized object type associated with the ' +
      'currently active HNB tab regardless of the case',
      function () {
        var hash = '#aSSessmenT_TEmpLaTe_wiDGet?aaa=bbb#audit_widget123';
        fakeWindow.location.href = 'http://www.foo.bar/baz/123' + hash;
        fakeWindow.location.hash = hash;

        result = method();

        expect(result).toEqual('Assessment Template');
      }
    );
  });
});
