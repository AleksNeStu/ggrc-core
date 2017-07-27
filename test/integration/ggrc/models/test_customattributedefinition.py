
# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Integration tests for Assessment"""

import ddt

from integration import ggrc


@ddt.ddt
class TestCAD(ggrc.TestCase):
  """CAD test cases"""

  @ddt.data(
      ("A,B,C",
       None,
       {"A": {"comment_required": False, "evidence_required": False},
        "B": {"comment_required": False, "evidence_required": False},
        "C": {"comment_required": False, "evidence_required": False}}),
      ("", None, {}),
      ("A,B,C,D",
       "1,2,3,0",
       {"A": {"comment_required": True, "evidence_required": False},
        "B": {"comment_required": False, "evidence_required": True},
        "C": {"comment_required": True, "evidence_required": True},
        "D": {"comment_required": False, "evidence_required": False}}),
      ("A,B,C",
       "1,0",
       {"A": {"comment_required": True, "evidence_required": False},
        "B": {"comment_required": False, "evidence_required": False}}),
      ("A,B",
       "1,0,1,1,1",
       {"A": {"comment_required": True, "evidence_required": False},
        "B": {"comment_required": False, "evidence_required": False}}),
  )
  @ddt.unpack
  def test_cad_options(self, options, checks, expected):
    self.assertDictEqual(
        expected,
        ggrc.models.factories.CustomAttributeDefinitionFactory(
            definition_type="control",
            attribute_type="Dropdown",
            title="Test Title",
            multi_choice_options=options,
            multi_choice_mandatory=checks
        ).options
    )
