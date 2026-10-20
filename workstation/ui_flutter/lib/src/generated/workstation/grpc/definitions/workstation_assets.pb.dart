//
//  Generated code. Do not modify.
//  source: workstation/grpc/definitions/workstation_assets.proto
//
// @dart = 2.12

// ignore_for_file: annotate_overrides, camel_case_types, comment_references
// ignore_for_file: constant_identifier_names, library_prefixes
// ignore_for_file: non_constant_identifier_names, prefer_final_fields
// ignore_for_file: unnecessary_import, unnecessary_this, unused_import

import 'dart:core' as $core;

import 'package:protobuf/protobuf.dart' as $pb;

/// What: One client-actionable artifact reference.
/// Why: Cross-platform clients need something richer than a server-local path.
/// How: Prefer this message over raw `open_paths` whenever the client might not
/// share the server filesystem.
/// Valid Example:
///   {
///     "label": "report.pdf",
///     "server_path": "/srv/workstations/transit/build/report.pdf",
///     "mime_type": "application/pdf",
///     "download_url": "http://127.0.0.1:8787/artifacts/abc123/report.pdf",
///     "can_open_locally": true
///   }
class ArtifactRef extends $pb.GeneratedMessage {
  factory ArtifactRef({
    $core.String? label,
    $core.String? serverPath,
    $core.String? mimeType,
    $core.String? downloadUrl,
    $core.bool? canOpenLocally,
  }) {
    final $result = create();
    if (label != null) {
      $result.label = label;
    }
    if (serverPath != null) {
      $result.serverPath = serverPath;
    }
    if (mimeType != null) {
      $result.mimeType = mimeType;
    }
    if (downloadUrl != null) {
      $result.downloadUrl = downloadUrl;
    }
    if (canOpenLocally != null) {
      $result.canOpenLocally = canOpenLocally;
    }
    return $result;
  }
  ArtifactRef._() : super();
  factory ArtifactRef.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory ArtifactRef.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'ArtifactRef', package: const $pb.PackageName(_omitMessageNames ? '' : 'workstation'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'label')
    ..aOS(2, _omitFieldNames ? '' : 'serverPath')
    ..aOS(3, _omitFieldNames ? '' : 'mimeType')
    ..aOS(4, _omitFieldNames ? '' : 'downloadUrl')
    ..aOB(5, _omitFieldNames ? '' : 'canOpenLocally')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  ArtifactRef clone() => ArtifactRef()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  ArtifactRef copyWith(void Function(ArtifactRef) updates) => super.copyWith((message) => updates(message as ArtifactRef)) as ArtifactRef;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static ArtifactRef create() => ArtifactRef._();
  ArtifactRef createEmptyInstance() => create();
  static $pb.PbList<ArtifactRef> createRepeated() => $pb.PbList<ArtifactRef>();
  @$core.pragma('dart2js:noInline')
  static ArtifactRef getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<ArtifactRef>(create);
  static ArtifactRef? _defaultInstance;

  /// What: Human-readable artifact label.
  /// Why: Users need a display name for the artifact.
  /// How: Render it on buttons, links, or file rows.
  /// Example: "report.pdf"
  @$pb.TagNumber(1)
  $core.String get label => $_getSZ(0);
  @$pb.TagNumber(1)
  set label($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasLabel() => $_has(0);
  @$pb.TagNumber(1)
  void clearLabel() => clearField(1);

  /// What: Canonical server-local artifact path.
  /// Why: Same-machine tooling and diagnostics still benefit from the real
  /// server path.
  /// How: Treat it as informational unless the client is explicitly local.
  /// Example: "/srv/workstations/transit/build/report.pdf"
  @$pb.TagNumber(2)
  $core.String get serverPath => $_getSZ(1);
  @$pb.TagNumber(2)
  set serverPath($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasServerPath() => $_has(1);
  @$pb.TagNumber(2)
  void clearServerPath() => clearField(2);

  /// What: Resolved MIME type for the artifact.
  /// Why: Clients need to choose icons, preview behavior, and download headers.
  /// How: Use it to decide how to open or present the artifact.
  /// Example: "application/pdf"
  @$pb.TagNumber(3)
  $core.String get mimeType => $_getSZ(2);
  @$pb.TagNumber(3)
  set mimeType($core.String v) { $_setString(2, v); }
  @$pb.TagNumber(3)
  $core.bool hasMimeType() => $_has(2);
  @$pb.TagNumber(3)
  void clearMimeType() => clearField(3);

  /// What: Client-usable download/open URL.
  /// Why: Web/mobile clients need a transportable reference they can actually
  /// fetch.
  /// How: Open it in a browser tab, external viewer, or download flow.
  /// Example: "http://127.0.0.1:8787/artifacts/abc123/report.pdf"
  @$pb.TagNumber(4)
  $core.String get downloadUrl => $_getSZ(3);
  @$pb.TagNumber(4)
  set downloadUrl($core.String v) { $_setString(3, v); }
  @$pb.TagNumber(4)
  $core.bool hasDownloadUrl() => $_has(3);
  @$pb.TagNumber(4)
  void clearDownloadUrl() => clearField(4);

  /// What: Whether the current client can safely attempt a direct local open.
  /// Why: Same-machine desktop clients may still prefer `open`/shell-style
  /// local opening over an HTTP download.
  /// How: If true, the client may use `server_path` directly when it knows it
  /// shares the server filesystem.
  /// Example: true
  @$pb.TagNumber(5)
  $core.bool get canOpenLocally => $_getBF(4);
  @$pb.TagNumber(5)
  set canOpenLocally($core.bool v) { $_setBool(4, v); }
  @$pb.TagNumber(5)
  $core.bool hasCanOpenLocally() => $_has(4);
  @$pb.TagNumber(5)
  void clearCanOpenLocally() => clearField(5);
}

/// What: Request to stage one markdown upload into the workstation root.
/// Why: Cross-platform clients cannot rely on server-visible local file paths.
/// How: Supply the chosen filename and raw bytes from the client file picker.
/// Valid Example:
///   {
///     "root_path": "/srv/workstations/transit",
///     "client_session_id": "flutter-shell-a",
///     "filename": "city-bus.md",
///     "content": "IyBTbWFydCBDaXR5IFRyYXZlbAo="
///   }
class StageMarkdownUploadRequest extends $pb.GeneratedMessage {
  factory StageMarkdownUploadRequest({
    $core.String? rootPath,
    $core.String? clientSessionId,
    $core.String? filename,
    $core.List<$core.int>? content,
  }) {
    final $result = create();
    if (rootPath != null) {
      $result.rootPath = rootPath;
    }
    if (clientSessionId != null) {
      $result.clientSessionId = clientSessionId;
    }
    if (filename != null) {
      $result.filename = filename;
    }
    if (content != null) {
      $result.content = content;
    }
    return $result;
  }
  StageMarkdownUploadRequest._() : super();
  factory StageMarkdownUploadRequest.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory StageMarkdownUploadRequest.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'StageMarkdownUploadRequest', package: const $pb.PackageName(_omitMessageNames ? '' : 'workstation'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'rootPath')
    ..aOS(2, _omitFieldNames ? '' : 'clientSessionId')
    ..aOS(3, _omitFieldNames ? '' : 'filename')
    ..a<$core.List<$core.int>>(4, _omitFieldNames ? '' : 'content', $pb.PbFieldType.OY)
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  StageMarkdownUploadRequest clone() => StageMarkdownUploadRequest()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  StageMarkdownUploadRequest copyWith(void Function(StageMarkdownUploadRequest) updates) => super.copyWith((message) => updates(message as StageMarkdownUploadRequest)) as StageMarkdownUploadRequest;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static StageMarkdownUploadRequest create() => StageMarkdownUploadRequest._();
  StageMarkdownUploadRequest createEmptyInstance() => create();
  static $pb.PbList<StageMarkdownUploadRequest> createRepeated() => $pb.PbList<StageMarkdownUploadRequest>();
  @$core.pragma('dart2js:noInline')
  static StageMarkdownUploadRequest getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<StageMarkdownUploadRequest>(create);
  static StageMarkdownUploadRequest? _defaultInstance;

  /// What: Absolute workstation root path on the server.
  /// Why: Upload staging is scoped to one workstation.
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

  /// What: Stable client session id.
  /// Why: The host can segregate staged uploads by session.
  /// How: Reuse the client session id from the shell/session bootstrap.
  /// Example: "flutter-shell-a"
  @$pb.TagNumber(2)
  $core.String get clientSessionId => $_getSZ(1);
  @$pb.TagNumber(2)
  set clientSessionId($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasClientSessionId() => $_has(1);
  @$pb.TagNumber(2)
  void clearClientSessionId() => clearField(2);

  /// What: Original client-side filename.
  /// Why: The staged artifact should preserve a user-meaningful name.
  /// How: Pass the basename selected from the file picker.
  /// Example: "city-bus.md"
  @$pb.TagNumber(3)
  $core.String get filename => $_getSZ(2);
  @$pb.TagNumber(3)
  set filename($core.String v) { $_setString(2, v); }
  @$pb.TagNumber(3)
  $core.bool hasFilename() => $_has(2);
  @$pb.TagNumber(3)
  void clearFilename() => clearField(3);

  /// What: Raw markdown file bytes.
  /// Why: The server needs real file content, not just a client-local path.
  /// How: Send the exact bytes selected in the file picker.
  /// Example: "IyBTbWFydCBDaXR5IFRyYXZlbAo="
  @$pb.TagNumber(4)
  $core.List<$core.int> get content => $_getN(3);
  @$pb.TagNumber(4)
  set content($core.List<$core.int> v) { $_setBytes(3, v); }
  @$pb.TagNumber(4)
  $core.bool hasContent() => $_has(3);
  @$pb.TagNumber(4)
  void clearContent() => clearField(4);
}

/// What: Response returned after staging one markdown upload.
/// Why: The client needs a server-visible path and integrity metadata for later
/// workflow requests.
/// How: Feed `staged_path` into `SubjectPhaseProjectionContext`.
/// Valid Example:
///   {
///     "staged_path": "/srv/workstations/transit/uploads/flutter-shell-a/city-bus.md",
///     "display_name": "city-bus.md",
///     "sha256": "4b1c3a9cfd0ba57f4d4b11eb0d5ff4da5424cbf7a5328f4f9459e88f82c6eaf5",
///     "trace_id": "asset-stage-response_81256598",
///     "parent_id": "asset-stage-request_0eb5dd9b"
///   }
class StageMarkdownUploadResponse extends $pb.GeneratedMessage {
  factory StageMarkdownUploadResponse({
    $core.String? stagedPath,
    $core.String? displayName,
    $core.String? sha256,
    $core.String? traceId,
    $core.String? parentId,
  }) {
    final $result = create();
    if (stagedPath != null) {
      $result.stagedPath = stagedPath;
    }
    if (displayName != null) {
      $result.displayName = displayName;
    }
    if (sha256 != null) {
      $result.sha256 = sha256;
    }
    if (traceId != null) {
      $result.traceId = traceId;
    }
    if (parentId != null) {
      $result.parentId = parentId;
    }
    return $result;
  }
  StageMarkdownUploadResponse._() : super();
  factory StageMarkdownUploadResponse.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory StageMarkdownUploadResponse.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'StageMarkdownUploadResponse', package: const $pb.PackageName(_omitMessageNames ? '' : 'workstation'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'stagedPath')
    ..aOS(2, _omitFieldNames ? '' : 'displayName')
    ..aOS(3, _omitFieldNames ? '' : 'sha256')
    ..aOS(100, _omitFieldNames ? '' : 'traceId')
    ..aOS(101, _omitFieldNames ? '' : 'parentId')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  StageMarkdownUploadResponse clone() => StageMarkdownUploadResponse()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  StageMarkdownUploadResponse copyWith(void Function(StageMarkdownUploadResponse) updates) => super.copyWith((message) => updates(message as StageMarkdownUploadResponse)) as StageMarkdownUploadResponse;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static StageMarkdownUploadResponse create() => StageMarkdownUploadResponse._();
  StageMarkdownUploadResponse createEmptyInstance() => create();
  static $pb.PbList<StageMarkdownUploadResponse> createRepeated() => $pb.PbList<StageMarkdownUploadResponse>();
  @$core.pragma('dart2js:noInline')
  static StageMarkdownUploadResponse getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<StageMarkdownUploadResponse>(create);
  static StageMarkdownUploadResponse? _defaultInstance;

  /// What: Server-visible staged path to the uploaded markdown file.
  /// Why: Later subject workflow RPCs still refer to a concrete server path.
  /// How: Put it into `markdown_selected_path` inside the projection context.
  /// Example: "/srv/workstations/transit/uploads/flutter-shell-a/city-bus.md"
  @$pb.TagNumber(1)
  $core.String get stagedPath => $_getSZ(0);
  @$pb.TagNumber(1)
  set stagedPath($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasStagedPath() => $_has(0);
  @$pb.TagNumber(1)
  void clearStagedPath() => clearField(1);

  /// What: Human-readable display name for the staged upload.
  /// Why: The client often wants to show the staged filename back to the user.
  /// How: Render it in upload/import status text.
  /// Example: "city-bus.md"
  @$pb.TagNumber(2)
  $core.String get displayName => $_getSZ(1);
  @$pb.TagNumber(2)
  set displayName($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasDisplayName() => $_has(1);
  @$pb.TagNumber(2)
  void clearDisplayName() => clearField(2);

  /// What: SHA-256 digest of the uploaded content.
  /// Why: Clients and logs may need a stable integrity fingerprint.
  /// How: Treat it as an opaque checksum string.
  /// Example: "4b1c3a9cfd0ba57f4d4b11eb0d5ff4da5424cbf7a5328f4f9459e88f82c6eaf5"
  @$pb.TagNumber(3)
  $core.String get sha256 => $_getSZ(2);
  @$pb.TagNumber(3)
  set sha256($core.String v) { $_setString(2, v); }
  @$pb.TagNumber(3)
  $core.bool hasSha256() => $_has(2);
  @$pb.TagNumber(3)
  void clearSha256() => clearField(3);

  /// What: Trace id for the response.
  /// Why: Upload staging is a traceable operation.
  /// How: Log it when debugging upload issues.
  /// Example: "asset-stage-response_81256598"
  @$pb.TagNumber(100)
  $core.String get traceId => $_getSZ(3);
  @$pb.TagNumber(100)
  set traceId($core.String v) { $_setString(3, v); }
  @$pb.TagNumber(100)
  $core.bool hasTraceId() => $_has(3);
  @$pb.TagNumber(100)
  void clearTraceId() => clearField(100);

  /// What: Parent trace id linking back to the request.
  /// Why: Diagnostics need causal request/response linkage.
  /// How: Treat it as opaque correlation metadata.
  /// Example: "asset-stage-request_0eb5dd9b"
  @$pb.TagNumber(101)
  $core.String get parentId => $_getSZ(4);
  @$pb.TagNumber(101)
  set parentId($core.String v) { $_setString(4, v); }
  @$pb.TagNumber(101)
  $core.bool hasParentId() => $_has(4);
  @$pb.TagNumber(101)
  void clearParentId() => clearField(101);
}

/// What: Request to resolve one or more server-local paths into artifact refs.
/// Why: The client may have legacy `open_paths` or informational paths that
/// need a usable `download_url`.
/// How: Pass the current root, client session id, and the server-local paths to
/// resolve.
/// Valid Example:
///   {
///     "root_path": "/srv/workstations/transit",
///     "client_session_id": "flutter-shell-a",
///     "server_paths": ["/srv/workstations/transit/build/report.pdf"]
///   }
class ResolveArtifactsRequest extends $pb.GeneratedMessage {
  factory ResolveArtifactsRequest({
    $core.String? rootPath,
    $core.String? clientSessionId,
    $core.Iterable<$core.String>? serverPaths,
  }) {
    final $result = create();
    if (rootPath != null) {
      $result.rootPath = rootPath;
    }
    if (clientSessionId != null) {
      $result.clientSessionId = clientSessionId;
    }
    if (serverPaths != null) {
      $result.serverPaths.addAll(serverPaths);
    }
    return $result;
  }
  ResolveArtifactsRequest._() : super();
  factory ResolveArtifactsRequest.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory ResolveArtifactsRequest.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'ResolveArtifactsRequest', package: const $pb.PackageName(_omitMessageNames ? '' : 'workstation'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'rootPath')
    ..aOS(2, _omitFieldNames ? '' : 'clientSessionId')
    ..pPS(3, _omitFieldNames ? '' : 'serverPaths')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  ResolveArtifactsRequest clone() => ResolveArtifactsRequest()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  ResolveArtifactsRequest copyWith(void Function(ResolveArtifactsRequest) updates) => super.copyWith((message) => updates(message as ResolveArtifactsRequest)) as ResolveArtifactsRequest;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static ResolveArtifactsRequest create() => ResolveArtifactsRequest._();
  ResolveArtifactsRequest createEmptyInstance() => create();
  static $pb.PbList<ResolveArtifactsRequest> createRepeated() => $pb.PbList<ResolveArtifactsRequest>();
  @$core.pragma('dart2js:noInline')
  static ResolveArtifactsRequest getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<ResolveArtifactsRequest>(create);
  static ResolveArtifactsRequest? _defaultInstance;

  /// What: Absolute workstation root path on the server.
  /// Why: Artifact resolution is scoped to one workstation root.
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

  /// What: Stable client session id.
  /// Why: Resolution behavior may depend on session-local host assumptions.
  /// How: Reuse the client session id.
  /// Example: "flutter-shell-a"
  @$pb.TagNumber(2)
  $core.String get clientSessionId => $_getSZ(1);
  @$pb.TagNumber(2)
  set clientSessionId($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasClientSessionId() => $_has(1);
  @$pb.TagNumber(2)
  void clearClientSessionId() => clearField(2);

  /// What: Server-local paths to resolve.
  /// Why: The host needs the concrete artifact locations to produce refs.
  /// How: Pass raw `open_paths` or other known server-local file paths.
  /// Example: ["/srv/workstations/transit/build/report.pdf"]
  @$pb.TagNumber(3)
  $core.List<$core.String> get serverPaths => $_getList(2);
}

/// What: Response containing resolved artifact refs.
/// Why: The client needs actionable artifact metadata rather than raw paths.
/// How: Use the returned refs for open/download UI.
/// Valid Example:
///   {
///     "artifacts": [
///       {
///         "label": "report.pdf",
///         "server_path": "/srv/workstations/transit/build/report.pdf",
///         "mime_type": "application/pdf",
///         "download_url": "http://127.0.0.1:8787/artifacts/abc123/report.pdf",
///         "can_open_locally": true
///       }
///     ],
///     "trace_id": "asset-resolve-response_17f8cb08",
///     "parent_id": "asset-resolve-request_51637f2a"
///   }
class ResolveArtifactsResponse extends $pb.GeneratedMessage {
  factory ResolveArtifactsResponse({
    $core.Iterable<ArtifactRef>? artifacts,
    $core.String? traceId,
    $core.String? parentId,
  }) {
    final $result = create();
    if (artifacts != null) {
      $result.artifacts.addAll(artifacts);
    }
    if (traceId != null) {
      $result.traceId = traceId;
    }
    if (parentId != null) {
      $result.parentId = parentId;
    }
    return $result;
  }
  ResolveArtifactsResponse._() : super();
  factory ResolveArtifactsResponse.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory ResolveArtifactsResponse.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'ResolveArtifactsResponse', package: const $pb.PackageName(_omitMessageNames ? '' : 'workstation'), createEmptyInstance: create)
    ..pc<ArtifactRef>(1, _omitFieldNames ? '' : 'artifacts', $pb.PbFieldType.PM, subBuilder: ArtifactRef.create)
    ..aOS(100, _omitFieldNames ? '' : 'traceId')
    ..aOS(101, _omitFieldNames ? '' : 'parentId')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  ResolveArtifactsResponse clone() => ResolveArtifactsResponse()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  ResolveArtifactsResponse copyWith(void Function(ResolveArtifactsResponse) updates) => super.copyWith((message) => updates(message as ResolveArtifactsResponse)) as ResolveArtifactsResponse;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static ResolveArtifactsResponse create() => ResolveArtifactsResponse._();
  ResolveArtifactsResponse createEmptyInstance() => create();
  static $pb.PbList<ResolveArtifactsResponse> createRepeated() => $pb.PbList<ResolveArtifactsResponse>();
  @$core.pragma('dart2js:noInline')
  static ResolveArtifactsResponse getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<ResolveArtifactsResponse>(create);
  static ResolveArtifactsResponse? _defaultInstance;

  /// What: Resolved client-actionable artifact refs.
  /// Why: The client needs actionable outputs for open/download behavior.
  /// How: Render or open each returned artifact according to client policy.
  /// Example: [{"label":"report.pdf","server_path":"/srv/workstations/transit/build/report.pdf","mime_type":"application/pdf","download_url":"http://127.0.0.1:8787/artifacts/abc123/report.pdf","can_open_locally":true}]
  @$pb.TagNumber(1)
  $core.List<ArtifactRef> get artifacts => $_getList(0);

  /// What: Trace id for the response.
  /// Why: Artifact resolution is traceable.
  /// How: Log it when debugging artifact-open issues.
  /// Example: "asset-resolve-response_17f8cb08"
  @$pb.TagNumber(100)
  $core.String get traceId => $_getSZ(1);
  @$pb.TagNumber(100)
  set traceId($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(100)
  $core.bool hasTraceId() => $_has(1);
  @$pb.TagNumber(100)
  void clearTraceId() => clearField(100);

  /// What: Parent trace id linking back to the request.
  /// Why: Diagnostics need causal request/response linkage.
  /// How: Treat it as opaque correlation metadata.
  /// Example: "asset-resolve-request_51637f2a"
  @$pb.TagNumber(101)
  $core.String get parentId => $_getSZ(2);
  @$pb.TagNumber(101)
  set parentId($core.String v) { $_setString(2, v); }
  @$pb.TagNumber(101)
  $core.bool hasParentId() => $_has(2);
  @$pb.TagNumber(101)
  void clearParentId() => clearField(101);
}


const _omitFieldNames = $core.bool.fromEnvironment('protobuf.omit_field_names');
const _omitMessageNames = $core.bool.fromEnvironment('protobuf.omit_message_names');
