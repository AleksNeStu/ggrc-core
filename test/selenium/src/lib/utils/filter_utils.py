# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Utils for filter operations."""

from dateutil import parser

import string_utils
from lib.constants import value_aliases as alias
from lib.constants.element import AdminWidgetCustomAttributes


class FilterUtils(object):
  """Class for work with filter utils."""

  @classmethod
  def _get_filter_exp(cls, criteria, grouping_operator=alias.OR_OP):
    """Get filter expression for single and multiple criteria used grouping
    operator. Grouping operator can be "OR" or "AND".
    """
    def get_exp(criterion):
      """Get one filter expression according to criterion.
      Example:
      criterion = ("field", "=", "value")
      :return '"field" = "value"'
      """
      field, operator, value = criterion
      return u'"{}" {} "{}"'.format(field, operator, value)
    return u" {} ".format(grouping_operator).join(
        get_exp(criterion) for criterion in criteria)

  @staticmethod
  def get_filter_exp(field, operator, list_values):
    """Get filter expression to search data by title according to field, operator
    and list of values.
    Example:
    field = "field"
    operator = "="
    list_values = ["value1", "value2"]
    :return '"field" = "value1" OR "field" = "value2"'
    """
    return FilterUtils._get_filter_exp(
        [(field, operator, value) for value in list_values])

  @staticmethod
  def get_filter_exp_by_title(titles):
    """Get filter expression to search data by title according to title(s).
    Example:
    for single title
    titles = "title1"
    :return '"title" = "title1"'

    for list of titles
    titles = ["title1", "title2"]
    :return '"title" = "title1" OR "title" = "title2"'
    """
    list_values = [titles] if type(titles) not in [list, tuple] else titles
    return FilterUtils.get_filter_exp(field="title",
                                      operator=alias.EQUAL_OP,
                                      list_values=list_values)

  def get_filter_exprs_by_ca(self, ca_title, ca_val, ca_type, operator):
    """Return all possible filter expressions for CA according to CA type"""
    if ca_type == AdminWidgetCustomAttributes.CHECKBOX:
      values_to_filter = (
          string_utils.get_list_of_all_cases(alias.YES_VAL) if
          string_utils.get_bool_value_from_arg(ca_val)
          else string_utils.get_list_of_all_cases(alias.NO_VAL))
    elif ca_type == AdminWidgetCustomAttributes.PERSON:
      from lib.service import rest_service
      person = rest_service.ObjectsInfoService().get_obj_by_id(
          *ca_val.split(":"))
      values_to_filter = [person.name, person.email]
    elif ca_type == AdminWidgetCustomAttributes.DATE:
      date_formats = ["%m/%d/%Y", "%m/%Y", "%Y-%m-%d", "%Y-%m", "%Y"]
      date = parser.parse(ca_val).date()
      values_to_filter = [date.strftime(_format) for _format in date_formats]
    else:
      values_to_filter = [ca_val]
    return [self.get_filter_exp(ca_title, operator, [val])
            for val in values_to_filter]

  def get_filter_exprs_by_cas(self, cas_defs, cas_ids_with_val, operator):
    """Return all possible filters expressions for passed Custom Attributes
    Definitions and CAs values.
    """
    cas = [
        (cas_def["title"], cas_val, cas_def["attribute_type"])
        for cas_id, cas_val in cas_ids_with_val.iteritems()
        for cas_def in cas_defs
        if cas_def["id"] == cas_id]
    return ([exprs for ca in cas
             for exprs in self.get_filter_exprs_by_ca(*ca, operator=operator)])
