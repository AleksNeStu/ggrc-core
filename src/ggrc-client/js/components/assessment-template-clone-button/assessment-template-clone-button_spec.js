/*
  Copyright (C) 2018 Google Inc.
  Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

import Component from './assessment-template-clone-button';
import {getComponentVM} from '../../../js_specs/spec_helpers';
import router from '../../router';

describe('assessment-template-clone-button component', () => {
  let events;
  let vm;

  beforeAll(() => {
    events = Component.prototype.events;
  });

  beforeEach(() => {
    vm = getComponentVM(Component);
  });

  describe('refreshTreeView() method', () => {
    let el;
    let closestSpy;

    beforeEach(() => {
      spyOn(can, 'trigger');
      spyOn(router, 'attr');
      closestSpy = jasmine.createSpy();
      el = {
        closest: closestSpy,
      };
    });

    it('triggers "refreshTree" event on closest tree-widget-container ' +
    'if there is closest tree-widget-container', () => {
      let $container = $('<div></div>');
      closestSpy.and.returnValue($container);

      vm.refreshTreeView(el);

      expect(can.trigger).toHaveBeenCalledWith($container, 'refreshTree');
    });

    it('sets "assessment_template_widget" to router with refetch flag ' +
    'if there is no closest tree-widget-container', () => {
      closestSpy.and.returnValue([]);
      vm.refreshTreeView(el);

      expect(router.attr).toHaveBeenCalledWith({
        widget: 'assessment_template_widget',
        refetch: true,
      });
    });
  });

  describe('events', () => {
    let handler;
    let vm;

    describe('"a click" handler', () => {
      beforeEach(() => {
        vm = {
          openCloneModal: jasmine.createSpy(),
        };
        handler = events['a click'].bind({viewModel: vm});
      });

      it('calls viewModel.openCloneModal method', () => {
        handler({});
        expect(vm.openCloneModal).toHaveBeenCalled();
      });
    });
  });
});
