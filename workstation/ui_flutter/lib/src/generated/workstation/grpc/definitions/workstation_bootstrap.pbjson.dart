//
//  Generated code. Do not modify.
//  source: workstation/grpc/definitions/workstation_bootstrap.proto
//
// @dart = 2.12

// ignore_for_file: annotate_overrides, camel_case_types, comment_references
// ignore_for_file: constant_identifier_names, library_prefixes
// ignore_for_file: non_constant_identifier_names, prefer_final_fields
// ignore_for_file: unnecessary_import, unnecessary_this, unused_import

import 'dart:convert' as $convert;
import 'dart:core' as $core;
import 'dart:typed_data' as $typed_data;

@$core.Deprecated('Use workstationRootDescriptorDescriptor instead')
const WorkstationRootDescriptor$json = {
  '1': 'WorkstationRootDescriptor',
  '2': [
    {'1': 'root_id', '3': 1, '4': 1, '5': 9, '10': 'rootId'},
    {'1': 'label', '3': 2, '4': 1, '5': 9, '10': 'label'},
    {'1': 'root_path', '3': 3, '4': 1, '5': 9, '10': 'rootPath'},
    {'1': 'workspace_name', '3': 4, '4': 1, '5': 9, '10': 'workspaceName'},
    {'1': 'is_default', '3': 5, '4': 1, '5': 8, '10': 'isDefault'},
  ],
};

/// Descriptor for `WorkstationRootDescriptor`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List workstationRootDescriptorDescriptor = $convert.base64Decode(
    'ChlXb3Jrc3RhdGlvblJvb3REZXNjcmlwdG9yEhcKB3Jvb3RfaWQYASABKAlSBnJvb3RJZBIUCg'
    'VsYWJlbBgCIAEoCVIFbGFiZWwSGwoJcm9vdF9wYXRoGAMgASgJUghyb290UGF0aBIlCg53b3Jr'
    'c3BhY2VfbmFtZRgEIAEoCVINd29ya3NwYWNlTmFtZRIdCgppc19kZWZhdWx0GAUgASgIUglpc0'
    'RlZmF1bHQ=');

@$core.Deprecated('Use listWorkstationRootsRequestDescriptor instead')
const ListWorkstationRootsRequest$json = {
  '1': 'ListWorkstationRootsRequest',
};

/// Descriptor for `ListWorkstationRootsRequest`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List listWorkstationRootsRequestDescriptor = $convert.base64Decode(
    'ChtMaXN0V29ya3N0YXRpb25Sb290c1JlcXVlc3Q=');

@$core.Deprecated('Use listWorkstationRootsResponseDescriptor instead')
const ListWorkstationRootsResponse$json = {
  '1': 'ListWorkstationRootsResponse',
  '2': [
    {'1': 'roots', '3': 1, '4': 3, '5': 11, '6': '.workstation.WorkstationRootDescriptor', '10': 'roots'},
    {'1': 'trace_id', '3': 100, '4': 1, '5': 9, '10': 'traceId'},
    {'1': 'parent_id', '3': 101, '4': 1, '5': 9, '10': 'parentId'},
  ],
};

/// Descriptor for `ListWorkstationRootsResponse`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List listWorkstationRootsResponseDescriptor = $convert.base64Decode(
    'ChxMaXN0V29ya3N0YXRpb25Sb290c1Jlc3BvbnNlEjwKBXJvb3RzGAEgAygLMiYud29ya3N0YX'
    'Rpb24uV29ya3N0YXRpb25Sb290RGVzY3JpcHRvclIFcm9vdHMSGQoIdHJhY2VfaWQYZCABKAlS'
    'B3RyYWNlSWQSGwoJcGFyZW50X2lkGGUgASgJUghwYXJlbnRJZA==');

