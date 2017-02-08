/*!
    Copyright (C) 2017 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

(function (GGRC, can) {
  GGRC.ListLoaders.BaseListLoader('GGRC.ListLoaders.ReifyingListLoader', {}, {
    init: function (source) {
      this._super();

      if (source instanceof GGRC.ListLoaders.ListBinding)
        this.source_binding = source;
      else
        this.source = source;
    },
    insert_from_source_binding: function (binding, results) {
      var self = this;
      var refreshQueue = new RefreshQueue();
      var newResults = [];

      can.each(results, function (result) {
        refreshQueue.enqueue(result.instance);
        newResults.push(self.make_result(result.instance, [result], binding));
      });
      refreshQueue.trigger().then(function () {
        self.insert_results(binding, newResults);
      });
    },
    init_listeners: function (binding) {
      var self = this;

      if (this.source_binding)
        binding.source_binding = this.source_binding;
      else
        binding.source_binding = binding.instance.get_binding(this.source);

      this.insert_from_source_binding(binding, binding.source_binding.list, 0);

      binding.source_binding.list.bind('add', function (ev, results, index) {
        self.insert_from_source_binding(binding, results, index);
      });

      binding.source_binding.list.bind('remove', function (ev, results, index) {
        can.each(results, function (result) {
          self.remove_instance(binding, result.instance, result);
        });
      });
    },
    _refresh_stubs: function (binding) {
      return binding.source_binding.refresh_stubs(binding);
    }
  });
})(window.GGRC, window.can);
