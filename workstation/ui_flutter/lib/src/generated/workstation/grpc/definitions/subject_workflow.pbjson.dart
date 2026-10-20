//
//  Generated code. Do not modify.
//  source: workstation/grpc/definitions/subject_workflow.proto
//
// @dart = 2.12

// ignore_for_file: annotate_overrides, camel_case_types, comment_references
// ignore_for_file: constant_identifier_names, library_prefixes
// ignore_for_file: non_constant_identifier_names, prefer_final_fields
// ignore_for_file: unnecessary_import, unnecessary_this, unused_import

import 'dart:convert' as $convert;
import 'dart:core' as $core;
import 'dart:typed_data' as $typed_data;

@$core.Deprecated('Use subjectScenarioSummaryDescriptor instead')
const SubjectScenarioSummary$json = {
  '1': 'SubjectScenarioSummary',
  '2': [
    {'1': 'key', '3': 1, '4': 1, '5': 9, '10': 'key'},
    {'1': 'subject_id', '3': 2, '4': 1, '5': 9, '10': 'subjectId'},
    {'1': 'title', '3': 3, '4': 1, '5': 9, '10': 'title'},
    {'1': 'family_title', '3': 4, '4': 1, '5': 9, '10': 'familyTitle'},
    {'1': 'context_id', '3': 5, '4': 1, '5': 9, '10': 'contextId'},
    {'1': 'summary', '3': 6, '4': 1, '5': 9, '10': 'summary'},
    {'1': 'governance_status', '3': 7, '4': 1, '5': 9, '10': 'governanceStatus'},
    {'1': 'context_snapshot_hash', '3': 8, '4': 1, '5': 9, '10': 'contextSnapshotHash'},
    {'1': 'unit_count', '3': 9, '4': 1, '5': 5, '10': 'unitCount'},
    {'1': 'admitted_unit_count', '3': 10, '4': 1, '5': 5, '10': 'admittedUnitCount'},
    {'1': 'source_count', '3': 11, '4': 1, '5': 5, '10': 'sourceCount'},
    {'1': 'delta_count', '3': 12, '4': 1, '5': 5, '10': 'deltaCount'},
    {'1': 'applied_delta_count', '3': 13, '4': 1, '5': 5, '10': 'appliedDeltaCount'},
    {'1': 'import_count', '3': 14, '4': 1, '5': 5, '10': 'importCount'},
    {'1': 'pending_import_count', '3': 15, '4': 1, '5': 5, '10': 'pendingImportCount'},
    {'1': 'reasoning_import_count', '3': 16, '4': 1, '5': 5, '10': 'reasoningImportCount'},
    {'1': 'imported_subject_count', '3': 17, '4': 1, '5': 5, '10': 'importedSubjectCount'},
    {'1': 'context_path', '3': 18, '4': 1, '5': 9, '10': 'contextPath'},
    {'1': 'subject_markdown_path', '3': 19, '4': 1, '5': 9, '10': 'subjectMarkdownPath'},
    {'1': 'subject_typst_path', '3': 20, '4': 1, '5': 9, '10': 'subjectTypstPath'},
    {'1': 'publication_id', '3': 21, '4': 1, '5': 9, '10': 'publicationId'},
    {'1': 'publication_title', '3': 22, '4': 1, '5': 9, '10': 'publicationTitle'},
    {'1': 'build_id', '3': 23, '4': 1, '5': 9, '10': 'buildId'},
    {'1': 'build_status', '3': 24, '4': 1, '5': 9, '10': 'buildStatus'},
    {'1': 'validation_status', '3': 25, '4': 1, '5': 9, '10': 'validationStatus'},
    {'1': 'build_path', '3': 26, '4': 1, '5': 9, '10': 'buildPath'},
    {'1': 'publication_section_count', '3': 27, '4': 1, '5': 5, '10': 'publicationSectionCount'},
    {'1': 'publication_claim_count', '3': 28, '4': 1, '5': 5, '10': 'publicationClaimCount'},
    {'1': 'publication_source_count', '3': 29, '4': 1, '5': 5, '10': 'publicationSourceCount'},
    {'1': 'publication_entity_count', '3': 30, '4': 1, '5': 5, '10': 'publicationEntityCount'},
    {'1': 'publication_xref_count', '3': 31, '4': 1, '5': 5, '10': 'publicationXrefCount'},
    {'1': 'publication_review_count', '3': 32, '4': 1, '5': 5, '10': 'publicationReviewCount'},
    {'1': 'report_markdown_path', '3': 33, '4': 1, '5': 9, '10': 'reportMarkdownPath'},
    {'1': 'report_typst_path', '3': 34, '4': 1, '5': 9, '10': 'reportTypstPath'},
    {'1': 'report_pdf_path', '3': 35, '4': 1, '5': 9, '10': 'reportPdfPath'},
    {'1': 'composition_id', '3': 36, '4': 1, '5': 9, '10': 'compositionId'},
    {'1': 'composition_status', '3': 37, '4': 1, '5': 9, '10': 'compositionStatus'},
    {'1': 'composition_title', '3': 38, '4': 1, '5': 9, '10': 'compositionTitle'},
    {'1': 'composition_scope_summary', '3': 39, '4': 1, '5': 9, '10': 'compositionScopeSummary'},
    {'1': 'composition_learning_context_snapshot_hash', '3': 40, '4': 1, '5': 9, '10': 'compositionLearningContextSnapshotHash'},
    {'1': 'composition_included_unit_count', '3': 41, '4': 1, '5': 5, '10': 'compositionIncludedUnitCount'},
    {'1': 'composition_selected_import_count', '3': 42, '4': 1, '5': 5, '10': 'compositionSelectedImportCount'},
    {'1': 'composition_section_count', '3': 43, '4': 1, '5': 5, '10': 'compositionSectionCount'},
    {'1': 'source_collection_count', '3': 44, '4': 1, '5': 5, '10': 'sourceCollectionCount'},
    {'1': 'staged_source_count', '3': 45, '4': 1, '5': 5, '10': 'stagedSourceCount'},
    {'1': 'source_collection_preview_lines', '3': 46, '4': 3, '5': 9, '10': 'sourceCollectionPreviewLines'},
    {'1': 'source_preview_lines', '3': 47, '4': 3, '5': 9, '10': 'sourcePreviewLines'},
    {'1': 'staged_source_preview_lines', '3': 48, '4': 3, '5': 9, '10': 'stagedSourcePreviewLines'},
    {'1': 'unit_preview_lines', '3': 49, '4': 3, '5': 9, '10': 'unitPreviewLines'},
    {'1': 'delta_preview_lines', '3': 50, '4': 3, '5': 9, '10': 'deltaPreviewLines'},
    {'1': 'pending_import_preview_lines', '3': 51, '4': 3, '5': 9, '10': 'pendingImportPreviewLines'},
    {'1': 'import_preview_lines', '3': 52, '4': 3, '5': 9, '10': 'importPreviewLines'},
    {'1': 'is_placeholder', '3': 53, '4': 1, '5': 8, '10': 'isPlaceholder'},
  ],
};

/// Descriptor for `SubjectScenarioSummary`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List subjectScenarioSummaryDescriptor = $convert.base64Decode(
    'ChZTdWJqZWN0U2NlbmFyaW9TdW1tYXJ5EhAKA2tleRgBIAEoCVIDa2V5Eh0KCnN1YmplY3RfaW'
    'QYAiABKAlSCXN1YmplY3RJZBIUCgV0aXRsZRgDIAEoCVIFdGl0bGUSIQoMZmFtaWx5X3RpdGxl'
    'GAQgASgJUgtmYW1pbHlUaXRsZRIdCgpjb250ZXh0X2lkGAUgASgJUgljb250ZXh0SWQSGAoHc3'
    'VtbWFyeRgGIAEoCVIHc3VtbWFyeRIrChFnb3Zlcm5hbmNlX3N0YXR1cxgHIAEoCVIQZ292ZXJu'
    'YW5jZVN0YXR1cxIyChVjb250ZXh0X3NuYXBzaG90X2hhc2gYCCABKAlSE2NvbnRleHRTbmFwc2'
    'hvdEhhc2gSHQoKdW5pdF9jb3VudBgJIAEoBVIJdW5pdENvdW50Ei4KE2FkbWl0dGVkX3VuaXRf'
    'Y291bnQYCiABKAVSEWFkbWl0dGVkVW5pdENvdW50EiEKDHNvdXJjZV9jb3VudBgLIAEoBVILc2'
    '91cmNlQ291bnQSHwoLZGVsdGFfY291bnQYDCABKAVSCmRlbHRhQ291bnQSLgoTYXBwbGllZF9k'
    'ZWx0YV9jb3VudBgNIAEoBVIRYXBwbGllZERlbHRhQ291bnQSIQoMaW1wb3J0X2NvdW50GA4gAS'
    'gFUgtpbXBvcnRDb3VudBIwChRwZW5kaW5nX2ltcG9ydF9jb3VudBgPIAEoBVIScGVuZGluZ0lt'
    'cG9ydENvdW50EjQKFnJlYXNvbmluZ19pbXBvcnRfY291bnQYECABKAVSFHJlYXNvbmluZ0ltcG'
    '9ydENvdW50EjQKFmltcG9ydGVkX3N1YmplY3RfY291bnQYESABKAVSFGltcG9ydGVkU3ViamVj'
    'dENvdW50EiEKDGNvbnRleHRfcGF0aBgSIAEoCVILY29udGV4dFBhdGgSMgoVc3ViamVjdF9tYX'
    'JrZG93bl9wYXRoGBMgASgJUhNzdWJqZWN0TWFya2Rvd25QYXRoEiwKEnN1YmplY3RfdHlwc3Rf'
    'cGF0aBgUIAEoCVIQc3ViamVjdFR5cHN0UGF0aBIlCg5wdWJsaWNhdGlvbl9pZBgVIAEoCVINcH'
    'VibGljYXRpb25JZBIrChFwdWJsaWNhdGlvbl90aXRsZRgWIAEoCVIQcHVibGljYXRpb25UaXRs'
    'ZRIZCghidWlsZF9pZBgXIAEoCVIHYnVpbGRJZBIhCgxidWlsZF9zdGF0dXMYGCABKAlSC2J1aW'
    'xkU3RhdHVzEisKEXZhbGlkYXRpb25fc3RhdHVzGBkgASgJUhB2YWxpZGF0aW9uU3RhdHVzEh0K'
    'CmJ1aWxkX3BhdGgYGiABKAlSCWJ1aWxkUGF0aBI6ChlwdWJsaWNhdGlvbl9zZWN0aW9uX2NvdW'
    '50GBsgASgFUhdwdWJsaWNhdGlvblNlY3Rpb25Db3VudBI2ChdwdWJsaWNhdGlvbl9jbGFpbV9j'
    'b3VudBgcIAEoBVIVcHVibGljYXRpb25DbGFpbUNvdW50EjgKGHB1YmxpY2F0aW9uX3NvdXJjZV'
    '9jb3VudBgdIAEoBVIWcHVibGljYXRpb25Tb3VyY2VDb3VudBI4ChhwdWJsaWNhdGlvbl9lbnRp'
    'dHlfY291bnQYHiABKAVSFnB1YmxpY2F0aW9uRW50aXR5Q291bnQSNAoWcHVibGljYXRpb25feH'
    'JlZl9jb3VudBgfIAEoBVIUcHVibGljYXRpb25YcmVmQ291bnQSOAoYcHVibGljYXRpb25fcmV2'
    'aWV3X2NvdW50GCAgASgFUhZwdWJsaWNhdGlvblJldmlld0NvdW50EjAKFHJlcG9ydF9tYXJrZG'
    '93bl9wYXRoGCEgASgJUhJyZXBvcnRNYXJrZG93blBhdGgSKgoRcmVwb3J0X3R5cHN0X3BhdGgY'
    'IiABKAlSD3JlcG9ydFR5cHN0UGF0aBImCg9yZXBvcnRfcGRmX3BhdGgYIyABKAlSDXJlcG9ydF'
    'BkZlBhdGgSJQoOY29tcG9zaXRpb25faWQYJCABKAlSDWNvbXBvc2l0aW9uSWQSLQoSY29tcG9z'
    'aXRpb25fc3RhdHVzGCUgASgJUhFjb21wb3NpdGlvblN0YXR1cxIrChFjb21wb3NpdGlvbl90aX'
    'RsZRgmIAEoCVIQY29tcG9zaXRpb25UaXRsZRI6Chljb21wb3NpdGlvbl9zY29wZV9zdW1tYXJ5'
    'GCcgASgJUhdjb21wb3NpdGlvblNjb3BlU3VtbWFyeRJaCipjb21wb3NpdGlvbl9sZWFybmluZ1'
    '9jb250ZXh0X3NuYXBzaG90X2hhc2gYKCABKAlSJmNvbXBvc2l0aW9uTGVhcm5pbmdDb250ZXh0'
    'U25hcHNob3RIYXNoEkUKH2NvbXBvc2l0aW9uX2luY2x1ZGVkX3VuaXRfY291bnQYKSABKAVSHG'
    'NvbXBvc2l0aW9uSW5jbHVkZWRVbml0Q291bnQSSQohY29tcG9zaXRpb25fc2VsZWN0ZWRfaW1w'
    'b3J0X2NvdW50GCogASgFUh5jb21wb3NpdGlvblNlbGVjdGVkSW1wb3J0Q291bnQSOgoZY29tcG'
    '9zaXRpb25fc2VjdGlvbl9jb3VudBgrIAEoBVIXY29tcG9zaXRpb25TZWN0aW9uQ291bnQSNgoX'
    'c291cmNlX2NvbGxlY3Rpb25fY291bnQYLCABKAVSFXNvdXJjZUNvbGxlY3Rpb25Db3VudBIuCh'
    'NzdGFnZWRfc291cmNlX2NvdW50GC0gASgFUhFzdGFnZWRTb3VyY2VDb3VudBJFCh9zb3VyY2Vf'
    'Y29sbGVjdGlvbl9wcmV2aWV3X2xpbmVzGC4gAygJUhxzb3VyY2VDb2xsZWN0aW9uUHJldmlld0'
    'xpbmVzEjAKFHNvdXJjZV9wcmV2aWV3X2xpbmVzGC8gAygJUhJzb3VyY2VQcmV2aWV3TGluZXMS'
    'PQobc3RhZ2VkX3NvdXJjZV9wcmV2aWV3X2xpbmVzGDAgAygJUhhzdGFnZWRTb3VyY2VQcmV2aW'
    'V3TGluZXMSLAoSdW5pdF9wcmV2aWV3X2xpbmVzGDEgAygJUhB1bml0UHJldmlld0xpbmVzEi4K'
    'E2RlbHRhX3ByZXZpZXdfbGluZXMYMiADKAlSEWRlbHRhUHJldmlld0xpbmVzEj8KHHBlbmRpbm'
    'dfaW1wb3J0X3ByZXZpZXdfbGluZXMYMyADKAlSGXBlbmRpbmdJbXBvcnRQcmV2aWV3TGluZXMS'
    'MAoUaW1wb3J0X3ByZXZpZXdfbGluZXMYNCADKAlSEmltcG9ydFByZXZpZXdMaW5lcxIlCg5pc1'
    '9wbGFjZWhvbGRlchg1IAEoCFINaXNQbGFjZWhvbGRlcg==');

@$core.Deprecated('Use keyValueRowDescriptor instead')
const KeyValueRow$json = {
  '1': 'KeyValueRow',
  '2': [
    {'1': 'label', '3': 1, '4': 1, '5': 9, '10': 'label'},
    {'1': 'value', '3': 2, '4': 1, '5': 9, '10': 'value'},
  ],
};

/// Descriptor for `KeyValueRow`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List keyValueRowDescriptor = $convert.base64Decode(
    'CgtLZXlWYWx1ZVJvdxIUCgVsYWJlbBgBIAEoCVIFbGFiZWwSFAoFdmFsdWUYAiABKAlSBXZhbH'
    'Vl');

@$core.Deprecated('Use subjectGateActionDescriptor instead')
const SubjectGateAction$json = {
  '1': 'SubjectGateAction',
  '2': [
    {'1': 'display_kind', '3': 1, '4': 1, '5': 14, '6': '.realized.workstation.subjectworkflow.v1.SubjectGateAction.DisplayKind', '10': 'displayKind'},
    {'1': 'action_kind', '3': 2, '4': 1, '5': 9, '10': 'actionKind'},
    {'1': 'key', '3': 3, '4': 1, '5': 9, '10': 'key'},
    {'1': 'label', '3': 4, '4': 1, '5': 9, '10': 'label'},
    {'1': 'enabled', '3': 5, '4': 1, '5': 8, '10': 'enabled'},
  ],
  '4': [SubjectGateAction_DisplayKind$json],
};

@$core.Deprecated('Use subjectGateActionDescriptor instead')
const SubjectGateAction_DisplayKind$json = {
  '1': 'DisplayKind',
  '2': [
    {'1': 'DISPLAY_KIND_UNSPECIFIED', '2': 0},
    {'1': 'BUTTON', '2': 1},
    {'1': 'LINK', '2': 2},
  ],
};

/// Descriptor for `SubjectGateAction`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List subjectGateActionDescriptor = $convert.base64Decode(
    'ChFTdWJqZWN0R2F0ZUFjdGlvbhJpCgxkaXNwbGF5X2tpbmQYASABKA4yRi5yZWFsaXplZC53b3'
    'Jrc3RhdGlvbi5zdWJqZWN0d29ya2Zsb3cudjEuU3ViamVjdEdhdGVBY3Rpb24uRGlzcGxheUtp'
    'bmRSC2Rpc3BsYXlLaW5kEh8KC2FjdGlvbl9raW5kGAIgASgJUgphY3Rpb25LaW5kEhAKA2tleR'
    'gDIAEoCVIDa2V5EhQKBWxhYmVsGAQgASgJUgVsYWJlbBIYCgdlbmFibGVkGAUgASgIUgdlbmFi'
    'bGVkIkEKC0Rpc3BsYXlLaW5kEhwKGERJU1BMQVlfS0lORF9VTlNQRUNJRklFRBAAEgoKBkJVVF'
    'RPThABEggKBExJTksQAg==');

@$core.Deprecated('Use subjectActionSpecDescriptor instead')
const SubjectActionSpec$json = {
  '1': 'SubjectActionSpec',
  '2': [
    {'1': 'key', '3': 1, '4': 1, '5': 9, '10': 'key'},
    {'1': 'label', '3': 2, '4': 1, '5': 9, '10': 'label'},
    {'1': 'enabled', '3': 3, '4': 1, '5': 8, '10': 'enabled'},
  ],
};

/// Descriptor for `SubjectActionSpec`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List subjectActionSpecDescriptor = $convert.base64Decode(
    'ChFTdWJqZWN0QWN0aW9uU3BlYxIQCgNrZXkYASABKAlSA2tleRIUCgVsYWJlbBgCIAEoCVIFbG'
    'FiZWwSGAoHZW5hYmxlZBgDIAEoCFIHZW5hYmxlZA==');

@$core.Deprecated('Use subjectOptionDescriptor instead')
const SubjectOption$json = {
  '1': 'SubjectOption',
  '2': [
    {'1': 'label', '3': 1, '4': 1, '5': 9, '10': 'label'},
    {'1': 'value', '3': 2, '4': 1, '5': 9, '10': 'value'},
  ],
};

/// Descriptor for `SubjectOption`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List subjectOptionDescriptor = $convert.base64Decode(
    'Cg1TdWJqZWN0T3B0aW9uEhQKBWxhYmVsGAEgASgJUgVsYWJlbBIUCgV2YWx1ZRgCIAEoCVIFdm'
    'FsdWU=');

@$core.Deprecated('Use subjectSelectionOptionDescriptor instead')
const SubjectSelectionOption$json = {
  '1': 'SubjectSelectionOption',
  '2': [
    {'1': 'label', '3': 1, '4': 1, '5': 9, '10': 'label'},
    {'1': 'value', '3': 2, '4': 1, '5': 9, '10': 'value'},
    {'1': 'selected', '3': 3, '4': 1, '5': 8, '10': 'selected'},
  ],
};

/// Descriptor for `SubjectSelectionOption`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List subjectSelectionOptionDescriptor = $convert.base64Decode(
    'ChZTdWJqZWN0U2VsZWN0aW9uT3B0aW9uEhQKBWxhYmVsGAEgASgJUgVsYWJlbBIUCgV2YWx1ZR'
    'gCIAEoCVIFdmFsdWUSGgoIc2VsZWN0ZWQYAyABKAhSCHNlbGVjdGVk');

@$core.Deprecated('Use subjectSelectSpecViewDescriptor instead')
const SubjectSelectSpecView$json = {
  '1': 'SubjectSelectSpecView',
  '2': [
    {'1': 'key', '3': 1, '4': 1, '5': 9, '10': 'key'},
    {'1': 'label', '3': 2, '4': 1, '5': 9, '10': 'label'},
    {'1': 'value', '3': 3, '4': 1, '5': 9, '10': 'value'},
    {'1': 'options', '3': 4, '4': 3, '5': 11, '6': '.realized.workstation.subjectworkflow.v1.SubjectOption', '10': 'options'},
    {'1': 'enabled', '3': 5, '4': 1, '5': 8, '10': 'enabled'},
  ],
};

/// Descriptor for `SubjectSelectSpecView`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List subjectSelectSpecViewDescriptor = $convert.base64Decode(
    'ChVTdWJqZWN0U2VsZWN0U3BlY1ZpZXcSEAoDa2V5GAEgASgJUgNrZXkSFAoFbGFiZWwYAiABKA'
    'lSBWxhYmVsEhQKBXZhbHVlGAMgASgJUgV2YWx1ZRJQCgdvcHRpb25zGAQgAygLMjYucmVhbGl6'
    'ZWQud29ya3N0YXRpb24uc3ViamVjdHdvcmtmbG93LnYxLlN1YmplY3RPcHRpb25SB29wdGlvbn'
    'MSGAoHZW5hYmxlZBgFIAEoCFIHZW5hYmxlZA==');

@$core.Deprecated('Use subjectSwitchSpecViewDescriptor instead')
const SubjectSwitchSpecView$json = {
  '1': 'SubjectSwitchSpecView',
  '2': [
    {'1': 'key', '3': 1, '4': 1, '5': 9, '10': 'key'},
    {'1': 'label', '3': 2, '4': 1, '5': 9, '10': 'label'},
    {'1': 'value', '3': 3, '4': 1, '5': 8, '10': 'value'},
    {'1': 'enabled', '3': 4, '4': 1, '5': 8, '10': 'enabled'},
  ],
};

/// Descriptor for `SubjectSwitchSpecView`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List subjectSwitchSpecViewDescriptor = $convert.base64Decode(
    'ChVTdWJqZWN0U3dpdGNoU3BlY1ZpZXcSEAoDa2V5GAEgASgJUgNrZXkSFAoFbGFiZWwYAiABKA'
    'lSBWxhYmVsEhQKBXZhbHVlGAMgASgIUgV2YWx1ZRIYCgdlbmFibGVkGAQgASgIUgdlbmFibGVk');

@$core.Deprecated('Use subjectSelectionListSpecViewDescriptor instead')
const SubjectSelectionListSpecView$json = {
  '1': 'SubjectSelectionListSpecView',
  '2': [
    {'1': 'key', '3': 1, '4': 1, '5': 9, '10': 'key'},
    {'1': 'label', '3': 2, '4': 1, '5': 9, '10': 'label'},
    {'1': 'action_key_prefix', '3': 3, '4': 1, '5': 9, '10': 'actionKeyPrefix'},
    {'1': 'options', '3': 4, '4': 3, '5': 11, '6': '.realized.workstation.subjectworkflow.v1.SubjectSelectionOption', '10': 'options'},
    {'1': 'enabled', '3': 5, '4': 1, '5': 8, '10': 'enabled'},
  ],
};

/// Descriptor for `SubjectSelectionListSpecView`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List subjectSelectionListSpecViewDescriptor = $convert.base64Decode(
    'ChxTdWJqZWN0U2VsZWN0aW9uTGlzdFNwZWNWaWV3EhAKA2tleRgBIAEoCVIDa2V5EhQKBWxhYm'
    'VsGAIgASgJUgVsYWJlbBIqChFhY3Rpb25fa2V5X3ByZWZpeBgDIAEoCVIPYWN0aW9uS2V5UHJl'
    'Zml4ElkKB29wdGlvbnMYBCADKAsyPy5yZWFsaXplZC53b3Jrc3RhdGlvbi5zdWJqZWN0d29ya2'
    'Zsb3cudjEuU3ViamVjdFNlbGVjdGlvbk9wdGlvblIHb3B0aW9ucxIYCgdlbmFibGVkGAUgASgI'
    'UgdlbmFibGVk');

@$core.Deprecated('Use subjectTableRowDescriptor instead')
const SubjectTableRow$json = {
  '1': 'SubjectTableRow',
  '2': [
    {'1': 'cells', '3': 1, '4': 3, '5': 9, '10': 'cells'},
  ],
};

/// Descriptor for `SubjectTableRow`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List subjectTableRowDescriptor = $convert.base64Decode(
    'Cg9TdWJqZWN0VGFibGVSb3cSFAoFY2VsbHMYASADKAlSBWNlbGxz');

@$core.Deprecated('Use subjectTableSpecViewDescriptor instead')
const SubjectTableSpecView$json = {
  '1': 'SubjectTableSpecView',
  '2': [
    {'1': 'key', '3': 1, '4': 1, '5': 9, '10': 'key'},
    {'1': 'label', '3': 2, '4': 1, '5': 9, '10': 'label'},
    {'1': 'columns', '3': 3, '4': 3, '5': 9, '10': 'columns'},
    {'1': 'rows', '3': 4, '4': 3, '5': 11, '6': '.realized.workstation.subjectworkflow.v1.SubjectTableRow', '10': 'rows'},
    {'1': 'enabled', '3': 5, '4': 1, '5': 8, '10': 'enabled'},
  ],
};

/// Descriptor for `SubjectTableSpecView`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List subjectTableSpecViewDescriptor = $convert.base64Decode(
    'ChRTdWJqZWN0VGFibGVTcGVjVmlldxIQCgNrZXkYASABKAlSA2tleRIUCgVsYWJlbBgCIAEoCV'
    'IFbGFiZWwSGAoHY29sdW1ucxgDIAMoCVIHY29sdW1ucxJMCgRyb3dzGAQgAygLMjgucmVhbGl6'
    'ZWQud29ya3N0YXRpb24uc3ViamVjdHdvcmtmbG93LnYxLlN1YmplY3RUYWJsZVJvd1IEcm93cx'
    'IYCgdlbmFibGVkGAUgASgIUgdlbmFibGVk');

@$core.Deprecated('Use subjectControlBundleViewDescriptor instead')
const SubjectControlBundleView$json = {
  '1': 'SubjectControlBundleView',
  '2': [
    {'1': 'phase', '3': 1, '4': 1, '5': 9, '10': 'phase'},
    {'1': 'more_actions', '3': 2, '4': 3, '5': 11, '6': '.realized.workstation.subjectworkflow.v1.SubjectActionSpec', '10': 'moreActions'},
    {'1': 'selects', '3': 3, '4': 3, '5': 11, '6': '.realized.workstation.subjectworkflow.v1.SubjectSelectSpecView', '10': 'selects'},
    {'1': 'switches', '3': 4, '4': 3, '5': 11, '6': '.realized.workstation.subjectworkflow.v1.SubjectSwitchSpecView', '10': 'switches'},
    {'1': 'selection_lists', '3': 5, '4': 3, '5': 11, '6': '.realized.workstation.subjectworkflow.v1.SubjectSelectionListSpecView', '10': 'selectionLists'},
    {'1': 'tables', '3': 6, '4': 3, '5': 11, '6': '.realized.workstation.subjectworkflow.v1.SubjectTableSpecView', '10': 'tables'},
  ],
};

/// Descriptor for `SubjectControlBundleView`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List subjectControlBundleViewDescriptor = $convert.base64Decode(
    'ChhTdWJqZWN0Q29udHJvbEJ1bmRsZVZpZXcSFAoFcGhhc2UYASABKAlSBXBoYXNlEl0KDG1vcm'
    'VfYWN0aW9ucxgCIAMoCzI6LnJlYWxpemVkLndvcmtzdGF0aW9uLnN1YmplY3R3b3JrZmxvdy52'
    'MS5TdWJqZWN0QWN0aW9uU3BlY1ILbW9yZUFjdGlvbnMSWAoHc2VsZWN0cxgDIAMoCzI+LnJlYW'
    'xpemVkLndvcmtzdGF0aW9uLnN1YmplY3R3b3JrZmxvdy52MS5TdWJqZWN0U2VsZWN0U3BlY1Zp'
    'ZXdSB3NlbGVjdHMSWgoIc3dpdGNoZXMYBCADKAsyPi5yZWFsaXplZC53b3Jrc3RhdGlvbi5zdW'
    'JqZWN0d29ya2Zsb3cudjEuU3ViamVjdFN3aXRjaFNwZWNWaWV3Ughzd2l0Y2hlcxJuCg9zZWxl'
    'Y3Rpb25fbGlzdHMYBSADKAsyRS5yZWFsaXplZC53b3Jrc3RhdGlvbi5zdWJqZWN0d29ya2Zsb3'
    'cudjEuU3ViamVjdFNlbGVjdGlvbkxpc3RTcGVjVmlld1IOc2VsZWN0aW9uTGlzdHMSVQoGdGFi'
    'bGVzGAYgAygLMj0ucmVhbGl6ZWQud29ya3N0YXRpb24uc3ViamVjdHdvcmtmbG93LnYxLlN1Ym'
    'plY3RUYWJsZVNwZWNWaWV3UgZ0YWJsZXM=');

@$core.Deprecated('Use subjectCurrentStepViewDescriptor instead')
const SubjectCurrentStepView$json = {
  '1': 'SubjectCurrentStepView',
  '2': [
    {'1': 'title', '3': 1, '4': 1, '5': 9, '10': 'title'},
    {'1': 'status', '3': 2, '4': 1, '5': 9, '10': 'status'},
    {'1': 'why', '3': 3, '4': 1, '5': 9, '10': 'why'},
    {'1': 'detail_lines', '3': 4, '4': 3, '5': 9, '10': 'detailLines'},
    {'1': 'actions', '3': 5, '4': 3, '5': 11, '6': '.realized.workstation.subjectworkflow.v1.SubjectGateAction', '10': 'actions'},
  ],
};

/// Descriptor for `SubjectCurrentStepView`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List subjectCurrentStepViewDescriptor = $convert.base64Decode(
    'ChZTdWJqZWN0Q3VycmVudFN0ZXBWaWV3EhQKBXRpdGxlGAEgASgJUgV0aXRsZRIWCgZzdGF0dX'
    'MYAiABKAlSBnN0YXR1cxIQCgN3aHkYAyABKAlSA3doeRIhCgxkZXRhaWxfbGluZXMYBCADKAlS'
    'C2RldGFpbExpbmVzElQKB2FjdGlvbnMYBSADKAsyOi5yZWFsaXplZC53b3Jrc3RhdGlvbi5zdW'
    'JqZWN0d29ya2Zsb3cudjEuU3ViamVjdEdhdGVBY3Rpb25SB2FjdGlvbnM=');

@$core.Deprecated('Use textSectionDescriptor instead')
const TextSection$json = {
  '1': 'TextSection',
  '2': [
    {'1': 'title', '3': 1, '4': 1, '5': 9, '10': 'title'},
    {'1': 'lines', '3': 2, '4': 3, '5': 9, '10': 'lines'},
  ],
};

/// Descriptor for `TextSection`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List textSectionDescriptor = $convert.base64Decode(
    'CgtUZXh0U2VjdGlvbhIUCgV0aXRsZRgBIAEoCVIFdGl0bGUSFAoFbGluZXMYAiADKAlSBWxpbm'
    'Vz');

@$core.Deprecated('Use subjectStatusViewDescriptor instead')
const SubjectStatusView$json = {
  '1': 'SubjectStatusView',
  '2': [
    {'1': 'title', '3': 1, '4': 1, '5': 9, '10': 'title'},
    {'1': 'rows', '3': 2, '4': 3, '5': 11, '6': '.realized.workstation.subjectworkflow.v1.KeyValueRow', '10': 'rows'},
  ],
};

/// Descriptor for `SubjectStatusView`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List subjectStatusViewDescriptor = $convert.base64Decode(
    'ChFTdWJqZWN0U3RhdHVzVmlldxIUCgV0aXRsZRgBIAEoCVIFdGl0bGUSSAoEcm93cxgCIAMoCz'
    'I0LnJlYWxpemVkLndvcmtzdGF0aW9uLnN1YmplY3R3b3JrZmxvdy52MS5LZXlWYWx1ZVJvd1IE'
    'cm93cw==');

@$core.Deprecated('Use subjectPhaseViewDescriptor instead')
const SubjectPhaseView$json = {
  '1': 'SubjectPhaseView',
  '2': [
    {'1': 'phase', '3': 1, '4': 1, '5': 9, '10': 'phase'},
    {'1': 'phase_title', '3': 2, '4': 1, '5': 9, '10': 'phaseTitle'},
    {'1': 'preferred_phase', '3': 3, '4': 1, '5': 9, '10': 'preferredPhase'},
    {'1': 'scenario', '3': 4, '4': 1, '5': 11, '6': '.realized.workstation.subjectworkflow.v1.SubjectScenarioSummary', '10': 'scenario'},
    {'1': 'current_step', '3': 5, '4': 1, '5': 11, '6': '.realized.workstation.subjectworkflow.v1.SubjectCurrentStepView', '10': 'currentStep'},
    {'1': 'status_view', '3': 6, '4': 1, '5': 11, '6': '.realized.workstation.subjectworkflow.v1.SubjectStatusView', '10': 'statusView'},
    {'1': 'journey_lines', '3': 7, '4': 3, '5': 9, '10': 'journeyLines'},
    {'1': 'workspace_view', '3': 8, '4': 1, '5': 11, '6': '.realized.workstation.subjectworkflow.v1.TextSection', '10': 'workspaceView'},
    {'1': 'latest_receipt_title', '3': 9, '4': 1, '5': 9, '10': 'latestReceiptTitle'},
    {'1': 'latest_receipt_lines', '3': 10, '4': 3, '5': 9, '10': 'latestReceiptLines'},
  ],
};

/// Descriptor for `SubjectPhaseView`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List subjectPhaseViewDescriptor = $convert.base64Decode(
    'ChBTdWJqZWN0UGhhc2VWaWV3EhQKBXBoYXNlGAEgASgJUgVwaGFzZRIfCgtwaGFzZV90aXRsZR'
    'gCIAEoCVIKcGhhc2VUaXRsZRInCg9wcmVmZXJyZWRfcGhhc2UYAyABKAlSDnByZWZlcnJlZFBo'
    'YXNlElsKCHNjZW5hcmlvGAQgASgLMj8ucmVhbGl6ZWQud29ya3N0YXRpb24uc3ViamVjdHdvcm'
    'tmbG93LnYxLlN1YmplY3RTY2VuYXJpb1N1bW1hcnlSCHNjZW5hcmlvEmIKDGN1cnJlbnRfc3Rl'
    'cBgFIAEoCzI/LnJlYWxpemVkLndvcmtzdGF0aW9uLnN1YmplY3R3b3JrZmxvdy52MS5TdWJqZW'
    'N0Q3VycmVudFN0ZXBWaWV3UgtjdXJyZW50U3RlcBJbCgtzdGF0dXNfdmlldxgGIAEoCzI6LnJl'
    'YWxpemVkLndvcmtzdGF0aW9uLnN1YmplY3R3b3JrZmxvdy52MS5TdWJqZWN0U3RhdHVzVmlld1'
    'IKc3RhdHVzVmlldxIjCg1qb3VybmV5X2xpbmVzGAcgAygJUgxqb3VybmV5TGluZXMSWwoOd29y'
    'a3NwYWNlX3ZpZXcYCCABKAsyNC5yZWFsaXplZC53b3Jrc3RhdGlvbi5zdWJqZWN0d29ya2Zsb3'
    'cudjEuVGV4dFNlY3Rpb25SDXdvcmtzcGFjZVZpZXcSMAoUbGF0ZXN0X3JlY2VpcHRfdGl0bGUY'
    'CSABKAlSEmxhdGVzdFJlY2VpcHRUaXRsZRIwChRsYXRlc3RfcmVjZWlwdF9saW5lcxgKIAMoCV'
    'ISbGF0ZXN0UmVjZWlwdExpbmVz');

@$core.Deprecated('Use subjectImportStagingDescriptor instead')
const SubjectImportStaging$json = {
  '1': 'SubjectImportStaging',
  '2': [
    {'1': 'source_subject_id', '3': 1, '4': 1, '5': 9, '10': 'sourceSubjectId'},
    {'1': 'source_subject_title', '3': 2, '4': 1, '5': 9, '10': 'sourceSubjectTitle'},
    {'1': 'source_subject_version_id', '3': 3, '4': 1, '5': 9, '10': 'sourceSubjectVersionId'},
    {'1': 'import_kind', '3': 4, '4': 1, '5': 9, '10': 'importKind'},
    {'1': 'selection_profile', '3': 5, '4': 1, '5': 9, '10': 'selectionProfile'},
  ],
};

/// Descriptor for `SubjectImportStaging`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List subjectImportStagingDescriptor = $convert.base64Decode(
    'ChRTdWJqZWN0SW1wb3J0U3RhZ2luZxIqChFzb3VyY2Vfc3ViamVjdF9pZBgBIAEoCVIPc291cm'
    'NlU3ViamVjdElkEjAKFHNvdXJjZV9zdWJqZWN0X3RpdGxlGAIgASgJUhJzb3VyY2VTdWJqZWN0'
    'VGl0bGUSOQoZc291cmNlX3N1YmplY3RfdmVyc2lvbl9pZBgDIAEoCVIWc291cmNlU3ViamVjdF'
    'ZlcnNpb25JZBIfCgtpbXBvcnRfa2luZBgEIAEoCVIKaW1wb3J0S2luZBIrChFzZWxlY3Rpb25f'
    'cHJvZmlsZRgFIAEoCVIQc2VsZWN0aW9uUHJvZmlsZQ==');

@$core.Deprecated('Use subjectPhaseProjectionContextDescriptor instead')
const SubjectPhaseProjectionContext$json = {
  '1': 'SubjectPhaseProjectionContext',
  '2': [
    {'1': 'can_capture_assistant', '3': 1, '4': 1, '5': 8, '10': 'canCaptureAssistant'},
    {'1': 'markdown_selected_path', '3': 2, '4': 1, '5': 9, '10': 'markdownSelectedPath'},
    {'1': 'markdown_status_text', '3': 3, '4': 1, '5': 9, '10': 'markdownStatusText'},
    {'1': 'markdown_busy', '3': 4, '4': 1, '5': 8, '10': 'markdownBusy'},
  ],
};

/// Descriptor for `SubjectPhaseProjectionContext`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List subjectPhaseProjectionContextDescriptor = $convert.base64Decode(
    'Ch1TdWJqZWN0UGhhc2VQcm9qZWN0aW9uQ29udGV4dBIyChVjYW5fY2FwdHVyZV9hc3Npc3Rhbn'
    'QYASABKAhSE2NhbkNhcHR1cmVBc3Npc3RhbnQSNAoWbWFya2Rvd25fc2VsZWN0ZWRfcGF0aBgC'
    'IAEoCVIUbWFya2Rvd25TZWxlY3RlZFBhdGgSMAoUbWFya2Rvd25fc3RhdHVzX3RleHQYAyABKA'
    'lSEm1hcmtkb3duU3RhdHVzVGV4dBIjCg1tYXJrZG93bl9idXN5GAQgASgIUgxtYXJrZG93bkJ1'
    'c3k=');

@$core.Deprecated('Use subjectActionResultDescriptor instead')
const SubjectActionResult$json = {
  '1': 'SubjectActionResult',
  '2': [
    {'1': 'status_text', '3': 1, '4': 1, '5': 9, '10': 'statusText'},
    {'1': 'timeline_text', '3': 2, '4': 1, '5': 9, '10': 'timelineText'},
    {'1': 'next_phase', '3': 3, '4': 1, '5': 9, '10': 'nextPhase'},
    {'1': 'next_tab', '3': 4, '4': 1, '5': 9, '10': 'nextTab'},
    {'1': 'reload_subjects', '3': 5, '4': 1, '5': 8, '10': 'reloadSubjects'},
    {'1': 'open_paths', '3': 6, '4': 3, '5': 9, '10': 'openPaths'},
    {'1': 'preferred_subject_key', '3': 7, '4': 1, '5': 9, '10': 'preferredSubjectKey'},
    {'1': 'open_artifacts', '3': 8, '4': 3, '5': 11, '6': '.workstation.ArtifactRef', '10': 'openArtifacts'},
  ],
};

/// Descriptor for `SubjectActionResult`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List subjectActionResultDescriptor = $convert.base64Decode(
    'ChNTdWJqZWN0QWN0aW9uUmVzdWx0Eh8KC3N0YXR1c190ZXh0GAEgASgJUgpzdGF0dXNUZXh0Ei'
    'MKDXRpbWVsaW5lX3RleHQYAiABKAlSDHRpbWVsaW5lVGV4dBIdCgpuZXh0X3BoYXNlGAMgASgJ'
    'UgluZXh0UGhhc2USGQoIbmV4dF90YWIYBCABKAlSB25leHRUYWISJwoPcmVsb2FkX3N1YmplY3'
    'RzGAUgASgIUg5yZWxvYWRTdWJqZWN0cxIdCgpvcGVuX3BhdGhzGAYgAygJUglvcGVuUGF0aHMS'
    'MgoVcHJlZmVycmVkX3N1YmplY3Rfa2V5GAcgASgJUhNwcmVmZXJyZWRTdWJqZWN0S2V5Ej8KDm'
    '9wZW5fYXJ0aWZhY3RzGAggAygLMhgud29ya3N0YXRpb24uQXJ0aWZhY3RSZWZSDW9wZW5BcnRp'
    'ZmFjdHM=');

@$core.Deprecated('Use listSubjectsRequestDescriptor instead')
const ListSubjectsRequest$json = {
  '1': 'ListSubjectsRequest',
  '2': [
    {'1': 'root_path', '3': 1, '4': 1, '5': 9, '10': 'rootPath'},
  ],
};

/// Descriptor for `ListSubjectsRequest`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List listSubjectsRequestDescriptor = $convert.base64Decode(
    'ChNMaXN0U3ViamVjdHNSZXF1ZXN0EhsKCXJvb3RfcGF0aBgBIAEoCVIIcm9vdFBhdGg=');

@$core.Deprecated('Use listSubjectsResponseDescriptor instead')
const ListSubjectsResponse$json = {
  '1': 'ListSubjectsResponse',
  '2': [
    {'1': 'subjects', '3': 1, '4': 3, '5': 11, '6': '.realized.workstation.subjectworkflow.v1.SubjectScenarioSummary', '10': 'subjects'},
    {'1': 'trace_id', '3': 100, '4': 1, '5': 9, '10': 'traceId'},
    {'1': 'parent_id', '3': 101, '4': 1, '5': 9, '10': 'parentId'},
  ],
};

/// Descriptor for `ListSubjectsResponse`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List listSubjectsResponseDescriptor = $convert.base64Decode(
    'ChRMaXN0U3ViamVjdHNSZXNwb25zZRJbCghzdWJqZWN0cxgBIAMoCzI/LnJlYWxpemVkLndvcm'
    'tzdGF0aW9uLnN1YmplY3R3b3JrZmxvdy52MS5TdWJqZWN0U2NlbmFyaW9TdW1tYXJ5UghzdWJq'
    'ZWN0cxIZCgh0cmFjZV9pZBhkIAEoCVIHdHJhY2VJZBIbCglwYXJlbnRfaWQYZSABKAlSCHBhcm'
    'VudElk');

@$core.Deprecated('Use getSubjectPhaseViewRequestDescriptor instead')
const GetSubjectPhaseViewRequest$json = {
  '1': 'GetSubjectPhaseViewRequest',
  '2': [
    {'1': 'root_path', '3': 1, '4': 1, '5': 9, '10': 'rootPath'},
    {'1': 'subject_id', '3': 2, '4': 1, '5': 9, '10': 'subjectId'},
    {'1': 'phase', '3': 3, '4': 1, '5': 9, '10': 'phase'},
    {'1': 'projection_context', '3': 4, '4': 1, '5': 11, '6': '.realized.workstation.subjectworkflow.v1.SubjectPhaseProjectionContext', '10': 'projectionContext'},
    {'1': 'client_session_id', '3': 5, '4': 1, '5': 9, '10': 'clientSessionId'},
  ],
};

/// Descriptor for `GetSubjectPhaseViewRequest`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List getSubjectPhaseViewRequestDescriptor = $convert.base64Decode(
    'ChpHZXRTdWJqZWN0UGhhc2VWaWV3UmVxdWVzdBIbCglyb290X3BhdGgYASABKAlSCHJvb3RQYX'
    'RoEh0KCnN1YmplY3RfaWQYAiABKAlSCXN1YmplY3RJZBIUCgVwaGFzZRgDIAEoCVIFcGhhc2US'
    'dQoScHJvamVjdGlvbl9jb250ZXh0GAQgASgLMkYucmVhbGl6ZWQud29ya3N0YXRpb24uc3Viam'
    'VjdHdvcmtmbG93LnYxLlN1YmplY3RQaGFzZVByb2plY3Rpb25Db250ZXh0UhFwcm9qZWN0aW9u'
    'Q29udGV4dBIqChFjbGllbnRfc2Vzc2lvbl9pZBgFIAEoCVIPY2xpZW50U2Vzc2lvbklk');

@$core.Deprecated('Use getSubjectPhaseViewResponseDescriptor instead')
const GetSubjectPhaseViewResponse$json = {
  '1': 'GetSubjectPhaseViewResponse',
  '2': [
    {'1': 'view', '3': 1, '4': 1, '5': 11, '6': '.realized.workstation.subjectworkflow.v1.SubjectPhaseView', '10': 'view'},
    {'1': 'trace_id', '3': 100, '4': 1, '5': 9, '10': 'traceId'},
    {'1': 'parent_id', '3': 101, '4': 1, '5': 9, '10': 'parentId'},
  ],
};

/// Descriptor for `GetSubjectPhaseViewResponse`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List getSubjectPhaseViewResponseDescriptor = $convert.base64Decode(
    'ChtHZXRTdWJqZWN0UGhhc2VWaWV3UmVzcG9uc2USTQoEdmlldxgBIAEoCzI5LnJlYWxpemVkLn'
    'dvcmtzdGF0aW9uLnN1YmplY3R3b3JrZmxvdy52MS5TdWJqZWN0UGhhc2VWaWV3UgR2aWV3EhkK'
    'CHRyYWNlX2lkGGQgASgJUgd0cmFjZUlkEhsKCXBhcmVudF9pZBhlIAEoCVIIcGFyZW50SWQ=');

@$core.Deprecated('Use getSubjectControlBundleRequestDescriptor instead')
const GetSubjectControlBundleRequest$json = {
  '1': 'GetSubjectControlBundleRequest',
  '2': [
    {'1': 'root_path', '3': 1, '4': 1, '5': 9, '10': 'rootPath'},
    {'1': 'subject_id', '3': 2, '4': 1, '5': 9, '10': 'subjectId'},
    {'1': 'phase', '3': 3, '4': 1, '5': 9, '10': 'phase'},
    {'1': 'projection_context', '3': 4, '4': 1, '5': 11, '6': '.realized.workstation.subjectworkflow.v1.SubjectPhaseProjectionContext', '10': 'projectionContext'},
    {'1': 'client_session_id', '3': 5, '4': 1, '5': 9, '10': 'clientSessionId'},
  ],
};

/// Descriptor for `GetSubjectControlBundleRequest`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List getSubjectControlBundleRequestDescriptor = $convert.base64Decode(
    'Ch5HZXRTdWJqZWN0Q29udHJvbEJ1bmRsZVJlcXVlc3QSGwoJcm9vdF9wYXRoGAEgASgJUghyb2'
    '90UGF0aBIdCgpzdWJqZWN0X2lkGAIgASgJUglzdWJqZWN0SWQSFAoFcGhhc2UYAyABKAlSBXBo'
    'YXNlEnUKEnByb2plY3Rpb25fY29udGV4dBgEIAEoCzJGLnJlYWxpemVkLndvcmtzdGF0aW9uLn'
    'N1YmplY3R3b3JrZmxvdy52MS5TdWJqZWN0UGhhc2VQcm9qZWN0aW9uQ29udGV4dFIRcHJvamVj'
    'dGlvbkNvbnRleHQSKgoRY2xpZW50X3Nlc3Npb25faWQYBSABKAlSD2NsaWVudFNlc3Npb25JZA'
    '==');

@$core.Deprecated('Use getSubjectControlBundleResponseDescriptor instead')
const GetSubjectControlBundleResponse$json = {
  '1': 'GetSubjectControlBundleResponse',
  '2': [
    {'1': 'bundle', '3': 1, '4': 1, '5': 11, '6': '.realized.workstation.subjectworkflow.v1.SubjectControlBundleView', '10': 'bundle'},
    {'1': 'trace_id', '3': 100, '4': 1, '5': 9, '10': 'traceId'},
    {'1': 'parent_id', '3': 101, '4': 1, '5': 9, '10': 'parentId'},
  ],
};

/// Descriptor for `GetSubjectControlBundleResponse`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List getSubjectControlBundleResponseDescriptor = $convert.base64Decode(
    'Ch9HZXRTdWJqZWN0Q29udHJvbEJ1bmRsZVJlc3BvbnNlElkKBmJ1bmRsZRgBIAEoCzJBLnJlYW'
    'xpemVkLndvcmtzdGF0aW9uLnN1YmplY3R3b3JrZmxvdy52MS5TdWJqZWN0Q29udHJvbEJ1bmRs'
    'ZVZpZXdSBmJ1bmRsZRIZCgh0cmFjZV9pZBhkIAEoCVIHdHJhY2VJZBIbCglwYXJlbnRfaWQYZS'
    'ABKAlSCHBhcmVudElk');

@$core.Deprecated('Use subjectPaneViewDescriptor instead')
const SubjectPaneView$json = {
  '1': 'SubjectPaneView',
  '2': [
    {'1': 'key', '3': 1, '4': 1, '5': 9, '10': 'key'},
    {'1': 'title', '3': 2, '4': 1, '5': 9, '10': 'title'},
    {'1': 'lines', '3': 3, '4': 3, '5': 9, '10': 'lines'},
    {'1': 'rows', '3': 4, '4': 3, '5': 11, '6': '.realized.workstation.subjectworkflow.v1.KeyValueRow', '10': 'rows'},
    {'1': 'is_structured_table', '3': 5, '4': 1, '5': 8, '10': 'isStructuredTable'},
    {'1': 'items', '3': 6, '4': 3, '5': 11, '6': '.realized.workstation.subjectworkflow.v1.SubjectPaneItemView', '10': 'items'},
  ],
};

/// Descriptor for `SubjectPaneView`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List subjectPaneViewDescriptor = $convert.base64Decode(
    'Cg9TdWJqZWN0UGFuZVZpZXcSEAoDa2V5GAEgASgJUgNrZXkSFAoFdGl0bGUYAiABKAlSBXRpdG'
    'xlEhQKBWxpbmVzGAMgAygJUgVsaW5lcxJICgRyb3dzGAQgAygLMjQucmVhbGl6ZWQud29ya3N0'
    'YXRpb24uc3ViamVjdHdvcmtmbG93LnYxLktleVZhbHVlUm93UgRyb3dzEi4KE2lzX3N0cnVjdH'
    'VyZWRfdGFibGUYBSABKAhSEWlzU3RydWN0dXJlZFRhYmxlElIKBWl0ZW1zGAYgAygLMjwucmVh'
    'bGl6ZWQud29ya3N0YXRpb24uc3ViamVjdHdvcmtmbG93LnYxLlN1YmplY3RQYW5lSXRlbVZpZX'
    'dSBWl0ZW1z');

@$core.Deprecated('Use subjectPaneItemViewDescriptor instead')
const SubjectPaneItemView$json = {
  '1': 'SubjectPaneItemView',
  '2': [
    {'1': 'entry_id', '3': 1, '4': 1, '5': 9, '10': 'entryId'},
    {'1': 'entry_kind', '3': 2, '4': 1, '5': 9, '10': 'entryKind'},
    {'1': 'label', '3': 3, '4': 1, '5': 9, '10': 'label'},
    {'1': 'ordinal', '3': 4, '4': 1, '5': 5, '10': 'ordinal'},
    {'1': 'parent_entry_id', '3': 5, '4': 1, '5': 9, '10': 'parentEntryId'},
    {'1': 'depth', '3': 6, '4': 1, '5': 5, '10': 'depth'},
    {'1': 'selectable', '3': 7, '4': 1, '5': 8, '10': 'selectable'},
    {'1': 'selected', '3': 8, '4': 1, '5': 8, '10': 'selected'},
    {'1': 'toggleable', '3': 9, '4': 1, '5': 8, '10': 'toggleable'},
    {'1': 'check_state', '3': 10, '4': 1, '5': 9, '10': 'checkState'},
    {'1': 'held', '3': 11, '4': 1, '5': 8, '10': 'held'},
    {'1': 'status', '3': 12, '4': 1, '5': 9, '10': 'status'},
    {'1': 'semantic_kind', '3': 13, '4': 1, '5': 9, '10': 'semanticKind'},
    {'1': 'render_kind', '3': 14, '4': 1, '5': 9, '10': 'renderKind'},
    {'1': 'evidence_mode', '3': 15, '4': 1, '5': 9, '10': 'evidenceMode'},
    {'1': 'transform_mode', '3': 16, '4': 1, '5': 9, '10': 'transformMode'},
    {'1': 'source_unit_id', '3': 17, '4': 1, '5': 9, '10': 'sourceUnitId'},
    {'1': 'source_item_id', '3': 18, '4': 1, '5': 9, '10': 'sourceItemId'},
    {'1': 'source_ref', '3': 19, '4': 1, '5': 9, '10': 'sourceRef'},
    {'1': 'source_kind', '3': 20, '4': 1, '5': 9, '10': 'sourceKind'},
    {'1': 'media_type', '3': 21, '4': 1, '5': 9, '10': 'mediaType'},
    {'1': 'latest_revision_id', '3': 22, '4': 1, '5': 9, '10': 'latestRevisionId'},
    {'1': 'latest_revision_kind', '3': 23, '4': 1, '5': 9, '10': 'latestRevisionKind'},
    {'1': 'revision_count', '3': 24, '4': 1, '5': 5, '10': 'revisionCount'},
    {'1': 'bundle_file_count', '3': 25, '4': 1, '5': 5, '10': 'bundleFileCount'},
    {'1': 'sort_kind', '3': 26, '4': 1, '5': 9, '10': 'sortKind'},
    {'1': 'summary', '3': 27, '4': 1, '5': 9, '10': 'summary'},
    {'1': 'description', '3': 28, '4': 1, '5': 9, '10': 'description'},
    {'1': 'query_text', '3': 29, '4': 1, '5': 9, '10': 'queryText'},
    {'1': 'notes', '3': 30, '4': 1, '5': 9, '10': 'notes'},
    {'1': 'confidence', '3': 31, '4': 1, '5': 1, '10': 'confidence'},
    {'1': 'related_ids', '3': 32, '4': 3, '5': 9, '10': 'relatedIds'},
    {'1': 'detail_title', '3': 33, '4': 1, '5': 9, '10': 'detailTitle'},
    {'1': 'detail_lines', '3': 34, '4': 3, '5': 9, '10': 'detailLines'},
    {'1': 'attributes', '3': 35, '4': 3, '5': 11, '6': '.realized.workstation.subjectworkflow.v1.KeyValueRow', '10': 'attributes'},
  ],
};

/// Descriptor for `SubjectPaneItemView`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List subjectPaneItemViewDescriptor = $convert.base64Decode(
    'ChNTdWJqZWN0UGFuZUl0ZW1WaWV3EhkKCGVudHJ5X2lkGAEgASgJUgdlbnRyeUlkEh0KCmVudH'
    'J5X2tpbmQYAiABKAlSCWVudHJ5S2luZBIUCgVsYWJlbBgDIAEoCVIFbGFiZWwSGAoHb3JkaW5h'
    'bBgEIAEoBVIHb3JkaW5hbBImCg9wYXJlbnRfZW50cnlfaWQYBSABKAlSDXBhcmVudEVudHJ5SW'
    'QSFAoFZGVwdGgYBiABKAVSBWRlcHRoEh4KCnNlbGVjdGFibGUYByABKAhSCnNlbGVjdGFibGUS'
    'GgoIc2VsZWN0ZWQYCCABKAhSCHNlbGVjdGVkEh4KCnRvZ2dsZWFibGUYCSABKAhSCnRvZ2dsZW'
    'FibGUSHwoLY2hlY2tfc3RhdGUYCiABKAlSCmNoZWNrU3RhdGUSEgoEaGVsZBgLIAEoCFIEaGVs'
    'ZBIWCgZzdGF0dXMYDCABKAlSBnN0YXR1cxIjCg1zZW1hbnRpY19raW5kGA0gASgJUgxzZW1hbn'
    'RpY0tpbmQSHwoLcmVuZGVyX2tpbmQYDiABKAlSCnJlbmRlcktpbmQSIwoNZXZpZGVuY2VfbW9k'
    'ZRgPIAEoCVIMZXZpZGVuY2VNb2RlEiUKDnRyYW5zZm9ybV9tb2RlGBAgASgJUg10cmFuc2Zvcm'
    '1Nb2RlEiQKDnNvdXJjZV91bml0X2lkGBEgASgJUgxzb3VyY2VVbml0SWQSJAoOc291cmNlX2l0'
    'ZW1faWQYEiABKAlSDHNvdXJjZUl0ZW1JZBIdCgpzb3VyY2VfcmVmGBMgASgJUglzb3VyY2VSZW'
    'YSHwoLc291cmNlX2tpbmQYFCABKAlSCnNvdXJjZUtpbmQSHQoKbWVkaWFfdHlwZRgVIAEoCVIJ'
    'bWVkaWFUeXBlEiwKEmxhdGVzdF9yZXZpc2lvbl9pZBgWIAEoCVIQbGF0ZXN0UmV2aXNpb25JZB'
    'IwChRsYXRlc3RfcmV2aXNpb25fa2luZBgXIAEoCVISbGF0ZXN0UmV2aXNpb25LaW5kEiUKDnJl'
    'dmlzaW9uX2NvdW50GBggASgFUg1yZXZpc2lvbkNvdW50EioKEWJ1bmRsZV9maWxlX2NvdW50GB'
    'kgASgFUg9idW5kbGVGaWxlQ291bnQSGwoJc29ydF9raW5kGBogASgJUghzb3J0S2luZBIYCgdz'
    'dW1tYXJ5GBsgASgJUgdzdW1tYXJ5EiAKC2Rlc2NyaXB0aW9uGBwgASgJUgtkZXNjcmlwdGlvbh'
    'IdCgpxdWVyeV90ZXh0GB0gASgJUglxdWVyeVRleHQSFAoFbm90ZXMYHiABKAlSBW5vdGVzEh4K'
    'CmNvbmZpZGVuY2UYHyABKAFSCmNvbmZpZGVuY2USHwoLcmVsYXRlZF9pZHMYICADKAlSCnJlbG'
    'F0ZWRJZHMSIQoMZGV0YWlsX3RpdGxlGCEgASgJUgtkZXRhaWxUaXRsZRIhCgxkZXRhaWxfbGlu'
    'ZXMYIiADKAlSC2RldGFpbExpbmVzElQKCmF0dHJpYnV0ZXMYIyADKAsyNC5yZWFsaXplZC53b3'
    'Jrc3RhdGlvbi5zdWJqZWN0d29ya2Zsb3cudjEuS2V5VmFsdWVSb3dSCmF0dHJpYnV0ZXM=');

@$core.Deprecated('Use subjectPaneBundleViewDescriptor instead')
const SubjectPaneBundleView$json = {
  '1': 'SubjectPaneBundleView',
  '2': [
    {'1': 'phase', '3': 1, '4': 1, '5': 9, '10': 'phase'},
    {'1': 'panes', '3': 2, '4': 3, '5': 11, '6': '.realized.workstation.subjectworkflow.v1.SubjectPaneView', '10': 'panes'},
  ],
};

/// Descriptor for `SubjectPaneBundleView`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List subjectPaneBundleViewDescriptor = $convert.base64Decode(
    'ChVTdWJqZWN0UGFuZUJ1bmRsZVZpZXcSFAoFcGhhc2UYASABKAlSBXBoYXNlEk4KBXBhbmVzGA'
    'IgAygLMjgucmVhbGl6ZWQud29ya3N0YXRpb24uc3ViamVjdHdvcmtmbG93LnYxLlN1YmplY3RQ'
    'YW5lVmlld1IFcGFuZXM=');

@$core.Deprecated('Use getSubjectPaneBundleRequestDescriptor instead')
const GetSubjectPaneBundleRequest$json = {
  '1': 'GetSubjectPaneBundleRequest',
  '2': [
    {'1': 'root_path', '3': 1, '4': 1, '5': 9, '10': 'rootPath'},
    {'1': 'subject_id', '3': 2, '4': 1, '5': 9, '10': 'subjectId'},
    {'1': 'phase', '3': 3, '4': 1, '5': 9, '10': 'phase'},
    {'1': 'client_session_id', '3': 4, '4': 1, '5': 9, '10': 'clientSessionId'},
  ],
};

/// Descriptor for `GetSubjectPaneBundleRequest`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List getSubjectPaneBundleRequestDescriptor = $convert.base64Decode(
    'ChtHZXRTdWJqZWN0UGFuZUJ1bmRsZVJlcXVlc3QSGwoJcm9vdF9wYXRoGAEgASgJUghyb290UG'
    'F0aBIdCgpzdWJqZWN0X2lkGAIgASgJUglzdWJqZWN0SWQSFAoFcGhhc2UYAyABKAlSBXBoYXNl'
    'EioKEWNsaWVudF9zZXNzaW9uX2lkGAQgASgJUg9jbGllbnRTZXNzaW9uSWQ=');

@$core.Deprecated('Use getSubjectPaneBundleResponseDescriptor instead')
const GetSubjectPaneBundleResponse$json = {
  '1': 'GetSubjectPaneBundleResponse',
  '2': [
    {'1': 'bundle', '3': 1, '4': 1, '5': 11, '6': '.realized.workstation.subjectworkflow.v1.SubjectPaneBundleView', '10': 'bundle'},
    {'1': 'trace_id', '3': 100, '4': 1, '5': 9, '10': 'traceId'},
    {'1': 'parent_id', '3': 101, '4': 1, '5': 9, '10': 'parentId'},
  ],
};

/// Descriptor for `GetSubjectPaneBundleResponse`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List getSubjectPaneBundleResponseDescriptor = $convert.base64Decode(
    'ChxHZXRTdWJqZWN0UGFuZUJ1bmRsZVJlc3BvbnNlElYKBmJ1bmRsZRgBIAEoCzI+LnJlYWxpem'
    'VkLndvcmtzdGF0aW9uLnN1YmplY3R3b3JrZmxvdy52MS5TdWJqZWN0UGFuZUJ1bmRsZVZpZXdS'
    'BmJ1bmRsZRIZCgh0cmFjZV9pZBhkIAEoCVIHdHJhY2VJZBIbCglwYXJlbnRfaWQYZSABKAlSCH'
    'BhcmVudElk');

@$core.Deprecated('Use subjectWorkflowSnapshotViewDescriptor instead')
const SubjectWorkflowSnapshotView$json = {
  '1': 'SubjectWorkflowSnapshotView',
  '2': [
    {'1': 'phase_view', '3': 1, '4': 1, '5': 11, '6': '.realized.workstation.subjectworkflow.v1.SubjectPhaseView', '10': 'phaseView'},
    {'1': 'control_bundle', '3': 2, '4': 1, '5': 11, '6': '.realized.workstation.subjectworkflow.v1.SubjectControlBundleView', '10': 'controlBundle'},
    {'1': 'pane_bundle', '3': 3, '4': 1, '5': 11, '6': '.realized.workstation.subjectworkflow.v1.SubjectPaneBundleView', '10': 'paneBundle'},
  ],
};

/// Descriptor for `SubjectWorkflowSnapshotView`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List subjectWorkflowSnapshotViewDescriptor = $convert.base64Decode(
    'ChtTdWJqZWN0V29ya2Zsb3dTbmFwc2hvdFZpZXcSWAoKcGhhc2VfdmlldxgBIAEoCzI5LnJlYW'
    'xpemVkLndvcmtzdGF0aW9uLnN1YmplY3R3b3JrZmxvdy52MS5TdWJqZWN0UGhhc2VWaWV3Uglw'
    'aGFzZVZpZXcSaAoOY29udHJvbF9idW5kbGUYAiABKAsyQS5yZWFsaXplZC53b3Jrc3RhdGlvbi'
    '5zdWJqZWN0d29ya2Zsb3cudjEuU3ViamVjdENvbnRyb2xCdW5kbGVWaWV3Ug1jb250cm9sQnVu'
    'ZGxlEl8KC3BhbmVfYnVuZGxlGAMgASgLMj4ucmVhbGl6ZWQud29ya3N0YXRpb24uc3ViamVjdH'
    'dvcmtmbG93LnYxLlN1YmplY3RQYW5lQnVuZGxlVmlld1IKcGFuZUJ1bmRsZQ==');

@$core.Deprecated('Use getSubjectWorkflowSnapshotRequestDescriptor instead')
const GetSubjectWorkflowSnapshotRequest$json = {
  '1': 'GetSubjectWorkflowSnapshotRequest',
  '2': [
    {'1': 'root_path', '3': 1, '4': 1, '5': 9, '10': 'rootPath'},
    {'1': 'subject_id', '3': 2, '4': 1, '5': 9, '10': 'subjectId'},
    {'1': 'phase', '3': 3, '4': 1, '5': 9, '10': 'phase'},
    {'1': 'projection_context', '3': 4, '4': 1, '5': 11, '6': '.realized.workstation.subjectworkflow.v1.SubjectPhaseProjectionContext', '10': 'projectionContext'},
    {'1': 'client_session_id', '3': 5, '4': 1, '5': 9, '10': 'clientSessionId'},
  ],
};

/// Descriptor for `GetSubjectWorkflowSnapshotRequest`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List getSubjectWorkflowSnapshotRequestDescriptor = $convert.base64Decode(
    'CiFHZXRTdWJqZWN0V29ya2Zsb3dTbmFwc2hvdFJlcXVlc3QSGwoJcm9vdF9wYXRoGAEgASgJUg'
    'hyb290UGF0aBIdCgpzdWJqZWN0X2lkGAIgASgJUglzdWJqZWN0SWQSFAoFcGhhc2UYAyABKAlS'
    'BXBoYXNlEnUKEnByb2plY3Rpb25fY29udGV4dBgEIAEoCzJGLnJlYWxpemVkLndvcmtzdGF0aW'
    '9uLnN1YmplY3R3b3JrZmxvdy52MS5TdWJqZWN0UGhhc2VQcm9qZWN0aW9uQ29udGV4dFIRcHJv'
    'amVjdGlvbkNvbnRleHQSKgoRY2xpZW50X3Nlc3Npb25faWQYBSABKAlSD2NsaWVudFNlc3Npb2'
    '5JZA==');

@$core.Deprecated('Use getSubjectWorkflowSnapshotResponseDescriptor instead')
const GetSubjectWorkflowSnapshotResponse$json = {
  '1': 'GetSubjectWorkflowSnapshotResponse',
  '2': [
    {'1': 'snapshot', '3': 1, '4': 1, '5': 11, '6': '.realized.workstation.subjectworkflow.v1.SubjectWorkflowSnapshotView', '10': 'snapshot'},
    {'1': 'trace_id', '3': 100, '4': 1, '5': 9, '10': 'traceId'},
    {'1': 'parent_id', '3': 101, '4': 1, '5': 9, '10': 'parentId'},
  ],
};

/// Descriptor for `GetSubjectWorkflowSnapshotResponse`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List getSubjectWorkflowSnapshotResponseDescriptor = $convert.base64Decode(
    'CiJHZXRTdWJqZWN0V29ya2Zsb3dTbmFwc2hvdFJlc3BvbnNlEmAKCHNuYXBzaG90GAEgASgLMk'
    'QucmVhbGl6ZWQud29ya3N0YXRpb24uc3ViamVjdHdvcmtmbG93LnYxLlN1YmplY3RXb3JrZmxv'
    'd1NuYXBzaG90Vmlld1IIc25hcHNob3QSGQoIdHJhY2VfaWQYZCABKAlSB3RyYWNlSWQSGwoJcG'
    'FyZW50X2lkGGUgASgJUghwYXJlbnRJZA==');

@$core.Deprecated('Use watchSubjectWorkflowRequestDescriptor instead')
const WatchSubjectWorkflowRequest$json = {
  '1': 'WatchSubjectWorkflowRequest',
  '2': [
    {'1': 'root_path', '3': 1, '4': 1, '5': 9, '10': 'rootPath'},
    {'1': 'subject_id', '3': 2, '4': 1, '5': 9, '10': 'subjectId'},
    {'1': 'phase', '3': 3, '4': 1, '5': 9, '10': 'phase'},
    {'1': 'projection_context', '3': 4, '4': 1, '5': 11, '6': '.realized.workstation.subjectworkflow.v1.SubjectPhaseProjectionContext', '10': 'projectionContext'},
    {'1': 'client_session_id', '3': 5, '4': 1, '5': 9, '10': 'clientSessionId'},
  ],
};

/// Descriptor for `WatchSubjectWorkflowRequest`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List watchSubjectWorkflowRequestDescriptor = $convert.base64Decode(
    'ChtXYXRjaFN1YmplY3RXb3JrZmxvd1JlcXVlc3QSGwoJcm9vdF9wYXRoGAEgASgJUghyb290UG'
    'F0aBIdCgpzdWJqZWN0X2lkGAIgASgJUglzdWJqZWN0SWQSFAoFcGhhc2UYAyABKAlSBXBoYXNl'
    'EnUKEnByb2plY3Rpb25fY29udGV4dBgEIAEoCzJGLnJlYWxpemVkLndvcmtzdGF0aW9uLnN1Ym'
    'plY3R3b3JrZmxvdy52MS5TdWJqZWN0UGhhc2VQcm9qZWN0aW9uQ29udGV4dFIRcHJvamVjdGlv'
    'bkNvbnRleHQSKgoRY2xpZW50X3Nlc3Npb25faWQYBSABKAlSD2NsaWVudFNlc3Npb25JZA==');

@$core.Deprecated('Use subjectWorkflowSnapshotUpdateDescriptor instead')
const SubjectWorkflowSnapshotUpdate$json = {
  '1': 'SubjectWorkflowSnapshotUpdate',
  '2': [
    {'1': 'event_kind', '3': 1, '4': 1, '5': 9, '10': 'eventKind'},
    {'1': 'snapshot', '3': 2, '4': 1, '5': 11, '6': '.realized.workstation.subjectworkflow.v1.SubjectWorkflowSnapshotView', '10': 'snapshot'},
    {'1': 'channel_key', '3': 3, '4': 1, '5': 9, '10': 'channelKey'},
    {'1': 'sequence', '3': 4, '4': 1, '5': 3, '10': 'sequence'},
    {'1': 'snapshot_version', '3': 5, '4': 1, '5': 9, '10': 'snapshotVersion'},
    {'1': 'progress_fingerprint', '3': 6, '4': 1, '5': 9, '10': 'progressFingerprint'},
    {'1': 'trace_id', '3': 100, '4': 1, '5': 9, '10': 'traceId'},
    {'1': 'parent_id', '3': 101, '4': 1, '5': 9, '10': 'parentId'},
  ],
};

/// Descriptor for `SubjectWorkflowSnapshotUpdate`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List subjectWorkflowSnapshotUpdateDescriptor = $convert.base64Decode(
    'Ch1TdWJqZWN0V29ya2Zsb3dTbmFwc2hvdFVwZGF0ZRIdCgpldmVudF9raW5kGAEgASgJUglldm'
    'VudEtpbmQSYAoIc25hcHNob3QYAiABKAsyRC5yZWFsaXplZC53b3Jrc3RhdGlvbi5zdWJqZWN0'
    'd29ya2Zsb3cudjEuU3ViamVjdFdvcmtmbG93U25hcHNob3RWaWV3UghzbmFwc2hvdBIfCgtjaG'
    'FubmVsX2tleRgDIAEoCVIKY2hhbm5lbEtleRIaCghzZXF1ZW5jZRgEIAEoA1IIc2VxdWVuY2US'
    'KQoQc25hcHNob3RfdmVyc2lvbhgFIAEoCVIPc25hcHNob3RWZXJzaW9uEjEKFHByb2dyZXNzX2'
    'ZpbmdlcnByaW50GAYgASgJUhNwcm9ncmVzc0ZpbmdlcnByaW50EhkKCHRyYWNlX2lkGGQgASgJ'
    'Ugd0cmFjZUlkEhsKCXBhcmVudF9pZBhlIAEoCVIIcGFyZW50SWQ=');

@$core.Deprecated('Use applySubjectActionRequestDescriptor instead')
const ApplySubjectActionRequest$json = {
  '1': 'ApplySubjectActionRequest',
  '2': [
    {'1': 'root_path', '3': 1, '4': 1, '5': 9, '10': 'rootPath'},
    {'1': 'subject_id', '3': 2, '4': 1, '5': 9, '10': 'subjectId'},
    {'1': 'phase', '3': 3, '4': 1, '5': 9, '10': 'phase'},
    {'1': 'action_key', '3': 4, '4': 1, '5': 9, '10': 'actionKey'},
    {'1': 'assistant_message_text', '3': 5, '4': 1, '5': 9, '10': 'assistantMessageText'},
    {'1': 'subject_title_override', '3': 6, '4': 1, '5': 9, '10': 'subjectTitleOverride'},
    {'1': 'import_staging', '3': 7, '4': 1, '5': 11, '6': '.realized.workstation.subjectworkflow.v1.SubjectImportStaging', '10': 'importStaging'},
    {'1': 'projection_context', '3': 8, '4': 1, '5': 11, '6': '.realized.workstation.subjectworkflow.v1.SubjectPhaseProjectionContext', '10': 'projectionContext'},
    {'1': 'client_session_id', '3': 9, '4': 1, '5': 9, '10': 'clientSessionId'},
  ],
};

/// Descriptor for `ApplySubjectActionRequest`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List applySubjectActionRequestDescriptor = $convert.base64Decode(
    'ChlBcHBseVN1YmplY3RBY3Rpb25SZXF1ZXN0EhsKCXJvb3RfcGF0aBgBIAEoCVIIcm9vdFBhdG'
    'gSHQoKc3ViamVjdF9pZBgCIAEoCVIJc3ViamVjdElkEhQKBXBoYXNlGAMgASgJUgVwaGFzZRId'
    'CgphY3Rpb25fa2V5GAQgASgJUglhY3Rpb25LZXkSNAoWYXNzaXN0YW50X21lc3NhZ2VfdGV4dB'
    'gFIAEoCVIUYXNzaXN0YW50TWVzc2FnZVRleHQSNAoWc3ViamVjdF90aXRsZV9vdmVycmlkZRgG'
    'IAEoCVIUc3ViamVjdFRpdGxlT3ZlcnJpZGUSZAoOaW1wb3J0X3N0YWdpbmcYByABKAsyPS5yZW'
    'FsaXplZC53b3Jrc3RhdGlvbi5zdWJqZWN0d29ya2Zsb3cudjEuU3ViamVjdEltcG9ydFN0YWdp'
    'bmdSDWltcG9ydFN0YWdpbmcSdQoScHJvamVjdGlvbl9jb250ZXh0GAggASgLMkYucmVhbGl6ZW'
    'Qud29ya3N0YXRpb24uc3ViamVjdHdvcmtmbG93LnYxLlN1YmplY3RQaGFzZVByb2plY3Rpb25D'
    'b250ZXh0UhFwcm9qZWN0aW9uQ29udGV4dBIqChFjbGllbnRfc2Vzc2lvbl9pZBgJIAEoCVIPY2'
    'xpZW50U2Vzc2lvbklk');

@$core.Deprecated('Use applySubjectActionResponseDescriptor instead')
const ApplySubjectActionResponse$json = {
  '1': 'ApplySubjectActionResponse',
  '2': [
    {'1': 'result', '3': 1, '4': 1, '5': 11, '6': '.realized.workstation.subjectworkflow.v1.SubjectActionResult', '10': 'result'},
    {'1': 'view', '3': 2, '4': 1, '5': 11, '6': '.realized.workstation.subjectworkflow.v1.SubjectPhaseView', '10': 'view'},
    {'1': 'trace_id', '3': 100, '4': 1, '5': 9, '10': 'traceId'},
    {'1': 'parent_id', '3': 101, '4': 1, '5': 9, '10': 'parentId'},
  ],
};

/// Descriptor for `ApplySubjectActionResponse`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List applySubjectActionResponseDescriptor = $convert.base64Decode(
    'ChpBcHBseVN1YmplY3RBY3Rpb25SZXNwb25zZRJUCgZyZXN1bHQYASABKAsyPC5yZWFsaXplZC'
    '53b3Jrc3RhdGlvbi5zdWJqZWN0d29ya2Zsb3cudjEuU3ViamVjdEFjdGlvblJlc3VsdFIGcmVz'
    'dWx0Ek0KBHZpZXcYAiABKAsyOS5yZWFsaXplZC53b3Jrc3RhdGlvbi5zdWJqZWN0d29ya2Zsb3'
    'cudjEuU3ViamVjdFBoYXNlVmlld1IEdmlldxIZCgh0cmFjZV9pZBhkIAEoCVIHdHJhY2VJZBIb'
    'CglwYXJlbnRfaWQYZSABKAlSCHBhcmVudElk');

@$core.Deprecated('Use getClientSubjectProgressRequestDescriptor instead')
const GetClientSubjectProgressRequest$json = {
  '1': 'GetClientSubjectProgressRequest',
  '2': [
    {'1': 'root_path', '3': 1, '4': 1, '5': 9, '10': 'rootPath'},
    {'1': 'subject_id', '3': 2, '4': 1, '5': 9, '10': 'subjectId'},
    {'1': 'client_session_id', '3': 3, '4': 1, '5': 9, '10': 'clientSessionId'},
  ],
};

/// Descriptor for `GetClientSubjectProgressRequest`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List getClientSubjectProgressRequestDescriptor = $convert.base64Decode(
    'Ch9HZXRDbGllbnRTdWJqZWN0UHJvZ3Jlc3NSZXF1ZXN0EhsKCXJvb3RfcGF0aBgBIAEoCVIIcm'
    '9vdFBhdGgSHQoKc3ViamVjdF9pZBgCIAEoCVIJc3ViamVjdElkEioKEWNsaWVudF9zZXNzaW9u'
    'X2lkGAMgASgJUg9jbGllbnRTZXNzaW9uSWQ=');

@$core.Deprecated('Use getClientSubjectProgressResponseDescriptor instead')
const GetClientSubjectProgressResponse$json = {
  '1': 'GetClientSubjectProgressResponse',
  '2': [
    {'1': 'progress_json', '3': 1, '4': 1, '5': 9, '10': 'progressJson'},
    {'1': 'trace_id', '3': 100, '4': 1, '5': 9, '10': 'traceId'},
    {'1': 'parent_id', '3': 101, '4': 1, '5': 9, '10': 'parentId'},
  ],
};

/// Descriptor for `GetClientSubjectProgressResponse`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List getClientSubjectProgressResponseDescriptor = $convert.base64Decode(
    'CiBHZXRDbGllbnRTdWJqZWN0UHJvZ3Jlc3NSZXNwb25zZRIjCg1wcm9ncmVzc19qc29uGAEgAS'
    'gJUgxwcm9ncmVzc0pzb24SGQoIdHJhY2VfaWQYZCABKAlSB3RyYWNlSWQSGwoJcGFyZW50X2lk'
    'GGUgASgJUghwYXJlbnRJZA==');

@$core.Deprecated('Use putClientSubjectProgressRequestDescriptor instead')
const PutClientSubjectProgressRequest$json = {
  '1': 'PutClientSubjectProgressRequest',
  '2': [
    {'1': 'root_path', '3': 1, '4': 1, '5': 9, '10': 'rootPath'},
    {'1': 'subject_id', '3': 2, '4': 1, '5': 9, '10': 'subjectId'},
    {'1': 'client_session_id', '3': 3, '4': 1, '5': 9, '10': 'clientSessionId'},
    {'1': 'progress_json', '3': 4, '4': 1, '5': 9, '10': 'progressJson'},
  ],
};

/// Descriptor for `PutClientSubjectProgressRequest`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List putClientSubjectProgressRequestDescriptor = $convert.base64Decode(
    'Ch9QdXRDbGllbnRTdWJqZWN0UHJvZ3Jlc3NSZXF1ZXN0EhsKCXJvb3RfcGF0aBgBIAEoCVIIcm'
    '9vdFBhdGgSHQoKc3ViamVjdF9pZBgCIAEoCVIJc3ViamVjdElkEioKEWNsaWVudF9zZXNzaW9u'
    'X2lkGAMgASgJUg9jbGllbnRTZXNzaW9uSWQSIwoNcHJvZ3Jlc3NfanNvbhgEIAEoCVIMcHJvZ3'
    'Jlc3NKc29u');

@$core.Deprecated('Use putClientSubjectProgressResponseDescriptor instead')
const PutClientSubjectProgressResponse$json = {
  '1': 'PutClientSubjectProgressResponse',
  '2': [
    {'1': 'progress_json', '3': 1, '4': 1, '5': 9, '10': 'progressJson'},
    {'1': 'trace_id', '3': 100, '4': 1, '5': 9, '10': 'traceId'},
    {'1': 'parent_id', '3': 101, '4': 1, '5': 9, '10': 'parentId'},
  ],
};

/// Descriptor for `PutClientSubjectProgressResponse`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List putClientSubjectProgressResponseDescriptor = $convert.base64Decode(
    'CiBQdXRDbGllbnRTdWJqZWN0UHJvZ3Jlc3NSZXNwb25zZRIjCg1wcm9ncmVzc19qc29uGAEgAS'
    'gJUgxwcm9ncmVzc0pzb24SGQoIdHJhY2VfaWQYZCABKAlSB3RyYWNlSWQSGwoJcGFyZW50X2lk'
    'GGUgASgJUghwYXJlbnRJZA==');

@$core.Deprecated('Use applySubjectInteractionRequestDescriptor instead')
const ApplySubjectInteractionRequest$json = {
  '1': 'ApplySubjectInteractionRequest',
  '2': [
    {'1': 'root_path', '3': 1, '4': 1, '5': 9, '10': 'rootPath'},
    {'1': 'subject_id', '3': 2, '4': 1, '5': 9, '10': 'subjectId'},
    {'1': 'phase', '3': 3, '4': 1, '5': 9, '10': 'phase'},
    {'1': 'client_session_id', '3': 4, '4': 1, '5': 9, '10': 'clientSessionId'},
    {'1': 'interaction_key', '3': 5, '4': 1, '5': 9, '10': 'interactionKey'},
    {'1': 'delta', '3': 6, '4': 1, '5': 5, '10': 'delta'},
    {'1': 'target_id', '3': 7, '4': 1, '5': 9, '10': 'targetId'},
    {'1': 'preview_only', '3': 8, '4': 1, '5': 8, '10': 'previewOnly'},
    {'1': 'projection_context', '3': 9, '4': 1, '5': 11, '6': '.realized.workstation.subjectworkflow.v1.SubjectPhaseProjectionContext', '10': 'projectionContext'},
  ],
};

/// Descriptor for `ApplySubjectInteractionRequest`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List applySubjectInteractionRequestDescriptor = $convert.base64Decode(
    'Ch5BcHBseVN1YmplY3RJbnRlcmFjdGlvblJlcXVlc3QSGwoJcm9vdF9wYXRoGAEgASgJUghyb2'
    '90UGF0aBIdCgpzdWJqZWN0X2lkGAIgASgJUglzdWJqZWN0SWQSFAoFcGhhc2UYAyABKAlSBXBo'
    'YXNlEioKEWNsaWVudF9zZXNzaW9uX2lkGAQgASgJUg9jbGllbnRTZXNzaW9uSWQSJwoPaW50ZX'
    'JhY3Rpb25fa2V5GAUgASgJUg5pbnRlcmFjdGlvbktleRIUCgVkZWx0YRgGIAEoBVIFZGVsdGES'
    'GwoJdGFyZ2V0X2lkGAcgASgJUgh0YXJnZXRJZBIhCgxwcmV2aWV3X29ubHkYCCABKAhSC3ByZX'
    'ZpZXdPbmx5EnUKEnByb2plY3Rpb25fY29udGV4dBgJIAEoCzJGLnJlYWxpemVkLndvcmtzdGF0'
    'aW9uLnN1YmplY3R3b3JrZmxvdy52MS5TdWJqZWN0UGhhc2VQcm9qZWN0aW9uQ29udGV4dFIRcH'
    'JvamVjdGlvbkNvbnRleHQ=');

@$core.Deprecated('Use applySubjectInteractionResponseDescriptor instead')
const ApplySubjectInteractionResponse$json = {
  '1': 'ApplySubjectInteractionResponse',
  '2': [
    {'1': 'snapshot', '3': 1, '4': 1, '5': 11, '6': '.realized.workstation.subjectworkflow.v1.SubjectWorkflowSnapshotView', '10': 'snapshot'},
    {'1': 'progress_json', '3': 2, '4': 1, '5': 9, '10': 'progressJson'},
    {'1': 'progress_fingerprint', '3': 3, '4': 1, '5': 9, '10': 'progressFingerprint'},
    {'1': 'trace_id', '3': 100, '4': 1, '5': 9, '10': 'traceId'},
    {'1': 'parent_id', '3': 101, '4': 1, '5': 9, '10': 'parentId'},
  ],
};

/// Descriptor for `ApplySubjectInteractionResponse`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List applySubjectInteractionResponseDescriptor = $convert.base64Decode(
    'Ch9BcHBseVN1YmplY3RJbnRlcmFjdGlvblJlc3BvbnNlEmAKCHNuYXBzaG90GAEgASgLMkQucm'
    'VhbGl6ZWQud29ya3N0YXRpb24uc3ViamVjdHdvcmtmbG93LnYxLlN1YmplY3RXb3JrZmxvd1Nu'
    'YXBzaG90Vmlld1IIc25hcHNob3QSIwoNcHJvZ3Jlc3NfanNvbhgCIAEoCVIMcHJvZ3Jlc3NKc2'
    '9uEjEKFHByb2dyZXNzX2ZpbmdlcnByaW50GAMgASgJUhNwcm9ncmVzc0ZpbmdlcnByaW50EhkK'
    'CHRyYWNlX2lkGGQgASgJUgd0cmFjZUlkEhsKCXBhcmVudF9pZBhlIAEoCVIIcGFyZW50SWQ=');

