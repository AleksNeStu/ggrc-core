/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

describe('GGRC Utils CurrentPage', function () {
  var pageType;
  beforeEach(function () {
    pageType = GGRC.pageType;
  });

  afterAll(function () {
    GGRC.pageType = pageType;
  });

  beforeEach(function () {
    var instance = {
      id: 1,
      type: 'Audit'
    };

    spyOn(GGRC, 'page_instance')
      .and.returnValue(instance);

    GGRC.pageType = undefined;
  });
  describe('getPageType() method', function () {
    var method;

    beforeEach(function () {
      method = GGRC.Utils.CurrentPage.getPageType;
    });

    it('returns pageType value if it defined', function () {
      GGRC.pageType = 'MOCK_PAGE';
      expect(method()).toEqual('MOCK_PAGE');
    });

    it('returns page_instance type if pageType not defined', function () {
      expect(method()).toEqual('Audit');
    });
  });

  describe('isMyAssessments() method', function () {
    var method;

    beforeEach(function () {
      method = GGRC.Utils.CurrentPage.isMyAssessments;
    });

    it('returns True for GGRC.pageType = MY_ASSESSMENTS', function () {
      GGRC.pageType = 'MY_ASSESSMENTS';
      expect(method()).toBeTruthy();
    });

    it('returns False if pageType not defined', function () {
      expect(method()).toBeFalsy();
    });

    it('returns False if GGRC.pageType not equal MY_ASSESSMENTS', function () {
      GGRC.pageType = 'FOO_BAR';
      expect(method()).toBeFalsy();
    });
  });

  describe('isMyWork() method', function () {
    var method;

    beforeEach(function () {
      method = GGRC.Utils.CurrentPage.isMyWork;
    });

    it('returns True for GGRC.pageType = MY_WORK', function () {
      GGRC.pageType = 'MY_WORK';
      expect(method()).toBeTruthy();
    });

    it('returns False if pageType not defined', function () {
      expect(method()).toBeFalsy();
    });

    it('returns False if GGRC.pageType not equal MY_WORK', function () {
      GGRC.pageType = 'FOO_BAR_BAR';
      expect(method()).toBeFalsy();
    });
  });

  describe('isAdmin() method', function () {
    var method;

    beforeEach(function () {
      method = GGRC.Utils.CurrentPage.isAdmin;
    });

    it('returns True for GGRC.pageType = ADMIN', function () {
      GGRC.pageType = 'ADMIN';
      expect(method()).toBeTruthy();
    });

    it('returns False if pageType not defined', function () {
      expect(method()).toBeFalsy();
    });

    it('returns False if GGRC.pageType not equal ADMIN', function () {
      GGRC.pageType = 'FOO_BAR_BAZ';
      expect(method()).toBeFalsy();
    });
  });

  describe('isObjectContextPage() method', function () {
    var method;

    beforeEach(function () {
      method = GGRC.Utils.CurrentPage.isObjectContextPage;
    });

    it('returns True if pageType not defined', function () {
      expect(method()).toBeTruthy();
    });

    it('returns False if pageType defined', function () {
      GGRC.pageType = 'ADMIN';
      expect(method()).toBeFalsy();
    });
  });

  describe('getWidgetList() method', function () {
    var method;

    beforeEach(function () {
      spyOn(GGRC.WidgetList, 'get_widget_list_for')
        .and.returnValue({
          control: {},
          Assessment: {},
          objective: {}
        });
      method = GGRC.Utils.CurrentPage.getWidgetList;
    });

    it('returns an empty object when model is not provided', function () {
      var result = method('', 'assessments_view');

      expect(result.assessment).toBeUndefined();
    });

    it('returns assessments widget for assessment view', function () {
      var result = method('assessment', '/assessments_view');
      var keys = Object.keys(result);

      expect(keys.length).toEqual(1);
      expect(keys).toContain('assessment');
    });

    it('returns widgets for non-assessment view', function () {
      var result = method('assessment', '/controls_view');
      var keys = Object.keys(result);

      expect(keys.length).toEqual(3);
    });
  });

  describe('getDefaultWidgets() method', function () {
    var method;

    beforeEach(function () {
      method = GGRC.Utils.CurrentPage.getDefaultWidgets;
    });

    it('should return "Info" widget for non-object browser path', function () {
      var result = method({
        control: {},
        assessment: {},
        objective: {},
        info: {}
      }, '/assessments_view');

      expect(result).toContain('info');
    });

    it('should return "Info" widget for non-object browser path', function () {
      var result = method({
        control: {},
        assessment: {},
        objective: {},
        info: {}
      }, '/objectBrowser/');

      expect(result).not.toContain('info');
    });
  });

  describe('getWidgetModels() method', function () {
    var method;

    beforeEach(function () {
      spyOn(GGRC.WidgetList, 'get_widget_list_for')
        .and.returnValue({
          control: {
            content_controller_options: {
              model: {
                shortName: 'Control'
              }
            }
          },
          Assessment: {
            content_controller_options: {
              model: {
                shortName: 'Assessment'
              }
            }
          },
          objective: {
            content_controller_options: {
              model: {
                shortName: 'Objective'
              }
            }
          },
          info: {
            content_controller_options: {
              model: {
                shortName: 'Info'
              }
            }
          }
        });
      method = GGRC.Utils.CurrentPage.getWidgetModels;
    });

    it('returns an empty array when model is not provided', function () {
      var result = method('', 'assessments_view');

      expect(result.length).toEqual(0);
    });

    it('returns assessment model name only for assessment view', function () {
      var result = method('assessment', '/assessments_view');

      expect(result).toContain('Assessment');
    });

    it('returns appropriate models for non-assessment view',
      function () {
        var result = method('assessment', '/controls_view');

        expect(result).toContain('Assessment');
        expect(result).toContain('Control');
        expect(result).toContain('Objective');
        expect(result).toContain('Info');
      });

    it('returns non-info models for object browser view',
      function () {
        var result = method('assessment', '/objectBrowser/');

        expect(result).toContain('Assessment');
        expect(result).toContain('Control');
        expect(result).toContain('Objective');
        expect(result).not.toContain('Info');
      });
  });

  describe('initCounts() method', function () {
    var method;
    var queryDfd;
    var getCounts;
    var id = 1;

    beforeEach(function () {
      queryDfd = can.Deferred();
      method = GGRC.Utils.CurrentPage.initCounts;
      getCounts = GGRC.Utils.CurrentPage.getCounts;

      spyOn(GGRC.Utils.TreeView, 'makeRelevantExpression')
        .and.returnValue({
          type: 'Assessment',
          id: id,
          operation: 'owned'
        });
      spyOn(GGRC.Utils.Snapshots, 'isSnapshotRelated')
        .and.callFake(function (type, widgetType) {
          return widgetType === 'Control';
        });
      spyOn(GGRC.Utils.QueryAPI, 'buildParam')
        .and.callFake(function (objName) {
          return {
            objectName: objName
          };
        });

      spyOn(GGRC.query_parser, 'parse')
        .and.returnValue({});

      spyOn(GGRC.Utils.QueryAPI, 'makeRequest')
        .and.returnValue(queryDfd);
    });

    it('should not make request when no widget was provided', function () {
      method([], 'Control', 1);

      expect(GGRC.Utils.QueryAPI.makeRequest)
        .not.toHaveBeenCalled();
    });

    it('should init counts for snapshotable objects', function () {
      var result;

      method(['Control'], 'Assessment', 1);

      expect(GGRC.Utils.QueryAPI.makeRequest)
        .toHaveBeenCalledWith({
          data: [
            {
              type: 'count',
              objectName: 'Snapshot'
            }
          ]
        });

      queryDfd.resolve([{
        Snapshot: {
          total: 10
        }
      }]);

      result = getCounts();

      expect(result.Control).toEqual(10);
    });

    it('should init counts for non-snapshotable objects', function () {
      var result;

      method(['Assessment'], 'Control', 1);

      expect(GGRC.Utils.QueryAPI.makeRequest)
        .toHaveBeenCalledWith({
          data: [
            {
              type: 'count',
              objectName: 'Assessment'
            }
          ]
        });

      queryDfd.resolve([{
        Assessment: {
          total: 10
        }
      }]);

      result = getCounts();

      expect(result.Assessment).toEqual(10);
    });

    it('should init counts for virtual objects', function () {
      var result;

      method([{
        name: 'Cycle',
        countsName: 'ActiveCycle'
      }], 'Control', 1);

      expect(GGRC.Utils.QueryAPI.makeRequest)
        .toHaveBeenCalledWith({
          data: [
            {
              type: 'count',
              objectName: 'Cycle'
            }
          ]
        });

      queryDfd.resolve([{
        Cycle: {
          total: 10
        }
      }]);

      result = getCounts();

      expect(result.ActiveCycle).toEqual(10);
    });
  });

  describe('initMappedInstances() method', function () {
    var requestDfds = [];
    var method;

    beforeEach(function () {
      var requestDfd;

      spyOn(GGRC.Utils.QueryAPI, 'buildRelevantIdsQuery')
        .and.callFake(function (objName, page, relevant, additionalFilter) {
          return {
            model: objName,
            operation: 'relevant'
          };
        });

      spyOn(GGRC.Utils.Snapshots, 'isSnapshotRelated')
        .and.callFake(function (parent, child) {
          return child === 'Control';
        });

      spyOn(GGRC.Utils.Snapshots, 'transformQuery')
        .and.callFake(function (query) {
          return query;
        });

      spyOn(GGRC.Utils.QueryAPI, 'batchRequests')
        .and.callFake(function () {
          requestDfd = can.Deferred();
          requestDfds.push(requestDfd);
          return requestDfd;
        });
      method = GGRC.Utils.CurrentPage.initMappedInstances;
    });

    it('should init mappings for snapshotable objects',
      function (done) {
        var snapshotIds = [1, 2, 3];

        function validateResult(result) {
          snapshotIds.forEach(function (id) {
            expect(result.Control[id]).toBeTruthy();
          });
          done();
        }

        spyOn(GGRC.Mappings, 'getMappingList')
          .and.returnValue(['Control']);

        method().then(validateResult);
        requestDfds.forEach(function (dfd) {
          dfd.resolve({
            Snapshot: {
              ids: snapshotIds
            }
          });
        });
      });

    it('should init mappings for non-snapshotable objects',
      function (done) {
        var nonSnapshotIds = [4, 5, 6];

        function validateResult(result) {
          nonSnapshotIds.forEach(function (id) {
            expect(result.Assessment[id]).toBeTruthy();
          });

          done();
        }

        spyOn(GGRC.Mappings, 'getMappingList')
          .and.returnValue(['Assessment']);

        method().then(validateResult);
        requestDfds.forEach(function (dfd) {
          dfd.resolve({
            Assessment: {
              ids: nonSnapshotIds
            }
          });
        });
      });
  });
});
