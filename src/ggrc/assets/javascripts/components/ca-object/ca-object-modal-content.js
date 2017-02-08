/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, GGRC) {
  'use strict';

  var tpl = can.view(GGRC.mustache_path +
    '/components/ca-object/ca-object-modal-content.mustache');

  can.Component.extend({
    tag: 'ca-object-modal-content',
    template: tpl,
    viewModel: {
      define: {
        comment: {
          get: function () {
            return this.attr('content.fields').indexOf('comment') > -1 &&
              this.attr('state.open');
          }
        },
        evidence: {
          get: function () {
            return this.attr('content.fields').indexOf('evidence') > -1 &&
              this.attr('state.open');
          }
        },
        state: {
          value: {
            open: false,
            save: false,
            controls: false
          }
        },
        isPerson: {
          get: function () {
            return this.attr('content.value') &&
              this.attr('content.type') === 'person';
          }
        },
        actionBtnText: {
          get: function () {
            return this.attr('comment') ? 'Save' : 'Done';
          }
        }
      },
      content: {
        fields: [],
        title: null,
        value: null,
        type: null
      },
      caIds: {},
      isEmpty: true,
      saveAttachments: function () {
        return this.attr('comment') ?
          this.attr('state.save', true) :
          this.attr('state.open', false);
      }
    }
  });
})(window.can, window.GGRC);
