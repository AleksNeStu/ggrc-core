# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Regular expressions for use in code."""

WIDGET_TITLE_AND_COUNT = r"(.*) \((.*)\)"
URL_WIDGET_INFO = (
    r"//[0-9a-z\-.]*[:0-9]*?/([a-z_]*)/?(\d*)#?([^/]*)/([a-z_]*)/?(\d*)/*")
TEXT_W_PARENTHESES = r"\([^)]*\) "
TEXT_WO_PARENTHESES = r"\((.*?)\)"
