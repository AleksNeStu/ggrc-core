# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Create and manipulate objects via REST API."""
# pylint: disable=too-few-public-methods

import json
import re

from requests import exceptions

from lib import environment
from lib.constants import url, objects
from lib.entities.entities_factory import (
  ProgramsFactory, AuditsFactory, AssessmentTemplatesFactory,
  AssessmentsFactory, ControlsFactory, IssuesFactory, PersonsFactory)
from lib.service.rest.client import RestClient


class BaseService(object):
  """Base class for business layer's services objects."""
  def __init__(self):
    self.client = RestClient(self.ENDPOINT)
    self._relationship = objects.get_singular(url.RELATIONSHIPS)
    self._object_owner = objects.get_singular(url.OBJECT_OWNERS)
    self._count = objects.COUNT

  def create_list_objs(self, factory, count, **kwargs):
    """Create list of objects used entity factory and REST API data
    (raw responses after REST API objects creation converted to list of dicts
    {"attr": "value", ...}). Return list of created objects.
    """
    list_factory_objs = [factory.create() for _ in xrange(count)]
    list_attrs = [
        self.get_obj_attrs(self.client.create_object(
            type=factory_obj.type, title=factory_obj.title,
            slug=factory_obj.code, **kwargs)) for
        factory_obj in list_factory_objs]
    return [self.set_obj_attrs(attrs, factory_obj, **kwargs) for
            attrs, factory_obj in zip(list_attrs, list_factory_objs)]

  @staticmethod
  def get_obj_attrs(response):
    """Form dictionary of object's attributes (dict's items)
    from server response.
    """
    def get_items_from_obj_el(obj_el):
      """Get values from dict object element (obj_el) and create new dict of
      items.
      """
      return {"id": obj_el.get("id"), "href": obj_el.get("selfLink"),
              "type": obj_el.get("type"), "title": obj_el.get("title"),
              "code": obj_el.get("slug"),
              "url": environment.APP_URL + obj_el.get("viewLink")[1:],
              "name": re.search(r"\/([a-z_]*)\/",
                                obj_el.get("viewLink")).group(1),
              "last_update": obj_el.get("updated_at")}
    resp = json.loads(response.text)
    if response.status_code == 200:
      # check that resp looks like [[resp_code, resp_message]] where resp_code
      # is int, resp_message is dict and remap resp to resp_message
      if (isinstance(resp, list) and len(resp[0]) == 2 and
              isinstance(resp[0][1], dict)):
        resp = resp[0][1]
      return get_items_from_obj_el(resp.itervalues().next())
    else:
      resp_code, resp_message = resp[0]
      print "Response_code: {code}, Response_message: {message}".format(
          code=resp_code, message=resp_message)
      raise exceptions.ContentDecodingError

  @staticmethod
  def set_obj_attrs(attrs, obj, **kwargs): # flake8: noqa
    """Update object's attributes according type of object and
    list of dicts with object's attributes (dict's items).
    """
    if (attrs.get("type") and
            attrs["type"] == objects.get_singular(objects.AUDITS).title()):
      obj.type = attrs["type"]
    if attrs.get("id"):
      obj.id = attrs["id"]
    if attrs.get("href"):
      obj.href = attrs["href"]
    if attrs.get("url"):
      obj.url = attrs["url"]
    if attrs.get("last_update"):
      obj.last_update = attrs["last_update"]
    if attrs.get("code") == obj.code:
      obj.code = attrs["code"]
    if attrs.get("title") == obj.title:
      obj.title = attrs["title"]
    if kwargs:
      # for Audit objects
      if kwargs.get("program") and kwargs.get("program").get("title"):
        obj.program = kwargs["program"]["title"]
      # for Assessment Template objects
      if kwargs.get("audit") and kwargs.get("audit").get("title"):
        obj.audit = kwargs["audit"]["title"]
      # for Assessment objects
      if kwargs.get("object") and kwargs.get("object").get("title"):
        obj.object = kwargs["object"]["title"]
    return obj

  def update_list_objs(self, list_old_objs, factory):
    """Update objects used old objects (list_old_objs) as target,
    entities factories as new attributes data generator,
    REST API as service for provide that.
    Return list of updated objects.
    """
    list_new_objs = [factory.create() for _ in xrange(len(list_old_objs))]
    list_new_attrs = [
        self.get_obj_attrs(self.client.update_object(
            href=old_obj.href, url=old_obj.url, title=new_obj.title,
            slug=new_obj.code)) for
        old_obj, new_obj in zip(list_old_objs, list_new_objs)]
    return [self.set_obj_attrs(new_attrs, new_obj) for
            new_attrs, new_obj in zip(list_new_attrs, list_new_objs)]


class ControlsService(BaseService):
  """Service for working with Controls entities."""
  ENDPOINT = url.CONTROLS

  def create(self, count):
    """Create new Controls objects via REST API and return created."""
    return self.create_list_objs(factory=ControlsFactory(), count=count)

  def update(self, objs):
    """Update an existing Controls objects via REST API and return updated."""
    return self.update_list_objs(
        list_old_objs=[objs], factory=ControlsFactory())


class ProgramsService(BaseService):
  """Service for working with Programs entities."""
  ENDPOINT = url.PROGRAMS

  def create(self, count):
    """Create new Programs objects via REST API and return created."""
    return self.create_list_objs(factory=ProgramsFactory(), count=count)


class AuditsService(BaseService):
  """Service for working with Audits entities."""
  ENDPOINT = url.AUDITS

  def create(self, count, program):
    """Create and return new Audits objects via REST API and return created.
    """
    return self.create_list_objs(factory=AuditsFactory(), count=count,
                                 program=program.__dict__)


class AssessmentTemplatesService(BaseService):
  """Service for working with Assessment Templates entities."""
  ENDPOINT = url.ASSESSMENT_TEMPLATES

  def create(self, count, audit):
    """Create new Assessment Templates objects via REST API and return
    created.
    """
    return self.create_list_objs(factory=AssessmentTemplatesFactory(),
                                 count=count, audit=audit.__dict__)


class AssessmentsService(BaseService):
  """Service for working with Assessments entities."""
  ENDPOINT = url.ASSESSMENTS

  def create(self, count, audit):
    """Create new Assessments objects via REST API and return created."""
    return self.create_list_objs(factory=AssessmentsFactory(),
                                 count=count, audit=audit.__dict__)


class IssuesService(BaseService):
  """Service for working with Issues entities."""
  ENDPOINT = url.ISSUES

  def create(self, count, audit):
    """Create new Issues objects via REST API and return created."""
    return self.create_list_objs(factory=IssuesFactory(), count=count,
                                 audit=audit.__dict__)


class RelationshipsService(BaseService):
  """Service for creating relationships between entities."""
  ENDPOINT = url.RELATIONSHIPS

  def create(self, src_obj, dest_objs):
    """Create relationship from source to destination objects and
    return created.
    """
    if isinstance(dest_objs, list):
      return [
          self.client.create_object(
              type=self._relationship, source=src_obj.__dict__,
              destination=dest_obj.__dict__) for dest_obj in dest_objs]
    else:
      return self.client.create_object(
          type=self._relationship, source=src_obj.__dict__,
          destination=dest_objs.__dict__)


class ObjectsOwnersService(BaseService):
  """Service for assigning owners to entities."""
  ENDPOINT = url.OBJECT_OWNERS

  def create(self, objs, owner=PersonsFactory().default()):
    """Assign of an owner to objects."""
    if isinstance(objs, list):
      return [
          self.client.create_object(
              type=self._object_owner, ownable=obj.__dict__,
              person=owner.__dict__) for obj in objs]
    else:
      return self.client.create_object(
          type=self._object_owner, ownable=objs.__dict__,
          person=owner.__dict__)


class ObjectsInfoService(BaseService):
  """Service for getting information about entities."""
  ENDPOINT = url.QUERY

  def get_total_count(self, obj_name):
    """Get and return total count of existing objects in system
    according to type of object.
    """
    resp = self.client.create_object(type=self._count, object_name=obj_name)
    dict_resp = json.loads(resp.text)[0]
    return dict_resp.get(obj_name).get("total")
