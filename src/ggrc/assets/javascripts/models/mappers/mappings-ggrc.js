/*!
    Copyright (C) 2017 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

(function (GGRC, can) {
  var Proxy = GGRC.MapperHelpers.Proxy;
  var Direct = GGRC.MapperHelpers.Direct;
  var Indirect = GGRC.MapperHelpers.Indirect;
  var Search = GGRC.MapperHelpers.Search;
  var Multi = GGRC.MapperHelpers.Multi;
  var TypeFilter = GGRC.MapperHelpers.TypeFilter;
  var AttrFilter = GGRC.MapperHelpers.AttrFilter;
  var CustomFilter = GGRC.MapperHelpers.CustomFilter;
  var Cross = GGRC.MapperHelpers.Cross;

  new GGRC.Mappings('ggrc_core', {
    base: {},

    // Governance
    Control: {
      _mixins: [
        'related_object', 'personable', 'assignable'
      ],
      related_business_objects: Multi([
        'related_data_assets', 'related_facilities', 'related_markets',
        'related_org_groups', 'related_vendors', 'related_processes',
        'related_products', 'related_projects', 'related_systems'
      ]),
      related_and_able_objects: Multi([
        'objectives', 'related_business_objects',
        'people', 'programs', 'clauses'
      ]),
      audits: Proxy(
        'Audit', 'audit', 'AuditObject', 'auditable', 'audit_objects'),
      orphaned_objects: Multi([
        'related_objects', 'clauses', 'controls', 'programs', 'objectives',
        'people'
      ])
    },
    Objective: {
      _mixins: ['related_object', 'personable'],
      related_and_able_objects: Multi([
        'controls', 'objectives', 'related_objects', 'people',
        'sections', 'clauses'
      ]),
      orphaned_objects: Multi([
        'related_objects', 'clauses', 'contracts', 'controls', 'objectives',
        'people', 'policies', 'programs', 'regulations', 'sections', 'standards'
      ])
    },
    Section: {
      _mixins: ['related_object', 'personable']
    },
    Clause: {
      _mixins: ['related_object', 'personable']
    },
    personable: {
      _canonical: {
        people: 'Person'
      },
      people: Proxy(
        'Person', 'person', 'ObjectPerson', 'personable', 'object_people')
    },
    documentable: {
      _canonical: {
        documents: 'Document'
      },
      documents: TypeFilter('related_objects', 'Document')
    },
    assignable: {
      urls: TypeFilter('related_objects', 'Document'),
      info_related_objects: CustomFilter('related_objects',
        function (relatedObjects) {
          return !_.includes(['Comment', 'Document', 'Person'],
            relatedObjects.instance.type);
        }),
      comments: TypeFilter('related_objects', 'Comment'),
      documents_from_comments: Cross('comments', 'documents'),
      urls_from_comments: Cross('comments', 'urls'),
      all_documents: Multi(['documents', 'documents_from_comments']),
      all_urls: Multi(['urls', 'urls_from_comments'])
    },
    related_object: {
      _canonical: {
        related_objects_as_source: [
          'DataAsset', 'Facility', 'Market', 'OrgGroup', 'Vendor', 'Process',
          'Product', 'Project', 'System', 'Regulation', 'Policy', 'Contract',
          'Standard', 'Program', 'Issue', 'Control', 'Section', 'Clause',
          'Objective', 'Audit', 'Assessment', 'AssessmentTemplate',
          'AccessGroup', 'Document', 'Risk', 'Threat'
        ]
      },
      related_objects_as_source: Proxy(
        null, 'destination', 'Relationship', 'source', 'related_destinations'),
      related_objects_as_destination: Proxy(
        null, 'source', 'Relationship', 'destination', 'related_sources'),
      related_objects:
        Multi(['related_objects_as_source', 'related_objects_as_destination']),
      destinations: Direct('Relationship', 'source', 'related_destinations'),
      sources: Direct('Relationship', 'destination', 'related_sources'),
      relationships: Multi(['sources', 'destinations']),
      related_access_groups: TypeFilter('related_objects', 'AccessGroup'),
      related_data_assets: TypeFilter('related_objects', 'DataAsset'),
      related_facilities: TypeFilter('related_objects', 'Facility'),
      related_markets: TypeFilter('related_objects', 'Market'),
      related_org_groups: TypeFilter('related_objects', 'OrgGroup'),
      related_vendors: TypeFilter('related_objects', 'Vendor'),
      related_processes: TypeFilter('related_objects', 'Process'),
      related_products: TypeFilter('related_objects', 'Product'),
      related_projects: TypeFilter('related_objects', 'Project'),
      related_systems: TypeFilter('related_objects', 'System'),
      related_issues: TypeFilter('related_objects', 'Issue'),
      related_audits: TypeFilter('related_objects', 'Audit'),
      related_controls: TypeFilter('related_objects', 'Control'),
      related_assessments: TypeFilter('related_objects', 'Assessment'),
      related_risks: TypeFilter('related_objects', 'Risk'),
      related_threats: TypeFilter('related_objects', 'Threat'),
      regulations: TypeFilter('related_objects', 'Regulation'),
      contracts: TypeFilter('related_objects', 'Contract'),
      policies: TypeFilter('related_objects', 'Policy'),
      standards: TypeFilter('related_objects', 'Standard'),
      programs: TypeFilter('related_objects', 'Program'),
      controls: TypeFilter('related_objects', 'Control'),
      sections: TypeFilter('related_objects', 'Section'),
      clauses: TypeFilter('related_objects', 'Clause'),
      objectives: TypeFilter('related_objects', 'Objective'),
      risks: TypeFilter('related_objects', 'Risk'),
      threats: TypeFilter('related_objects', 'Threat')
    },
    // Program
    Program: {
      _mixins: [
        'related_object', 'personable'
      ],
      _canonical: {
        audits: 'Audit',
        context: 'Context'
      },
      related_issues: TypeFilter('related_objects', 'Issue'),
      audits: Direct('Audit', 'program', 'audits'),
      related_people_via_audits:
        TypeFilter('related_objects_via_audits', 'Person'),
      authorizations_via_audits: Cross('audits', 'authorizations'),
      context: Direct('Context', 'related_object', 'context'),
      contexts_via_audits: Cross('audits', 'context'),
      program_authorized_people: Cross('context', 'authorized_people'),
      program_authorizations: Cross('context', 'user_roles'),
      authorization_contexts: Multi(['context', 'contexts_via_audits']),
      authorizations_via_contexts:
        Cross('authorization_contexts', 'user_roles'),
      authorizations: Cross('authorization_contexts', 'user_roles'),
      authorized_people: Cross('authorization_contexts', 'authorized_people'),
      mapped_and_or_authorized_people: Multi([
        'people', 'authorized_people'
      ]),
      owner_authorizations: CustomFilter('program_authorizations',
        function (authBinding) {
          return new RefreshQueue()
            .enqueue(authBinding.instance.role.reify())
            .trigger()
            .then(function (roles) {
              return roles[0].name === 'ProgramOwner';
            });
        }),
      program_owners: Cross('owner_authorizations', 'person'),
      orphaned_objects: Multi([
        'related_objects', 'people'
      ])
    },
    directive_object: {
      _mixins: [
        'related_object', 'personable'
      ],
      orphaned_objects: Multi([
        'people', 'controls', 'objectives', 'related_objects'
      ])
    },

    // Directives
    Regulation: {
      _mixins: ['directive_object']
    },
    Contract: {
      _mixins: ['directive_object']
    },
    Standard: {
      _mixins: ['directive_object']
    },
    Policy: {
      _mixins: ['directive_object']
    },

    // Business objects
    business_object: {
      _mixins: [
        'related_object', 'personable'
      ],
      orphaned_objects: Multi([
        'related_objects', 'people', 'controls', 'objectives', 'sections',
        'clauses'
      ])
    },
    AccessGroup: {
      _mixins: ['business_object']
    },
    DataAsset: {
      _mixins: ['business_object']
    },
    Facility: {
      _mixins: ['business_object']
    },
    Market: {
      _mixins: ['business_object']
    },
    OrgGroup: {
      _mixins: ['business_object']
    },
    Vendor: {
      _mixins: ['business_object']
    },
    Product: {
      _mixins: ['business_object']
    },
    Project: {
      _mixins: ['business_object']
    },
    System: {
      _mixins: ['business_object']
    },
    Process: {
      _mixins: ['business_object']
    },
    Person: {
      _canonical: {
        related_objects: [
          'Program', 'Regulation', 'Contract', 'Policy', 'Standard',
          'AccessGroup', 'Objective', 'Control', 'Section', 'Clause',
          'DataAsset', 'Facility', 'Market', 'OrgGroup', 'Vendor', 'Process',
          'Product', 'Project', 'System', 'Issue', 'Risk', 'Threat'],
        authorizations: 'UserRole'
      },
      owned_programs: Indirect('Program', 'contact'),
      owned_regulations: Indirect('Regulation', 'contact'),
      owned_contracts: Indirect('Contract', 'contact'),
      owned_policies: Indirect('Policy', 'contact'),
      owned_standards: Indirect('Standard', 'contact'),
      owned_objectives: Indirect('Objective', 'contact'),
      owned_controls: Indirect('Control', 'contact'),
      owned_sections: Indirect('Section', 'contact'),
      owned_clauses: Indirect('Clause', 'contact'),
      owned_access_groups: Indirect('AccessGroup', 'contact'),
      owned_data_assets: Indirect('DataAsset', 'contact'),
      owned_facilities: Indirect('Facility', 'contact'),
      owned_markets: Indirect('Market', 'contact'),
      owned_org_groups: Indirect('OrgGroup', 'contact'),
      owned_vendors: Indirect('Vendor', 'contact'),
      owned_processes: Indirect('Process', 'contact'),
      owned_products: Indirect('Product', 'contact'),
      owned_projects: Indirect('Project', 'contact'),
      owned_systems: Indirect('System', 'contact'),
      owned_risks: Indirect('Risk', 'contact'),
      owned_threats: Indirect('Threat', 'contact'),
      related_objects: Proxy(
        null, 'personable', 'ObjectPerson', 'person', 'object_people'),
      related_programs: TypeFilter('related_objects', 'Program'),
      related_regulations: TypeFilter('related_objects', 'Regulation'),
      related_contracts: TypeFilter('related_objects', 'Contract'),
      related_policies: TypeFilter('related_objects', 'Policy'),
      related_standards: TypeFilter('related_objects', 'Standard'),
      related_objectives: TypeFilter('related_objects', 'Objective'),
      related_controls: TypeFilter('related_objects', 'Control'),
      related_sections: TypeFilter('related_objects', 'Section'),
      related_clauses: TypeFilter('related_objects', 'Clause'),
      related_access_groups: TypeFilter('related_objects', 'AccessGroup'),
      related_data_assets: TypeFilter('related_objects', 'DataAsset'),
      related_facilities: TypeFilter('related_objects', 'Facility'),
      related_markets: TypeFilter('related_objects', 'Market'),
      related_org_groups: TypeFilter('related_objects', 'OrgGroup'),
      related_vendors: TypeFilter('related_objects', 'Vendor'),
      related_processes: TypeFilter('related_objects', 'Process'),
      related_products: TypeFilter('related_objects', 'Product'),
      related_projects: TypeFilter('related_objects', 'Project'),
      related_systems: TypeFilter('related_objects', 'System'),
      related_issues: TypeFilter('related_objects', 'Issue'),
      related_risks: TypeFilter('related_objects', 'Risk'),
      related_threats: TypeFilter('related_objects', 'Threat'),
      authorizations: Direct('UserRole', 'person', 'user_roles'),
      programs_via_authorizations:
        Cross('authorizations', 'program_via_context'),
      extended_related_programs: Multi(['related_programs', 'owned_programs',
          'programs_via_authorizations']),
      extended_related_regulations:
        Multi(['related_regulations', 'owned_regulations']),
      extended_related_contracts:
        Multi(['related_contracts', 'owned_contracts']),
      extended_related_policies: Multi(['related_policies', 'owned_policies']),
      extended_related_objectives:
        Multi(['related_objectives', 'owned_objectives']),
      extended_related_controls: Multi(['related_controls', 'owned_controls']),
      extended_related_sections: Multi(['related_sections', 'owned_sections']),
      extended_related_clauses: Multi(['related_clauses', 'owned_clauses']),
      extended_related_data_assets:
        Multi(['related_data_assets', 'owned_data_assets']),
      extended_related_facilities:
        Multi(['related_facilities', 'owned_facilities']),
      extended_related_markets: Multi(['related_markets', 'owned_markets']),
      extended_related_org_groups:
        Multi(['related_org_groups', 'owned_org_groups']),
      extended_related_vendors: Multi(['related_vendors', 'owned_vendors']),
      extended_related_processes:
        Multi(['related_processes', 'owned_processes']),
      extended_related_products: Multi(['related_products', 'owned_products']),
      extended_related_projects: Multi(['related_projects', 'owned_projects']),
      extended_related_systems: Multi(['related_systems', 'owned_systems']),
      related_objects_via_search: Search(function (binding) {
        var types = this.observe_types;

        // checkfor window.location
        if (/^\/objectBrowser\/?$/.test(window.location.pathname)) {
          return GGRC.Models.Search.search_for_types('', types, {})
            .pipe(function (mappings) {
              return mappings.entries;
            });
        }
        return GGRC.Models.Search.search_for_types('', types, {
          contact_id: binding.instance.id
        }).pipe(function (mappings) {
          return mappings.entries;
        });
      }, 'Program,Regulation,Contract,Policy,Standard,Section,Clause,' +
        'Objective,Control,System,Process,DataAsset,AccessGroup,Product,' +
        'Project,Facility,Market,OrgGroup,Vendor,' +
        'Audit,Assessment,Issue,Risk,Threat'),
      extended_related_programs_via_search:
        TypeFilter('related_objects_via_search', 'Program'),
      extended_related_regulations_via_search:
        TypeFilter('related_objects_via_search', 'Regulation'),
      extended_related_contracts_via_search:
        TypeFilter('related_objects_via_search', 'Contract'),
      extended_related_policies_via_search:
        TypeFilter('related_objects_via_search', 'Policy'),
      extended_related_standards_via_search:
        TypeFilter('related_objects_via_search', 'Standard'),
      extended_related_objectives_via_search:
        TypeFilter('related_objects_via_search', 'Objective'),
      extended_related_controls_via_search:
        TypeFilter('related_objects_via_search', 'Control'),
      extended_related_sections_via_search:
        TypeFilter('related_objects_via_search', 'Section'),
      extended_related_clauses_via_search:
        TypeFilter('related_objects_via_search', 'Clause'),
      extended_related_access_groups_via_search:
        TypeFilter('related_objects_via_search', 'AccessGroup'),
      extended_related_data_assets_via_search:
        TypeFilter('related_objects_via_search', 'DataAsset'),
      extended_related_facilities_via_search:
        TypeFilter('related_objects_via_search', 'Facility'),
      extended_related_markets_via_search:
        TypeFilter('related_objects_via_search', 'Market'),
      extended_related_org_groups_via_search:
        TypeFilter('related_objects_via_search', 'OrgGroup'),
      extended_related_vendors_via_search:
        TypeFilter('related_objects_via_search', 'Vendor'),
      extended_related_processes_via_search:
        TypeFilter('related_objects_via_search', 'Process'),
      extended_related_products_via_search:
        TypeFilter('related_objects_via_search', 'Product'),
      extended_related_projects_via_search:
        TypeFilter('related_objects_via_search', 'Project'),
      extended_related_systems_via_search:
        TypeFilter('related_objects_via_search', 'System'),
      extended_related_audits_via_search:
        TypeFilter('related_objects_via_search', 'Audit'),
      extended_related_issues_via_search:
        TypeFilter('related_objects_via_search', 'Issue'),
      extended_related_assessment_via_search:
        TypeFilter('related_objects_via_search', 'Assessment'),
      extended_related_risks_via_search:
        TypeFilter('related_objects_via_search', 'Risk'),
      extended_related_threats_via_search:
        TypeFilter('related_objects_via_search', 'Threat')
    },
    Context: {
      _canonical: {
        user_roles: 'UserRole',
        authorized_people: 'Person'
      },
      user_roles: Direct('UserRole', 'context', 'user_roles'),
      authorized_people: Proxy('Person', 'person', 'UserRole', 'context',
        'user_roles')
    },
    UserRole: {
      // FIXME: These should not need to be `Indirect` --
      //   `context.related_object` *should* point to the right object.
      program_via_context: Indirect('Program', 'context'),
      audit_via_context: Indirect('Audit', 'context'),
      person: Direct('Person', 'user_roles', 'person'),
      role: Direct('Role', 'user_roles', 'role')
    },
    Audit: {
      _canonical: {
        _program: 'Program',
        context: 'Context'

      },
      _mixins: [
        'related_object'
      ],
      _program: Direct('Program', 'audits', 'program'),
      program_controls: Cross('_program', 'controls'),
      program_issues: Cross('_program', 'related_issues'),
      program_assessments: Cross('_program', 'related_assessments'),
      objects:
        Proxy(null, 'auditable', 'AuditObject', 'audit', 'audit_objects'),
      context: Direct('Context', 'related_object', 'context'),
      authorizations: Cross('context', 'user_roles'),
      authorized_program_people: Cross('_program', 'authorized_people'),
      authorized_audit_people: Cross('authorizations', 'person'),
      authorized_people:
        Multi(['authorized_audit_people', 'authorized_program_people']),
      auditor_authorizations: CustomFilter('authorizations', function (result) {
        return new RefreshQueue()
          .enqueue(result.instance.role.reify())
          .trigger()
          .then(function (roles) {
            return roles[0].name === 'Auditor';
          });
      }),
      auditors: Cross('auditor_authorizations', 'person'),
      related_assessment_templates: TypeFilter(
        'related_objects', 'AssessmentTemplate')
    },
    Assessment: {
      _mixins: [
        'related_object', 'personable', 'documentable', 'assignable'
      ],
      audits: TypeFilter('related_objects', 'Audit'),
      related_controls: TypeFilter('related_objects', 'Control'),
      related_regulations: TypeFilter('related_objects', 'Regulation'),
      related_creators:
        AttrFilter('related_objects', 'AssigneeType', 'Creator', 'Person'),
      related_assessors:
        AttrFilter('related_objects', 'AssigneeType', 'Assessor', 'Person'),
      related_verifiers:
        AttrFilter('related_objects', 'AssigneeType', 'Verifier', 'Person'),
      people: AttrFilter('related_objects', 'AssigneeType', null, 'Person')
    },
    AssessmentTemplate: {
      _mixins: ['related_object']
    },
    Issue: {
      _mixins: [
        'related_object', 'personable', 'documentable', 'assignable'
      ],
      audits: TypeFilter('related_objects', 'Audit')
    },
    Comment: {
      _mixins: ['related_object', 'documentable'],
      urls: TypeFilter('related_objects', 'Document'),
      documents_and_urls: Multi(['documents', 'urls'])
    },
    Meeting: {
      _mixins: ['personable']
    },
    MultitypeSearch: {
      _mixins: ['directive_object'],
      _canonical: {
        audits: 'Audit',
        workflows: 'Workflow'
      },
      audits: Proxy(
        'Audit', 'audit', 'MultitypeSearchJoin'),
      workflows: Proxy(
        'Workflow', 'workflow', 'MultitypeSearchJoin'),
      sections: Proxy(
        'Section', 'section', 'MultitypeSearchJoin')
    },
    AuditObject: {
      _auditable: Direct(null, null, 'auditable')
    },
    // Used by Custom Attributes widget
    CustomAttributable: {
      custom_attribute_definitions: Search(function (binding) {
        return CMS.Models.CustomAttributeDefinition.findAll({
          definition_type: binding.instance.root_object,
          definition_id: null
        });
      }, 'CustomAttributeDefinition')
    },
    // used by the Custom Roles admin panel tab
    Roleable: {
      access_control_roles: Search(function (binding) {
          return CMS.Models.AccessControlRole.findAll({
            object_type: binding.instance.model_singular
          });
      }, 'AccessControlRole')
    },
    Risk: {
      _mixins: ['directive_object']
    },
    Threat: {
      _mixins: ['directive_object']
    }
  });
})(window.GGRC, window.can);
