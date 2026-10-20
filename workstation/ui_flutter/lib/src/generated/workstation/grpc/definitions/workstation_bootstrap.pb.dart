//
//  Generated code. Do not modify.
//  source: workstation/grpc/definitions/workstation_bootstrap.proto
//
// @dart = 2.12

// ignore_for_file: annotate_overrides, camel_case_types, comment_references
// ignore_for_file: constant_identifier_names, library_prefixes
// ignore_for_file: non_constant_identifier_names, prefer_final_fields
// ignore_for_file: unnecessary_import, unnecessary_this, unused_import

import 'dart:core' as $core;

import 'package:protobuf/protobuf.dart' as $pb;

/// What: One workstation root the host is willing to serve.
/// Why: Clients need a stable descriptor for selection and later routing.
/// How: Use `root_path` as the root argument for later shell and subject
/// workflow requests.
/// Valid Example:
///   {
///     "root_id": "transit",
///     "label": "Transit Workstation",
///     "root_path": "/srv/workstations/transit",
///     "workspace_name": "Transit",
///     "is_default": true
///   }
class WorkstationRootDescriptor extends $pb.GeneratedMessage {
  factory WorkstationRootDescriptor({
    $core.String? rootId,
    $core.String? label,
    $core.String? rootPath,
    $core.String? workspaceName,
    $core.bool? isDefault,
  }) {
    final $result = create();
    if (rootId != null) {
      $result.rootId = rootId;
    }
    if (label != null) {
      $result.label = label;
    }
    if (rootPath != null) {
      $result.rootPath = rootPath;
    }
    if (workspaceName != null) {
      $result.workspaceName = workspaceName;
    }
    if (isDefault != null) {
      $result.isDefault = isDefault;
    }
    return $result;
  }
  WorkstationRootDescriptor._() : super();
  factory WorkstationRootDescriptor.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory WorkstationRootDescriptor.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'WorkstationRootDescriptor', package: const $pb.PackageName(_omitMessageNames ? '' : 'workstation'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'rootId')
    ..aOS(2, _omitFieldNames ? '' : 'label')
    ..aOS(3, _omitFieldNames ? '' : 'rootPath')
    ..aOS(4, _omitFieldNames ? '' : 'workspaceName')
    ..aOB(5, _omitFieldNames ? '' : 'isDefault')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  WorkstationRootDescriptor clone() => WorkstationRootDescriptor()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  WorkstationRootDescriptor copyWith(void Function(WorkstationRootDescriptor) updates) => super.copyWith((message) => updates(message as WorkstationRootDescriptor)) as WorkstationRootDescriptor;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static WorkstationRootDescriptor create() => WorkstationRootDescriptor._();
  WorkstationRootDescriptor createEmptyInstance() => create();
  static $pb.PbList<WorkstationRootDescriptor> createRepeated() => $pb.PbList<WorkstationRootDescriptor>();
  @$core.pragma('dart2js:noInline')
  static WorkstationRootDescriptor getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<WorkstationRootDescriptor>(create);
  static WorkstationRootDescriptor? _defaultInstance;

  /// What: Stable host-level id for the served root.
  /// Why: UI selection state should not rely on display labels alone.
  /// How: Use it as the selected option value in the bootstrap UI.
  /// Example: "transit"
  @$pb.TagNumber(1)
  $core.String get rootId => $_getSZ(0);
  @$pb.TagNumber(1)
  set rootId($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasRootId() => $_has(0);
  @$pb.TagNumber(1)
  void clearRootId() => clearField(1);

  /// What: Human-readable selection label.
  /// Why: Users need a readable name in the bootstrap screen.
  /// How: Render it in the root selector.
  /// Example: "Transit Workstation"
  @$pb.TagNumber(2)
  $core.String get label => $_getSZ(1);
  @$pb.TagNumber(2)
  set label($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasLabel() => $_has(1);
  @$pb.TagNumber(2)
  void clearLabel() => clearField(2);

  /// What: Absolute workstation root path on the server.
  /// Why: Later workflow RPCs are still rooted by server path.
  /// How: Pass it into shell and subject workflow requests.
  /// Example: "/srv/workstations/transit"
  @$pb.TagNumber(3)
  $core.String get rootPath => $_getSZ(2);
  @$pb.TagNumber(3)
  set rootPath($core.String v) { $_setString(2, v); }
  @$pb.TagNumber(3)
  $core.bool hasRootPath() => $_has(2);
  @$pb.TagNumber(3)
  void clearRootPath() => clearField(3);

  /// What: Human-readable workspace name associated with the root.
  /// Why: Some environments use a shorter friendly workspace name.
  /// How: Render it as supporting context in the root picker.
  /// Example: "Transit"
  @$pb.TagNumber(4)
  $core.String get workspaceName => $_getSZ(3);
  @$pb.TagNumber(4)
  set workspaceName($core.String v) { $_setString(3, v); }
  @$pb.TagNumber(4)
  $core.bool hasWorkspaceName() => $_has(3);
  @$pb.TagNumber(4)
  void clearWorkspaceName() => clearField(4);

  /// What: Whether this is the host's default workstation root.
  /// Why: Clients often want an initial selection without additional policy.
  /// How: Preselect the first descriptor where this is true.
  /// Example: true
  @$pb.TagNumber(5)
  $core.bool get isDefault => $_getBF(4);
  @$pb.TagNumber(5)
  set isDefault($core.bool v) { $_setBool(4, v); }
  @$pb.TagNumber(5)
  $core.bool hasIsDefault() => $_has(4);
  @$pb.TagNumber(5)
  void clearIsDefault() => clearField(5);
}

/// What: Request to list the workstation roots served by the host.
/// Why: Cross-platform clients need explicit root discovery before they can
/// open sessions.
/// How: Call it immediately after connecting to the host.
/// Valid Example:
///   {}
class ListWorkstationRootsRequest extends $pb.GeneratedMessage {
  factory ListWorkstationRootsRequest() => create();
  ListWorkstationRootsRequest._() : super();
  factory ListWorkstationRootsRequest.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory ListWorkstationRootsRequest.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'ListWorkstationRootsRequest', package: const $pb.PackageName(_omitMessageNames ? '' : 'workstation'), createEmptyInstance: create)
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  ListWorkstationRootsRequest clone() => ListWorkstationRootsRequest()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  ListWorkstationRootsRequest copyWith(void Function(ListWorkstationRootsRequest) updates) => super.copyWith((message) => updates(message as ListWorkstationRootsRequest)) as ListWorkstationRootsRequest;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static ListWorkstationRootsRequest create() => ListWorkstationRootsRequest._();
  ListWorkstationRootsRequest createEmptyInstance() => create();
  static $pb.PbList<ListWorkstationRootsRequest> createRepeated() => $pb.PbList<ListWorkstationRootsRequest>();
  @$core.pragma('dart2js:noInline')
  static ListWorkstationRootsRequest getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<ListWorkstationRootsRequest>(create);
  static ListWorkstationRootsRequest? _defaultInstance;
}

/// What: Response containing all served workstation roots.
/// Why: The client needs both root descriptors and trace metadata.
/// How: Render the returned roots in the bootstrap selection UI.
/// Valid Example:
///   {
///     "roots": [
///       {
///         "root_id": "transit",
///         "label": "Transit Workstation",
///         "root_path": "/srv/workstations/transit",
///         "workspace_name": "Transit",
///         "is_default": true
///       }
///     ],
///     "trace_id": "bootstrap-roots-response_2f3cbe90",
///     "parent_id": "bootstrap-roots-request_90fdb95e"
///   }
class ListWorkstationRootsResponse extends $pb.GeneratedMessage {
  factory ListWorkstationRootsResponse({
    $core.Iterable<WorkstationRootDescriptor>? roots,
    $core.String? traceId,
    $core.String? parentId,
  }) {
    final $result = create();
    if (roots != null) {
      $result.roots.addAll(roots);
    }
    if (traceId != null) {
      $result.traceId = traceId;
    }
    if (parentId != null) {
      $result.parentId = parentId;
    }
    return $result;
  }
  ListWorkstationRootsResponse._() : super();
  factory ListWorkstationRootsResponse.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory ListWorkstationRootsResponse.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'ListWorkstationRootsResponse', package: const $pb.PackageName(_omitMessageNames ? '' : 'workstation'), createEmptyInstance: create)
    ..pc<WorkstationRootDescriptor>(1, _omitFieldNames ? '' : 'roots', $pb.PbFieldType.PM, subBuilder: WorkstationRootDescriptor.create)
    ..aOS(100, _omitFieldNames ? '' : 'traceId')
    ..aOS(101, _omitFieldNames ? '' : 'parentId')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  ListWorkstationRootsResponse clone() => ListWorkstationRootsResponse()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  ListWorkstationRootsResponse copyWith(void Function(ListWorkstationRootsResponse) updates) => super.copyWith((message) => updates(message as ListWorkstationRootsResponse)) as ListWorkstationRootsResponse;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static ListWorkstationRootsResponse create() => ListWorkstationRootsResponse._();
  ListWorkstationRootsResponse createEmptyInstance() => create();
  static $pb.PbList<ListWorkstationRootsResponse> createRepeated() => $pb.PbList<ListWorkstationRootsResponse>();
  @$core.pragma('dart2js:noInline')
  static ListWorkstationRootsResponse getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<ListWorkstationRootsResponse>(create);
  static ListWorkstationRootsResponse? _defaultInstance;

  /// What: Served workstation root descriptors.
  /// Why: The client needs the available workstation choices.
  /// How: Render one selectable row per descriptor.
  /// Example: [{"root_id":"transit","label":"Transit Workstation","root_path":"/srv/workstations/transit","workspace_name":"Transit","is_default":true}]
  @$pb.TagNumber(1)
  $core.List<WorkstationRootDescriptor> get roots => $_getList(0);

  /// What: Trace id for the response.
  /// Why: Bootstrap operations participate in host-level traceability.
  /// How: Log it when debugging connection/bootstrap issues.
  /// Example: "bootstrap-roots-response_2f3cbe90"
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
  /// Example: "bootstrap-roots-request_90fdb95e"
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
