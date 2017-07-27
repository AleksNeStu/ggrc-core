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
        }
      },
      formSavedDeferred: can.Deferred(),
      isUpdatingEvidences: false,
      content: {
        contextScope: {},
        fields: [],
        title: '',
        type: 'dropdown',
        value: null,
        options: []
      },
      onCommentCreated: function (e) {
        var comment = e.comment;
        var instance = this.attr('instance');
        var context = instance.attr('context');
        var relation = new CMS.Models.Relationship({
          context: context,
          destination: instance
        });
        var self = this;
        var addComment = function (data) {
          return comment.attr(data)
            .save()
            .done(function (comment) {
              relation.attr({source: comment.serialize()})
                .save()
                .then(function () {
                  self.dispatch('afterCommentCreated');
                  instance.dispatch('refreshInstance');
                });
            });
        };

        this.dispatch({
          type: 'beforeCommentCreated',
          items: [can.extend(comment.attr(), {
            assignee_type: GGRC.Utils.getAssigneeType(instance),
            custom_attribute_revision: {
              custom_attribute: {
                title: this.attr('content.title')
              },
              custom_attribute_stored_value: this.attr('content.value')
            }
          })]
        });
        this.attr('content.contextScope.errorsMap.comment', false);
        this.attr('content.contextScope.validation.valid',
          !this.attr('content.contextScope.errorsMap.evidence'));
        this.attr('content.contextScope.validation.hasMissingInfo',
          this.attr('content.contextScope.errorsMap.evidence'));
        this.attr('state.open', false);
        this.attr('state.save', false);

        this.attr('formSavedDeferred')
          .then(function () {
            addComment({
              context: context,
              assignee_type: GGRC.Utils.getAssigneeType(instance),
              custom_attribute_revision_upd: {
                custom_attribute_value: {
                  id: self.attr('content.contextScope.valueId')()
                },
                custom_attribute_definition: {
                  id: self.attr('content.contextScope.id')
                }
              }
            });
          });
      }
    }
  });
})(window.can, window.GGRC);
