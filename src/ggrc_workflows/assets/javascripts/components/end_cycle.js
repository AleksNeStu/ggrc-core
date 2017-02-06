  /*!
  Copyright (C) 2017 Google Inc.
  Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

/**
 * A component that wraps a button for ending a Workflow cycle, and
 * automatically handles a click on it.
 *
 * As a result, the Cycle instance passed to the component is ended, and
 * a couple of affected objects are refreshed in the process.
 *
 * Usage example (state and permission checks not included):
 *
 *   <cycle-end-cycle cycle="instance">
 *       <button>Click to end a Cycle</button>
 *   </cycle-end-cycle>
 *
 */
(function (GGRC, can) {
  'use strict';

  GGRC.Components('endCycleButtonWrap', {
    tag: 'cycle-end-cycle',
    template: '<content/>',
    events: {
      click: function (el, ev) {
        ev.stopPropagation();

        this.scope.cycle
          .refresh()
          .then(function (cycle) {
            return cycle.attr('is_current', false).save();
          })
          .then(function () {
            return GGRC.page_instance().refresh();
          })
          .then(function () {
            // We need to update person's assigned_tasks mapping manually
            var person = CMS.Models.Person.cache[GGRC.current_user.id];
            var binding = person.get_binding('assigned_tasks');

            // FIXME: Find a better way of removing stagnant
            // items from the list.
            binding.list.splice(0, binding.list.length);
            return binding.loader.refresh_list(binding);
          })
          .then(function () {
            var pageInstance = GGRC.page_instance();
            var WorkflowExtension =
              GGRC.extensions.find(function (extension) {
                return extension.name === 'workflows';
              });

            $('body').trigger('treeupdate');
            return GGRC.Utils.CurrentPage
              .initCounts([
                WorkflowExtension.countsMap.history
              ], {
                type: pageInstance.type,
                id: pageInstance.id
              });
          });
      }
    }
  });
})(window.GGRC, window.can);
