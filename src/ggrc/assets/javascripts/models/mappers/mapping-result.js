/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (GGRC, can) {
  /*  GGRC.ListLoaders.MappingResult
   *
   *  - `instance`: The resulting item itself
   *  - `mappings`: Essentially, the reason(s) the instance appears in the
   *      list.  This may be an instance of can.Model or a pair containing
   *      (binding, result) in the case of a chained ListLoader.
   *
   *  For FilteredListLoader, the mappings are (`result`, `binding`), where
   *    `binding` is the binding in which the result appears, and thus,
   *    `binding.loader` contains information about the filter.
   *    `binding.instance`, then, is the instance on which the original,
   *    unfiltered list is specified.
   *  For CrossListLoader, the mappings are (`result`, `binding`), where
   *    `binding` is the "remote binding" which
   */
  can.Map.extend('GGRC.ListLoaders.MappingResult', {}, {
    init: function (instance, mappings, binding) {
      if (!mappings) {
        // Assume item was passed in as an object
        mappings = instance.mappings;
        binding = instance.binding;
        instance = instance.instance;
      }

      this.instance = instance;
      this.mappings = this._make_mappings(mappings);
      this.binding = binding;
    },

    //  `_make_mappings`
    //  - Ensures that every instance in `mappings` is an instance of
    //    `MappingResult`.
    _make_mappings: function (mappings) {
      mappings = mappings || [];
      return mappings.map(function (mapping) {
        if (!(mapping instanceof GGRC.ListLoaders.MappingResult))
          mapping = new GGRC.ListLoaders.MappingResult(mapping);
        return mapping;
      });
    },

    //  `observe_trigger`, `watch_observe_trigger`, `trigger_observe_trigger`
    //  - These exist solely to support dynamic updating of `*_compute`.
    //    Basically, these fake dependencies for those computes so each is
    //    updated any time a mapping is inserted or removed beyond a
    //    "virtual" level, which would otherwise obscure changes in the
    //    "first-level mappings" which both `bindings_compute` and
    //    `mappings_compute` depend on.
    observe_trigger: function () {
      if (!this._observe_trigger)
        this._observe_trigger = new can.Map({change_count: 1});
      return this._observe_trigger;
    },

    watch_observe_trigger: function () {
      this.observe_trigger().attr('change_count');
      can.each(this.mappings, function (mapping) {
        if (mapping.watch_observe_trigger)
          mapping.watch_observe_trigger();
      });
    },

    trigger_observe_trigger: function () {
      var observeTrigger = this.observe_trigger();
      observeTrigger.attr('change_count', observeTrigger.change_count + 1);
    },

    //  `insert_mapping` and `remove_mapping`
    //  - These exist solely to trigger an `observe_trigger` change event
    insert_mapping: function (mapping) {
      this.mappings.push(mapping);
      // Trigger change event
      this.trigger_observe_trigger();
    },

    remove_mapping: function (mapping) {
      var ret;
      var mappingIndex = this.mappings.indexOf(mapping);
      if (mappingIndex > -1) {
        ret = this.mappings.splice(mappingIndex, 1);
        //  Trigger change event
        this.trigger_observe_trigger();
        return ret;
      }
    },

    //  `get_bindings`, `bindings_compute`, `get_bindings_compute`
    //  - Returns a list of the `ListBinding` instances which are the source
    //    of 'first-level mappings'.
    get_bindings: function () {
      var bindings = [];

      this.walk_instances(function (instance, result, depth) {
        if (depth === 1)
          bindings.push(result.binding);
      });
      return bindings;
    },

    bindings_compute: function () {
      if (!this._bindings_compute)
        this._bindings_compute = this.get_bindings_compute();
      return this._bindings_compute;
    },

    get_bindings_compute: function () {
      var self = this;

      return can.compute(function () {
        // Unnecessarily access observe_trigger to be able to trigger change
        self.watch_observe_trigger();
        return self.get_bindings();
      });
    },

    //  `get_mappings`, `mappings_compute`, and `get_mappings_compute`
    //  - Returns a list of first-level mapping instances, even if they're
    //    several levels down due to virtual mappers like Multi or Cross
    //  - "First-level mappings" are the objects whose existence causes the
    //    `binding.instance` to be in the current `binding.list`.  (E.g.,
    //    if any of the "first-level mappings" exist, the instance will
    //    appear in the list.
    get_mappings: function () {
      var self = this;
      var mappings = [];

      this.walk_instances(function (instance, result, depth) {
        if (depth === 1) {
          if (instance === true)
            mappings.push(self.instance);
          else
            mappings.push(instance);
        }
      });
      return mappings;
    },

    mappings_compute: function () {
      if (!this._mappings_compute)
        this._mappings_compute = this.get_mappings_compute();
      return this._mappings_compute;
    },

    get_mappings_compute: function () {
      var self = this;

      return can.compute(function () {
        // Unnecessarily access _observe_trigger to be able to trigger change
        self.watch_observe_trigger();
        return self.get_mappings();
      });
    },

    //  `walk_instances`
    //  - `binding.mappings` can have several "virtual" levels due to mappers
    //    like `Multi`, `Cross`, and `Filter` -- e.g., mappers which just
    //    aggregate or filter results of other mappers.  `walk_instances`
    //    iterates over these "virtual" levels to emit instances only once
    //    per time they appear in a traversal path of `binding.mappings`.
    walk_instances: function (fn, lastInstance, depth) {
      var i;
      if (!depth)
        depth = 0;
      if (this.instance !== lastInstance) {
        fn(this.instance, this, depth);
        depth++;
      }
      for (i = 0; i < this.mappings.length; i++) {
        this.mappings[i].walk_instances(fn, this.instance, depth);
      }
    }
  });
})(window.GGRC, window.can);
