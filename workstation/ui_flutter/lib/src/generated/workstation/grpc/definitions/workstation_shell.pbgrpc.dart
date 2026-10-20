//
//  Generated code. Do not modify.
//  source: workstation/grpc/definitions/workstation_shell.proto
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

import 'workstation_shell.pb.dart' as $3;

export 'workstation_shell.pb.dart';

@$pb.GrpcServiceName('workstation.WorkstationShellService')
class WorkstationShellServiceClient extends $grpc.Client {
  static final _$openClientSession = $grpc.ClientMethod<$3.ClientSessionRequest, $3.ClientSessionResponse>(
      '/workstation.WorkstationShellService/OpenClientSession',
      ($3.ClientSessionRequest value) => value.writeToBuffer(),
      ($core.List<$core.int> value) => $3.ClientSessionResponse.fromBuffer(value));
  static final _$closeClientSession = $grpc.ClientMethod<$3.ClientSessionRequest, $3.ClientSessionResponse>(
      '/workstation.WorkstationShellService/CloseClientSession',
      ($3.ClientSessionRequest value) => value.writeToBuffer(),
      ($core.List<$core.int> value) => $3.ClientSessionResponse.fromBuffer(value));
  static final _$getChatSnapshot = $grpc.ClientMethod<$3.ChatSnapshotRequest, $3.ChatSnapshotResponse>(
      '/workstation.WorkstationShellService/GetChatSnapshot',
      ($3.ChatSnapshotRequest value) => value.writeToBuffer(),
      ($core.List<$core.int> value) => $3.ChatSnapshotResponse.fromBuffer(value));
  static final _$prepareChatPromptTarget = $grpc.ClientMethod<$3.PrepareChatPromptTargetRequest, $3.PrepareChatPromptTargetResponse>(
      '/workstation.WorkstationShellService/PrepareChatPromptTarget',
      ($3.PrepareChatPromptTargetRequest value) => value.writeToBuffer(),
      ($core.List<$core.int> value) => $3.PrepareChatPromptTargetResponse.fromBuffer(value));
  static final _$submitChatInput = $grpc.ClientMethod<$3.SubmitChatInputRequest, $3.SubmitChatInputResponse>(
      '/workstation.WorkstationShellService/SubmitChatInput',
      ($3.SubmitChatInputRequest value) => value.writeToBuffer(),
      ($core.List<$core.int> value) => $3.SubmitChatInputResponse.fromBuffer(value));
  static final _$appendShellTurn = $grpc.ClientMethod<$3.AppendShellTurnRequest, $3.AppendShellTurnResponse>(
      '/workstation.WorkstationShellService/AppendShellTurn',
      ($3.AppendShellTurnRequest value) => value.writeToBuffer(),
      ($core.List<$core.int> value) => $3.AppendShellTurnResponse.fromBuffer(value));
  static final _$getActivityView = $grpc.ClientMethod<$3.ActivityViewRequest, $3.ShellTextView>(
      '/workstation.WorkstationShellService/GetActivityView',
      ($3.ActivityViewRequest value) => value.writeToBuffer(),
      ($core.List<$core.int> value) => $3.ShellTextView.fromBuffer(value));
  static final _$getPermissionsView = $grpc.ClientMethod<$3.PermissionsViewRequest, $3.ShellTextView>(
      '/workstation.WorkstationShellService/GetPermissionsView',
      ($3.PermissionsViewRequest value) => value.writeToBuffer(),
      ($core.List<$core.int> value) => $3.ShellTextView.fromBuffer(value));
  static final _$getSkillsView = $grpc.ClientMethod<$3.SkillsViewRequest, $3.ShellTextView>(
      '/workstation.WorkstationShellService/GetSkillsView',
      ($3.SkillsViewRequest value) => value.writeToBuffer(),
      ($core.List<$core.int> value) => $3.ShellTextView.fromBuffer(value));
  static final _$watchWorkstationShell = $grpc.ClientMethod<$3.WatchWorkstationShellRequest, $3.WorkstationShellWatchEvent>(
      '/workstation.WorkstationShellService/WatchWorkstationShell',
      ($3.WatchWorkstationShellRequest value) => value.writeToBuffer(),
      ($core.List<$core.int> value) => $3.WorkstationShellWatchEvent.fromBuffer(value));

  WorkstationShellServiceClient($grpc.ClientChannel channel,
      {$grpc.CallOptions? options,
      $core.Iterable<$grpc.ClientInterceptor>? interceptors})
      : super(channel, options: options,
        interceptors: interceptors);

  $grpc.ResponseFuture<$3.ClientSessionResponse> openClientSession($3.ClientSessionRequest request, {$grpc.CallOptions? options}) {
    return $createUnaryCall(_$openClientSession, request, options: options);
  }

  $grpc.ResponseFuture<$3.ClientSessionResponse> closeClientSession($3.ClientSessionRequest request, {$grpc.CallOptions? options}) {
    return $createUnaryCall(_$closeClientSession, request, options: options);
  }

  $grpc.ResponseFuture<$3.ChatSnapshotResponse> getChatSnapshot($3.ChatSnapshotRequest request, {$grpc.CallOptions? options}) {
    return $createUnaryCall(_$getChatSnapshot, request, options: options);
  }

  $grpc.ResponseFuture<$3.PrepareChatPromptTargetResponse> prepareChatPromptTarget($3.PrepareChatPromptTargetRequest request, {$grpc.CallOptions? options}) {
    return $createUnaryCall(_$prepareChatPromptTarget, request, options: options);
  }

  $grpc.ResponseFuture<$3.SubmitChatInputResponse> submitChatInput($3.SubmitChatInputRequest request, {$grpc.CallOptions? options}) {
    return $createUnaryCall(_$submitChatInput, request, options: options);
  }

  $grpc.ResponseFuture<$3.AppendShellTurnResponse> appendShellTurn($3.AppendShellTurnRequest request, {$grpc.CallOptions? options}) {
    return $createUnaryCall(_$appendShellTurn, request, options: options);
  }

  $grpc.ResponseFuture<$3.ShellTextView> getActivityView($3.ActivityViewRequest request, {$grpc.CallOptions? options}) {
    return $createUnaryCall(_$getActivityView, request, options: options);
  }

  $grpc.ResponseFuture<$3.ShellTextView> getPermissionsView($3.PermissionsViewRequest request, {$grpc.CallOptions? options}) {
    return $createUnaryCall(_$getPermissionsView, request, options: options);
  }

  $grpc.ResponseFuture<$3.ShellTextView> getSkillsView($3.SkillsViewRequest request, {$grpc.CallOptions? options}) {
    return $createUnaryCall(_$getSkillsView, request, options: options);
  }

  $grpc.ResponseStream<$3.WorkstationShellWatchEvent> watchWorkstationShell($3.WatchWorkstationShellRequest request, {$grpc.CallOptions? options}) {
    return $createStreamingCall(_$watchWorkstationShell, $async.Stream.fromIterable([request]), options: options);
  }
}

@$pb.GrpcServiceName('workstation.WorkstationShellService')
abstract class WorkstationShellServiceBase extends $grpc.Service {
  $core.String get $name => 'workstation.WorkstationShellService';

  WorkstationShellServiceBase() {
    $addMethod($grpc.ServiceMethod<$3.ClientSessionRequest, $3.ClientSessionResponse>(
        'OpenClientSession',
        openClientSession_Pre,
        false,
        false,
        ($core.List<$core.int> value) => $3.ClientSessionRequest.fromBuffer(value),
        ($3.ClientSessionResponse value) => value.writeToBuffer()));
    $addMethod($grpc.ServiceMethod<$3.ClientSessionRequest, $3.ClientSessionResponse>(
        'CloseClientSession',
        closeClientSession_Pre,
        false,
        false,
        ($core.List<$core.int> value) => $3.ClientSessionRequest.fromBuffer(value),
        ($3.ClientSessionResponse value) => value.writeToBuffer()));
    $addMethod($grpc.ServiceMethod<$3.ChatSnapshotRequest, $3.ChatSnapshotResponse>(
        'GetChatSnapshot',
        getChatSnapshot_Pre,
        false,
        false,
        ($core.List<$core.int> value) => $3.ChatSnapshotRequest.fromBuffer(value),
        ($3.ChatSnapshotResponse value) => value.writeToBuffer()));
    $addMethod($grpc.ServiceMethod<$3.PrepareChatPromptTargetRequest, $3.PrepareChatPromptTargetResponse>(
        'PrepareChatPromptTarget',
        prepareChatPromptTarget_Pre,
        false,
        false,
        ($core.List<$core.int> value) => $3.PrepareChatPromptTargetRequest.fromBuffer(value),
        ($3.PrepareChatPromptTargetResponse value) => value.writeToBuffer()));
    $addMethod($grpc.ServiceMethod<$3.SubmitChatInputRequest, $3.SubmitChatInputResponse>(
        'SubmitChatInput',
        submitChatInput_Pre,
        false,
        false,
        ($core.List<$core.int> value) => $3.SubmitChatInputRequest.fromBuffer(value),
        ($3.SubmitChatInputResponse value) => value.writeToBuffer()));
    $addMethod($grpc.ServiceMethod<$3.AppendShellTurnRequest, $3.AppendShellTurnResponse>(
        'AppendShellTurn',
        appendShellTurn_Pre,
        false,
        false,
        ($core.List<$core.int> value) => $3.AppendShellTurnRequest.fromBuffer(value),
        ($3.AppendShellTurnResponse value) => value.writeToBuffer()));
    $addMethod($grpc.ServiceMethod<$3.ActivityViewRequest, $3.ShellTextView>(
        'GetActivityView',
        getActivityView_Pre,
        false,
        false,
        ($core.List<$core.int> value) => $3.ActivityViewRequest.fromBuffer(value),
        ($3.ShellTextView value) => value.writeToBuffer()));
    $addMethod($grpc.ServiceMethod<$3.PermissionsViewRequest, $3.ShellTextView>(
        'GetPermissionsView',
        getPermissionsView_Pre,
        false,
        false,
        ($core.List<$core.int> value) => $3.PermissionsViewRequest.fromBuffer(value),
        ($3.ShellTextView value) => value.writeToBuffer()));
    $addMethod($grpc.ServiceMethod<$3.SkillsViewRequest, $3.ShellTextView>(
        'GetSkillsView',
        getSkillsView_Pre,
        false,
        false,
        ($core.List<$core.int> value) => $3.SkillsViewRequest.fromBuffer(value),
        ($3.ShellTextView value) => value.writeToBuffer()));
    $addMethod($grpc.ServiceMethod<$3.WatchWorkstationShellRequest, $3.WorkstationShellWatchEvent>(
        'WatchWorkstationShell',
        watchWorkstationShell_Pre,
        false,
        true,
        ($core.List<$core.int> value) => $3.WatchWorkstationShellRequest.fromBuffer(value),
        ($3.WorkstationShellWatchEvent value) => value.writeToBuffer()));
  }

  $async.Future<$3.ClientSessionResponse> openClientSession_Pre($grpc.ServiceCall call, $async.Future<$3.ClientSessionRequest> request) async {
    return openClientSession(call, await request);
  }

  $async.Future<$3.ClientSessionResponse> closeClientSession_Pre($grpc.ServiceCall call, $async.Future<$3.ClientSessionRequest> request) async {
    return closeClientSession(call, await request);
  }

  $async.Future<$3.ChatSnapshotResponse> getChatSnapshot_Pre($grpc.ServiceCall call, $async.Future<$3.ChatSnapshotRequest> request) async {
    return getChatSnapshot(call, await request);
  }

  $async.Future<$3.PrepareChatPromptTargetResponse> prepareChatPromptTarget_Pre($grpc.ServiceCall call, $async.Future<$3.PrepareChatPromptTargetRequest> request) async {
    return prepareChatPromptTarget(call, await request);
  }

  $async.Future<$3.SubmitChatInputResponse> submitChatInput_Pre($grpc.ServiceCall call, $async.Future<$3.SubmitChatInputRequest> request) async {
    return submitChatInput(call, await request);
  }

  $async.Future<$3.AppendShellTurnResponse> appendShellTurn_Pre($grpc.ServiceCall call, $async.Future<$3.AppendShellTurnRequest> request) async {
    return appendShellTurn(call, await request);
  }

  $async.Future<$3.ShellTextView> getActivityView_Pre($grpc.ServiceCall call, $async.Future<$3.ActivityViewRequest> request) async {
    return getActivityView(call, await request);
  }

  $async.Future<$3.ShellTextView> getPermissionsView_Pre($grpc.ServiceCall call, $async.Future<$3.PermissionsViewRequest> request) async {
    return getPermissionsView(call, await request);
  }

  $async.Future<$3.ShellTextView> getSkillsView_Pre($grpc.ServiceCall call, $async.Future<$3.SkillsViewRequest> request) async {
    return getSkillsView(call, await request);
  }

  $async.Stream<$3.WorkstationShellWatchEvent> watchWorkstationShell_Pre($grpc.ServiceCall call, $async.Future<$3.WatchWorkstationShellRequest> request) async* {
    yield* watchWorkstationShell(call, await request);
  }

  $async.Future<$3.ClientSessionResponse> openClientSession($grpc.ServiceCall call, $3.ClientSessionRequest request);
  $async.Future<$3.ClientSessionResponse> closeClientSession($grpc.ServiceCall call, $3.ClientSessionRequest request);
  $async.Future<$3.ChatSnapshotResponse> getChatSnapshot($grpc.ServiceCall call, $3.ChatSnapshotRequest request);
  $async.Future<$3.PrepareChatPromptTargetResponse> prepareChatPromptTarget($grpc.ServiceCall call, $3.PrepareChatPromptTargetRequest request);
  $async.Future<$3.SubmitChatInputResponse> submitChatInput($grpc.ServiceCall call, $3.SubmitChatInputRequest request);
  $async.Future<$3.AppendShellTurnResponse> appendShellTurn($grpc.ServiceCall call, $3.AppendShellTurnRequest request);
  $async.Future<$3.ShellTextView> getActivityView($grpc.ServiceCall call, $3.ActivityViewRequest request);
  $async.Future<$3.ShellTextView> getPermissionsView($grpc.ServiceCall call, $3.PermissionsViewRequest request);
  $async.Future<$3.ShellTextView> getSkillsView($grpc.ServiceCall call, $3.SkillsViewRequest request);
  $async.Stream<$3.WorkstationShellWatchEvent> watchWorkstationShell($grpc.ServiceCall call, $3.WatchWorkstationShellRequest request);
}
