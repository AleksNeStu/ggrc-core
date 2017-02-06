/*!
    Copyright (C) 2017 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

(function(can, $) {

  GGRC.Components('csvImportWidget', {
    tag: "csv-import",
    template: "<content></content>",
    requestData: null,
    scope: {
      importUrl: "/_service/import_csv",
      import: null,
      filename: "",
      isLoading: false,
      state: "select",
      states: function () {
        var state = this.attr("state") || "select",
            states = {
              select: {
                class: "btn-success",
                text: "Choose CSV file to import"
              },
              analyzing: {
                class: "btn-draft",
                showSpinner: true,
                isDisabled: true,
                text: "Analyzing"
              },
              import: {
                class: "btn-primary",
                text: "Import data",
                isDisabled: function () {
                  var toImport = this.import;  // info on blocks to import
                  var nonEmptyBlockExists;

                  if (!toImport || toImport.length < 1) {
                    return true;
                  }

                  // A non-empty block is a block containing at least one
                  // line that is not ignored (due to errors, etc.).
                  nonEmptyBlockExists = _.any(toImport, function (block) {
                    return block.rows > block.ignored;
                  });

                  return !nonEmptyBlockExists;
                }.bind(this)  // bind the scope object as context
              },
              importing: {
                class: "btn-draft",
                showSpinner: true,
                isDisabled: true,
                text: "Importing"
              },
              success: {
                class: "btn-success",
                isDisabled: true,
                text: "<i class=\"fa fa-check-square-o white\">"+
                  "</i> Import successful"
              }
            };

        return _.extend(states[state], {state: state});
      }
    },
    events: {
      ".state-reset click": function (el, ev) {
        ev.preventDefault();
        this.scope.attr({
          state: "select",
          filename: "",
          import: null
        });
        this.element.find(".csv-upload").val("");
      },
      ".state-select click": function (el, ev) {
        ev.preventDefault();
        this.element.find(".csv-upload").trigger("click");
      },
      ".state-import click": function (el, ev) {
        ev.preventDefault();
        this.scope.attr("state", "importing");
        this.requestData.headers["X-test-only"] = "false";

        $.ajax(this.requestData)
        .done(function (data) {
          var result_count = data.reduce(function (prev, curr) {
                _.each(Object.keys(prev), function(key) {
                  prev[key] += curr[key] || 0;
                });
                return prev;
              }, {created: 0, updated: 0, deleted: 0, ignored: 0});

          this.scope.attr("state", "success");
          this.scope.attr("data", [result_count]);
        }.bind(this))
        .fail(function (data) {
          this.scope.attr("state", "select");
          $("body").trigger("ajax:flash", {
            "error": $(data.responseText.split("\n")[3]).text()
          });
        }.bind(this))
        .always(function () {
          this.scope.attr("isLoading", false);
        }.bind(this));
      },
      ".csv-upload change": function (el, ev) {
        var file = el[0].files[0],
            formData = new FormData();

        this.scope.attr("state", "analyzing");
        this.scope.attr("isLoading", true);
        this.scope.attr("filename", file.name);
        formData.append("file", file);

        this.requestData = {
          type: "POST",
          url: this.scope.attr("importUrl"),
          data: formData,
          cache: false,
          contentType: false,
          processData: false,
          headers: {
            "X-test-only": "true",
            "X-requested-by": "GGRC"
          }
        };

        $.ajax(this.requestData)
        .done(function (data) {
          this.scope.attr("import", _.map(data, function (element) {
            element.data = [];
            if (element.block_errors.concat(element.row_errors).length) {
              element.data.push({
                status: "errors",
                messages: element.block_errors.concat(element.row_errors)
              });
            }
            if (element.block_warnings.concat(element.row_warnings).length) {
              element.data.push({
                status: "warnings",
                messages: element.block_warnings.concat(element.row_warnings)
              });
            }
            return element;
          }));
          this.scope.attr("state", "import");
        }.bind(this))
        .fail(function (data) {
          this.scope.attr("state", "select");
          $("body").trigger("ajax:flash", {
            "error": $(data.responseText.split("\n")[3]).text()
          });
        }.bind(this))
        .always(function () {
          this.scope.attr("isLoading", false);
        }.bind(this));
      }
    }
  });
  var csvImport = $("#csv_import");
  if (csvImport.length) {
    csvImport.html(can.view(GGRC.mustache_path + "/import_export/import.mustache", {}));
  }

})(window.can, window.can.$);
