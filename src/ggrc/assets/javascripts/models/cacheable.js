/*!
    Copyright (C) 2017 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

// = require can.jquery-all

(function (can, GGRC, CMS) {
  var _oldAttr;
  function makeFindRelated(thistype, othertype) {
    return function (params) {
      if (!params[thistype + '_type']) {
        params[thistype + '_type'] = this.shortName;
      }
      return CMS.Models.Relationship.findAll(params).then(
        function (relationships) {
          var dfds = [];
          var things = new can.Model.List();
          can.each(relationships, function (rel, idx) {
            var dfd;
            if (rel[othertype].selfLink) {
              things.push(rel[othertype]);
            } else {
              dfd = rel[othertype].refresh().then(function (dest) {
                things.splice(idx, 1, dest);
              });
              dfds.push(dfd);
              things.push(dfd);
            }
          });
          return $.when.apply($, dfds).then(function () {
            return things;
          });
        });
    };
  }

  function dateConverter(date, oldValue, fn, key) {
    var conversion = 'YYYY-MM-DD\\THH:mm:ss\\Z';
    var ret;
    if (typeof date === 'object' && date) {
      date = date.getTime();
    }
    if (typeof date === 'number') {
      date /= 1000;
      conversion = 'X';
    }
    if (typeof date === 'string' && ~date.indexOf('/')) {
      conversion = 'MM/DD/YYYY';
    }
    date = date ? date.toString() : null;
    ret = moment(date, conversion);
    if (!ret.unix()) {
      // invalid date computed. Result of unix() is NaN.
      return undefined;
    }

    if (typeof date === 'string' && ret &&
      //  Don't correct timezone for dates
        !/^\d+-\d+-\d+$/.test(date) && !/^\d+\/\d+\/\d+$/.test(date) &&
      //  Don't correct timezone if `moment.js` has already done it
        !/[-+]\d\d:?\d\d/.test(date)) {
      // Use the UTC offset that was active at the moment in time to correct
      // the date's timezone.
      ret.add(ret.utcOffset(), 'minute');
    }

    if (oldValue && oldValue.getTime &&
      ret && ret.toDate().getTime() === oldValue.getTime()) {
      // avoid changing to new Date object if the value is the same.
      return oldValue;
    }
    return ret ? ret.toDate() : undefined;
  }

  function makeDateUnpacker(keys) {
    return function (date, oldValue, fn, attr) {
      return can.reduce(keys, function (curr, key) {
        return curr || (date[key] && dateConverter(
            date[key], oldValue, fn, attr));
      }, null) || date;
    };
  }

  function makeDateSerializer(type, key) {
    var conversion = type === 'date' ?
      'YYYY-MM-DD' :
      'YYYY-MM-DD\\THH:mm:ss\\Z';
    return function (date) {
      var retstr;
      var retval;
      if (date === null || date === undefined) {
        return '';
      }
      if (typeof date !== 'number') {
        date = date.getTime();
      }
      retstr = moment((date / 1000).toString(), 'X');
      if (type !== 'date') {
        retstr = retstr.utc();
      }
      retstr = retstr.format(conversion);
      if (key) {
        retval = {};
        retval[key] = retstr;
      } else {
        retval = retstr;
      }
      return retval;
    };
  }

  can.Model('can.Model.Cacheable', {
    root_object: '',
    attr_list: [
      {
        attr_title: 'Title',
        attr_name: 'title',
        order: 10
      },
      {
        attr_title: 'Admin',
        attr_name: 'owner',
        attr_sort_field: 'owners',
        order: 20
      },
      {
        attr_title: 'Code',
        attr_name: 'slug',
        order: 30
      },
      {
        attr_title: 'State',
        attr_name: 'status',
        order: 40
      },
      {
        attr_title: 'Primary Contact',
        attr_name: 'contact',
        attr_sort_field: 'contact',
        order: 50
      },
      {
        attr_title: 'Secondary Contact',
        attr_name: 'secondary_contact',
        attr_sort_field: 'secondary_contact',
        order: 60
      },
      {
        attr_title: 'Last Updated',
        attr_name: 'updated_at',
        order: 70
      },
      {
        attr_title: 'Review State',
        attr_name: 'os_state',
        order: 80
      }
    ],

    root_collection: '',
    model_singular: '',
    model_plural: '',
    table_singular: '',
    table_plural: '',
    title_singular: '',
    title_plural: '',
    findOne: 'GET {href}',

    makeDestroy: function (destroy) {
      return function (id, instance) {
        return destroy(id).then(function (result) {
          if ('background_task' in result) {
            return CMS.Models.BackgroundTask.findOne(
            {id: result.background_task.id}
          ).then(function (task) {
            if (!task) {
              return;
            }
            return task.poll();
          }).then(function () {
            return instance;
          });
          } else {
            return instance;
          }
        });
      };
    },

    makeFindAll: function (finder) {
      return function (params, success, error) {
        var deferred = can.Deferred();
        var sourceDeferred = finder.call(this, params);
        var self = this;
        var tracker_stop = GGRC.Tracker.start('modelize', self.shortName);

        deferred.then(success, error);
        sourceDeferred.then(function (sourceData) {
          if (sourceData[self.root_collection + '_collection']) {
            sourceData = sourceData[self.root_collection + '_collection'];
          }
          if (sourceData[self.root_collection]) {
            sourceData = sourceData[self.root_collection];
          }

          if (!sourceData.splice) {
            sourceData = [sourceData];
          }

          self._modelize(sourceData, deferred);
        }, function () {
          deferred.reject.apply(deferred, arguments);
        });

        return deferred.done(tracker_stop);
      };
    },

    setup: function (construct, name, statics, prototypes) {
      var overrideFindAll = false;

      if (this.fullName === 'can.Model.Cacheable') {
        this.findAll = function () {
          throw new Error('No default findAll() exists for subclasses of Cacheable');
        };
        this.findPage = function () {
          throw new Error('No default findPage() exists for subclasses of Cacheable');
        };
      } else if ((!statics || !statics.findAll) && this.findAll === can.Model.Cacheable.findAll) {
        if (this.root_collection) {
          this.findAll = 'GET /api/' + this.root_collection;
        } else {
          overrideFindAll = true;
        }
      }
      if (this.root_collection) {
        this.model_plural = statics.model_plural || this.root_collection.replace(/(?:^|_)([a-z])/g, function (s, l) { return l.toUpperCase(); });
        this.title_plural = statics.title_plural || this.root_collection.replace(/(^|_)([a-z])/g, function (s, u, l) { return (u ? ' ' : '') + l.toUpperCase(); });
        this.table_plural = statics.table_plural || this.root_collection;
      }
      if (this.root_object) {
        this.model_singular = statics.model_singular || this.root_object.replace(/(?:^|_)([a-z])/g, function (s, l) { return l.toUpperCase(); });
        this.title_singular = statics.title_singular || this.root_object.replace(/(^|_)([a-z])/g, function (s, u, l) { return (u ? ' ' : '') + l.toUpperCase(); });
        this.table_singular = statics.table_singular || this.root_object;
      }

      if (!can.isFunction(this.findAll)) {
        this.findPage = this.makeFindPage(this.findAll);
      }

    // Prevent event "bleeding" from other members of the Cacheable tree.
    // This fix causes breakages in places where we're expecting model class
    //  events not to be isolated (like in the LHN controller).
    //  I've submitted a fix to CanJS for this but it remains to be seen
    //  whether it gets in and when.  --BM 3/4/14
    // this.__bindEvents = {};

      var that = this;
      if (statics.mixins) {
        can.each(statics.mixins, function (mixin) {
          var _mixin = mixin;
          if (typeof _mixin === 'string') {
            _mixin = can.getObject(_mixin, CMS.Models.Mixins);
          }
          if (_mixin) {
            _mixin.add_to(that);
          } else {
            throw new Error('Error: Cannot find mixin ' +
              mixin + ' for class ' + that.fullName);
          }
        });
        delete this.mixins;
      }

      var ret = this._super.apply(this, arguments);
      if (overrideFindAll)
        this.findAll = can.Model.Cacheable.findAll;

    // set up default attribute converters/serializers for all classes
      can.extend(this.attributes, {
        created_at: 'datetime',
        updated_at: 'datetime'
      });

      return ret;
    },

    init: function () {
      var id_key = this.id;
      var _update = this.update;
      var _create = this.create;
      this.bind('created', function (ev, new_obj) {
        var cache = can.getObject('cache', new_obj.constructor, true);
        if (new_obj[id_key] || new_obj[id_key] === 0) {
          if (!GGRC.Utils.Snapshots.isSnapshot(new_obj)) {
            cache[new_obj[id_key]] = new_obj;
          }
          if (cache[undefined] === new_obj)
            delete cache[undefined];
        }
      });
      this.bind('destroyed', function (ev, old_obj) {
        delete can.getObject('cache', old_obj.constructor, true)[old_obj[id_key]];
      });

    // FIXME:  This gets set up in a chain of multiple calls to the function defined
    //  below when the update endpoint isn't set in the model's static config.
    //  This leads to conflicts not actually rejecting because on the second go-round
    //  the local and remote objects look the same.  --BM 2015-02-06
      this.update = function (id, params) {
        var self = this;
        var ret = _update
        .call(this, id, this.process_args(params))
        .then(
          this.resolve_deferred_bindings.bind(this),
          function (xhr) {
            if (xhr.status === 409) {
              $(document.body).trigger('ajax:flash', {
                warning: 'There was a conflict while saving.' +
                'Your changes have not yet been saved.' +
                ' Please check any fields you were editing and try saving again'
              });
              // TODO: we should show modal window here
              return self.findInCacheById(id).refresh();
            }
            return xhr;
          }
        );
        delete ret.hasFailCallback;
        return ret;
      };
      this.create = function (params) {
        var ret = _create
        .call(this, this.process_args(params))
        .then(this.resolve_deferred_bindings.bind(this));
        delete ret.hasFailCallback;
        return ret;
      };

    // Register this type as a custom attributable type if it is one.
      if (this.is_custom_attributable) {
        if (!GGRC.custom_attributable_types) {
          GGRC.custom_attributable_types = [];
        }
        GGRC.custom_attributable_types.push(can.extend({}, this));
      }
    },

    resolve_deferred_bindings: function (obj) {
      var _pjs;
      var refresh_dfds = [];
      var dfds = [];
      var dfds_apply;
      if (obj._pending_joins && obj._pending_joins.length) {
        _pjs = obj._pending_joins.slice(0); // refresh of bindings later will muck up the pending joins on the object
        can.each(can.unique(can.map(_pjs, function (pj) {
          return pj.through;
        })), function (binding) {
          refresh_dfds.push(obj.get_binding(binding).refresh_stubs());
        });

        return $.when.apply($, refresh_dfds)
      .then(function () {
        can.each(obj._pending_joins, function (pj) {
          var inst;
          var binding = obj.get_binding(pj.through);
          var model = (CMS.Models[binding.loader.model_name] ||
                       GGRC.Models[binding.loader.model_name]);
          if (pj.how === 'add') {
            // Don't re-add -- if the object is already mapped (could be direct or through a proxy)
            // move on to the next one
            if (_.includes(_.map(binding.list, 'instance'), pj.what) ||
               (binding.loader.option_attr &&
                _.includes(_.map(binding.list, function (join_obj) {
                  return join_obj.instance[binding.loader.option_attr];
                }), pj.what))) {
              return;
            }
            inst = pj.what instanceof model
              ? pj.what
              : new model({
                context: obj.context
              });
            dfds.push(
              $.when(pj.what !== inst && pj.what.isNew() ? pj.what.save() : null)
               .then(function () {
                 if (binding.loader.object_attr) {
                   inst.attr(binding.loader.object_attr, obj.stub());
                 }
                 if (binding.loader.option_attr) {
                   inst.attr(binding.loader.option_attr, pj.what.stub());
                 }
                 if (pj.extra) {
                   inst.attr(pj.extra);
                 }
                 return inst.save();
               })
            );
          } else if (pj.how === 'update') {
            binding.list.forEach(function (bound_obj) {
              if (bound_obj.instance === pj.what ||
                  bound_obj.instance[binding.loader.option_attr] === pj.what) {
                bound_obj.get_mappings().forEach(function (mapping) {
                  dfds.push(mapping.refresh().then(function () {
                    if (pj.extra) {
                      mapping.attr(pj.extra);
                    }
                    return mapping.save();
                  }));
                });
              }
            });
          } else if (pj.how === 'remove') {
            can.map(binding.list, function (bound_obj) {
              if (bound_obj.instance === pj.what || bound_obj.instance[binding.loader.option_attr] === pj.what) {
                can.each(bound_obj.get_mappings(), function (mapping) {
                  dfds.push(mapping.refresh().then(function () {
                    mapping.destroy();
                  }));
                });
              }
            });
          }
        });

        dfds_apply = $.when.apply($, dfds);

        obj.attr('_pending_joins', []);
        obj.attr('_pending_joins_dfd', dfds_apply);

        return dfds_apply.then(function () {
          can.trigger(this, 'resolved');
          return obj.refresh();
        });
      });
      }
      return obj;
    },

    findInCacheById: function (id) {
      return can.getObject('cache', this, true)[id];
    },

    removeFromCacheById: function (key) {
      return delete this.store[key];
    },

    newInstance: function (args) {
      var cache = can.getObject('cache', this, true);
      var isKeyExists = args && args[this.id];
      var isObjectExists = isKeyExists && cache[args[this.id]];
      var notSnapshot = args && !GGRC.Utils.Snapshots.isSnapshot(args);
      if (isObjectExists && notSnapshot) {
        // cache[args.id].attr(args, false); //CanJS has bugs in recursive merging
        // (merging -- adding properties from an object without removing existing ones
        //  -- doesn't work in nested objects).  So we're just going to not merge properties.
        return cache[args[this.id]];
      }
      return this._super.apply(this, arguments);
    },
    process_args: function (args) {
      var pargs = {};
      var obj = pargs;
      var src;
      var go_names;
      if (this.root_object && !(this.root_object in args)) {
        obj = pargs[this.root_object] = {};
      }
      src = args.serialize ? args.serialize() : args;
      go_names = Object.keys(src);
      for (var i = 0; i < (go_names.length || 0); i++) {
        obj[go_names[i]] = src[go_names[i]];
      }
      return pargs;
    },

    findRelated: makeFindRelated('source', 'destination'),
    findRelatedSource: makeFindRelated('destination', 'source'),

    models: function (params) {
      var ms;
      if (params[this.root_collection + '_collection']) {
        params = params[this.root_collection + '_collection'];
      }
      if (params[this.root_collection]) {
        params = params[this.root_collection];
      }
      if (!params || params.length === 0)
        return new this.List();
      ms = this._super(params);
      if (params instanceof can.Map || params instanceof can.List) {
        params.replace(ms);
        return params;
      }
      return ms;
    },

    query: function (request) {
      var deferred = can.Deferred();
      var self = this;

      GGRC.Utils.QueryAPI.makeRequest(request)
        .then(function (sourceData) {
          var values = [];
          var listDfd = can.Deferred();
          if (sourceData.length) {
            sourceData = sourceData[0];
          } else {
            sourceData = {};
          }

          if (sourceData[self.shortName]) {
            sourceData = sourceData[self.shortName];
            values = sourceData.values;
          } else if (sourceData.Snapshot) {
            // This is response with snapshots - convert it to objects
            sourceData = sourceData.Snapshot;
            values = GGRC.Utils.Snapshots.toObjects(sourceData.values);
          }

          if (!values.splice) {
            values = [values];
          }
          self._modelize(values, listDfd);

          listDfd.then(function (list) {
            sourceData.values = list;
            deferred.resolve(sourceData);
          });
        }, function () {
          deferred.reject.apply(deferred, arguments);
        });

      return deferred;
    },

    queryAll: function (request) {
      var deferred = can.Deferred();

      GGRC.Utils.QueryAPI.makeRequest(request)
        .then(function (sourceData) {
          var values = [];

          sourceData = sourceData.length ? sourceData : {};

          values = _.map(sourceData, function (object) {
            return _.compact(_.map(object, function (obj, key) {
              if (obj && obj.ids) {
                return _.map(obj.ids, function (item) {
                  return {id: item, type: key};
                });
              }
              if (obj && obj.values) {
                return obj.values;
              }
            }));
          });

          values = _.flattenDeep(values);

          deferred.resolve(values);
        }, deferred.reject.bind(deferred));

      return deferred.promise();
    },

  _modelize: function (sourceData, deferred) {
    var obsList = new this.List([]);
    var index = 0;
    var self = this;
    function modelizeMS(ms) {
      var item;
      var start;
      var instances = [];

      start = Date.now();
      while (sourceData.length > index && (Date.now() - start) < ms) {
        can.batch.start();
        item = sourceData[index];
        index += 1;
        instances.push.apply(instances, self.models([item]));
        can.batch.stop();
      }
      can.batch.start();
      obsList.push.apply(obsList, instances);
      can.batch.stop();
    }

    // Trigger a setTimeout loop to modelize remaining objects
    (function cb() {
      modelizeMS(100);
      if (sourceData.length > index) {
        setTimeout(cb, 5);
      } else {
        deferred.resolve(obsList);
      }
    })();
  },

    object_from_resource: function (params) {
      var obj_name = this.root_object;
      if (!params) {
        return params;
      }
      if (typeof obj_name !== 'undefined' && params[obj_name]) {
        for (var i in params[obj_name]) {
          if (params[obj_name].hasOwnProperty(i)) {
            params.attr
            ? params.attr(i, params[obj_name][i])
            : (params[i] = params[obj_name][i]);
          }
        }
        if (params.removeAttr) {
          params.removeAttr(obj_name);
        } else {
          delete params[obj_name];
        }
      }
      return params;
    },

    stubs: function (params) {
      return new can.List(can.map(this.models(params), function (instance) {
        if (!instance) {
          return instance;
        }
        return instance.stub();
      }));
    },

    stub: function (params) {
      if (!params) {
        return params;
      }
      return this.model(params).stub();
    },
    model: function (params) {
      var model;
      params = this.object_from_resource(params);
      if (!params)
        return params;
      model = this.findInCacheById(params[this.id]) ||
        (params.provisional_id &&
        can.getObject('provisional_cache', can.Model.Cacheable, true)[params.provisional_id]);
      if (model && !GGRC.Utils.Snapshots.isSnapshot(params)) {
        if (model.provisional_id && params.id) {
          delete can.Model.Cacheable.provisional_cache[model.provisional_id];
          model.removeAttr('provisional_id');
          model.constructor.cache[params.id] = model;
          model.attr('id', params.id);
        }
        model.attr(params);
      } else {
        model = this._super(params);
      }
      return model;
    },

    convert: {
      date: dateConverter,
      datetime: dateConverter,
      packaged_datetime: makeDateUnpacker(['dateTime', 'date'])
    },
    serialize: {
      datetime: makeDateSerializer('datetime'),
      date: makeDateSerializer('date'),
      packaged_datetime: makeDateSerializer('datetime', 'dateTime')
    },
    tree_view_options: {
      display_attr_names: ['title', 'owner', 'status'],
      mandatory_attr_names: ['title']
    },
    obj_nav_options: {},
    list_view_options: {},

    makeFindPage: function (findAllSpec) {
    /* Create a findPage function that will return a paging object that will
     * provide access to the model items provided in a single page as well
     * as paging capability to retrieve the named pages provided in the
     * response.
     *
     * findPage returns an object with two properties:
     * {this.options.model.root_collection}_collection and paging. The models
     * property will be an array of all model instances in the page retrieved
     * for the collection. The paging property will be an object that can be
     * used to retrieve other named pages from the collection.  The names of
     * pages include first, prev, next, last. Named page properties will
     * either be functions or the null value in the case where there is no
     * link available in the collection under that name.  Paging functions
     * have the same type of return value as the findPage function.
     *
     * This method assumes that findAllSpec is a string like
     * "GET /api/programs". If this assumption is invalid, this function
     * WILL NOT work correctly.
     */
      var parts;
      var method;
      var collectionUrl;
      var baseParams;

      var that = this;

      function makePaginator(paging, baseParams, scope) {
        function getPage(pageName) {
          if (paging[pageName]) {
            return function () {
              // the paging ("next", "prev", etc. URLs already include query
              // string params, thus passing null for them
              return findPageFunc(paging[pageName], null, baseParams, scope);
            };
          }
          return null;
        }

        return {
          count: paging.count,
          total: paging.total,
          first: getPage('first'),
          prev: getPage('prev'),
          next: getPage('next'),
          last: getPage('last'),
          has_next: function () {
            return this.next !== null;
          },
          has_prev: function () {
            return this.prev !== null;
          }
        };
      }

      function findPageFunc(url, data, params, scope) {
        var ajaxOptions = can.extend({
          url: url,
          data: data
        }, params);

        return can.ajax(ajaxOptions).then(function (response) {
          var collection = response[that.root_collection + '_collection'];
          var paginator = makePaginator(collection.paging, params, scope);
          var ret = {
            paging: paginator
          };
          ret[scope.root_collection + '_collection'] =
            scope.models(collection[scope.root_collection]);
          return ret;
        });
      }

      if (typeof findAllSpec === 'string') {
        parts = findAllSpec.split(' ');
        method = parts.length === 2 ? parts[0] : 'GET';
        collectionUrl = parts.length === 2 ? parts[1] : parts[0];
      } else if (typeof findAllSpec === 'object') {
        method = findAllSpec.type || 'GET';
        collectionUrl = findAllSpec.url;
      } else {
        return; // TODO make a pager if findAllSpec is a function.
      }

      baseParams = {
        type: method,
        dataType: 'json'
      };

      return function (params) {
        params = params || {};
        if (!params.__page) {
          params.__page = 1;
        }
        if (!params.__page_size) {
          params.__page_size = 50;
        }
        return findPageFunc(collectionUrl, params, baseParams, that);
      };
    },

    get_mapper: function (name) {
      var mapper;
      var mappers = GGRC.Mappings.get_mappings_for(this.shortName);
      if (mappers) {
        mapper = mappers[name];
        return mapper;
      }
    }
  }, {
    init: function () {
      var cache = can.getObject('cache', this.constructor, true);
      var id_key = this.constructor.id;
      var that = this;
      GGRC.Utils.Snapshots.setAttrs(this);
      if ((this[id_key] || this[id_key] === 0) &&
        !GGRC.Utils.Snapshots.isSnapshot(this)) {
        cache[this[id_key]] = this;
      }
      this.attr('class', this.constructor);
      this.notifier = new PersistentNotifier({name: this.constructor.model_singular});

      if (!this._pending_joins) {
        this.attr('_pending_joins', []);
      }
    },
    load_custom_attribute_definitions: function () {
      var definitions;
      if (this.attr('custom_attribute_definitions')) {
        return;
      }
      if (GGRC.custom_attr_defs === undefined) {
        GGRC.custom_attr_defs = {};
        console.warn('Missing injected custom attribute definitions');
      }
      definitions = can.map(GGRC.custom_attr_defs, function (def) {
        var idCheck = !def.definition_id || def.definition_id === this.id;
        if (idCheck && def.definition_type === this.constructor.table_singular) {
          return def;
        }
      }.bind(this));
      this.attr('custom_attribute_definitions', definitions);
    },

  /**
   * Setup the instance's custom attribute validations, and initialize their
   * values, if necessary.
   */
    setup_custom_attributes: function () {
      var self = this;
      var key;

    // Remove existing custom_attribute validations,
    // some of them might have changed
      for (key in this.class.validations) {
        if (key.indexOf('custom_attributes.') === 0) {
          delete this.class.validations[key];
        }
      }

    // setup validators for custom attributes based on their definitions
      can.each(this.custom_attribute_definitions, function (definition) {
        if (definition.mandatory && !this.ignore_ca_errors) {
          if (definition.attribute_type === 'Checkbox') {
            self.class.validate('custom_attributes.' + definition.id,
              function (val) {
                return val ? '' : 'must be checked';
              });
          } else {
            self.class.validateNonBlank('custom_attributes.' + definition.id);
          }
        }
      }.bind(this));

    // if necessary, initialize custom attributes' values on the instance
      if (!this.custom_attributes) {
        this.attr('custom_attributes', new can.Map());
        can.each(this.custom_attribute_values, function (value) {
          var def;
          var attributeValue;
          var object;
          value = value.isStub ? value : value.reify();
          def = _.find(this.custom_attribute_definitions, {
            id: value.custom_attribute_id
          });
          if (def) {
            if (def.attribute_type.startsWith('Map:')) {
              object = value.attribute_object;
              attributeValue = object.type + ':' + object.id;
            } else {
              attributeValue = value.attribute_value;
            }
            self.custom_attributes.attr(value.custom_attribute_id,
                                      attributeValue);
          }
        }.bind(this));
      }

    // Due to the current lack on any information on sort order, just use the
    // order the custom attributes were defined in.
      function sortById(a, b) {
        return a.id - b.id;
      }
      // Sort only if definitions were attached.
      if (this.attr('custom_attribute_definitions')) {
        this.attr('custom_attribute_definitions').sort(sortById);
      }
    },

    _custom_attribute_map: function (attrId, object) {
      var definition;
      attrId = Number(attrId); // coming from mustache this will be a string
      definition = _.find(this.custom_attribute_definitions, {id: attrId});

      if (!definition || !definition.attribute_type.startsWith('Map:')) {
        return;
      }
      if (typeof object === 'string' && object.length > 0) {
        return;
      }
      object = object.stub ? object.stub() : undefined;
      if (object) {
        this.custom_attributes.attr(attrId, object.type + ':' + object.id);
      } else {
        this.custom_attributes.attr(attrId, 'Person:None');
      }
    },
    computed_errors: function () {
      var errors = this.errors();
      if (this.attr('_suppress_errors')) {
        return null;
      }
      return errors;
    },
    computed_unsuppressed_errors: function () {
      return this.errors();
    },
    get_list_counter: function (name) {
      var binding = this.get_binding(name);
      if (!binding) {
        return can.Deferred().reject();
      }
      return binding.refresh_count();
    },

    get_list_loader: function (name) {
      var binding = this.get_binding(name);
      return binding.refresh_list();
    },

    get_mapping: function (name) {
      var binding = this.get_binding(name);
      if (binding) {
        binding.refresh_list();
        return binding.list;
      }
      return [];
    },

    get_mapping_deferred: function (name) {
      return this.get_binding(name).refresh_list();
    },

  // This retrieves the potential orphan stats for a given instance
  // Example: "This may also delete 3 Sections, 2 Controls, and 4 object mappings."
    get_orphaned_count: function () {
      if (!this.get_binding('orphaned_objects')) {
        return can.Deferred().reject();
      }
      return this.get_list_loader('orphaned_objects').then(function (list) {
        var objects = [];
        var mappings = [];
        var counts = {};
        var result = [];
        var parts = 0;

        function is_join(mapping) {
          if (mapping.mappings.length > 0) {
            for (var i = 0, child; child = mapping.mappings[i]; i++) {
              if (child = is_join(child)) {
                return child;
              }
            }
          }
          return mapping.instance &&
            mapping.instance instanceof can.Model.Join &&
            mapping.instance;
        }
        can.each(list, function (mapping) {
          var inst;
          if (inst = is_join(mapping))
            mappings.push(inst);
          else
          objects.push(mapping.instance);
        });

      // Generate the summary
        if (objects.length || mappings.length) {
          result.push('This may also delete');
        }
        if (objects.length) {
          can.each(objects, function (instance) {
            var title = instance.constructor.title_singular;
            counts[title] = counts[title] ||
              {
                model: instance.constructor,
                count: 0
              };
            counts[title].count++;
          });
          can.each(counts, function (count, i) {
            parts++;
            result.push(count.count + ' ' + (count.count === 1 ? count.model.title_singular : count.model.title_plural) + ',');
          });
        }
        if (mappings.length) {
          parts++;
          result.push(mappings.length + ' object mapping' + (mappings.length !== 1 ? 's' : ''));
        }

      // Clean up commas, add an "and" if appropriate
        parts >= 1 && parts <= 2 && (result[result.length - 1] = result[result.length - 1].replace(',', ''));
        parts === 2 && (result[result.length - 2] = result[result.length - 2].replace(',', ''));
        parts >= 2 && result.splice(result.length - 1, 0, 'and');
        return result.join(' ') + (objects.length || mappings.length ? '.' : '');
      });
    },

    _get_binding_attr: function (mapper) {
      if (typeof (mapper) === 'string') {
        return '_' + mapper + '_binding';
      }
    },

  // checks if binding exists without throwing debug statements
  // modeled after what get_binding is doing
    has_binding: function (mapper) {
      var binding;
      var mapping;
      var binding_attr = this._get_binding_attr(mapper);

      if (binding_attr) {
        binding = this[binding_attr];
      }

      if (!binding) {
        if (typeof (mapper) === 'string') {
          mapping = this.constructor.get_mapper(mapper);
          if (!mapping) {
            return false;
          }
        } else if (!(mapper instanceof GGRC.ListLoaders.BaseListLoader)) {
          return false;
        }
      }

      return true;
    },

    get_binding: function (mapper) {
      var mapping;
      var binding;
      var binding_attr = this._get_binding_attr(mapper);

      if (binding_attr) {
        binding = this[binding_attr];
      }

      if (!binding) {
        if (typeof (mapper) === 'string') {
        // Lookup and attach named mapper
          mapping = this.constructor.get_mapper(mapper);
          if (!mapping)
            console.debug('No such mapper:  ' + this.constructor.shortName + '.' + mapper);
          else
          binding = mapping.attach(this);
        } else if (mapper instanceof GGRC.ListLoaders.BaseListLoader) {
        // Loader directly provided, so just attach
          binding = mapper.attach(this);
        } else {
          console.debug('Invalid mapper specified:', mapper);
        }
        if (binding && binding_attr) {
          this[binding_attr] = binding;
          binding.name = this.constructor.shortName + '.' + mapper;
        }
      }
      return binding;
    },
    refresh: function (params) {
      var dfd;
      var href = this.selfLink || this.href;
      var that = this;

      if (!href) {
        return can.Deferred().reject();
      }
      if (!this._pending_refresh) {
        this._pending_refresh = {
          dfd: can.Deferred(),
          fn: _.throttle(function () {
            var dfd = that._pending_refresh.dfd;
            can.ajax({
              url: href,
              params: params,
              type: 'get',
              dataType: 'json'
            })
          .then(function (resources) {
            delete that._pending_refresh;
            return resources;
          })
          .then($.proxy(that.constructor, 'model'))
          .done(function (response) {
            response.backup();
            dfd.resolve.apply(dfd, arguments);
          })
          .fail(function () {
            dfd.reject.apply(dfd, arguments);
          });
          }, 1000, {trailing: false})
        };
      }
      dfd = this._pending_refresh.dfd;
      this._pending_refresh.fn();
      return dfd;
    },
  // TODO: should be refactored and sliced on multiple functions
    serialize: function () {
      var serial = {};
      var fnName;
      var val;
      if (arguments.length) {
        return this._super.apply(this, arguments);
      }
      /* Serialize only meaningful properties */
      Object.keys(this._data).forEach(function (name) {
        val = this[name];
        if (this.constructor.attributes && this.constructor.attributes[name]) {
          fnName = this.constructor.attributes[name];
          fnName = fnName.substr(fnName.lastIndexOf('.') + 1);
          if (fnName === 'stubs' || fnName === 'get_stubs' ||
          fnName === 'models' || fnName === 'get_instances') {
          // val can be null in some cases
            if (val) {
              serial[name] = val.stubs().serialize();
            }
          } else if (fnName === 'stub' || fnName === 'get_stub' ||
          fnName === 'model' || fnName === 'get_instance') {
            serial[name] = (val ? val.stub().serialize() : null);
          } else {
            serial[name] = val;
          }
        } else if (val && can.isFunction(val.save)) {
          serial[name] = val.stub().serialize();
        } else if (typeof val === 'object' && val !== null && val.length) {
          serial[name] = can.map(val, function (v) {
            var isModel = v && can.isFunction(v.save);
            return isModel ?
                   v.stub().serialize() :
                   (v && v.serialize) ? v.serialize() : v;
          });
        } else if (!can.isFunction(val)) {
          if (this[name] && this[name].isComputed) {
            serial[name] = val && val.serialize ? val.serialize() : val;
          } else {
            serial[name] = this[name] && this[name].serialize ?
            this[name].serialize() :
            serial[name] = val;
          }
        }
      }.bind(this));
      return serial;
    },
    display_name: function () {
      var displayName = this.title || this.name;

      if (_.isUndefined(displayName)) {
        return '"' + this.type + ' ID: ' + this.id + '" (DELETED)';
      }

      return displayName;
    },
    display_type: function () {
      return this.type;
    },
    autocomplete_label: function () {
      return this.title;
    },
    get_permalink: function () {
      var dfd = can.Deferred();
      var constructor = this.constructor;
      if (!constructor.permalink_options) {
        return dfd.resolve(this.viewLink);
      }
      $.when(this.refresh_all.apply(this, constructor.permalink_options.base.split(':')))
        .then(function (base) {
          return dfd.resolve(_.template(constructor.permalink_options.url)({base: base, instance: this}));
        }.bind(this));
      return dfd.promise();
    },

    /*
     * Set up a deferred join object update when this object is updated.
     */
    mark_for_update: function (join_attr, obj, extra_attrs, options) {
      obj = obj.reify ? obj.reify() : obj;
      extra_attrs = _.isEmpty(extra_attrs) ? undefined : extra_attrs;

      this.remove_duplicate_pending_joins(obj);
      this._pending_joins.push({
        how: 'update',
        what: obj,
        through: join_attr,
        extra: extra_attrs,
        opts: options
      });
    },
    /*
     * Set up a deferred join object deletion when this object is updated.
     */
    mark_for_deletion: function (join_attr, obj, extra_attrs, options) {
      obj = obj.reify ? obj.reify() : obj;

      this.remove_duplicate_pending_joins(obj);
      this._pending_joins.push({how: 'remove', what: obj, through: join_attr, opts: options});
    },

    /*
     * Set up a deferred join object creation when this object is updated.
     */
    mark_for_addition: function (joinAttr, obj, extraAttrs, options) {
      obj = obj.reify ? obj.reify() : obj;
      extraAttrs = _.isEmpty(extraAttrs) ? undefined : extraAttrs;

      this.remove_duplicate_pending_joins(obj);
      this._pending_joins.push({
        how: 'add',
        what: obj,
        through: joinAttr,
        extra: extraAttrs,
        opts: options
      });
    },

    remove_duplicate_pending_joins: function (obj) {
      var joins;
      var len;
      if (!this._pending_joins) {
        this.attr('_pending_joins', []);
      }
      len = this._pending_joins.length;
      joins = _.filter(this._pending_joins, function (val) {
        return val.what !== obj;
      });

      if (len !== joins.length) {
        this.attr('_pending_joins').replace(joins);
      }
    },

    delay_resolving_save_until: function (dfd) {
      return this.notifier.queue(dfd);
    },
    _save: function () {
      var that = this;
      var _super = Array.prototype.pop.call(arguments);
      var isNew = this.isNew();
      var xhr;
      var dfd = this._dfd;
      var pre_save_notifier =
        new PersistentNotifier({name:
        this.constructor.model_singular + ' (pre-save)'});

      if (this.before_save) {
        this.before_save(pre_save_notifier);
      }
      if (isNew) {
        this.attr('provisional_id', 'provisional_' + Date.now());
        can.getObject('provisional_cache',
          can.Model.Cacheable, true)[this.provisional_id] = this;
        if (this.before_create) {
          this.before_create(pre_save_notifier);
        }
      } else {
        if (this.before_update) {
          this.before_update(pre_save_notifier);
        }
      }

      pre_save_notifier.on_empty(function () {
        xhr = _super.apply(that, arguments)
      .then(function (result) {
        if (isNew) {
          that.after_create && that.after_create();
        } else {
          that.after_update && that.after_update();
        }
        that.after_save && that.after_save();
        return result;
      }, function (xhr, status, message) {
        that.save_error && that.save_error(xhr.responseText);
        return new can.Deferred().reject(xhr, status, message);
      })
      .fail(function (response) {
        that.notifier.on_empty(function () {
          dfd.reject(that, response);
        });
      })
      .done(function () {
        that.notifier.on_empty(function () {
          dfd.resolve(that);
        });
      });

        GGRC.delay_leaving_page_until(xhr);
        GGRC.delay_leaving_page_until(dfd);
      });
      return dfd;
    },
    save: function () {
      Array.prototype.push.call(arguments, this._super);
      this._dfd = new can.Deferred();
      GGRC.SaveQueue.enqueue(this, arguments);
      return this._dfd;
    },
    refresh_all: function () {
      var props = Array.prototype.slice.call(arguments, 0);

      return RefreshQueue.refresh_all(this, props);
    },
    refresh_all_force: function () {
      var props = Array.prototype.slice.call(arguments, 0);

      return RefreshQueue.refresh_all(this, props, true);
    },
    hash_fragment: function () {
      var type = can.spaceCamelCase(this.type || '')
            .toLowerCase()
            .replace(/ /g, '_');

      return [type, this.id].join('/');
    }
  });
  /* TODO: hack on can.Observe should be removed or at least placed outside of Cacheable Model Class */
  _oldAttr = can.Observe.prototype.attr;
  can.Observe.prototype.attr = function (key, val) {
    if (key instanceof can.Observe) {
      if (arguments[0] === this) {
        return this;
      }
      return _oldAttr.apply(this, [key.serialize()]);
    }
    return _oldAttr.apply(this, arguments);
  };

  can.Observe.prototype.stub = function () {
    var type;
    var id;

    if (!(this instanceof can.Model || this instanceof can.Stub))
      console.debug('.stub() called on non-stub, non-instance object', this);

    if (this instanceof can.Stub) {
      return this;
    }

    if (this instanceof can.Model) {
      type = this.constructor.shortName;
    } else {
      type = this.type;
    }

    if (this.constructor.id) {
      id = this[this.constructor.id];
    } else {
      id = this.id;
    }

    if (!id && id !== 0) {
      return null;
    }

    return can.Stub.get_or_create({
      id: id,
      href: this.selfLink || this.href,
      type: type
    });
  };

  can.Observe('can.Stub', {
    get_or_create: function (obj) {
      var id = obj.id;
      var stub;
      var type = obj.type;

      CMS.Models.stub_cache = CMS.Models.stub_cache || {};
      CMS.Models.stub_cache[type] = CMS.Models.stub_cache[type] || {};
      if (!CMS.Models.stub_cache[type][id]) {
        stub = new can.Stub(obj);
        CMS.Models.stub_cache[type][id] = stub;
      }
      return CMS.Models.stub_cache[type][id];
    }
  }, {
    init: function () {
      var that = this;
      this._super.apply(this, arguments);
      this._instance().bind('destroyed', function (ev) {
        // Trigger propagating `change` event to convey `stub-destroyed` message
        can.trigger(
          that, 'change', ['stub_destroyed', 'stub_destroyed', that, null]);
        delete CMS.Models.stub_cache[that.type][that.id];
      });
    },

    _model: function () {
      return CMS.Models[this.type] || GGRC.Models[this.type];
    },

    _instance: function () {
      if (!this.__instance) {
        this.__instance = this._model().model(this);
      }
      return this.__instance;
    },

    getInstance: function () {
      return this._instance();
    }
  });

  can.Observe.List.prototype.stubs = function () {
    return new can.Observe.List(can.map(this, function (obj) {
      return obj.stub();
    }));
  };

  can.Observe.prototype.reify = function () {
    var type;
    var model;

    if (this instanceof can.Model) {
      return this;
    }
    if (!(this instanceof can.Stub)) {
      console.debug('`reify()` called on non-stub, non-instance object', this);
    }

    type = this.type;
    model = CMS.Models[type] || GGRC.Models[type];

    if (!model) {
      console.debug('`reify()` called with unrecognized type', this);
    } else {
      return model.model(this);
    }
  };

  can.Observe.List.prototype.reify = function () {
    return new can.Observe.List(can.map(this, function (obj) {
      return obj.reify();
    }));
  };
})(window.can, window.GGRC, window.CMS);
