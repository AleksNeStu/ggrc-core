/*
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

/**
 * The component is used to integrate separate autocomplete component
 * with some old pards of code which are working with autocomplete plugin
 * and controllers.
 * 
 * Generally it emulates autocomplete_select handlers from several controllers.
 */
export default GGRC.Components('inlineAutocompleteWrapper', {
  tag: 'inline-autocomplete-wrapper',
  viewModel: {
    /**
     * Contains a model.
     * @type {Can.Map}
     */
    instance: null,
    /**
     * Contains path to set object from autocomplete to instance.
     * @type {String}
     */
    path: '',
    /**
     * Contains a propery name that should be displayed in input after user
     * selects an item in autocomplete.
     * @type {String}
     */
    displayProp: '',
    /**
     * Contains value that should be displayed in autocomplete input.
     */
    textValue: '',
    /**
     * Applies user's input.
     * @param {Can.Map|String} item - The item picked in autocomplete or string pasted by user.
     */
    setItem(item) {
      let instance = this.attr('instance');
      let path = this.attr('path');

      if (_.isEmpty(item)) {
        instance.attr(path, null);
      } else if (_.isObject(item)) {
        instance.attr(path, item);
        this.updateTextValue(item);
      }

      this.updateTransient(item);
    },
    /**
     * Updates text displayed in autocomplete input.
     * @param {Can.Map|String} item - The item picked in autocomplete or any string.
     */
    updateTextValue(item) {
      let text = _.isObject(item) ? item.attr(this.attr('displayProp')) : item;
      this.attr('textValue', text);
    },
    /**
     * Updates '_transient' property in instance.
     * It used for change detection.
     * @param {*} value - the new property value.
     */
    updateTransient(value) {
      let instance = this.attr('instance');
      let path = this.attr('path');
      if (!instance.attr('_transient')) {
        instance.attr('_transient', can.Map());
      }
      instance.attr('_transient.' + path, value);
    },
  },
});
