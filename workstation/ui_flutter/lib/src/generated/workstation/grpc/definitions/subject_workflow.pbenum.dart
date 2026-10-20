//
//  Generated code. Do not modify.
//  source: workstation/grpc/definitions/subject_workflow.proto
//
// @dart = 2.12

// ignore_for_file: annotate_overrides, camel_case_types, comment_references
// ignore_for_file: constant_identifier_names, library_prefixes
// ignore_for_file: non_constant_identifier_names, prefer_final_fields
// ignore_for_file: unnecessary_import, unnecessary_this, unused_import

import 'dart:core' as $core;

import 'package:protobuf/protobuf.dart' as $pb;

/// What: Visual treatment hint for a gate action.
/// Why: Some actions should render as buttons while others are better shown
/// as links.
/// How: Style the same semantic action differently based on the enum value.
class SubjectGateAction_DisplayKind extends $pb.ProtobufEnum {
  static const SubjectGateAction_DisplayKind DISPLAY_KIND_UNSPECIFIED = SubjectGateAction_DisplayKind._(0, _omitEnumNames ? '' : 'DISPLAY_KIND_UNSPECIFIED');
  static const SubjectGateAction_DisplayKind BUTTON = SubjectGateAction_DisplayKind._(1, _omitEnumNames ? '' : 'BUTTON');
  static const SubjectGateAction_DisplayKind LINK = SubjectGateAction_DisplayKind._(2, _omitEnumNames ? '' : 'LINK');

  static const $core.List<SubjectGateAction_DisplayKind> values = <SubjectGateAction_DisplayKind> [
    DISPLAY_KIND_UNSPECIFIED,
    BUTTON,
    LINK,
  ];

  static final $core.Map<$core.int, SubjectGateAction_DisplayKind> _byValue = $pb.ProtobufEnum.initByValue(values);
  static SubjectGateAction_DisplayKind? valueOf($core.int value) => _byValue[value];

  const SubjectGateAction_DisplayKind._($core.int v, $core.String n) : super(v, n);
}


const _omitEnumNames = $core.bool.fromEnvironment('protobuf.omit_enum_names');
