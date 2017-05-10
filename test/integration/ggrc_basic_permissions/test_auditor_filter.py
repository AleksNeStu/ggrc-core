# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Test audit RBAC"""
# pylint: disable=unused-import
from ggrc.app import app  # NOQA

from ggrc.models import all_models

from integration.ggrc import TestCase
from integration.ggrc.api_helper import Api
from integration.ggrc.generator import ObjectGenerator

from integration.ggrc.models import factories
from integration.ggrc_basic_permissions.models \
    import factories as rbac_factories

from appengine import base


@base.with_memcache
class TestFilterByAuditor(TestCase):
  """ Test for filter by Auditor. """

  def setUp(self):
    super(TestFilterByAuditor, self).setUp()
    self.api = Api()
    self.generator = ObjectGenerator()
    _, self.auditor = self.generator.generate_person(user_role="Creator")
    auditor_role = all_models.Role.query.filter_by(name="Auditor").first()
    with factories.single_commit():
      self.audit = factories.AuditFactory(status="In Progress")
      self.audit_id = self.audit.id
      audit_context = factories.ContextFactory()
      self.audit.context = audit_context
      rbac_factories.UserRoleFactory(
          context=audit_context,
          role=auditor_role,
          person=self.auditor)
    self.api.set_user(self.auditor)

  def test_query_audits_by_auditor(self):
    """test get audit as query get"""
    objects = self.api.get_query(all_models.Audit, "")
    self.assertEqual(1, len(objects.json["audits_collection"]["audits"]))
    audit_dict = objects.json["audits_collection"]["audits"][0]
    self.assertEqual(self.audit_id, audit_dict["id"])

  def test_filter_audits_by_auditor(self):
    """Test query on audit Global Search.

    This query is the fact query that frontend is sending in global search.
    """
    query_request_data = [
        {
            u'fields': [],
            u'filters': {
                u'expression': {
                    u'left': {
                        u'left': u'status',
                        u'op': {u'name': u'='},
                        u'right': u'Planned'
                    },
                    u'op': {u'name': u'OR'},
                    u'right': {
                        u'left': {
                            u'left': u'status',
                            u'op': {u'name': u'='},
                            u'right': u'In Progress'
                        },
                        u'op': {u'name': u'OR'},
                        u'right': {
                            u'left': {
                                u'left': u'status',
                                u'op': {u'name': u'='},
                                u'right': u'Manager Review'
                            },
                            u'op': {u'name': u'OR'},
                            u'right': {
                                u'left': {
                                    u'left': u'status',
                                    u'op': {u'name': u'='},
                                    u'right': u'Ready for External Review',
                                },
                                u'op': {u'name': u'OR'},
                                u'right': {
                                    u'left': u'status',
                                    u'op': {u'name': u'='},
                                    u'right': u'Completed',
                                }
                            },
                        },
                    },
                },
                u'keys': [u'status'],
                u'order_by': {
                    u'compare': None,
                    u'keys': [],
                    u'order': u'',
                }
            },
            u'limit': [0, 5],
            u'object_name': u'Audit',
            u'permissions': u'read',
            u'type': u'values',
        },
        {
            u'filters': {
                u'expression': {
                    u'ids': [u'150'],
                    u'object_name': u'undefined',
                    u'op': {u'name': u'relevant'}
                },
                u'keys': [],
                u'order_by': {u'compare': None, u'keys': [], u'order': u''}
            },
            u'object_name': u'Audit',
            u'type': u'ids',
        },
    ]
    resp = self.api.send_request(self.api.client.post,
                                 data=query_request_data,
                                 api_link="/query")
    self.assertEqual(1, resp.json[0]["Audit"]["count"])
    self.assertEqual(self.audit_id, resp.json[0]["Audit"]["values"][0]["id"])
