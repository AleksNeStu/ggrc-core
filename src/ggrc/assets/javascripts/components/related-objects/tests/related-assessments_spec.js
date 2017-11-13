/*
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

import Component from '../related-assessments';

describe('GGRC.Components.relatedAssessments', () => {
  describe('viewModel scope', () => {
    let originalModels;
    let viewModel;

    beforeAll(() => {
      let vmConfig = Component.prototype.viewModel;
      viewModel = new (can.Map.extend(vmConfig));
    });

    describe('relativeObjectsTitle get() method', () => {
      beforeAll(() => {
        originalModels = CMS.Models;
      });

      afterAll(() => {
        CMS.Models = originalModels;
      });

      it('returns title based on instance.assessment_type', () => {
        let asmtModelType = 'Model1';
        let modelPlural = 'Awesome_models1';
        let expectedTitle;

        CMS.Models = {
          [asmtModelType]: {
            model_plural: modelPlural,
          },
        };
        viewModel.attr('instance.assessment_type', asmtModelType);
        expectedTitle = `Related ${modelPlural}`;

        expect(viewModel.attr('relatedObjectsTitle')).toBe(expectedTitle);
      });

      it(`returns title based on instance.type if is gotten related
          assessments not from assessment info pane`, () => {
        let modelType = 'Model1';
        let modelPlural = 'Awesome_models1';
        let expectedTitle;

        CMS.Models = {
          [modelType]: {
            model_plural: modelPlural,
          },
        };
        viewModel.attr('instance.assessment_type', null);
        viewModel.attr('instance.type', modelType);
        expectedTitle = `Related ${modelPlural}`;

        expect(viewModel.attr('relatedObjectsTitle')).toBe(expectedTitle);
      });
    });
  });
});
