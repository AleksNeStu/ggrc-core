/*
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

 import Component from '../inline-autocomplete-wrapper';

describe('GGRC.Components.inline-autocomplete-wrapper', ()=> {
  let viewModel;
  let instance;
  let path;
  beforeEach(()=> {
    instance = new can.Model.Cacheable();
    path = 'testPath';

    viewModel = new (can.Map.extend(Component.prototype.viewModel))({
      instance,
      path,
    });
  });

  describe('viewModel', ()=> {
    describe('setItem() method', ()=> {
      beforeEach(()=> {
        spyOn(viewModel, 'updateTextValue');
        spyOn(viewModel, 'updateTransient');
      });

      describe('when argument is empty', ()=> {
        it('clears value', ()=> {
          instance.attr(path, {});

          viewModel.setItem('');

          expect(instance.attr(path)).toBe(null);
        });

        it('does not update text', ()=> {
          viewModel.setItem('');
          expect(viewModel.updateTextValue).not.toHaveBeenCalled();
        });

        it('updates transient', ()=> {
          viewModel.setItem('');
          expect(viewModel.updateTransient).toHaveBeenCalled();
        });
      });

      describe('when argument is not empty', ()=> {
        describe('object', ()=> {
          let item;
          beforeEach(()=> {
            item = {
              test: true,
            };
          });

          it('updates value', ()=> {
            instance.attr(path, {});

            viewModel.setItem(item);

            expect(instance.attr(path).serialize()).toEqual(item);
          });

          it('updates text', ()=> {
            viewModel.setItem(item);

            expect(viewModel.updateTextValue).toHaveBeenCalledWith(item);
          });

          it('updates transient', ()=> {
            viewModel.setItem(item);
            expect(viewModel.updateTransient).toHaveBeenCalled();
          });
        });

        describe('string', ()=> {
          let item;
          beforeEach(()=> {
            item = 'testValue';
          });

          it('does not update value', ()=> {
            instance.attr(path, null);

            viewModel.setItem(item);

            expect(instance.attr(path)).toBe(null);
          });

          it('updates transient', ()=> {
            viewModel.setItem(item);
            expect(viewModel.updateTransient).toHaveBeenCalled();
          });
        });
      });
    });

    describe('updateTextValue() method', ()=> {
      it('sets "displayProp" value if argument is object', ()=> {
        viewModel.attr('displayProp', 'test');
        viewModel.attr('textValue', null);

        viewModel.updateTextValue(new can.Map({
          test: 'testTextValue',
        }));

        expect(viewModel.attr('textValue')).toBe('testTextValue');
      });

      it('sets argument if argument is not object', ()=> {
        viewModel.attr('textValue', null);

        viewModel.updateTextValue('testTextValue');

        expect(viewModel.attr('textValue')).toBe('testTextValue');
      });
    });

    describe('updateTransient() method', ()=> {
      it('creates "_transient" property if it not exist or empty', ()=> {
        instance.attr('_transient', null);

        viewModel.updateTransient('test');

        expect(instance.attr('_transient')).toBeTruthy();
      });

      it('set argument to "_transient" property by path', ()=> {
        instance.attr('_transient', null);

        viewModel.updateTransient('test');

        expect(instance.attr('_transient.testPath')).toBe('test');
      });
    });
  });
});
