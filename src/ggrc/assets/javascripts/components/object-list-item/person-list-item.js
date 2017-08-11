/*!
 Copyright (C) 2017 Google Inc., authors, and contributors
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, GGRC, CMS, RefreshQueue) {
  'use strict';

  var tpl = can.view(GGRC.mustache_path +
    '/components/object-list-item/person-list-item.mustache');
  var tag = 'person-list-item';
  /**
   * Person List Item Component
   */
  GGRC.Components('personListItem', {
    tag: tag,
    template: tpl,
    viewModel: {
      define: {
        personId: {
          type: 'number',
          set: function (newVal) {
            this.attr('person', {id: newVal});
            return newVal;
          }
        },
        person: {
          Type: CMS.Models.Person,
          set: function (newVal, setVal) {
            var actualPerson;
            if (!newVal.id) {
              setVal({});
              return;
            }
            actualPerson = CMS.Models.Person.store[newVal.id] || {};
            if (actualPerson.email) {
              setVal(actualPerson);
            } else {
              actualPerson = new CMS.Models.Person({id: newVal.id});
              new RefreshQueue()
                .enqueue(actualPerson)
                .trigger()
                .done(function (person) {
                  person = Array.isArray(person) ? person[0] : person;
                  setVal(person);
                })
                .fail(function () {
                  setVal({});
                  GGRC.Errors.notifier('error',
                    'Failed to fetch data for person ' + newVal.id + '.');
                });
            }
          }
        },
        personEmail: {
          get: function () {
            return this.attr('person.email') || false;
          }
        },
        personName: {
          get: function () {
            return this.attr('person.name') || this.attr('personEmail');
          }
        },
        hasNoAccess: {
          get: function () {
            return this.attr('person.system_wide_role') === 'No Access';
          }
        }
      },
      withDetails: true
    }
  });
})(window.can, window.GGRC, window.CMS, window.RefreshQueue);
