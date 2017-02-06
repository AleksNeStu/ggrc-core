# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>


from collections import namedtuple

CacheEntry = namedtuple('CacheEntry', 'model_plural class_name cache_type')
MappingEntry = namedtuple('MappingEntry', 'class_name attr polymorph')


def resource(model_plural, class_name, cache_type='memcache'):
  return CacheEntry(model_plural, class_name, cache_type)


def mapping(class_name, attr, polymorph=False):
  return MappingEntry(class_name, attr, polymorph)


def all_cache_entries():
  ret = [
      resource('access_groups', 'AccessGroup'),
      resource('audits', 'Audit'),
      resource('custom_attribute_values', 'CustomAttributeValue'),
      resource('categorizations', 'Categorization'),
      resource('category_bases', 'CategoryBase'),
      resource('comments', 'Comment'),
      resource('control_categories', 'ControlCategory'),
      resource('control_assertions', 'ControlAssertion'),
      resource('contexts', 'Context'),
      resource('controls', 'Control'),
      resource('assessments', 'Assessments'),
      resource('assessment_templates', 'AssessmentTemplate'),
      resource('data_assets', 'DataAsset'),
      resource('directives', 'Directive'),
      resource('contracts', 'Contract'),
      resource('policies', 'Policy'),
      resource('regulations', 'Regulation'),
      resource('standards', 'Standard'),
      resource('documents', 'Document'),
      resource('events', 'Event'),
      resource('facilities', 'Facility'),
      resource('helps', 'Help'),
      resource('markets', 'Market'),
      resource('meetings', 'Meeting'),
      resource('object_documents', 'ObjectDocument'),
      resource('object_owners', 'ObjectOwner'),
      resource('object_people', 'ObjectPerson'),
      resource('objectives', 'Objective'),
      resource('options', 'Option'),
      resource('org_groups', 'OrgGroup'),
      resource('vendors', 'Vendor'),
      resource('people', 'Person'),
      resource('products', 'Product'),
      resource('projects', 'Project'),
      resource('programs', 'Program'),
      resource('relationships', 'Relationship'),
      resource('revisions', 'Revision'),
      resource('sections', 'Section'),
      resource('clauses', 'Clause'),
      resource('systems_or_processes', 'SystemOrProcess'),
      resource('systems', 'System'),
      resource('processes', 'Process'),
      resource('issues', 'Issue'),
      resource('snapshots', 'Snapshot'),

      # ggrc notification models
      resource('notification_configs', 'NotificationConfig'),
      resource('notifications', 'Notification'),
      resource('notification_type', 'NotificationType'),

      # ggrc custom attribuess
      resource('custom_attribute_definitions', 'CustomAttributeDefinition'),
      resource('custom_attribute_values', 'CustomAttributeValue'),

      # FIXME: Extension-defined models should be registered
      #        from the extensions.

      # ggrc_basic_permissions models
      resource('roles', 'Role'),
      resource('user_roles', 'UserRole'),

      # ggrc_gdrive_integration models
      resource('object_folders', 'ObjectFolder'),
      resource('object_files', 'ObjectFile'),
      resource('object_events', 'ObjectEvent'),

      # ggrc_risk_assessments models
      resource('templates', 'Template'),
      resource('risk_assessments', 'RiskAssessment'),
      resource('risk_assessment_mappings', 'RiskAssessmentMapping'),
      resource('risk_assessment_control_mappings',
               'RiskAssessmentControlMapping'),
      resource('threats', 'Threat'),
      resource('vulnerabilities', 'Vulnerability'),

      # ggrc_workflows models
      resource('cycle_task_entries', 'CycleTaskEntry'),
      resource('cycle_task_group_object_tasks', 'CycleTaskGroupObjectTask'),
      resource('cycle_task_groups', 'CycleTaskGroup'),
      resource('cycles', 'Cycle'),
      resource('task_group_objects', 'TaskGroupObject'),
      resource('task_group_tasks', 'TaskGroupTask'),
      resource('task_groups', 'TaskGroup'),
      resource('workflow_people', 'WorkflowPerson'),
      resource('workflows', 'Workflow'),
  ]

  return ret


def all_mapping_entries():
  ret = [
      mapping('Audit', 'program'),
      mapping('CustomAttributeValue', 'attributable', True),
      mapping('ObjectDocument', 'document'),
      mapping('ObjectDocument', 'documentable', True),
      mapping('ObjectOwner', 'person'),
      mapping('ObjectOwner', 'ownable', True),
      mapping('ObjectPerson', 'person'),
      mapping('ObjectPerson', 'personable', True),
      mapping('Section', 'directive'),  # this goes out?
      mapping('Relationship', 'source', True),
      mapping('Relationship', 'destination', True),
      mapping('UserRole', 'context'),
      mapping('UserRole', 'person'),
      mapping('UserRole', 'role'),
      mapping('ObjectEvent', 'eventable', True),
      mapping('ObjectFolder', 'folderable', True),
      mapping('ObjectFile', 'fileable', True),
      mapping('Notification', 'recipients'),
      mapping('Notification', 'notification_object'),
      # ggrc_workflows mappings:
      mapping('TaskGroupObject', 'object', True),
      mapping('TaskGroupObject', 'task_group'),
      mapping('TaskGroupTask', 'task_group'),
      mapping('TaskGroup', 'workflow'),
      mapping('WorkflowPerson', 'context'),
      mapping('WorkflowPerson', 'person'),
      mapping('WorkflowPerson', 'workflow'),
      mapping('Cycle', 'workflow'),
      mapping('Cycle', 'cycle_task_groups'),
      mapping('CycleTaskGroup', 'cycle'),
      mapping('CycleTaskGroup', 'task_group'),
      mapping('CycleTaskGroupObjectTask', 'cycle'),
      mapping('CycleTaskGroupObjectTask', 'cycle_task_entries'),
      mapping('CycleTaskGroupObjectTask', 'task_group_task'),
      mapping('CycleTaskGroupObjectTask', 'cycle_task_objects_for_cache'),
      mapping('CycleTaskEntry', 'cycle'),
      mapping('CycleTaskEntry', 'cycle_task_group_object_task'),
      # mapping('RiskAssessmentMapping'),
      # mapping('RiskAssessmentControlMapping'),
  ]

  return ret


class Cache:
  name = None
  supported_resources = {}

  def __init__(self):
    pass

  def get_name(self):
    return None

  def get(self, *_):
    return None

  def add(self, *_):
    return None

  def update(self, *_):
    return None

  def remove(self, *_):
    return None

  def get_multi(self, *_):
    return None

  def add_multi(self, *_):
    return None

  def update_multi(self, *_):
    return None

  def remove_multi(self, *_):
    return None

  def clean(self):
    return False

  def get_key(self, category, resource):
    cache_key = category + ":" + resource
    return cache_key

  def parse_filter(self, filter):
    return filter.get('ids'), filter.get('attrs')

  def is_caching_supported(self, category, resource):
    if category is 'collection':
      return resource in self.supported_resources
    else:
      return False
