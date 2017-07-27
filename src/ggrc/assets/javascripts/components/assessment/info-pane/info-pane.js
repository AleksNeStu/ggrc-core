/*!
 Copyright (C) 2017 Google Inc., authors, and contributors
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, GGRC) {
  'use strict';
  var tpl = can.view(GGRC.mustache_path +
    '/components/assessment/info-pane/info-pane.mustache');

  /**
   * Assessment Specific Info Pane View Component
   */
  GGRC.Components('assessmentInfoPane', {
    tag: 'assessment-info-pane',
    template: tpl,
    viewModel: {
      define: {
        isSaving: {
          type: 'boolean',
          value: false
        },
        isLoading: {
          type: 'boolean',
          value: false
        },
        mappedSnapshots: {
          Value: can.List
        },
        controls: {
          get: function () {
            return this.attr('mappedSnapshots')
              .filter(function (item) {
                return item.child_type === 'Control';
              });
          }
        },
        relatedInformation: {
          get: function () {
            return this.attr('mappedSnapshots')
              .filter(function (item) {
                return item.child_type !== 'Control';
              });
          }
        },
        comments: {
          Value: can.List
        },
        urls: {
          Value: can.List
        },
        evidences: {
          Value: can.List
        },
        editMode: {
          type: 'boolean',
          get: function () {
            return this.attr('instance.status') !== 'Completed' &&
              this.attr('instance.status') !== 'Ready for Review' &&
              !this.attr('instance.archived');
          },
          set: function () {
            this.onStateChange({state: 'In Progress', undo: false});
          }
        },
        isEditDenied: {
          get: function () {
            return !Permission
              .is_allowed_for('update', this.attr('instance')) ||
              this.attr('instance.archived');
          }
        },
        instance: {}
      },
      modal: {
        open: false
      },
      onStateChangeDfd: {},
      formState: {},
      noItemsText: '',
      triggerFormSaveCbs: $.Callbacks(),
      setInProgressState: function () {
        this.onStateChange({state: 'In Progress', undo: false});
      },
      getQuery: function (type, sortObj, additionalFilter) {
        var relevantFilters = [{
          type: this.attr('instance.type'),
          id: this.attr('instance.id'),
          operation: 'relevant'
        }];
        return GGRC.Utils.QueryAPI
          .buildParam(type,
            sortObj || {},
            relevantFilters,
            [],
            additionalFilter || []);
      },
      getCommentQuery: function () {
        return this.getQuery('Comment',
          {sortBy: 'created_at', sortDirection: 'desc'});
      },
      getSnapshotQuery: function () {
        return this.getQuery('Snapshot');
      },
      getEvidenceQuery: function () {
        var evidenceType = CMS.Models.Document.EVIDENCE;
        return this.getQuery(
          'Document',
          {sortBy: 'created_at', sortDirection: 'desc'},
          this.getDocumentAdditionFilter(evidenceType));
      },
      getUrlQuery: function () {
        var urlType = CMS.Models.Document.URL;
        return this.getQuery(
          'Document',
          {sortBy: 'created_at', sortDirection: 'desc'},
          this.getDocumentAdditionFilter(urlType));
      },
      requestQuery: function (query, type) {
        var dfd = can.Deferred();
        type = type || '';
        this.attr('isUpdating' + can.capitalize(type), true);
        GGRC.Utils.QueryAPI
          .batchRequests(query)
          .done(function (response) {
            var type = Object.keys(response)[0];
            var values = response[type].values;
            dfd.resolve(values);
          })
          .fail(function () {
            dfd.resolve([]);
          })
          .always(function () {
            this.attr('isUpdating' + can.capitalize(type), false);
          }.bind(this));
        return dfd;
      },
      loadSnapshots: function () {
        var query = this.getSnapshotQuery();
        return this.requestQuery(query);
      },
      loadComments: function () {
        var query = this.getCommentQuery();
        return this.requestQuery(query, 'comments');
      },
      loadEvidences: function () {
        var query = this.getEvidenceQuery();
        return this.requestQuery(query, 'evidences');
      },
      loadUrls: function () {
        var query = this.getUrlQuery();
        return this.requestQuery(query, 'urls');
      },
      updateItems: function () {
        can.makeArray(arguments).forEach(function (type) {
          this.attr(type).replace(this['load' + can.capitalize(type)]());
        }.bind(this));
      },
      removeItem: function (event, type) {
        var item = event.item;
        var index = this.attr(type).indexOf(item);
        this.attr('isUpdating' + can.capitalize(type), true);
        return this.attr(type).splice(index, 1);
      },
      addItems: function (event, type) {
        var items = event.items;
        this.attr('isUpdating' + can.capitalize(type), true);
        return this.attr(type).unshift.apply(this.attr(type),
          can.makeArray(items));
      },
      getDocumentAdditionFilter: function (documentType) {
        return documentType ?
          {
            expression: {
              left: 'document_type',
              op: {name: '='},
              right: documentType
            }
          } :
          [];
      },
      updateRelatedItems: function () {
        this.attr('mappedSnapshots')
          .replace(this.loadSnapshots());
        this.attr('comments')
          .replace(this.loadComments());
        this.attr('evidences')
          .replace(this.loadEvidences());
        this.attr('urls')
          .replace(this.loadUrls());
      },
      initializeFormFields: function () {
        this.attr('formFields',
            this.attr('instance.local_attributes')
              .map(GGRC.Utils.CustomAttributes.prepareLocalAttribute)
        );
      },
      initGlobalAttributes: function () {
        return this.attr('globalAttributes',
          this.attr('instance.global_attributes')
            .map(GGRC.Utils.CustomAttributes.prepareGlobalAttribute));
      },
      onFormSave: function () {
        this.attr('triggerFormSaveCbs').fire();
      },
      onStateChange: function (event) {
        var isUndo = event.undo;
        var newStatus = event.state;
        var instance = this.attr('instance');
        var self = this;
        var previousStatus = instance.attr('previousStatus') || 'In Progress';
        this.attr('onStateChangeDfd', can.Deferred());

        if (isUndo) {
          instance.attr('previousStatus', undefined);
        } else {
          instance.attr('previousStatus', instance.attr('status'));
        }
        instance.attr('isPending', true);

        this.attr('formState.formSavedDeferred')
          .then(function () {
            instance.refresh().then(function () {
              instance.attr('status', isUndo ? previousStatus : newStatus);
              return instance.save()
              .then(function () {
                instance.attr('isPending', false);
                self.initializeFormFields();
                self.attr('onStateChangeDfd').resolve();
              });
            });
          });
      },
      saveGlobalAttributes: function (event) {
        var globalAttributes = event.globalAttributes;
        var caValues = this.attr('instance.global_attributes');
        can.Map.keys(globalAttributes).forEach(function (fieldId) {
          var caValue =
            caValues.filter(function (item) {
              return item.id === Number(fieldId);
            })[0];
          if (!caValue) {
            console.error('Corrupted Date: ', caValues);
            return;
          }
          if (caValue.attr('values').length) {
            caValue.attr('values')[0].attr('value', globalAttributes[fieldId]);
          } else {
            caValue.attr('values').push({value: globalAttributes[fieldId]});
          }
        });

        return this.attr('instance').save();
      },
      saveFormFields: function (formFields) {
        var caValues = this.attr('instance.local_attributes');
        can.Map.keys(formFields).forEach(function (fieldId) {
          var caValue =
            caValues.filter(function (item) {
              return item.id === Number(fieldId);
            })[0];
          if (!caValue) {
            console.error('Corrupted Date: ', caValues);
            return;
          }
          if (caValue.attr('values').length) {
            caValue.attr('values')[0].attr('value', formFields[fieldId]);
          } else {
            caValue.attr('values').push({value: formFields[fieldId]});
          }
        });

        return this.attr('instance').save();
      },
      showRequiredInfoModal: function (e, field) {
        var scope = field || e.field;
        var errors = scope.attr('errorsMap');
        var errorsList = can.Map.keys(errors)
          .map(function (error) {
            return errors[error] ? error : null;
          })
          .filter(function (errorCode) {
            return !!errorCode;
          });
        var data = {
          options: scope.attr('options'),
          contextScope: scope,
          fields: errorsList,
          value: scope.attr('value'),
          title: scope.attr('title'),
          type: scope.attr('type')
        };
        var title = 'Required ' +
          data.fields.map(function (field) {
            return can.capitalize(field);
          }).join(' and ');

        can.batch.start();
        this.attr('modal', {
          content: data,
          modalTitle: title,
          state: {}
        });
        can.batch.stop();
        this.attr('modal.state.open', true);
      }
    },
    init: function () {
      this.viewModel.initializeFormFields();
      this.viewModel.initGlobalAttributes();
      this.viewModel.updateRelatedItems();
    },
    events: {
      '{viewModel.instance} refreshInstance': function () {
        this.viewModel.attr('mappedSnapshots')
          .replace(this.viewModel.loadSnapshots());
      }
    }
  });
})(window.can, window.GGRC);
