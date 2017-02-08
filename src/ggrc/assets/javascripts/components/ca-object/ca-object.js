/*!
 Copyright (C) 2017 Google Inc., authors, and contributors
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can) {
  'use strict';

  can.Component.extend({
    tag: 'ca-object',
    viewModel: {
      valueId: null,
      value: null,
      type: null,
      def: null,
      isSaving: false,
      addComment: function () {
        can.batch.start();
        this.attr('modal', {
          content: {
            fields: ['comment'],
            value: this.attr('value'),
            title: this.attr('def.title'),
            type: this.attr('type')
          },
          caIds: {
            defId: this.attr('def.id'),
            valueId: this.attr('valueId')
          },
          modalTitle: 'Add comment',
          state: {}
        });
        can.batch.stop();

        this.attr('modal.state.open', true);
      }
    },
    events: {
      '{viewModel} isSaving': function (scope, ev, isSaving) {
        if (isSaving) {
          this.element.trigger('saveCustomAttribute', [scope]);
        }
      }
    }
  });
})(window.can);
