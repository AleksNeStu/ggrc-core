/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

/**
 * Utils methods for showing standart modals
 */

const path = GGRC.mustache_path || '/static/mustache';
const BUTTON_VIEW_DONE = `${path}/modals/done_buttons.mustache`;
const BUTTON_VIEW_CLOSE = `${path}/modals/close_buttons.mustache`;
const BUTTON_VIEW_SAVE_CANCEL = `${path}/modals/save_cancel_buttons.mustache`;
const BUTTON_VIEW_SAVE_CANCEL_DELETE =
  `${path}/modals/save_cancel_delete_buttons.mustache`;
const BUTTON_VIEW_OK_CLOSE = `${path}/modals/confirm_cancel_buttons.mustache`;
const CONTENT_VIEW_WARNING =
  `${path}/base_objects/confirm_warning.mustache`;
const BUTTON_VIEW_CONFIRM = `${path}/modals/confirm_button.mustache`;
const BUTTON_VIEW_CONFIRM_CANCEL = `${path}/modals/confirm_buttons.mustache`;
const CONTENT_VIEW_CONFIRM = `${path}/modals/confirm.mustache`;
const BUTTON_CREATE_PROPOSAL = `${path}/modals/create_proposal.mustache`;

/**
 * Shows a warning popup within given options. If a user confirms
 * warning popup, then are called a success callback else - a fail callback.
 *
 * For showing the popup, by default, are used a
 * confirm method which controls user actions.
 *
 * Also the user can set own controller by setting controller field in
 * extra param.
 * Warning! Controller should have attached context!
 *
 * Note! It's not recommended to override content_view in the options param,
 * because popup is configured for the default template. If you want to use own
 * logic for confirmation you should explore _setupWarning method and use
 * own templates appropriate to its logic.
 * Be careful with confirmOperationName field - remember that standart
 * confirm uses confirmOperationName='confirm'
 * If you sets another value (for example, 'delete'), confirm button will
 * not be able to call success callback. If you want to set it then change
 * a controller with help extra param
 * which will process events for tags with data-{{your confirmOperationName}}
 *
 * @param {Object} options - Sets options for popup. See warning.settings
 *                           with default options.
 * @param {Function} success - Called if a user confirms the warning
 * @param {Function} fail - Called if a user dismiss the warning
 * @param {Object} [extra] - Extra options for warning. See warning.extraSettings
 *                           with default options.
 * @param {Function} extra.controller - Controller with attached context
 * @return {Object} - confirm window
 *
 * @example <caption>Default usage</caption>
 * var options = {
 *  skip_refresh: false,               // refreshes information about instance
 *  modal_title: 'Delete operation',   // title for popup
 *  objectShortInfo: 'Object #21',     // short title for object, for which confirmation is required
 *  modal_description: 'Operation is irreversible', // description for operation
 *  confirmTextForTyping: 'I confirm deletion', // text for confirm input
 *  buttonExtraClasses: 'disabled'     // initially confirm button is disabled
 * };
 *
 * warning(
 *  options,
 *  function () {
 *    console.log('Success!');
 *  },
 *  function () {
 *    console.log('Fail:(');
 *  }
 * )
 */
function warning(options, success, fail, extra) {
  var confirmOptions = _.extend({}, warning.settings, options);
  var confirmController;
  var confirmResult;

  extra = extra || {};

  confirmController = extra.controller || confirm;
  confirmResult = confirmController(confirmOptions, success, fail);

  _setupWarning(confirmResult, confirmOptions);
  return confirmResult;
}

function confirm (options, success, dismiss) {
  var $target = $('<div class="modal hide ' +
    options.extraCssClass +
    '"></div>');

  import(/* webpackChunkName: "modalsCtrls" */'../../controllers/modals')
    .then(() => {
      $target
        .modal({backdrop: 'static'})
        .ggrc_controllers_modals(can.extend({
          new_object_form: false,
          button_view: BUTTON_VIEW_CONFIRM_CANCEL,
          modal_confirm: 'Confirm',
          modal_description: 'description',
          modal_title: 'Confirm',
          content_view: CONTENT_VIEW_CONFIRM,
        }, options))
        .on('click', 'a.btn[data-toggle=confirm]', function (e) {
          var params = $(e.target).closest('.modal').find('form')
            .serializeArray();
          $target.modal('hide').remove();
          if (success) {
            success(params, $(e.target).data('option'));
          }
        })
        .on('click.modal-form.close', '[data-dismiss="modal"]', function () {
          $target.modal('hide').remove();
          if (dismiss) {
            dismiss();
          }
        });
    });

    return $target;
}

// default static const settings
warning.settings = Object.freeze({
  skip_refresh: true, // do not reload info about instance
  modal_title: 'Warning',
  objectShortInfo: 'Object',
  modal_description: '',
  confirmOperationName: 'confirm',
  confirmTextForTyping: 'I confirm',
  content_view: CONTENT_VIEW_WARNING,
  button_view: BUTTON_VIEW_CONFIRM,
  buttonExtraClasses: 'disabled'
});

function _setupWarning(confirm, settings) {
  var confirmText = settings.confirmTextForTyping.toLowerCase();
  var toggleClasses = settings.buttonExtraClasses;
  var operation = settings.confirmOperationName;
  var buttonSelector = '[data-toggle=' + operation + ']';

  confirm.on('change paste keyup', 'input[data-edit=confirm]',
  function (e) {
    var confirmButton = confirm.find(buttonSelector);
    var text = $(this)
      .val()
        .trim()
        .toLowerCase();

    if (text === confirmText) {
      confirmButton.removeClass(toggleClasses);
    } else {
      confirmButton.addClass(toggleClasses);
    }
  })
  .on('keyup', (e) => {
    //handle pressing enter
    if (e.keyCode === 13) {
      let confirmButton = confirm.find(buttonSelector);
      if (!confirmButton.attr('disabled')) {
        confirmButton.trigger('click');
      }
    }
  });
}

export {
  warning,
  confirm,
  BUTTON_VIEW_DONE,
  BUTTON_VIEW_CLOSE,
  BUTTON_VIEW_SAVE_CANCEL,
  BUTTON_VIEW_SAVE_CANCEL_DELETE,
  BUTTON_VIEW_OK_CLOSE,
  BUTTON_CREATE_PROPOSAL,
};
