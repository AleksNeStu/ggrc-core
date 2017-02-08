/*!
  Copyright (C) 2017 Google Inc.
  Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

describe('GGRC.Controllers.Modals', function () {
  'use strict';

  var Ctrl;  // the controller under test

  beforeAll(function () {
    Ctrl = GGRC.Controllers.Modals;
  });

  describe('init() method', function () {
    var ctrlInst;  // fake controller instance
    var init;  // the method under tests

    beforeEach(function () {
      var html = [
        '<div>',
        '  <div class="modal-body"></div>',
        '</div>'
      ].join('');

      var $el = $(html);

      ctrlInst = {
        options: new can.Map({}),
        element: $el,
        after_preload: jasmine.createSpy()
      };

      init = Ctrl.prototype.init.bind(ctrlInst);
    });

    it('waits until current user is pre-fetched if not yet in cache',
      function () {
        var userId = GGRC.current_user.id;
        var dfdFetch = new can.Deferred();
        var fetchedUser = new can.Map({id: userId, email: 'john@doe.com'});

        spyOn(CMS.Models.Person, 'findOne').and.returnValue(dfdFetch.promise());
        delete CMS.Models.Person.cache[userId];

        init();

        expect(ctrlInst.after_preload).not.toHaveBeenCalled();
        dfdFetch.resolve(fetchedUser);
        expect(ctrlInst.after_preload).toHaveBeenCalled();
      }
    );

    it('waits until current user is pre-fetched if only partially in cache',
      function () {
        var userId = GGRC.current_user.id;
        var dfdRefresh = new can.Deferred();
        var fetchedUser = new can.Map({id: userId, email: 'john@doe.com'});

        var partialUser = new can.Map({
          id: userId,
          email: '',  // simulate user object only partially loaded
          refresh: jasmine.createSpy().and.returnValue(dfdRefresh.promise())
        });

        spyOn(partialUser, 'reify').and.returnValue(partialUser);
        CMS.Models.Person.cache[userId] = partialUser;

        init();

        expect(ctrlInst.after_preload).not.toHaveBeenCalled();
        dfdRefresh.resolve(fetchedUser);
        expect(ctrlInst.after_preload).toHaveBeenCalled();
      }
    );

    it('does not wait for fetching the current user if already in cache',
      function () {
        var dfdRefresh = new can.Deferred();
        var userId = GGRC.current_user.id;

        var fullUser = new can.Map({
          id: userId,
          email: 'john@doe.com',
          refresh: jasmine.createSpy().and.returnValue(dfdRefresh.promise())
        });

        spyOn(fullUser, 'reify').and.returnValue(fullUser);
        CMS.Models.Person.cache[userId] = fullUser;

        init();

        // after_preload should have been called immediately
        expect(ctrlInst.after_preload).toHaveBeenCalled();
      }
    );
  });
});
