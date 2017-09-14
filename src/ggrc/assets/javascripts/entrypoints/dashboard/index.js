/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

import '../../permission';
import '../../bootstrap/sticky-popover';
import '../../bootstrap/modal-form';
import '../../plugins/lodash_helpers';
import '../../plugins/persistent_notifier';
import '../../ggrc_base';
import '../../apps/base_widgets';
import '../../application';
import '../../plugins/utils';
import '../../plugins/datepicker';
import '../../plugins/can_control';
import '../../plugins/autocomplete';
import '../../plugins/ajax_extensions';
import '../../plugins/canjs_extensions';
import '../../plugins/component_registry';
import '../../plugins/openclose';
import '../../plugins/tooltip';
import '../../plugins/popover';
import '../../plugins/popover_template';
import '../../mustache_helper';
import '../../generated/ggrc_filter_query_parser';

// Models
import '../../models';

// ViewModels
import '../../components/view-models/advanced-search-container-vm';
import '../../components/view-models/tree-item-base-vm';
import '../../components/view-models/tree-people-base-vm';
import '../../components/base-objects/pagination';

// Controllers
import '../../controllers/tree/tree-loader';
import '../../controllers/tree/tree-view';
import '../../controllers/tree/tree-view-node';
import '../../controllers/tree/list_view_controller';
import '../../controllers/dashboard_widgets_controller';
import '../../controllers/info_widget_controller';
import '../../controllers/summary_widget_controller';
import '../../controllers/dashboard_widget_controller';
import '../../controllers/modals';
import '../../controllers/info_pin_controller';
import '../../controllers/automapper_controller';
import '../../controllers/dashboard_controller';
import '../../controllers/mapper';

// Modules and Apps
import '../../modules/widget_list';
import '../../pbc/workflow_controller';
import '../../apps/quick_search';
import '../../apps/business_objects';
import '../../apps/custom_attributes_wrap';

// Components
import '../../components/state-colors-map/state-colors-map';
import '../../components/spinner/spinner';
import '../../components/collapsible-panel/collapsible-panel';
import '../../components/read-more/read-more';
import '../../components/assessment/custom-attributes';
import '../../components/assessment/inline';
import '../../components/assessment/info-pane/confirm-edit-action';
import '../../components/comment/comment-add-form';
import '../../components/comment/comment-input';
import '../../components/comment/comment-add-button';
import '../../components/object-list-item/business-object-list-item';
import '../../components/object-list-item/person-list-item';
import '../../components/object-list-item/comment-list-item';
import '../../components/object-list-item/document-object-list-item';
import '../../components/object-list-item/detailed-business-object-list-item';
import '../../components/object-list-item/editable-document-object-list-item';
import '../../components/object-list-item/object-list-item-updater';
import '../../components/object-popover/related-assessment-popover';
import '../../components/object-popover/object-popover';
import '../../components/mapped-objects/directly-mapped-objects';
import '../../components/mapped-objects/mapped-objects';
import '../../components/related-objects/related-audits';
import '../../components/related-objects/related-assessment-item';
import '../../components/related-objects/related-assessment-list';
import '../../components/related-objects/related-comments';
import '../../components/related-objects/related-controls-objectives';
import '../../components/related-objects/related-issues';
import '../../components/object-state-toolbar/object-state-toolbar';
import '../../components/object-list/object-list';
import '../../components/ca-object/ca-object';
import '../../components/form/form-validation-icon';
import '../../components/ca-object/ca-object-value-mapper';
import '../../components/ca-object/ca-object-modal-content';
import '../../components/related-objects/related-objects';
import '../../components/reusable-objects/reusable-objects-list';
import '../../components/reusable-objects/reusable-objects-item';
import '../../components/simple-modal/simple-modal';
import '../../components/simple-popover/simple-popover';
import '../../components/show-more/show-more';
import '../../components/show-related-assessments-button/show-related-assessments-button';
import '../../components/mapping-controls/mapping-type-selector';
import '../../components/dropdown/dropdown';
import '../../components/dropdown/multiselect-dropdown';
import '../../components/autocomplete/autocomplete';
import '../../components/datepicker/datepicker';
import '../../components/person/person';
import '../../components/inline_edit/inline';
import '../../components/unarchive_link';
import '../../components/link_to_clipboard';
import '../../components/relevant_filters';
import '../../components/people_list';
import '../../components/mapped_tree_view';
import '../../components/reusable_objects';
import '../../components/assessment_generator';
import '../../components/paginate';
import '../../components/tabs/tab-container';
import '../../components/tabs/tab-panel';
import '../../components/assessment_attributes';
import '../../components/lazy_open_close';
import '../../components/revision-log/revision-log';
import '../../components/quick_form/quick_add';
import '../../components/quick_form/quick_update';
import '../../components/access_control_list/access_control_list';
import '../../components/modal_wrappers/assessment_template_form';
import '../../components/modal_wrappers/checkboxes_to_list';
import '../../components/reminder';
import '../../components/rich_text/rich_text';
import '../../components/object_cloner/object_cloner';
import '../../components/sort_by_sort_index/sort_by_sort_index';
import '../../components/tree_pagination/tree_pagination';
import '../../components/tree/tree-widget-container';
import '../../components/effective-dates/effective-dates';
import '../../components/snapshotter/revisions-comparer';
import '../../components/snapshotter/scope-update';
import '../../components/textarea-array/textarea-array';
import '../../components/page-header/page-header';
import '../../components/action-toolbar/action-toolbar';
import '../../components/action-toolbar-control/action-toolbar-control';
import '../../components/unmap-button/unmap-button';
import '../../components/related-objects/related-documents';
import '../../components/related-objects/related-evidences-and-urls';
import '../../components/related-objects/related-reference-urls';
import '../../components/assessment/assessment-people';
import '../../components/assessment/attach-button';
import '../../components/assessment/assessment-object-type-dropdown';
import '../../components/assessment/map-button-using-assessment-type';
import '../../components/assessment/info-pane-save-status';
import '../../components/inline/inline';
import '../../components/csv/export';
import '../../components/csv/import';
import '../../components/people/editable-people-group-header';
import '../../components/people/people-list-info';
import '../../components/prev-next-buttons/prev-next-buttons';
import '../../components/loading/loading-status';
import '../../components/lazy-render/lazy-render';

import '../../components/custom-attributes/custom-attributes-field-view';
import '../../components/form/form-validation-text';

import '../../components/form/fields/checkbox-form-field';
import '../../components/form/fields/date-form-field';
import '../../components/form/fields/dropdown-form-field';
import '../../components/form/fields/person-form-field';
import '../../components/form/fields/rich-text-form-field';
import '../../components/form/fields/text-form-field';
import '../../components/global-custom-attributes/global-custom-attributes';
import '../../components/issue/issue-unmap-item';
import '../../components/issue/issue-unmap-dropdown-item';
import '../../components/issue/issue-unmap';

// This modal should be loaded here as it requires some components
import '../../bootstrap/modal-ajax';

import '../../dashboard';

import '../../../stylesheets/dashboard.scss';
