//
//  Generated code. Do not modify.
//  source: workstation/grpc/definitions/workstation_assets.proto
//
// @dart = 2.12

// ignore_for_file: annotate_overrides, camel_case_types, comment_references
// ignore_for_file: constant_identifier_names, library_prefixes
// ignore_for_file: non_constant_identifier_names, prefer_final_fields
// ignore_for_file: unnecessary_import, unnecessary_this, unused_import

import 'dart:async' as $async;
import 'dart:core' as $core;

import 'package:grpc/service_api.dart' as $grpc;
import 'package:protobuf/protobuf.dart' as $pb;

import 'workstation_assets.pb.dart' as $0;

export 'workstation_assets.pb.dart';

@$pb.GrpcServiceName('workstation.WorkstationAssetService')
class WorkstationAssetServiceClient extends $grpc.Client {
  static final _$stageMarkdownUpload = $grpc.ClientMethod<$0.StageMarkdownUploadRequest, $0.StageMarkdownUploadResponse>(
      '/workstation.WorkstationAssetService/StageMarkdownUpload',
      ($0.StageMarkdownUploadRequest value) => value.writeToBuffer(),
      ($core.List<$core.int> value) => $0.StageMarkdownUploadResponse.fromBuffer(value));
  static final _$resolveArtifacts = $grpc.ClientMethod<$0.ResolveArtifactsRequest, $0.ResolveArtifactsResponse>(
      '/workstation.WorkstationAssetService/ResolveArtifacts',
      ($0.ResolveArtifactsRequest value) => value.writeToBuffer(),
      ($core.List<$core.int> value) => $0.ResolveArtifactsResponse.fromBuffer(value));

  WorkstationAssetServiceClient($grpc.ClientChannel channel,
      {$grpc.CallOptions? options,
      $core.Iterable<$grpc.ClientInterceptor>? interceptors})
      : super(channel, options: options,
        interceptors: interceptors);

  $grpc.ResponseFuture<$0.StageMarkdownUploadResponse> stageMarkdownUpload($0.StageMarkdownUploadRequest request, {$grpc.CallOptions? options}) {
    return $createUnaryCall(_$stageMarkdownUpload, request, options: options);
  }

  $grpc.ResponseFuture<$0.ResolveArtifactsResponse> resolveArtifacts($0.ResolveArtifactsRequest request, {$grpc.CallOptions? options}) {
    return $createUnaryCall(_$resolveArtifacts, request, options: options);
  }
}

@$pb.GrpcServiceName('workstation.WorkstationAssetService')
abstract class WorkstationAssetServiceBase extends $grpc.Service {
  $core.String get $name => 'workstation.WorkstationAssetService';

  WorkstationAssetServiceBase() {
    $addMethod($grpc.ServiceMethod<$0.StageMarkdownUploadRequest, $0.StageMarkdownUploadResponse>(
        'StageMarkdownUpload',
        stageMarkdownUpload_Pre,
        false,
        false,
        ($core.List<$core.int> value) => $0.StageMarkdownUploadRequest.fromBuffer(value),
        ($0.StageMarkdownUploadResponse value) => value.writeToBuffer()));
    $addMethod($grpc.ServiceMethod<$0.ResolveArtifactsRequest, $0.ResolveArtifactsResponse>(
        'ResolveArtifacts',
        resolveArtifacts_Pre,
        false,
        false,
        ($core.List<$core.int> value) => $0.ResolveArtifactsRequest.fromBuffer(value),
        ($0.ResolveArtifactsResponse value) => value.writeToBuffer()));
  }

  $async.Future<$0.StageMarkdownUploadResponse> stageMarkdownUpload_Pre($grpc.ServiceCall call, $async.Future<$0.StageMarkdownUploadRequest> request) async {
    return stageMarkdownUpload(call, await request);
  }

  $async.Future<$0.ResolveArtifactsResponse> resolveArtifacts_Pre($grpc.ServiceCall call, $async.Future<$0.ResolveArtifactsRequest> request) async {
    return resolveArtifacts(call, await request);
  }

  $async.Future<$0.StageMarkdownUploadResponse> stageMarkdownUpload($grpc.ServiceCall call, $0.StageMarkdownUploadRequest request);
  $async.Future<$0.ResolveArtifactsResponse> resolveArtifacts($grpc.ServiceCall call, $0.ResolveArtifactsRequest request);
}
