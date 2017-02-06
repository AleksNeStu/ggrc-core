# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Base objects for csv file converters."""

from collections import defaultdict

from ggrc import settings
from ggrc.utils import structures
from ggrc.cache.memcache import MemCache
from ggrc.converters import get_exportables
from ggrc.converters.base_block import BlockConverter
from ggrc.converters.import_helper import extract_relevant_data
from ggrc.converters.import_helper import split_array
from ggrc.fulltext import get_indexer


class Converter(object):
  """Base class for csv converters.

  This class contains and handles all block converters and makes sure that
  blocks and columns are handled in the correct order. It also holds cache
  objects that need to be shared between all blocks and rows for mappings and
  similar uses.
  """

  CLASS_ORDER = [
      "Person",
      "Program",
      "Risk Assessment",
      "Audit",
      "Policy",
      "Regulation",
      "Standard",
      "Section",
      "Control",
      "Assessment Template",
      "Custom Attribute Definition",
      "Assessment",
      "Workflow",
      "Task Group",
      "Task Group Task",
  ]

  priority_columns = [
      "email",
      "slug",
      "delete",
      "task_type",
  ]

  def __init__(self, **kwargs):
    self.dry_run = kwargs.get("dry_run", True)
    self.csv_data = kwargs.get("csv_data", [])
    self.ids_by_type = kwargs.get("ids_by_type", [])
    self.block_converters = []
    self.new_objects = defaultdict(structures.CaseInsensitiveDict)
    self.shared_state = {}
    self.response_data = []
    self.exportable = get_exportables()
    self.indexer = get_indexer()

  def to_array(self):
    self.block_converters_from_ids()
    self.handle_row_data()
    return self.to_block_array()

  def to_block_array(self):
    """ exporting each in it's own block separated by empty lines

    Generate 2d array where each cell represents a cell in a csv file
    """
    csv_data = []
    for block_converter in self.block_converters:
      csv_header, csv_body = block_converter.to_array()
      # multi block csv must have first column empty
      two_empty_lines = [[], []]
      block_data = csv_header + csv_body + two_empty_lines
      for line in block_data:
        line.insert(0, "")
      block_data[0][0] = "Object type"
      block_data[1][0] = block_converter.name
      csv_data.extend(block_data)
    return csv_data

  def import_csv(self):
    self.block_converters_from_csv()
    self.row_converters_from_csv()
    self.handle_priority_columns()
    self.import_objects()
    self.import_secondary_objects()
    self.drop_cache()

  def handle_priority_columns(self):
    for attr_name in self.priority_columns:
      for block_converter in self.block_converters:
        block_converter.handle_row_data(attr_name)

  def handle_row_data(self):
    for converter in self.block_converters:
      converter.handle_row_data()

  def row_converters_from_csv(self):
    for converter in self.block_converters:
      converter.row_converters_from_csv()

  def block_converters_from_ids(self):
    """ fill the block_converters class variable

    Generate block converters from a list of tuples with an object name and ids
    """
    object_map = {o.__name__: o for o in self.exportable.values()}
    for object_data in self.ids_by_type:
      class_name = object_data["object_name"]
      object_class = object_map[class_name]
      object_ids = object_data.get("ids", [])
      fields = object_data.get("fields")
      block_converter = BlockConverter(self, object_class=object_class,
                                       fields=fields, object_ids=object_ids,
                                       class_name=class_name)
      block_converter.check_block_restrictions()
      block_converter.row_converters_from_ids()
      self.block_converters.append(block_converter)

  def block_converters_from_csv(self):
    """Prepare BlockConverters and order them like specified in
    self.CLASS_ORDER.
    """
    offsets, data_blocks = split_array(self.csv_data)
    for offset, data in zip(offsets, data_blocks):
      if len(data) < 2:
        continue  # empty block
      class_name = data[1][0].strip().lower()
      object_class = self.exportable.get(class_name)
      raw_headers, rows = extract_relevant_data(data)
      block_converter = BlockConverter(self, object_class=object_class,
                                       rows=rows, raw_headers=raw_headers,
                                       offset=offset, class_name=class_name)
      block_converter.check_block_restrictions()
      self.block_converters.append(block_converter)

    order = defaultdict(int)
    order.update({c: i for i, c in enumerate(self.CLASS_ORDER)})
    order["Person"] = -1
    self.block_converters.sort(key=lambda x: order[x.name])

  def import_objects(self):
    for converter in self.block_converters:
      converter.handle_row_data()
      converter.import_objects()

  def import_secondary_objects(self):
    for converter in self.block_converters:
      converter.import_secondary_objects(self.new_objects)

  def get_info(self):
    for converter in self.block_converters:
      self.response_data.append(converter.get_info())
    return self.response_data

  def get_object_names(self):
    return [c.object_class.__name__ for c in self.block_converters]

  @classmethod
  def drop_cache(cls):
    if not getattr(settings, 'MEMCACHE_MECHANISM', False):
      return
    memcache = MemCache()
    memcache.clean()
