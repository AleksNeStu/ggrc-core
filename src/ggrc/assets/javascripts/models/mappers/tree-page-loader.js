/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (GGRC, can) {
  'use strict';

  GGRC.ListLoaders.TreeBaseLoader('GGRC.ListLoaders.TreePageLoader', {}, {
    load: function (params) {
      var snapshots = GGRC.Utils.Snapshots;
      var queryParams = params;
      var result;
      if (snapshots.isSnapshotScope(this.binding.instance) &&
        snapshots.isSnapshotModel(params.data[0].object_name)) {
        params.data[0] = snapshots.transformQuery(params.data[0]);
        queryParams = params;
      }
      return this.model.query(queryParams)
        .then(function (data) {
          result = data;
          return this.insertInstancesFromMappings(data.values);
        }.bind(this))
        .then(function (values) {
          result.values = values;
          return result;
        });
    }
  });
})(GGRC, can);
