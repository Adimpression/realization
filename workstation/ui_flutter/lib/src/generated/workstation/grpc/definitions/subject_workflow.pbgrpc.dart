//
//  Generated code. Do not modify.
//  source: workstation/grpc/definitions/subject_workflow.proto
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

import 'subject_workflow.pb.dart' as $2;

export 'subject_workflow.pb.dart';

@$pb.GrpcServiceName('realized.workstation.subjectworkflow.v1.SubjectWorkflowService')
class SubjectWorkflowServiceClient extends $grpc.Client {
  static final _$listSubjects = $grpc.ClientMethod<$2.ListSubjectsRequest, $2.ListSubjectsResponse>(
      '/realized.workstation.subjectworkflow.v1.SubjectWorkflowService/ListSubjects',
      ($2.ListSubjectsRequest value) => value.writeToBuffer(),
      ($core.List<$core.int> value) => $2.ListSubjectsResponse.fromBuffer(value));
  static final _$getSubjectPhaseView = $grpc.ClientMethod<$2.GetSubjectPhaseViewRequest, $2.GetSubjectPhaseViewResponse>(
      '/realized.workstation.subjectworkflow.v1.SubjectWorkflowService/GetSubjectPhaseView',
      ($2.GetSubjectPhaseViewRequest value) => value.writeToBuffer(),
      ($core.List<$core.int> value) => $2.GetSubjectPhaseViewResponse.fromBuffer(value));
  static final _$getSubjectControlBundle = $grpc.ClientMethod<$2.GetSubjectControlBundleRequest, $2.GetSubjectControlBundleResponse>(
      '/realized.workstation.subjectworkflow.v1.SubjectWorkflowService/GetSubjectControlBundle',
      ($2.GetSubjectControlBundleRequest value) => value.writeToBuffer(),
      ($core.List<$core.int> value) => $2.GetSubjectControlBundleResponse.fromBuffer(value));
  static final _$getSubjectPaneBundle = $grpc.ClientMethod<$2.GetSubjectPaneBundleRequest, $2.GetSubjectPaneBundleResponse>(
      '/realized.workstation.subjectworkflow.v1.SubjectWorkflowService/GetSubjectPaneBundle',
      ($2.GetSubjectPaneBundleRequest value) => value.writeToBuffer(),
      ($core.List<$core.int> value) => $2.GetSubjectPaneBundleResponse.fromBuffer(value));
  static final _$getSubjectWorkflowSnapshot = $grpc.ClientMethod<$2.GetSubjectWorkflowSnapshotRequest, $2.GetSubjectWorkflowSnapshotResponse>(
      '/realized.workstation.subjectworkflow.v1.SubjectWorkflowService/GetSubjectWorkflowSnapshot',
      ($2.GetSubjectWorkflowSnapshotRequest value) => value.writeToBuffer(),
      ($core.List<$core.int> value) => $2.GetSubjectWorkflowSnapshotResponse.fromBuffer(value));
  static final _$watchSubjectWorkflow = $grpc.ClientMethod<$2.WatchSubjectWorkflowRequest, $2.SubjectWorkflowSnapshotUpdate>(
      '/realized.workstation.subjectworkflow.v1.SubjectWorkflowService/WatchSubjectWorkflow',
      ($2.WatchSubjectWorkflowRequest value) => value.writeToBuffer(),
      ($core.List<$core.int> value) => $2.SubjectWorkflowSnapshotUpdate.fromBuffer(value));
  static final _$applySubjectAction = $grpc.ClientMethod<$2.ApplySubjectActionRequest, $2.ApplySubjectActionResponse>(
      '/realized.workstation.subjectworkflow.v1.SubjectWorkflowService/ApplySubjectAction',
      ($2.ApplySubjectActionRequest value) => value.writeToBuffer(),
      ($core.List<$core.int> value) => $2.ApplySubjectActionResponse.fromBuffer(value));
  static final _$getClientSubjectProgress = $grpc.ClientMethod<$2.GetClientSubjectProgressRequest, $2.GetClientSubjectProgressResponse>(
      '/realized.workstation.subjectworkflow.v1.SubjectWorkflowService/GetClientSubjectProgress',
      ($2.GetClientSubjectProgressRequest value) => value.writeToBuffer(),
      ($core.List<$core.int> value) => $2.GetClientSubjectProgressResponse.fromBuffer(value));
  static final _$putClientSubjectProgress = $grpc.ClientMethod<$2.PutClientSubjectProgressRequest, $2.PutClientSubjectProgressResponse>(
      '/realized.workstation.subjectworkflow.v1.SubjectWorkflowService/PutClientSubjectProgress',
      ($2.PutClientSubjectProgressRequest value) => value.writeToBuffer(),
      ($core.List<$core.int> value) => $2.PutClientSubjectProgressResponse.fromBuffer(value));
  static final _$applySubjectInteraction = $grpc.ClientMethod<$2.ApplySubjectInteractionRequest, $2.ApplySubjectInteractionResponse>(
      '/realized.workstation.subjectworkflow.v1.SubjectWorkflowService/ApplySubjectInteraction',
      ($2.ApplySubjectInteractionRequest value) => value.writeToBuffer(),
      ($core.List<$core.int> value) => $2.ApplySubjectInteractionResponse.fromBuffer(value));

  SubjectWorkflowServiceClient($grpc.ClientChannel channel,
      {$grpc.CallOptions? options,
      $core.Iterable<$grpc.ClientInterceptor>? interceptors})
      : super(channel, options: options,
        interceptors: interceptors);

  $grpc.ResponseFuture<$2.ListSubjectsResponse> listSubjects($2.ListSubjectsRequest request, {$grpc.CallOptions? options}) {
    return $createUnaryCall(_$listSubjects, request, options: options);
  }

  $grpc.ResponseFuture<$2.GetSubjectPhaseViewResponse> getSubjectPhaseView($2.GetSubjectPhaseViewRequest request, {$grpc.CallOptions? options}) {
    return $createUnaryCall(_$getSubjectPhaseView, request, options: options);
  }

  $grpc.ResponseFuture<$2.GetSubjectControlBundleResponse> getSubjectControlBundle($2.GetSubjectControlBundleRequest request, {$grpc.CallOptions? options}) {
    return $createUnaryCall(_$getSubjectControlBundle, request, options: options);
  }

  $grpc.ResponseFuture<$2.GetSubjectPaneBundleResponse> getSubjectPaneBundle($2.GetSubjectPaneBundleRequest request, {$grpc.CallOptions? options}) {
    return $createUnaryCall(_$getSubjectPaneBundle, request, options: options);
  }

  $grpc.ResponseFuture<$2.GetSubjectWorkflowSnapshotResponse> getSubjectWorkflowSnapshot($2.GetSubjectWorkflowSnapshotRequest request, {$grpc.CallOptions? options}) {
    return $createUnaryCall(_$getSubjectWorkflowSnapshot, request, options: options);
  }

  $grpc.ResponseStream<$2.SubjectWorkflowSnapshotUpdate> watchSubjectWorkflow($2.WatchSubjectWorkflowRequest request, {$grpc.CallOptions? options}) {
    return $createStreamingCall(_$watchSubjectWorkflow, $async.Stream.fromIterable([request]), options: options);
  }

  $grpc.ResponseFuture<$2.ApplySubjectActionResponse> applySubjectAction($2.ApplySubjectActionRequest request, {$grpc.CallOptions? options}) {
    return $createUnaryCall(_$applySubjectAction, request, options: options);
  }

  $grpc.ResponseFuture<$2.GetClientSubjectProgressResponse> getClientSubjectProgress($2.GetClientSubjectProgressRequest request, {$grpc.CallOptions? options}) {
    return $createUnaryCall(_$getClientSubjectProgress, request, options: options);
  }

  $grpc.ResponseFuture<$2.PutClientSubjectProgressResponse> putClientSubjectProgress($2.PutClientSubjectProgressRequest request, {$grpc.CallOptions? options}) {
    return $createUnaryCall(_$putClientSubjectProgress, request, options: options);
  }

  $grpc.ResponseFuture<$2.ApplySubjectInteractionResponse> applySubjectInteraction($2.ApplySubjectInteractionRequest request, {$grpc.CallOptions? options}) {
    return $createUnaryCall(_$applySubjectInteraction, request, options: options);
  }
}

@$pb.GrpcServiceName('realized.workstation.subjectworkflow.v1.SubjectWorkflowService')
abstract class SubjectWorkflowServiceBase extends $grpc.Service {
  $core.String get $name => 'realized.workstation.subjectworkflow.v1.SubjectWorkflowService';

  SubjectWorkflowServiceBase() {
    $addMethod($grpc.ServiceMethod<$2.ListSubjectsRequest, $2.ListSubjectsResponse>(
        'ListSubjects',
        listSubjects_Pre,
        false,
        false,
        ($core.List<$core.int> value) => $2.ListSubjectsRequest.fromBuffer(value),
        ($2.ListSubjectsResponse value) => value.writeToBuffer()));
    $addMethod($grpc.ServiceMethod<$2.GetSubjectPhaseViewRequest, $2.GetSubjectPhaseViewResponse>(
        'GetSubjectPhaseView',
        getSubjectPhaseView_Pre,
        false,
        false,
        ($core.List<$core.int> value) => $2.GetSubjectPhaseViewRequest.fromBuffer(value),
        ($2.GetSubjectPhaseViewResponse value) => value.writeToBuffer()));
    $addMethod($grpc.ServiceMethod<$2.GetSubjectControlBundleRequest, $2.GetSubjectControlBundleResponse>(
        'GetSubjectControlBundle',
        getSubjectControlBundle_Pre,
        false,
        false,
        ($core.List<$core.int> value) => $2.GetSubjectControlBundleRequest.fromBuffer(value),
        ($2.GetSubjectControlBundleResponse value) => value.writeToBuffer()));
    $addMethod($grpc.ServiceMethod<$2.GetSubjectPaneBundleRequest, $2.GetSubjectPaneBundleResponse>(
        'GetSubjectPaneBundle',
        getSubjectPaneBundle_Pre,
        false,
        false,
        ($core.List<$core.int> value) => $2.GetSubjectPaneBundleRequest.fromBuffer(value),
        ($2.GetSubjectPaneBundleResponse value) => value.writeToBuffer()));
    $addMethod($grpc.ServiceMethod<$2.GetSubjectWorkflowSnapshotRequest, $2.GetSubjectWorkflowSnapshotResponse>(
        'GetSubjectWorkflowSnapshot',
        getSubjectWorkflowSnapshot_Pre,
        false,
        false,
        ($core.List<$core.int> value) => $2.GetSubjectWorkflowSnapshotRequest.fromBuffer(value),
        ($2.GetSubjectWorkflowSnapshotResponse value) => value.writeToBuffer()));
    $addMethod($grpc.ServiceMethod<$2.WatchSubjectWorkflowRequest, $2.SubjectWorkflowSnapshotUpdate>(
        'WatchSubjectWorkflow',
        watchSubjectWorkflow_Pre,
        false,
        true,
        ($core.List<$core.int> value) => $2.WatchSubjectWorkflowRequest.fromBuffer(value),
        ($2.SubjectWorkflowSnapshotUpdate value) => value.writeToBuffer()));
    $addMethod($grpc.ServiceMethod<$2.ApplySubjectActionRequest, $2.ApplySubjectActionResponse>(
        'ApplySubjectAction',
        applySubjectAction_Pre,
        false,
        false,
        ($core.List<$core.int> value) => $2.ApplySubjectActionRequest.fromBuffer(value),
        ($2.ApplySubjectActionResponse value) => value.writeToBuffer()));
    $addMethod($grpc.ServiceMethod<$2.GetClientSubjectProgressRequest, $2.GetClientSubjectProgressResponse>(
        'GetClientSubjectProgress',
        getClientSubjectProgress_Pre,
        false,
        false,
        ($core.List<$core.int> value) => $2.GetClientSubjectProgressRequest.fromBuffer(value),
        ($2.GetClientSubjectProgressResponse value) => value.writeToBuffer()));
    $addMethod($grpc.ServiceMethod<$2.PutClientSubjectProgressRequest, $2.PutClientSubjectProgressResponse>(
        'PutClientSubjectProgress',
        putClientSubjectProgress_Pre,
        false,
        false,
        ($core.List<$core.int> value) => $2.PutClientSubjectProgressRequest.fromBuffer(value),
        ($2.PutClientSubjectProgressResponse value) => value.writeToBuffer()));
    $addMethod($grpc.ServiceMethod<$2.ApplySubjectInteractionRequest, $2.ApplySubjectInteractionResponse>(
        'ApplySubjectInteraction',
        applySubjectInteraction_Pre,
        false,
        false,
        ($core.List<$core.int> value) => $2.ApplySubjectInteractionRequest.fromBuffer(value),
        ($2.ApplySubjectInteractionResponse value) => value.writeToBuffer()));
  }

  $async.Future<$2.ListSubjectsResponse> listSubjects_Pre($grpc.ServiceCall call, $async.Future<$2.ListSubjectsRequest> request) async {
    return listSubjects(call, await request);
  }

  $async.Future<$2.GetSubjectPhaseViewResponse> getSubjectPhaseView_Pre($grpc.ServiceCall call, $async.Future<$2.GetSubjectPhaseViewRequest> request) async {
    return getSubjectPhaseView(call, await request);
  }

  $async.Future<$2.GetSubjectControlBundleResponse> getSubjectControlBundle_Pre($grpc.ServiceCall call, $async.Future<$2.GetSubjectControlBundleRequest> request) async {
    return getSubjectControlBundle(call, await request);
  }

  $async.Future<$2.GetSubjectPaneBundleResponse> getSubjectPaneBundle_Pre($grpc.ServiceCall call, $async.Future<$2.GetSubjectPaneBundleRequest> request) async {
    return getSubjectPaneBundle(call, await request);
  }

  $async.Future<$2.GetSubjectWorkflowSnapshotResponse> getSubjectWorkflowSnapshot_Pre($grpc.ServiceCall call, $async.Future<$2.GetSubjectWorkflowSnapshotRequest> request) async {
    return getSubjectWorkflowSnapshot(call, await request);
  }

  $async.Stream<$2.SubjectWorkflowSnapshotUpdate> watchSubjectWorkflow_Pre($grpc.ServiceCall call, $async.Future<$2.WatchSubjectWorkflowRequest> request) async* {
    yield* watchSubjectWorkflow(call, await request);
  }

  $async.Future<$2.ApplySubjectActionResponse> applySubjectAction_Pre($grpc.ServiceCall call, $async.Future<$2.ApplySubjectActionRequest> request) async {
    return applySubjectAction(call, await request);
  }

  $async.Future<$2.GetClientSubjectProgressResponse> getClientSubjectProgress_Pre($grpc.ServiceCall call, $async.Future<$2.GetClientSubjectProgressRequest> request) async {
    return getClientSubjectProgress(call, await request);
  }

  $async.Future<$2.PutClientSubjectProgressResponse> putClientSubjectProgress_Pre($grpc.ServiceCall call, $async.Future<$2.PutClientSubjectProgressRequest> request) async {
    return putClientSubjectProgress(call, await request);
  }

  $async.Future<$2.ApplySubjectInteractionResponse> applySubjectInteraction_Pre($grpc.ServiceCall call, $async.Future<$2.ApplySubjectInteractionRequest> request) async {
    return applySubjectInteraction(call, await request);
  }

  $async.Future<$2.ListSubjectsResponse> listSubjects($grpc.ServiceCall call, $2.ListSubjectsRequest request);
  $async.Future<$2.GetSubjectPhaseViewResponse> getSubjectPhaseView($grpc.ServiceCall call, $2.GetSubjectPhaseViewRequest request);
  $async.Future<$2.GetSubjectControlBundleResponse> getSubjectControlBundle($grpc.ServiceCall call, $2.GetSubjectControlBundleRequest request);
  $async.Future<$2.GetSubjectPaneBundleResponse> getSubjectPaneBundle($grpc.ServiceCall call, $2.GetSubjectPaneBundleRequest request);
  $async.Future<$2.GetSubjectWorkflowSnapshotResponse> getSubjectWorkflowSnapshot($grpc.ServiceCall call, $2.GetSubjectWorkflowSnapshotRequest request);
  $async.Stream<$2.SubjectWorkflowSnapshotUpdate> watchSubjectWorkflow($grpc.ServiceCall call, $2.WatchSubjectWorkflowRequest request);
  $async.Future<$2.ApplySubjectActionResponse> applySubjectAction($grpc.ServiceCall call, $2.ApplySubjectActionRequest request);
  $async.Future<$2.GetClientSubjectProgressResponse> getClientSubjectProgress($grpc.ServiceCall call, $2.GetClientSubjectProgressRequest request);
  $async.Future<$2.PutClientSubjectProgressResponse> putClientSubjectProgress($grpc.ServiceCall call, $2.PutClientSubjectProgressRequest request);
  $async.Future<$2.ApplySubjectInteractionResponse> applySubjectInteraction($grpc.ServiceCall call, $2.ApplySubjectInteractionRequest request);
}
