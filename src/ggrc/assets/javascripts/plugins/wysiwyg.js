/*!
    Copyright (C) 2017 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/
(function($) {
  $.fn.cms_wysihtml5 = function() {
    if ($(this).data('_wysihtml5_initialized')) {
      return;
    }

    wysihtml5ParserRules.cleanUp = false;

    $(this).data('_wysihtml5_initialized', true);
    this.wysihtml5({
      link: true,
      image: false,
      html: true,
      'font-styles': false,
      parserRules: wysihtml5ParserRules
    });
    this.each(function() {
      var $that = $(this),
        editor = $that.data("wysihtml5").editor,
        $textarea = $(editor.textarea.element);

      if ($that.data("cms_events_bound")) {
        return;
      }
      editor.on('beforeinteraction:composer', function() {
        $that.val(this.getValue()).trigger('change');
      });

      var $wysiarea = $that.closest(".wysiwyg-area").resizable({
        handles: "s",
        minHeight: 100,
        alsoResize: "#" + $that.uniqueId().attr("id") + ", #" + $that.closest(".wysiwyg-area").uniqueId().attr("id") + " iframe",
        autoHide: false
      }).bind("resizestop", function(ev) {
        ev.stopPropagation();
        $that.css({
          "display": "block",
          "height": $that.height() + 20
        }); //10px offset between reported height and styled height.
        $textarea.css('width', $textarea.width() + 20);
        editor.composer.style(); // re-copy new size of textarea to composer
        editor.fire('change_view', editor.currentView.name);
      });
      var $sandbox = $wysiarea.find(".wysihtml5-sandbox");

      $($sandbox.prop("contentWindow"))
        .bind("mouseover mousemove mouseup", function(ev) {
          var e = new $.Event(ev.type === "mouseup" ? "mouseup" : "mousemove"); //jQUI resize listens on this.
          e.pageX = $sandbox.offset().left + ev.pageX;
          e.pageY = $sandbox.offset().top + ev.pageY;
          $sandbox.trigger(e);
        });

      $that.data("cms_events_bound", true);
    });

    return this;
  };
})(jQuery);
