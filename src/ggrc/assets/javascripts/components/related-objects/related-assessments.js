/*
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

import './related-objects';
import './related-audits';
import './related-assessment-list';
import './related-assessment-item';
import './related-controls-objectives';
import './related-evidences-and-urls';
import '../sortable-column/sortable-column';
import '../object-list/object-list';
import '../object-list-item/business-object-list-item';
import '../object-list-item/document-object-list-item';
import '../object-popover/related-assessment-popover';
import '../mapped-objects/mapped-objects';
import '../reusable-objects/reusable-objects-item';
import '../state-colors-map/state-colors-map';
import '../spinner/spinner';
import '../tree_pagination/tree_pagination';
import template from './templates/related-assessments.mustache';

let mapper = {
  mapObjects: function (source, destination) {
    return new CMS.Models.Relationship({
      context: source.context || {id: null},
      source: source,
      destination: destination
    });
  }
};

export default GGRC.Components('relatedAssessments', {
  tag: 'related-assessments',
  template,
  viewModel: {
    define: {
      baseInstanceDocuments: {
        get: function () {
          return this.attr('urls').concat(this.attr('evidences'));
        }
      },
      hasSelected: {
        get: function () {
          return this.attr('documentList.length');
        }
      },
      needReuse: {
        type: 'boolean',
        value: true,
      },
      relatedObjectType: {
        get: function () {
          // Get related object type based on assessment or the instance itself
          // 'instance.assessment_type' is used for object in "Related assessments" in
          // assessments info pane.
          // 'instance.type' is used when we are getting related assessment for
          // a snapshot.
          return this.attr('instance.assessment_type') ||
                 this.attr('instance.type');
        },
      },
      relatedObjectsTitle: {
        get: function () {
          const relObjType = this.attr('relatedObjectType');

          const objectName = CMS.Models[relObjType].model_plural;
          return `Related ${objectName}`;
        },
      },
    },
    evidences: [],
    urls: [],
    instance: {},
    documentList: [],
    isSaving: false,
    needReuse: '@',
    baseInstanceDocuments: [],
    getMapObjects: function (source, list) {
      return list
        .filter(function (item, index) {
          return index === list.indexOf(item);
        })
        // Get Array of mapped models
        .map(function (destination) {
          return mapper
            .mapObjects(source, destination)
            .save();
        });
    },
    reuseSelected: function () {
      var reusedObjectList =
        this.getMapObjects(
          this.attr('instance'),
          this.attr('documentList'));
      this.attr('isSaving', true);

      can.when.apply(can, reusedObjectList)
        .always(this.restoreDefaults.bind(this));
    },
    restoreDefaults: function () {
      this.attr('documentList').replace([]);
      this.attr('isSaving', false);
      this.dispatch('afterObjectReused');
      this.attr('instance').dispatch('refreshInstance');
    }
  }
});
