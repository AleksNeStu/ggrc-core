/*!
  Copyright (C) 2017 Google Inc.
  Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

describe('GGRC.Components.personItem', function () {
  'use strict';

  var Component; // the component under test

  beforeAll(function () {
    Component = GGRC.Components.get('personItem');
  });

  describe('defining default scope values', function () {
    var viewModel; // the viewModel under test

    beforeAll(function () {
      viewModel = GGRC.Components.getViewModel('personItem');
    });

    it('sets the personObj to null', function () {
      expect(viewModel.attr('personObj')).toBeNull();
    });
  });

  describe('init() method', function () {
    var dfdFindOne;
    var template;  // the DOM element passed to the component instance
    var component;
    var frag;

    beforeEach(function () {
      dfdFindOne = new can.Deferred();
      spyOn(RefreshQueue.prototype, 'trigger').and.returnValue(dfdFindOne);
    });

    afterEach(function () {
      CMS.Models.Person.cache = {};
    });

    it('sets the personObj in scope to the cached Person object ' +
      'if found there',
      function () {
        var person42 = new CMS.Models.Person({
          id: 42, name: 'John', email: 'john@doe.com'
        });

        template = can.view
          .mustache('<person-info person-id="42"></person-info>');
        frag = template();
        frag = $(frag);
        component = frag.find('person-info').control();

        expect(component.scope.attr('personObj'))
          .toBe(person42);
      }
    );

    it('sets the personObj in scope to the fetched Person object ' +
      'if not found in cache',
      function () {
        var person123 = new can.Map({
          id: 123, name: 'Mike', email: 'mike@mike.com'
        });

        template = can.view
          .mustache('<person-info person-id="123"></person-info>');
        frag = template();

        frag = $(frag);
        component = frag.find('person-info').control();

        delete CMS.Models.Person.cache[123];

        dfdFindOne.resolve(person123);

        expect(RefreshQueue.prototype.trigger).toHaveBeenCalled();
        expect(component.scope.attr('personObj')).toBe(person123);
      }
    );

    it('sets the personObj in scope to the fetched Person object ' +
      'for partially loaded objects in cache',
      function () {
        var person123 = new can.Map({id: 123, name: '', email: ''});
        var fetchedPerson = new can.Map({
          id: 123, name: 'John', email: 'john@doe.com'
        });

        template = can.view
          .mustache('<person-info person-id="123"></person-info>');
        frag = template();

        CMS.Models.Person.cache[123] = person123;

        frag = $(frag);
        component = frag.find('person-info').control();

        dfdFindOne.resolve(fetchedPerson);

        expect(RefreshQueue.prototype.trigger).toHaveBeenCalled();
        expect(component.scope.attr('personObj')).toBe(fetchedPerson);
      }
    );
    it('does not make a get request when person-id is undefined',
      function () {
        spyOn(console, 'warn');
        template = can.view
          .mustache('<person-info person-id=""></person-info>');
        frag = template();

        frag = $(frag);
        component = frag.find('person-info').control();

        expect(RefreshQueue.prototype.trigger).not.toHaveBeenCalled();
        expect(console.warn).toHaveBeenCalled();
      }
    );
    it('gets stub from cache and then makes a request', function () {
      var person123 = new CMS.Models.Person({
        id: 123, name: '', type: 'Person'
      });

      template = can.view
        .mustache('<person-info person-obj="person"></person-info>');
      frag = template({
        person: person123
      });
      frag = $(frag);
      component = frag.find('person-info').control();

      expect(RefreshQueue.prototype.trigger).toHaveBeenCalled();
    });
    it('gets person object from and doesn\'t make a request', function () {
      var personObj = new can.Map({
        id: 123, name: '', type: 'Person'
      });
      new CMS.Models.Person({
        id: 123, name: 'Ivan', email: 'ivan@google.com', type: 'Person'
      });

      template = can.view
        .mustache('<person-info person-obj="person"></person-info>');
      frag = template({
        person: personObj
      });
      frag = $(frag);
      component = frag.find('person-info').control();

      expect(component.scope.attr('personObj'))
          .toBe(CMS.Models.Person.cache['123']);
      expect(RefreshQueue.prototype.trigger).not.toHaveBeenCalled();
    });
    it('gets person object from context and it doesn\'t trigger ' +
       'the RefreshQueue', function () {
      var personObj = new CMS.Models.Person({
        id: 123, name: 'Ivan', email: 'ivan@google.com', type: 'Person'
      });

      template = can.view
        .mustache('<person-info person-obj="person"></person-info>');
      frag = template({
        person: personObj
      });
      frag = $(frag);
      component = frag.find('person-info').control();

      expect(component.scope.attr('personObj'))
          .toBe(CMS.Models.Person.cache['123']);
      expect(RefreshQueue.prototype.trigger).not.toHaveBeenCalled();
    });
  });

  describe('unmap person click event handler', function () {
    var handler;  // the event handler under test
    var componentInst;  // fake component instance

    beforeEach(function () {
      componentInst = {
        element: {
          triggerHandler: jasmine.createSpy()
        },
        scope: new can.Map()
      };
      componentInst.viewModel = componentInst.scope;

      handler = Component.prototype.events['a.unmap click'].bind(componentInst);
    });

    it('triggers the person-remove event with the person object as the ' +
      'event argument',
      function () {
        var call;
        componentInst.scope.attr('personObj', {id: 123, name: 'John'});

        handler();

        expect(componentInst.element.triggerHandler).toHaveBeenCalled();
        call = componentInst.element.triggerHandler.calls.mostRecent();
        expect(call.args[0].type).toEqual(
          Component.prototype._EV_REMOVE_CLICK);
        expect(call.args[0].person.attr()).toEqual({id: 123, name: 'John'});
      }
    );

    it('emits the person-remove event using the dispatch mechanism',
      function () {
        var call;
        componentInst.viewModel.attr('personObj', {id: 123, name: 'John'});
        spyOn(componentInst.viewModel, 'dispatch');

        handler();

        expect(componentInst.viewModel.dispatch).toHaveBeenCalled();
        call = componentInst.viewModel.dispatch.calls.mostRecent();
        expect(call.args[0].type).toEqual('personRemove');
        expect(call.args[0].person.attr()).toEqual({id: 123, name: 'John'});
      }
    );
  });
});
