# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Utility functions for string operations."""

import random
import string
import uuid
from collections import defaultdict


class Symbols(object):
  """Symbols' constants and variables to call."""
  # pylint: disable=too-few-public-methods
  BLANK = ""
  STAR = "*"
  WHITESPACE = " "
  COMMA = ","
  LESS = "<"
  MORE = ">"
  DOUBLE_QUOTES = '"'
  SINGLE_QUOTE = "'"
  BACK_QUOTE = "`"
  BACKSLASH = "\\"
  PIPE = "|"

  def __init__(self):
    # need exclude to prevent raising coding (encoding) issues
    self.exclude_chars = self.BLANK.join(
        (self.COMMA, self.LESS, self.MORE, self.DOUBLE_QUOTES,
         self.SINGLE_QUOTE, self.BACK_QUOTE, self.BACKSLASH, self.PIPE))
    self.special_chars = self.BLANK.join(
        symbol for symbol in string.punctuation.encode("string-escape")
        if symbol not in self.exclude_chars)
    self.standard_chars = string.letters + self.special_chars + string.digits


class StringMethods(object):
  """String methods."""
  RANDOM_STR_LENGTH = 5
  RANDOM_UUID_LENGTH = 13
  RANDOM_STR_LISTS_COUNT = 3

  @staticmethod
  def random_string(size=RANDOM_UUID_LENGTH, chars=Symbols().standard_chars):
    """Return string with corresponding size that filled by values from
    selected chars.
    """
    return Symbols.BLANK.join(random.choice(chars) for _ in range(size))

  @staticmethod
  def random_uuid(length=RANDOM_UUID_LENGTH):
    """Return string with predefined length base on UUID."""
    return str(uuid.uuid4())[:length]

  @classmethod
  def random_list_strings(
      cls, list_len=RANDOM_STR_LISTS_COUNT, item_size=RANDOM_STR_LENGTH,
      chars=Symbols().standard_chars
  ):
    """Return list of random strings separated by comma."""
    return Symbols.COMMA.join(
        cls.random_string(item_size, chars) for _ in range(list_len))

  @staticmethod
  def get_bool_value_from_arg(arg):
    """Get and return boolean value from argument in title case (return
    True if 'arg': 'Yes', 'True', else return False if 'arg': 'No', 'False')
    else return 'arg' without changing.
    """
    converted_value = arg
    if isinstance(arg, (str, unicode)):
      from lib.constants import value_aliases as alias
      converted_value = (
          True if arg.title() in [alias.YES_VAL, alias.TRUE_VAL, "1"] else
          False if arg.title() in [alias.NO_VAL, alias.FALSE_VAL, "0"] else
          arg)
    return converted_value

  @staticmethod
  def get_list_of_all_cases(*args):
    """Return list of all cases (title, lower, upper) for string if string has
    alpha characters. Return empty list of args are not string type.
    """
    list_of_cases = []
    for arg in args:
      if isinstance(arg, (str, unicode)):
        if (str(arg).isdigit() or
                all(char in string.punctuation for char in str(arg))):
          list_of_cases.append(arg)
        else:
          list_of_cases.extend(
              [str(arg).title(), str(arg).lower(), str(arg).upper()])
    return list_of_cases

  @staticmethod
  def exchange_dicts_items(transform_dict, dicts,
                           is_keys_not_values=True):
    """Exchange items (keys as default or optional values if
    'is_keys_not_values' is False) for 'dicts' (can be dict or list of dicts)
    according to 'transform_dict'. If 'dicts' is dict then return dictionary,
    if 'dicts' is list of dicts then return list of dictionaries.
    Examples:
    'list_dicts=[{"a": 1, "c": 2}, {"a": 3, "c": 4}, {"a": 5, "c": 6}]'
    'is_keys_not_values=True'
    'transform_dict={"a": "a_", "b": "b_"}',
    return:
    'list_dicts=[{"a_": 1, "c": 2}, {"a_": 3, "c": 4}, {"a_": 5, "b": 6}]'
    'is_keys_not_values=False'
    'transform_dict={"a": "5", "b": "4"}',
    return:'list_dicts=[{"a": 5, "c": 2}, {"a": 5, "c":4}, {"a": 5, "b": 6}]'
    """
    def replace_dict_keys(dic):
      """Replace keys of dictionary."""
      return {(transform_dict[k] if transform_dict.get(k) else k): v
              for k, v in dic.iteritems()}

    def replace_dict_values(dic):
      """Replace values of dictionary."""
      return {k: (transform_dict.get(k) if k in transform_dict.keys() else v)
              for k, v in dic.iteritems()}

    if isinstance(dicts, dict):
      dicts = (
          replace_dict_keys(dicts) if is_keys_not_values
          else replace_dict_values(dicts))
    if isinstance(dicts, list) and all(isinstance(dic, dict) for dic in dicts):
      dicts = [
          replace_dict_keys(dic) if is_keys_not_values
          else replace_dict_values(dic) for dic in dicts]
    return dicts

  @staticmethod
  def remap_values_for_list_dicts(dict_of_transform_keys, list_dicts):
    """Remap keys names for old list of dictionaries according
    transformation dictionary {OLD KEY: NEW KEY} and return new updated
    list of dictionaries.
    """
    return [
        {(dict_of_transform_keys[k] if dict_of_transform_keys.get(k) else k): v
         for k, v in dic.iteritems()} for dic in list_dicts]

  @staticmethod
  def convert_list_elements_to_list(list_to_convert):
    """Converts list elements in list to sequence of elements:
    Example: [1, 2, 3, [4, 5], 6, [7]] = [1, 2, 3, 4, 5, 6, 7]
    """
    converted_list = []
    for element in list_to_convert:
      if isinstance(element, list):
        converted_list.extend(element)
      else:
        converted_list.append(element)
    return converted_list

  @staticmethod
  def merge_dicts_by_same_key(list_dicts, is_delete_keys=False):
    """Merger list of two (*or more if not 'is_delete_keys') dictionaries with
    the same keys.
    Examples:
    list_dicts = ({1: 55, 2: 66}, {2: 67, 1: 56})
    If not 'is_delete_keys' then result: {1: [55, 56], 2: [66, 67]}
    If 'is_delete_keys' then result: {55: 56, 66: 67} * len(list_dicts) == 2
    """
    merged_dict = defaultdict(list)
    for _dict in list_dicts:
      if isinstance(_dict, dict):
        for key, val in _dict.iteritems():
          merged_dict[key].append(val)
    if is_delete_keys:
      if (merged_dict != {None: [None, None]} and
         all(len(values) == 2 for values in merged_dict.values())):
        merged_dict = {
            key: val for key, val in merged_dict.items() if
            val and len(val) == 2}
      merged_dict = dict([tuple(item) for item in merged_dict.values()])
    return merged_dict

  @staticmethod
  def is_subset_of_dicts(src_dict, dest_dict):
    """Check is all items of one dictionary 'src_dict' is subset of items of
    another dictionary 'dest_dict', where 'src_dict' should has same or less
    length then 'dest_dict'.
    Examples:
    ({"b": 2, "a": 1}, {"a": 1, "b": 2, "c": 4}) = True
    ({"a": 1, "b": 2, "c": 4}, {"b": 2, "a": 1}) = False
    """
    return all(item in dest_dict.iteritems() for item in src_dict.iteritems())

  @staticmethod
  def get_first_word_from_str(line):
    """Get first word from string."""
    return line.split(None, 1)[0]

  @staticmethod
  def dict_keys_to_upper_case(dictionary):
    """Convert keys of dictionary to upper case."""
    return {k.upper(): v for k, v in dictionary.iteritems()}

  @classmethod
  def update_dicts_values(cls, dic, old_values_list, new_value):
    """Update values in all nested dicts to 'new_value' if value of dict item
    contains in 'old_values_list'.
    """
    if not isinstance(old_values_list, list):
      raise TypeError(
          "Pass list of values to replace. Current type: {}".format(
              type(old_values_list)))
    for key, val in dic.iteritems():
      if isinstance(val, dict):
        cls.update_dicts_values(val, old_values_list, new_value)
      elif val in old_values_list:
        dic[key] = new_value
