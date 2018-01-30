# -*- coding: utf-8 -*-
# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Constants to fill of create modals."""
from lib.constants import roles

SHORT_TITLE = u"""Un texte en français and additionally đšžćč!#./?€ħ&^~'"""

LONG_DESCRIPTION = u"""Governance, Risk Management, and Compliance (GRC)
    are three pillars that work together for purpose of
    assuring that an organization meets its objectives. ...
    Governance is combination of processes established '
    and executed by board of directors that are '
    reflected in organization's structure and how it '
    ismanaged and led toward achieving goals. Risk '
    management is predicting and managing risks that could '
    hinder organization to achieve its objectives. '
    Compliance with company's policies and procedures, '
    laws and regulations, strong and efficient governance is '
    considered key to an organization's success." [4] GRC '
    is discipline that aims to synchronize information and '
    activity across governance, risk management and compliance '
    in order to operate more efficiently, enable effective '
    information sharing, more effectively report activities '
    and avoid wasteful overlaps. Although interpreted '
    differently in various organizations, GRC typically '
    encompasses activities such as corporate governance, '
    enterprise risk management (ERM) and corporate '
    compliance with applicable laws and regulations. '
    Organizations reach size where coordinated control '
    over GRC activities is required to operate effectively. '
    Each of these three disciplines creates information of '
    value to other two, and all three impact same
    technologies, people, processes and information.
    Substantial duplication of tasks evolves when
    governance, risk management and compliance are managed
    independently. Overlapping and duplicated GRC activities
    negatively impact both operational costs and GRC metrics.
    For example, each internal service might be audited and
    assessed by multiple groups on an annual basis, creating
    enormous cost and disconnected results. A disconnected
    GRC approach will also prevent an organization from
    providing real-time GRC executive reports. Like badly
    planned transport system, every individual route will
    operate, but network will lack qualities that
    allow them to work together effectively. If not
    integrated, if tackled in traditional "silo" approach,
    most organizations must sustain unmanageable numbers of
    GRC-related requirements due to changes in technology,
    increasing data storage, market globalization and
    increased regulation. Un texte en français"""


class Programs(object):
  """Constants to fill of Program create modals."""
  PROGRAM_URL = "www.program_url.com"
  REFERENCE_URL = "www.reference_url.com"
  EFFECTIVE_DATE = "12/01/2014"
  DEFAULT_MANAGER = roles.DefaultSuperuser.EMAIL
