/*!
    Copyright (C) 2017 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

(function(can, $) {

GGRC.Controllers.Modals("GGRC.Controllers.Delete", {
    defaults: {
        skip_refresh: true
    }
}, {
  init : function() {
    this._super();
  }

  , "{$footer} a.btn[data-toggle=delete]:not(:disabled) click" : function(el, ev) {
    var that = this,
    // Disable the cancel button.
        cancel_button = this.element.find("a.btn[data-dismiss=modal]"),
        modal_backdrop = this.element.data("modal_form").$backdrop;

    this.bindXHRToButton(this.options.instance.refresh().then(function(instance) {
      return instance.destroy();
    }).then(function(instance) {
      // If this modal is spawned from an edit modal, make sure that one does
      // not refresh the instance post-delete.
      var parent_controller = $(that.options.$trigger).closest('.modal').control();
      var msg;
      if (parent_controller) {
        parent_controller.options.skip_refresh = true;
      }

      msg = instance.display_name() + " deleted successfully";
      $(document.body).trigger("ajax:flash", { success : msg});
      if (that.element) {
        that.element.trigger("modal:success", that.options.instance);
      }

      return new $.Deferred(); // on success, just let the modal be destroyed or navigation happen.
                               // Do not re-enable the form elements.

    }).fail(function(xhr, status){
      var message = xhr.responseJSON;

      if (xhr.responseJSON && xhr.responseJSON.message) {
        message = xhr.responseJSON.message;
      }

      GGRC.Errors.notifier('error', message);
    }), el.add(cancel_button).add(modal_backdrop));
  }

});

})(window.can, window.can.$);
