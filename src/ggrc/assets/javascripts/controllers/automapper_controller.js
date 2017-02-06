/*!
    Copyright (C) 2017 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

;(function (CMS, GGRC, can, $) {
  var MIN_WAIT = 2000;
  var MAX_WAIT = 5000;

  var refresher = {
    instanceQueue: [],
    lastRefresh: Date.now(),
    refreshInstance: function (instance) {
      this.instanceQueue.push(instance);
      setTimeout(this.tick(instance), MIN_WAIT);
    },
    tick: function (instance) {
      return (function () {
        var isCurrent =
          this.instanceQueue[this.instanceQueue.length - 1] === instance;
        var isOverdue = (this.lastRefresh + MAX_WAIT) < Date.now();
        if (isCurrent || isOverdue) {
          this.go();
        }
      }).bind(this);
    },
    go: function () {
      var instances = this.instanceQueue;
      var ids = $.map(instances, function (instance) {
        return instance.id;
      });
      var filter = {automapping_id__in: ids.join()};
      this.lastRefresh = Date.now();
      this.instanceQueue = [];

      CMS.Models.Relationship.findAll(filter).then(function (relationships) {
        var instance = GGRC.page_instance();
        var modelName = instance.constructor.shortName;
        if (relationships.length) {
          return GGRC.Utils.CurrentPage
            .initCounts(GGRC.tree_view.orderedWidgetsByType[modelName], {
              type: instance.type,
              id: instance.id
            });
        }
      }).then(function () {
        var rq = new RefreshQueue();
        can.each(instances, function (instance) {
          rq.enqueue(instance.source);
          rq.enqueue(instance.destination);
        });
        return rq.trigger();
      });
    }
  };

  var flashWarning = function () {
    // timeout is required because a 'mapping created' success flash will show up
    // and we do not currently support multiple simultaneous flashes
    setTimeout(function () {
      $(document.body).trigger('ajax:flash', {
        warning: 'Automatic mappings were not created because that would ' +
        'result in too many new mappings'
      });
    }, 2000); // 2000 is a magic number that feels nice in the UI
  };

  var Controller = can.Control({
    '{CMS.Models.Relationship} created': function (model, ev, instance) {
      var limitExceeded;
      if (instance instanceof CMS.Models.Relationship) {
        limitExceeded = instance.extras &&
          instance.extras.automapping_limit_exceeded;
        if (limitExceeded) {
          flashWarning();
        } else {
          refresher.refreshInstance(instance);
        }
      }
    }
  });

  $(function () {
    new Controller();
  });
})(this.CMS, this.GGRC, this.can, this.can.$);

