/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, GGRC, CMS) {
  'use strict';
  var CurrentPageUtils = GGRC.Utils.CurrentPage;

  GGRC.Components('addIssueButton', {
    tag: 'add-issue-button',
    template: can.view(
      GGRC.mustache_path +
      '/components/add-issue-button/add-issue-button.mustache'
    ),
    viewModel: {
      define: {
        prepareJSON: {
          get: function () {
            var instance = this.attr('relatedInstance');
            var json = {
              assessment: {
                title: instance.title,
                id: instance.id,
                type: instance.type,
                title_singular: instance.class.title_singular,
                table_singular: instance.class.table_singular
              }
            };

            return JSON.stringify(json);
          }
        }
      },
      relatedInstance: {},
      snapshots: []
    },
    events: {
      refreshIssueList: function (window, event, instance) {
        var pageInstance;

        if (instance instanceof CMS.Models.Issue) {
          pageInstance = GGRC.page_instance();
          CurrentPageUtils.initCounts(
            ['Issue'],
            pageInstance.type,
            pageInstance.id
          );
        }

        this.viewModel.attr('relatedInstance').dispatch('refreshInstance');
      },
      '{window} modal:added': 'refreshIssueList',
      '{window} modal:success': 'refreshIssueList'
    }
  });
})(window.can, window.GGRC, window.CMS);
