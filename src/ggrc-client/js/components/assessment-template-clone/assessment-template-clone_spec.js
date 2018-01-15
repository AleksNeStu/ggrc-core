/*
  Copyright (C) 2018 Google Inc.
  Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

import Component from './assessment-template-clone';

describe('assessment-template-clone component', () => {
  let events;

  beforeAll(() => {
    events = Component.prototype.events;
  });

  describe('viewModel() method', () => {
    let method;
    let parentViewModel;
    let attrs;
    let result;

    beforeEach(() => {
      parentViewModel = new can.Map({
        refreshTreeView: 'mock1',
      });
      method = Component.prototype.viewModel;
      attrs = {
        type: 'mockType',
        object: 'mockObject',
        join_object_id: 'mockId',
      };

      result = method(attrs, parentViewModel)();
    });

    it('returns viewModel with setted attributes', () => {
      Object.keys(attrs).forEach((key) => {
        expect(result[key]).toEqual(attrs[key]);
      });
    });

    it('sets refreshTreeView from parent view model', () => {
      expect(result.refreshTreeView).toEqual(parentViewModel.refreshTreeView);
    });
  });

  describe('events', () => {
    let handler;
    let vm;

    describe('inserted handler', () => {
      beforeEach(() => {
        vm = new can.Map({
          submitCbs: {
            fire: jasmine.createSpy(),
          },
        });
        handler = events.inserted.bind({viewModel: vm});
      });

      it('calls fire() of submitCbs attribute', () => {
        handler();
        expect(vm.submitCbs.fire).toHaveBeenCalled();
      });
    });

    describe('closeModal handler', () => {
      let el;
      let modalDismiss;

      beforeEach(() => {
        modalDismiss = {
          trigger: jasmine.createSpy(),
        };
        el = {
          find: () => modalDismiss,
        };

        handler = events.closeModal.bind({element: el});
      });

      it('triggers click event on element with "modal-dismiss" class', () => {
        handler();
        expect(modalDismiss.trigger).toHaveBeenCalledWith('click');
      });
    });

    describe('"{window} preload" handler', () => {
      let that;
      let ev;
      let $target;
      let spy;

      beforeEach(() => {
        $target = $('<div></div>');
        $('body').append($target);

        spy = spyOn($.fn, 'data');
        that = {
          closeModal: jasmine.createSpy(),
        };
        ev = {target: $target};

        handler = events['{window} preload'].bind(that);
      });

      afterEach(() => {
        $target.remove();
      });

      it('calls closeModal handler if originalTitle is ' +
      '"Define Assessment template"', () => {
        spy.and.returnValue({
          options: {
            originalTitle: 'Define Assessment template',
          },
        });
        handler({}, ev);
        expect(that.closeModal).toHaveBeenCalled();
      });

      it('does not call closeModal handler if originalTitle is nothing ' +
      '"Define Assessment template"', () => {
        spy.and.returnValue({
          options: {},
        });
        handler({}, ev);
        expect(that.closeModal).not.toHaveBeenCalled();
      });
    });

    describe('".btn-cancel click" handler', () => {
      let that;

      beforeEach(() => {
        that = {
          closeModal: jasmine.createSpy(),
        };

        handler = events['.btn-cancel click'].bind(that);
      });

      it('calls closeModal()', () => {
        handler();
        expect(that.closeModal).toHaveBeenCalled();
      });
    });

    describe('".btn-clone click" handler', () => {
      let that;
      let vm;
      let dfd;

      beforeEach(() => {
        vm = new can.Map({
          refreshTreeView: jasmine.createSpy(),
        });
        dfd = new can.Deferred();
        that = {
          viewModel: vm,
          closeModal: jasmine.createSpy(),
          cloneObjects: jasmine.createSpy().and.returnValue(dfd),
        };

        handler = events['.btn-clone click'].bind(that);
      });

      it('calls cloneObjects()', () => {
        handler();
        expect(that.cloneObjects).toHaveBeenCalled();
      });

      describe('in case of success', () => {
        beforeEach(() => {
          dfd.resolve();
        });

        it('sets false to viewModel.is_saving attribute', () => {
          that.viewModel.attr('is_saving', true);
          handler();
          expect(that.viewModel.attr('is_saving')).toBe(false);
        });

        it('calls closeModal()', () => {
          handler();
          expect(that.closeModal).toHaveBeenCalled();
        });

        it('calls viewModel.refreshTreeView()', () => {
          handler();
          expect(vm.refreshTreeView).toHaveBeenCalled();
        });
      });

      describe('in case of fail', () => {
        beforeEach(() => {
          dfd.reject();
        });

        it('sets false to viewModel.is_saving attribute', () => {
          that.viewModel.attr('is_saving', true);
          handler();
          expect(that.viewModel.attr('is_saving')).toBe(false);
        });
      });
    });

    describe('cloneObjects handler', () => {
      let vm;
      let expectedResult;

      beforeEach(() => {
        vm = new can.Map({
          selected: [{id: 1}, {id: 2}, {id: 3}],
          join_object_id: 321,
        });
        expectedResult = 'mockDfd';
        spyOn($, 'post').and.returnValue(expectedResult);
        handler = events.cloneObjects.bind({viewModel: vm});
      });

      it('sets true to viewModel.is_saving attribute', () => {
        vm.attr('is_saving', false);
        handler();
        expect(vm.attr('is_saving')).toBe(true);
      });

      it('returns response of post request for clone', () => {
        let expectedArguments = [{
          sourceObjectIds: _.map(vm.attr('selected'), (item) => item.id),
          destination: {
            type: 'Audit',
            id: vm.attr('join_object_id'),
          },
        }];
        expect(handler()).toBe(expectedResult);
        expect($.post).toHaveBeenCalledWith('/api/assessment_template/clone',
          expectedArguments);
      });
    });
  });
});
