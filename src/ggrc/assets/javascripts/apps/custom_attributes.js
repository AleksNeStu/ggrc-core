/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, GGRC) {
  'use strict';

  GGRC.Components('customAttributes', {
    tag: 'custom-attributes',
    template: '<content/>',
    scope: {
      instance: null,
      items: [],
      setItems: function (isReady) {
        var values = [];
        if (isReady) {
          values = this.getValues().sort(function (a, b) {
            return a.cad.id - b.cad.id;
          });
          this.attr('items', values);
        }
      },
      getValues: function () {
        var result = [];

        can.each(this.attr('instance.custom_attribute_definitions'),
          function (cad) {
            var cav;
            var type = cad.attribute_type;
            can.each(this.attr('instance.custom_attribute_values'),
              function (val) {
                val = val.isStub ? val : val.reify();
                if (val.custom_attribute_id === cad.id) {
                  cav = val;
                }
              });
            result.push({
              cav: cav,
              cad: {
                id: cad.id,
                attribute_type: cad.attribute_type,
                mandatory: cad.mandatory,
                title: cad.title,
                label: cad.label,
                placeholder: cad.placeholder,
                helptext: cad.helptext,
                multi_choice_options: cad.multi_choice_options
              },
              type: GGRC.Utils.mapCAType(type)
            });
          }.bind(this));
        return result;
      }
    },
    init: function () {
      if (this.scope.instance.class.is_custom_attributable) {
        this.scope.instance.setup_custom_attributes();
      }
      this.scope.setItems(true);
    },
    events: {
      '{scope.instance} isReadyForRender': function (sc, ev, isReady) {
        this.scope.setItems(isReady);
      }
    }
  });
})(window.can, window.GGRC);
