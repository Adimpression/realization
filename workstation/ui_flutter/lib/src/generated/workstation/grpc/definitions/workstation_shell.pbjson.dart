//
//  Generated code. Do not modify.
//  source: workstation/grpc/definitions/workstation_shell.proto
//
// @dart = 2.12

// ignore_for_file: annotate_overrides, camel_case_types, comment_references
// ignore_for_file: constant_identifier_names, library_prefixes
// ignore_for_file: non_constant_identifier_names, prefer_final_fields
// ignore_for_file: unnecessary_import, unnecessary_this, unused_import

import 'dart:convert' as $convert;
import 'dart:core' as $core;
import 'dart:typed_data' as $typed_data;

@$core.Deprecated('Use clientSessionRequestDescriptor instead')
const ClientSessionRequest$json = {
  '1': 'ClientSessionRequest',
  '2': [
    {'1': 'root_path', '3': 1, '4': 1, '5': 9, '10': 'rootPath'},
    {'1': 'client_session_id', '3': 2, '4': 1, '5': 9, '10': 'clientSessionId'},
    {'1': 'selected_subject_id', '3': 3, '4': 1, '5': 9, '10': 'selectedSubjectId'},
    {'1': 'selected_phase', '3': 4, '4': 1, '5': 9, '10': 'selectedPhase'},
  ],
};

/// Descriptor for `ClientSessionRequest`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List clientSessionRequestDescriptor = $convert.base64Decode(
    'ChRDbGllbnRTZXNzaW9uUmVxdWVzdBIbCglyb290X3BhdGgYASABKAlSCHJvb3RQYXRoEioKEW'
    'NsaWVudF9zZXNzaW9uX2lkGAIgASgJUg9jbGllbnRTZXNzaW9uSWQSLgoTc2VsZWN0ZWRfc3Vi'
    'amVjdF9pZBgDIAEoCVIRc2VsZWN0ZWRTdWJqZWN0SWQSJQoOc2VsZWN0ZWRfcGhhc2UYBCABKA'
    'lSDXNlbGVjdGVkUGhhc2U=');

@$core.Deprecated('Use clientSessionResponseDescriptor instead')
const ClientSessionResponse$json = {
  '1': 'ClientSessionResponse',
  '2': [
    {'1': 'client_session_id', '3': 1, '4': 1, '5': 9, '10': 'clientSessionId'},
    {'1': 'trace_id', '3': 100, '4': 1, '5': 9, '10': 'traceId'},
    {'1': 'parent_id', '3': 101, '4': 1, '5': 9, '10': 'parentId'},
  ],
};

/// Descriptor for `ClientSessionResponse`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List clientSessionResponseDescriptor = $convert.base64Decode(
    'ChVDbGllbnRTZXNzaW9uUmVzcG9uc2USKgoRY2xpZW50X3Nlc3Npb25faWQYASABKAlSD2NsaW'
    'VudFNlc3Npb25JZBIZCgh0cmFjZV9pZBhkIAEoCVIHdHJhY2VJZBIbCglwYXJlbnRfaWQYZSAB'
    'KAlSCHBhcmVudElk');

@$core.Deprecated('Use workstationChatMessageDescriptor instead')
const WorkstationChatMessage$json = {
  '1': 'WorkstationChatMessage',
  '2': [
    {'1': 'role', '3': 1, '4': 1, '5': 9, '10': 'role'},
    {'1': 'content', '3': 2, '4': 1, '5': 9, '10': 'content'},
    {'1': 'timestamp_epoch_ms', '3': 3, '4': 1, '5': 3, '10': 'timestampEpochMs'},
    {'1': 'message_id', '3': 4, '4': 1, '5': 9, '10': 'messageId'},
    {'1': 'turn_id', '3': 5, '4': 1, '5': 9, '10': 'turnId'},
    {'1': 'sequence', '3': 6, '4': 1, '5': 3, '10': 'sequence'},
  ],
};

/// Descriptor for `WorkstationChatMessage`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List workstationChatMessageDescriptor = $convert.base64Decode(
    'ChZXb3Jrc3RhdGlvbkNoYXRNZXNzYWdlEhIKBHJvbGUYASABKAlSBHJvbGUSGAoHY29udGVudB'
    'gCIAEoCVIHY29udGVudBIsChJ0aW1lc3RhbXBfZXBvY2hfbXMYAyABKANSEHRpbWVzdGFtcEVw'
    'b2NoTXMSHQoKbWVzc2FnZV9pZBgEIAEoCVIJbWVzc2FnZUlkEhcKB3R1cm5faWQYBSABKAlSBn'
    'R1cm5JZBIaCghzZXF1ZW5jZRgGIAEoA1IIc2VxdWVuY2U=');

@$core.Deprecated('Use chatSnapshotRequestDescriptor instead')
const ChatSnapshotRequest$json = {
  '1': 'ChatSnapshotRequest',
  '2': [
    {'1': 'root_path', '3': 1, '4': 1, '5': 9, '10': 'rootPath'},
    {'1': 'client_session_id', '3': 2, '4': 1, '5': 9, '10': 'clientSessionId'},
    {'1': 'limit', '3': 3, '4': 1, '5': 5, '10': 'limit'},
    {'1': 'selected_subject_id', '3': 4, '4': 1, '5': 9, '10': 'selectedSubjectId'},
    {'1': 'selected_phase', '3': 5, '4': 1, '5': 9, '10': 'selectedPhase'},
  ],
};

/// Descriptor for `ChatSnapshotRequest`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List chatSnapshotRequestDescriptor = $convert.base64Decode(
    'ChNDaGF0U25hcHNob3RSZXF1ZXN0EhsKCXJvb3RfcGF0aBgBIAEoCVIIcm9vdFBhdGgSKgoRY2'
    'xpZW50X3Nlc3Npb25faWQYAiABKAlSD2NsaWVudFNlc3Npb25JZBIUCgVsaW1pdBgDIAEoBVIF'
    'bGltaXQSLgoTc2VsZWN0ZWRfc3ViamVjdF9pZBgEIAEoCVIRc2VsZWN0ZWRTdWJqZWN0SWQSJQ'
    'oOc2VsZWN0ZWRfcGhhc2UYBSABKAlSDXNlbGVjdGVkUGhhc2U=');

@$core.Deprecated('Use chatSnapshotResponseDescriptor instead')
const ChatSnapshotResponse$json = {
  '1': 'ChatSnapshotResponse',
  '2': [
    {'1': 'messages', '3': 1, '4': 3, '5': 11, '6': '.workstation.WorkstationChatMessage', '10': 'messages'},
    {'1': 'session_status', '3': 2, '4': 1, '5': 9, '10': 'sessionStatus'},
    {'1': 'snapshot_version', '3': 3, '4': 1, '5': 9, '10': 'snapshotVersion'},
    {'1': 'progress_fingerprint', '3': 4, '4': 1, '5': 9, '10': 'progressFingerprint'},
    {'1': 'trace_id', '3': 100, '4': 1, '5': 9, '10': 'traceId'},
    {'1': 'parent_id', '3': 101, '4': 1, '5': 9, '10': 'parentId'},
  ],
};

/// Descriptor for `ChatSnapshotResponse`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List chatSnapshotResponseDescriptor = $convert.base64Decode(
    'ChRDaGF0U25hcHNob3RSZXNwb25zZRI/CghtZXNzYWdlcxgBIAMoCzIjLndvcmtzdGF0aW9uLl'
    'dvcmtzdGF0aW9uQ2hhdE1lc3NhZ2VSCG1lc3NhZ2VzEiUKDnNlc3Npb25fc3RhdHVzGAIgASgJ'
    'Ug1zZXNzaW9uU3RhdHVzEikKEHNuYXBzaG90X3ZlcnNpb24YAyABKAlSD3NuYXBzaG90VmVyc2'
    'lvbhIxChRwcm9ncmVzc19maW5nZXJwcmludBgEIAEoCVITcHJvZ3Jlc3NGaW5nZXJwcmludBIZ'
    'Cgh0cmFjZV9pZBhkIAEoCVIHdHJhY2VJZBIbCglwYXJlbnRfaWQYZSABKAlSCHBhcmVudElk');

@$core.Deprecated('Use prepareChatPromptTargetRequestDescriptor instead')
const PrepareChatPromptTargetRequest$json = {
  '1': 'PrepareChatPromptTargetRequest',
  '2': [
    {'1': 'root_path', '3': 1, '4': 1, '5': 9, '10': 'rootPath'},
    {'1': 'client_session_id', '3': 2, '4': 1, '5': 9, '10': 'clientSessionId'},
    {'1': 'prompt_text', '3': 3, '4': 1, '5': 9, '10': 'promptText'},
    {'1': 'selected_subject_id', '3': 4, '4': 1, '5': 9, '10': 'selectedSubjectId'},
    {'1': 'selected_phase', '3': 5, '4': 1, '5': 9, '10': 'selectedPhase'},
  ],
};

/// Descriptor for `PrepareChatPromptTargetRequest`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List prepareChatPromptTargetRequestDescriptor = $convert.base64Decode(
    'Ch5QcmVwYXJlQ2hhdFByb21wdFRhcmdldFJlcXVlc3QSGwoJcm9vdF9wYXRoGAEgASgJUghyb2'
    '90UGF0aBIqChFjbGllbnRfc2Vzc2lvbl9pZBgCIAEoCVIPY2xpZW50U2Vzc2lvbklkEh8KC3By'
    'b21wdF90ZXh0GAMgASgJUgpwcm9tcHRUZXh0Ei4KE3NlbGVjdGVkX3N1YmplY3RfaWQYBCABKA'
    'lSEXNlbGVjdGVkU3ViamVjdElkEiUKDnNlbGVjdGVkX3BoYXNlGAUgASgJUg1zZWxlY3RlZFBo'
    'YXNl');

@$core.Deprecated('Use prepareChatPromptTargetResponseDescriptor instead')
const PrepareChatPromptTargetResponse$json = {
  '1': 'PrepareChatPromptTargetResponse',
  '2': [
    {'1': 'kind', '3': 1, '4': 1, '5': 9, '10': 'kind'},
    {'1': 'prepared_prompt', '3': 2, '4': 1, '5': 9, '10': 'preparedPrompt'},
    {'1': 'shell_text', '3': 3, '4': 1, '5': 9, '10': 'shellText'},
    {'1': 'target_kind', '3': 4, '4': 1, '5': 9, '10': 'targetKind'},
    {'1': 'routing_metadata_json', '3': 5, '4': 1, '5': 9, '10': 'routingMetadataJson'},
    {'1': 'trace_id', '3': 100, '4': 1, '5': 9, '10': 'traceId'},
    {'1': 'parent_id', '3': 101, '4': 1, '5': 9, '10': 'parentId'},
  ],
};

/// Descriptor for `PrepareChatPromptTargetResponse`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List prepareChatPromptTargetResponseDescriptor = $convert.base64Decode(
    'Ch9QcmVwYXJlQ2hhdFByb21wdFRhcmdldFJlc3BvbnNlEhIKBGtpbmQYASABKAlSBGtpbmQSJw'
    'oPcHJlcGFyZWRfcHJvbXB0GAIgASgJUg5wcmVwYXJlZFByb21wdBIdCgpzaGVsbF90ZXh0GAMg'
    'ASgJUglzaGVsbFRleHQSHwoLdGFyZ2V0X2tpbmQYBCABKAlSCnRhcmdldEtpbmQSMgoVcm91dG'
    'luZ19tZXRhZGF0YV9qc29uGAUgASgJUhNyb3V0aW5nTWV0YWRhdGFKc29uEhkKCHRyYWNlX2lk'
    'GGQgASgJUgd0cmFjZUlkEhsKCXBhcmVudF9pZBhlIAEoCVIIcGFyZW50SWQ=');

@$core.Deprecated('Use submitChatInputRequestDescriptor instead')
const SubmitChatInputRequest$json = {
  '1': 'SubmitChatInputRequest',
  '2': [
    {'1': 'root_path', '3': 1, '4': 1, '5': 9, '10': 'rootPath'},
    {'1': 'client_session_id', '3': 2, '4': 1, '5': 9, '10': 'clientSessionId'},
    {'1': 'prompt_text', '3': 3, '4': 1, '5': 9, '10': 'promptText'},
    {'1': 'model', '3': 4, '4': 1, '5': 9, '10': 'model'},
    {'1': 'max_tool_rounds', '3': 5, '4': 1, '5': 5, '10': 'maxToolRounds'},
    {'1': 'force_llm_only', '3': 6, '4': 1, '5': 8, '10': 'forceLlmOnly'},
    {'1': 'interaction_mode', '3': 7, '4': 1, '5': 9, '10': 'interactionMode'},
    {'1': 'governed_treatment', '3': 8, '4': 1, '5': 9, '10': 'governedTreatment'},
    {'1': 'governed_parent_run_id', '3': 9, '4': 1, '5': 9, '10': 'governedParentRunId'},
    {'1': 'governed_llm_policy', '3': 10, '4': 1, '5': 9, '10': 'governedLlmPolicy'},
    {'1': 'governed_max_steps', '3': 11, '4': 1, '5': 5, '9': 0, '10': 'governedMaxSteps', '17': true},
  ],
  '8': [
    {'1': '_governed_max_steps'},
  ],
};

/// Descriptor for `SubmitChatInputRequest`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List submitChatInputRequestDescriptor = $convert.base64Decode(
    'ChZTdWJtaXRDaGF0SW5wdXRSZXF1ZXN0EhsKCXJvb3RfcGF0aBgBIAEoCVIIcm9vdFBhdGgSKg'
    'oRY2xpZW50X3Nlc3Npb25faWQYAiABKAlSD2NsaWVudFNlc3Npb25JZBIfCgtwcm9tcHRfdGV4'
    'dBgDIAEoCVIKcHJvbXB0VGV4dBIUCgVtb2RlbBgEIAEoCVIFbW9kZWwSJgoPbWF4X3Rvb2xfcm'
    '91bmRzGAUgASgFUg1tYXhUb29sUm91bmRzEiQKDmZvcmNlX2xsbV9vbmx5GAYgASgIUgxmb3Jj'
    'ZUxsbU9ubHkSKQoQaW50ZXJhY3Rpb25fbW9kZRgHIAEoCVIPaW50ZXJhY3Rpb25Nb2RlEi0KEm'
    'dvdmVybmVkX3RyZWF0bWVudBgIIAEoCVIRZ292ZXJuZWRUcmVhdG1lbnQSMwoWZ292ZXJuZWRf'
    'cGFyZW50X3J1bl9pZBgJIAEoCVITZ292ZXJuZWRQYXJlbnRSdW5JZBIuChNnb3Zlcm5lZF9sbG'
    '1fcG9saWN5GAogASgJUhFnb3Zlcm5lZExsbVBvbGljeRIxChJnb3Zlcm5lZF9tYXhfc3RlcHMY'
    'CyABKAVIAFIQZ292ZXJuZWRNYXhTdGVwc4gBAUIVChNfZ292ZXJuZWRfbWF4X3N0ZXBz');

@$core.Deprecated('Use submitChatInputResponseDescriptor instead')
const SubmitChatInputResponse$json = {
  '1': 'SubmitChatInputResponse',
  '2': [
    {'1': 'assistant_text', '3': 1, '4': 1, '5': 9, '10': 'assistantText'},
    {'1': 'messages', '3': 2, '4': 3, '5': 11, '6': '.workstation.WorkstationChatMessage', '10': 'messages'},
    {'1': 'fulfilled_by', '3': 3, '4': 1, '5': 9, '10': 'fulfilledBy'},
    {'1': 'rounds', '3': 4, '4': 1, '5': 5, '10': 'rounds'},
    {'1': 'tool_receipts_json', '3': 5, '4': 1, '5': 9, '10': 'toolReceiptsJson'},
    {'1': 'status_text', '3': 6, '4': 1, '5': 9, '10': 'statusText'},
    {'1': 'snapshot_version', '3': 7, '4': 1, '5': 9, '10': 'snapshotVersion'},
    {'1': 'progress_fingerprint', '3': 8, '4': 1, '5': 9, '10': 'progressFingerprint'},
    {'1': 'turn_id', '3': 9, '4': 1, '5': 9, '10': 'turnId'},
    {'1': 'run_id', '3': 10, '4': 1, '5': 9, '10': 'runId'},
    {'1': 'run_outcome', '3': 11, '4': 1, '5': 9, '10': 'runOutcome'},
    {'1': 'checkpoint_path', '3': 12, '4': 1, '5': 9, '10': 'checkpointPath'},
    {'1': 'trace_id', '3': 100, '4': 1, '5': 9, '10': 'traceId'},
    {'1': 'parent_id', '3': 101, '4': 1, '5': 9, '10': 'parentId'},
  ],
};

/// Descriptor for `SubmitChatInputResponse`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List submitChatInputResponseDescriptor = $convert.base64Decode(
    'ChdTdWJtaXRDaGF0SW5wdXRSZXNwb25zZRIlCg5hc3Npc3RhbnRfdGV4dBgBIAEoCVINYXNzaX'
    'N0YW50VGV4dBI/CghtZXNzYWdlcxgCIAMoCzIjLndvcmtzdGF0aW9uLldvcmtzdGF0aW9uQ2hh'
    'dE1lc3NhZ2VSCG1lc3NhZ2VzEiEKDGZ1bGZpbGxlZF9ieRgDIAEoCVILZnVsZmlsbGVkQnkSFg'
    'oGcm91bmRzGAQgASgFUgZyb3VuZHMSLAoSdG9vbF9yZWNlaXB0c19qc29uGAUgASgJUhB0b29s'
    'UmVjZWlwdHNKc29uEh8KC3N0YXR1c190ZXh0GAYgASgJUgpzdGF0dXNUZXh0EikKEHNuYXBzaG'
    '90X3ZlcnNpb24YByABKAlSD3NuYXBzaG90VmVyc2lvbhIxChRwcm9ncmVzc19maW5nZXJwcmlu'
    'dBgIIAEoCVITcHJvZ3Jlc3NGaW5nZXJwcmludBIXCgd0dXJuX2lkGAkgASgJUgZ0dXJuSWQSFQ'
    'oGcnVuX2lkGAogASgJUgVydW5JZBIfCgtydW5fb3V0Y29tZRgLIAEoCVIKcnVuT3V0Y29tZRIn'
    'Cg9jaGVja3BvaW50X3BhdGgYDCABKAlSDmNoZWNrcG9pbnRQYXRoEhkKCHRyYWNlX2lkGGQgAS'
    'gJUgd0cmFjZUlkEhsKCXBhcmVudF9pZBhlIAEoCVIIcGFyZW50SWQ=');

@$core.Deprecated('Use appendShellTurnRequestDescriptor instead')
const AppendShellTurnRequest$json = {
  '1': 'AppendShellTurnRequest',
  '2': [
    {'1': 'root_path', '3': 1, '4': 1, '5': 9, '10': 'rootPath'},
    {'1': 'client_session_id', '3': 2, '4': 1, '5': 9, '10': 'clientSessionId'},
    {'1': 'prompt_text', '3': 3, '4': 1, '5': 9, '10': 'promptText'},
    {'1': 'assistant_text', '3': 4, '4': 1, '5': 9, '10': 'assistantText'},
    {'1': 'assistant_role', '3': 5, '4': 1, '5': 9, '10': 'assistantRole'},
  ],
};

/// Descriptor for `AppendShellTurnRequest`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List appendShellTurnRequestDescriptor = $convert.base64Decode(
    'ChZBcHBlbmRTaGVsbFR1cm5SZXF1ZXN0EhsKCXJvb3RfcGF0aBgBIAEoCVIIcm9vdFBhdGgSKg'
    'oRY2xpZW50X3Nlc3Npb25faWQYAiABKAlSD2NsaWVudFNlc3Npb25JZBIfCgtwcm9tcHRfdGV4'
    'dBgDIAEoCVIKcHJvbXB0VGV4dBIlCg5hc3Npc3RhbnRfdGV4dBgEIAEoCVINYXNzaXN0YW50VG'
    'V4dBIlCg5hc3Npc3RhbnRfcm9sZRgFIAEoCVINYXNzaXN0YW50Um9sZQ==');

@$core.Deprecated('Use appendShellTurnResponseDescriptor instead')
const AppendShellTurnResponse$json = {
  '1': 'AppendShellTurnResponse',
  '2': [
    {'1': 'snapshot', '3': 1, '4': 1, '5': 11, '6': '.workstation.ChatSnapshotResponse', '10': 'snapshot'},
    {'1': 'trace_id', '3': 100, '4': 1, '5': 9, '10': 'traceId'},
    {'1': 'parent_id', '3': 101, '4': 1, '5': 9, '10': 'parentId'},
  ],
};

/// Descriptor for `AppendShellTurnResponse`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List appendShellTurnResponseDescriptor = $convert.base64Decode(
    'ChdBcHBlbmRTaGVsbFR1cm5SZXNwb25zZRI9CghzbmFwc2hvdBgBIAEoCzIhLndvcmtzdGF0aW'
    '9uLkNoYXRTbmFwc2hvdFJlc3BvbnNlUghzbmFwc2hvdBIZCgh0cmFjZV9pZBhkIAEoCVIHdHJh'
    'Y2VJZBIbCglwYXJlbnRfaWQYZSABKAlSCHBhcmVudElk');

@$core.Deprecated('Use activityViewRequestDescriptor instead')
const ActivityViewRequest$json = {
  '1': 'ActivityViewRequest',
  '2': [
    {'1': 'root_path', '3': 1, '4': 1, '5': 9, '10': 'rootPath'},
    {'1': 'client_session_id', '3': 2, '4': 1, '5': 9, '10': 'clientSessionId'},
    {'1': 'limit', '3': 3, '4': 1, '5': 5, '10': 'limit'},
  ],
};

/// Descriptor for `ActivityViewRequest`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List activityViewRequestDescriptor = $convert.base64Decode(
    'ChNBY3Rpdml0eVZpZXdSZXF1ZXN0EhsKCXJvb3RfcGF0aBgBIAEoCVIIcm9vdFBhdGgSKgoRY2'
    'xpZW50X3Nlc3Npb25faWQYAiABKAlSD2NsaWVudFNlc3Npb25JZBIUCgVsaW1pdBgDIAEoBVIF'
    'bGltaXQ=');

@$core.Deprecated('Use permissionsViewRequestDescriptor instead')
const PermissionsViewRequest$json = {
  '1': 'PermissionsViewRequest',
  '2': [
    {'1': 'root_path', '3': 1, '4': 1, '5': 9, '10': 'rootPath'},
    {'1': 'client_session_id', '3': 2, '4': 1, '5': 9, '10': 'clientSessionId'},
  ],
};

/// Descriptor for `PermissionsViewRequest`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List permissionsViewRequestDescriptor = $convert.base64Decode(
    'ChZQZXJtaXNzaW9uc1ZpZXdSZXF1ZXN0EhsKCXJvb3RfcGF0aBgBIAEoCVIIcm9vdFBhdGgSKg'
    'oRY2xpZW50X3Nlc3Npb25faWQYAiABKAlSD2NsaWVudFNlc3Npb25JZA==');

@$core.Deprecated('Use skillsViewRequestDescriptor instead')
const SkillsViewRequest$json = {
  '1': 'SkillsViewRequest',
  '2': [
    {'1': 'root_path', '3': 1, '4': 1, '5': 9, '10': 'rootPath'},
    {'1': 'client_session_id', '3': 2, '4': 1, '5': 9, '10': 'clientSessionId'},
    {'1': 'query', '3': 3, '4': 1, '5': 9, '10': 'query'},
  ],
};

/// Descriptor for `SkillsViewRequest`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List skillsViewRequestDescriptor = $convert.base64Decode(
    'ChFTa2lsbHNWaWV3UmVxdWVzdBIbCglyb290X3BhdGgYASABKAlSCHJvb3RQYXRoEioKEWNsaW'
    'VudF9zZXNzaW9uX2lkGAIgASgJUg9jbGllbnRTZXNzaW9uSWQSFAoFcXVlcnkYAyABKAlSBXF1'
    'ZXJ5');

@$core.Deprecated('Use shellTextViewDescriptor instead')
const ShellTextView$json = {
  '1': 'ShellTextView',
  '2': [
    {'1': 'text', '3': 1, '4': 1, '5': 9, '10': 'text'},
    {'1': 'snapshot_version', '3': 2, '4': 1, '5': 9, '10': 'snapshotVersion'},
    {'1': 'progress_fingerprint', '3': 3, '4': 1, '5': 9, '10': 'progressFingerprint'},
    {'1': 'trace_id', '3': 100, '4': 1, '5': 9, '10': 'traceId'},
    {'1': 'parent_id', '3': 101, '4': 1, '5': 9, '10': 'parentId'},
  ],
};

/// Descriptor for `ShellTextView`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List shellTextViewDescriptor = $convert.base64Decode(
    'Cg1TaGVsbFRleHRWaWV3EhIKBHRleHQYASABKAlSBHRleHQSKQoQc25hcHNob3RfdmVyc2lvbh'
    'gCIAEoCVIPc25hcHNob3RWZXJzaW9uEjEKFHByb2dyZXNzX2ZpbmdlcnByaW50GAMgASgJUhNw'
    'cm9ncmVzc0ZpbmdlcnByaW50EhkKCHRyYWNlX2lkGGQgASgJUgd0cmFjZUlkEhsKCXBhcmVudF'
    '9pZBhlIAEoCVIIcGFyZW50SWQ=');

@$core.Deprecated('Use watchWorkstationShellRequestDescriptor instead')
const WatchWorkstationShellRequest$json = {
  '1': 'WatchWorkstationShellRequest',
  '2': [
    {'1': 'root_path', '3': 1, '4': 1, '5': 9, '10': 'rootPath'},
    {'1': 'client_session_id', '3': 2, '4': 1, '5': 9, '10': 'clientSessionId'},
    {'1': 'last_seen_version', '3': 3, '4': 1, '5': 9, '10': 'lastSeenVersion'},
  ],
};

/// Descriptor for `WatchWorkstationShellRequest`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List watchWorkstationShellRequestDescriptor = $convert.base64Decode(
    'ChxXYXRjaFdvcmtzdGF0aW9uU2hlbGxSZXF1ZXN0EhsKCXJvb3RfcGF0aBgBIAEoCVIIcm9vdF'
    'BhdGgSKgoRY2xpZW50X3Nlc3Npb25faWQYAiABKAlSD2NsaWVudFNlc3Npb25JZBIqChFsYXN0'
    'X3NlZW5fdmVyc2lvbhgDIAEoCVIPbGFzdFNlZW5WZXJzaW9u');

@$core.Deprecated('Use workstationShellWatchEventDescriptor instead')
const WorkstationShellWatchEvent$json = {
  '1': 'WorkstationShellWatchEvent',
  '2': [
    {'1': 'event_kind', '3': 1, '4': 1, '5': 9, '10': 'eventKind'},
    {'1': 'channel_key', '3': 2, '4': 1, '5': 9, '10': 'channelKey'},
    {'1': 'sequence', '3': 3, '4': 1, '5': 3, '10': 'sequence'},
    {'1': 'snapshot_version', '3': 4, '4': 1, '5': 9, '10': 'snapshotVersion'},
    {'1': 'progress_fingerprint', '3': 5, '4': 1, '5': 9, '10': 'progressFingerprint'},
    {'1': 'trace_id', '3': 100, '4': 1, '5': 9, '10': 'traceId'},
    {'1': 'parent_id', '3': 101, '4': 1, '5': 9, '10': 'parentId'},
    {'1': 'chat_snapshot', '3': 10, '4': 1, '5': 11, '6': '.workstation.ChatSnapshotResponse', '9': 0, '10': 'chatSnapshot'},
    {'1': 'activity_view', '3': 11, '4': 1, '5': 11, '6': '.workstation.ShellTextView', '9': 0, '10': 'activityView'},
    {'1': 'permissions_view', '3': 12, '4': 1, '5': 11, '6': '.workstation.ShellTextView', '9': 0, '10': 'permissionsView'},
    {'1': 'skills_view', '3': 13, '4': 1, '5': 11, '6': '.workstation.ShellTextView', '9': 0, '10': 'skillsView'},
    {'1': 'status_view', '3': 14, '4': 1, '5': 11, '6': '.workstation.ShellTextView', '9': 0, '10': 'statusView'},
  ],
  '8': [
    {'1': 'payload'},
  ],
};

/// Descriptor for `WorkstationShellWatchEvent`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List workstationShellWatchEventDescriptor = $convert.base64Decode(
    'ChpXb3Jrc3RhdGlvblNoZWxsV2F0Y2hFdmVudBIdCgpldmVudF9raW5kGAEgASgJUglldmVudE'
    'tpbmQSHwoLY2hhbm5lbF9rZXkYAiABKAlSCmNoYW5uZWxLZXkSGgoIc2VxdWVuY2UYAyABKANS'
    'CHNlcXVlbmNlEikKEHNuYXBzaG90X3ZlcnNpb24YBCABKAlSD3NuYXBzaG90VmVyc2lvbhIxCh'
    'Rwcm9ncmVzc19maW5nZXJwcmludBgFIAEoCVITcHJvZ3Jlc3NGaW5nZXJwcmludBIZCgh0cmFj'
    'ZV9pZBhkIAEoCVIHdHJhY2VJZBIbCglwYXJlbnRfaWQYZSABKAlSCHBhcmVudElkEkgKDWNoYX'
    'Rfc25hcHNob3QYCiABKAsyIS53b3Jrc3RhdGlvbi5DaGF0U25hcHNob3RSZXNwb25zZUgAUgxj'
    'aGF0U25hcHNob3QSQQoNYWN0aXZpdHlfdmlldxgLIAEoCzIaLndvcmtzdGF0aW9uLlNoZWxsVG'
    'V4dFZpZXdIAFIMYWN0aXZpdHlWaWV3EkcKEHBlcm1pc3Npb25zX3ZpZXcYDCABKAsyGi53b3Jr'
    'c3RhdGlvbi5TaGVsbFRleHRWaWV3SABSD3Blcm1pc3Npb25zVmlldxI9Cgtza2lsbHNfdmlldx'
    'gNIAEoCzIaLndvcmtzdGF0aW9uLlNoZWxsVGV4dFZpZXdIAFIKc2tpbGxzVmlldxI9CgtzdGF0'
    'dXNfdmlldxgOIAEoCzIaLndvcmtzdGF0aW9uLlNoZWxsVGV4dFZpZXdIAFIKc3RhdHVzVmlld0'
    'IJCgdwYXlsb2Fk');

