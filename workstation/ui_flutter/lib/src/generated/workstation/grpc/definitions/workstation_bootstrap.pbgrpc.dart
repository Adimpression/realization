//
//  Generated code. Do not modify.
//  source: workstation/grpc/definitions/workstation_bootstrap.proto
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

import 'workstation_bootstrap.pb.dart' as $1;

export 'workstation_bootstrap.pb.dart';

@$pb.GrpcServiceName('workstation.WorkstationBootstrapService')
class WorkstationBootstrapServiceClient extends $grpc.Client {
  static final _$listWorkstationRoots = $grpc.ClientMethod<$1.ListWorkstationRootsRequest, $1.ListWorkstationRootsResponse>(
      '/workstation.WorkstationBootstrapService/ListWorkstationRoots',
      ($1.ListWorkstationRootsRequest value) => value.writeToBuffer(),
      ($core.List<$core.int> value) => $1.ListWorkstationRootsResponse.fromBuffer(value));

  WorkstationBootstrapServiceClient($grpc.ClientChannel channel,
      {$grpc.CallOptions? options,
      $core.Iterable<$grpc.ClientInterceptor>? interceptors})
      : super(channel, options: options,
        interceptors: interceptors);

  $grpc.ResponseFuture<$1.ListWorkstationRootsResponse> listWorkstationRoots($1.ListWorkstationRootsRequest request, {$grpc.CallOptions? options}) {
    return $createUnaryCall(_$listWorkstationRoots, request, options: options);
  }
}

@$pb.GrpcServiceName('workstation.WorkstationBootstrapService')
abstract class WorkstationBootstrapServiceBase extends $grpc.Service {
  $core.String get $name => 'workstation.WorkstationBootstrapService';

  WorkstationBootstrapServiceBase() {
    $addMethod($grpc.ServiceMethod<$1.ListWorkstationRootsRequest, $1.ListWorkstationRootsResponse>(
        'ListWorkstationRoots',
        listWorkstationRoots_Pre,
        false,
        false,
        ($core.List<$core.int> value) => $1.ListWorkstationRootsRequest.fromBuffer(value),
        ($1.ListWorkstationRootsResponse value) => value.writeToBuffer()));
  }

  $async.Future<$1.ListWorkstationRootsResponse> listWorkstationRoots_Pre($grpc.ServiceCall call, $async.Future<$1.ListWorkstationRootsRequest> request) async {
    return listWorkstationRoots(call, await request);
  }

  $async.Future<$1.ListWorkstationRootsResponse> listWorkstationRoots($grpc.ServiceCall call, $1.ListWorkstationRootsRequest request);
}
