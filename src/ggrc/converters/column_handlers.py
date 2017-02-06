# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""List of all column handlers for objects in the ggrc module."""

from ggrc.converters.handlers import assessment_template
from ggrc.converters.handlers import boolean
from ggrc.converters.handlers import default_people
from ggrc.converters.handlers import handlers
from ggrc.converters.handlers import list_handlers
from ggrc.converters.handlers import related_person
from ggrc.converters.handlers import template
from ggrc.converters.handlers import document
from ggrc.extensions import get_extension_modules

GGRC_COLUMN_HANDLERS = {
    "assertions": handlers.ControlAssertionColumnHandler,
    "assessment_template": assessment_template.AssessmentTemplateColumnHandler,
    "assignee": handlers.UserColumnHandler,
    "audit": handlers.AuditColumnHandler,
    "categories": handlers.ControlCategoryColumnHandler,
    "company": handlers.TextColumnHandler,
    "contact": handlers.UserColumnHandler,
    "default_assessors": default_people.DefaultPersonColumnHandler,
    "default_verifier": default_people.DefaultPersonColumnHandler,
    "delete": handlers.DeleteColumnHandler,
    "description": handlers.TextareaColumnHandler,
    "design": handlers.ConclusionColumnHandler,
    "document_evidence": document.DocumentEvidenceHandler,
    "document_url": document.DocumentUrlHandler,
    "documents": handlers.DocumentsColumnHandler,
    "due_on": handlers.DateColumnHandler,
    "email": handlers.EmailColumnHandler,
    "end_date": handlers.DateColumnHandler,
    "fraud_related": boolean.CheckboxColumnHandler,
    "is_enabled": boolean.CheckboxColumnHandler,
    "key_control": boolean.KeyControlColumnHandler,
    "directive_kind": handlers.DirectiveKindColumnHandler,
    "kind": handlers.OptionColumnHandler,
    "link": handlers.TextColumnHandler,
    "means": handlers.OptionColumnHandler,
    "name": handlers.TextColumnHandler,
    "network_zone": handlers.OptionColumnHandler,
    "notes": handlers.TextareaColumnHandler,
    "operationally": handlers.ConclusionColumnHandler,
    "owners": handlers.OwnerColumnHandler,
    "principal_assessor": handlers.UserColumnHandler,
    "program": handlers.ProgramColumnHandler,
    "recipients": list_handlers.ValueListHandler,
    "reference_url": handlers.TextColumnHandler,
    "related_assessors": related_person.RelatedAssessorsColumnHandler,
    "related_assignees": related_person.RelatedAssigneesColumnHandler,
    "related_creators": related_person.RelatedCreatorsColumnHandler,
    "related_verifiers": related_person.RelatedVerifiersColumnHandler,
    "report_end_date": handlers.DateColumnHandler,
    "report_start_date": handlers.DateColumnHandler,
    "secondary_assessor": handlers.UserColumnHandler,
    "secondary_contact": handlers.UserColumnHandler,
    "send_by_default": boolean.CheckboxColumnHandler,
    "slug": handlers.SlugColumnHandler,
    "start_date": handlers.DateColumnHandler,
    "status": handlers.StatusColumnHandler,
    "os_state": handlers.ExportOnlyColumnHandler,
    "template_custom_attributes": template.TemplateCaColumnHandler,
    "template_object_type": template.TemplateObjectColumnHandler,
    "test_plan": handlers.TextareaColumnHandler,
    "test_plan_procedure": boolean.CheckboxColumnHandler,
    "title": handlers.RequiredTextColumnHandler,
    "url": handlers.TextColumnHandler,
    "verify_frequency": handlers.OptionColumnHandler,

    # Mapping column handlers
    "__mapping__:person": handlers.PersonMappingColumnHandler,
    "__unmapping__:person": handlers.PersonUnmappingColumnHandler,
    "control": handlers.ControlColumnHandler,
    "directive": handlers.SectionDirectiveColumnHandler,
}


def get_all_column_handlers():
  """Search through all enabled modules for their contributed column handlers.

  Returns:
    extension_handlers (dict): dict of all extension handlers
  """
  extension_handlers = GGRC_COLUMN_HANDLERS
  for extension_module in get_extension_modules():
    contributed_handlers = getattr(
        extension_module, "contributed_column_handlers", None)
    if callable(contributed_handlers):
      extension_handlers.update(contributed_handlers())
    elif isinstance(contributed_handlers, dict):
      extension_handlers.update(contributed_handlers)
  return extension_handlers


COLUMN_HANDLERS = get_all_column_handlers()
