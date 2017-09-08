# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Add 6 types GCAs for all entities via REST API."""

import pytest

from lib import base
from lib.constants import objects


class TestAddGCAS(base.Test):

  @pytest.yield_fixture(scope="function")
  def dynamic_new_gcas_for_entities(self, request):
    import conftest
    yield conftest._common_fixtures(request.param) if request.param else None

  @pytest.mark.smoke_tests
  @pytest.mark.parametrize(
    "dynamic_new_gcas_for_entities",
    ["new_cas_for_{obj}_rest".format(obj=obj) for obj in objects.ALL_CA_OBJS],
    indirect=["dynamic_new_gcas_for_entities"])
  def test_add_6gcas_for_all_entities(self, dynamic_new_gcas_for_entities):
    for gcas in dynamic_new_gcas_for_entities:
      print gcas
      print "\n"
