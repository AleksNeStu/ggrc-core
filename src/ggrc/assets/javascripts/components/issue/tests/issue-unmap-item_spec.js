/*
    Copyright (C) 2017 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/
import component from '../issue-unmap-item';

describe('GGRC.Components.IssueUnmapRelatedSnapshots', function () {
  var viewModel;
  var events;
  beforeEach(function () {
    viewModel = new (can.Map.extend(component.prototype.viewModel));
    events = component.prototype.events;
  });

  describe('paging value', function () {
    it('returns GGRC.VM.Pagination object with [5, 10, 15] pagination',
    function () {
      var pagination = viewModel.attr('paging');
      expect(pagination.attr('pageSizeSelect').serialize())
        .toEqual([5, 10, 15]);
    });
  });

  describe('buildQuery() method', function () {
    it('sets object_name to passed type', function () {
      var type = 'Type';
      var query = viewModel.buildQuery(type);
      expect(query.object_name).toBe(type);
    });

    it('sets limit to [0, 5]', function () {
      var query = viewModel.buildQuery('Type');
      expect(query.limit).toEqual([0, 5]);
    });

    describe('configures filters.expression namely', function () {
      it('sets assessment.id from viewModel.target.id', function () {
        var query;
        var id = 1234567;

        viewModel.attr('target.id', id);
        query = viewModel.buildQuery('Type');

        expect(query.filters.expression.assessment.id).toBe(id);
      });

      it('sets issue.id from viewModel.issueInstance.id', function () {
        var query;
        var id = 1234567;

        viewModel.attr('issueInstance.id', id);
        query = viewModel.buildQuery('Type');

        expect(query.filters.expression.issue.id).toBe(id);
      });

      it('sets op.name to "cascade_unmappable" string', function () {
        var operationName = 'cascade_unmappable';
        var query = viewModel.buildQuery('Type');
        expect(query.filters.expression.op.name).toBe(operationName);
      });
    });
  });

  describe('processRelatedSnapshots() method', function () {
    beforeEach(function () {
      spyOn(viewModel, 'loadRelatedObjects')
        .and.returnValue(can.Deferred().resolve());
      spyOn(viewModel, 'showModal');
      spyOn(viewModel, 'unmap');
    });

    it('shows modal if there are items to unmap', function () {
      viewModel.attr('total', 2);

      viewModel.processRelatedSnapshots();

      expect(viewModel.showModal).toHaveBeenCalled();
      expect(viewModel.unmap).not.toHaveBeenCalled();
    });

    it('unmaps issue if there are no related items', function () {
      viewModel.attr('total', 0);

      viewModel.processRelatedSnapshots();

      expect(viewModel.showModal).not.toHaveBeenCalled();
      expect(viewModel.unmap).toHaveBeenCalledWith();
    });
  });

  describe('loadRelatedObjects() method', function () {
    var reqDeferred;
    var response;

    beforeEach(function () {
      response = [{
        Snapshot: {
          values: [{}, {}],
          total: 10,
        },
      }, {
        Audit: {
          values: [{}],
          total: 1,
      }}];
      reqDeferred = can.Deferred();
      spyOn(viewModel, 'buildQuery').and.returnValue(['query']);
      spyOn(GGRC.Utils.QueryAPI, 'makeRequest').and.returnValue(reqDeferred);
      spyOn($.prototype, 'trigger');
    });

    it('should change "isLoading" flag in case of success', function () {
      viewModel.attr('isLoading', false);

      viewModel.loadRelatedObjects();
      expect(viewModel.attr('isLoading')).toBeTruthy();

      reqDeferred.resolve(response);
      expect(viewModel.attr('isLoading')).toBeFalsy();
    });

    it('should change "isLoading" flag in case of error', function () {
      viewModel.attr('isLoading', false);

      viewModel.loadRelatedObjects();
      expect(viewModel.attr('isLoading')).toBeTruthy();

      reqDeferred.reject();
      expect(viewModel.attr('isLoading')).toBeFalsy();
    });

    it('should load snapshots correctly', function () {
      viewModel.loadRelatedObjects();
      reqDeferred.resolve(response);

      expect(viewModel.attr('total')).toBe(11);
      expect(viewModel.attr('relatedSnapshots.length')).toBe(2);
      expect(viewModel.attr('paging.total')).toBe(10);
    });

    it('should handle server errors correctly', function () {
      viewModel.loadRelatedObjects();
      reqDeferred.reject();

      expect($.prototype.trigger).toHaveBeenCalledWith('ajax:flash', {
        error: 'There was a problem with retrieving related objects.',
      });
    });
  });

  describe('showModal() method', function () {
    it('updates singular title', function () {
      viewModel.attr('total', 1);

      viewModel.showModal();

      expect(viewModel.attr('modalTitle')).toBe('Unmapping (1 object)');
    });

    it('updates plural title', function () {
      viewModel.attr('total', 5);

      viewModel.showModal();

      expect(viewModel.attr('modalTitle')).toBe('Unmapping (5 objects)');
    });

    it('changes modal state', function () {
      viewModel.attr('modalState.open', false);

      viewModel.showModal();

      expect(viewModel.attr('modalState.open')).toBe(true);
    });
  });

  describe('openObject() method', function () {
    var relatedObject;
    var originalModels;
    var getParam;
    var ARGS;

    beforeAll(function () {
      getParam = function (spy, index) {
        return spy.calls.argsFor(0)[index];
      };
      ARGS = {
        FIRST: 0,
        SECOND: 1,
      };
      originalModels = CMS.Models;
    });

    afterAll(function () {
      CMS.Models = originalModels;
    });

    beforeEach(function () {
      relatedObject = {
        id: 123,
        type: 'Type',
      };

      CMS.Models = {};
      CMS.Models[relatedObject.type] = {
        root_collection: 'rootCollectionType',
      };

      spyOn(window, 'open');
    });

    it('calls window.open with second "_blank" param', function () {
      var secondParam;
      viewModel.openObject(relatedObject);
      secondParam = getParam(window.open, ARGS.SECOND);
      expect(secondParam).toBe('_blank');
    });

    describe('sets url as a first param where', function () {
      var buildUrl;

      beforeAll(function () {
        buildUrl = function (type, id) {
          return '/' + type + '/' + id;
        };
      });

      it('url consists of root_collection from appopriate model and id ' +
      'based on passed related object', function () {
        var rootCollectionType = CMS.Models[relatedObject.type].root_collection;
        var expectedUrl;

        viewModel.openObject(relatedObject);
        expectedUrl = buildUrl(rootCollectionType, relatedObject.id);

        expect(getParam(window.open, ARGS.FIRST)).toBe(expectedUrl);
      });

      it('url consists of type and id from relatet object\'s child_type ' +
      'and child_id props if a type of related object equals to "Snapshot"',
      function () {
        var relatedObjectType = 'Snapshot';
        var rootCollectionType = CMS.Models[relatedObject.type].root_collection;
        var oldRelatedObjectType = relatedObject.type;
        var expectedUrl;

        _.extend(relatedObject, {
          type: relatedObjectType,
          child_type: oldRelatedObjectType,
          child_id: 54321,
        });
        viewModel.openObject(relatedObject);
        expectedUrl = buildUrl(
          rootCollectionType,
          relatedObject.child_id
        );

        expect(getParam(window.open, ARGS.FIRST)).toBe(expectedUrl);
      });
    });
  });

  describe('unmap() method', function () {
    var refreshDfd;
    var unmapDfd;
    var pageInstance;

    beforeEach(function () {
      var relationship;
      pageInstance = new can.Map({viewLink: 'temp url'});
      unmapDfd = can.Deferred();
      refreshDfd = can.Deferred();
      relationship = {
        refresh: function () {
          return refreshDfd;
        },
        unmap: function () {
          return unmapDfd;
        },
      };
      spyOn($.prototype, 'trigger');
      spyOn(CMS.Models.Relationship, 'findInCacheById')
        .and.returnValue(relationship);
      spyOn(GGRC, 'page_instance')
        .and.returnValue(pageInstance);
      spyOn(GGRC, 'navigate');
    });

    it('should change "isLoading" flag in case of success', function () {
      viewModel.attr('isLoading', false);

      viewModel.unmap();
      expect(viewModel.attr('isLoading')).toBeTruthy();

      refreshDfd.resolve();
      unmapDfd.resolve();
      expect(viewModel.attr('isLoading')).toBeFalsy();
    });

    it('should change "isLoading" flag in case of error', function () {
      viewModel.attr('isLoading', false);

      viewModel.unmap();
      expect(viewModel.attr('isLoading')).toBeTruthy();

      refreshDfd.reject();
      expect(viewModel.attr('isLoading')).toBeFalsy();
    });

    it('should unmap issue correctly', function () {
      viewModel.attr('issueInstance', {});
      viewModel.attr('issueInstance.related_sources', [
        {id: 1}, {id: 2}, {id: 3}]);
      viewModel.attr('target.related_destinations', [
        {id: 4}, {id: 4}, {id: 3}]);

      viewModel.unmap();
      refreshDfd.resolve();
      unmapDfd.resolve();

      expect(viewModel.attr('showRelatedSnapshots')).toBeFalsy();
    });

    it('should unmap from issue correctly', function () {
      viewModel.attr('issueInstance', pageInstance);
      viewModel.attr('issueInstance.related_sources', [
        {id: 1}, {id: 2}, {id: 3}]);
      viewModel.attr('target.related_destinations', [
        {id: 4}, {id: 4}, {id: 3}]);

      viewModel.unmap();
      refreshDfd.resolve();
      unmapDfd.resolve();

      expect(GGRC.navigate).toHaveBeenCalledWith('temp url');
    });

    it('should handle server errors correctly', function () {
      viewModel.unmap();
      refreshDfd.reject();

      expect($.prototype.trigger).toHaveBeenCalledWith('ajax:flash', {
        error: 'There was a problem with unmapping.',
      });
    });
  });

  describe('"click" event', function () {
    var handler;
    var event;
    beforeEach(function () {
      handler = events.click.bind({viewModel: viewModel});
      event = jasmine.createSpyObj(['preventDefault']);
      spyOn(viewModel, 'processRelatedSnapshots');
      spyOn(viewModel, 'dispatch');
    });

    it('prevents default action of the event', function () {
      handler(null, event);

      expect(event.preventDefault).toHaveBeenCalled();
    });

    it('calls processRelatedSnapshots() if target is assessment and ' +
    'not allowed to unmap issue from audit', function () {
      viewModel.attr('target.type', 'Assessment');
      viewModel.attr('issueInstance.allow_unmap_from_audit', false);

      handler(null, event);

      expect(viewModel.processRelatedSnapshots).toHaveBeenCalled();
      expect(viewModel.dispatch).not.toHaveBeenCalled();
    });

    it('dispatches "unmapIssue" event if target', function () {
      viewModel.attr('target.type', 'Control');
      viewModel.attr('issueInstance.allow_unmap_from_audit', true);

      handler(null, event);

      expect(viewModel.processRelatedSnapshots).not.toHaveBeenCalled();
      expect(viewModel.dispatch).toHaveBeenCalledWith('unmapIssue');
    });
  });

  describe('"{viewModel.paging} current" event', function () {
    var handler;
    beforeEach(function () {
      handler = events['{viewModel.paging} current']
        .bind({viewModel: viewModel});
    });

    it('call loadRelatedObjects() method', function () {
      spyOn(viewModel, 'loadRelatedObjects');

      handler();

      expect(viewModel.loadRelatedObjects).toHaveBeenCalled();
    });
  });

  describe('"{viewModel.paging} pageSize" event', function () {
    var handler;
    beforeEach(function () {
      handler = events['{viewModel.paging} pageSize']
        .bind({viewModel: viewModel});
    });

    it('call loadRelatedObjects() method', function () {
      spyOn(viewModel, 'loadRelatedObjects');

      handler();

      expect(viewModel.loadRelatedObjects).toHaveBeenCalled();
    });
  });
});
