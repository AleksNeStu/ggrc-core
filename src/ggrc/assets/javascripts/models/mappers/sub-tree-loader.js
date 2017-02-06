/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (GGRC, can) {
  'use strict';

  GGRC.ListLoaders.TreeBaseLoader('GGRC.ListLoaders.SubTreeLoader', {}, {
    load: function (params, models) {
      return GGRC.Utils.QueryAPI.makeRequest(params)
        .then(function (response) {
          var mapped = [];
          models.forEach(function (modelName, idx) {
            var values = can.makeArray(response[idx][modelName].values);
            var models = values.map(function (source) {
              return CMS.Models[modelName].model(source);
            });
            mapped = mapped.concat(models);
          });
          return mapped;
        })
        .then(function (list) {
          var mappedToCurrent = [];
          var rest = [];
          var related = GGRC.Utils.CurrentPage.related;

          list.forEach(function (inst) {
            var relates = related.attr(inst.type);
            if (relates && relates[inst.id]) {
              mappedToCurrent.push(inst);
            } else {
              rest.push(inst);
            }
          });
          mappedToCurrent = mappedToCurrent.concat(rest);
          return this.insertInstancesFromMappings(mappedToCurrent);
        }.bind(this));
    }
  });
})(GGRC, can);
