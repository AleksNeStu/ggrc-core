# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Utils for manipulation with directories and files."""

import csv
import logging
import os
import shutil
import time
from collections import defaultdict

from lib import constants


LOGGER = logging.getLogger(__name__)


def wait_file_downloaded(
    path_to_csv,
    timeout=constants.ux.MAX_USER_WAIT_SECONDS,
    poll_frequency=constants.ux.POLL_FREQUENCY
):
  """Wait until file is exist or IOError is raised."""
  end_time = time.time() + timeout
  while not os.path.exists(path_to_csv):
    time.sleep(poll_frequency)
    if time.time() > end_time:
      raise IOError(
          "No such file {} or directory after waiting for {} sec.".format(
              path_to_csv, timeout))
  file_size = os.path.getsize(path_to_csv)
  while True:
    current_file_size = os.path.getsize(path_to_csv)
    if current_file_size == file_size and file_size != 0:
      break
    file_size = current_file_size
    time.sleep(poll_frequency)
    if time.time() > end_time:
      raise IOError(
          "File {} not changed size from {} bytes during {} sec of "
          "waiting.".format(path_to_csv, current_file_size, timeout))


def get_list_objs_scopes_from_csv(path_to_csv):
  """Open according to 'path_to_csv' CSV file witch is expected to contain
  exported objects, parse through CSV file's structure and return list of
  objects scopes (dicts with keys as exportable field names, values as values
  of this field for current instance).
  """
  wait_file_downloaded(path_to_csv)
  with open(path_to_csv) as csv_file:
    rows = csv.reader(csv_file)
    object_type = None
    keys = []
    results = defaultdict(list)
    for columns in rows:
      if not any(columns):
        continue
      if columns[0] == "Object type":
        # new block started
        object_type = None
        keys = []
        continue
      if object_type is None:
        keys = columns[1:]
        object_type = columns[0]
        continue
      columns = [unicode(val) for val in columns]
      results[object_type].append(dict(zip(keys, columns[1:])))
    return results


def create_directory(path):
  """Create directory if it doesn't already exist. Check if path is a file_path
  or a dir_path. Dir path is a string that ends with os.sep.
  """
  if path[-1] != os.sep:
    path, _ = os.path.split(path)
  if not os.path.exists(path):
    LOGGER.info("Creating directory: %s", path)
    os.makedirs(path)


def get_unique_postfix(file_path, extension):
  """Add numeric postfix for file."""
  postfix = 0
  new_path = file_path + str(postfix) + extension
  while os.path.isfile(new_path):
    postfix += 1
    new_path = file_path + str(postfix) + extension
  return new_path


def delete_directory_contents(path):
  """Remove all files and sub-dir in provided path."""
  shutil.rmtree(path)
