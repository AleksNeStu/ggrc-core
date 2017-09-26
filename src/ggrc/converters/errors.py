# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""List of all error and warning messages for imports."""


WRONG_FILE_TYPE = (u"Line {line}: Wrong file type. Only .csv files are"
                   u" supported. Please upload a .csv file.")

MISSING_COLUMN = (u"Line {line}: Missing mandatory column{s} {column_names},"
                  u" when adding object.")

MISSING_CUSTOM_ATTRIBUTE_COLUMN = (u"Line {line}: Missing custom column"
                                   " {column_name}, when adding object.")

WRONG_OBJECT_TYPE = u"Line {line}: Unknown object type '{object_name}'"

UNKNOWN_COLUMN = (u"Line {line}: Attribute '{column_name}' does not"
                  u" exist. Column will be ignored.")

DELETE_UNKNOWN_OBJECT = (u"Line {line}: Object '{slug}' does not exist, so it"
                         u" can't be deleted.")

DUPLICATE_COLUMN = (u"Line {line}: Duplicate columns found {duplicates}."
                    u" Object block will be ignored.")

DUPLICATE_VALUE = (u"Line {line}: {column_name} '{value}' already exists."
                   u"Record will be ignored.")

DUPLICATE_IN_MULTI_VALUE = (
    u"Line {line}: {column_name} contains duplicate values. Only a single "
    u"value from each group of identical values will be used. "
    u"Duplicates: {duplicates}"
)

DUPLICATE_VALUE_IN_CSV = (u"Lines {line_list} have same {column_name}"
                          u" '{value}'. Line{s} {ignore_lines} will be"
                          u" ignored.")

MAP_UNMAP_CONFLICT = (u"Line {line}: Object '{slug}' scheduled for mapping and"
                      u" unmapping at the same time. Mapping rule update will"
                      u" be ignored.")

UNKNOWN_OBJECT = (u"Line {line}: {object_type} '{slug}' doesn't exist, so it"
                  u" can't be mapped/unmapped.")

UNKNOWN_USER_WARNING = (u"Line {line}: Specified user '{email}' does not "
                        u"exist. That user will be ignored.")

OWNER_MISSING = (u"Line {line}: {column_name} field does not contain a valid "
                 u"value. You will be assigned as object {column_name}.")

WRONG_MULTI_VALUE = (u"Line {line}: {column_name} contains invalid line. The"
                     u" value '{value}' will be ignored.")

WRONG_VALUE = (u"Line {line}: Field '{column_name}' contains invalid data. The"
               u" value will be ignored.")

WRONG_VALUE_DEFAULT = (u"Line {line}: Field '{column_name}' contains invalid"
                       u" data. The default value will be used.")

WRONG_VALUE_ERROR = (u"Line {line}: Field '{column_name}' contains invalid "
                     u"data. The line will be ignored.")

WRONG_REQUIRED_VALUE = (u"Line {line}: Required field {column_name} contains"
                        u" invalid data '{value}'. The default value will be"
                        u" used.")

MISSING_VALUE_WARNING = (u"Line {line}: Field '{column_name}' is required. "
                         u"The default value '{default_value}' will be used.")

MISSING_VALUE_ERROR = (u"Line {line}: Field '{column_name}' is required. The "
                       u"line will be ignored.")

PERMISSION_ERROR = (u"Line {line}: You don't have permission to update/delete"
                    u" this record.")

MAPPING_PERMISSION_ERROR = (u"Line {line}: You don't have permission to update"
                            " mappings for {object_type}: {slug}.")

DELETE_NEW_OBJECT_ERROR = (u"Line {line}: Tried to create and delete the same"
                           " object {object_type}: {slug} in one import.")

DELETE_CASCADE_ERROR = (u"Line {line}: Cannot delete object {object_type}:"
                        " {slug} without deleting other objects")

UNKNOWN_ERROR = u"Line {line}: Import failed due to unknown error."

INVALID_START_END_DATES = (u"Line {line}: {start_date} can not be after "
                           u"{end_date}. The line will be ignored.")

UNKNOWN_DATE_FORMAT = (u"Line {line}: Field {column_name} contains invalid "
                       u"date format, use YYYY-MM-DD or MM/DD/YYYY. The line "
                       u"will be ignored.")

WRONG_DATE_FORMAT = (u"Line {line}: Field {column_name} contains invalid "
                     u"date format. Expected MM/DD, but found MM/DD/YYYY, "
                     u"the YYYY part of the date will be ignored.")

UNSUPPORTED_LIST_ERROR = (u"Line {line}: Field {column_name} does not support "
                          u"{value_type}.")

UNSUPPORTED_OPERATION_ERROR = (u"Line {line}: {operation} is not supported. "
                               u"The line will be ignored.")

INVALID_ATTRIBUTE_WARNING = (u"Line {line}: Object does not contain attribute "
                             u"'{column_name}'. The value will be ignored.")

CREATE_INSTANCE_ERROR = (u"Line {line}: New instance creation is denied. "
                         u"The line will be ignored.")

INVALID_STATUS_DATE_CORRELATION = (u"Line {line}: Cannot change {date} for "
                                   u"task which status is {status}. "
                                   u"The line will be ignored.")

ONLY_IMPORTABLE_COLUMNS_WARNING = (u"Line {line}: Only the following "
                                   u"attributes are importable: {columns}. "
                                   u"All other columns will be ignored.")

EXPORT_ONLY_WARNING = (u"Line {line}: Field '{column_name}' "
                       u"can not be imported. The value will be ignored.")

ILLEGAL_APPEND_CONTROL_VALUE = ("Line {line}: "
                                "You can not map {mapped_type} to "
                                "{object_type}, because this {mapped_type} is "
                                "not mapped to the related audit.")

UNMODIFIABLE_COLUMN = (u"Line {line}: Column '{column_name}' can not be "
                       u"modified. The value will be ignored.")

ARCHIVED_IMPORT_ERROR = (u"Line {line}: Importing archived instance is "
                         u"prohibited. The line will be ignored.")

VALIDATION_ERROR = (u"Line {line}: Field '{column_name}' validation failed "
                    u"with the following reason: {message}."
                    u"The line will be ignored.")

SINGLE_AUDIT_RESTRICTION = (u"Line {line}: You can not map {mapped_type} to "
                            u"{object_type}, because this {object_type} is "
                            u"already mapped to an {mapped_type}")
