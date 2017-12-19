/*!
    Copyright (C) 2017 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

import '../components/info-pin-buttons/info-pin-buttons';
import '../components/questions-link/questions-link';
import '../components/info-pane/info-pane-footer';
import '../components/assessment/info-pane/info-pane';
import '../components/folder-attachments-list/folder-attachments-list';
import '../components/unmap-button/unmap-person-button';
import '../components/issue-tracker/info-issue-tracker-fields';
import '../components/comment/comment-data-provider';
import '../components/comment/comment-add-form';
import '../components/comment/mapped-comments';
import '../components/object-list-item/document-object-list-item';
import '../components/object-list-item/editable-document-object-list-item';
import '../components/show-related-assessments-button/show-related-assessments-button';
import '../components/proposal/create-proposal-button';
import '../components/related-objects/proposals/related-proposals';
import '../components/related-objects/proposals/related-proposals-item';
import '../components/unarchive_link';
import '../components/sort/sort-by';
import * as TreeViewUtils from '../plugins/utils/tree-view-utils';
import {confirm} from '../plugins/utils/modals';

export default can.Control({
  pluginName: 'cms_controllers_info_pin',
  defaults: {
    view: GGRC.mustache_path + '/base_objects/info.mustache'
  }
}, {
  init: function (el, options) {
    this.element.height(0);
  },
  isPinVisible() {
    const height = this.element.height();
    return height > 0;
  },
  findView: function (instance) {
    var view = instance.class.table_plural + '/info';

    if (instance instanceof CMS.Models.Person) {
      view = GGRC.mustache_path +
        '/people_roles/info.mustache';
    } else if (view in GGRC.Templates) {
      view = GGRC.mustache_path + '/' + view + '.mustache';
    } else {
      view = this.options.view;
    }
    return view;
  },
  findOptions: function (el) {
    var options;
    var treeNode = el.closest('.cms_controllers_tree_view_node');

    if (treeNode.length) {
      options = treeNode.control().options;
    } else {
      options = el.closest('.tree-item-element').viewModel();
    }
    return options;
  },
  getPinHeight: function (maximizedState) {
    if (maximizedState) {
      return Math.floor($(window).height() * 3 / 4);
    }
    return Math.floor($(window).height() / 3);
  },
  hideInstance: function () {
    this.unsetInstance();
    $(window).trigger('resize');
  },
  unsetInstance: function () {
    this.element
      .css({
        height: 0,
        'z-index': -1,
        opacity: 0
      })
      .html('');
  },
  setHtml: function (opts, view, confirmEdit, options, maximizedState) {
    var instance = opts.attr('instance');
    var parentInstance = opts.attr('parent_instance');
    var self = this;
    import(/* webpackChunkName: "modalsCtrls" */'./modals')
      .then(() => {
        this.element.html(can.view(view, {
          instance: instance,
          isSnapshot: !!instance.snapshot || instance.isRevision,
          parentInstance: parentInstance,
          model: instance.class,
          confirmEdit: confirmEdit,
          is_info_pin: true,
          options: options,
          result: options.result,
          page_instance: GGRC.page_instance(),
          maximized: maximizedState,
          onChangeMaximizedState: function () {
            return self.changeMaximizedState.bind(self);
          },
          onClose: function () {
            return self.close.bind(self);
          }
        }));
      });
  },
  prepareView: function (opts, el, maximizedState, setHtml) {
    var instance = opts.attr('instance');
    var options = this.findOptions(el);
    var populatedOpts = opts.attr('options');
    var confirmEdit = instance.class.confirmEditModal ?
      instance.class.confirmEditModal : {};
    var view = this.findView(instance);
    instance.attr('view', view);

    if (populatedOpts && !options.attr('result')) {
      options = populatedOpts;
    }

    if (!_.isEmpty(confirmEdit)) {
      confirmEdit.confirm = this.confirmEdit;
    }

    if (setHtml) {
      this.setHtml(opts, view, confirmEdit, options, maximizedState);
    }
  },
  setInstance: function (opts, el, maximizedState) {
    var instance = opts.attr('instance');
    var panelHeight = this.getPinHeight(maximizedState);
    var currentPanelHeight;
    var infoPaneOpenDfd = can.Deferred();
    var isSubtreeItem = opts.attr('options.isSubTreeItem');

    opts.attr('options.isDirectlyRelated',
      !isSubtreeItem ||
      TreeViewUtils.isDirectlyRelated(instance));

    this.prepareView(opts, el, maximizedState, true);

    if (instance.info_pane_preload) {
      instance.info_pane_preload();
    }

    // Make sure pin is visible
    currentPanelHeight = this.element.height();
    if (!currentPanelHeight || currentPanelHeight !== panelHeight) {
      this.element.css('height', this.getPinHeight(true));
    } else {
      this.ensureElementVisible(el);
    }

    this.element.css('z-index', 1);
    this.element.css('opacity', 1);

    // Temporary solution...
    setTimeout(infoPaneOpenDfd.resolve, 1000);

    this.element.trigger('scroll');
    return infoPaneOpenDfd;
  },
  updateInstance: function (selector, instance) {
    var vm = this.element.find(selector).viewModel();

    vm.attr('instance', instance);
    vm.attr('instance').dispatch({
      type: 'update'
    });
  },
  setLoadingIndicator: function (selector, isLoading) {
    this.element.toggleClass('loading');

    this.element.find(selector)
      .viewModel()
      .attr('isLoading', isLoading);
  },
  ensureElementVisible: function (el) {
    var $objectArea;
    var $header;
    var $filter;
    var elTop;
    var elBottom;
    var headerTop;
    var headerBottom;
    var infoTop;

    $(window).trigger('resize');
    $objectArea = $('.object-area');
    $header = $('.tree-header:visible');
    $filter = $('.tree-filter:visible');

    if (_.isEmpty(el) || _.isEmpty($header)) {
      return;
    }

    elTop = el.offset().top;
    elBottom = elTop + el.height();

    headerTop = $header.offset().top;
    headerBottom = headerTop + $header.height();
    infoTop = this.element.offset().top;

    if (elTop < headerBottom || elBottom > infoTop) {
      el[0].scrollIntoView(false);
      if (elTop < headerBottom) {
        el[0].scrollIntoView(true);
        $objectArea.scrollTop(
          $objectArea.scrollTop() - $header.height() - $filter.height());
      } else {
        el[0].scrollIntoView(false);
      }
    }
  },
  confirmEdit: function (instance, modalDetails) {
    var confirmDfd = $.Deferred();
    var renderer = can.view.mustache(modalDetails.description);
    confirm({
      modal_description: renderer(instance).textContent,
      modal_confirm: modalDetails.button,
      modal_title: modalDetails.title,
      button_view: GGRC.mustache_path + '/quick_form/confirm_buttons.mustache'
    }, confirmDfd.resolve);
    return confirmDfd;
  },
  changeMaximizedState: function (maximizedState) {
    var $activeTree = $('.cms_controllers_tree_view_node.active');
    var size = this.getPinHeight(maximizedState);

    this.element.css('height', size);

    if (maximizedState) {
      $activeTree
        .addClass('maximized-info-pane');
    } else {
      $activeTree
        .removeClass('maximized-info-pane');
    }
  },
  close: function () {
    var visibleWidget = $('.widget-area .widget:visible');
    var element = visibleWidget.find('.cms_controllers_tree_view');

    if (element.length) {
      element.control().deselect();
    } else {
      visibleWidget.find('.item-active')
        .removeClass('item-active');
    }

    this.unsetInstance();
  },
  /**
   * Checks if there are modals on top of the info pane.
   * @return {boolean} - true if there are modals on top of the info pane else
   *  false.
   */
  existModals() {
    return (
      $('.modal:visible').length > 0 ||
      $('[role=dialog]:visible').length > 0
    );
  },
  /**
   * Checks if $target is an element wherein shouldn't be closed the info pane
   * with help the escape key.
   * @param {jQuery} $target - an jQuery element.
   * @return {boolean} - true if the escape key shouldn't be processed
   *  otherwise false.
   */
  isEscapeKeyException($target) {
    const insideInfoPane = $target.closest('.pin-content').length > 0;
    const excludeForEscapeKey = ['button', '[role=button]', '.btn', 'input',
      'textarea'];
    const isExcludingControl = _.any(excludeForEscapeKey, (typeName) =>
      $target.is(typeName)
    );
    return (
      insideInfoPane &&
      (
        isExcludingControl ||
        $target.attr('contentEditable') === 'true'
      )
    );
  },
  ' scroll': function (el, ev) {
    var header = this.element.find('.pane-header');
    var isFixed = el.scrollTop() > 0;
    var offset = isFixed ? header.height() : 0;
    var HEADER_PADDING = -15;

    this.element.find('.tier-content').css('paddingTop', offset);
    header.css('marginTop', function () {
      // Header in info pane is padded by 15px, and we need to make sure
      // text doesn't bleed below.
      return HEADER_PADDING - offset;
    });
    header.toggleClass('pane-header__fixed', isFixed);
  },
  '{window} keyup'(el, event) {
    const ESCAPE_KEY_CODE = 27;
    const $target = $(event.target);
    const escapeKeyWasPressed = event.keyCode === ESCAPE_KEY_CODE;

    const close = (
      escapeKeyWasPressed &&
      this.isPinVisible() &&
      !this.existModals() &&
      !this.isEscapeKeyException($target)
    );

    if (close) {
      this.close();
      event.stopPropagation();
    }
  },
});
