//
//  Generated code. Do not modify.
//  source: workstation/grpc/definitions/workstation_shell.proto
//
// @dart = 2.12

// ignore_for_file: annotate_overrides, camel_case_types, comment_references
// ignore_for_file: constant_identifier_names, library_prefixes
// ignore_for_file: non_constant_identifier_names, prefer_final_fields
// ignore_for_file: unnecessary_import, unnecessary_this, unused_import

import 'dart:core' as $core;

import 'package:fixnum/fixnum.dart' as $fixnum;
import 'package:protobuf/protobuf.dart' as $pb;

/// What: Request used to open or close one shell client session.
/// Why: The shell API scopes transcript cursors and shell-side view state to a
/// single client session id.
/// How: Supply the workstation root and the caller's stable client session id;
/// optional subject/phase hints let one client keep the shell aligned to the
/// currently focused subject workflow state.
/// Valid Example:
///   {
///     "root_path": "/srv/workstations/transit",
///     "client_session_id": "flutter-shell-a",
///     "selected_subject_id": "subject_transit_modernization",
///     "selected_phase": "research"
///   }
class ClientSessionRequest extends $pb.GeneratedMessage {
  factory ClientSessionRequest({
    $core.String? rootPath,
    $core.String? clientSessionId,
    $core.String? selectedSubjectId,
    $core.String? selectedPhase,
  }) {
    final $result = create();
    if (rootPath != null) {
      $result.rootPath = rootPath;
    }
    if (clientSessionId != null) {
      $result.clientSessionId = clientSessionId;
    }
    if (selectedSubjectId != null) {
      $result.selectedSubjectId = selectedSubjectId;
    }
    if (selectedPhase != null) {
      $result.selectedPhase = selectedPhase;
    }
    return $result;
  }
  ClientSessionRequest._() : super();
  factory ClientSessionRequest.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory ClientSessionRequest.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'ClientSessionRequest', package: const $pb.PackageName(_omitMessageNames ? '' : 'workstation'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'rootPath')
    ..aOS(2, _omitFieldNames ? '' : 'clientSessionId')
    ..aOS(3, _omitFieldNames ? '' : 'selectedSubjectId')
    ..aOS(4, _omitFieldNames ? '' : 'selectedPhase')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  ClientSessionRequest clone() => ClientSessionRequest()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  ClientSessionRequest copyWith(void Function(ClientSessionRequest) updates) => super.copyWith((message) => updates(message as ClientSessionRequest)) as ClientSessionRequest;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static ClientSessionRequest create() => ClientSessionRequest._();
  ClientSessionRequest createEmptyInstance() => create();
  static $pb.PbList<ClientSessionRequest> createRepeated() => $pb.PbList<ClientSessionRequest>();
  @$core.pragma('dart2js:noInline')
  static ClientSessionRequest getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<ClientSessionRequest>(create);
  static ClientSessionRequest? _defaultInstance;

  /// What: Absolute workstation root path on the server.
  /// Why: The shell service needs a concrete workstation instance to read and
  /// write transcript, capability, and projection state.
  /// How: Use the `root_path` returned by `ListWorkstationRoots`.
  /// Example: "/srv/workstations/transit"
  @$pb.TagNumber(1)
  $core.String get rootPath => $_getSZ(0);
  @$pb.TagNumber(1)
  set rootPath($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasRootPath() => $_has(0);
  @$pb.TagNumber(1)
  void clearRootPath() => clearField(1);

  /// What: Stable caller-chosen session id.
  /// Why: Transcript cursors and shell-side state must survive multiple RPCs.
  /// How: Reuse the same id for the lifetime of one UI session.
  /// Example: "flutter-shell-a"
  @$pb.TagNumber(2)
  $core.String get clientSessionId => $_getSZ(1);
  @$pb.TagNumber(2)
  set clientSessionId($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasClientSessionId() => $_has(1);
  @$pb.TagNumber(2)
  void clearClientSessionId() => clearField(2);

  /// What: Optional currently focused subject id.
  /// Why: Shell-side routing can align context-sensitive suggestions with the
  /// subject the user is actively viewing.
  /// How: Set it when the UI has one selected subject; otherwise leave empty.
  /// Example: "subject_transit_modernization"
  @$pb.TagNumber(3)
  $core.String get selectedSubjectId => $_getSZ(2);
  @$pb.TagNumber(3)
  set selectedSubjectId($core.String v) { $_setString(2, v); }
  @$pb.TagNumber(3)
  $core.bool hasSelectedSubjectId() => $_has(2);
  @$pb.TagNumber(3)
  void clearSelectedSubjectId() => clearField(3);

  /// What: Optional currently focused workflow phase.
  /// Why: Shell prompt routing can tailor assistance to the active phase.
  /// How: Set it to the phase currently shown in the UI.
  /// Example: "research"
  @$pb.TagNumber(4)
  $core.String get selectedPhase => $_getSZ(3);
  @$pb.TagNumber(4)
  set selectedPhase($core.String v) { $_setString(3, v); }
  @$pb.TagNumber(4)
  $core.bool hasSelectedPhase() => $_has(3);
  @$pb.TagNumber(4)
  void clearSelectedPhase() => clearField(4);
}

/// What: Response returned after opening or closing a shell client session.
/// Why: The server may normalize the client session id and always emits tracing
/// identifiers for auditability.
/// How: Persist the returned `client_session_id` if the caller supplied an
/// empty or provisional id.
/// Valid Example:
///   {
///     "client_session_id": "flutter-shell-a",
///     "trace_id": "shell-session-response_7aa54f5d",
///     "parent_id": "shell-open-session-request_1fe3df36"
///   }
class ClientSessionResponse extends $pb.GeneratedMessage {
  factory ClientSessionResponse({
    $core.String? clientSessionId,
    $core.String? traceId,
    $core.String? parentId,
  }) {
    final $result = create();
    if (clientSessionId != null) {
      $result.clientSessionId = clientSessionId;
    }
    if (traceId != null) {
      $result.traceId = traceId;
    }
    if (parentId != null) {
      $result.parentId = parentId;
    }
    return $result;
  }
  ClientSessionResponse._() : super();
  factory ClientSessionResponse.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory ClientSessionResponse.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'ClientSessionResponse', package: const $pb.PackageName(_omitMessageNames ? '' : 'workstation'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'clientSessionId')
    ..aOS(100, _omitFieldNames ? '' : 'traceId')
    ..aOS(101, _omitFieldNames ? '' : 'parentId')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  ClientSessionResponse clone() => ClientSessionResponse()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  ClientSessionResponse copyWith(void Function(ClientSessionResponse) updates) => super.copyWith((message) => updates(message as ClientSessionResponse)) as ClientSessionResponse;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static ClientSessionResponse create() => ClientSessionResponse._();
  ClientSessionResponse createEmptyInstance() => create();
  static $pb.PbList<ClientSessionResponse> createRepeated() => $pb.PbList<ClientSessionResponse>();
  @$core.pragma('dart2js:noInline')
  static ClientSessionResponse getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<ClientSessionResponse>(create);
  static ClientSessionResponse? _defaultInstance;

  /// What: Effective session id accepted by the server.
  /// Why: Callers need one canonical id for subsequent shell RPCs.
  /// How: Store and reuse it on every later request.
  /// Example: "flutter-shell-a"
  @$pb.TagNumber(1)
  $core.String get clientSessionId => $_getSZ(0);
  @$pb.TagNumber(1)
  set clientSessionId($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasClientSessionId() => $_has(0);
  @$pb.TagNumber(1)
  void clearClientSessionId() => clearField(1);

  /// What: Trace id for the response message.
  /// Why: Shell transport events are auditable and trace-linked across layers.
  /// How: Log it or correlate it with server diagnostics when debugging.
  /// Example: "shell-session-response_7aa54f5d"
  @$pb.TagNumber(100)
  $core.String get traceId => $_getSZ(1);
  @$pb.TagNumber(100)
  set traceId($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(100)
  $core.bool hasTraceId() => $_has(1);
  @$pb.TagNumber(100)
  void clearTraceId() => clearField(100);

  /// What: Parent trace id that links this message to the initiating request.
  /// Why: Downstream tools need causal linkage across request/response edges.
  /// How: Treat it as an opaque correlation value.
  /// Example: "shell-open-session-request_1fe3df36"
  @$pb.TagNumber(101)
  $core.String get parentId => $_getSZ(2);
  @$pb.TagNumber(101)
  set parentId($core.String v) { $_setString(2, v); }
  @$pb.TagNumber(101)
  $core.bool hasParentId() => $_has(2);
  @$pb.TagNumber(101)
  void clearParentId() => clearField(101);
}

/// What: One transcript message rendered in the workstation shell.
/// Why: Chat transcripts are exchanged as structured entries rather than raw
/// monolithic text so UIs can style and diff them accurately.
/// How: Render each entry according to `role` and order by
/// `timestamp_epoch_ms`.
/// Valid Example:
///   {
///     "role": "assistant",
///     "content": "Use /help to inspect shell commands.",
///     "timestamp_epoch_ms": 1777780023123
///   }
class WorkstationChatMessage extends $pb.GeneratedMessage {
  factory WorkstationChatMessage({
    $core.String? role,
    $core.String? content,
    $fixnum.Int64? timestampEpochMs,
  }) {
    final $result = create();
    if (role != null) {
      $result.role = role;
    }
    if (content != null) {
      $result.content = content;
    }
    if (timestampEpochMs != null) {
      $result.timestampEpochMs = timestampEpochMs;
    }
    return $result;
  }
  WorkstationChatMessage._() : super();
  factory WorkstationChatMessage.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory WorkstationChatMessage.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'WorkstationChatMessage', package: const $pb.PackageName(_omitMessageNames ? '' : 'workstation'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'role')
    ..aOS(2, _omitFieldNames ? '' : 'content')
    ..aInt64(3, _omitFieldNames ? '' : 'timestampEpochMs')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  WorkstationChatMessage clone() => WorkstationChatMessage()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  WorkstationChatMessage copyWith(void Function(WorkstationChatMessage) updates) => super.copyWith((message) => updates(message as WorkstationChatMessage)) as WorkstationChatMessage;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static WorkstationChatMessage create() => WorkstationChatMessage._();
  WorkstationChatMessage createEmptyInstance() => create();
  static $pb.PbList<WorkstationChatMessage> createRepeated() => $pb.PbList<WorkstationChatMessage>();
  @$core.pragma('dart2js:noInline')
  static WorkstationChatMessage getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<WorkstationChatMessage>(create);
  static WorkstationChatMessage? _defaultInstance;

  /// What: Semantic transcript role.
  /// Why: UIs need to distinguish user, assistant, shell, and system turns.
  /// How: Render with role-appropriate styling.
  /// Example: "assistant"
  @$pb.TagNumber(1)
  $core.String get role => $_getSZ(0);
  @$pb.TagNumber(1)
  set role($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasRole() => $_has(0);
  @$pb.TagNumber(1)
  void clearRole() => clearField(1);

  /// What: Message body text.
  /// Why: This is the human-readable content shown in the transcript.
  /// How: Display it exactly as returned unless the UI has richer markdown
  /// rendering rules.
  /// Example: "Use /help to inspect shell commands."
  @$pb.TagNumber(2)
  $core.String get content => $_getSZ(1);
  @$pb.TagNumber(2)
  set content($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasContent() => $_has(1);
  @$pb.TagNumber(2)
  void clearContent() => clearField(2);

  /// What: Unix epoch timestamp in milliseconds.
  /// Why: Clients need stable chronological ordering and human time displays.
  /// How: Convert to local time for presentation.
  /// Example: 1777780023123
  @$pb.TagNumber(3)
  $fixnum.Int64 get timestampEpochMs => $_getI64(2);
  @$pb.TagNumber(3)
  set timestampEpochMs($fixnum.Int64 v) { $_setInt64(2, v); }
  @$pb.TagNumber(3)
  $core.bool hasTimestampEpochMs() => $_has(2);
  @$pb.TagNumber(3)
  void clearTimestampEpochMs() => clearField(3);
}

/// What: Request for a bounded transcript snapshot.
/// Why: Clients need an initial transcript state before switching to watch
/// streams.
/// How: Call this after opening a session and before rendering the chat pane.
/// Valid Example:
///   {
///     "root_path": "/srv/workstations/transit",
///     "client_session_id": "flutter-shell-a",
///     "limit": 120,
///     "selected_subject_id": "subject_transit_modernization",
///     "selected_phase": "research"
///   }
class ChatSnapshotRequest extends $pb.GeneratedMessage {
  factory ChatSnapshotRequest({
    $core.String? rootPath,
    $core.String? clientSessionId,
    $core.int? limit,
    $core.String? selectedSubjectId,
    $core.String? selectedPhase,
  }) {
    final $result = create();
    if (rootPath != null) {
      $result.rootPath = rootPath;
    }
    if (clientSessionId != null) {
      $result.clientSessionId = clientSessionId;
    }
    if (limit != null) {
      $result.limit = limit;
    }
    if (selectedSubjectId != null) {
      $result.selectedSubjectId = selectedSubjectId;
    }
    if (selectedPhase != null) {
      $result.selectedPhase = selectedPhase;
    }
    return $result;
  }
  ChatSnapshotRequest._() : super();
  factory ChatSnapshotRequest.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory ChatSnapshotRequest.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'ChatSnapshotRequest', package: const $pb.PackageName(_omitMessageNames ? '' : 'workstation'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'rootPath')
    ..aOS(2, _omitFieldNames ? '' : 'clientSessionId')
    ..a<$core.int>(3, _omitFieldNames ? '' : 'limit', $pb.PbFieldType.O3)
    ..aOS(4, _omitFieldNames ? '' : 'selectedSubjectId')
    ..aOS(5, _omitFieldNames ? '' : 'selectedPhase')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  ChatSnapshotRequest clone() => ChatSnapshotRequest()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  ChatSnapshotRequest copyWith(void Function(ChatSnapshotRequest) updates) => super.copyWith((message) => updates(message as ChatSnapshotRequest)) as ChatSnapshotRequest;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static ChatSnapshotRequest create() => ChatSnapshotRequest._();
  ChatSnapshotRequest createEmptyInstance() => create();
  static $pb.PbList<ChatSnapshotRequest> createRepeated() => $pb.PbList<ChatSnapshotRequest>();
  @$core.pragma('dart2js:noInline')
  static ChatSnapshotRequest getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<ChatSnapshotRequest>(create);
  static ChatSnapshotRequest? _defaultInstance;

  /// What: Absolute workstation root path on the server.
  /// Why: Snapshot lookup is scoped to one workstation instance.
  /// How: Reuse the root selected during bootstrap.
  /// Example: "/srv/workstations/transit"
  @$pb.TagNumber(1)
  $core.String get rootPath => $_getSZ(0);
  @$pb.TagNumber(1)
  set rootPath($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasRootPath() => $_has(0);
  @$pb.TagNumber(1)
  void clearRootPath() => clearField(1);

  /// What: Stable caller session id.
  /// Why: Snapshot materialization may incorporate session-scoped shell state.
  /// How: Reuse the same id returned by `OpenClientSession`.
  /// Example: "flutter-shell-a"
  @$pb.TagNumber(2)
  $core.String get clientSessionId => $_getSZ(1);
  @$pb.TagNumber(2)
  set clientSessionId($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasClientSessionId() => $_has(1);
  @$pb.TagNumber(2)
  void clearClientSessionId() => clearField(2);

  /// What: Maximum number of transcript messages to return.
  /// Why: Clients often want a recent bounded window instead of the full
  /// transcript history.
  /// How: Set a positive integer such as 120 for the initial load.
  /// Example: 120
  @$pb.TagNumber(3)
  $core.int get limit => $_getIZ(2);
  @$pb.TagNumber(3)
  set limit($core.int v) { $_setSignedInt32(2, v); }
  @$pb.TagNumber(3)
  $core.bool hasLimit() => $_has(2);
  @$pb.TagNumber(3)
  void clearLimit() => clearField(3);

  /// What: Optional currently focused subject id.
  /// Why: The shell can align snapshot metadata with the selected subject.
  /// How: Leave empty when the shell is not subject-focused.
  /// Example: "subject_transit_modernization"
  @$pb.TagNumber(4)
  $core.String get selectedSubjectId => $_getSZ(3);
  @$pb.TagNumber(4)
  set selectedSubjectId($core.String v) { $_setString(3, v); }
  @$pb.TagNumber(4)
  $core.bool hasSelectedSubjectId() => $_has(3);
  @$pb.TagNumber(4)
  void clearSelectedSubjectId() => clearField(4);

  /// What: Optional currently focused workflow phase.
  /// Why: The shell can emit phase-aware status text and suggestions.
  /// How: Set it to the active phase name or leave empty.
  /// Example: "research"
  @$pb.TagNumber(5)
  $core.String get selectedPhase => $_getSZ(4);
  @$pb.TagNumber(5)
  set selectedPhase($core.String v) { $_setString(4, v); }
  @$pb.TagNumber(5)
  $core.bool hasSelectedPhase() => $_has(4);
  @$pb.TagNumber(5)
  void clearSelectedPhase() => clearField(5);
}

/// What: Transcript snapshot plus shell status metadata.
/// Why: Clients need both transcript entries and stable version markers to
/// decide whether a watch event is newer than local state.
/// How: Render `messages`, show `session_status`, and cache
/// `snapshot_version`/`progress_fingerprint` for watch reconciliation.
/// Valid Example:
///   {
///     "messages": [
///       {
///         "role": "assistant",
///         "content": "Use /help to inspect shell commands.",
///         "timestamp_epoch_ms": 1777780023123
///       }
///     ],
///     "session_status": "ready",
///     "snapshot_version": "shell-chat-14",
///     "progress_fingerprint": "3a5fd0b71420f1ad",
///     "trace_id": "shell-chat-snapshot_66c83e6b",
///     "parent_id": "shell-chat-request_bec93057"
///   }
class ChatSnapshotResponse extends $pb.GeneratedMessage {
  factory ChatSnapshotResponse({
    $core.Iterable<WorkstationChatMessage>? messages,
    $core.String? sessionStatus,
    $core.String? snapshotVersion,
    $core.String? progressFingerprint,
    $core.String? traceId,
    $core.String? parentId,
  }) {
    final $result = create();
    if (messages != null) {
      $result.messages.addAll(messages);
    }
    if (sessionStatus != null) {
      $result.sessionStatus = sessionStatus;
    }
    if (snapshotVersion != null) {
      $result.snapshotVersion = snapshotVersion;
    }
    if (progressFingerprint != null) {
      $result.progressFingerprint = progressFingerprint;
    }
    if (traceId != null) {
      $result.traceId = traceId;
    }
    if (parentId != null) {
      $result.parentId = parentId;
    }
    return $result;
  }
  ChatSnapshotResponse._() : super();
  factory ChatSnapshotResponse.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory ChatSnapshotResponse.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'ChatSnapshotResponse', package: const $pb.PackageName(_omitMessageNames ? '' : 'workstation'), createEmptyInstance: create)
    ..pc<WorkstationChatMessage>(1, _omitFieldNames ? '' : 'messages', $pb.PbFieldType.PM, subBuilder: WorkstationChatMessage.create)
    ..aOS(2, _omitFieldNames ? '' : 'sessionStatus')
    ..aOS(3, _omitFieldNames ? '' : 'snapshotVersion')
    ..aOS(4, _omitFieldNames ? '' : 'progressFingerprint')
    ..aOS(100, _omitFieldNames ? '' : 'traceId')
    ..aOS(101, _omitFieldNames ? '' : 'parentId')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  ChatSnapshotResponse clone() => ChatSnapshotResponse()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  ChatSnapshotResponse copyWith(void Function(ChatSnapshotResponse) updates) => super.copyWith((message) => updates(message as ChatSnapshotResponse)) as ChatSnapshotResponse;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static ChatSnapshotResponse create() => ChatSnapshotResponse._();
  ChatSnapshotResponse createEmptyInstance() => create();
  static $pb.PbList<ChatSnapshotResponse> createRepeated() => $pb.PbList<ChatSnapshotResponse>();
  @$core.pragma('dart2js:noInline')
  static ChatSnapshotResponse getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<ChatSnapshotResponse>(create);
  static ChatSnapshotResponse? _defaultInstance;

  /// What: Ordered transcript entries.
  /// Why: The transcript pane is rendered from structured messages.
  /// How: Replace or merge the local transcript with this sequence.
  /// Example: [{"role":"assistant","content":"Use /help to inspect shell commands.","timestamp_epoch_ms":1777780023123}]
  @$pb.TagNumber(1)
  $core.List<WorkstationChatMessage> get messages => $_getList(0);

  /// What: High-level shell readiness status.
  /// Why: Clients need a concise shell banner such as `ready` or `busy`.
  /// How: Surface it in the chat status strip.
  /// Example: "ready"
  @$pb.TagNumber(2)
  $core.String get sessionStatus => $_getSZ(1);
  @$pb.TagNumber(2)
  set sessionStatus($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasSessionStatus() => $_has(1);
  @$pb.TagNumber(2)
  void clearSessionStatus() => clearField(2);

  /// What: Monotonic snapshot version token for the transcript channel.
  /// Why: Watch streams and polling clients need a stable change token.
  /// How: Cache it and pass it back as `last_seen_version` in watch requests.
  /// Example: "shell-chat-14"
  @$pb.TagNumber(3)
  $core.String get snapshotVersion => $_getSZ(2);
  @$pb.TagNumber(3)
  set snapshotVersion($core.String v) { $_setString(2, v); }
  @$pb.TagNumber(3)
  $core.bool hasSnapshotVersion() => $_has(2);
  @$pb.TagNumber(3)
  void clearSnapshotVersion() => clearField(3);

  /// What: Fingerprint of the relevant progress state.
  /// Why: Clients can cheaply detect whether local projections are stale.
  /// How: Treat it as an opaque version checksum.
  /// Example: "3a5fd0b71420f1ad"
  @$pb.TagNumber(4)
  $core.String get progressFingerprint => $_getSZ(3);
  @$pb.TagNumber(4)
  set progressFingerprint($core.String v) { $_setString(3, v); }
  @$pb.TagNumber(4)
  $core.bool hasProgressFingerprint() => $_has(3);
  @$pb.TagNumber(4)
  void clearProgressFingerprint() => clearField(4);

  /// What: Trace id for this snapshot response.
  /// Why: Transcript fetches participate in traceable host operations.
  /// How: Log it for correlation when debugging.
  /// Example: "shell-chat-snapshot_66c83e6b"
  @$pb.TagNumber(100)
  $core.String get traceId => $_getSZ(4);
  @$pb.TagNumber(100)
  set traceId($core.String v) { $_setString(4, v); }
  @$pb.TagNumber(100)
  $core.bool hasTraceId() => $_has(4);
  @$pb.TagNumber(100)
  void clearTraceId() => clearField(100);

  /// What: Parent trace id linking back to the initiating request.
  /// Why: Distributed audit logs need response-to-request linkage.
  /// How: Treat it as opaque correlation metadata.
  /// Example: "shell-chat-request_bec93057"
  @$pb.TagNumber(101)
  $core.String get parentId => $_getSZ(5);
  @$pb.TagNumber(101)
  set parentId($core.String v) { $_setString(5, v); }
  @$pb.TagNumber(101)
  $core.bool hasParentId() => $_has(5);
  @$pb.TagNumber(101)
  void clearParentId() => clearField(101);
}

/// What: Request for shell-side prompt routing and target preparation.
/// Why: Clients often want to preview whether a prompt will be routed to shell
/// help, a slash command, or the LLM/tool loop before submission.
/// How: Call this while the user is composing or immediately before submit.
/// Valid Example:
///   {
///     "root_path": "/srv/workstations/transit",
///     "client_session_id": "flutter-shell-a",
///     "prompt_text": "/help",
///     "selected_subject_id": "subject_transit_modernization",
///     "selected_phase": "research"
///   }
class PrepareChatPromptTargetRequest extends $pb.GeneratedMessage {
  factory PrepareChatPromptTargetRequest({
    $core.String? rootPath,
    $core.String? clientSessionId,
    $core.String? promptText,
    $core.String? selectedSubjectId,
    $core.String? selectedPhase,
  }) {
    final $result = create();
    if (rootPath != null) {
      $result.rootPath = rootPath;
    }
    if (clientSessionId != null) {
      $result.clientSessionId = clientSessionId;
    }
    if (promptText != null) {
      $result.promptText = promptText;
    }
    if (selectedSubjectId != null) {
      $result.selectedSubjectId = selectedSubjectId;
    }
    if (selectedPhase != null) {
      $result.selectedPhase = selectedPhase;
    }
    return $result;
  }
  PrepareChatPromptTargetRequest._() : super();
  factory PrepareChatPromptTargetRequest.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory PrepareChatPromptTargetRequest.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'PrepareChatPromptTargetRequest', package: const $pb.PackageName(_omitMessageNames ? '' : 'workstation'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'rootPath')
    ..aOS(2, _omitFieldNames ? '' : 'clientSessionId')
    ..aOS(3, _omitFieldNames ? '' : 'promptText')
    ..aOS(4, _omitFieldNames ? '' : 'selectedSubjectId')
    ..aOS(5, _omitFieldNames ? '' : 'selectedPhase')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  PrepareChatPromptTargetRequest clone() => PrepareChatPromptTargetRequest()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  PrepareChatPromptTargetRequest copyWith(void Function(PrepareChatPromptTargetRequest) updates) => super.copyWith((message) => updates(message as PrepareChatPromptTargetRequest)) as PrepareChatPromptTargetRequest;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static PrepareChatPromptTargetRequest create() => PrepareChatPromptTargetRequest._();
  PrepareChatPromptTargetRequest createEmptyInstance() => create();
  static $pb.PbList<PrepareChatPromptTargetRequest> createRepeated() => $pb.PbList<PrepareChatPromptTargetRequest>();
  @$core.pragma('dart2js:noInline')
  static PrepareChatPromptTargetRequest getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<PrepareChatPromptTargetRequest>(create);
  static PrepareChatPromptTargetRequest? _defaultInstance;

  /// What: Absolute workstation root path on the server.
  /// Why: Prompt routing needs workstation-local capabilities and state.
  /// How: Reuse the bootstrapped root path.
  /// Example: "/srv/workstations/transit"
  @$pb.TagNumber(1)
  $core.String get rootPath => $_getSZ(0);
  @$pb.TagNumber(1)
  set rootPath($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasRootPath() => $_has(0);
  @$pb.TagNumber(1)
  void clearRootPath() => clearField(1);

  /// What: Stable caller session id.
  /// Why: Routing may depend on session-scoped shell context.
  /// How: Use the active shell session id.
  /// Example: "flutter-shell-a"
  @$pb.TagNumber(2)
  $core.String get clientSessionId => $_getSZ(1);
  @$pb.TagNumber(2)
  set clientSessionId($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasClientSessionId() => $_has(1);
  @$pb.TagNumber(2)
  void clearClientSessionId() => clearField(2);

  /// What: Raw user-entered prompt text.
  /// Why: The routing service analyzes exactly what the user intends to send.
  /// How: Pass the current composer text unchanged.
  /// Example: "/help"
  @$pb.TagNumber(3)
  $core.String get promptText => $_getSZ(2);
  @$pb.TagNumber(3)
  set promptText($core.String v) { $_setString(2, v); }
  @$pb.TagNumber(3)
  $core.bool hasPromptText() => $_has(2);
  @$pb.TagNumber(3)
  void clearPromptText() => clearField(3);

  /// What: Optional focused subject id.
  /// Why: Prompt routing can use it to tailor subject-aware help or context.
  /// How: Leave empty when the shell is not subject-focused.
  /// Example: "subject_transit_modernization"
  @$pb.TagNumber(4)
  $core.String get selectedSubjectId => $_getSZ(3);
  @$pb.TagNumber(4)
  set selectedSubjectId($core.String v) { $_setString(3, v); }
  @$pb.TagNumber(4)
  $core.bool hasSelectedSubjectId() => $_has(3);
  @$pb.TagNumber(4)
  void clearSelectedSubjectId() => clearField(4);

  /// What: Optional focused workflow phase.
  /// Why: The routing plan can reference the active phase in guidance text.
  /// How: Set it to the active phase or leave empty.
  /// Example: "research"
  @$pb.TagNumber(5)
  $core.String get selectedPhase => $_getSZ(4);
  @$pb.TagNumber(5)
  set selectedPhase($core.String v) { $_setString(4, v); }
  @$pb.TagNumber(5)
  $core.bool hasSelectedPhase() => $_has(4);
  @$pb.TagNumber(5)
  void clearSelectedPhase() => clearField(5);
}

/// What: Prepared routing decision for one prompt.
/// Why: The UI needs structured routing output rather than reimplementing shell
/// heuristics locally.
/// How: Use `kind` and `target_kind` to explain the routing result; submit the
/// original prompt with `SubmitChatInput` when the user confirms.
/// Valid Example:
///   {
///     "kind": "shell.route",
///     "prepared_prompt": "/help",
///     "shell_text": "Show workstation shell help.",
///     "target_kind": "shell.help",
///     "routing_metadata_json": "{\"slash_command\":\"/help\"}",
///     "trace_id": "shell-route-response_84bb59b1",
///     "parent_id": "shell-route-request_0d5aa431"
///   }
class PrepareChatPromptTargetResponse extends $pb.GeneratedMessage {
  factory PrepareChatPromptTargetResponse({
    $core.String? kind,
    $core.String? preparedPrompt,
    $core.String? shellText,
    $core.String? targetKind,
    $core.String? routingMetadataJson,
    $core.String? traceId,
    $core.String? parentId,
  }) {
    final $result = create();
    if (kind != null) {
      $result.kind = kind;
    }
    if (preparedPrompt != null) {
      $result.preparedPrompt = preparedPrompt;
    }
    if (shellText != null) {
      $result.shellText = shellText;
    }
    if (targetKind != null) {
      $result.targetKind = targetKind;
    }
    if (routingMetadataJson != null) {
      $result.routingMetadataJson = routingMetadataJson;
    }
    if (traceId != null) {
      $result.traceId = traceId;
    }
    if (parentId != null) {
      $result.parentId = parentId;
    }
    return $result;
  }
  PrepareChatPromptTargetResponse._() : super();
  factory PrepareChatPromptTargetResponse.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory PrepareChatPromptTargetResponse.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'PrepareChatPromptTargetResponse', package: const $pb.PackageName(_omitMessageNames ? '' : 'workstation'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'kind')
    ..aOS(2, _omitFieldNames ? '' : 'preparedPrompt')
    ..aOS(3, _omitFieldNames ? '' : 'shellText')
    ..aOS(4, _omitFieldNames ? '' : 'targetKind')
    ..aOS(5, _omitFieldNames ? '' : 'routingMetadataJson')
    ..aOS(100, _omitFieldNames ? '' : 'traceId')
    ..aOS(101, _omitFieldNames ? '' : 'parentId')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  PrepareChatPromptTargetResponse clone() => PrepareChatPromptTargetResponse()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  PrepareChatPromptTargetResponse copyWith(void Function(PrepareChatPromptTargetResponse) updates) => super.copyWith((message) => updates(message as PrepareChatPromptTargetResponse)) as PrepareChatPromptTargetResponse;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static PrepareChatPromptTargetResponse create() => PrepareChatPromptTargetResponse._();
  PrepareChatPromptTargetResponse createEmptyInstance() => create();
  static $pb.PbList<PrepareChatPromptTargetResponse> createRepeated() => $pb.PbList<PrepareChatPromptTargetResponse>();
  @$core.pragma('dart2js:noInline')
  static PrepareChatPromptTargetResponse getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<PrepareChatPromptTargetResponse>(create);
  static PrepareChatPromptTargetResponse? _defaultInstance;

  /// What: High-level response kind.
  /// Why: Clients may render different routing banners for different kinds.
  /// How: Treat it as a semantic classifier from the shell service.
  /// Example: "shell.route"
  @$pb.TagNumber(1)
  $core.String get kind => $_getSZ(0);
  @$pb.TagNumber(1)
  set kind($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasKind() => $_has(0);
  @$pb.TagNumber(1)
  void clearKind() => clearField(1);

  /// What: Normalized prompt text ready for submission.
  /// Why: The shell may canonicalize slash commands or routed prompts.
  /// How: Display it as the server's normalized interpretation.
  /// Example: "/help"
  @$pb.TagNumber(2)
  $core.String get preparedPrompt => $_getSZ(1);
  @$pb.TagNumber(2)
  set preparedPrompt($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasPreparedPrompt() => $_has(1);
  @$pb.TagNumber(2)
  void clearPreparedPrompt() => clearField(2);

  /// What: Human-readable shell explanation of the routing target.
  /// Why: Users need an understandable preview of what will happen.
  /// How: Render it inline in the composer or submit confirmation UI.
  /// Example: "Show workstation shell help."
  @$pb.TagNumber(3)
  $core.String get shellText => $_getSZ(2);
  @$pb.TagNumber(3)
  set shellText($core.String v) { $_setString(2, v); }
  @$pb.TagNumber(3)
  $core.bool hasShellText() => $_has(2);
  @$pb.TagNumber(3)
  void clearShellText() => clearField(3);

  /// What: Concrete routing target kind.
  /// Why: Clients may special-case help, slash commands, or LLM routing.
  /// How: Treat it as a stable semantic target identifier.
  /// Example: "shell.help"
  @$pb.TagNumber(4)
  $core.String get targetKind => $_getSZ(3);
  @$pb.TagNumber(4)
  set targetKind($core.String v) { $_setString(3, v); }
  @$pb.TagNumber(4)
  $core.bool hasTargetKind() => $_has(3);
  @$pb.TagNumber(4)
  void clearTargetKind() => clearField(4);

  /// What: Additional routing metadata serialized as JSON.
  /// Why: The server can expose structured details without inflating the proto
  /// shape for every routing branch.
  /// How: Parse it only if the client needs branch-specific rendering.
  /// Example: "{\"slash_command\":\"/help\"}"
  @$pb.TagNumber(5)
  $core.String get routingMetadataJson => $_getSZ(4);
  @$pb.TagNumber(5)
  set routingMetadataJson($core.String v) { $_setString(4, v); }
  @$pb.TagNumber(5)
  $core.bool hasRoutingMetadataJson() => $_has(4);
  @$pb.TagNumber(5)
  void clearRoutingMetadataJson() => clearField(5);

  /// What: Trace id for the routing response.
  /// Why: Prompt-routing decisions participate in host tracing.
  /// How: Log it for diagnostics when needed.
  /// Example: "shell-route-response_84bb59b1"
  @$pb.TagNumber(100)
  $core.String get traceId => $_getSZ(5);
  @$pb.TagNumber(100)
  set traceId($core.String v) { $_setString(5, v); }
  @$pb.TagNumber(100)
  $core.bool hasTraceId() => $_has(5);
  @$pb.TagNumber(100)
  void clearTraceId() => clearField(100);

  /// What: Parent trace id that links back to the routing request.
  /// Why: Trace trees need causal parentage.
  /// How: Treat it as opaque correlation metadata.
  /// Example: "shell-route-request_0d5aa431"
  @$pb.TagNumber(101)
  $core.String get parentId => $_getSZ(6);
  @$pb.TagNumber(101)
  set parentId($core.String v) { $_setString(6, v); }
  @$pb.TagNumber(101)
  $core.bool hasParentId() => $_has(6);
  @$pb.TagNumber(101)
  void clearParentId() => clearField(101);
}

/// What: Request that submits one prompt to the shell service.
/// Why: This is the primary shell execution entrypoint for help, slash
/// commands, and LLM/tool-assisted turns.
/// How: Send the raw prompt and optional execution policy overrides.
/// Valid Example:
///   {
///     "root_path": "/srv/workstations/transit",
///     "client_session_id": "flutter-shell-a",
///     "prompt_text": "/help",
///     "model": "gpt-5.5",
///     "max_tool_rounds": 8,
///     "force_llm_only": false
///   }
class SubmitChatInputRequest extends $pb.GeneratedMessage {
  factory SubmitChatInputRequest({
    $core.String? rootPath,
    $core.String? clientSessionId,
    $core.String? promptText,
    $core.String? model,
    $core.int? maxToolRounds,
    $core.bool? forceLlmOnly,
  }) {
    final $result = create();
    if (rootPath != null) {
      $result.rootPath = rootPath;
    }
    if (clientSessionId != null) {
      $result.clientSessionId = clientSessionId;
    }
    if (promptText != null) {
      $result.promptText = promptText;
    }
    if (model != null) {
      $result.model = model;
    }
    if (maxToolRounds != null) {
      $result.maxToolRounds = maxToolRounds;
    }
    if (forceLlmOnly != null) {
      $result.forceLlmOnly = forceLlmOnly;
    }
    return $result;
  }
  SubmitChatInputRequest._() : super();
  factory SubmitChatInputRequest.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory SubmitChatInputRequest.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'SubmitChatInputRequest', package: const $pb.PackageName(_omitMessageNames ? '' : 'workstation'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'rootPath')
    ..aOS(2, _omitFieldNames ? '' : 'clientSessionId')
    ..aOS(3, _omitFieldNames ? '' : 'promptText')
    ..aOS(4, _omitFieldNames ? '' : 'model')
    ..a<$core.int>(5, _omitFieldNames ? '' : 'maxToolRounds', $pb.PbFieldType.O3)
    ..aOB(6, _omitFieldNames ? '' : 'forceLlmOnly')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  SubmitChatInputRequest clone() => SubmitChatInputRequest()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  SubmitChatInputRequest copyWith(void Function(SubmitChatInputRequest) updates) => super.copyWith((message) => updates(message as SubmitChatInputRequest)) as SubmitChatInputRequest;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static SubmitChatInputRequest create() => SubmitChatInputRequest._();
  SubmitChatInputRequest createEmptyInstance() => create();
  static $pb.PbList<SubmitChatInputRequest> createRepeated() => $pb.PbList<SubmitChatInputRequest>();
  @$core.pragma('dart2js:noInline')
  static SubmitChatInputRequest getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<SubmitChatInputRequest>(create);
  static SubmitChatInputRequest? _defaultInstance;

  /// What: Absolute workstation root path on the server.
  /// Why: Prompt execution is scoped to one workstation instance.
  /// How: Reuse the selected root path.
  /// Example: "/srv/workstations/transit"
  @$pb.TagNumber(1)
  $core.String get rootPath => $_getSZ(0);
  @$pb.TagNumber(1)
  set rootPath($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasRootPath() => $_has(0);
  @$pb.TagNumber(1)
  void clearRootPath() => clearField(1);

  /// What: Stable caller session id.
  /// Why: The server appends turns and session-scoped side effects under one
  /// shell session.
  /// How: Reuse the active shell session id.
  /// Example: "flutter-shell-a"
  @$pb.TagNumber(2)
  $core.String get clientSessionId => $_getSZ(1);
  @$pb.TagNumber(2)
  set clientSessionId($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasClientSessionId() => $_has(1);
  @$pb.TagNumber(2)
  void clearClientSessionId() => clearField(2);

  /// What: Raw user prompt text to execute.
  /// Why: The shell service is the source of truth for prompt interpretation.
  /// How: Send the composer text exactly as the user submitted it.
  /// Example: "/help"
  @$pb.TagNumber(3)
  $core.String get promptText => $_getSZ(2);
  @$pb.TagNumber(3)
  set promptText($core.String v) { $_setString(2, v); }
  @$pb.TagNumber(3)
  $core.bool hasPromptText() => $_has(2);
  @$pb.TagNumber(3)
  void clearPromptText() => clearField(3);

  /// What: Optional explicit model override.
  /// Why: Some clients let advanced users override the default model.
  /// How: Leave empty to use the session default model policy.
  /// Example: "gpt-5.5"
  @$pb.TagNumber(4)
  $core.String get model => $_getSZ(3);
  @$pb.TagNumber(4)
  set model($core.String v) { $_setString(3, v); }
  @$pb.TagNumber(4)
  $core.bool hasModel() => $_has(3);
  @$pb.TagNumber(4)
  void clearModel() => clearField(4);

  /// What: Maximum number of tool rounds permitted for the turn.
  /// Why: Clients need bounded tool execution.
  /// How: Use a positive integer such as 8.
  /// Example: 8
  @$pb.TagNumber(5)
  $core.int get maxToolRounds => $_getIZ(4);
  @$pb.TagNumber(5)
  set maxToolRounds($core.int v) { $_setSignedInt32(4, v); }
  @$pb.TagNumber(5)
  $core.bool hasMaxToolRounds() => $_has(4);
  @$pb.TagNumber(5)
  void clearMaxToolRounds() => clearField(5);

  /// What: Flag that disables tool use and forces LLM-only execution.
  /// Why: Some callers need a purely model-driven turn for debugging or policy.
  /// How: Set true only when intentionally bypassing tool use.
  /// Example: false
  @$pb.TagNumber(6)
  $core.bool get forceLlmOnly => $_getBF(5);
  @$pb.TagNumber(6)
  set forceLlmOnly($core.bool v) { $_setBool(5, v); }
  @$pb.TagNumber(6)
  $core.bool hasForceLlmOnly() => $_has(5);
  @$pb.TagNumber(6)
  void clearForceLlmOnly() => clearField(6);
}

/// What: Result of one shell prompt submission.
/// Why: Clients need both the assistant reply and the new transcript state.
/// How: Append the assistant text to the visible transcript and cache the new
/// snapshot/progress version tokens.
/// Valid Example:
///   {
///     "assistant_text": "Available commands: /help, /exit, /quit",
///     "messages": [
///       {
///         "role": "user",
///         "content": "/help",
///         "timestamp_epoch_ms": 1777780022123
///       },
///       {
///         "role": "shell",
///         "content": "Available commands: /help, /exit, /quit",
///         "timestamp_epoch_ms": 1777780023123
///       }
///     ],
///     "fulfilled_by": "shell.help",
///     "rounds": 0,
///     "tool_receipts_json": "[]",
///     "status_text": "ready",
///     "snapshot_version": "shell-chat-15",
///     "progress_fingerprint": "c9537d2bd4abf311",
///     "trace_id": "shell-submit-response_a245df05",
///     "parent_id": "shell-submit-request_377bea11"
///   }
class SubmitChatInputResponse extends $pb.GeneratedMessage {
  factory SubmitChatInputResponse({
    $core.String? assistantText,
    $core.Iterable<WorkstationChatMessage>? messages,
    $core.String? fulfilledBy,
    $core.int? rounds,
    $core.String? toolReceiptsJson,
    $core.String? statusText,
    $core.String? snapshotVersion,
    $core.String? progressFingerprint,
    $core.String? traceId,
    $core.String? parentId,
  }) {
    final $result = create();
    if (assistantText != null) {
      $result.assistantText = assistantText;
    }
    if (messages != null) {
      $result.messages.addAll(messages);
    }
    if (fulfilledBy != null) {
      $result.fulfilledBy = fulfilledBy;
    }
    if (rounds != null) {
      $result.rounds = rounds;
    }
    if (toolReceiptsJson != null) {
      $result.toolReceiptsJson = toolReceiptsJson;
    }
    if (statusText != null) {
      $result.statusText = statusText;
    }
    if (snapshotVersion != null) {
      $result.snapshotVersion = snapshotVersion;
    }
    if (progressFingerprint != null) {
      $result.progressFingerprint = progressFingerprint;
    }
    if (traceId != null) {
      $result.traceId = traceId;
    }
    if (parentId != null) {
      $result.parentId = parentId;
    }
    return $result;
  }
  SubmitChatInputResponse._() : super();
  factory SubmitChatInputResponse.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory SubmitChatInputResponse.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'SubmitChatInputResponse', package: const $pb.PackageName(_omitMessageNames ? '' : 'workstation'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'assistantText')
    ..pc<WorkstationChatMessage>(2, _omitFieldNames ? '' : 'messages', $pb.PbFieldType.PM, subBuilder: WorkstationChatMessage.create)
    ..aOS(3, _omitFieldNames ? '' : 'fulfilledBy')
    ..a<$core.int>(4, _omitFieldNames ? '' : 'rounds', $pb.PbFieldType.O3)
    ..aOS(5, _omitFieldNames ? '' : 'toolReceiptsJson')
    ..aOS(6, _omitFieldNames ? '' : 'statusText')
    ..aOS(7, _omitFieldNames ? '' : 'snapshotVersion')
    ..aOS(8, _omitFieldNames ? '' : 'progressFingerprint')
    ..aOS(100, _omitFieldNames ? '' : 'traceId')
    ..aOS(101, _omitFieldNames ? '' : 'parentId')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  SubmitChatInputResponse clone() => SubmitChatInputResponse()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  SubmitChatInputResponse copyWith(void Function(SubmitChatInputResponse) updates) => super.copyWith((message) => updates(message as SubmitChatInputResponse)) as SubmitChatInputResponse;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static SubmitChatInputResponse create() => SubmitChatInputResponse._();
  SubmitChatInputResponse createEmptyInstance() => create();
  static $pb.PbList<SubmitChatInputResponse> createRepeated() => $pb.PbList<SubmitChatInputResponse>();
  @$core.pragma('dart2js:noInline')
  static SubmitChatInputResponse getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<SubmitChatInputResponse>(create);
  static SubmitChatInputResponse? _defaultInstance;

  /// What: Top-level assistant reply text for the turn.
  /// Why: Many clients want the final assistant text directly without scanning
  /// the full transcript delta.
  /// How: Render it as the latest assistant/shell response.
  /// Example: "Available commands: /help, /exit, /quit"
  @$pb.TagNumber(1)
  $core.String get assistantText => $_getSZ(0);
  @$pb.TagNumber(1)
  set assistantText($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasAssistantText() => $_has(0);
  @$pb.TagNumber(1)
  void clearAssistantText() => clearField(1);

  /// What: Transcript window after the submitted turn completed.
  /// Why: Clients need the updated visible chat state.
  /// How: Replace or merge the local transcript with this ordered sequence.
  /// Example: [{"role":"user","content":"/help","timestamp_epoch_ms":1777780022123},{"role":"shell","content":"Available commands: /help, /exit, /quit","timestamp_epoch_ms":1777780023123}]
  @$pb.TagNumber(2)
  $core.List<WorkstationChatMessage> get messages => $_getList(1);

  /// What: Execution path that fulfilled the prompt.
  /// Why: Clients may show whether a response came from shell help, a command,
  /// or an LLM/tool loop.
  /// How: Treat it as a semantic execution classifier.
  /// Example: "shell.help"
  @$pb.TagNumber(3)
  $core.String get fulfilledBy => $_getSZ(2);
  @$pb.TagNumber(3)
  set fulfilledBy($core.String v) { $_setString(2, v); }
  @$pb.TagNumber(3)
  $core.bool hasFulfilledBy() => $_has(2);
  @$pb.TagNumber(3)
  void clearFulfilledBy() => clearField(3);

  /// What: Number of tool rounds spent on the turn.
  /// Why: Tool-driven clients need visible bounded-execution accounting.
  /// How: Display or log it as telemetry.
  /// Example: 0
  @$pb.TagNumber(4)
  $core.int get rounds => $_getIZ(3);
  @$pb.TagNumber(4)
  set rounds($core.int v) { $_setSignedInt32(3, v); }
  @$pb.TagNumber(4)
  $core.bool hasRounds() => $_has(3);
  @$pb.TagNumber(4)
  void clearRounds() => clearField(4);

  /// What: Serialized tool receipts as JSON.
  /// Why: The shell can expose structured receipts without duplicating a large
  /// tool receipt schema in this proto.
  /// How: Parse it only when the client needs tool execution details.
  /// Example: "[]"
  @$pb.TagNumber(5)
  $core.String get toolReceiptsJson => $_getSZ(4);
  @$pb.TagNumber(5)
  set toolReceiptsJson($core.String v) { $_setString(4, v); }
  @$pb.TagNumber(5)
  $core.bool hasToolReceiptsJson() => $_has(4);
  @$pb.TagNumber(5)
  void clearToolReceiptsJson() => clearField(5);

  /// What: High-level shell status after the turn.
  /// Why: Clients often display readiness or busy state separately from the
  /// transcript itself.
  /// How: Surface it in the status strip.
  /// Example: "ready"
  @$pb.TagNumber(6)
  $core.String get statusText => $_getSZ(5);
  @$pb.TagNumber(6)
  set statusText($core.String v) { $_setString(5, v); }
  @$pb.TagNumber(6)
  $core.bool hasStatusText() => $_has(5);
  @$pb.TagNumber(6)
  void clearStatusText() => clearField(6);

  /// What: Monotonic version token for the updated transcript snapshot.
  /// Why: Watchers need a stable change token.
  /// How: Cache it and compare it with later watch events.
  /// Example: "shell-chat-15"
  @$pb.TagNumber(7)
  $core.String get snapshotVersion => $_getSZ(6);
  @$pb.TagNumber(7)
  set snapshotVersion($core.String v) { $_setString(6, v); }
  @$pb.TagNumber(7)
  $core.bool hasSnapshotVersion() => $_has(6);
  @$pb.TagNumber(7)
  void clearSnapshotVersion() => clearField(7);

  /// What: Opaque fingerprint of the relevant progress state.
  /// Why: Clients can cheaply detect whether projections changed.
  /// How: Treat it as an opaque checksum.
  /// Example: "c9537d2bd4abf311"
  @$pb.TagNumber(8)
  $core.String get progressFingerprint => $_getSZ(7);
  @$pb.TagNumber(8)
  set progressFingerprint($core.String v) { $_setString(7, v); }
  @$pb.TagNumber(8)
  $core.bool hasProgressFingerprint() => $_has(7);
  @$pb.TagNumber(8)
  void clearProgressFingerprint() => clearField(8);

  /// What: Trace id for the submit response.
  /// Why: Prompt execution must be traceable across shell, tools, and host
  /// layers.
  /// How: Log it for diagnostics when needed.
  /// Example: "shell-submit-response_a245df05"
  @$pb.TagNumber(100)
  $core.String get traceId => $_getSZ(8);
  @$pb.TagNumber(100)
  set traceId($core.String v) { $_setString(8, v); }
  @$pb.TagNumber(100)
  $core.bool hasTraceId() => $_has(8);
  @$pb.TagNumber(100)
  void clearTraceId() => clearField(100);

  /// What: Parent trace id linking back to the submit request.
  /// Why: Trace trees need causal linkage.
  /// How: Treat it as opaque correlation metadata.
  /// Example: "shell-submit-request_377bea11"
  @$pb.TagNumber(101)
  $core.String get parentId => $_getSZ(9);
  @$pb.TagNumber(101)
  set parentId($core.String v) { $_setString(9, v); }
  @$pb.TagNumber(101)
  $core.bool hasParentId() => $_has(9);
  @$pb.TagNumber(101)
  void clearParentId() => clearField(101);
}

/// What: Request that appends an externally produced shell turn.
/// Why: Some hosts already executed work elsewhere and only need to mirror the
/// resulting prompt/assistant pair into the canonical transcript.
/// How: Use it when another UI or host process needs to synchronize the shared
/// transcript without re-running prompt execution.
/// Valid Example:
///   {
///     "root_path": "/srv/workstations/transit",
///     "client_session_id": "flutter-shell-a",
///     "prompt_text": "/help",
///     "assistant_text": "Available commands: /help, /exit, /quit",
///     "assistant_role": "shell"
///   }
class AppendShellTurnRequest extends $pb.GeneratedMessage {
  factory AppendShellTurnRequest({
    $core.String? rootPath,
    $core.String? clientSessionId,
    $core.String? promptText,
    $core.String? assistantText,
    $core.String? assistantRole,
  }) {
    final $result = create();
    if (rootPath != null) {
      $result.rootPath = rootPath;
    }
    if (clientSessionId != null) {
      $result.clientSessionId = clientSessionId;
    }
    if (promptText != null) {
      $result.promptText = promptText;
    }
    if (assistantText != null) {
      $result.assistantText = assistantText;
    }
    if (assistantRole != null) {
      $result.assistantRole = assistantRole;
    }
    return $result;
  }
  AppendShellTurnRequest._() : super();
  factory AppendShellTurnRequest.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory AppendShellTurnRequest.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'AppendShellTurnRequest', package: const $pb.PackageName(_omitMessageNames ? '' : 'workstation'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'rootPath')
    ..aOS(2, _omitFieldNames ? '' : 'clientSessionId')
    ..aOS(3, _omitFieldNames ? '' : 'promptText')
    ..aOS(4, _omitFieldNames ? '' : 'assistantText')
    ..aOS(5, _omitFieldNames ? '' : 'assistantRole')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  AppendShellTurnRequest clone() => AppendShellTurnRequest()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  AppendShellTurnRequest copyWith(void Function(AppendShellTurnRequest) updates) => super.copyWith((message) => updates(message as AppendShellTurnRequest)) as AppendShellTurnRequest;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static AppendShellTurnRequest create() => AppendShellTurnRequest._();
  AppendShellTurnRequest createEmptyInstance() => create();
  static $pb.PbList<AppendShellTurnRequest> createRepeated() => $pb.PbList<AppendShellTurnRequest>();
  @$core.pragma('dart2js:noInline')
  static AppendShellTurnRequest getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<AppendShellTurnRequest>(create);
  static AppendShellTurnRequest? _defaultInstance;

  /// What: Absolute workstation root path on the server.
  /// Why: Turn appends are scoped to one workstation instance.
  /// How: Reuse the selected root path.
  /// Example: "/srv/workstations/transit"
  @$pb.TagNumber(1)
  $core.String get rootPath => $_getSZ(0);
  @$pb.TagNumber(1)
  set rootPath($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasRootPath() => $_has(0);
  @$pb.TagNumber(1)
  void clearRootPath() => clearField(1);

  /// What: Stable caller session id.
  /// Why: Transcript synchronization still belongs to one logical shell client.
  /// How: Reuse the active shell session id.
  /// Example: "flutter-shell-a"
  @$pb.TagNumber(2)
  $core.String get clientSessionId => $_getSZ(1);
  @$pb.TagNumber(2)
  set clientSessionId($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasClientSessionId() => $_has(1);
  @$pb.TagNumber(2)
  void clearClientSessionId() => clearField(2);

  /// What: Prompt text that produced the appended assistant output.
  /// Why: The canonical transcript stores both sides of the turn.
  /// How: Leave empty only when appending assistant-only status text.
  /// Example: "/help"
  @$pb.TagNumber(3)
  $core.String get promptText => $_getSZ(2);
  @$pb.TagNumber(3)
  set promptText($core.String v) { $_setString(2, v); }
  @$pb.TagNumber(3)
  $core.bool hasPromptText() => $_has(2);
  @$pb.TagNumber(3)
  void clearPromptText() => clearField(3);

  /// What: Assistant or shell response text to append.
  /// Why: This is the output that should appear in the transcript.
  /// How: Supply the final text exactly as it should be rendered.
  /// Example: "Available commands: /help, /exit, /quit"
  @$pb.TagNumber(4)
  $core.String get assistantText => $_getSZ(3);
  @$pb.TagNumber(4)
  set assistantText($core.String v) { $_setString(3, v); }
  @$pb.TagNumber(4)
  $core.bool hasAssistantText() => $_has(3);
  @$pb.TagNumber(4)
  void clearAssistantText() => clearField(4);

  /// What: Semantic role for the appended assistant text.
  /// Why: Transcript styling depends on whether the output is from `shell`,
  /// `assistant`, or another supported role.
  /// How: Set it to the role the UI should render.
  /// Example: "shell"
  @$pb.TagNumber(5)
  $core.String get assistantRole => $_getSZ(4);
  @$pb.TagNumber(5)
  set assistantRole($core.String v) { $_setString(4, v); }
  @$pb.TagNumber(5)
  $core.bool hasAssistantRole() => $_has(4);
  @$pb.TagNumber(5)
  void clearAssistantRole() => clearField(5);
}

/// What: Response returned after appending a shell turn.
/// Why: Clients need the canonical transcript snapshot after the append.
/// How: Replace or merge local transcript state with the returned snapshot.
/// Valid Example:
///   {
///     "snapshot": {
///       "messages": [
///         {
///           "role": "shell",
///           "content": "Available commands: /help, /exit, /quit",
///           "timestamp_epoch_ms": 1777780023123
///         }
///       ],
///       "session_status": "ready",
///       "snapshot_version": "shell-chat-16",
///       "progress_fingerprint": "a5110d6fbd08f4c4"
///     },
///     "trace_id": "shell-append-turn-response_e859e2b4",
///     "parent_id": "shell-append-turn-request_9dd4cc0a"
///   }
class AppendShellTurnResponse extends $pb.GeneratedMessage {
  factory AppendShellTurnResponse({
    ChatSnapshotResponse? snapshot,
    $core.String? traceId,
    $core.String? parentId,
  }) {
    final $result = create();
    if (snapshot != null) {
      $result.snapshot = snapshot;
    }
    if (traceId != null) {
      $result.traceId = traceId;
    }
    if (parentId != null) {
      $result.parentId = parentId;
    }
    return $result;
  }
  AppendShellTurnResponse._() : super();
  factory AppendShellTurnResponse.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory AppendShellTurnResponse.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'AppendShellTurnResponse', package: const $pb.PackageName(_omitMessageNames ? '' : 'workstation'), createEmptyInstance: create)
    ..aOM<ChatSnapshotResponse>(1, _omitFieldNames ? '' : 'snapshot', subBuilder: ChatSnapshotResponse.create)
    ..aOS(100, _omitFieldNames ? '' : 'traceId')
    ..aOS(101, _omitFieldNames ? '' : 'parentId')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  AppendShellTurnResponse clone() => AppendShellTurnResponse()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  AppendShellTurnResponse copyWith(void Function(AppendShellTurnResponse) updates) => super.copyWith((message) => updates(message as AppendShellTurnResponse)) as AppendShellTurnResponse;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static AppendShellTurnResponse create() => AppendShellTurnResponse._();
  AppendShellTurnResponse createEmptyInstance() => create();
  static $pb.PbList<AppendShellTurnResponse> createRepeated() => $pb.PbList<AppendShellTurnResponse>();
  @$core.pragma('dart2js:noInline')
  static AppendShellTurnResponse getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<AppendShellTurnResponse>(create);
  static AppendShellTurnResponse? _defaultInstance;

  /// What: Canonical transcript snapshot after the append completed.
  /// Why: The client needs the server-authoritative chat state.
  /// How: Use it to refresh the transcript immediately.
  /// Example: {"messages":[{"role":"shell","content":"Available commands: /help, /exit, /quit","timestamp_epoch_ms":1777780023123}],"session_status":"ready","snapshot_version":"shell-chat-16","progress_fingerprint":"a5110d6fbd08f4c4"}
  @$pb.TagNumber(1)
  ChatSnapshotResponse get snapshot => $_getN(0);
  @$pb.TagNumber(1)
  set snapshot(ChatSnapshotResponse v) { setField(1, v); }
  @$pb.TagNumber(1)
  $core.bool hasSnapshot() => $_has(0);
  @$pb.TagNumber(1)
  void clearSnapshot() => clearField(1);
  @$pb.TagNumber(1)
  ChatSnapshotResponse ensureSnapshot() => $_ensure(0);

  /// What: Trace id for the append response.
  /// Why: Transcript synchronization events must remain traceable.
  /// How: Log it if append diagnostics are needed.
  /// Example: "shell-append-turn-response_e859e2b4"
  @$pb.TagNumber(100)
  $core.String get traceId => $_getSZ(1);
  @$pb.TagNumber(100)
  set traceId($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(100)
  $core.bool hasTraceId() => $_has(1);
  @$pb.TagNumber(100)
  void clearTraceId() => clearField(100);

  /// What: Parent trace id linking to the append request.
  /// Why: Trace trees need response/request linkage.
  /// How: Treat it as opaque correlation metadata.
  /// Example: "shell-append-turn-request_9dd4cc0a"
  @$pb.TagNumber(101)
  $core.String get parentId => $_getSZ(2);
  @$pb.TagNumber(101)
  set parentId($core.String v) { $_setString(2, v); }
  @$pb.TagNumber(101)
  $core.bool hasParentId() => $_has(2);
  @$pb.TagNumber(101)
  void clearParentId() => clearField(101);
}

/// What: Request for the recent activity text panel.
/// Why: Activity is rendered separately from the chat transcript but still
/// belongs to the shell surface.
/// How: Call it on initial load or use the watch stream for later deltas.
/// Valid Example:
///   {
///     "root_path": "/srv/workstations/transit",
///     "client_session_id": "flutter-shell-a",
///     "limit": 120
///   }
class ActivityViewRequest extends $pb.GeneratedMessage {
  factory ActivityViewRequest({
    $core.String? rootPath,
    $core.String? clientSessionId,
    $core.int? limit,
  }) {
    final $result = create();
    if (rootPath != null) {
      $result.rootPath = rootPath;
    }
    if (clientSessionId != null) {
      $result.clientSessionId = clientSessionId;
    }
    if (limit != null) {
      $result.limit = limit;
    }
    return $result;
  }
  ActivityViewRequest._() : super();
  factory ActivityViewRequest.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory ActivityViewRequest.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'ActivityViewRequest', package: const $pb.PackageName(_omitMessageNames ? '' : 'workstation'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'rootPath')
    ..aOS(2, _omitFieldNames ? '' : 'clientSessionId')
    ..a<$core.int>(3, _omitFieldNames ? '' : 'limit', $pb.PbFieldType.O3)
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  ActivityViewRequest clone() => ActivityViewRequest()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  ActivityViewRequest copyWith(void Function(ActivityViewRequest) updates) => super.copyWith((message) => updates(message as ActivityViewRequest)) as ActivityViewRequest;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static ActivityViewRequest create() => ActivityViewRequest._();
  ActivityViewRequest createEmptyInstance() => create();
  static $pb.PbList<ActivityViewRequest> createRepeated() => $pb.PbList<ActivityViewRequest>();
  @$core.pragma('dart2js:noInline')
  static ActivityViewRequest getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<ActivityViewRequest>(create);
  static ActivityViewRequest? _defaultInstance;

  /// What: Absolute workstation root path on the server.
  /// Why: Activity is scoped to one workstation instance.
  /// How: Reuse the selected root path.
  /// Example: "/srv/workstations/transit"
  @$pb.TagNumber(1)
  $core.String get rootPath => $_getSZ(0);
  @$pb.TagNumber(1)
  set rootPath($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasRootPath() => $_has(0);
  @$pb.TagNumber(1)
  void clearRootPath() => clearField(1);

  /// What: Stable caller session id.
  /// Why: Activity polling participates in one shell session context.
  /// How: Reuse the active shell session id.
  /// Example: "flutter-shell-a"
  @$pb.TagNumber(2)
  $core.String get clientSessionId => $_getSZ(1);
  @$pb.TagNumber(2)
  set clientSessionId($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasClientSessionId() => $_has(1);
  @$pb.TagNumber(2)
  void clearClientSessionId() => clearField(2);

  /// What: Maximum number of activity lines to return.
  /// Why: Clients typically need a recent bounded feed rather than the entire
  /// activity log.
  /// How: Use a positive value such as 120.
  /// Example: 120
  @$pb.TagNumber(3)
  $core.int get limit => $_getIZ(2);
  @$pb.TagNumber(3)
  set limit($core.int v) { $_setSignedInt32(2, v); }
  @$pb.TagNumber(3)
  $core.bool hasLimit() => $_has(2);
  @$pb.TagNumber(3)
  void clearLimit() => clearField(3);
}

/// What: Request for the permissions panel text.
/// Why: Permission state is rendered as an auxiliary shell panel.
/// How: Call it on initial load or refresh via the shell watch stream.
/// Valid Example:
///   {
///     "root_path": "/srv/workstations/transit",
///     "client_session_id": "flutter-shell-a"
///   }
class PermissionsViewRequest extends $pb.GeneratedMessage {
  factory PermissionsViewRequest({
    $core.String? rootPath,
    $core.String? clientSessionId,
  }) {
    final $result = create();
    if (rootPath != null) {
      $result.rootPath = rootPath;
    }
    if (clientSessionId != null) {
      $result.clientSessionId = clientSessionId;
    }
    return $result;
  }
  PermissionsViewRequest._() : super();
  factory PermissionsViewRequest.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory PermissionsViewRequest.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'PermissionsViewRequest', package: const $pb.PackageName(_omitMessageNames ? '' : 'workstation'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'rootPath')
    ..aOS(2, _omitFieldNames ? '' : 'clientSessionId')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  PermissionsViewRequest clone() => PermissionsViewRequest()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  PermissionsViewRequest copyWith(void Function(PermissionsViewRequest) updates) => super.copyWith((message) => updates(message as PermissionsViewRequest)) as PermissionsViewRequest;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static PermissionsViewRequest create() => PermissionsViewRequest._();
  PermissionsViewRequest createEmptyInstance() => create();
  static $pb.PbList<PermissionsViewRequest> createRepeated() => $pb.PbList<PermissionsViewRequest>();
  @$core.pragma('dart2js:noInline')
  static PermissionsViewRequest getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<PermissionsViewRequest>(create);
  static PermissionsViewRequest? _defaultInstance;

  /// What: Absolute workstation root path on the server.
  /// Why: Permission data belongs to one workstation instance.
  /// How: Reuse the selected root path.
  /// Example: "/srv/workstations/transit"
  @$pb.TagNumber(1)
  $core.String get rootPath => $_getSZ(0);
  @$pb.TagNumber(1)
  set rootPath($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasRootPath() => $_has(0);
  @$pb.TagNumber(1)
  void clearRootPath() => clearField(1);

  /// What: Stable caller session id.
  /// Why: Permission rendering can still be session-scoped.
  /// How: Reuse the active shell session id.
  /// Example: "flutter-shell-a"
  @$pb.TagNumber(2)
  $core.String get clientSessionId => $_getSZ(1);
  @$pb.TagNumber(2)
  set clientSessionId($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasClientSessionId() => $_has(1);
  @$pb.TagNumber(2)
  void clearClientSessionId() => clearField(2);
}

/// What: Request for the skills panel text.
/// Why: Skills are displayed as a shell-side textual catalog.
/// How: Provide an optional short filter query.
/// Valid Example:
///   {
///     "root_path": "/srv/workstations/transit",
///     "client_session_id": "flutter-shell-a",
///     "query": "markdown"
///   }
class SkillsViewRequest extends $pb.GeneratedMessage {
  factory SkillsViewRequest({
    $core.String? rootPath,
    $core.String? clientSessionId,
    $core.String? query,
  }) {
    final $result = create();
    if (rootPath != null) {
      $result.rootPath = rootPath;
    }
    if (clientSessionId != null) {
      $result.clientSessionId = clientSessionId;
    }
    if (query != null) {
      $result.query = query;
    }
    return $result;
  }
  SkillsViewRequest._() : super();
  factory SkillsViewRequest.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory SkillsViewRequest.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'SkillsViewRequest', package: const $pb.PackageName(_omitMessageNames ? '' : 'workstation'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'rootPath')
    ..aOS(2, _omitFieldNames ? '' : 'clientSessionId')
    ..aOS(3, _omitFieldNames ? '' : 'query')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  SkillsViewRequest clone() => SkillsViewRequest()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  SkillsViewRequest copyWith(void Function(SkillsViewRequest) updates) => super.copyWith((message) => updates(message as SkillsViewRequest)) as SkillsViewRequest;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static SkillsViewRequest create() => SkillsViewRequest._();
  SkillsViewRequest createEmptyInstance() => create();
  static $pb.PbList<SkillsViewRequest> createRepeated() => $pb.PbList<SkillsViewRequest>();
  @$core.pragma('dart2js:noInline')
  static SkillsViewRequest getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<SkillsViewRequest>(create);
  static SkillsViewRequest? _defaultInstance;

  /// What: Absolute workstation root path on the server.
  /// Why: Skill catalog state belongs to one workstation instance.
  /// How: Reuse the selected root path.
  /// Example: "/srv/workstations/transit"
  @$pb.TagNumber(1)
  $core.String get rootPath => $_getSZ(0);
  @$pb.TagNumber(1)
  set rootPath($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasRootPath() => $_has(0);
  @$pb.TagNumber(1)
  void clearRootPath() => clearField(1);

  /// What: Stable caller session id.
  /// Why: Skill panel refreshes belong to one shell session context.
  /// How: Reuse the active shell session id.
  /// Example: "flutter-shell-a"
  @$pb.TagNumber(2)
  $core.String get clientSessionId => $_getSZ(1);
  @$pb.TagNumber(2)
  set clientSessionId($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasClientSessionId() => $_has(1);
  @$pb.TagNumber(2)
  void clearClientSessionId() => clearField(2);

  /// What: Optional short filter query.
  /// Why: Clients often need a narrowed skill catalog view.
  /// How: Leave empty for the full rendered skills panel.
  /// Example: "markdown"
  @$pb.TagNumber(3)
  $core.String get query => $_getSZ(2);
  @$pb.TagNumber(3)
  set query($core.String v) { $_setString(2, v); }
  @$pb.TagNumber(3)
  $core.bool hasQuery() => $_has(2);
  @$pb.TagNumber(3)
  void clearQuery() => clearField(3);
}

/// What: Generic text panel view with version markers.
/// Why: Activity, permissions, skills, and status panels share the same basic
/// shape: rendered text plus snapshot metadata.
/// How: Render `text` verbatim and cache the version markers for incremental
/// updates.
/// Valid Example:
///   {
///     "text": "Mode: ready\nAllowed capabilities: ws.skill.catalog",
///     "snapshot_version": "permissions-4",
///     "progress_fingerprint": "bf8b7db74101f4de",
///     "trace_id": "shell-text-view_13cddce1",
///     "parent_id": "shell-text-request_37ac77ba"
///   }
class ShellTextView extends $pb.GeneratedMessage {
  factory ShellTextView({
    $core.String? text,
    $core.String? snapshotVersion,
    $core.String? progressFingerprint,
    $core.String? traceId,
    $core.String? parentId,
  }) {
    final $result = create();
    if (text != null) {
      $result.text = text;
    }
    if (snapshotVersion != null) {
      $result.snapshotVersion = snapshotVersion;
    }
    if (progressFingerprint != null) {
      $result.progressFingerprint = progressFingerprint;
    }
    if (traceId != null) {
      $result.traceId = traceId;
    }
    if (parentId != null) {
      $result.parentId = parentId;
    }
    return $result;
  }
  ShellTextView._() : super();
  factory ShellTextView.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory ShellTextView.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'ShellTextView', package: const $pb.PackageName(_omitMessageNames ? '' : 'workstation'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'text')
    ..aOS(2, _omitFieldNames ? '' : 'snapshotVersion')
    ..aOS(3, _omitFieldNames ? '' : 'progressFingerprint')
    ..aOS(100, _omitFieldNames ? '' : 'traceId')
    ..aOS(101, _omitFieldNames ? '' : 'parentId')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  ShellTextView clone() => ShellTextView()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  ShellTextView copyWith(void Function(ShellTextView) updates) => super.copyWith((message) => updates(message as ShellTextView)) as ShellTextView;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static ShellTextView create() => ShellTextView._();
  ShellTextView createEmptyInstance() => create();
  static $pb.PbList<ShellTextView> createRepeated() => $pb.PbList<ShellTextView>();
  @$core.pragma('dart2js:noInline')
  static ShellTextView getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<ShellTextView>(create);
  static ShellTextView? _defaultInstance;

  /// What: Fully rendered panel text.
  /// Why: These auxiliary panels are delivered as pre-rendered textual
  /// projections.
  /// How: Display it in the matching panel with monospaced styling.
  /// Example: "Mode: ready\nAllowed capabilities: ws.skill.catalog"
  @$pb.TagNumber(1)
  $core.String get text => $_getSZ(0);
  @$pb.TagNumber(1)
  set text($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasText() => $_has(0);
  @$pb.TagNumber(1)
  void clearText() => clearField(1);

  /// What: Monotonic version token for the panel snapshot.
  /// Why: Watch clients need to know whether a panel changed.
  /// How: Cache it and compare it with later watch events.
  /// Example: "permissions-4"
  @$pb.TagNumber(2)
  $core.String get snapshotVersion => $_getSZ(1);
  @$pb.TagNumber(2)
  set snapshotVersion($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasSnapshotVersion() => $_has(1);
  @$pb.TagNumber(2)
  void clearSnapshotVersion() => clearField(2);

  /// What: Opaque fingerprint of the related progress state.
  /// Why: Clients can cheaply detect whether the projection is stale.
  /// How: Treat it as an opaque checksum.
  /// Example: "bf8b7db74101f4de"
  @$pb.TagNumber(3)
  $core.String get progressFingerprint => $_getSZ(2);
  @$pb.TagNumber(3)
  set progressFingerprint($core.String v) { $_setString(2, v); }
  @$pb.TagNumber(3)
  $core.bool hasProgressFingerprint() => $_has(2);
  @$pb.TagNumber(3)
  void clearProgressFingerprint() => clearField(3);

  /// What: Trace id for the panel response.
  /// Why: Auxiliary panel fetches are part of traceable host activity.
  /// How: Log it if panel diagnostics are needed.
  /// Example: "shell-text-view_13cddce1"
  @$pb.TagNumber(100)
  $core.String get traceId => $_getSZ(3);
  @$pb.TagNumber(100)
  set traceId($core.String v) { $_setString(3, v); }
  @$pb.TagNumber(100)
  $core.bool hasTraceId() => $_has(3);
  @$pb.TagNumber(100)
  void clearTraceId() => clearField(100);

  /// What: Parent trace id linking back to the initiating request.
  /// Why: Trace trees need causal parentage.
  /// How: Treat it as opaque correlation metadata.
  /// Example: "shell-text-request_37ac77ba"
  @$pb.TagNumber(101)
  $core.String get parentId => $_getSZ(4);
  @$pb.TagNumber(101)
  set parentId($core.String v) { $_setString(4, v); }
  @$pb.TagNumber(101)
  $core.bool hasParentId() => $_has(4);
  @$pb.TagNumber(101)
  void clearParentId() => clearField(101);
}

/// What: Request that opens a server-streamed shell watch channel.
/// Why: Clients need incremental updates without polling every panel
/// continuously.
/// How: Call it after the initial snapshot load and supply the last seen chat
/// snapshot version when resuming.
/// Valid Example:
///   {
///     "root_path": "/srv/workstations/transit",
///     "client_session_id": "flutter-shell-a",
///     "last_seen_version": "shell-chat-15"
///   }
class WatchWorkstationShellRequest extends $pb.GeneratedMessage {
  factory WatchWorkstationShellRequest({
    $core.String? rootPath,
    $core.String? clientSessionId,
    $core.String? lastSeenVersion,
  }) {
    final $result = create();
    if (rootPath != null) {
      $result.rootPath = rootPath;
    }
    if (clientSessionId != null) {
      $result.clientSessionId = clientSessionId;
    }
    if (lastSeenVersion != null) {
      $result.lastSeenVersion = lastSeenVersion;
    }
    return $result;
  }
  WatchWorkstationShellRequest._() : super();
  factory WatchWorkstationShellRequest.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory WatchWorkstationShellRequest.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'WatchWorkstationShellRequest', package: const $pb.PackageName(_omitMessageNames ? '' : 'workstation'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'rootPath')
    ..aOS(2, _omitFieldNames ? '' : 'clientSessionId')
    ..aOS(3, _omitFieldNames ? '' : 'lastSeenVersion')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  WatchWorkstationShellRequest clone() => WatchWorkstationShellRequest()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  WatchWorkstationShellRequest copyWith(void Function(WatchWorkstationShellRequest) updates) => super.copyWith((message) => updates(message as WatchWorkstationShellRequest)) as WatchWorkstationShellRequest;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static WatchWorkstationShellRequest create() => WatchWorkstationShellRequest._();
  WatchWorkstationShellRequest createEmptyInstance() => create();
  static $pb.PbList<WatchWorkstationShellRequest> createRepeated() => $pb.PbList<WatchWorkstationShellRequest>();
  @$core.pragma('dart2js:noInline')
  static WatchWorkstationShellRequest getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<WatchWorkstationShellRequest>(create);
  static WatchWorkstationShellRequest? _defaultInstance;

  /// What: Absolute workstation root path on the server.
  /// Why: The watch stream is scoped to one workstation instance.
  /// How: Reuse the selected root path.
  /// Example: "/srv/workstations/transit"
  @$pb.TagNumber(1)
  $core.String get rootPath => $_getSZ(0);
  @$pb.TagNumber(1)
  set rootPath($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasRootPath() => $_has(0);
  @$pb.TagNumber(1)
  void clearRootPath() => clearField(1);

  /// What: Stable caller session id.
  /// Why: Watch state is maintained per client shell session.
  /// How: Reuse the active shell session id.
  /// Example: "flutter-shell-a"
  @$pb.TagNumber(2)
  $core.String get clientSessionId => $_getSZ(1);
  @$pb.TagNumber(2)
  set clientSessionId($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasClientSessionId() => $_has(1);
  @$pb.TagNumber(2)
  void clearClientSessionId() => clearField(2);

  /// What: Last chat snapshot version already observed by the client.
  /// Why: The server can decide whether to emit only fresh deltas or a new
  /// initial snapshot.
  /// How: Leave empty on the first watch call; reuse the last known version
  /// after reconnect.
  /// Example: "shell-chat-15"
  @$pb.TagNumber(3)
  $core.String get lastSeenVersion => $_getSZ(2);
  @$pb.TagNumber(3)
  set lastSeenVersion($core.String v) { $_setString(2, v); }
  @$pb.TagNumber(3)
  $core.bool hasLastSeenVersion() => $_has(2);
  @$pb.TagNumber(3)
  void clearLastSeenVersion() => clearField(3);
}

enum WorkstationShellWatchEvent_Payload {
  chatSnapshot, 
  activityView, 
  permissionsView, 
  skillsView, 
  statusView, 
  notSet
}

/// What: One streamed update from the shell watch channel.
/// Why: The shell watch API multiplexes several projection channels over one
/// stream.
/// How: Inspect `event_kind`, `channel_key`, and the populated `payload`
/// variant; then update the matching local panel.
/// Valid Example Sequence:
///   1.
///     {
///       "event_kind": "initial",
///       "channel_key": "shell/chat",
///       "sequence": 0,
///       "snapshot_version": "shell-chat-15",
///       "progress_fingerprint": "c9537d2bd4abf311",
///       "chat_snapshot": {
///         "messages": [
///           {
///             "role": "shell",
///             "content": "Available commands: /help, /exit, /quit",
///             "timestamp_epoch_ms": 1777780023123
///           }
///         ],
///         "session_status": "ready",
///         "snapshot_version": "shell-chat-15",
///         "progress_fingerprint": "c9537d2bd4abf311"
///       }
///     }
///   2.
///     {
///       "event_kind": "workstation_activity_changed",
///       "channel_key": "shell/activity",
///       "sequence": 1,
///       "snapshot_version": "activity-9",
///       "progress_fingerprint": "c9537d2bd4abf311",
///       "activity_view": {
///         "text": "Started /help",
///         "snapshot_version": "activity-9",
///         "progress_fingerprint": "c9537d2bd4abf311"
///       }
///     }
class WorkstationShellWatchEvent extends $pb.GeneratedMessage {
  factory WorkstationShellWatchEvent({
    $core.String? eventKind,
    $core.String? channelKey,
    $fixnum.Int64? sequence,
    $core.String? snapshotVersion,
    $core.String? progressFingerprint,
    ChatSnapshotResponse? chatSnapshot,
    ShellTextView? activityView,
    ShellTextView? permissionsView,
    ShellTextView? skillsView,
    ShellTextView? statusView,
    $core.String? traceId,
    $core.String? parentId,
  }) {
    final $result = create();
    if (eventKind != null) {
      $result.eventKind = eventKind;
    }
    if (channelKey != null) {
      $result.channelKey = channelKey;
    }
    if (sequence != null) {
      $result.sequence = sequence;
    }
    if (snapshotVersion != null) {
      $result.snapshotVersion = snapshotVersion;
    }
    if (progressFingerprint != null) {
      $result.progressFingerprint = progressFingerprint;
    }
    if (chatSnapshot != null) {
      $result.chatSnapshot = chatSnapshot;
    }
    if (activityView != null) {
      $result.activityView = activityView;
    }
    if (permissionsView != null) {
      $result.permissionsView = permissionsView;
    }
    if (skillsView != null) {
      $result.skillsView = skillsView;
    }
    if (statusView != null) {
      $result.statusView = statusView;
    }
    if (traceId != null) {
      $result.traceId = traceId;
    }
    if (parentId != null) {
      $result.parentId = parentId;
    }
    return $result;
  }
  WorkstationShellWatchEvent._() : super();
  factory WorkstationShellWatchEvent.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory WorkstationShellWatchEvent.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static const $core.Map<$core.int, WorkstationShellWatchEvent_Payload> _WorkstationShellWatchEvent_PayloadByTag = {
    10 : WorkstationShellWatchEvent_Payload.chatSnapshot,
    11 : WorkstationShellWatchEvent_Payload.activityView,
    12 : WorkstationShellWatchEvent_Payload.permissionsView,
    13 : WorkstationShellWatchEvent_Payload.skillsView,
    14 : WorkstationShellWatchEvent_Payload.statusView,
    0 : WorkstationShellWatchEvent_Payload.notSet
  };
  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'WorkstationShellWatchEvent', package: const $pb.PackageName(_omitMessageNames ? '' : 'workstation'), createEmptyInstance: create)
    ..oo(0, [10, 11, 12, 13, 14])
    ..aOS(1, _omitFieldNames ? '' : 'eventKind')
    ..aOS(2, _omitFieldNames ? '' : 'channelKey')
    ..aInt64(3, _omitFieldNames ? '' : 'sequence')
    ..aOS(4, _omitFieldNames ? '' : 'snapshotVersion')
    ..aOS(5, _omitFieldNames ? '' : 'progressFingerprint')
    ..aOM<ChatSnapshotResponse>(10, _omitFieldNames ? '' : 'chatSnapshot', subBuilder: ChatSnapshotResponse.create)
    ..aOM<ShellTextView>(11, _omitFieldNames ? '' : 'activityView', subBuilder: ShellTextView.create)
    ..aOM<ShellTextView>(12, _omitFieldNames ? '' : 'permissionsView', subBuilder: ShellTextView.create)
    ..aOM<ShellTextView>(13, _omitFieldNames ? '' : 'skillsView', subBuilder: ShellTextView.create)
    ..aOM<ShellTextView>(14, _omitFieldNames ? '' : 'statusView', subBuilder: ShellTextView.create)
    ..aOS(100, _omitFieldNames ? '' : 'traceId')
    ..aOS(101, _omitFieldNames ? '' : 'parentId')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  WorkstationShellWatchEvent clone() => WorkstationShellWatchEvent()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  WorkstationShellWatchEvent copyWith(void Function(WorkstationShellWatchEvent) updates) => super.copyWith((message) => updates(message as WorkstationShellWatchEvent)) as WorkstationShellWatchEvent;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static WorkstationShellWatchEvent create() => WorkstationShellWatchEvent._();
  WorkstationShellWatchEvent createEmptyInstance() => create();
  static $pb.PbList<WorkstationShellWatchEvent> createRepeated() => $pb.PbList<WorkstationShellWatchEvent>();
  @$core.pragma('dart2js:noInline')
  static WorkstationShellWatchEvent getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<WorkstationShellWatchEvent>(create);
  static WorkstationShellWatchEvent? _defaultInstance;

  WorkstationShellWatchEvent_Payload whichPayload() => _WorkstationShellWatchEvent_PayloadByTag[$_whichOneof(0)]!;
  void clearPayload() => clearField($_whichOneof(0));

  /// What: Semantic event kind.
  /// Why: Clients need to distinguish initial snapshots from later changes.
  /// How: Treat it as the top-level stream event classifier.
  /// Example: "initial"
  @$pb.TagNumber(1)
  $core.String get eventKind => $_getSZ(0);
  @$pb.TagNumber(1)
  set eventKind($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasEventKind() => $_has(0);
  @$pb.TagNumber(1)
  void clearEventKind() => clearField(1);

  /// What: Stream sub-channel identifier.
  /// Why: One shell watch stream multiplexes chat and auxiliary panels.
  /// How: Route the payload to the panel identified by this key.
  /// Example: "shell/chat"
  @$pb.TagNumber(2)
  $core.String get channelKey => $_getSZ(1);
  @$pb.TagNumber(2)
  set channelKey($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasChannelKey() => $_has(1);
  @$pb.TagNumber(2)
  void clearChannelKey() => clearField(2);

  /// What: Monotonic sequence number within the watch channel.
  /// Why: Clients can ignore out-of-order or duplicate events.
  /// How: Track the latest applied sequence per channel.
  /// Example: 0
  @$pb.TagNumber(3)
  $fixnum.Int64 get sequence => $_getI64(2);
  @$pb.TagNumber(3)
  set sequence($fixnum.Int64 v) { $_setInt64(2, v); }
  @$pb.TagNumber(3)
  $core.bool hasSequence() => $_has(2);
  @$pb.TagNumber(3)
  void clearSequence() => clearField(3);

  /// What: Snapshot version for the payload carried by this event.
  /// Why: Clients need stable version markers after each update.
  /// How: Cache it for resume or staleness checks.
  /// Example: "shell-chat-15"
  @$pb.TagNumber(4)
  $core.String get snapshotVersion => $_getSZ(3);
  @$pb.TagNumber(4)
  set snapshotVersion($core.String v) { $_setString(3, v); }
  @$pb.TagNumber(4)
  $core.bool hasSnapshotVersion() => $_has(3);
  @$pb.TagNumber(4)
  void clearSnapshotVersion() => clearField(4);

  /// What: Opaque fingerprint of the related progress state.
  /// Why: Clients can cheaply detect whether projections changed.
  /// How: Treat it as an opaque checksum.
  /// Example: "c9537d2bd4abf311"
  @$pb.TagNumber(5)
  $core.String get progressFingerprint => $_getSZ(4);
  @$pb.TagNumber(5)
  set progressFingerprint($core.String v) { $_setString(4, v); }
  @$pb.TagNumber(5)
  $core.bool hasProgressFingerprint() => $_has(4);
  @$pb.TagNumber(5)
  void clearProgressFingerprint() => clearField(5);

  /// What: Updated transcript snapshot.
  /// Why: Chat changes are delivered as full structured transcript snapshots.
  /// How: Replace or merge the transcript with this snapshot.
  /// Example: {"messages":[{"role":"shell","content":"Available commands: /help, /exit, /quit","timestamp_epoch_ms":1777780023123}],"session_status":"ready","snapshot_version":"shell-chat-15","progress_fingerprint":"c9537d2bd4abf311"}
  @$pb.TagNumber(10)
  ChatSnapshotResponse get chatSnapshot => $_getN(5);
  @$pb.TagNumber(10)
  set chatSnapshot(ChatSnapshotResponse v) { setField(10, v); }
  @$pb.TagNumber(10)
  $core.bool hasChatSnapshot() => $_has(5);
  @$pb.TagNumber(10)
  void clearChatSnapshot() => clearField(10);
  @$pb.TagNumber(10)
  ChatSnapshotResponse ensureChatSnapshot() => $_ensure(5);

  /// What: Updated rendered activity panel.
  /// Why: Activity changes are delivered independently from chat.
  /// How: Refresh only the activity panel.
  /// Example: {"text":"Started /help","snapshot_version":"activity-9","progress_fingerprint":"c9537d2bd4abf311"}
  @$pb.TagNumber(11)
  ShellTextView get activityView => $_getN(6);
  @$pb.TagNumber(11)
  set activityView(ShellTextView v) { setField(11, v); }
  @$pb.TagNumber(11)
  $core.bool hasActivityView() => $_has(6);
  @$pb.TagNumber(11)
  void clearActivityView() => clearField(11);
  @$pb.TagNumber(11)
  ShellTextView ensureActivityView() => $_ensure(6);

  /// What: Updated rendered permissions panel.
  /// Why: Permission changes are delivered independently from chat.
  /// How: Refresh only the permissions panel.
  /// Example: {"text":"Allowed capabilities: ws.skill.catalog","snapshot_version":"permissions-4","progress_fingerprint":"c9537d2bd4abf311"}
  @$pb.TagNumber(12)
  ShellTextView get permissionsView => $_getN(7);
  @$pb.TagNumber(12)
  set permissionsView(ShellTextView v) { setField(12, v); }
  @$pb.TagNumber(12)
  $core.bool hasPermissionsView() => $_has(7);
  @$pb.TagNumber(12)
  void clearPermissionsView() => clearField(12);
  @$pb.TagNumber(12)
  ShellTextView ensurePermissionsView() => $_ensure(7);

  /// What: Updated rendered skills panel.
  /// Why: Skill catalog changes are delivered independently from chat.
  /// How: Refresh only the skills panel.
  /// Example: {"text":"Skill: Learn Markdown","snapshot_version":"skills-11","progress_fingerprint":"c9537d2bd4abf311"}
  @$pb.TagNumber(13)
  ShellTextView get skillsView => $_getN(8);
  @$pb.TagNumber(13)
  set skillsView(ShellTextView v) { setField(13, v); }
  @$pb.TagNumber(13)
  $core.bool hasSkillsView() => $_has(8);
  @$pb.TagNumber(13)
  void clearSkillsView() => clearField(13);
  @$pb.TagNumber(13)
  ShellTextView ensureSkillsView() => $_ensure(8);

  /// What: Updated rendered shell status panel.
  /// Why: Some clients want shell status updates outside chat snapshots.
  /// How: Refresh only the status strip or panel.
  /// Example: {"text":"ready","snapshot_version":"status-5","progress_fingerprint":"c9537d2bd4abf311"}
  @$pb.TagNumber(14)
  ShellTextView get statusView => $_getN(9);
  @$pb.TagNumber(14)
  set statusView(ShellTextView v) { setField(14, v); }
  @$pb.TagNumber(14)
  $core.bool hasStatusView() => $_has(9);
  @$pb.TagNumber(14)
  void clearStatusView() => clearField(14);
  @$pb.TagNumber(14)
  ShellTextView ensureStatusView() => $_ensure(9);

  /// What: Trace id for this streamed event.
  /// Why: Stream updates still participate in traceable host activity.
  /// How: Log it only if event-level diagnostics are needed.
  /// Example: "shell-watch-event_941fbe54"
  @$pb.TagNumber(100)
  $core.String get traceId => $_getSZ(10);
  @$pb.TagNumber(100)
  set traceId($core.String v) { $_setString(10, v); }
  @$pb.TagNumber(100)
  $core.bool hasTraceId() => $_has(10);
  @$pb.TagNumber(100)
  void clearTraceId() => clearField(100);

  /// What: Parent trace id that links the event to its originating activity.
  /// Why: Trace trees need causal linkage even for streamed updates.
  /// How: Treat it as opaque correlation metadata.
  /// Example: "shell-watch-request_5a7653fe"
  @$pb.TagNumber(101)
  $core.String get parentId => $_getSZ(11);
  @$pb.TagNumber(101)
  set parentId($core.String v) { $_setString(11, v); }
  @$pb.TagNumber(101)
  $core.bool hasParentId() => $_has(11);
  @$pb.TagNumber(101)
  void clearParentId() => clearField(101);
}


const _omitFieldNames = $core.bool.fromEnvironment('protobuf.omit_field_names');
const _omitMessageNames = $core.bool.fromEnvironment('protobuf.omit_message_names');
