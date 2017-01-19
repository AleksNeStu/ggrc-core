# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""The module provides API for creating and manipulating GGRC's business
objects via REST."""
# pylint: disable=too-few-public-methods

import json

import re

from lib import environment
from lib.constants import url
from lib.entities.entities_factory import (
    ProgramFactory, AuditFactory, AsmtTmplFactory, AsmtFactory, ControlFactory,
    PersonFactory)
from lib.service.rest.client import RestClient


class BaseService(object):
  """Base class for business layer's services objects."""

  def __init__(self):
    self.client = RestClient(self.ENDPOINT)

  def create_objs(self, count, factory, **kwargs):
    """Create business objects used entities factories and REST API
    (responses from web-server parsed to list of attributes (list of dicts))
    Return list of objects.
    """
    objs = [factory.create() for _ in xrange(count)]
    list_of_attrs = [
        self.get_list_of_obj_attributes(self.client.create_object(
            type=obj.type, title=obj.title, **kwargs)) for
        obj in objs]
    return [self.set_obj_attrs(attrs, obj, **kwargs) for
            attrs, obj in zip(list_of_attrs, objs)]

  @staticmethod
  def get_list_of_obj_attributes(response):
    """Form the list of dicts with business object's attributes (dict's items)
    from server response.
    """

    def minimize(object_element):
      """Minimize response json data to request ready format."""
      obj = object_element[1].values()[0]
      return {"id": obj["id"], "href": obj["selfLink"], "type": obj["type"],
              "title": obj["title"],
              "url": environment.APP_URL + obj["viewLink"][1:],
              "name": re.search(r"\/([a-z_]*)\/", obj["viewLink"]).group(1)}

    return [minimize(object_element=x) for x in json.loads(response.text)][0]

  @staticmethod
  def set_obj_attrs(attrs, obj, **kwargs):
    """Update business object's attributes according type of object and
    list of dicts with business object's attributes (dict's items).
    """
    if attrs.get("id"):
      obj.id = attrs["id"]
    if attrs.get("href"):
      obj.href = attrs["href"]
    if kwargs:
      if kwargs.get("program") and kwargs.get("program").get("title"):
        obj.program = kwargs["program"]["title"]
      if kwargs.get("audit") and kwargs.get("audit").get("title"):
        obj.audit = kwargs["audit"]["title"]
      if kwargs.get("object") and kwargs.get("object").get("title"):
        obj.object = kwargs["object"]["title"]
    return obj


class ControlsService(BaseService):
  """Encapsulates logic for working with business entity Control."""
  ENDPOINT = url.CONTROLS

  def create(self, count):
    return self.create_objs(count=count, factory=ControlFactory())

  @staticmethod
  def update(objs):
    return [objs.__dict__]


class ProgramsService(BaseService):
  """Encapsulates logic for working with business entity Program."""
  ENDPOINT = url.PROGRAMS

  def create(self, count):
    return self.create_objs(count=count, factory=ProgramFactory())


class AuditsService(BaseService):
  """Encapsulates logic for working with business entity Audit."""
  ENDPOINT = url.AUDITS

  def create(self, count, program):
    return self.create_objs(count=count, factory=AuditFactory(),
                            program=program.__dict__)


class AsmtTmplsService(BaseService):
  """Encapsulates logic for working with business entity
  Assessment Template.
  """
  ENDPOINT = url.ASSESSMENT_TEMPLATES

  def create(self, count, audit):
    return self.create_objs(count=count, factory=AsmtTmplFactory(),
                            audit=audit.__dict__)


class AssessmentsService(BaseService):
  """Encapsulates logic for working with business entity Assessment."""
  ENDPOINT = url.ASSESSMENTS

  def create(self, count, obj, audit):
    return self.create_objs(count=count, factory=AsmtFactory(),
                            object=obj.__dict__, audit=audit.__dict__)


class RelationshipsService(BaseService):
  """Encapsulates logic for working with business entity Relationship."""
  ENDPOINT = url.RELATIONSHIPS

  def create(self, src_obj, dest_objs):
    if isinstance(dest_objs, list):
      return [self.client.create_object("relationship",
                                        source=src_obj.__dict__,
                                        destination=dest_obj.__dict__) for
              dest_obj in dest_objs]
    else:
      return self.client.create_object("relationship", source=src_obj.__dict__,
                                       destination=dest_objs.__dict__)


class ObjectsOwnersService(BaseService):
  """Encapsulates logic for working with business entity Object Owners."""
  ENDPOINT = url.OBJECT_OWNERS

  def create(self, objs, owner=PersonFactory().default()):
    if isinstance(objs, list):
      return [self.client.create_object("object_owner", ownable=obj.__dict__,
                                        person=owner.__dict__) for
              obj in objs]
    else:
      return self.client.create_object("object_owner", ownable=objs.__dict__,
                                       person=owner.__dict__)
