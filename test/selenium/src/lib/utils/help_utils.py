# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Help functions."""


def is_multiple_objs(obj_or_objs, types=None):
  """Check if 'obj_or_objs' is single or plural objects and if 'types' then
  check it according types, return boolean value.
  Examples:
  if 'obj_or_objs':
  [obj1, obj2, ...]; (obj1, obj2); (obj1 and obj2) then True
  [obj]; (obj); obj then False
  """
  is_multiple = False
  if isinstance(obj_or_objs, (list, tuple)) and len(obj_or_objs) >= 2:
    is_multiple = (all(isinstance(item, types) for item in obj_or_objs)
                   if types else True)
  return is_multiple


def get_single_obj(obj):
  """Check if 'obj' is single or single in list or tuple and return got object
  accordingly.
  """
  return (obj[0] if (not is_multiple_objs(obj) and
                     isinstance(obj, (list, tuple))) else obj)


def execute_method_according_to_plurality(obj_or_objs, method_name, types=None,
                                          **method_kwargs):
  """Get single object or multiple objects from 'obj_or_objs' according to
  'types' and execute procedure under got executing method by 'method_name'.
  """
  # pylint: disable=invalid-name
  return (
      [method_name(obj, **method_kwargs) for obj in obj_or_objs] if
      is_multiple_objs(obj_or_objs, types) else
      method_name(get_single_obj(obj_or_objs), **method_kwargs))
