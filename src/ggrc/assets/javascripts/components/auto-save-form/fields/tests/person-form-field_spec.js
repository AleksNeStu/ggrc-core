describe('GGRC.Components.personFormField', function () {
  'use strict';
  var viewModel;

  beforeEach(function () {
    viewModel = GGRC.Components
      .getViewModel('personFormField');
    spyOn(viewModel, 'dispatch');
    viewModel.attr('fieldId', 1);
  });

  it('does not fire valueChanged event' +
    ' on first value assignation', function () {
    viewModel.attr('value', undefined);
    expect(viewModel.dispatch).not.toHaveBeenCalled();
  });

  it('sets the value of the input', function () {
    viewModel.attr('value', 'test');
    expect(viewModel.attr('_value')).toEqual('test');
  });

  it('does not fire valueChanged event if value wasn\'t changed', function () {
    viewModel.attr('value', {});
    viewModel.attr('_value', 1);
    viewModel.dispatch.calls.reset();
    viewModel.attr('_value', 1);
    expect(viewModel.dispatch).not.toHaveBeenCalled();
  });

  it('fires valueChanged event on input value change', function () {
    viewModel.attr('value', '');
    viewModel.attr('_value', 1);
    expect(viewModel.dispatch).toHaveBeenCalledWith({
      type: 'valueChanged',
      fieldId: 1,
      value: viewModel.attr('_value')
    });
    viewModel.attr('_value', 2);
    expect(viewModel.dispatch).toHaveBeenCalledWith({
      type: 'valueChanged',
      fieldId: 1,
      value: viewModel.attr('_value')
    });
  });

  it('unsets a person and fires valueChanged event', function () {
    viewModel.attr('value', '');
    viewModel.attr('_value', 'newValue');
    viewModel.dispatch.calls.reset();
    viewModel.unsetPerson(null, null, new Event('mock'));
    expect(viewModel.dispatch).toHaveBeenCalledWith({
      type: 'valueChanged',
      fieldId: 1,
      value: null
    });
  });
});
