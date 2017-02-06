# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Provides an HTML cleaner function with sqalchemy compatible API"""

from HTMLParser import HTMLParser

import bleach


# Set up custom tags/attributes for bleach
BLEACH_TAGS = [
    'caption', 'strong', 'em', 'b', 'i', 'p', 'code', 'pre', 'tt', 'samp',
    'kbd', 'var', 'sub', 'sup', 'dfn', 'cite', 'big', 'small', 'address',
    'hr', 'br', 'div', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul',
    'ol', 'li', 'dl', 'dt', 'dd', 'abbr', 'acronym', 'a', 'img',
    'blockquote', 'del', 'ins', 'table', 'tbody', 'tr', 'td', 'th',
] + bleach.ALLOWED_TAGS

BLEACH_ATTRS = {}

ATTRS = [
    'href', 'src', 'width', 'height', 'alt', 'cite', 'datetime',
    'title', 'class', 'name', 'xml:lang', 'abbr'
]

for tag in BLEACH_TAGS:
  BLEACH_ATTRS[tag] = ATTRS


def cleaner(dummy, value, *_):
  """Cleans out unsafe HTML tags.

  Uses bleach and unescape until it reaches a fix point.

  Args:
    dummy: unused, sqalchemy will pass in the model class
    value: html (string) to be cleaned
  Returns:
    Html (string) without unsafe tags.
  """
  # Some cases don't use the title value and it's nullable, so check for that
  if value is None:
    return value
  if not isinstance(value, basestring):
    # no point in sanitizing non-strings
    return value

  parser = HTMLParser()
  value = unicode(value)
  while True:
    lastvalue = value
    value = parser.unescape(
        bleach.clean(value, BLEACH_TAGS, BLEACH_ATTRS, strip=True)
    )
    if value == lastvalue:
      break
  return value
