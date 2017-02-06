# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

from collections import OrderedDict
from cache import Cache
from cache import all_cache_entries

"""
LocalCache implements the caching mechanism that is local to
the AppEngine instance
"""


class LocalCache(Cache):
  """ LocalCache inherits from cache and it provides caching mechanism that is
      local to a particular GGRC instance

      Attributes:
        cache_entries: Ordered dictionary containing resource id as key and
        value as JSON object (dictionary)
  """

  cache_entries = OrderedDict()

  def __init__(self):
    self.name = 'local'

    for cache_entry in all_cache_entries():
      if cache_entry.cache_type is self.name:
        self.supported_resources[cache_entry.model_plural] = \
            cache_entry.class_name

    for key in self.supported_resources.keys():
      self.cache_entries['collection:' + key] = {}

  def get_name(self):
    return self.name

  def get(self, category, resource, filter):
    """ Get data from local cache for the specified filter

    Args:
      category: collection or stub
      resource: regulation, controls, etc.
      filter: dictionary containing ids and optional attrs

    Returns:
      All or None policy is applied by default
      None on any errors
      Mapping of DTO formatted string, e.g. JSON string representation
    """
    if not self.is_caching_supported(category, resource):
      return None

    cache_key = self.get_key(category, resource)
    if cache_key is None:
      return None

    entries = self.cache_entries.get(cache_key)
    if entries is None:
      return None

    ids, attrs = self.parse_filter(filter)
    if ids is None and attrs is None:
      return None
    else:
      if ids is None:
        return self.get_data(entries.keys(), entries, attrs)
      else:
        return self.get_data(ids, entries, attrs)

  def add(self, category, resource, data, expiration_time=0):
    """ Add data to local cache for the specified data

    Args:
      category: collection or stub
      resource: regulation, controls, etc.
      data: dictionary containing ids and attrs

    Returns:
      None on any errors
      Mapping of DTO formatted string, e.g. JSON string representation
    """
    if not self.is_caching_supported(category, resource):
      return None
    cache_key = self.get_key(category, resource)
    if cache_key is None:
      return None
    if self.cache_entries is None:
      return None
    entries = self.cache_entries.get(cache_key)
    if entries is None:
      return None

    # TODO(dan): Should we perform deep copy of data
    for key in data.keys():
      entries[key] = data.get(key)

    return entries

  def update(self, category, resource, data, expiration_time=0):
    """ Update data in local cache for the specified data
    TODO(dan): updates is not available for local cache
    """
    return None

  def remove(self, category, resource, data, lockadd_seconds=0):
    """ Remove data from local cache for the specified data
    Args:
      category: collection or stub
      resource: regulation, controls, etc.
      data: List of keys

    Returns:
      None on any errors
      mapping of DTO formatted string, e.g. JSON string representation
    """
    if not self.is_caching_supported(category, resource):
      return None
    cache_key = self.get_key(category, resource)
    if cache_key is None:
      return None
    if self.cache_entries is None:
      return None
    entries = self.cache_entries.get(cache_key)

    for key in data.keys():
      del entries[key]

    return entries

  def get_data(self, keys, cacheitems, attrs):
    """ Get data from cache for the given set of keys and attributes in cache
        TODO(dan): all or none default policy is implemeted here, it should be
        in cachemanager
    Args:
      keys: set of keys to search from local cache
      cacheitems: cache entries
      attrs:  set of attributes to search from local cache

    Returns:
      None on any errors
      mapping of DTO formatted string, e.g. JSON string representation
    """
    data = OrderedDict()

    for key in keys:
      if key not in cacheitems:
        #  ALL or None Policy: if a key is not in cache, stop processing and
        #  continue as before going to Data-ORM layer
        return None
      attrvalues = cacheitems.get(key)
      targetattrs = None
      if attrs is None and attrvalues is not None:
        targetattrs = attrvalues.keys()
      elif attrvalues is None:
        # Do nothing as there are no attrs to get
        continue
      else:
        targetattrs = attrs

      attr_dict = {}
      for attr in targetattrs:
        if attr in attrvalues:
          attr_dict[attr] = attrvalues.get(attr)

      data[key] = attr_dict

    return data

  def clean(self):
    """ Cleanup
    """
    self.cache_entries.clear()

  def __repr__(self):
    """ Print content of cache
    """
    return str(self.cache_entries.keys()) + str(self.cache_entries.values())
