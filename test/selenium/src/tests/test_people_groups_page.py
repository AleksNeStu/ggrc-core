# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""People/Groups page smoke tests."""
# pylint: disable=no-self-use
# pylint: disable=invalid-name

import pytest  # pylint: disable=import-error

from lib import base
from lib.constants import url


class TestOrgGroupPage(base.Test):
  """Tests org group page, part of smoke tests, section 7."""
  # pylint: disable=too-few-public-methods

  @pytest.mark.smoke_tests
  def test_app_redirects_to_new_org_group_page(self, new_org_group_ui):
    """Tests if after saving and closing lhn_modal app redirects to
    the object page.
    Generally we start at random url. Here we verify that after saving
    and closing lhn_modal we're redirected to an url that contains an
    object id.
    """
    # pylint: disable=unused-argument
    expected_url = (
      url.All.ORG_GROUPS + "/" + new_org_group_ui.source_obj_id_from_url)
    actual_url = new_org_group_ui.url
    assert expected_url in actual_url
