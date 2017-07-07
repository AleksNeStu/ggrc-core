/*!
 Copyright (C) 2017 Google Inc., authors, and contributors
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, GGRC) {
  'use strict';

  var tag = 'custom-roles-modal';
  var tpl = can.view(GGRC.mustache_path +
    '/components/custom-roles/custom-roles-modal.mustache');

  GGRC.Components('customRolesModal', {
    tag: tag,
    template: tpl,
    viewModel: {
      instance: {},
      updatableGroupId: null,
      isNewInstance: false
    }
  });
})(window.can, window.GGRC);
