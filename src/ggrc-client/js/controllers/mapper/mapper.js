/*
    Copyright (C) 2018 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

import '../../components/assessment-template-clone/assessment-template-clone';
import '../../components/object-bulk-update/object-bulk-update';
import '../../components/object-mapper/object-mapper';
import '../../components/object-generator/object-generator';
import '../../components/object-search/object-search';
import {
  isInScopeModel,
} from '../../plugins/utils/snapshot-utils';
import assessmentTemplateCloneTemplate from './assessment-template-clone-modal.mustache';
import objectGeneratorTemplate from './object-generator-modal.mustache';
import objectMapperTemplate from './object-mapper-modal.mustache';
import objectSearchTemplate from './object-search-modal.mustache';
import objectBulkUpdateTemplate from './object-bulk-update-modal.mustache';

const DATA_CORRUPTION_MESSAGE = 'Some Data is corrupted! ' +
            'Missing Scope Object';
const OBJECT_REQUIRED_MESSAGE = 'Required Data for In Scope Object is missing' +
  ' - Original Object is mandatory';

const ObjectMapper = can.Control.extend({
  defaults: {
    component: objectMapperTemplate,
  },
  launch: function ($trigger, options) {
    let href = $trigger ?
      $trigger.attr('data-href') || $trigger.attr('href') :
      '';
    let modalId = 'ajax-modal-' + (href || '')
        .replace(/[\/\?=\&#%]/g, '-')
        .replace(/^-/, '');
    let $target =
      $('<div id="' + modalId +
      '" class="modal modal-selector object-modal hide"></div>');

    $target.modal_form({}, $trigger);
    this.newInstance($target[0], can.extend({
      $trigger: $trigger,
    }, options));

    $target.on('modal:dismiss', function () {
      $(this).remove();
    });

    $target.on('hideModal', function (e) {
      $target.modal_form('silentHide');
    });

    $target.on('showModal', function () {
      $target.modal_form('show');
    });

    return $target;
  },
  isLoading: false,
  openMapper: function (data, disableMapper, btn) {
    let self = this;
    let isSearch = /unified-search/ig.test(data.toggle);

    if (disableMapper || this.isLoading) {
      return;
    }

    if (
        _.isUndefined(data.join_object_type) ||
        _.isNull(data.join_object_type)
    ) {
      throw new Error(OBJECT_REQUIRED_MESSAGE);
    }

    if (isInScopeModel(data.join_object_type) && !isSearch) {
      openForSnapshots(data);
    } else {
      openForCommonObjects(data, isSearch);
    }

    // each object type will be perceived as a snapshot, except types with
    // special config
    function openForSnapshots(data) {
      let inScopeObject;
      let config = getBaseConfig();
      let special = [{
        types: ['Issue'],
        // set config like for common objects
        config: getConfigForCommonObjects(data).general,
      }];

      _.extend(config.general, {useSnapshots: true});
      _.extend(config.special, special);

      if (data.is_new) {
        _.extend(config.general, {
          object: data.join_object_type,
          type: data.join_option_type,
          isNew: true,
          relevantTo: [{
            readOnly: true,
            type: data.snapshot_scope_type,
            id: data.snapshot_scope_id,
          }],
        });
        self.launch(btn, can.extend(config, data));
        return;
      }

      if (
        _.isUndefined(data.join_object_id) ||
        _.isNull(data.join_object_id)
      ) {
        throw new Error(OBJECT_REQUIRED_MESSAGE);
      }

      self.isLoading = true;
      inScopeObject =
        CMS.Models[data.join_object_type].store[data.join_object_id];
      inScopeObject.updateScopeObject().then(function () {
        let scopeObject = inScopeObject.attr('audit');

        if (!scopeObject.id) {
          GGRC.Errors.notifier('error', DATA_CORRUPTION_MESSAGE);
          setTimeout(function () {
            window.location.assign(location.origin + '/dashboard');
          }, 3000);
          return;
        }

        _.extend(config.general, {
          object: data.join_object_type,
          'join-object-id': data.join_object_id,
          type: data.join_option_type,
          relevantTo: [{
            readOnly: true,
            type: scopeObject.type,
            id: scopeObject.id,
            title: scopeObject.title,
          }],
        });

        self.launch(btn, can.extend(config, data));
      })
      .always(() => self.isLoading = false);
    }

    function openForCommonObjects(data, isSearch) {
      let config = getConfigForCommonObjects(data);

      if (isSearch) {
        ObjectSearch.launch(btn, can.extend(config, data));
      } else {
        self.launch(btn, can.extend(config, data));
      }
    }

    function getBaseConfig() {
      return {
        general: {
          useSnapshots: false,
          object: '',
          type: '',
          'join-object-id': null,
          // if set then each mapped object will be relevant to
          // relevantTo object (for example, snapshots relevant to Audit (at 08/2017))
          relevantTo: null,
        },
        special: [],
      };
    }

    function getConfigForCommonObjects(data) {
      let base = getBaseConfig();

      _.extend(base.general, {
        object: data.join_object_type,
        type: data.join_option_type,
        'join-object-id': data.join_object_id,
      });

      return base;
    }
  },
}, {
  init: function () {
    this.element.html(can.view.mustache(this.options.component)(this.options));
  },
});

const ObjectSearch = ObjectMapper.extend({
  defaults: {
    component: objectSearchTemplate,
  },
}, {});

const ObjectGenerator = ObjectMapper.extend({
  defaults: {
    component: objectGeneratorTemplate,
  },
}, {});

const ObjectBulkUpdate = ObjectMapper.extend({
    defaults: {
      component: objectBulkUpdateTemplate,
    },
  }, {});

const AssessmentTemplateClone = ObjectMapper.extend({
    defaults: {
      component: assessmentTemplateCloneTemplate,
    },
  }, {});

export {
  ObjectMapper,
  ObjectGenerator,
  ObjectSearch,
  ObjectBulkUpdate,
  AssessmentTemplateClone,
};
