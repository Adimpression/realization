//
//  Generated code. Do not modify.
//  source: workstation/grpc/definitions/workstation_assets.proto
//
// @dart = 2.12

// ignore_for_file: annotate_overrides, camel_case_types, comment_references
// ignore_for_file: constant_identifier_names, library_prefixes
// ignore_for_file: non_constant_identifier_names, prefer_final_fields
// ignore_for_file: unnecessary_import, unnecessary_this, unused_import

import 'dart:convert' as $convert;
import 'dart:core' as $core;
import 'dart:typed_data' as $typed_data;

@$core.Deprecated('Use artifactRefDescriptor instead')
const ArtifactRef$json = {
  '1': 'ArtifactRef',
  '2': [
    {'1': 'label', '3': 1, '4': 1, '5': 9, '10': 'label'},
    {'1': 'server_path', '3': 2, '4': 1, '5': 9, '10': 'serverPath'},
    {'1': 'mime_type', '3': 3, '4': 1, '5': 9, '10': 'mimeType'},
    {'1': 'download_url', '3': 4, '4': 1, '5': 9, '10': 'downloadUrl'},
    {'1': 'can_open_locally', '3': 5, '4': 1, '5': 8, '10': 'canOpenLocally'},
  ],
};

/// Descriptor for `ArtifactRef`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List artifactRefDescriptor = $convert.base64Decode(
    'CgtBcnRpZmFjdFJlZhIUCgVsYWJlbBgBIAEoCVIFbGFiZWwSHwoLc2VydmVyX3BhdGgYAiABKA'
    'lSCnNlcnZlclBhdGgSGwoJbWltZV90eXBlGAMgASgJUghtaW1lVHlwZRIhCgxkb3dubG9hZF91'
    'cmwYBCABKAlSC2Rvd25sb2FkVXJsEigKEGNhbl9vcGVuX2xvY2FsbHkYBSABKAhSDmNhbk9wZW'
    '5Mb2NhbGx5');

@$core.Deprecated('Use stageMarkdownUploadRequestDescriptor instead')
const StageMarkdownUploadRequest$json = {
  '1': 'StageMarkdownUploadRequest',
  '2': [
    {'1': 'root_path', '3': 1, '4': 1, '5': 9, '10': 'rootPath'},
    {'1': 'client_session_id', '3': 2, '4': 1, '5': 9, '10': 'clientSessionId'},
    {'1': 'filename', '3': 3, '4': 1, '5': 9, '10': 'filename'},
    {'1': 'content', '3': 4, '4': 1, '5': 12, '10': 'content'},
  ],
};

/// Descriptor for `StageMarkdownUploadRequest`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List stageMarkdownUploadRequestDescriptor = $convert.base64Decode(
    'ChpTdGFnZU1hcmtkb3duVXBsb2FkUmVxdWVzdBIbCglyb290X3BhdGgYASABKAlSCHJvb3RQYX'
    'RoEioKEWNsaWVudF9zZXNzaW9uX2lkGAIgASgJUg9jbGllbnRTZXNzaW9uSWQSGgoIZmlsZW5h'
    'bWUYAyABKAlSCGZpbGVuYW1lEhgKB2NvbnRlbnQYBCABKAxSB2NvbnRlbnQ=');

@$core.Deprecated('Use stageMarkdownUploadResponseDescriptor instead')
const StageMarkdownUploadResponse$json = {
  '1': 'StageMarkdownUploadResponse',
  '2': [
    {'1': 'staged_path', '3': 1, '4': 1, '5': 9, '10': 'stagedPath'},
    {'1': 'display_name', '3': 2, '4': 1, '5': 9, '10': 'displayName'},
    {'1': 'sha256', '3': 3, '4': 1, '5': 9, '10': 'sha256'},
    {'1': 'trace_id', '3': 100, '4': 1, '5': 9, '10': 'traceId'},
    {'1': 'parent_id', '3': 101, '4': 1, '5': 9, '10': 'parentId'},
  ],
};

/// Descriptor for `StageMarkdownUploadResponse`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List stageMarkdownUploadResponseDescriptor = $convert.base64Decode(
    'ChtTdGFnZU1hcmtkb3duVXBsb2FkUmVzcG9uc2USHwoLc3RhZ2VkX3BhdGgYASABKAlSCnN0YW'
    'dlZFBhdGgSIQoMZGlzcGxheV9uYW1lGAIgASgJUgtkaXNwbGF5TmFtZRIWCgZzaGEyNTYYAyAB'
    'KAlSBnNoYTI1NhIZCgh0cmFjZV9pZBhkIAEoCVIHdHJhY2VJZBIbCglwYXJlbnRfaWQYZSABKA'
    'lSCHBhcmVudElk');

@$core.Deprecated('Use resolveArtifactsRequestDescriptor instead')
const ResolveArtifactsRequest$json = {
  '1': 'ResolveArtifactsRequest',
  '2': [
    {'1': 'root_path', '3': 1, '4': 1, '5': 9, '10': 'rootPath'},
    {'1': 'client_session_id', '3': 2, '4': 1, '5': 9, '10': 'clientSessionId'},
    {'1': 'server_paths', '3': 3, '4': 3, '5': 9, '10': 'serverPaths'},
  ],
};

/// Descriptor for `ResolveArtifactsRequest`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List resolveArtifactsRequestDescriptor = $convert.base64Decode(
    'ChdSZXNvbHZlQXJ0aWZhY3RzUmVxdWVzdBIbCglyb290X3BhdGgYASABKAlSCHJvb3RQYXRoEi'
    'oKEWNsaWVudF9zZXNzaW9uX2lkGAIgASgJUg9jbGllbnRTZXNzaW9uSWQSIQoMc2VydmVyX3Bh'
    'dGhzGAMgAygJUgtzZXJ2ZXJQYXRocw==');

@$core.Deprecated('Use resolveArtifactsResponseDescriptor instead')
const ResolveArtifactsResponse$json = {
  '1': 'ResolveArtifactsResponse',
  '2': [
    {'1': 'artifacts', '3': 1, '4': 3, '5': 11, '6': '.workstation.ArtifactRef', '10': 'artifacts'},
    {'1': 'trace_id', '3': 100, '4': 1, '5': 9, '10': 'traceId'},
    {'1': 'parent_id', '3': 101, '4': 1, '5': 9, '10': 'parentId'},
  ],
};

/// Descriptor for `ResolveArtifactsResponse`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List resolveArtifactsResponseDescriptor = $convert.base64Decode(
    'ChhSZXNvbHZlQXJ0aWZhY3RzUmVzcG9uc2USNgoJYXJ0aWZhY3RzGAEgAygLMhgud29ya3N0YX'
    'Rpb24uQXJ0aWZhY3RSZWZSCWFydGlmYWN0cxIZCgh0cmFjZV9pZBhkIAEoCVIHdHJhY2VJZBIb'
    'CglwYXJlbnRfaWQYZSABKAlSCHBhcmVudElk');

