# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Help functions."""


def is_multiple_objs(objs, types=None):
  """Check if 'objs' is single or plural objects and if 'types' then
  check it according types, return boolean value.
  Examples:
  if 'objs':
  [obj1, obj2, ...]; (obj1, obj2); (obj1 and obj2) then True
  [obj]; (obj); obj then False
  """
  is_multiple = False
  if isinstance(objs, (list, tuple)) and len(objs) >= 2:
    is_multiple = (all(isinstance(item, types) for item in objs)
                   if types else True)
  return is_multiple


def get_single_obj(obj):
  """Check if 'obj' is single or single in list or tuple and return got object
  accordingly.
  """
  return (obj[0] if (not is_multiple_objs(obj) and
                     isinstance(obj, (list, tuple))) else obj)


def execute_method_according_to_plurality(objs, method_name, types=None,
                                          **method_kwargs):
  """Get single object or multiple objects from 'objs' according to
  'types' and execute procedure under got executing method by 'method_name'.
  """
  # pylint: disable=invalid-name
  return (
      [method_name(obj, **method_kwargs) for obj in objs] if
      is_multiple_objs(objs, types) else
      method_name(get_single_obj(objs), **method_kwargs))


def convert_to_list(items):
  """Converts items to list items:
  - if items are already list items then skip;
  - if are not list items then convert to list items."""
  list_items = items if isinstance(items, list) else [items, ]
  return list_items
