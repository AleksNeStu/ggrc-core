# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Help functions."""


def is_multiple_objs(objs, objs_types=None):
  """Check if 'objs' is single or plural objects and if 'objs_types' then
  check it according types, return boolean value.
  Examples:
  if 'objs':
  [obj1, obj2, ...]; (obj1, obj2); (obj1 and obj2) then True
  [obj]; (obj); obj then False
  """
  is_multiple = False
  if isinstance(objs, (list, tuple)) and len(objs) >= 2:
    is_multiple = (all(isinstance(item, objs_types) for item in objs)
                   if objs_types else True)
  return is_multiple


def get_single_obj(objs):
  """Check if 'objs' is single or single in list or tuple and return got object
  accordingly.
  """
  return (objs[0] if (not is_multiple_objs(objs) and
                      isinstance(objs, (list, tuple))) else objs)


def execute_according_to_plurality(objs, method, objs_types=None,
                                   **method_kwargs):
  """Get single object or multiple objects from 'objs' according to
  'objs_types' and execute procedure under got executing method by 'method'.
  """
  # pylint: disable=invalid-name
  return (
      [method(obj, **method_kwargs) for obj in objs] if
      is_multiple_objs(objs, objs_types) else
      method(get_single_obj(objs), **method_kwargs))


def execute_according_to_list_tuple_type(objs, method, **method_kwargs):
  """Check if 'objs' is instance of list or tuple and execute 'method'
  procedure' accordingly.
  """
  # pylint: disable=invalid-name
  return (
      [method(obj, **method_kwargs) for obj in objs] if
      isinstance(objs, (list, tuple)) else method(objs, **method_kwargs))


def convert_to_list(items):
  """Converts items to list items:
  - if items are already list items then skip;
  - if are not list items then convert to list items."""
  list_items = items if isinstance(items, list) else [items, ]
  return list_items


def convert_list_els_to_list(list_els):
  """Converts list elements in list to sequence of elements:
  Example: [1, 2, 3, [4, 5], 6, [7]] = [1, 2, 3, 4, 5, 6, 7]
  """
  converted_list = []
  for element in list_els:
    if isinstance(element, list):
      converted_list.extend(element)
    else:
      converted_list.append(element)
  return converted_list
