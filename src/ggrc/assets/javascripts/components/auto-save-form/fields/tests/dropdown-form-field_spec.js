describe('GGRC.Components.dropdownFormField', function () {
  'use strict';
  var viewModel;

  beforeEach(function () {
    viewModel = GGRC.Components
      .getViewModel('dropdownFormField');
    spyOn(viewModel, 'dispatch');
    viewModel.attr('fieldId', 1);
  });

  it('does not fire valueChanged event on' +
    ' first value assignation', function () {
    viewModel.attr('value', '');
    expect(viewModel.dispatch).not.toHaveBeenCalled();
  });

  it('sets the value of the input', function () {
    viewModel.attr('value', 'test');
    expect(viewModel.attr('_value')).toEqual('test');
  });

  it('does not fire valueChanged event if value wasn\'t changed', function () {
    viewModel.attr('value', '');
    viewModel.attr('_value', 'newValue');
    viewModel.dispatch.calls.reset();
    viewModel.attr('_value', 'newValue');
    expect(viewModel.dispatch).not.toHaveBeenCalled();
  });

  it('fires valueChanged event on input value change', function () {
    viewModel.attr('value', '');
    viewModel.attr('_value', 'newValue');
    expect(viewModel.dispatch).toHaveBeenCalledWith({
      type: 'valueChanged',
      fieldId: 1,
      value: 'newValue'
    });
    viewModel.attr('_value', 'newValue2');
    expect(viewModel.dispatch).toHaveBeenCalledWith({
      type: 'valueChanged',
      fieldId: 1,
      value: 'newValue2'
    });
  });
});
