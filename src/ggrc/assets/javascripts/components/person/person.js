/*!
  Copyright (C) 2017 Google Inc.
  Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

/**
 * A component that renders a single Person item, fetching the object from the
 * server if necessary.
 */
(function (GGRC, can) {
  'use strict';

  // the component's configuration object (i.e. its constructor's prototype)
  var component = {
    tag: 'person-info',

    template: can.view(
      GGRC.mustache_path +
      '/components/person/person.mustache'
    ),

    viewModel: {
      personObj: null,
      emptyText: '@',
      define: {
        personId: {
          type: 'number'
        },
        editable: {
          type: 'htmlbool'
        }
      }
    },

    _EV_REMOVE_CLICK: 'person-remove',

    /**
     * The component's entry point. Invoked when a new component instance has
     * been created.
     *
     * @param {Object} element - the (unwrapped) DOM element that triggered the
     *   creation of the component instance
     * @param {Object} options - the component instantiation options
     */
    init: function (element, options) {
      var scope = this.viewModel;
      var personId = scope.attr('personId');
      var person = scope.attr('personObj');
      var personModel;
      var noPerson = _.isEmpty(
        person && person.serialize ? person.serialize() : person);

      if (noPerson && isNaN(personId)) {
        console.warn('`personObj` or `personId` are missing');
        return;
      }

      if (noPerson ||
        (person && !person.email)) {
        personModel = CMS.Models.Person
          .findInCacheById(personId || person.id);
        if (personModel) {
          personModel = personModel.reify();
        }
      } else if (person) {
        personModel = person;
      }
      // For some reason the cache sometimes contains partially loaded objects,
      // thus we also need to check if "email" (a required field) is present.
      // If it is, we can be certain that we can use the object from the cache.
      if (personModel && personModel.email) {
        scope.attr('personObj', personModel);
        scope.attr('personId', personModel.id);
        return;
      }
      if (isNaN(personId) || personId <= 0) {
        personId = person.id;
      }

      // but if not in cache, we need to fetch the person object...
      person = new CMS.Models.Person({id: personId});
      new RefreshQueue().enqueue(person).trigger()
        .then(function (person) {
          person = Array.isArray(person) ? person[0] : person;
          scope.attr('personObj', person);
          scope.attr('personId', person.id);
        }, function () {
          $(document.body).trigger(
            'ajax:flash',
            {error: 'Failed to fetch data for person ' + personId + '.'});
        });
    },

    events: {
      /**
       * Event handler when a user clicks the trash icon.
       *
       * @param {jQuery.Element} $el - the source of the event `ev`
       * @param {jQuery.Event} ev - the event object
       */
      'a.unmap click': function ($el, ev) {
        // the handler is registered on the component's root element,
        // thus it needs to be triggered on it (and not on the $el)
        this.element.triggerHandler({
          type: component._EV_REMOVE_CLICK,
          person: this.scope.personObj
        });

        // keep the legacy event emitting mechanism above, but emit the event
        // using the more modern dispatch mechanism, too
        this.viewModel.dispatch({
          type: 'personRemove',
          person: this.scope.personObj
        });
      }
    }
  };

  GGRC.Components('personItem', component);
})(window.GGRC, window.can);
