/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

describe('can.mustache.helper.if_mapping_ready', function () {
  'use strict';

  var instance;
  var mappingResult;
  var template;
  var templateContext;
  var render;
  var innerText;

  beforeAll(function () {
    innerText = 'someInnerText';

    template = [
      '<div>',
      '  {{#if_mapping_ready "comments" instance}}',
      innerText,
      '  {{/if_mapping_ready}}',
      '</div>'
    ].join('');

    render = can.view.mustache(template);
  });

  beforeEach(function () {
    mappingResult = new can.List();

    instance = {
      type: 'Assessment',
      get_mapping_deferred: function () {
        return new $.Deferred().resolve(mappingResult);
      }
    };

    templateContext = {
      instance: instance
    };
  });

  it('Change mapping`s length after render. html should contain text',
    function (done) {
      var html = render(templateContext);
      var renderText = $(html).children('div').text().trim();

      // mapping didn't change
      // helper should not render "innerText"
      expect(renderText).toEqual('');

      // change length of mapping
      mappingResult.push({id: 123});

      // SetTimeout is necessary because "if_mapping_ready" uses a "defer_render"
      setTimeout(function () {
        renderText = $(html).children('div').text().trim();
        expect(renderText).toEqual(innerText);
        done();
      }, 3);
    });

  it('Change mapping`s length before render. html should contain text',
    function (done) {
      var html;
      var renderText;

      // change length of mapping
      mappingResult.push({id: 123});

      html = render(templateContext);

      // SetTimeout is necessary because "if_mapping_ready" uses a "defer_render"
      setTimeout(function () {
        renderText = $(html).children('div').text().trim();
        expect(renderText).toEqual(innerText);
        done();
      }, 3);
    });

  it('Do not change mapping`s length. html should not contain text',
    function (done) {
      var html = render(templateContext);

      // SetTimeout is necessary because "if_mapping_ready" uses a "defer_render"
      setTimeout(function () {
        var renderText = $(html).children('div').text().trim();
        expect(renderText).toEqual('');
        done();
      }, 3);
    });
});
