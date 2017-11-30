/*!
    Copyright (C) 2017 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

import Spinner from 'spin.js';
import {
  warning,
  BUTTON_VIEW_SAVE_CANCEL_DELETE,
  BUTTON_CREATE_PROPOSAL,
} from '../plugins/utils/modals';
import {
  hasWarningType,
  shouldApplyPreconditions,
} from '../plugins/utils/controllers';
import Permission from '../permission';

(function (can, $, GGRC) {
  'use strict';

  var originalModalShow = $.fn.modal.Constructor.prototype.show;
  var originalModalHide = $.fn.modal.Constructor.prototype.hide;

  var handlers = {
    modal: function ($target, $trigger, option) {
      $target.modal(option).draggable({handle: '.modal-header'});
    },

    deleteform: function ($target, $trigger, option) {
      var model = CMS.Models[$trigger.attr('data-object-singular')];
      var instance;
      var deleteCounts = new can.Map({loading: true, counts: ''});
      var modalSettings;

      if ($trigger.attr('data-object-id') === 'page') {
        instance = GGRC.page_instance();
      } else {
        instance = model.findInCacheById($trigger.attr('data-object-id'));
      }

      instance.get_orphaned_count().done(function (counts) {
        deleteCounts.attr('loading', false);
        deleteCounts.attr('counts', counts);
      }).fail(function () {
        deleteCounts.attr('loading', false);
      });

      modalSettings = {
        $trigger: $trigger,
        skip_refresh: !$trigger.data('refresh'),
        new_object_form: false,
        button_view:
          GGRC.mustache_path + '/modals/delete_cancel_buttons.mustache',
        model: model,
        instance: instance,
        delete_counts: deleteCounts,
        modal_title: 'Delete ' + $trigger.attr('data-object-singular'),
        content_view:
          GGRC.mustache_path + '/base_objects/confirm_delete.mustache'
      };

      if (hasWarningType(instance)) {
        modalSettings = _.extend(
          modalSettings,
          warning.settings,
          {
            objectShortInfo: [instance.type, instance.title].join(' '),
            confirmOperationName: 'delete',
            operation: 'deletion'
          }
        );
      }

      warning(
        modalSettings,
        _.constant({}),
        _.constant({}), {
          controller: $target
            .modal_form(option, $trigger)
            .ggrc_controllers_delete.bind($target)
        });

      $target.on('modal:success', function (e, data) {
        var modelName = $trigger.attr('data-object-plural').toLowerCase();
        if ($trigger.attr('data-object-id') === 'page' ||
          (instance === GGRC.page_instance())) {
          GGRC.navigate('/dashboard');
        } else if (modelName === 'people' || modelName === 'roles') {
          window.location.assign('/admin#' + modelName + '_list_widget');
          GGRC.navigate();
        } else {
          $trigger.trigger('modal:success', data);
          $target.modal_form('hide');
        }
      });
    },

    unmapform: function ($target, $trigger, option) {
      var objectParams = $trigger.attr('data-object-params');
      var model = CMS.Models[$trigger.attr('data-object-singular')];
      var instance;
      if ($trigger.attr('data-object-id') === 'page') {
        instance = GGRC.page_instance();
      } else {
        instance = model.findInCacheById($trigger.attr('data-object-id'));
      }
      objectParams = objectParams ?
        JSON.parse(objectParams.replace(/\\n/g, '\n')) :
        {};

      $target
        .modal_form(option, $trigger)
        .ggrc_controllers_unmap({
          $trigger: $trigger,
          new_object_form: false,
          button_view: GGRC.mustache_path +
            '/modals/unmap_cancel_buttons.mustache',
          model: model,
          instance: instance,
          object_params: objectParams,
          modal_title: $trigger.attr('data-modal-title') ||
            ('Delete ' + $trigger.attr('data-object-singular')),
          content_view: $trigger.attr('data-content-view') ||
            (GGRC.mustache_path + '/base_objects/confirm_unmap.mustache')
        });

      $target.on('modal:success', function () {
        $trigger.children('.result').each(function (i, resultEl) {
          var $resultEl = $(resultEl);
          var result = $resultEl.data('result');
          var mappings = result && result.get_mappings();

          can.each(mappings, function (mapping) {
            mapping.refresh().done(function () {
              if (mapping instanceof CMS.Models.Control) {
                mapping.removeAttr('directive');
                mapping.save();
              } else {
                mapping.destroy();
              }
            });
          });
        });
      });
    },

    form: function ($target, $trigger, option) {
      var formTarget = $trigger.data('form-target');
      var objectParams = $trigger.attr('data-object-params');
      var triggerParent = $trigger.closest('.add-button');
      var model = CMS.Models[$trigger.attr('data-object-singular')] ||
        CMS.ModelHelpers[$trigger.attr('data-object-singular')];
      var mapping = $trigger.data('mapping');
      var isProposal = $trigger.data('is-proposal');
      var instance;
      var modalTitle;
      var titleOverride;
      var contentView;

      if ($trigger.attr('data-object-id') === 'page') {
        instance = GGRC.page_instance();
      } else {
        instance = model.findInCacheById($trigger.attr('data-object-id'));
      }

      objectParams = objectParams ? JSON.parse(objectParams) : {};

      modalTitle =
        (instance ? 'Edit ' : 'New ') +
        ($trigger.attr('data-object-singular-override') ||
        model.title_singular ||
        $trigger.attr('data-object-singular'));
      // If this was initiated via quick join link
      if (objectParams.section) {
        modalTitle = 'Map ' + modalTitle + ' to ' + objectParams.section.title;
      }
      titleOverride = $trigger.attr('data-modal-title-override');
      if (titleOverride) {
        modalTitle = titleOverride;
      }
      if (isProposal) {
        modalTitle = `Proposal for ${model.title_singular}`;
      }

      contentView = $trigger.data('template') ||
        GGRC.mustache_path + '/' +
        $trigger.attr('data-object-plural') +
        '/modal_content.mustache';

      $target
        .modal_form(option, $trigger)
        .ggrc_controllers_modals({
          new_object_form: !$trigger.attr('data-object-id'),
          object_params: objectParams,
          button_view: isProposal ?
            BUTTON_CREATE_PROPOSAL :
            BUTTON_VIEW_SAVE_CANCEL_DELETE,
          model: model,
          oldData: {
            status: instance && instance.status // status before changing
          },
          applyPreconditions:
            shouldApplyPreconditions(instance),
          current_user: GGRC.current_user,
          instance: instance,
          modal_title: objectParams.modal_title || modalTitle,
          content_view: contentView,
          mapping: mapping,
          isProposal: isProposal,
          $trigger: $trigger
        });

      $target.on('modal:success', function (e, data, xhr) {
        var dirty;
        var $active;
        var WARN_MSG = [
          'The $trigger element was not found in the DOM, thus some',
          'application events will not be propagated.'
        ].join(' ');
        var args = arguments;

        if (formTarget === 'refresh') {
          refreshPage();
        } else if (formTarget === 'redirect') {
          if (typeof xhr !== 'undefined' && 'getResponseHeader' in xhr) {
            GGRC.navigate(xhr.getResponseHeader('location'));
          } else if (data._redirect) {
            GGRC.navigate(data._redirect);
          } else {
            GGRC.navigate(data.selfLink.replace('/api', ''));
          }
        } else if (formTarget === 'refresh_page_instance') {
          GGRC.page_instance().refresh();
        } else {
          $target.modal_form('hide');
          if ($trigger.data('dirty')) {
            dirty = $($trigger.data('dirty').split(',')).map(function (i, val) {
              return '[href="' + val.trim() + '"]';
            }).get().join(',');
            $(dirty).data('tab-loaded', false);
          }
          if (dirty) {
            $active = $(dirty).filter('.active [href]');
            $active.closest('.active').removeClass('active');
            $active.click();
          }

          // For some reason it can happen that the original $trigger element
          // is removed from the DOM and replaced with another identical
          // element. We thus need to trigger the event on that new element
          // (present in the DOM) if we want event handlers to be invoked.
          if (!document.contains($trigger[0])) {
            $trigger = $('[data-link-purpose="open-edit-modal"]');
            if (_.isEmpty($trigger)) {
              console.warn(WARN_MSG);
              return;
            }
          }

          $trigger.trigger('routeparam', $trigger.data('route'));

          if (triggerParent && triggerParent.length) {
            $trigger = triggerParent;
          }

          Permission.refresh().then(function () {
            var hiddenElement;
            var tagName;

            // 'is_allowed' helper rerenders an elements
            // we should trigger event for hidden element
            if (!$trigger.is(':visible') && option.uniqueId &&
              $trigger.context) {
              tagName = $trigger.context.tagName;

              hiddenElement =
                $(tagName + "[data-unique-id='" + option.uniqueId + "']");

              if (hiddenElement) {
                $trigger = hiddenElement;
              }
            }

            $trigger.trigger(
              'modal:success', Array.prototype.slice.call(args, 1)
            );
          });
        }
      });
    },

    helpform: function ($target, $trigger, option) {
      $target
        .modal_form(option, $trigger)
        .ggrc_controllers_help({slug: $trigger.attr('data-help-slug')});
    },

    archiveform: function ($target, $trigger, option) {
      var model = CMS.Models[$trigger.attr('data-object-singular')];
      var instance;

      if ($trigger.attr('data-object-id') === 'page') {
        instance = GGRC.page_instance();
      } else {
        instance = model.findInCacheById($trigger.attr('data-object-id'));
      }

      $target
        .modal_form(option, $trigger)
        .ggrc_controllers_toggle_archive({
          $trigger: $trigger,
          new_object_form: false,
          button_view: GGRC.mustache_path +
          '/modals/archive_cancel_buttons.mustache',
          model: model,
          instance: instance,
          modal_title: 'Archive ' + $trigger.attr('data-object-singular'),
          content_view: GGRC.mustache_path +
          '/base_objects/confirm_archive.mustache'
        });

      $target.on('modal:success', function (e, data) {
        $trigger.trigger('modal:success', data);
        $target.modal_form('hide');
      });
    }
  };

  function preloadContent() {
    var template =
      ['<div class="modal-header">',
        '<a class="pull-right modal-dismiss" href="#" data-dismiss="modal">',
        '<i class="fa fa-times black"></i>',
        '</a>',
        '<h2>Loading...</h2>',
        '</div>',
        '<div class="modal-body" style="padding-top:150px;"></div>',
        '<div class="modal-footer">',
        '</div>'
      ];
    return $(template.join('\n'))
      .filter('.modal-body')
      .html(
        $(new Spinner().spin().el)
          .css({
            width: '100px', height: '100px',
            left: '50%', top: '50%',
            zIndex: calculate_spinner_z_index
          })
      ).end();
  }

  function emitLoaded(responseText, textStatus, xhr) {
    if (xhr.status === 403) {
      // For now, only inject the response HTML in the case
      // of an authorization error
      $(this).html(responseText);
    }
    $(this).trigger('loaded');
  }

  function refreshPage() {
    setTimeout(GGRC.navigate.bind(GGRC), 10);
  }

  function arrangeBackgroundModals(modals, referenceModal) {
    var $header;
    var headerHeight;
    var _top;
    modals = $(modals).not(referenceModal);
    if (modals.length < 1) return;

    $header = referenceModal.find('.modal-header');
    headerHeight = $header.height() +
      Number($header.css('padding-top')) +
      Number($header.css('padding-bottom'));
    _top = Number($(referenceModal).offset().top);

    modals.css({
      overflow: 'hidden',
      height: function () {
        return headerHeight;
      },
      top: function (i) {
        return _top - (modals.length - i) * (headerHeight);
      },
      'margin-top': 0,
      position: 'absolute'
    });
    modals.off('scroll.modalajax');
  }

  function arrangeTopModal(modal) {
    var $header = modal.find('.modal-header:first');
    var headerHeight = $header.height() +
      Number($header.css('padding-top')) +
      Number($header.css('padding-bottom'));

    var offsetParent = modal.offsetParent();
    var _scrollY = 0;
    var _top = 0;
    var _left = modal.position().left;
    if (!offsetParent.length || offsetParent.is('html, body')) {
      offsetParent = $(window);
      _scrollY = window.scrollY;
      _top = _scrollY +
        (offsetParent.height() -
        modal.height()) / 5 +
        headerHeight / 5;
    } else {
      _top = offsetParent.closest('.modal').offset().top -
        offsetParent.offset().top + headerHeight;
      _left = offsetParent.closest('.modal').offset().left +
        offsetParent.closest('.modal').width() / 2 -
        offsetParent.offset().left;
    }
    if (_top < 0) {
      _top = 0;
    }
    modal
      .css('top', _top + 'px')
      .css({position: 'absolute', 'margin-top': 0, left: _left});
  }

  function reconfigureModals() {
    var modalBackdrops = $('.modal-backdrop').css('z-index', function (i) {
      return 2990 + i * 20;
    });

    var modals = $('.modal:visible');
    modals.each(function (i) {
      var parent = this.parentNode;
      if (parent !== document.body) {
        modalBackdrops
          .eq(i)
          .detach()
          .appendTo(parent);
      }
    });
    modalBackdrops.slice(modals.length).remove();

    modals.not(this.$element).css('z-index', function (i) {
      return 3000 + i * 20;
    });
    this.$element.css('z-index', 3000 + (modals.length - 1) * 20);
    if (this.$element.length) {
      arrangeTopModal(this.$element);
    }
    arrangeBackgroundModals(modals, this.$element);
  }

  $.fn.modal.Constructor.prototype.show = function () {
    var that = this;
    var $el = this.$element;
    var shownevents;
    var keyevents;
    if (!(shownevents = $._data($el[0], 'events').shown) ||
      $(shownevents).filter(function () {
        return $.inArray('arrange', this.namespace.split('.')) > -1;
      }).length < 1) {
      $el.on('shown.arrange, loaded.arrange', function (ev) {
        if (ev.target === ev.currentTarget)
          reconfigureModals.call(that);
      });
    }

    if ($el.is('body > * *')) {
      this.$cloneEl = $('<div>').appendTo($el.parent());
      can.each($el[0].attributes, function (attr) {
        that.$cloneEl.attr(attr.name, attr.value);
      });
      $el.find('*').uniqueId();
      this.$cloneEl.html($el.html());
      $el.detach().appendTo(document.body);
      this.$cloneEl
        .removeAttr('id')
        .find('*')
        .attr('data-original-id', function () {
          return this.id;
        })
        .removeAttr('id');

      $el.on(['click',
          'mouseup',
          'keypress',
          'keydown',
          'keyup',
          'show',
          'shown',
          'hide',
          'hidden']
          .join('.clone ') + '.clone', function (e) {
        return that.$cloneEl ?
          that.$cloneEl
            .find("[data-original-id='" + e.target.id + "']")
            .trigger(new $.Event(e)) :
          $el.off('.clone');
      });
    }

    // prevent form submissions when descendant elements are also modals.
    if (!(keyevents = $._data($el[0], 'events').keypress) ||
      $(keyevents).filter(function () {
        return $.inArray('preventdoublesubmit', this.namespace.split('.')) > -1;
      }).length < 1) {
      $el.on('keypress.preventdoublesubmit', function (ev) {
        if (ev.which === 13 &&
          !$(document.activeElement).hasClass('wysihtml5') &&
          !$(document.activeElement).hasClass('create-form__input') &&
          !$(document.activeElement).parents('.pagination').length
        ) {
          ev.preventDefault();
          if (ev.originalEvent) {
            ev.originalEvent.preventDefault();
          }
          return false;
        }
      });
    }
    if (!(keyevents = $._data($el[0], 'events').keyup) ||
      $(keyevents).filter(function () {
        return $.inArray('preventdoubleescape', this.namespace.split('.')) > -1;
      }).length < 1) {
      $el.on('keyup.preventdoubleescape', function (ev) {
        if (ev.which === 27 && $(ev.target).closest('.modal').length) {
          $(ev.target).closest('.modal').attr('tabindex', -1).focus();
          ev.stopPropagation();
          if (ev.originalEvent) {
            ev.originalEvent.stopPropagation();
          }
          // perform additional check before simple hide
          that.hide(ev, true);
        }
      });
      if (!$el.attr('tabindex')) {
        $el.attr('tabindex', -1);
      }
      setTimeout(function () {
        $el.focus();
      }, 1);
    }
    // This is a hack to stop propagation for
    // modals when we dismiss modal
    $(document).on('keyup.dismiss.modal', (e) => {
      e.stopPropagation();
    });
    originalModalShow.apply(this, arguments);
  };

  $.fn.modal.Constructor.prototype.hide = function (ev) {
    var modals;
    var lastModal;
    var animated;
    // We already hid one
    if (ev && (ev.modalHidden)) {
      return;
    }

    if (this.$cloneEl) {
      this.$element.detach().appendTo(this.$cloneEl.parent());
      this.$cloneEl.remove();
      this.$cloneEl = null;
      this.$element.off('.clone');
    }

    originalModalHide.apply(this, arguments);

    animated =
      $('.modal').filter(':animated');
    if (animated.length) {
      animated.stop(true, true);
    }

    modals = $('.modal:visible');
    lastModal = modals.last();
    lastModal.css({height: '', overflow: '', top: '', 'margin-top': ''});
    if (lastModal.length) {
      arrangeTopModal(lastModal);

      // The app has several types of modals. After
      // closing several of them there are situations when focus is lost
      // (is set to body) and events (for example, press the escape key) don't
      // work correctly (open modals is closing in the wrong order). Thus
      // we should set focus on the top modal to all events spread from it.
      lastModal.focus();
    }
    arrangeBackgroundModals(modals, lastModal);
    // mark that we've hidden one
    if (ev) {
      ev.modalHidden = true;
    }
  };

  GGRC.register_modal_hook = function (toggle, launchFn) {
    $(function () {
      $('body').on(
        'click.modal-ajax.data-api keydown.modal-ajax.data-api',
        toggle ?
        '[data-toggle=modal-ajax-' + toggle + ']' :
          '[data-toggle=modal-ajax]',
        function (e) {
          var $this = $(this);
          var loadHref;
          var modalId;
          var target;
          var $target;
          var option;
          var href;
          var newTarget;

          if ($this.hasClass('disabled')) {
            return;
          }
          if (e.type === 'keydown' && e.which !== 13) {
            return;  // activate for keydown on Enter/Return only.
          }

          href = $this.attr('data-href') || $this.attr('href');
          loadHref = !$this.data().noHrefLoad;

          modalId = 'ajax-modal-' +
            href.replace(/[\/\?=&#%!]/g, '-').replace(/^-/, '');
          target = $this.attr('data-target') || $('#' + modalId);

          $target = $(target);
          newTarget = $target.length === 0;

          if (newTarget) {
            $target = $('<div id="' + modalId + '" class="modal hide"></div>');
            $target.addClass($this.attr('data-modal-class'));
            $this.attr('data-target', '#' + modalId);
          }

          $target.on('hidden', function (ev) {
            if (ev.target === ev.currentTarget) {
              $target.remove();
            }
          });

          if (newTarget || $this.data('modal-reset') === 'reset') {
            $target.html(preloadContent());
            if (
              $this.prop('protocol') === window.location.protocol &&
              loadHref
            ) {
              $target.load(href, emitLoaded);
            }
          }

          option = $target.data('modal-help') ?
            'toggle' : $.extend({}, $target.data(), $this.data());
          import(/* webpackChunkName: "modalsCtrls" */'../controllers/modals')
            .then(() => {
              launchFn.apply($target, [$target, $this, option]);
            });
        });
    });
  };
  $(function () {
    can.each({
      '': handlers.modal,
      form: handlers.form,
      helpform: handlers.helpform,
      deleteform: handlers.deleteform,
      unmapform: handlers.unmapform,
      archiveform: handlers.archiveform
    },
      function (launchFn, toggle) {
        GGRC.register_modal_hook(toggle, launchFn);
      }
    );
  });
})(window.can, window.can.$, window.GGRC);
