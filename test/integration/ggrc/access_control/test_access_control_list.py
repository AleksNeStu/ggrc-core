# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Test Access Control List"""

from ggrc.fulltext import mysql
from ggrc.models import all_models
from integration.ggrc import TestCase
from integration.ggrc.models import factories
from integration.ggrc.models.factories import random_str
from integration.ggrc.api_helper import Api


def _acl_json(role_id, person_id):
  """Helper function for setting acl json"""
  return {
      "ac_role_id": role_id,
      "person": {
          "type": "Person",
          "id": person_id
      }
  }


def _acl_asserts(acl, id_, person_id):
  """Run asserts on a given acl list"""
  assert len(acl) == 1, \
      "Access control list did not get saved {}".format(acl)

  assert acl[0]["id"] > 0, \
      "Acces control list did not set an id"

  assert acl[0]["ac_role_id"] == id_, \
      "Access control list does not include the saved role id"

  assert acl[0]["person_id"] == person_id, \
      "Access control list does not include person id {}".format(acl[0])


class TestAccessControlList(TestCase):
  """TestAccessControlList"""

  def setUp(self):
    super(TestAccessControlList, self).setUp()
    self.api = Api()
    self.person = factories.PersonFactory(name="My Person")
    self.control = factories.ControlFactory()
    self.acr = factories.AccessControlRoleFactory(
        object_type="Control",
        read=True
    )
    self.second_acr = factories.AccessControlRoleFactory(
        object_type="Control",
        read=True
    )
    self.acl = factories.AccessControlListFactory(
        object=self.control,
        ac_role_id=self.acr.id,
        person=self.person
    )

  def _post_control(self, id_, person_id, collection=False):
    """Helper function for posting a control"""
    title = random_str(prefix="Control - ")
    control = {
        "control": {
            "title": title,
            "type": "Control",
            "context": None,
            "access_control_list": [
                _acl_json(id_, person_id)
            ]
        },
    }
    response = self.api.post(
        all_models.Control, [control] if collection else control)
    assert response.status_code == 200 or response.status_code == 201, \
        "Control with acl not created successfully {}".format(response.status)

    if collection:
      return response.json[0][1]
    return response.json

  def test_object_roles(self):
    """Test if roles are fetched with the object"""
    id_, person_id = self.acr.id, self.person.id
    response = self.api.get(all_models.Control, self.control.id)
    assert response.status_code == 200, \
        "Failed to fetch created control {}".format(response.status)

    assert "access_control_list" in response.json["control"], \
        "Access Control List not a property in {}".format(
            response.json["control"].keys())

    ac_list = response.json["control"]["access_control_list"]
    assert len(ac_list) == 1, "{}".format(len(ac_list))

    assert ac_list[0]["ac_role_id"] == id_, \
        "ac_role_id not properly set {}".format(ac_list[0].get("ac_role_id"))
    assert ac_list[0]["person"]["id"] == person_id, \
        "Person stub not properly set {}".format(ac_list[0]["person"])

  def test_post_object_roles(self):
    """Test if roles are stored correctly when POSTed with the object"""
    id_, person_id = self.acr.id, self.person.id
    response = self._post_control(id_, person_id)

    acl = response["control"]["access_control_list"]
    _acl_asserts(acl, id_, person_id)

  def test_acl_revision_content(self):
    """Test if the access control list is added to revisions"""
    id_, person_id = self.acr.id, self.person.id
    response = self._post_control(id_, person_id)
    control_id = response["control"]["id"]
    rev = all_models.Revision.query.filter(
        all_models.Revision.resource_id == control_id,
        all_models.Revision.resource_type == "Control"
    ).first()

    acl = rev.content["access_control_list"]
    _acl_asserts(acl, id_, person_id)

  def test_put_object_roles(self):
    """Test if PUTing object roles saves them correctly"""
    id_2, person_id = self.second_acr.id, self.person.id

    response = self.api.get(all_models.Control, self.control.id)
    assert response.status_code == 200, \
        "Failed to fetch created control {}".format(response.status)
    control = response.json['control']
    control['access_control_list'].append(_acl_json(id_2, person_id))
    response = self.api.put(self.control, {"control": control})
    assert response.status_code == 200, \
        "PUTing control failed {}".format(response.status)
    acl = response.json['control']['access_control_list']
    assert len(acl) == 2, \
        "Access control list not correctly updated {}".format(acl)

  def test_put_removing_roles(self):
    """Test if PUTing an empty list removes object roles correct"""
    response = self.api.get(all_models.Control, self.control.id)
    assert response.status_code == 200, \
        "Failed to fetch created control {}".format(response.status)
    control = response.json['control']
    control['access_control_list'] = []
    response = self.api.put(self.control, {"control": control})
    assert response.status_code == 200, \
        "PUTing control failed {}".format(response.status)
    acl = response.json['control']['access_control_list']
    assert len(acl) == 0, \
        "Access control list not empty {}".format(acl)

  def test_acl_indexing_on_post(self):
    """Test if roles are stored correctly when POSTed with the object"""
    id_, person_id = self.acr.id, self.person.id
    response = self._post_control(id_, person_id, True)
    control = response["control"]
    res = mysql.MysqlRecordProperty.query.filter(
        mysql.MysqlRecordProperty.type == "Control",
        mysql.MysqlRecordProperty.key == control["id"],
        mysql.MysqlRecordProperty.property == self.acr.name
    ).all()
    assert len(res) > 0, \
        "Full text record index not created for {}".format(self.acr.name)
    assert len([r for r in res if r.content == self.person.email]) == 1, \
        "Person email not indexed {}".format(self.person.email)
    assert len([r for r in res if r.content == self.person.name]) == 1, \
        "Person name not indexed {}".format(self.person.name)

  def test_acl_revision_count(self):
    """Test if acl revision is created when object POSTed and PUTed"""
    id_, person_id = self.acr.id, self.person.id

    response = self._post_control(id_, person_id)
    # One ACL and Control created in setUp and on by POST
    self.assertEqual(
        all_models.Revision.query.filter_by(
            resource_type="AccessControlList"
        ).count(),
        2
    )
    self.assertEqual(
        all_models.Revision.query.filter_by(
            resource_type="Control"
        ).count(),
        2
    )

    # If content of "access_control_list" is changed,
    # new revision should be created for ACL
    control = response["control"]
    control["access_control_list"] = []
    self.api.put(
        all_models.Control.query.get(control["id"]),
        {"control": control}
    )
    self.assertEqual(
        all_models.Revision.query.filter_by(
            resource_type="AccessControlList"
        ).count(),
        3
    )
    self.assertEqual(
        all_models.Revision.query.filter_by(
            resource_type="Control"
        ).count(),
        3
    )
