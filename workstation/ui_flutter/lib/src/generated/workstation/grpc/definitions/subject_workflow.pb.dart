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

import 'package:fixnum/fixnum.dart' as $fixnum;
import 'package:protobuf/protobuf.dart' as $pb;

import 'subject_workflow.pbenum.dart';
import 'workstation_assets.pb.dart' as $0;

export 'subject_workflow.pbenum.dart';

/// What: Summary row describing one subject scenario in the workstation corpus.
/// Why: Subject lists need a compact but information-rich projection for
/// selection, sorting, and quick status inspection before opening a phase view.
/// How: Render these values in subject pickers, status strips, and summary
/// dashboards; use the more detailed phase snapshot when the user opens one
/// subject.
/// Valid Example:
///   {
///     "key": "smart_city_travel",
///     "subject_id": "smart_city_travel",
///     "title": "Smart City Travel",
///     "family_title": "City bus prose v2",
///     "context_id": "ctx_smart_city_travel",
///     "summary": "A city transit authority wants to modernize fare payment.",
///     "governance_status": "ready",
///     "context_snapshot_hash": "9c0bbf2d",
///     "unit_count": 12,
///     "admitted_unit_count": 12,
///     "source_count": 1,
///     "delta_count": 1,
///     "applied_delta_count": 1,
///     "import_count": 1,
///     "pending_import_count": 0,
///     "reasoning_import_count": 0,
///     "imported_subject_count": 0,
///     "context_path": "corpus/smart-city-travel/context.json",
///     "subject_markdown_path": "/srv/workstations/transit/dst/City bus prose v2.md",
///     "subject_typst_path": "",
///     "publication_id": "",
///     "publication_title": "",
///     "build_id": "",
///     "build_status": "",
///     "validation_status": "",
///     "build_path": "",
///     "publication_section_count": 0,
///     "publication_claim_count": 0,
///     "publication_source_count": 0,
///     "publication_entity_count": 0,
///     "publication_xref_count": 0,
///     "publication_review_count": 0,
///     "report_markdown_path": "",
///     "report_typst_path": "",
///     "report_pdf_path": "",
///     "composition_id": "",
///     "composition_status": "",
///     "composition_title": "",
///     "composition_scope_summary": "",
///     "composition_learning_context_snapshot_hash": "",
///     "composition_included_unit_count": 0,
///     "composition_selected_import_count": 0,
///     "composition_section_count": 0,
///     "source_collection_count": 1,
///     "staged_source_count": 0,
///     "source_collection_preview_lines": ["All Gather Sources"],
///     "source_preview_lines": ["City bus prose v2.md"],
///     "staged_source_preview_lines": [],
///     "unit_preview_lines": ["Smart City Travel"],
///     "delta_preview_lines": ["definition: Smart City Travel"],
///     "pending_import_preview_lines": [],
///     "import_preview_lines": ["City bus prose v2.md"],
///     "is_placeholder": false
///   }
class SubjectScenarioSummary extends $pb.GeneratedMessage {
  factory SubjectScenarioSummary({
    $core.String? key,
    $core.String? subjectId,
    $core.String? title,
    $core.String? familyTitle,
    $core.String? contextId,
    $core.String? summary,
    $core.String? governanceStatus,
    $core.String? contextSnapshotHash,
    $core.int? unitCount,
    $core.int? admittedUnitCount,
    $core.int? sourceCount,
    $core.int? deltaCount,
    $core.int? appliedDeltaCount,
    $core.int? importCount,
    $core.int? pendingImportCount,
    $core.int? reasoningImportCount,
    $core.int? importedSubjectCount,
    $core.String? contextPath,
    $core.String? subjectMarkdownPath,
    $core.String? subjectTypstPath,
    $core.String? publicationId,
    $core.String? publicationTitle,
    $core.String? buildId,
    $core.String? buildStatus,
    $core.String? validationStatus,
    $core.String? buildPath,
    $core.int? publicationSectionCount,
    $core.int? publicationClaimCount,
    $core.int? publicationSourceCount,
    $core.int? publicationEntityCount,
    $core.int? publicationXrefCount,
    $core.int? publicationReviewCount,
    $core.String? reportMarkdownPath,
    $core.String? reportTypstPath,
    $core.String? reportPdfPath,
    $core.String? compositionId,
    $core.String? compositionStatus,
    $core.String? compositionTitle,
    $core.String? compositionScopeSummary,
    $core.String? compositionLearningContextSnapshotHash,
    $core.int? compositionIncludedUnitCount,
    $core.int? compositionSelectedImportCount,
    $core.int? compositionSectionCount,
    $core.int? sourceCollectionCount,
    $core.int? stagedSourceCount,
    $core.Iterable<$core.String>? sourceCollectionPreviewLines,
    $core.Iterable<$core.String>? sourcePreviewLines,
    $core.Iterable<$core.String>? stagedSourcePreviewLines,
    $core.Iterable<$core.String>? unitPreviewLines,
    $core.Iterable<$core.String>? deltaPreviewLines,
    $core.Iterable<$core.String>? pendingImportPreviewLines,
    $core.Iterable<$core.String>? importPreviewLines,
    $core.bool? isPlaceholder,
  }) {
    final $result = create();
    if (key != null) {
      $result.key = key;
    }
    if (subjectId != null) {
      $result.subjectId = subjectId;
    }
    if (title != null) {
      $result.title = title;
    }
    if (familyTitle != null) {
      $result.familyTitle = familyTitle;
    }
    if (contextId != null) {
      $result.contextId = contextId;
    }
    if (summary != null) {
      $result.summary = summary;
    }
    if (governanceStatus != null) {
      $result.governanceStatus = governanceStatus;
    }
    if (contextSnapshotHash != null) {
      $result.contextSnapshotHash = contextSnapshotHash;
    }
    if (unitCount != null) {
      $result.unitCount = unitCount;
    }
    if (admittedUnitCount != null) {
      $result.admittedUnitCount = admittedUnitCount;
    }
    if (sourceCount != null) {
      $result.sourceCount = sourceCount;
    }
    if (deltaCount != null) {
      $result.deltaCount = deltaCount;
    }
    if (appliedDeltaCount != null) {
      $result.appliedDeltaCount = appliedDeltaCount;
    }
    if (importCount != null) {
      $result.importCount = importCount;
    }
    if (pendingImportCount != null) {
      $result.pendingImportCount = pendingImportCount;
    }
    if (reasoningImportCount != null) {
      $result.reasoningImportCount = reasoningImportCount;
    }
    if (importedSubjectCount != null) {
      $result.importedSubjectCount = importedSubjectCount;
    }
    if (contextPath != null) {
      $result.contextPath = contextPath;
    }
    if (subjectMarkdownPath != null) {
      $result.subjectMarkdownPath = subjectMarkdownPath;
    }
    if (subjectTypstPath != null) {
      $result.subjectTypstPath = subjectTypstPath;
    }
    if (publicationId != null) {
      $result.publicationId = publicationId;
    }
    if (publicationTitle != null) {
      $result.publicationTitle = publicationTitle;
    }
    if (buildId != null) {
      $result.buildId = buildId;
    }
    if (buildStatus != null) {
      $result.buildStatus = buildStatus;
    }
    if (validationStatus != null) {
      $result.validationStatus = validationStatus;
    }
    if (buildPath != null) {
      $result.buildPath = buildPath;
    }
    if (publicationSectionCount != null) {
      $result.publicationSectionCount = publicationSectionCount;
    }
    if (publicationClaimCount != null) {
      $result.publicationClaimCount = publicationClaimCount;
    }
    if (publicationSourceCount != null) {
      $result.publicationSourceCount = publicationSourceCount;
    }
    if (publicationEntityCount != null) {
      $result.publicationEntityCount = publicationEntityCount;
    }
    if (publicationXrefCount != null) {
      $result.publicationXrefCount = publicationXrefCount;
    }
    if (publicationReviewCount != null) {
      $result.publicationReviewCount = publicationReviewCount;
    }
    if (reportMarkdownPath != null) {
      $result.reportMarkdownPath = reportMarkdownPath;
    }
    if (reportTypstPath != null) {
      $result.reportTypstPath = reportTypstPath;
    }
    if (reportPdfPath != null) {
      $result.reportPdfPath = reportPdfPath;
    }
    if (compositionId != null) {
      $result.compositionId = compositionId;
    }
    if (compositionStatus != null) {
      $result.compositionStatus = compositionStatus;
    }
    if (compositionTitle != null) {
      $result.compositionTitle = compositionTitle;
    }
    if (compositionScopeSummary != null) {
      $result.compositionScopeSummary = compositionScopeSummary;
    }
    if (compositionLearningContextSnapshotHash != null) {
      $result.compositionLearningContextSnapshotHash = compositionLearningContextSnapshotHash;
    }
    if (compositionIncludedUnitCount != null) {
      $result.compositionIncludedUnitCount = compositionIncludedUnitCount;
    }
    if (compositionSelectedImportCount != null) {
      $result.compositionSelectedImportCount = compositionSelectedImportCount;
    }
    if (compositionSectionCount != null) {
      $result.compositionSectionCount = compositionSectionCount;
    }
    if (sourceCollectionCount != null) {
      $result.sourceCollectionCount = sourceCollectionCount;
    }
    if (stagedSourceCount != null) {
      $result.stagedSourceCount = stagedSourceCount;
    }
    if (sourceCollectionPreviewLines != null) {
      $result.sourceCollectionPreviewLines.addAll(sourceCollectionPreviewLines);
    }
    if (sourcePreviewLines != null) {
      $result.sourcePreviewLines.addAll(sourcePreviewLines);
    }
    if (stagedSourcePreviewLines != null) {
      $result.stagedSourcePreviewLines.addAll(stagedSourcePreviewLines);
    }
    if (unitPreviewLines != null) {
      $result.unitPreviewLines.addAll(unitPreviewLines);
    }
    if (deltaPreviewLines != null) {
      $result.deltaPreviewLines.addAll(deltaPreviewLines);
    }
    if (pendingImportPreviewLines != null) {
      $result.pendingImportPreviewLines.addAll(pendingImportPreviewLines);
    }
    if (importPreviewLines != null) {
      $result.importPreviewLines.addAll(importPreviewLines);
    }
    if (isPlaceholder != null) {
      $result.isPlaceholder = isPlaceholder;
    }
    return $result;
  }
  SubjectScenarioSummary._() : super();
  factory SubjectScenarioSummary.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory SubjectScenarioSummary.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'SubjectScenarioSummary', package: const $pb.PackageName(_omitMessageNames ? '' : 'realized.workstation.subjectworkflow.v1'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'key')
    ..aOS(2, _omitFieldNames ? '' : 'subjectId')
    ..aOS(3, _omitFieldNames ? '' : 'title')
    ..aOS(4, _omitFieldNames ? '' : 'familyTitle')
    ..aOS(5, _omitFieldNames ? '' : 'contextId')
    ..aOS(6, _omitFieldNames ? '' : 'summary')
    ..aOS(7, _omitFieldNames ? '' : 'governanceStatus')
    ..aOS(8, _omitFieldNames ? '' : 'contextSnapshotHash')
    ..a<$core.int>(9, _omitFieldNames ? '' : 'unitCount', $pb.PbFieldType.O3)
    ..a<$core.int>(10, _omitFieldNames ? '' : 'admittedUnitCount', $pb.PbFieldType.O3)
    ..a<$core.int>(11, _omitFieldNames ? '' : 'sourceCount', $pb.PbFieldType.O3)
    ..a<$core.int>(12, _omitFieldNames ? '' : 'deltaCount', $pb.PbFieldType.O3)
    ..a<$core.int>(13, _omitFieldNames ? '' : 'appliedDeltaCount', $pb.PbFieldType.O3)
    ..a<$core.int>(14, _omitFieldNames ? '' : 'importCount', $pb.PbFieldType.O3)
    ..a<$core.int>(15, _omitFieldNames ? '' : 'pendingImportCount', $pb.PbFieldType.O3)
    ..a<$core.int>(16, _omitFieldNames ? '' : 'reasoningImportCount', $pb.PbFieldType.O3)
    ..a<$core.int>(17, _omitFieldNames ? '' : 'importedSubjectCount', $pb.PbFieldType.O3)
    ..aOS(18, _omitFieldNames ? '' : 'contextPath')
    ..aOS(19, _omitFieldNames ? '' : 'subjectMarkdownPath')
    ..aOS(20, _omitFieldNames ? '' : 'subjectTypstPath')
    ..aOS(21, _omitFieldNames ? '' : 'publicationId')
    ..aOS(22, _omitFieldNames ? '' : 'publicationTitle')
    ..aOS(23, _omitFieldNames ? '' : 'buildId')
    ..aOS(24, _omitFieldNames ? '' : 'buildStatus')
    ..aOS(25, _omitFieldNames ? '' : 'validationStatus')
    ..aOS(26, _omitFieldNames ? '' : 'buildPath')
    ..a<$core.int>(27, _omitFieldNames ? '' : 'publicationSectionCount', $pb.PbFieldType.O3)
    ..a<$core.int>(28, _omitFieldNames ? '' : 'publicationClaimCount', $pb.PbFieldType.O3)
    ..a<$core.int>(29, _omitFieldNames ? '' : 'publicationSourceCount', $pb.PbFieldType.O3)
    ..a<$core.int>(30, _omitFieldNames ? '' : 'publicationEntityCount', $pb.PbFieldType.O3)
    ..a<$core.int>(31, _omitFieldNames ? '' : 'publicationXrefCount', $pb.PbFieldType.O3)
    ..a<$core.int>(32, _omitFieldNames ? '' : 'publicationReviewCount', $pb.PbFieldType.O3)
    ..aOS(33, _omitFieldNames ? '' : 'reportMarkdownPath')
    ..aOS(34, _omitFieldNames ? '' : 'reportTypstPath')
    ..aOS(35, _omitFieldNames ? '' : 'reportPdfPath')
    ..aOS(36, _omitFieldNames ? '' : 'compositionId')
    ..aOS(37, _omitFieldNames ? '' : 'compositionStatus')
    ..aOS(38, _omitFieldNames ? '' : 'compositionTitle')
    ..aOS(39, _omitFieldNames ? '' : 'compositionScopeSummary')
    ..aOS(40, _omitFieldNames ? '' : 'compositionLearningContextSnapshotHash')
    ..a<$core.int>(41, _omitFieldNames ? '' : 'compositionIncludedUnitCount', $pb.PbFieldType.O3)
    ..a<$core.int>(42, _omitFieldNames ? '' : 'compositionSelectedImportCount', $pb.PbFieldType.O3)
    ..a<$core.int>(43, _omitFieldNames ? '' : 'compositionSectionCount', $pb.PbFieldType.O3)
    ..a<$core.int>(44, _omitFieldNames ? '' : 'sourceCollectionCount', $pb.PbFieldType.O3)
    ..a<$core.int>(45, _omitFieldNames ? '' : 'stagedSourceCount', $pb.PbFieldType.O3)
    ..pPS(46, _omitFieldNames ? '' : 'sourceCollectionPreviewLines')
    ..pPS(47, _omitFieldNames ? '' : 'sourcePreviewLines')
    ..pPS(48, _omitFieldNames ? '' : 'stagedSourcePreviewLines')
    ..pPS(49, _omitFieldNames ? '' : 'unitPreviewLines')
    ..pPS(50, _omitFieldNames ? '' : 'deltaPreviewLines')
    ..pPS(51, _omitFieldNames ? '' : 'pendingImportPreviewLines')
    ..pPS(52, _omitFieldNames ? '' : 'importPreviewLines')
    ..aOB(53, _omitFieldNames ? '' : 'isPlaceholder')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  SubjectScenarioSummary clone() => SubjectScenarioSummary()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  SubjectScenarioSummary copyWith(void Function(SubjectScenarioSummary) updates) => super.copyWith((message) => updates(message as SubjectScenarioSummary)) as SubjectScenarioSummary;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static SubjectScenarioSummary create() => SubjectScenarioSummary._();
  SubjectScenarioSummary createEmptyInstance() => create();
  static $pb.PbList<SubjectScenarioSummary> createRepeated() => $pb.PbList<SubjectScenarioSummary>();
  @$core.pragma('dart2js:noInline')
  static SubjectScenarioSummary getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<SubjectScenarioSummary>(create);
  static SubjectScenarioSummary? _defaultInstance;

  /// What: Stable scenario key used by selectors and summaries.
  /// Why: Clients need a durable identity token that is safe to store in local
  /// UI state.
  /// How: Use it as the option value when choosing a subject from a list.
  /// Example: "smart_city_travel"
  @$pb.TagNumber(1)
  $core.String get key => $_getSZ(0);
  @$pb.TagNumber(1)
  set key($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasKey() => $_has(0);
  @$pb.TagNumber(1)
  void clearKey() => clearField(1);

  /// What: Canonical subject id for workflow operations.
  /// Why: Action, snapshot, and progress RPCs target subjects by id.
  /// How: Pass it into later subject workflow requests.
  /// Example: "smart_city_travel"
  @$pb.TagNumber(2)
  $core.String get subjectId => $_getSZ(1);
  @$pb.TagNumber(2)
  set subjectId($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasSubjectId() => $_has(1);
  @$pb.TagNumber(2)
  void clearSubjectId() => clearField(2);

  /// What: Current subject title.
  /// Why: Lists and tabs should show the human-readable subject name.
  /// How: Render it anywhere the user needs to identify the subject.
  /// Example: "Smart City Travel"
  @$pb.TagNumber(3)
  $core.String get title => $_getSZ(2);
  @$pb.TagNumber(3)
  set title($core.String v) { $_setString(2, v); }
  @$pb.TagNumber(3)
  $core.bool hasTitle() => $_has(2);
  @$pb.TagNumber(3)
  void clearTitle() => clearField(3);

  /// What: Family or source-derived subject label.
  /// Why: Users often need to know which original material produced the subject.
  /// How: Show it as supporting context beside the main title.
  /// Example: "City bus prose v2"
  @$pb.TagNumber(4)
  $core.String get familyTitle => $_getSZ(3);
  @$pb.TagNumber(4)
  set familyTitle($core.String v) { $_setString(3, v); }
  @$pb.TagNumber(4)
  $core.bool hasFamilyTitle() => $_has(3);
  @$pb.TagNumber(4)
  void clearFamilyTitle() => clearField(4);

  /// What: Context document id that backs the subject.
  /// Why: Context lifecycle tools need a durable identity for the stored
  /// learning context.
  /// How: Treat it as an opaque system id unless you are debugging.
  /// Example: "ctx_smart_city_travel"
  @$pb.TagNumber(5)
  $core.String get contextId => $_getSZ(4);
  @$pb.TagNumber(5)
  set contextId($core.String v) { $_setString(4, v); }
  @$pb.TagNumber(5)
  $core.bool hasContextId() => $_has(4);
  @$pb.TagNumber(5)
  void clearContextId() => clearField(5);

  /// What: Short subject summary.
  /// Why: Subject lists need a compressed preview before the user opens a full
  /// phase projection.
  /// How: Render it as a subtitle or summary card body.
  /// Example: "A city transit authority wants to modernize fare payment."
  @$pb.TagNumber(6)
  $core.String get summary => $_getSZ(5);
  @$pb.TagNumber(6)
  set summary($core.String v) { $_setString(5, v); }
  @$pb.TagNumber(6)
  $core.bool hasSummary() => $_has(5);
  @$pb.TagNumber(6)
  void clearSummary() => clearField(6);

  /// What: Governance/readiness status for the subject.
  /// Why: The list view should surface whether the subject is ready, stale,
  /// blocked, or otherwise gated.
  /// How: Render it as status text or a badge.
  /// Example: "ready"
  @$pb.TagNumber(7)
  $core.String get governanceStatus => $_getSZ(6);
  @$pb.TagNumber(7)
  set governanceStatus($core.String v) { $_setString(6, v); }
  @$pb.TagNumber(7)
  $core.bool hasGovernanceStatus() => $_has(6);
  @$pb.TagNumber(7)
  void clearGovernanceStatus() => clearField(7);

  /// What: Hash of the current learning-context snapshot.
  /// Why: Clients and services use it to detect whether downstream artifacts are
  /// stale relative to current intake.
  /// How: Treat it as an opaque fingerprint for comparison.
  /// Example: "9c0bbf2d"
  @$pb.TagNumber(8)
  $core.String get contextSnapshotHash => $_getSZ(7);
  @$pb.TagNumber(8)
  set contextSnapshotHash($core.String v) { $_setString(7, v); }
  @$pb.TagNumber(8)
  $core.bool hasContextSnapshotHash() => $_has(7);
  @$pb.TagNumber(8)
  void clearContextSnapshotHash() => clearField(8);

  /// What: Total unit count currently represented in the subject context.
  /// Why: The list view often needs a high-level measure of subject size.
  /// How: Display it as informational summary data.
  /// Example: 12
  @$pb.TagNumber(9)
  $core.int get unitCount => $_getIZ(8);
  @$pb.TagNumber(9)
  set unitCount($core.int v) { $_setSignedInt32(8, v); }
  @$pb.TagNumber(9)
  $core.bool hasUnitCount() => $_has(8);
  @$pb.TagNumber(9)
  void clearUnitCount() => clearField(9);

  /// What: Count of admitted units in the context.
  /// Why: Workflows distinguish between discovered and admitted material.
  /// How: Show it when governance or intake readiness matters.
  /// Example: 12
  @$pb.TagNumber(10)
  $core.int get admittedUnitCount => $_getIZ(9);
  @$pb.TagNumber(10)
  set admittedUnitCount($core.int v) { $_setSignedInt32(9, v); }
  @$pb.TagNumber(10)
  $core.bool hasAdmittedUnitCount() => $_has(9);
  @$pb.TagNumber(10)
  void clearAdmittedUnitCount() => clearField(10);

  /// What: Count of source records associated with the subject.
  /// Why: Users need a quick sense of source breadth.
  /// How: Render it in summaries or phase status views.
  /// Example: 1
  @$pb.TagNumber(11)
  $core.int get sourceCount => $_getIZ(10);
  @$pb.TagNumber(11)
  set sourceCount($core.int v) { $_setSignedInt32(10, v); }
  @$pb.TagNumber(11)
  $core.bool hasSourceCount() => $_has(10);
  @$pb.TagNumber(11)
  void clearSourceCount() => clearField(11);

  /// What: Count of recorded deltas for the subject.
  /// Why: Intake and refinement often materialize incremental changes.
  /// How: Show it as part of current subject health/shape.
  /// Example: 1
  @$pb.TagNumber(12)
  $core.int get deltaCount => $_getIZ(11);
  @$pb.TagNumber(12)
  set deltaCount($core.int v) { $_setSignedInt32(11, v); }
  @$pb.TagNumber(12)
  $core.bool hasDeltaCount() => $_has(11);
  @$pb.TagNumber(12)
  void clearDeltaCount() => clearField(12);

  /// What: Count of deltas that have been applied.
  /// Why: Users need to know whether proposed changes have been absorbed.
  /// How: Compare it with `delta_count` in progress summaries.
  /// Example: 1
  @$pb.TagNumber(13)
  $core.int get appliedDeltaCount => $_getIZ(12);
  @$pb.TagNumber(13)
  set appliedDeltaCount($core.int v) { $_setSignedInt32(12, v); }
  @$pb.TagNumber(13)
  $core.bool hasAppliedDeltaCount() => $_has(12);
  @$pb.TagNumber(13)
  void clearAppliedDeltaCount() => clearField(13);

  /// What: Count of imported records attached to the subject.
  /// Why: Import activity is a first-class workflow concern in Gather.
  /// How: Display it in intake summaries.
  /// Example: 1
  @$pb.TagNumber(14)
  $core.int get importCount => $_getIZ(13);
  @$pb.TagNumber(14)
  set importCount($core.int v) { $_setSignedInt32(13, v); }
  @$pb.TagNumber(14)
  $core.bool hasImportCount() => $_has(13);
  @$pb.TagNumber(14)
  void clearImportCount() => clearField(14);

  /// What: Count of imports waiting for approval or resolution.
  /// Why: Pending imports usually gate the next recommended action.
  /// How: Highlight non-zero values in Gather.
  /// Example: 0
  @$pb.TagNumber(15)
  $core.int get pendingImportCount => $_getIZ(14);
  @$pb.TagNumber(15)
  set pendingImportCount($core.int v) { $_setSignedInt32(14, v); }
  @$pb.TagNumber(15)
  $core.bool hasPendingImportCount() => $_has(14);
  @$pb.TagNumber(15)
  void clearPendingImportCount() => clearField(15);

  /// What: Count of reasoning-scope imports.
  /// Why: Some imports support reasoning context rather than primary definition.
  /// How: Treat it as advanced diagnostic metadata.
  /// Example: 0
  @$pb.TagNumber(16)
  $core.int get reasoningImportCount => $_getIZ(15);
  @$pb.TagNumber(16)
  set reasoningImportCount($core.int v) { $_setSignedInt32(15, v); }
  @$pb.TagNumber(16)
  $core.bool hasReasoningImportCount() => $_has(15);
  @$pb.TagNumber(16)
  void clearReasoningImportCount() => clearField(16);

  /// What: Count of imported subjects linked into this subject.
  /// Why: Cross-subject reuse is part of the workstation domain model.
  /// How: Surface it in advanced status or subject relation views.
  /// Example: 0
  @$pb.TagNumber(17)
  $core.int get importedSubjectCount => $_getIZ(16);
  @$pb.TagNumber(17)
  set importedSubjectCount($core.int v) { $_setSignedInt32(16, v); }
  @$pb.TagNumber(17)
  $core.bool hasImportedSubjectCount() => $_has(16);
  @$pb.TagNumber(17)
  void clearImportedSubjectCount() => clearField(17);

  /// What: Server-local path to the stored subject context document.
  /// Why: Operators and same-machine desktop clients may need the canonical
  /// storage location for diagnostics.
  /// How: Treat it as informational; web/mobile should not assume it is
  /// directly usable.
  /// Example: "corpus/smart-city-travel/context.json"
  @$pb.TagNumber(18)
  $core.String get contextPath => $_getSZ(17);
  @$pb.TagNumber(18)
  set contextPath($core.String v) { $_setString(17, v); }
  @$pb.TagNumber(18)
  $core.bool hasContextPath() => $_has(17);
  @$pb.TagNumber(18)
  void clearContextPath() => clearField(18);

  /// What: Server-local path to the learned subject markdown source.
  /// Why: Same-machine tooling and diagnostics often need the originating file.
  /// How: Treat it as informational; actionable opening should use
  /// `open_artifacts` or `ResolveArtifacts`.
  /// Example: "/srv/workstations/transit/dst/City bus prose v2.md"
  @$pb.TagNumber(19)
  $core.String get subjectMarkdownPath => $_getSZ(18);
  @$pb.TagNumber(19)
  set subjectMarkdownPath($core.String v) { $_setString(18, v); }
  @$pb.TagNumber(19)
  $core.bool hasSubjectMarkdownPath() => $_has(18);
  @$pb.TagNumber(19)
  void clearSubjectMarkdownPath() => clearField(19);

  /// What: Server-local path to the subject Typst projection, when present.
  /// Why: Draft/publication tooling may materialize Typst alongside markdown.
  /// How: Treat it as informational unless resolved through the asset surface.
  /// Example: ""
  @$pb.TagNumber(20)
  $core.String get subjectTypstPath => $_getSZ(19);
  @$pb.TagNumber(20)
  set subjectTypstPath($core.String v) { $_setString(19, v); }
  @$pb.TagNumber(20)
  $core.bool hasSubjectTypstPath() => $_has(19);
  @$pb.TagNumber(20)
  void clearSubjectTypstPath() => clearField(20);

  /// What: Current publication id for this subject.
  /// Why: Publication is a durable governed object with its own identity.
  /// How: Treat it as opaque metadata for diagnostics or deep links.
  /// Example: ""
  @$pb.TagNumber(21)
  $core.String get publicationId => $_getSZ(20);
  @$pb.TagNumber(21)
  set publicationId($core.String v) { $_setString(20, v); }
  @$pb.TagNumber(21)
  $core.bool hasPublicationId() => $_has(20);
  @$pb.TagNumber(21)
  void clearPublicationId() => clearField(21);

  /// What: Human-readable publication title.
  /// Why: Publication outputs often have their own presentation title.
  /// How: Render when publication exists.
  /// Example: ""
  @$pb.TagNumber(22)
  $core.String get publicationTitle => $_getSZ(21);
  @$pb.TagNumber(22)
  set publicationTitle($core.String v) { $_setString(21, v); }
  @$pb.TagNumber(22)
  $core.bool hasPublicationTitle() => $_has(21);
  @$pb.TagNumber(22)
  void clearPublicationTitle() => clearField(22);

  /// What: Current build id for the subject publication.
  /// Why: Publication builds are versioned and traceable.
  /// How: Treat it as opaque metadata for diagnostics.
  /// Example: ""
  @$pb.TagNumber(23)
  $core.String get buildId => $_getSZ(22);
  @$pb.TagNumber(23)
  set buildId($core.String v) { $_setString(22, v); }
  @$pb.TagNumber(23)
  $core.bool hasBuildId() => $_has(22);
  @$pb.TagNumber(23)
  void clearBuildId() => clearField(23);

  /// What: Current publication build status.
  /// Why: Clients need to know whether a build is absent, running, failed, or
  /// complete.
  /// How: Render it in Publication status areas.
  /// Example: ""
  @$pb.TagNumber(24)
  $core.String get buildStatus => $_getSZ(23);
  @$pb.TagNumber(24)
  set buildStatus($core.String v) { $_setString(23, v); }
  @$pb.TagNumber(24)
  $core.bool hasBuildStatus() => $_has(23);
  @$pb.TagNumber(24)
  void clearBuildStatus() => clearField(24);

  /// What: Validation status for the built publication.
  /// Why: Publication review depends on build validation outcomes.
  /// How: Surface it near build status.
  /// Example: ""
  @$pb.TagNumber(25)
  $core.String get validationStatus => $_getSZ(24);
  @$pb.TagNumber(25)
  set validationStatus($core.String v) { $_setString(24, v); }
  @$pb.TagNumber(25)
  $core.bool hasValidationStatus() => $_has(24);
  @$pb.TagNumber(25)
  void clearValidationStatus() => clearField(25);

  /// What: Server-local path to the build output directory.
  /// Why: Same-machine debugging and release tooling may need it.
  /// How: Treat it as informational unless exposed through an artifact URL.
  /// Example: ""
  @$pb.TagNumber(26)
  $core.String get buildPath => $_getSZ(25);
  @$pb.TagNumber(26)
  set buildPath($core.String v) { $_setString(25, v); }
  @$pb.TagNumber(26)
  $core.bool hasBuildPath() => $_has(25);
  @$pb.TagNumber(26)
  void clearBuildPath() => clearField(26);

  /// What: Count of publication sections.
  /// Why: Publication complexity is part of summary state.
  /// How: Render in publication-oriented summaries when non-zero.
  /// Example: 0
  @$pb.TagNumber(27)
  $core.int get publicationSectionCount => $_getIZ(26);
  @$pb.TagNumber(27)
  set publicationSectionCount($core.int v) { $_setSignedInt32(26, v); }
  @$pb.TagNumber(27)
  $core.bool hasPublicationSectionCount() => $_has(26);
  @$pb.TagNumber(27)
  void clearPublicationSectionCount() => clearField(27);

  /// What: Count of publication claims.
  /// Why: Reviewers often need a top-level sense of claim volume.
  /// How: Show in publication diagnostics or status.
  /// Example: 0
  @$pb.TagNumber(28)
  $core.int get publicationClaimCount => $_getIZ(27);
  @$pb.TagNumber(28)
  set publicationClaimCount($core.int v) { $_setSignedInt32(27, v); }
  @$pb.TagNumber(28)
  $core.bool hasPublicationClaimCount() => $_has(27);
  @$pb.TagNumber(28)
  void clearPublicationClaimCount() => clearField(28);

  /// What: Count of publication sources.
  /// Why: Publication/source completeness is review-relevant.
  /// How: Render when publication artifacts exist.
  /// Example: 0
  @$pb.TagNumber(29)
  $core.int get publicationSourceCount => $_getIZ(28);
  @$pb.TagNumber(29)
  set publicationSourceCount($core.int v) { $_setSignedInt32(28, v); }
  @$pb.TagNumber(29)
  $core.bool hasPublicationSourceCount() => $_has(28);
  @$pb.TagNumber(29)
  void clearPublicationSourceCount() => clearField(29);

  /// What: Count of publication entities.
  /// Why: Entity coverage is useful for publication diagnostics.
  /// How: Treat it as publication metadata.
  /// Example: 0
  @$pb.TagNumber(30)
  $core.int get publicationEntityCount => $_getIZ(29);
  @$pb.TagNumber(30)
  set publicationEntityCount($core.int v) { $_setSignedInt32(29, v); }
  @$pb.TagNumber(30)
  $core.bool hasPublicationEntityCount() => $_has(29);
  @$pb.TagNumber(30)
  void clearPublicationEntityCount() => clearField(30);

  /// What: Count of publication cross-references.
  /// Why: Cross-reference density can indicate publication completeness.
  /// How: Show it in advanced publication views.
  /// Example: 0
  @$pb.TagNumber(31)
  $core.int get publicationXrefCount => $_getIZ(30);
  @$pb.TagNumber(31)
  set publicationXrefCount($core.int v) { $_setSignedInt32(30, v); }
  @$pb.TagNumber(31)
  $core.bool hasPublicationXrefCount() => $_has(30);
  @$pb.TagNumber(31)
  void clearPublicationXrefCount() => clearField(31);

  /// What: Count of recorded publication reviews.
  /// Why: Review completion is a workflow concept and useful summary statistic.
  /// How: Render in Review/Publication status summaries.
  /// Example: 0
  @$pb.TagNumber(32)
  $core.int get publicationReviewCount => $_getIZ(31);
  @$pb.TagNumber(32)
  set publicationReviewCount($core.int v) { $_setSignedInt32(31, v); }
  @$pb.TagNumber(32)
  $core.bool hasPublicationReviewCount() => $_has(31);
  @$pb.TagNumber(32)
  void clearPublicationReviewCount() => clearField(32);

  /// What: Server-local path to the current report markdown output.
  /// Why: Same-machine clients can inspect the raw output directly.
  /// How: Treat it as informational; cross-platform clients should use artifact
  /// refs instead of opening the path.
  /// Example: ""
  @$pb.TagNumber(33)
  $core.String get reportMarkdownPath => $_getSZ(32);
  @$pb.TagNumber(33)
  set reportMarkdownPath($core.String v) { $_setString(32, v); }
  @$pb.TagNumber(33)
  $core.bool hasReportMarkdownPath() => $_has(32);
  @$pb.TagNumber(33)
  void clearReportMarkdownPath() => clearField(33);

  /// What: Server-local path to the current report Typst output.
  /// Why: Publication tooling may render or diff the Typst source.
  /// How: Treat it as informational.
  /// Example: ""
  @$pb.TagNumber(34)
  $core.String get reportTypstPath => $_getSZ(33);
  @$pb.TagNumber(34)
  set reportTypstPath($core.String v) { $_setString(33, v); }
  @$pb.TagNumber(34)
  $core.bool hasReportTypstPath() => $_has(33);
  @$pb.TagNumber(34)
  void clearReportTypstPath() => clearField(34);

  /// What: Server-local path to the current report PDF output.
  /// Why: Same-machine preview and release workflows often open the PDF.
  /// How: Use `open_artifacts` or `ResolveArtifacts` for client-actionable
  /// access.
  /// Example: ""
  @$pb.TagNumber(35)
  $core.String get reportPdfPath => $_getSZ(34);
  @$pb.TagNumber(35)
  set reportPdfPath($core.String v) { $_setString(34, v); }
  @$pb.TagNumber(35)
  $core.bool hasReportPdfPath() => $_has(34);
  @$pb.TagNumber(35)
  void clearReportPdfPath() => clearField(35);

  /// What: Current composition id.
  /// Why: Composition is a governed intermediate object in later phases.
  /// How: Treat it as opaque metadata.
  /// Example: ""
  @$pb.TagNumber(36)
  $core.String get compositionId => $_getSZ(35);
  @$pb.TagNumber(36)
  set compositionId($core.String v) { $_setString(35, v); }
  @$pb.TagNumber(36)
  $core.bool hasCompositionId() => $_has(35);
  @$pb.TagNumber(36)
  void clearCompositionId() => clearField(36);

  /// What: Current composition status.
  /// Why: Draft/Review views need to know whether composition exists or is
  /// stale.
  /// How: Render it in workflow status panes.
  /// Example: ""
  @$pb.TagNumber(37)
  $core.String get compositionStatus => $_getSZ(36);
  @$pb.TagNumber(37)
  set compositionStatus($core.String v) { $_setString(36, v); }
  @$pb.TagNumber(37)
  $core.bool hasCompositionStatus() => $_has(36);
  @$pb.TagNumber(37)
  void clearCompositionStatus() => clearField(37);

  /// What: Composition title.
  /// Why: The report or composition may diverge from the subject title.
  /// How: Show it when composition exists.
  /// Example: ""
  @$pb.TagNumber(38)
  $core.String get compositionTitle => $_getSZ(37);
  @$pb.TagNumber(38)
  set compositionTitle($core.String v) { $_setString(37, v); }
  @$pb.TagNumber(38)
  $core.bool hasCompositionTitle() => $_has(37);
  @$pb.TagNumber(38)
  void clearCompositionTitle() => clearField(38);

  /// What: Short summary of current composition scope.
  /// Why: Users need to know what subset of the subject the composition covers.
  /// How: Render it in Draft/Review summaries.
  /// Example: ""
  @$pb.TagNumber(39)
  $core.String get compositionScopeSummary => $_getSZ(38);
  @$pb.TagNumber(39)
  set compositionScopeSummary($core.String v) { $_setString(38, v); }
  @$pb.TagNumber(39)
  $core.bool hasCompositionScopeSummary() => $_has(38);
  @$pb.TagNumber(39)
  void clearCompositionScopeSummary() => clearField(39);

  /// What: Context fingerprint captured when composition was generated.
  /// Why: Drift detection depends on comparing composition inputs with the
  /// current subject context.
  /// How: Treat it as an opaque comparison fingerprint.
  /// Example: ""
  @$pb.TagNumber(40)
  $core.String get compositionLearningContextSnapshotHash => $_getSZ(39);
  @$pb.TagNumber(40)
  set compositionLearningContextSnapshotHash($core.String v) { $_setString(39, v); }
  @$pb.TagNumber(40)
  $core.bool hasCompositionLearningContextSnapshotHash() => $_has(39);
  @$pb.TagNumber(40)
  void clearCompositionLearningContextSnapshotHash() => clearField(40);

  /// What: Count of units included in the composition.
  /// Why: Draft/publication summaries often need scope size.
  /// How: Show it when composition exists.
  /// Example: 0
  @$pb.TagNumber(41)
  $core.int get compositionIncludedUnitCount => $_getIZ(40);
  @$pb.TagNumber(41)
  set compositionIncludedUnitCount($core.int v) { $_setSignedInt32(40, v); }
  @$pb.TagNumber(41)
  $core.bool hasCompositionIncludedUnitCount() => $_has(40);
  @$pb.TagNumber(41)
  void clearCompositionIncludedUnitCount() => clearField(41);

  /// What: Count of imports selected into the composition.
  /// Why: Compositions can selectively include imported supporting material.
  /// How: Render as advanced composition metadata.
  /// Example: 0
  @$pb.TagNumber(42)
  $core.int get compositionSelectedImportCount => $_getIZ(41);
  @$pb.TagNumber(42)
  set compositionSelectedImportCount($core.int v) { $_setSignedInt32(41, v); }
  @$pb.TagNumber(42)
  $core.bool hasCompositionSelectedImportCount() => $_has(41);
  @$pb.TagNumber(42)
  void clearCompositionSelectedImportCount() => clearField(42);

  /// What: Count of composition sections.
  /// Why: Draft/publication views need a quick measure of structure size.
  /// How: Show it when composition exists.
  /// Example: 0
  @$pb.TagNumber(43)
  $core.int get compositionSectionCount => $_getIZ(42);
  @$pb.TagNumber(43)
  set compositionSectionCount($core.int v) { $_setSignedInt32(42, v); }
  @$pb.TagNumber(43)
  $core.bool hasCompositionSectionCount() => $_has(42);
  @$pb.TagNumber(43)
  void clearCompositionSectionCount() => clearField(43);

  /// What: Count of source collections attached to the subject.
  /// Why: The workflow tracks both individual sources and grouped collections.
  /// How: Surface it in Gather status summaries.
  /// Example: 1
  @$pb.TagNumber(44)
  $core.int get sourceCollectionCount => $_getIZ(43);
  @$pb.TagNumber(44)
  set sourceCollectionCount($core.int v) { $_setSignedInt32(43, v); }
  @$pb.TagNumber(44)
  $core.bool hasSourceCollectionCount() => $_has(43);
  @$pb.TagNumber(44)
  void clearSourceCollectionCount() => clearField(44);

  /// What: Count of staged sources not yet admitted into the corpus.
  /// Why: Gather workflows often stage material before admission.
  /// How: Highlight non-zero values in Gather.
  /// Example: 0
  @$pb.TagNumber(45)
  $core.int get stagedSourceCount => $_getIZ(44);
  @$pb.TagNumber(45)
  set stagedSourceCount($core.int v) { $_setSignedInt32(44, v); }
  @$pb.TagNumber(45)
  $core.bool hasStagedSourceCount() => $_has(44);
  @$pb.TagNumber(45)
  void clearStagedSourceCount() => clearField(45);

  /// What: Preview lines for source collections.
  /// Why: Subject lists sometimes need richer preview text than counts alone.
  /// How: Render each string as an already-assembled preview line.
  /// Example: ["All Gather Sources"]
  @$pb.TagNumber(46)
  $core.List<$core.String> get sourceCollectionPreviewLines => $_getList(45);

  /// What: Preview lines for the current source inventory.
  /// Why: The summary can expose source names without opening the subject.
  /// How: Render each string as one line of preview text.
  /// Example: ["City bus prose v2.md"]
  @$pb.TagNumber(47)
  $core.List<$core.String> get sourcePreviewLines => $_getList(46);

  /// What: Preview lines for staged sources.
  /// Why: Users may need to see staged-but-not-admitted material in lists.
  /// How: Render each string as one preview line.
  /// Example: []
  @$pb.TagNumber(48)
  $core.List<$core.String> get stagedSourcePreviewLines => $_getList(47);

  /// What: Preview lines for units in the subject.
  /// Why: A small unit preview makes subject selection more informative.
  /// How: Render them as ready-to-display lines.
  /// Example: ["Smart City Travel"]
  @$pb.TagNumber(49)
  $core.List<$core.String> get unitPreviewLines => $_getList(48);

  /// What: Preview lines for subject deltas.
  /// Why: Deltas are a key part of Gather and Review diagnostics.
  /// How: Render each entry as already-composed human text.
  /// Example: ["definition: Smart City Travel"]
  @$pb.TagNumber(50)
  $core.List<$core.String> get deltaPreviewLines => $_getList(49);

  /// What: Preview lines for pending imports.
  /// Why: Gather needs to surface unresolved imports quickly.
  /// How: Render the provided human-readable lines.
  /// Example: []
  @$pb.TagNumber(51)
  $core.List<$core.String> get pendingImportPreviewLines => $_getList(50);

  /// What: Preview lines for completed imports.
  /// Why: Imports are often more understandable as names than counts.
  /// How: Render each string as one preview line.
  /// Example: ["City bus prose v2.md"]
  @$pb.TagNumber(52)
  $core.List<$core.String> get importPreviewLines => $_getList(51);

  /// What: Whether this summary is a placeholder rather than a fully realized
  /// subject.
  /// Why: Some views reserve space or signal empty states using placeholder
  /// summaries.
  /// How: Treat `true` as non-actionable unless the UI explicitly supports
  /// placeholders.
  /// Example: false
  @$pb.TagNumber(53)
  $core.bool get isPlaceholder => $_getBF(52);
  @$pb.TagNumber(53)
  set isPlaceholder($core.bool v) { $_setBool(52, v); }
  @$pb.TagNumber(53)
  $core.bool hasIsPlaceholder() => $_has(52);
  @$pb.TagNumber(53)
  void clearIsPlaceholder() => clearField(53);
}

/// What: One labeled value row used across status and structured panes.
/// Why: Many workstation projections are semantically key/value data rather than
/// free-form text.
/// How: Render `label` and `value` as one structured row.
/// Valid Example:
///   {"label": "Mode", "value": "Live subject workflow"}
class KeyValueRow extends $pb.GeneratedMessage {
  factory KeyValueRow({
    $core.String? label,
    $core.String? value,
  }) {
    final $result = create();
    if (label != null) {
      $result.label = label;
    }
    if (value != null) {
      $result.value = value;
    }
    return $result;
  }
  KeyValueRow._() : super();
  factory KeyValueRow.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory KeyValueRow.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'KeyValueRow', package: const $pb.PackageName(_omitMessageNames ? '' : 'realized.workstation.subjectworkflow.v1'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'label')
    ..aOS(2, _omitFieldNames ? '' : 'value')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  KeyValueRow clone() => KeyValueRow()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  KeyValueRow copyWith(void Function(KeyValueRow) updates) => super.copyWith((message) => updates(message as KeyValueRow)) as KeyValueRow;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static KeyValueRow create() => KeyValueRow._();
  KeyValueRow createEmptyInstance() => create();
  static $pb.PbList<KeyValueRow> createRepeated() => $pb.PbList<KeyValueRow>();
  @$core.pragma('dart2js:noInline')
  static KeyValueRow getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<KeyValueRow>(create);
  static KeyValueRow? _defaultInstance;

  /// What: Human-readable field label.
  /// Why: Structured rows need a stable display label.
  /// How: Render it as the left-hand column or key text.
  /// Example: "Mode"
  @$pb.TagNumber(1)
  $core.String get label => $_getSZ(0);
  @$pb.TagNumber(1)
  set label($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasLabel() => $_has(0);
  @$pb.TagNumber(1)
  void clearLabel() => clearField(1);

  /// What: Human-readable field value.
  /// Why: Structured rows need the projected value text.
  /// How: Render it as the right-hand column or value text.
  /// Example: "Live subject workflow"
  @$pb.TagNumber(2)
  $core.String get value => $_getSZ(1);
  @$pb.TagNumber(2)
  set value($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasValue() => $_has(1);
  @$pb.TagNumber(2)
  void clearValue() => clearField(2);
}

/// What: One gate/action control shown in the current-step section.
/// Why: Current-step guidance needs explicit actionable affordances, not just
/// prose.
/// How: Render it using `display_kind`, show `label`, and submit `key` when the
/// user activates it.
/// Valid Example:
///   {
///     "display_kind": "BUTTON",
///     "action_kind": "subject_action",
///     "key": "approve_import",
///     "label": "Approve Import",
///     "enabled": true
///   }
class SubjectGateAction extends $pb.GeneratedMessage {
  factory SubjectGateAction({
    SubjectGateAction_DisplayKind? displayKind,
    $core.String? actionKind,
    $core.String? key,
    $core.String? label,
    $core.bool? enabled,
  }) {
    final $result = create();
    if (displayKind != null) {
      $result.displayKind = displayKind;
    }
    if (actionKind != null) {
      $result.actionKind = actionKind;
    }
    if (key != null) {
      $result.key = key;
    }
    if (label != null) {
      $result.label = label;
    }
    if (enabled != null) {
      $result.enabled = enabled;
    }
    return $result;
  }
  SubjectGateAction._() : super();
  factory SubjectGateAction.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory SubjectGateAction.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'SubjectGateAction', package: const $pb.PackageName(_omitMessageNames ? '' : 'realized.workstation.subjectworkflow.v1'), createEmptyInstance: create)
    ..e<SubjectGateAction_DisplayKind>(1, _omitFieldNames ? '' : 'displayKind', $pb.PbFieldType.OE, defaultOrMaker: SubjectGateAction_DisplayKind.DISPLAY_KIND_UNSPECIFIED, valueOf: SubjectGateAction_DisplayKind.valueOf, enumValues: SubjectGateAction_DisplayKind.values)
    ..aOS(2, _omitFieldNames ? '' : 'actionKind')
    ..aOS(3, _omitFieldNames ? '' : 'key')
    ..aOS(4, _omitFieldNames ? '' : 'label')
    ..aOB(5, _omitFieldNames ? '' : 'enabled')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  SubjectGateAction clone() => SubjectGateAction()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  SubjectGateAction copyWith(void Function(SubjectGateAction) updates) => super.copyWith((message) => updates(message as SubjectGateAction)) as SubjectGateAction;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static SubjectGateAction create() => SubjectGateAction._();
  SubjectGateAction createEmptyInstance() => create();
  static $pb.PbList<SubjectGateAction> createRepeated() => $pb.PbList<SubjectGateAction>();
  @$core.pragma('dart2js:noInline')
  static SubjectGateAction getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<SubjectGateAction>(create);
  static SubjectGateAction? _defaultInstance;

  /// What: Rendering hint for the action.
  /// Why: UIs need a consistent semantic style cue.
  /// How: Render it according to the enum value.
  /// Example: "BUTTON"
  @$pb.TagNumber(1)
  SubjectGateAction_DisplayKind get displayKind => $_getN(0);
  @$pb.TagNumber(1)
  set displayKind(SubjectGateAction_DisplayKind v) { setField(1, v); }
  @$pb.TagNumber(1)
  $core.bool hasDisplayKind() => $_has(0);
  @$pb.TagNumber(1)
  void clearDisplayKind() => clearField(1);

  /// What: Category of action semantics.
  /// Why: Some clients distinguish subject actions from other kinds of action.
  /// How: Treat it as opaque workflow metadata.
  /// Example: "subject_action"
  @$pb.TagNumber(2)
  $core.String get actionKind => $_getSZ(1);
  @$pb.TagNumber(2)
  set actionKind($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasActionKind() => $_has(1);
  @$pb.TagNumber(2)
  void clearActionKind() => clearField(2);

  /// What: Canonical action key.
  /// Why: The workflow service applies actions by key.
  /// How: Submit it back through `ApplySubjectAction`.
  /// Example: "approve_import"
  @$pb.TagNumber(3)
  $core.String get key => $_getSZ(2);
  @$pb.TagNumber(3)
  set key($core.String v) { $_setString(2, v); }
  @$pb.TagNumber(3)
  $core.bool hasKey() => $_has(2);
  @$pb.TagNumber(3)
  void clearKey() => clearField(3);

  /// What: Human-readable control label.
  /// Why: Users need a display label for the affordance.
  /// How: Render it directly on the control.
  /// Example: "Approve Import"
  @$pb.TagNumber(4)
  $core.String get label => $_getSZ(3);
  @$pb.TagNumber(4)
  set label($core.String v) { $_setString(3, v); }
  @$pb.TagNumber(4)
  $core.bool hasLabel() => $_has(3);
  @$pb.TagNumber(4)
  void clearLabel() => clearField(4);

  /// What: Whether the action is currently allowed.
  /// Why: The service, not the UI, owns action availability.
  /// How: Disable or hide the control according to client policy.
  /// Example: true
  @$pb.TagNumber(5)
  $core.bool get enabled => $_getBF(4);
  @$pb.TagNumber(5)
  set enabled($core.bool v) { $_setBool(4, v); }
  @$pb.TagNumber(5)
  $core.bool hasEnabled() => $_has(4);
  @$pb.TagNumber(5)
  void clearEnabled() => clearField(5);
}

/// What: One non-primary action listed in a phase control bundle.
/// Why: More-actions areas need stable action metadata.
/// How: Render the label and submit the key through `ApplySubjectAction`.
/// Valid Example:
///   {"key": "refresh_subjects", "label": "Refresh Subjects", "enabled": true}
class SubjectActionSpec extends $pb.GeneratedMessage {
  factory SubjectActionSpec({
    $core.String? key,
    $core.String? label,
    $core.bool? enabled,
  }) {
    final $result = create();
    if (key != null) {
      $result.key = key;
    }
    if (label != null) {
      $result.label = label;
    }
    if (enabled != null) {
      $result.enabled = enabled;
    }
    return $result;
  }
  SubjectActionSpec._() : super();
  factory SubjectActionSpec.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory SubjectActionSpec.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'SubjectActionSpec', package: const $pb.PackageName(_omitMessageNames ? '' : 'realized.workstation.subjectworkflow.v1'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'key')
    ..aOS(2, _omitFieldNames ? '' : 'label')
    ..aOB(3, _omitFieldNames ? '' : 'enabled')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  SubjectActionSpec clone() => SubjectActionSpec()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  SubjectActionSpec copyWith(void Function(SubjectActionSpec) updates) => super.copyWith((message) => updates(message as SubjectActionSpec)) as SubjectActionSpec;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static SubjectActionSpec create() => SubjectActionSpec._();
  SubjectActionSpec createEmptyInstance() => create();
  static $pb.PbList<SubjectActionSpec> createRepeated() => $pb.PbList<SubjectActionSpec>();
  @$core.pragma('dart2js:noInline')
  static SubjectActionSpec getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<SubjectActionSpec>(create);
  static SubjectActionSpec? _defaultInstance;

  /// What: Canonical action key.
  /// Why: The action service applies actions by key.
  /// How: Submit it as `action_key`.
  /// Example: "refresh_subjects"
  @$pb.TagNumber(1)
  $core.String get key => $_getSZ(0);
  @$pb.TagNumber(1)
  set key($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasKey() => $_has(0);
  @$pb.TagNumber(1)
  void clearKey() => clearField(1);

  /// What: Human-readable action label.
  /// Why: Users need to understand what clicking the control will do.
  /// How: Render it on the control surface.
  /// Example: "Refresh Subjects"
  @$pb.TagNumber(2)
  $core.String get label => $_getSZ(1);
  @$pb.TagNumber(2)
  set label($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasLabel() => $_has(1);
  @$pb.TagNumber(2)
  void clearLabel() => clearField(2);

  /// What: Whether the action is currently enabled.
  /// Why: The service should be the authority for action availability.
  /// How: Disable or hide it according to client policy.
  /// Example: true
  @$pb.TagNumber(3)
  $core.bool get enabled => $_getBF(2);
  @$pb.TagNumber(3)
  set enabled($core.bool v) { $_setBool(2, v); }
  @$pb.TagNumber(3)
  $core.bool hasEnabled() => $_has(2);
  @$pb.TagNumber(3)
  void clearEnabled() => clearField(3);
}

/// What: One selectable option within a select control.
/// Why: Select fields need stable `(label, value)` pairs from the service.
/// How: Render `label` and submit/store `value`.
/// Valid Example:
///   {"label": "All Gather Sources", "value": "all_gather_sources"}
class SubjectOption extends $pb.GeneratedMessage {
  factory SubjectOption({
    $core.String? label,
    $core.String? value,
  }) {
    final $result = create();
    if (label != null) {
      $result.label = label;
    }
    if (value != null) {
      $result.value = value;
    }
    return $result;
  }
  SubjectOption._() : super();
  factory SubjectOption.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory SubjectOption.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'SubjectOption', package: const $pb.PackageName(_omitMessageNames ? '' : 'realized.workstation.subjectworkflow.v1'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'label')
    ..aOS(2, _omitFieldNames ? '' : 'value')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  SubjectOption clone() => SubjectOption()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  SubjectOption copyWith(void Function(SubjectOption) updates) => super.copyWith((message) => updates(message as SubjectOption)) as SubjectOption;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static SubjectOption create() => SubjectOption._();
  SubjectOption createEmptyInstance() => create();
  static $pb.PbList<SubjectOption> createRepeated() => $pb.PbList<SubjectOption>();
  @$core.pragma('dart2js:noInline')
  static SubjectOption getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<SubjectOption>(create);
  static SubjectOption? _defaultInstance;

  /// What: Human-readable option label.
  /// Why: Users need display text for the option.
  /// How: Show it in the select dropdown or menu.
  /// Example: "All Gather Sources"
  @$pb.TagNumber(1)
  $core.String get label => $_getSZ(0);
  @$pb.TagNumber(1)
  set label($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasLabel() => $_has(0);
  @$pb.TagNumber(1)
  void clearLabel() => clearField(1);

  /// What: Canonical option value.
  /// Why: The workflow logic operates on stable symbolic values.
  /// How: Send or persist this value instead of the label.
  /// Example: "all_gather_sources"
  @$pb.TagNumber(2)
  $core.String get value => $_getSZ(1);
  @$pb.TagNumber(2)
  set value($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasValue() => $_has(1);
  @$pb.TagNumber(2)
  void clearValue() => clearField(2);
}

/// What: One selectable option inside a multi-item selection list.
/// Why: Selection lists need to show both available options and current
/// selection state.
/// How: Render the label and reflect `selected` in the row state.
/// Valid Example:
///   {"label": "Smart City Travel", "value": "smart_city_travel", "selected": true}
class SubjectSelectionOption extends $pb.GeneratedMessage {
  factory SubjectSelectionOption({
    $core.String? label,
    $core.String? value,
    $core.bool? selected,
  }) {
    final $result = create();
    if (label != null) {
      $result.label = label;
    }
    if (value != null) {
      $result.value = value;
    }
    if (selected != null) {
      $result.selected = selected;
    }
    return $result;
  }
  SubjectSelectionOption._() : super();
  factory SubjectSelectionOption.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory SubjectSelectionOption.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'SubjectSelectionOption', package: const $pb.PackageName(_omitMessageNames ? '' : 'realized.workstation.subjectworkflow.v1'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'label')
    ..aOS(2, _omitFieldNames ? '' : 'value')
    ..aOB(3, _omitFieldNames ? '' : 'selected')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  SubjectSelectionOption clone() => SubjectSelectionOption()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  SubjectSelectionOption copyWith(void Function(SubjectSelectionOption) updates) => super.copyWith((message) => updates(message as SubjectSelectionOption)) as SubjectSelectionOption;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static SubjectSelectionOption create() => SubjectSelectionOption._();
  SubjectSelectionOption createEmptyInstance() => create();
  static $pb.PbList<SubjectSelectionOption> createRepeated() => $pb.PbList<SubjectSelectionOption>();
  @$core.pragma('dart2js:noInline')
  static SubjectSelectionOption getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<SubjectSelectionOption>(create);
  static SubjectSelectionOption? _defaultInstance;

  /// What: Human-readable option label.
  /// Why: Selection rows need readable text.
  /// How: Render it directly.
  /// Example: "Smart City Travel"
  @$pb.TagNumber(1)
  $core.String get label => $_getSZ(0);
  @$pb.TagNumber(1)
  set label($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasLabel() => $_has(0);
  @$pb.TagNumber(1)
  void clearLabel() => clearField(1);

  /// What: Canonical option value.
  /// Why: Selection toggles target stable ids rather than display text.
  /// How: Use it to derive the action target.
  /// Example: "smart_city_travel"
  @$pb.TagNumber(2)
  $core.String get value => $_getSZ(1);
  @$pb.TagNumber(2)
  set value($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasValue() => $_has(1);
  @$pb.TagNumber(2)
  void clearValue() => clearField(2);

  /// What: Whether this option is currently selected.
  /// Why: Clients need authoritative current state for selection lists.
  /// How: Reflect it in row styling or checkbox state.
  /// Example: true
  @$pb.TagNumber(3)
  $core.bool get selected => $_getBF(2);
  @$pb.TagNumber(3)
  set selected($core.bool v) { $_setBool(2, v); }
  @$pb.TagNumber(3)
  $core.bool hasSelected() => $_has(2);
  @$pb.TagNumber(3)
  void clearSelected() => clearField(3);
}

/// What: Select control specification for one workflow phase.
/// Why: The service owns available select inputs and their options.
/// How: Render one select widget bound to `key`.
/// Valid Example:
///   {
///     "key": "source_set",
///     "label": "Source Set",
///     "value": "all_gather_sources",
///     "options": [{"label": "All Gather Sources", "value": "all_gather_sources"}],
///     "enabled": true
///   }
class SubjectSelectSpecView extends $pb.GeneratedMessage {
  factory SubjectSelectSpecView({
    $core.String? key,
    $core.String? label,
    $core.String? value,
    $core.Iterable<SubjectOption>? options,
    $core.bool? enabled,
  }) {
    final $result = create();
    if (key != null) {
      $result.key = key;
    }
    if (label != null) {
      $result.label = label;
    }
    if (value != null) {
      $result.value = value;
    }
    if (options != null) {
      $result.options.addAll(options);
    }
    if (enabled != null) {
      $result.enabled = enabled;
    }
    return $result;
  }
  SubjectSelectSpecView._() : super();
  factory SubjectSelectSpecView.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory SubjectSelectSpecView.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'SubjectSelectSpecView', package: const $pb.PackageName(_omitMessageNames ? '' : 'realized.workstation.subjectworkflow.v1'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'key')
    ..aOS(2, _omitFieldNames ? '' : 'label')
    ..aOS(3, _omitFieldNames ? '' : 'value')
    ..pc<SubjectOption>(4, _omitFieldNames ? '' : 'options', $pb.PbFieldType.PM, subBuilder: SubjectOption.create)
    ..aOB(5, _omitFieldNames ? '' : 'enabled')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  SubjectSelectSpecView clone() => SubjectSelectSpecView()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  SubjectSelectSpecView copyWith(void Function(SubjectSelectSpecView) updates) => super.copyWith((message) => updates(message as SubjectSelectSpecView)) as SubjectSelectSpecView;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static SubjectSelectSpecView create() => SubjectSelectSpecView._();
  SubjectSelectSpecView createEmptyInstance() => create();
  static $pb.PbList<SubjectSelectSpecView> createRepeated() => $pb.PbList<SubjectSelectSpecView>();
  @$core.pragma('dart2js:noInline')
  static SubjectSelectSpecView getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<SubjectSelectSpecView>(create);
  static SubjectSelectSpecView? _defaultInstance;

  /// What: Canonical control key.
  /// Why: Clients need a stable identity for the select.
  /// How: Use it when storing local widget state.
  /// Example: "source_set"
  @$pb.TagNumber(1)
  $core.String get key => $_getSZ(0);
  @$pb.TagNumber(1)
  set key($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasKey() => $_has(0);
  @$pb.TagNumber(1)
  void clearKey() => clearField(1);

  /// What: Human-readable control label.
  /// Why: Users need to know what the select changes.
  /// How: Render it as the field label.
  /// Example: "Source Set"
  @$pb.TagNumber(2)
  $core.String get label => $_getSZ(1);
  @$pb.TagNumber(2)
  set label($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasLabel() => $_has(1);
  @$pb.TagNumber(2)
  void clearLabel() => clearField(2);

  /// What: Currently selected option value.
  /// Why: The service is the source of truth for the active selection.
  /// How: Set the select widget's current value to it.
  /// Example: "all_gather_sources"
  @$pb.TagNumber(3)
  $core.String get value => $_getSZ(2);
  @$pb.TagNumber(3)
  set value($core.String v) { $_setString(2, v); }
  @$pb.TagNumber(3)
  $core.bool hasValue() => $_has(2);
  @$pb.TagNumber(3)
  void clearValue() => clearField(3);

  /// What: Allowed options for the select.
  /// Why: Workflow semantics determine valid choices.
  /// How: Populate the dropdown from this sequence.
  /// Example: [{"label": "All Gather Sources", "value": "all_gather_sources"}]
  @$pb.TagNumber(4)
  $core.List<SubjectOption> get options => $_getList(3);

  /// What: Whether the select is currently interactive.
  /// Why: Phase state sometimes makes a control read-only.
  /// How: Disable the widget when false.
  /// Example: true
  @$pb.TagNumber(5)
  $core.bool get enabled => $_getBF(4);
  @$pb.TagNumber(5)
  set enabled($core.bool v) { $_setBool(4, v); }
  @$pb.TagNumber(5)
  $core.bool hasEnabled() => $_has(4);
  @$pb.TagNumber(5)
  void clearEnabled() => clearField(5);
}

/// What: Switch/toggle control specification for one workflow phase.
/// Why: Some phase controls are boolean rather than multi-valued.
/// How: Render a switch or checkbox bound to `key`.
/// Valid Example:
///   {"key": "include_sources", "label": "Include Sources", "value": true, "enabled": true}
class SubjectSwitchSpecView extends $pb.GeneratedMessage {
  factory SubjectSwitchSpecView({
    $core.String? key,
    $core.String? label,
    $core.bool? value,
    $core.bool? enabled,
  }) {
    final $result = create();
    if (key != null) {
      $result.key = key;
    }
    if (label != null) {
      $result.label = label;
    }
    if (value != null) {
      $result.value = value;
    }
    if (enabled != null) {
      $result.enabled = enabled;
    }
    return $result;
  }
  SubjectSwitchSpecView._() : super();
  factory SubjectSwitchSpecView.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory SubjectSwitchSpecView.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'SubjectSwitchSpecView', package: const $pb.PackageName(_omitMessageNames ? '' : 'realized.workstation.subjectworkflow.v1'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'key')
    ..aOS(2, _omitFieldNames ? '' : 'label')
    ..aOB(3, _omitFieldNames ? '' : 'value')
    ..aOB(4, _omitFieldNames ? '' : 'enabled')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  SubjectSwitchSpecView clone() => SubjectSwitchSpecView()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  SubjectSwitchSpecView copyWith(void Function(SubjectSwitchSpecView) updates) => super.copyWith((message) => updates(message as SubjectSwitchSpecView)) as SubjectSwitchSpecView;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static SubjectSwitchSpecView create() => SubjectSwitchSpecView._();
  SubjectSwitchSpecView createEmptyInstance() => create();
  static $pb.PbList<SubjectSwitchSpecView> createRepeated() => $pb.PbList<SubjectSwitchSpecView>();
  @$core.pragma('dart2js:noInline')
  static SubjectSwitchSpecView getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<SubjectSwitchSpecView>(create);
  static SubjectSwitchSpecView? _defaultInstance;

  /// What: Canonical control key.
  /// Why: Clients need a stable toggle identity.
  /// How: Use it in local widget state and event routing.
  /// Example: "include_sources"
  @$pb.TagNumber(1)
  $core.String get key => $_getSZ(0);
  @$pb.TagNumber(1)
  set key($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasKey() => $_has(0);
  @$pb.TagNumber(1)
  void clearKey() => clearField(1);

  /// What: Human-readable control label.
  /// Why: Users need to know what the toggle changes.
  /// How: Render it beside the switch.
  /// Example: "Include Sources"
  @$pb.TagNumber(2)
  $core.String get label => $_getSZ(1);
  @$pb.TagNumber(2)
  set label($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasLabel() => $_has(1);
  @$pb.TagNumber(2)
  void clearLabel() => clearField(2);

  /// What: Current boolean value.
  /// Why: The service owns current toggle state.
  /// How: Set the widget state from it.
  /// Example: true
  @$pb.TagNumber(3)
  $core.bool get value => $_getBF(2);
  @$pb.TagNumber(3)
  set value($core.bool v) { $_setBool(2, v); }
  @$pb.TagNumber(3)
  $core.bool hasValue() => $_has(2);
  @$pb.TagNumber(3)
  void clearValue() => clearField(3);

  /// What: Whether the toggle is interactive.
  /// Why: Some workflow states make toggles read-only.
  /// How: Disable the widget when false.
  /// Example: true
  @$pb.TagNumber(4)
  $core.bool get enabled => $_getBF(3);
  @$pb.TagNumber(4)
  set enabled($core.bool v) { $_setBool(3, v); }
  @$pb.TagNumber(4)
  $core.bool hasEnabled() => $_has(3);
  @$pb.TagNumber(4)
  void clearEnabled() => clearField(4);
}

/// What: Multi-row selection control specification.
/// Why: Some workflow selections are better represented as explicit lists than
/// as dropdowns.
/// How: Render the options and submit actions derived from
/// `action_key_prefix + option.value`.
/// Valid Example:
///   {
///     "key": "subject_imports",
///     "label": "Imports",
///     "action_key_prefix": "select_import:",
///     "options": [{"label": "City bus prose v2.md", "value": "import_1", "selected": true}],
///     "enabled": true
///   }
class SubjectSelectionListSpecView extends $pb.GeneratedMessage {
  factory SubjectSelectionListSpecView({
    $core.String? key,
    $core.String? label,
    $core.String? actionKeyPrefix,
    $core.Iterable<SubjectSelectionOption>? options,
    $core.bool? enabled,
  }) {
    final $result = create();
    if (key != null) {
      $result.key = key;
    }
    if (label != null) {
      $result.label = label;
    }
    if (actionKeyPrefix != null) {
      $result.actionKeyPrefix = actionKeyPrefix;
    }
    if (options != null) {
      $result.options.addAll(options);
    }
    if (enabled != null) {
      $result.enabled = enabled;
    }
    return $result;
  }
  SubjectSelectionListSpecView._() : super();
  factory SubjectSelectionListSpecView.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory SubjectSelectionListSpecView.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'SubjectSelectionListSpecView', package: const $pb.PackageName(_omitMessageNames ? '' : 'realized.workstation.subjectworkflow.v1'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'key')
    ..aOS(2, _omitFieldNames ? '' : 'label')
    ..aOS(3, _omitFieldNames ? '' : 'actionKeyPrefix')
    ..pc<SubjectSelectionOption>(4, _omitFieldNames ? '' : 'options', $pb.PbFieldType.PM, subBuilder: SubjectSelectionOption.create)
    ..aOB(5, _omitFieldNames ? '' : 'enabled')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  SubjectSelectionListSpecView clone() => SubjectSelectionListSpecView()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  SubjectSelectionListSpecView copyWith(void Function(SubjectSelectionListSpecView) updates) => super.copyWith((message) => updates(message as SubjectSelectionListSpecView)) as SubjectSelectionListSpecView;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static SubjectSelectionListSpecView create() => SubjectSelectionListSpecView._();
  SubjectSelectionListSpecView createEmptyInstance() => create();
  static $pb.PbList<SubjectSelectionListSpecView> createRepeated() => $pb.PbList<SubjectSelectionListSpecView>();
  @$core.pragma('dart2js:noInline')
  static SubjectSelectionListSpecView getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<SubjectSelectionListSpecView>(create);
  static SubjectSelectionListSpecView? _defaultInstance;

  /// What: Canonical selection-list key.
  /// Why: Clients need a stable identity for the list.
  /// How: Use it when storing local UI state.
  /// Example: "subject_imports"
  @$pb.TagNumber(1)
  $core.String get key => $_getSZ(0);
  @$pb.TagNumber(1)
  set key($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasKey() => $_has(0);
  @$pb.TagNumber(1)
  void clearKey() => clearField(1);

  /// What: Human-readable selection-list label.
  /// Why: Users need to know what the list controls.
  /// How: Render it as the section label.
  /// Example: "Imports"
  @$pb.TagNumber(2)
  $core.String get label => $_getSZ(1);
  @$pb.TagNumber(2)
  set label($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasLabel() => $_has(1);
  @$pb.TagNumber(2)
  void clearLabel() => clearField(2);

  /// What: Prefix used to derive per-option action keys.
  /// Why: Interaction with selection lists often maps to action-key prefixes.
  /// How: Concatenate it with the chosen option value if your client models row
  /// actions locally.
  /// Example: "select_import:"
  @$pb.TagNumber(3)
  $core.String get actionKeyPrefix => $_getSZ(2);
  @$pb.TagNumber(3)
  set actionKeyPrefix($core.String v) { $_setString(2, v); }
  @$pb.TagNumber(3)
  $core.bool hasActionKeyPrefix() => $_has(2);
  @$pb.TagNumber(3)
  void clearActionKeyPrefix() => clearField(3);

  /// What: Available options and their current selection state.
  /// Why: The service defines the valid selection surface.
  /// How: Render one row per option.
  /// Example: [{"label":"City bus prose v2.md","value":"import_1","selected":true}]
  @$pb.TagNumber(4)
  $core.List<SubjectSelectionOption> get options => $_getList(3);

  /// What: Whether the selection list is interactive.
  /// Why: Some workflow states allow inspection but not mutation.
  /// How: Disable row interaction when false.
  /// Example: true
  @$pb.TagNumber(5)
  $core.bool get enabled => $_getBF(4);
  @$pb.TagNumber(5)
  set enabled($core.bool v) { $_setBool(4, v); }
  @$pb.TagNumber(5)
  $core.bool hasEnabled() => $_has(4);
  @$pb.TagNumber(5)
  void clearEnabled() => clearField(5);
}

/// What: One row in a structured table pane/control.
/// Why: Several workstation projections are tabular rather than narrative.
/// How: Render each string in `cells` under the corresponding table column.
/// Valid Example:
///   {"cells": ["report.pdf", "ready"]}
class SubjectTableRow extends $pb.GeneratedMessage {
  factory SubjectTableRow({
    $core.Iterable<$core.String>? cells,
  }) {
    final $result = create();
    if (cells != null) {
      $result.cells.addAll(cells);
    }
    return $result;
  }
  SubjectTableRow._() : super();
  factory SubjectTableRow.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory SubjectTableRow.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'SubjectTableRow', package: const $pb.PackageName(_omitMessageNames ? '' : 'realized.workstation.subjectworkflow.v1'), createEmptyInstance: create)
    ..pPS(1, _omitFieldNames ? '' : 'cells')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  SubjectTableRow clone() => SubjectTableRow()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  SubjectTableRow copyWith(void Function(SubjectTableRow) updates) => super.copyWith((message) => updates(message as SubjectTableRow)) as SubjectTableRow;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static SubjectTableRow create() => SubjectTableRow._();
  SubjectTableRow createEmptyInstance() => create();
  static $pb.PbList<SubjectTableRow> createRepeated() => $pb.PbList<SubjectTableRow>();
  @$core.pragma('dart2js:noInline')
  static SubjectTableRow getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<SubjectTableRow>(create);
  static SubjectTableRow? _defaultInstance;

  /// What: Ordered row cell values.
  /// Why: Tabular views need stable cell ordering.
  /// How: Render them against the table's declared columns.
  /// Example: ["report.pdf", "ready"]
  @$pb.TagNumber(1)
  $core.List<$core.String> get cells => $_getList(0);
}

/// What: Structured table specification within a control bundle.
/// Why: Some phases expose tabular controls or diagnostics rather than plain
/// text.
/// How: Render a table with the declared columns and rows.
/// Valid Example:
///   {
///     "key": "publication_build_artifacts",
///     "label": "Build Artifacts",
///     "columns": ["Artifact", "Status"],
///     "rows": [{"cells": ["report.pdf", "ready"]}],
///     "enabled": true
///   }
class SubjectTableSpecView extends $pb.GeneratedMessage {
  factory SubjectTableSpecView({
    $core.String? key,
    $core.String? label,
    $core.Iterable<$core.String>? columns,
    $core.Iterable<SubjectTableRow>? rows,
    $core.bool? enabled,
  }) {
    final $result = create();
    if (key != null) {
      $result.key = key;
    }
    if (label != null) {
      $result.label = label;
    }
    if (columns != null) {
      $result.columns.addAll(columns);
    }
    if (rows != null) {
      $result.rows.addAll(rows);
    }
    if (enabled != null) {
      $result.enabled = enabled;
    }
    return $result;
  }
  SubjectTableSpecView._() : super();
  factory SubjectTableSpecView.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory SubjectTableSpecView.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'SubjectTableSpecView', package: const $pb.PackageName(_omitMessageNames ? '' : 'realized.workstation.subjectworkflow.v1'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'key')
    ..aOS(2, _omitFieldNames ? '' : 'label')
    ..pPS(3, _omitFieldNames ? '' : 'columns')
    ..pc<SubjectTableRow>(4, _omitFieldNames ? '' : 'rows', $pb.PbFieldType.PM, subBuilder: SubjectTableRow.create)
    ..aOB(5, _omitFieldNames ? '' : 'enabled')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  SubjectTableSpecView clone() => SubjectTableSpecView()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  SubjectTableSpecView copyWith(void Function(SubjectTableSpecView) updates) => super.copyWith((message) => updates(message as SubjectTableSpecView)) as SubjectTableSpecView;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static SubjectTableSpecView create() => SubjectTableSpecView._();
  SubjectTableSpecView createEmptyInstance() => create();
  static $pb.PbList<SubjectTableSpecView> createRepeated() => $pb.PbList<SubjectTableSpecView>();
  @$core.pragma('dart2js:noInline')
  static SubjectTableSpecView getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<SubjectTableSpecView>(create);
  static SubjectTableSpecView? _defaultInstance;

  /// What: Canonical table key.
  /// Why: Clients need a stable identity for refresh and lookup.
  /// How: Use it as the widget id or lookup key.
  /// Example: "publication_build_artifacts"
  @$pb.TagNumber(1)
  $core.String get key => $_getSZ(0);
  @$pb.TagNumber(1)
  set key($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasKey() => $_has(0);
  @$pb.TagNumber(1)
  void clearKey() => clearField(1);

  /// What: Human-readable table label.
  /// Why: Users need to know what the table represents.
  /// How: Render it as the table title.
  /// Example: "Build Artifacts"
  @$pb.TagNumber(2)
  $core.String get label => $_getSZ(1);
  @$pb.TagNumber(2)
  set label($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasLabel() => $_has(1);
  @$pb.TagNumber(2)
  void clearLabel() => clearField(2);

  /// What: Ordered column titles.
  /// Why: Structured tables need explicit headers.
  /// How: Render them as header cells.
  /// Example: ["Artifact", "Status"]
  @$pb.TagNumber(3)
  $core.List<$core.String> get columns => $_getList(2);

  /// What: Ordered table rows.
  /// Why: The service projects tabular content directly.
  /// How: Render them beneath `columns`.
  /// Example: [{"cells": ["report.pdf", "ready"]}]
  @$pb.TagNumber(4)
  $core.List<SubjectTableRow> get rows => $_getList(3);

  /// What: Whether the table or related actions are currently enabled.
  /// Why: Some tables participate in editable control surfaces.
  /// How: Treat false as read-only or disabled according to client policy.
  /// Example: true
  @$pb.TagNumber(5)
  $core.bool get enabled => $_getBF(4);
  @$pb.TagNumber(5)
  set enabled($core.bool v) { $_setBool(4, v); }
  @$pb.TagNumber(5)
  $core.bool hasEnabled() => $_has(4);
  @$pb.TagNumber(5)
  void clearEnabled() => clearField(5);
}

/// What: Full set of interactive controls projected for one phase.
/// Why: Clients should not infer the control surface by phase name alone.
/// How: Render the actions, selects, switches, lists, and tables directly from
/// this message.
/// Valid Example:
///   {
///     "phase": "research",
///     "more_actions": [{"key": "refresh_subjects", "label": "Refresh Subjects", "enabled": true}],
///     "selects": [],
///     "switches": [],
///     "selection_lists": [],
///     "tables": []
///   }
class SubjectControlBundleView extends $pb.GeneratedMessage {
  factory SubjectControlBundleView({
    $core.String? phase,
    $core.Iterable<SubjectActionSpec>? moreActions,
    $core.Iterable<SubjectSelectSpecView>? selects,
    $core.Iterable<SubjectSwitchSpecView>? switches,
    $core.Iterable<SubjectSelectionListSpecView>? selectionLists,
    $core.Iterable<SubjectTableSpecView>? tables,
  }) {
    final $result = create();
    if (phase != null) {
      $result.phase = phase;
    }
    if (moreActions != null) {
      $result.moreActions.addAll(moreActions);
    }
    if (selects != null) {
      $result.selects.addAll(selects);
    }
    if (switches != null) {
      $result.switches.addAll(switches);
    }
    if (selectionLists != null) {
      $result.selectionLists.addAll(selectionLists);
    }
    if (tables != null) {
      $result.tables.addAll(tables);
    }
    return $result;
  }
  SubjectControlBundleView._() : super();
  factory SubjectControlBundleView.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory SubjectControlBundleView.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'SubjectControlBundleView', package: const $pb.PackageName(_omitMessageNames ? '' : 'realized.workstation.subjectworkflow.v1'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'phase')
    ..pc<SubjectActionSpec>(2, _omitFieldNames ? '' : 'moreActions', $pb.PbFieldType.PM, subBuilder: SubjectActionSpec.create)
    ..pc<SubjectSelectSpecView>(3, _omitFieldNames ? '' : 'selects', $pb.PbFieldType.PM, subBuilder: SubjectSelectSpecView.create)
    ..pc<SubjectSwitchSpecView>(4, _omitFieldNames ? '' : 'switches', $pb.PbFieldType.PM, subBuilder: SubjectSwitchSpecView.create)
    ..pc<SubjectSelectionListSpecView>(5, _omitFieldNames ? '' : 'selectionLists', $pb.PbFieldType.PM, subBuilder: SubjectSelectionListSpecView.create)
    ..pc<SubjectTableSpecView>(6, _omitFieldNames ? '' : 'tables', $pb.PbFieldType.PM, subBuilder: SubjectTableSpecView.create)
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  SubjectControlBundleView clone() => SubjectControlBundleView()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  SubjectControlBundleView copyWith(void Function(SubjectControlBundleView) updates) => super.copyWith((message) => updates(message as SubjectControlBundleView)) as SubjectControlBundleView;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static SubjectControlBundleView create() => SubjectControlBundleView._();
  SubjectControlBundleView createEmptyInstance() => create();
  static $pb.PbList<SubjectControlBundleView> createRepeated() => $pb.PbList<SubjectControlBundleView>();
  @$core.pragma('dart2js:noInline')
  static SubjectControlBundleView getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<SubjectControlBundleView>(create);
  static SubjectControlBundleView? _defaultInstance;

  /// What: Phase that this control bundle belongs to.
  /// Why: Clients often cache multiple bundles and need a stable discriminator.
  /// How: Associate it with the active tab/phase.
  /// Example: "research"
  @$pb.TagNumber(1)
  $core.String get phase => $_getSZ(0);
  @$pb.TagNumber(1)
  set phase($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasPhase() => $_has(0);
  @$pb.TagNumber(1)
  void clearPhase() => clearField(1);

  /// What: Secondary action controls for the phase.
  /// Why: More-actions areas need explicit service-owned action metadata.
  /// How: Render them in the phase action surface.
  /// Example: [{"key":"refresh_subjects","label":"Refresh Subjects","enabled":true}]
  @$pb.TagNumber(2)
  $core.List<SubjectActionSpec> get moreActions => $_getList(1);

  /// What: Select controls for the phase.
  /// Why: Workflow semantics determine select controls and options.
  /// How: Render one select per entry.
  /// Example: []
  @$pb.TagNumber(3)
  $core.List<SubjectSelectSpecView> get selects => $_getList(2);

  /// What: Switch controls for the phase.
  /// Why: Boolean workflow controls must come from the service.
  /// How: Render one toggle per entry.
  /// Example: []
  @$pb.TagNumber(4)
  $core.List<SubjectSwitchSpecView> get switches => $_getList(3);

  /// What: Selection-list controls for the phase.
  /// Why: Some workflow state is best represented as explicit lists.
  /// How: Render one section per entry.
  /// Example: []
  @$pb.TagNumber(5)
  $core.List<SubjectSelectionListSpecView> get selectionLists => $_getList(4);

  /// What: Structured tables for the phase.
  /// Why: Tables surface dense structured information more clearly than prose.
  /// How: Render one table per entry.
  /// Example: []
  @$pb.TagNumber(6)
  $core.List<SubjectTableSpecView> get tables => $_getList(5);
}

/// What: Current-step guidance for the active phase.
/// Why: The service owns the recommended next action and the reasoning behind
/// it.
/// How: Render the title/status/why text and the gate actions exactly as
/// returned.
/// Valid Example:
///   {
///     "title": "Current Step",
///     "status": "Markdown intake is running.",
///     "why": "Wait for the import to finish so the subject state can update.",
///     "detail_lines": ["- source markdown: City bus prose v2.md"],
///     "actions": []
///   }
class SubjectCurrentStepView extends $pb.GeneratedMessage {
  factory SubjectCurrentStepView({
    $core.String? title,
    $core.String? status,
    $core.String? why,
    $core.Iterable<$core.String>? detailLines,
    $core.Iterable<SubjectGateAction>? actions,
  }) {
    final $result = create();
    if (title != null) {
      $result.title = title;
    }
    if (status != null) {
      $result.status = status;
    }
    if (why != null) {
      $result.why = why;
    }
    if (detailLines != null) {
      $result.detailLines.addAll(detailLines);
    }
    if (actions != null) {
      $result.actions.addAll(actions);
    }
    return $result;
  }
  SubjectCurrentStepView._() : super();
  factory SubjectCurrentStepView.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory SubjectCurrentStepView.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'SubjectCurrentStepView', package: const $pb.PackageName(_omitMessageNames ? '' : 'realized.workstation.subjectworkflow.v1'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'title')
    ..aOS(2, _omitFieldNames ? '' : 'status')
    ..aOS(3, _omitFieldNames ? '' : 'why')
    ..pPS(4, _omitFieldNames ? '' : 'detailLines')
    ..pc<SubjectGateAction>(5, _omitFieldNames ? '' : 'actions', $pb.PbFieldType.PM, subBuilder: SubjectGateAction.create)
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  SubjectCurrentStepView clone() => SubjectCurrentStepView()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  SubjectCurrentStepView copyWith(void Function(SubjectCurrentStepView) updates) => super.copyWith((message) => updates(message as SubjectCurrentStepView)) as SubjectCurrentStepView;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static SubjectCurrentStepView create() => SubjectCurrentStepView._();
  SubjectCurrentStepView createEmptyInstance() => create();
  static $pb.PbList<SubjectCurrentStepView> createRepeated() => $pb.PbList<SubjectCurrentStepView>();
  @$core.pragma('dart2js:noInline')
  static SubjectCurrentStepView getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<SubjectCurrentStepView>(create);
  static SubjectCurrentStepView? _defaultInstance;

  /// What: Section title for the current-step panel.
  /// Why: Some clients render current-step content as a titled card.
  /// How: Show it as the panel heading.
  /// Example: "Current Step"
  @$pb.TagNumber(1)
  $core.String get title => $_getSZ(0);
  @$pb.TagNumber(1)
  set title($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasTitle() => $_has(0);
  @$pb.TagNumber(1)
  void clearTitle() => clearField(1);

  /// What: Primary current-step status text.
  /// Why: Users need the current workflow state in one sentence.
  /// How: Render it as the main status line.
  /// Example: "Markdown intake is running."
  @$pb.TagNumber(2)
  $core.String get status => $_getSZ(1);
  @$pb.TagNumber(2)
  set status($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasStatus() => $_has(1);
  @$pb.TagNumber(2)
  void clearStatus() => clearField(2);

  /// What: Reason the current step matters now.
  /// Why: Guidance is more actionable when the user understands why.
  /// How: Render it beneath the status text.
  /// Example: "Wait for the import to finish so the subject state can update."
  @$pb.TagNumber(3)
  $core.String get why => $_getSZ(2);
  @$pb.TagNumber(3)
  set why($core.String v) { $_setString(2, v); }
  @$pb.TagNumber(3)
  $core.bool hasWhy() => $_has(2);
  @$pb.TagNumber(3)
  void clearWhy() => clearField(3);

  /// What: Additional detail lines for the current step.
  /// Why: Some steps need supporting detail without changing the main status.
  /// How: Render each string as one already-composed line.
  /// Example: ["- source markdown: City bus prose v2.md"]
  @$pb.TagNumber(4)
  $core.List<$core.String> get detailLines => $_getList(3);

  /// What: Gate actions directly associated with the current step.
  /// Why: The recommended next action should travel with the current-step text.
  /// How: Render these as the primary controls in the section.
  /// Example: []
  @$pb.TagNumber(5)
  $core.List<SubjectGateAction> get actions => $_getList(4);
}

/// What: Simple titled text block used in subject projections.
/// Why: Several panes and workspace sections are semantically narrative text.
/// How: Render `title` and each string in `lines` as provided.
/// Valid Example:
///   {"title": "Workspace", "lines": ["Root: /srv/workstations/transit"]}
class TextSection extends $pb.GeneratedMessage {
  factory TextSection({
    $core.String? title,
    $core.Iterable<$core.String>? lines,
  }) {
    final $result = create();
    if (title != null) {
      $result.title = title;
    }
    if (lines != null) {
      $result.lines.addAll(lines);
    }
    return $result;
  }
  TextSection._() : super();
  factory TextSection.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory TextSection.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'TextSection', package: const $pb.PackageName(_omitMessageNames ? '' : 'realized.workstation.subjectworkflow.v1'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'title')
    ..pPS(2, _omitFieldNames ? '' : 'lines')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  TextSection clone() => TextSection()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  TextSection copyWith(void Function(TextSection) updates) => super.copyWith((message) => updates(message as TextSection)) as TextSection;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static TextSection create() => TextSection._();
  TextSection createEmptyInstance() => create();
  static $pb.PbList<TextSection> createRepeated() => $pb.PbList<TextSection>();
  @$core.pragma('dart2js:noInline')
  static TextSection getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<TextSection>(create);
  static TextSection? _defaultInstance;

  /// What: Section title.
  /// Why: Narrative blocks still need a heading.
  /// How: Render it as the section title.
  /// Example: "Workspace"
  @$pb.TagNumber(1)
  $core.String get title => $_getSZ(0);
  @$pb.TagNumber(1)
  set title($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasTitle() => $_has(0);
  @$pb.TagNumber(1)
  void clearTitle() => clearField(1);

  /// What: Ordered already-composed text lines.
  /// Why: The service controls the exact textual projection.
  /// How: Render each string as one line or paragraph according to client
  /// styling.
  /// Example: ["Root: /srv/workstations/transit"]
  @$pb.TagNumber(2)
  $core.List<$core.String> get lines => $_getList(1);
}

/// What: Structured status block for the active phase.
/// Why: The workflow exposes key/value operational status alongside narrative
/// guidance.
/// How: Render the title and rows in a structured card or table.
/// Valid Example:
///   {"title": "Subject Status", "rows": [{"label": "Phase", "value": "Gather"}]}
class SubjectStatusView extends $pb.GeneratedMessage {
  factory SubjectStatusView({
    $core.String? title,
    $core.Iterable<KeyValueRow>? rows,
  }) {
    final $result = create();
    if (title != null) {
      $result.title = title;
    }
    if (rows != null) {
      $result.rows.addAll(rows);
    }
    return $result;
  }
  SubjectStatusView._() : super();
  factory SubjectStatusView.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory SubjectStatusView.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'SubjectStatusView', package: const $pb.PackageName(_omitMessageNames ? '' : 'realized.workstation.subjectworkflow.v1'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'title')
    ..pc<KeyValueRow>(2, _omitFieldNames ? '' : 'rows', $pb.PbFieldType.PM, subBuilder: KeyValueRow.create)
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  SubjectStatusView clone() => SubjectStatusView()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  SubjectStatusView copyWith(void Function(SubjectStatusView) updates) => super.copyWith((message) => updates(message as SubjectStatusView)) as SubjectStatusView;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static SubjectStatusView create() => SubjectStatusView._();
  SubjectStatusView createEmptyInstance() => create();
  static $pb.PbList<SubjectStatusView> createRepeated() => $pb.PbList<SubjectStatusView>();
  @$core.pragma('dart2js:noInline')
  static SubjectStatusView getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<SubjectStatusView>(create);
  static SubjectStatusView? _defaultInstance;

  /// What: Title for the status block.
  /// Why: Users need to know what the structured rows describe.
  /// How: Render it as the panel title.
  /// Example: "Subject Status"
  @$pb.TagNumber(1)
  $core.String get title => $_getSZ(0);
  @$pb.TagNumber(1)
  set title($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasTitle() => $_has(0);
  @$pb.TagNumber(1)
  void clearTitle() => clearField(1);

  /// What: Ordered structured rows.
  /// Why: Phase status is naturally represented as labeled values.
  /// How: Render each row as a key/value pair.
  /// Example: [{"label": "Phase", "value": "Gather"}]
  @$pb.TagNumber(2)
  $core.List<KeyValueRow> get rows => $_getList(1);
}

/// What: Full phase projection for one subject and one phase.
/// Why: This is the central semantic snapshot for the active workflow phase.
/// How: Render it as the phase body and treat it as authoritative for current
/// status and next-step guidance.
/// Valid Example:
///   {
///     "phase": "research",
///     "phase_title": "Gather",
///     "preferred_phase": "research",
///     "scenario": {"key": "smart_city_travel"},
///     "current_step": {"title": "Current Step"},
///     "status_view": {"title": "Subject Status"},
///     "journey_lines": ["1. Gather"],
///     "workspace_view": {"title": "Workspace", "lines": ["Root: /srv/workstations/transit"]},
///     "latest_receipt_title": "Latest Receipt",
///     "latest_receipt_lines": ["No recent receipts."]
///   }
class SubjectPhaseView extends $pb.GeneratedMessage {
  factory SubjectPhaseView({
    $core.String? phase,
    $core.String? phaseTitle,
    $core.String? preferredPhase,
    SubjectScenarioSummary? scenario,
    SubjectCurrentStepView? currentStep,
    SubjectStatusView? statusView,
    $core.Iterable<$core.String>? journeyLines,
    TextSection? workspaceView,
    $core.String? latestReceiptTitle,
    $core.Iterable<$core.String>? latestReceiptLines,
  }) {
    final $result = create();
    if (phase != null) {
      $result.phase = phase;
    }
    if (phaseTitle != null) {
      $result.phaseTitle = phaseTitle;
    }
    if (preferredPhase != null) {
      $result.preferredPhase = preferredPhase;
    }
    if (scenario != null) {
      $result.scenario = scenario;
    }
    if (currentStep != null) {
      $result.currentStep = currentStep;
    }
    if (statusView != null) {
      $result.statusView = statusView;
    }
    if (journeyLines != null) {
      $result.journeyLines.addAll(journeyLines);
    }
    if (workspaceView != null) {
      $result.workspaceView = workspaceView;
    }
    if (latestReceiptTitle != null) {
      $result.latestReceiptTitle = latestReceiptTitle;
    }
    if (latestReceiptLines != null) {
      $result.latestReceiptLines.addAll(latestReceiptLines);
    }
    return $result;
  }
  SubjectPhaseView._() : super();
  factory SubjectPhaseView.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory SubjectPhaseView.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'SubjectPhaseView', package: const $pb.PackageName(_omitMessageNames ? '' : 'realized.workstation.subjectworkflow.v1'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'phase')
    ..aOS(2, _omitFieldNames ? '' : 'phaseTitle')
    ..aOS(3, _omitFieldNames ? '' : 'preferredPhase')
    ..aOM<SubjectScenarioSummary>(4, _omitFieldNames ? '' : 'scenario', subBuilder: SubjectScenarioSummary.create)
    ..aOM<SubjectCurrentStepView>(5, _omitFieldNames ? '' : 'currentStep', subBuilder: SubjectCurrentStepView.create)
    ..aOM<SubjectStatusView>(6, _omitFieldNames ? '' : 'statusView', subBuilder: SubjectStatusView.create)
    ..pPS(7, _omitFieldNames ? '' : 'journeyLines')
    ..aOM<TextSection>(8, _omitFieldNames ? '' : 'workspaceView', subBuilder: TextSection.create)
    ..aOS(9, _omitFieldNames ? '' : 'latestReceiptTitle')
    ..pPS(10, _omitFieldNames ? '' : 'latestReceiptLines')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  SubjectPhaseView clone() => SubjectPhaseView()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  SubjectPhaseView copyWith(void Function(SubjectPhaseView) updates) => super.copyWith((message) => updates(message as SubjectPhaseView)) as SubjectPhaseView;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static SubjectPhaseView create() => SubjectPhaseView._();
  SubjectPhaseView createEmptyInstance() => create();
  static $pb.PbList<SubjectPhaseView> createRepeated() => $pb.PbList<SubjectPhaseView>();
  @$core.pragma('dart2js:noInline')
  static SubjectPhaseView getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<SubjectPhaseView>(create);
  static SubjectPhaseView? _defaultInstance;

  /// What: Canonical phase key.
  /// Why: Clients often map tabs and layouts by phase key.
  /// How: Use it to identify the active workflow phase.
  /// Example: "research"
  @$pb.TagNumber(1)
  $core.String get phase => $_getSZ(0);
  @$pb.TagNumber(1)
  set phase($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasPhase() => $_has(0);
  @$pb.TagNumber(1)
  void clearPhase() => clearField(1);

  /// What: Human-readable phase title.
  /// Why: Users should see display titles rather than internal keys.
  /// How: Render it in headers or tab labels when needed.
  /// Example: "Gather"
  @$pb.TagNumber(2)
  $core.String get phaseTitle => $_getSZ(1);
  @$pb.TagNumber(2)
  set phaseTitle($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasPhaseTitle() => $_has(1);
  @$pb.TagNumber(2)
  void clearPhaseTitle() => clearField(2);

  /// What: Service-recommended phase after considering current workflow state.
  /// Why: The service owns workflow guidance and can suggest cross-phase moves.
  /// How: Treat it as advisory routing guidance, not a mandatory UI command.
  /// Example: "research"
  @$pb.TagNumber(3)
  $core.String get preferredPhase => $_getSZ(2);
  @$pb.TagNumber(3)
  set preferredPhase($core.String v) { $_setString(2, v); }
  @$pb.TagNumber(3)
  $core.bool hasPreferredPhase() => $_has(2);
  @$pb.TagNumber(3)
  void clearPreferredPhase() => clearField(3);

  /// What: High-level summary of the subject.
  /// Why: Every phase needs access to the current subject summary.
  /// How: Render or cache it as phase-level metadata.
  /// Example: {"key": "smart_city_travel"}
  @$pb.TagNumber(4)
  SubjectScenarioSummary get scenario => $_getN(3);
  @$pb.TagNumber(4)
  set scenario(SubjectScenarioSummary v) { setField(4, v); }
  @$pb.TagNumber(4)
  $core.bool hasScenario() => $_has(3);
  @$pb.TagNumber(4)
  void clearScenario() => clearField(4);
  @$pb.TagNumber(4)
  SubjectScenarioSummary ensureScenario() => $_ensure(3);

  /// What: Current-step guidance block.
  /// Why: The user needs explicit next-step workflow guidance.
  /// How: Render it prominently in the phase.
  /// Example: {"title": "Current Step"}
  @$pb.TagNumber(5)
  SubjectCurrentStepView get currentStep => $_getN(4);
  @$pb.TagNumber(5)
  set currentStep(SubjectCurrentStepView v) { setField(5, v); }
  @$pb.TagNumber(5)
  $core.bool hasCurrentStep() => $_has(4);
  @$pb.TagNumber(5)
  void clearCurrentStep() => clearField(5);
  @$pb.TagNumber(5)
  SubjectCurrentStepView ensureCurrentStep() => $_ensure(4);

  /// What: Structured phase status block.
  /// Why: Narrative guidance alone is insufficient for workflow inspection.
  /// How: Render it as a structured card or table.
  /// Example: {"title": "Subject Status"}
  @$pb.TagNumber(6)
  SubjectStatusView get statusView => $_getN(5);
  @$pb.TagNumber(6)
  set statusView(SubjectStatusView v) { setField(6, v); }
  @$pb.TagNumber(6)
  $core.bool hasStatusView() => $_has(5);
  @$pb.TagNumber(6)
  void clearStatusView() => clearField(6);
  @$pb.TagNumber(6)
  SubjectStatusView ensureStatusView() => $_ensure(5);

  /// What: High-level journey/progress lines.
  /// Why: Users benefit from a concise sense of where the phase sits in the
  /// overall flow.
  /// How: Render each string as one line of progress text.
  /// Example: ["1. Gather"]
  @$pb.TagNumber(7)
  $core.List<$core.String> get journeyLines => $_getList(6);

  /// What: Workspace-specific narrative text.
  /// Why: Some phase context is best shown as a titled narrative block.
  /// How: Render it in a workspace/info pane.
  /// Example: {"title":"Workspace","lines":["Root: /srv/workstations/transit"]}
  @$pb.TagNumber(8)
  TextSection get workspaceView => $_getN(7);
  @$pb.TagNumber(8)
  set workspaceView(TextSection v) { setField(8, v); }
  @$pb.TagNumber(8)
  $core.bool hasWorkspaceView() => $_has(7);
  @$pb.TagNumber(8)
  void clearWorkspaceView() => clearField(8);
  @$pb.TagNumber(8)
  TextSection ensureWorkspaceView() => $_ensure(7);

  /// What: Title for the latest receipt/log block.
  /// Why: Receipts are distinct from general workspace text.
  /// How: Render it as the heading for recent receipts.
  /// Example: "Latest Receipt"
  @$pb.TagNumber(9)
  $core.String get latestReceiptTitle => $_getSZ(8);
  @$pb.TagNumber(9)
  set latestReceiptTitle($core.String v) { $_setString(8, v); }
  @$pb.TagNumber(9)
  $core.bool hasLatestReceiptTitle() => $_has(8);
  @$pb.TagNumber(9)
  void clearLatestReceiptTitle() => clearField(9);

  /// What: Latest receipt lines for the phase.
  /// Why: Users need the most recent workflow receipt without leaving the phase.
  /// How: Render each string as one line.
  /// Example: ["No recent receipts."]
  @$pb.TagNumber(10)
  $core.List<$core.String> get latestReceiptLines => $_getList(9);
}

/// What: Pending import metadata supplied when applying an import-related
/// action.
/// Why: Gather import approval often needs more detail than just an action key.
/// How: Supply it only for import actions that require a selected staging item.
/// Valid Example:
///   {
///     "source_subject_id": "smart_city_travel",
///     "source_subject_title": "Smart City Travel",
///     "source_subject_version_id": "subject-version-1",
///     "import_kind": "definition_support",
///     "selection_profile": "units_only"
///   }
class SubjectImportStaging extends $pb.GeneratedMessage {
  factory SubjectImportStaging({
    $core.String? sourceSubjectId,
    $core.String? sourceSubjectTitle,
    $core.String? sourceSubjectVersionId,
    $core.String? importKind,
    $core.String? selectionProfile,
  }) {
    final $result = create();
    if (sourceSubjectId != null) {
      $result.sourceSubjectId = sourceSubjectId;
    }
    if (sourceSubjectTitle != null) {
      $result.sourceSubjectTitle = sourceSubjectTitle;
    }
    if (sourceSubjectVersionId != null) {
      $result.sourceSubjectVersionId = sourceSubjectVersionId;
    }
    if (importKind != null) {
      $result.importKind = importKind;
    }
    if (selectionProfile != null) {
      $result.selectionProfile = selectionProfile;
    }
    return $result;
  }
  SubjectImportStaging._() : super();
  factory SubjectImportStaging.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory SubjectImportStaging.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'SubjectImportStaging', package: const $pb.PackageName(_omitMessageNames ? '' : 'realized.workstation.subjectworkflow.v1'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'sourceSubjectId')
    ..aOS(2, _omitFieldNames ? '' : 'sourceSubjectTitle')
    ..aOS(3, _omitFieldNames ? '' : 'sourceSubjectVersionId')
    ..aOS(4, _omitFieldNames ? '' : 'importKind')
    ..aOS(5, _omitFieldNames ? '' : 'selectionProfile')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  SubjectImportStaging clone() => SubjectImportStaging()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  SubjectImportStaging copyWith(void Function(SubjectImportStaging) updates) => super.copyWith((message) => updates(message as SubjectImportStaging)) as SubjectImportStaging;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static SubjectImportStaging create() => SubjectImportStaging._();
  SubjectImportStaging createEmptyInstance() => create();
  static $pb.PbList<SubjectImportStaging> createRepeated() => $pb.PbList<SubjectImportStaging>();
  @$core.pragma('dart2js:noInline')
  static SubjectImportStaging getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<SubjectImportStaging>(create);
  static SubjectImportStaging? _defaultInstance;

  /// What: Source subject id for the staged import.
  /// Why: The workflow must know which subject the import originated from.
  /// How: Fill it from the selected staged import entry.
  /// Example: "smart_city_travel"
  @$pb.TagNumber(1)
  $core.String get sourceSubjectId => $_getSZ(0);
  @$pb.TagNumber(1)
  set sourceSubjectId($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasSourceSubjectId() => $_has(0);
  @$pb.TagNumber(1)
  void clearSourceSubjectId() => clearField(1);

  /// What: Human-readable source subject title.
  /// Why: Receipts and diagnostics often include the source subject title.
  /// How: Pass the title of the selected staged import.
  /// Example: "Smart City Travel"
  @$pb.TagNumber(2)
  $core.String get sourceSubjectTitle => $_getSZ(1);
  @$pb.TagNumber(2)
  set sourceSubjectTitle($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasSourceSubjectTitle() => $_has(1);
  @$pb.TagNumber(2)
  void clearSourceSubjectTitle() => clearField(2);

  /// What: Source subject version id.
  /// Why: Imports can be version-sensitive.
  /// How: Pass the selected source version id when known.
  /// Example: "subject-version-1"
  @$pb.TagNumber(3)
  $core.String get sourceSubjectVersionId => $_getSZ(2);
  @$pb.TagNumber(3)
  set sourceSubjectVersionId($core.String v) { $_setString(2, v); }
  @$pb.TagNumber(3)
  $core.bool hasSourceSubjectVersionId() => $_has(2);
  @$pb.TagNumber(3)
  void clearSourceSubjectVersionId() => clearField(3);

  /// What: Import semantic kind.
  /// Why: The workflow distinguishes different kinds of imported support.
  /// How: Use the service-defined symbolic value.
  /// Example: "definition_support"
  @$pb.TagNumber(4)
  $core.String get importKind => $_getSZ(3);
  @$pb.TagNumber(4)
  set importKind($core.String v) { $_setString(3, v); }
  @$pb.TagNumber(4)
  $core.bool hasImportKind() => $_has(3);
  @$pb.TagNumber(4)
  void clearImportKind() => clearField(4);

  /// What: Selection profile that shapes the imported material.
  /// Why: Import approval can select units-only versus broader import shapes.
  /// How: Use the symbolic profile the service expects.
  /// Example: "units_only"
  @$pb.TagNumber(5)
  $core.String get selectionProfile => $_getSZ(4);
  @$pb.TagNumber(5)
  set selectionProfile($core.String v) { $_setString(4, v); }
  @$pb.TagNumber(5)
  $core.bool hasSelectionProfile() => $_has(4);
  @$pb.TagNumber(5)
  void clearSelectionProfile() => clearField(5);
}

/// What: UI projection context that influences but does not redefine the
/// workflow snapshot.
/// Why: Some subject projections depend on client-local state such as a chosen
/// markdown file or whether the assistant input can be captured in the current
/// phase.
/// How: Pass the current client-local context on snapshot, watch, action, and
/// interaction requests.
/// Valid Example:
///   {
///     "can_capture_assistant": true,
///     "markdown_selected_path": "/srv/workstations/transit/uploads/flutter-shell-a/city-bus.md",
///     "markdown_status_text": "Stage markdown and approve import.",
///     "markdown_busy": false
///   }
class SubjectPhaseProjectionContext extends $pb.GeneratedMessage {
  factory SubjectPhaseProjectionContext({
    $core.bool? canCaptureAssistant,
    $core.String? markdownSelectedPath,
    $core.String? markdownStatusText,
    $core.bool? markdownBusy,
  }) {
    final $result = create();
    if (canCaptureAssistant != null) {
      $result.canCaptureAssistant = canCaptureAssistant;
    }
    if (markdownSelectedPath != null) {
      $result.markdownSelectedPath = markdownSelectedPath;
    }
    if (markdownStatusText != null) {
      $result.markdownStatusText = markdownStatusText;
    }
    if (markdownBusy != null) {
      $result.markdownBusy = markdownBusy;
    }
    return $result;
  }
  SubjectPhaseProjectionContext._() : super();
  factory SubjectPhaseProjectionContext.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory SubjectPhaseProjectionContext.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'SubjectPhaseProjectionContext', package: const $pb.PackageName(_omitMessageNames ? '' : 'realized.workstation.subjectworkflow.v1'), createEmptyInstance: create)
    ..aOB(1, _omitFieldNames ? '' : 'canCaptureAssistant')
    ..aOS(2, _omitFieldNames ? '' : 'markdownSelectedPath')
    ..aOS(3, _omitFieldNames ? '' : 'markdownStatusText')
    ..aOB(4, _omitFieldNames ? '' : 'markdownBusy')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  SubjectPhaseProjectionContext clone() => SubjectPhaseProjectionContext()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  SubjectPhaseProjectionContext copyWith(void Function(SubjectPhaseProjectionContext) updates) => super.copyWith((message) => updates(message as SubjectPhaseProjectionContext)) as SubjectPhaseProjectionContext;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static SubjectPhaseProjectionContext create() => SubjectPhaseProjectionContext._();
  SubjectPhaseProjectionContext createEmptyInstance() => create();
  static $pb.PbList<SubjectPhaseProjectionContext> createRepeated() => $pb.PbList<SubjectPhaseProjectionContext>();
  @$core.pragma('dart2js:noInline')
  static SubjectPhaseProjectionContext getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<SubjectPhaseProjectionContext>(create);
  static SubjectPhaseProjectionContext? _defaultInstance;

  /// What: Whether the active client can currently capture assistant text into
  /// the phase workflow.
  /// Why: Some phase controls depend on whether assistant output can be applied.
  /// How: Set it from the UI's local capability state.
  /// Example: true
  @$pb.TagNumber(1)
  $core.bool get canCaptureAssistant => $_getBF(0);
  @$pb.TagNumber(1)
  set canCaptureAssistant($core.bool v) { $_setBool(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasCanCaptureAssistant() => $_has(0);
  @$pb.TagNumber(1)
  void clearCanCaptureAssistant() => clearField(1);

  /// What: Server-visible path for the currently selected markdown source.
  /// Why: Gather import flows need a concrete staged or same-machine path.
  /// How: For cross-platform clients, use the staged path returned by
  /// `StageMarkdownUpload`.
  /// Example: "/srv/workstations/transit/uploads/flutter-shell-a/city-bus.md"
  @$pb.TagNumber(2)
  $core.String get markdownSelectedPath => $_getSZ(1);
  @$pb.TagNumber(2)
  set markdownSelectedPath($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasMarkdownSelectedPath() => $_has(1);
  @$pb.TagNumber(2)
  void clearMarkdownSelectedPath() => clearField(2);

  /// What: Client-visible markdown status text.
  /// Why: The projection can incorporate current markdown-import guidance.
  /// How: Pass the current markdown-related status line from the UI.
  /// Example: "Stage markdown and approve import."
  @$pb.TagNumber(3)
  $core.String get markdownStatusText => $_getSZ(2);
  @$pb.TagNumber(3)
  set markdownStatusText($core.String v) { $_setString(2, v); }
  @$pb.TagNumber(3)
  $core.bool hasMarkdownStatusText() => $_has(2);
  @$pb.TagNumber(3)
  void clearMarkdownStatusText() => clearField(3);

  /// What: Whether a markdown-related operation is currently busy.
  /// Why: Phase guidance sometimes changes while import work is running.
  /// How: Set true while upload/import work is in progress.
  /// Example: false
  @$pb.TagNumber(4)
  $core.bool get markdownBusy => $_getBF(3);
  @$pb.TagNumber(4)
  set markdownBusy($core.bool v) { $_setBool(3, v); }
  @$pb.TagNumber(4)
  $core.bool hasMarkdownBusy() => $_has(3);
  @$pb.TagNumber(4)
  void clearMarkdownBusy() => clearField(4);
}

/// What: Outcome of applying one workflow action.
/// Why: Action application needs a stable contract for status text, routing
/// guidance, reload hints, and actionable artifacts.
/// How: Render the status/receipt, optionally follow `next_phase` or `next_tab`,
/// refresh subject lists when requested, and use `open_artifacts` for any
/// client-actionable outputs.
/// Valid Example:
///   {
///     "status_text": "Report build completed.",
///     "timeline_text": "Built publication output.",
///     "next_phase": "publication",
///     "next_tab": "publication",
///     "reload_subjects": true,
///     "open_paths": ["/srv/workstations/transit/build/report.pdf"],
///     "preferred_subject_key": "smart_city_travel",
///     "open_artifacts": [
///       {
///         "label": "report.pdf",
///         "server_path": "/srv/workstations/transit/build/report.pdf",
///         "mime_type": "application/pdf",
///         "download_url": "http://127.0.0.1:8787/artifacts/abc123/report.pdf",
///         "can_open_locally": true
///       }
///     ]
///   }
class SubjectActionResult extends $pb.GeneratedMessage {
  factory SubjectActionResult({
    $core.String? statusText,
    $core.String? timelineText,
    $core.String? nextPhase,
    $core.String? nextTab,
    $core.bool? reloadSubjects,
    $core.Iterable<$core.String>? openPaths,
    $core.String? preferredSubjectKey,
    $core.Iterable<$0.ArtifactRef>? openArtifacts,
  }) {
    final $result = create();
    if (statusText != null) {
      $result.statusText = statusText;
    }
    if (timelineText != null) {
      $result.timelineText = timelineText;
    }
    if (nextPhase != null) {
      $result.nextPhase = nextPhase;
    }
    if (nextTab != null) {
      $result.nextTab = nextTab;
    }
    if (reloadSubjects != null) {
      $result.reloadSubjects = reloadSubjects;
    }
    if (openPaths != null) {
      $result.openPaths.addAll(openPaths);
    }
    if (preferredSubjectKey != null) {
      $result.preferredSubjectKey = preferredSubjectKey;
    }
    if (openArtifacts != null) {
      $result.openArtifacts.addAll(openArtifacts);
    }
    return $result;
  }
  SubjectActionResult._() : super();
  factory SubjectActionResult.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory SubjectActionResult.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'SubjectActionResult', package: const $pb.PackageName(_omitMessageNames ? '' : 'realized.workstation.subjectworkflow.v1'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'statusText')
    ..aOS(2, _omitFieldNames ? '' : 'timelineText')
    ..aOS(3, _omitFieldNames ? '' : 'nextPhase')
    ..aOS(4, _omitFieldNames ? '' : 'nextTab')
    ..aOB(5, _omitFieldNames ? '' : 'reloadSubjects')
    ..pPS(6, _omitFieldNames ? '' : 'openPaths')
    ..aOS(7, _omitFieldNames ? '' : 'preferredSubjectKey')
    ..pc<$0.ArtifactRef>(8, _omitFieldNames ? '' : 'openArtifacts', $pb.PbFieldType.PM, subBuilder: $0.ArtifactRef.create)
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  SubjectActionResult clone() => SubjectActionResult()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  SubjectActionResult copyWith(void Function(SubjectActionResult) updates) => super.copyWith((message) => updates(message as SubjectActionResult)) as SubjectActionResult;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static SubjectActionResult create() => SubjectActionResult._();
  SubjectActionResult createEmptyInstance() => create();
  static $pb.PbList<SubjectActionResult> createRepeated() => $pb.PbList<SubjectActionResult>();
  @$core.pragma('dart2js:noInline')
  static SubjectActionResult getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<SubjectActionResult>(create);
  static SubjectActionResult? _defaultInstance;

  /// What: Primary human-readable status text for the completed action.
  /// Why: Users need immediate confirmation of what happened.
  /// How: Render it as a receipt/status message.
  /// Example: "Report build completed."
  @$pb.TagNumber(1)
  $core.String get statusText => $_getSZ(0);
  @$pb.TagNumber(1)
  set statusText($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasStatusText() => $_has(0);
  @$pb.TagNumber(1)
  void clearStatusText() => clearField(1);

  /// What: Timeline/receipt text for the action.
  /// Why: The workflow records a narrative receipt for history and context.
  /// How: Append or display it in the latest-receipt surface.
  /// Example: "Built publication output."
  @$pb.TagNumber(2)
  $core.String get timelineText => $_getSZ(1);
  @$pb.TagNumber(2)
  set timelineText($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasTimelineText() => $_has(1);
  @$pb.TagNumber(2)
  void clearTimelineText() => clearField(2);

  /// What: Service-directed next workflow phase, when the action semantically
  /// changes where the user should be.
  /// Why: Post-action routing should come from workflow semantics, not UI guesswork.
  /// How: Treat it as the highest-priority advisory routing field.
  /// Example: "publication"
  @$pb.TagNumber(3)
  $core.String get nextPhase => $_getSZ(2);
  @$pb.TagNumber(3)
  set nextPhase($core.String v) { $_setString(2, v); }
  @$pb.TagNumber(3)
  $core.bool hasNextPhase() => $_has(2);
  @$pb.TagNumber(3)
  void clearNextPhase() => clearField(3);

  /// What: UI tab key aligned with the next workflow surface.
  /// Why: Some clients route by tab key rather than raw phase name.
  /// How: Use it as an advisory tab selection hint.
  /// Example: "publication"
  @$pb.TagNumber(4)
  $core.String get nextTab => $_getSZ(3);
  @$pb.TagNumber(4)
  set nextTab($core.String v) { $_setString(3, v); }
  @$pb.TagNumber(4)
  $core.bool hasNextTab() => $_has(3);
  @$pb.TagNumber(4)
  void clearNextTab() => clearField(4);

  /// What: Whether subject lists should be reloaded after the action.
  /// Why: Some actions materially change list-visible subject summaries.
  /// How: Refresh the list if true.
  /// Example: true
  @$pb.TagNumber(5)
  $core.bool get reloadSubjects => $_getBF(4);
  @$pb.TagNumber(5)
  set reloadSubjects($core.bool v) { $_setBool(4, v); }
  @$pb.TagNumber(5)
  $core.bool hasReloadSubjects() => $_has(4);
  @$pb.TagNumber(5)
  void clearReloadSubjects() => clearField(5);

  /// What: Legacy same-filesystem paths opened by existing desktop clients.
  /// Why: Textual and other same-machine desktop workflows still rely on direct
  /// local opens.
  /// How: Keep supporting them for backward compatibility, but prefer
  /// `open_artifacts` for new cross-platform clients.
  /// Example: ["/srv/workstations/transit/build/report.pdf"]
  @$pb.TagNumber(6)
  $core.List<$core.String> get openPaths => $_getList(5);

  /// What: Preferred subject key after the action.
  /// Why: Some actions switch the effective subject context.
  /// How: Use it when refreshing the selected subject after an action.
  /// Example: "smart_city_travel"
  @$pb.TagNumber(7)
  $core.String get preferredSubjectKey => $_getSZ(6);
  @$pb.TagNumber(7)
  set preferredSubjectKey($core.String v) { $_setString(6, v); }
  @$pb.TagNumber(7)
  $core.bool hasPreferredSubjectKey() => $_has(6);
  @$pb.TagNumber(7)
  void clearPreferredSubjectKey() => clearField(7);

  /// What: Client-actionable artifact references opened or produced by the
  /// action.
  /// Why: Web/mobile clients cannot rely on server-local filesystem paths.
  /// How: Prefer these refs over `open_paths` when present.
  /// Example: [{"label":"report.pdf","server_path":"/srv/workstations/transit/build/report.pdf","mime_type":"application/pdf","download_url":"http://127.0.0.1:8787/artifacts/abc123/report.pdf","can_open_locally":true}]
  @$pb.TagNumber(8)
  $core.List<$0.ArtifactRef> get openArtifacts => $_getList(7);
}

/// What: Request to list subjects for one workstation root.
/// Why: Clients need to discover available subjects before selecting one.
/// How: Supply the root path chosen during bootstrap.
/// Valid Example:
///   {"root_path": "/srv/workstations/transit"}
class ListSubjectsRequest extends $pb.GeneratedMessage {
  factory ListSubjectsRequest({
    $core.String? rootPath,
  }) {
    final $result = create();
    if (rootPath != null) {
      $result.rootPath = rootPath;
    }
    return $result;
  }
  ListSubjectsRequest._() : super();
  factory ListSubjectsRequest.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory ListSubjectsRequest.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'ListSubjectsRequest', package: const $pb.PackageName(_omitMessageNames ? '' : 'realized.workstation.subjectworkflow.v1'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'rootPath')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  ListSubjectsRequest clone() => ListSubjectsRequest()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  ListSubjectsRequest copyWith(void Function(ListSubjectsRequest) updates) => super.copyWith((message) => updates(message as ListSubjectsRequest)) as ListSubjectsRequest;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static ListSubjectsRequest create() => ListSubjectsRequest._();
  ListSubjectsRequest createEmptyInstance() => create();
  static $pb.PbList<ListSubjectsRequest> createRepeated() => $pb.PbList<ListSubjectsRequest>();
  @$core.pragma('dart2js:noInline')
  static ListSubjectsRequest getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<ListSubjectsRequest>(create);
  static ListSubjectsRequest? _defaultInstance;

  /// What: Absolute workstation root path on the server.
  /// Why: Subject lists are scoped to one workstation instance.
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
}

/// What: Response containing all current subject summaries.
/// Why: Subject lists need both data and trace metadata.
/// How: Render `subjects` and optionally log the trace fields for diagnostics.
/// Valid Example:
///   {
///     "subjects": [{"key": "smart_city_travel", "subject_id": "smart_city_travel"}],
///     "trace_id": "subject-list-response_04b7d44f",
///     "parent_id": "subject-list-request_169cb3c8"
///   }
class ListSubjectsResponse extends $pb.GeneratedMessage {
  factory ListSubjectsResponse({
    $core.Iterable<SubjectScenarioSummary>? subjects,
    $core.String? traceId,
    $core.String? parentId,
  }) {
    final $result = create();
    if (subjects != null) {
      $result.subjects.addAll(subjects);
    }
    if (traceId != null) {
      $result.traceId = traceId;
    }
    if (parentId != null) {
      $result.parentId = parentId;
    }
    return $result;
  }
  ListSubjectsResponse._() : super();
  factory ListSubjectsResponse.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory ListSubjectsResponse.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'ListSubjectsResponse', package: const $pb.PackageName(_omitMessageNames ? '' : 'realized.workstation.subjectworkflow.v1'), createEmptyInstance: create)
    ..pc<SubjectScenarioSummary>(1, _omitFieldNames ? '' : 'subjects', $pb.PbFieldType.PM, subBuilder: SubjectScenarioSummary.create)
    ..aOS(100, _omitFieldNames ? '' : 'traceId')
    ..aOS(101, _omitFieldNames ? '' : 'parentId')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  ListSubjectsResponse clone() => ListSubjectsResponse()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  ListSubjectsResponse copyWith(void Function(ListSubjectsResponse) updates) => super.copyWith((message) => updates(message as ListSubjectsResponse)) as ListSubjectsResponse;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static ListSubjectsResponse create() => ListSubjectsResponse._();
  ListSubjectsResponse createEmptyInstance() => create();
  static $pb.PbList<ListSubjectsResponse> createRepeated() => $pb.PbList<ListSubjectsResponse>();
  @$core.pragma('dart2js:noInline')
  static ListSubjectsResponse getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<ListSubjectsResponse>(create);
  static ListSubjectsResponse? _defaultInstance;

  /// What: Ordered subject summaries.
  /// Why: Clients use them to render the subject picker.
  /// How: Replace or refresh the local subject list from this sequence.
  /// Example: [{"key":"smart_city_travel","subject_id":"smart_city_travel"}]
  @$pb.TagNumber(1)
  $core.List<SubjectScenarioSummary> get subjects => $_getList(0);

  /// What: Trace id for this response.
  /// Why: List operations participate in host-level traceability.
  /// How: Log or correlate it when debugging.
  /// Example: "subject-list-response_04b7d44f"
  @$pb.TagNumber(100)
  $core.String get traceId => $_getSZ(1);
  @$pb.TagNumber(100)
  set traceId($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(100)
  $core.bool hasTraceId() => $_has(1);
  @$pb.TagNumber(100)
  void clearTraceId() => clearField(100);

  /// What: Parent trace id linking back to the triggering request.
  /// Why: Diagnostics need causal request/response linkage.
  /// How: Treat it as opaque correlation metadata.
  /// Example: "subject-list-request_169cb3c8"
  @$pb.TagNumber(101)
  $core.String get parentId => $_getSZ(2);
  @$pb.TagNumber(101)
  set parentId($core.String v) { $_setString(2, v); }
  @$pb.TagNumber(101)
  $core.bool hasParentId() => $_has(2);
  @$pb.TagNumber(101)
  void clearParentId() => clearField(101);
}

/// What: Request for one phase projection.
/// Why: Clients sometimes need just the phase body without controls or panes.
/// How: Supply root, subject, phase, client session, and current projection
/// context.
/// Valid Example:
///   {
///     "root_path": "/srv/workstations/transit",
///     "subject_id": "smart_city_travel",
///     "phase": "research",
///     "projection_context": {"can_capture_assistant": true},
///     "client_session_id": "flutter-shell-a"
///   }
class GetSubjectPhaseViewRequest extends $pb.GeneratedMessage {
  factory GetSubjectPhaseViewRequest({
    $core.String? rootPath,
    $core.String? subjectId,
    $core.String? phase,
    SubjectPhaseProjectionContext? projectionContext,
    $core.String? clientSessionId,
  }) {
    final $result = create();
    if (rootPath != null) {
      $result.rootPath = rootPath;
    }
    if (subjectId != null) {
      $result.subjectId = subjectId;
    }
    if (phase != null) {
      $result.phase = phase;
    }
    if (projectionContext != null) {
      $result.projectionContext = projectionContext;
    }
    if (clientSessionId != null) {
      $result.clientSessionId = clientSessionId;
    }
    return $result;
  }
  GetSubjectPhaseViewRequest._() : super();
  factory GetSubjectPhaseViewRequest.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory GetSubjectPhaseViewRequest.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'GetSubjectPhaseViewRequest', package: const $pb.PackageName(_omitMessageNames ? '' : 'realized.workstation.subjectworkflow.v1'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'rootPath')
    ..aOS(2, _omitFieldNames ? '' : 'subjectId')
    ..aOS(3, _omitFieldNames ? '' : 'phase')
    ..aOM<SubjectPhaseProjectionContext>(4, _omitFieldNames ? '' : 'projectionContext', subBuilder: SubjectPhaseProjectionContext.create)
    ..aOS(5, _omitFieldNames ? '' : 'clientSessionId')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  GetSubjectPhaseViewRequest clone() => GetSubjectPhaseViewRequest()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  GetSubjectPhaseViewRequest copyWith(void Function(GetSubjectPhaseViewRequest) updates) => super.copyWith((message) => updates(message as GetSubjectPhaseViewRequest)) as GetSubjectPhaseViewRequest;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static GetSubjectPhaseViewRequest create() => GetSubjectPhaseViewRequest._();
  GetSubjectPhaseViewRequest createEmptyInstance() => create();
  static $pb.PbList<GetSubjectPhaseViewRequest> createRepeated() => $pb.PbList<GetSubjectPhaseViewRequest>();
  @$core.pragma('dart2js:noInline')
  static GetSubjectPhaseViewRequest getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<GetSubjectPhaseViewRequest>(create);
  static GetSubjectPhaseViewRequest? _defaultInstance;

  /// What: Absolute workstation root path on the server.
  /// Why: Phase projections are scoped to one workstation.
  /// How: Reuse the bootstrapped root.
  /// Example: "/srv/workstations/transit"
  @$pb.TagNumber(1)
  $core.String get rootPath => $_getSZ(0);
  @$pb.TagNumber(1)
  set rootPath($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasRootPath() => $_has(0);
  @$pb.TagNumber(1)
  void clearRootPath() => clearField(1);

  /// What: Target subject id.
  /// Why: The server needs to know which subject to project.
  /// How: Use the selected subject id from `ListSubjects`.
  /// Example: "smart_city_travel"
  @$pb.TagNumber(2)
  $core.String get subjectId => $_getSZ(1);
  @$pb.TagNumber(2)
  set subjectId($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasSubjectId() => $_has(1);
  @$pb.TagNumber(2)
  void clearSubjectId() => clearField(2);

  /// What: Requested workflow phase key.
  /// Why: The server can project different semantic views per phase.
  /// How: Pass one of `research`, `itemize`, `draft`, `review`, or
  /// `publication`.
  /// Example: "research"
  @$pb.TagNumber(3)
  $core.String get phase => $_getSZ(2);
  @$pb.TagNumber(3)
  set phase($core.String v) { $_setString(2, v); }
  @$pb.TagNumber(3)
  $core.bool hasPhase() => $_has(2);
  @$pb.TagNumber(3)
  void clearPhase() => clearField(3);

  /// What: Current UI projection context.
  /// Why: The phase projection may depend on client-local markdown/assistant
  /// state.
  /// How: Fill it from current client-local workflow context.
  /// Example: {"can_capture_assistant": true}
  @$pb.TagNumber(4)
  SubjectPhaseProjectionContext get projectionContext => $_getN(3);
  @$pb.TagNumber(4)
  set projectionContext(SubjectPhaseProjectionContext v) { setField(4, v); }
  @$pb.TagNumber(4)
  $core.bool hasProjectionContext() => $_has(3);
  @$pb.TagNumber(4)
  void clearProjectionContext() => clearField(4);
  @$pb.TagNumber(4)
  SubjectPhaseProjectionContext ensureProjectionContext() => $_ensure(3);

  /// What: Stable client session id.
  /// Why: Subject projections can depend on client-specific progress/view state.
  /// How: Reuse the id from `OpenClientSession`.
  /// Example: "flutter-shell-a"
  @$pb.TagNumber(5)
  $core.String get clientSessionId => $_getSZ(4);
  @$pb.TagNumber(5)
  set clientSessionId($core.String v) { $_setString(4, v); }
  @$pb.TagNumber(5)
  $core.bool hasClientSessionId() => $_has(4);
  @$pb.TagNumber(5)
  void clearClientSessionId() => clearField(5);
}

/// What: Response containing one phase projection.
/// Why: The client needs the phase body plus trace metadata.
/// How: Render `view` as the current phase panel.
/// Valid Example:
///   {
///     "view": {"phase": "research", "phase_title": "Gather"},
///     "trace_id": "subject-phase-response_0a2d7091",
///     "parent_id": "subject-phase-request_9d19641d"
///   }
class GetSubjectPhaseViewResponse extends $pb.GeneratedMessage {
  factory GetSubjectPhaseViewResponse({
    SubjectPhaseView? view,
    $core.String? traceId,
    $core.String? parentId,
  }) {
    final $result = create();
    if (view != null) {
      $result.view = view;
    }
    if (traceId != null) {
      $result.traceId = traceId;
    }
    if (parentId != null) {
      $result.parentId = parentId;
    }
    return $result;
  }
  GetSubjectPhaseViewResponse._() : super();
  factory GetSubjectPhaseViewResponse.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory GetSubjectPhaseViewResponse.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'GetSubjectPhaseViewResponse', package: const $pb.PackageName(_omitMessageNames ? '' : 'realized.workstation.subjectworkflow.v1'), createEmptyInstance: create)
    ..aOM<SubjectPhaseView>(1, _omitFieldNames ? '' : 'view', subBuilder: SubjectPhaseView.create)
    ..aOS(100, _omitFieldNames ? '' : 'traceId')
    ..aOS(101, _omitFieldNames ? '' : 'parentId')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  GetSubjectPhaseViewResponse clone() => GetSubjectPhaseViewResponse()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  GetSubjectPhaseViewResponse copyWith(void Function(GetSubjectPhaseViewResponse) updates) => super.copyWith((message) => updates(message as GetSubjectPhaseViewResponse)) as GetSubjectPhaseViewResponse;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static GetSubjectPhaseViewResponse create() => GetSubjectPhaseViewResponse._();
  GetSubjectPhaseViewResponse createEmptyInstance() => create();
  static $pb.PbList<GetSubjectPhaseViewResponse> createRepeated() => $pb.PbList<GetSubjectPhaseViewResponse>();
  @$core.pragma('dart2js:noInline')
  static GetSubjectPhaseViewResponse getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<GetSubjectPhaseViewResponse>(create);
  static GetSubjectPhaseViewResponse? _defaultInstance;

  /// What: Projected phase body.
  /// Why: This is the main data the client requested.
  /// How: Render it as the current phase surface.
  /// Example: {"phase":"research","phase_title":"Gather"}
  @$pb.TagNumber(1)
  SubjectPhaseView get view => $_getN(0);
  @$pb.TagNumber(1)
  set view(SubjectPhaseView v) { setField(1, v); }
  @$pb.TagNumber(1)
  $core.bool hasView() => $_has(0);
  @$pb.TagNumber(1)
  void clearView() => clearField(1);
  @$pb.TagNumber(1)
  SubjectPhaseView ensureView() => $_ensure(0);

  /// What: Trace id for the response.
  /// Why: Phase reads participate in traceable host operations.
  /// How: Log it when debugging.
  /// Example: "subject-phase-response_0a2d7091"
  @$pb.TagNumber(100)
  $core.String get traceId => $_getSZ(1);
  @$pb.TagNumber(100)
  set traceId($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(100)
  $core.bool hasTraceId() => $_has(1);
  @$pb.TagNumber(100)
  void clearTraceId() => clearField(100);

  /// What: Parent trace id linking back to the request.
  /// Why: Diagnostics need causal linkage.
  /// How: Treat it as opaque metadata.
  /// Example: "subject-phase-request_9d19641d"
  @$pb.TagNumber(101)
  $core.String get parentId => $_getSZ(2);
  @$pb.TagNumber(101)
  set parentId($core.String v) { $_setString(2, v); }
  @$pb.TagNumber(101)
  $core.bool hasParentId() => $_has(2);
  @$pb.TagNumber(101)
  void clearParentId() => clearField(101);
}

/// What: Request for the control bundle of one phase.
/// Why: Some clients fetch controls independently from the phase body.
/// How: Use the same targeting fields as `GetSubjectPhaseView`.
/// Valid Example:
///   {
///     "root_path": "/srv/workstations/transit",
///     "subject_id": "smart_city_travel",
///     "phase": "research",
///     "projection_context": {"can_capture_assistant": true},
///     "client_session_id": "flutter-shell-a"
///   }
class GetSubjectControlBundleRequest extends $pb.GeneratedMessage {
  factory GetSubjectControlBundleRequest({
    $core.String? rootPath,
    $core.String? subjectId,
    $core.String? phase,
    SubjectPhaseProjectionContext? projectionContext,
    $core.String? clientSessionId,
  }) {
    final $result = create();
    if (rootPath != null) {
      $result.rootPath = rootPath;
    }
    if (subjectId != null) {
      $result.subjectId = subjectId;
    }
    if (phase != null) {
      $result.phase = phase;
    }
    if (projectionContext != null) {
      $result.projectionContext = projectionContext;
    }
    if (clientSessionId != null) {
      $result.clientSessionId = clientSessionId;
    }
    return $result;
  }
  GetSubjectControlBundleRequest._() : super();
  factory GetSubjectControlBundleRequest.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory GetSubjectControlBundleRequest.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'GetSubjectControlBundleRequest', package: const $pb.PackageName(_omitMessageNames ? '' : 'realized.workstation.subjectworkflow.v1'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'rootPath')
    ..aOS(2, _omitFieldNames ? '' : 'subjectId')
    ..aOS(3, _omitFieldNames ? '' : 'phase')
    ..aOM<SubjectPhaseProjectionContext>(4, _omitFieldNames ? '' : 'projectionContext', subBuilder: SubjectPhaseProjectionContext.create)
    ..aOS(5, _omitFieldNames ? '' : 'clientSessionId')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  GetSubjectControlBundleRequest clone() => GetSubjectControlBundleRequest()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  GetSubjectControlBundleRequest copyWith(void Function(GetSubjectControlBundleRequest) updates) => super.copyWith((message) => updates(message as GetSubjectControlBundleRequest)) as GetSubjectControlBundleRequest;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static GetSubjectControlBundleRequest create() => GetSubjectControlBundleRequest._();
  GetSubjectControlBundleRequest createEmptyInstance() => create();
  static $pb.PbList<GetSubjectControlBundleRequest> createRepeated() => $pb.PbList<GetSubjectControlBundleRequest>();
  @$core.pragma('dart2js:noInline')
  static GetSubjectControlBundleRequest getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<GetSubjectControlBundleRequest>(create);
  static GetSubjectControlBundleRequest? _defaultInstance;

  /// What: Absolute workstation root path on the server.
  /// Why: Control bundles are scoped to one workstation.
  /// How: Reuse the bootstrapped root.
  /// Example: "/srv/workstations/transit"
  @$pb.TagNumber(1)
  $core.String get rootPath => $_getSZ(0);
  @$pb.TagNumber(1)
  set rootPath($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasRootPath() => $_has(0);
  @$pb.TagNumber(1)
  void clearRootPath() => clearField(1);

  /// What: Target subject id.
  /// Why: Controls are subject-specific.
  /// How: Use the selected subject id.
  /// Example: "smart_city_travel"
  @$pb.TagNumber(2)
  $core.String get subjectId => $_getSZ(1);
  @$pb.TagNumber(2)
  set subjectId($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasSubjectId() => $_has(1);
  @$pb.TagNumber(2)
  void clearSubjectId() => clearField(2);

  /// What: Requested phase key.
  /// Why: Control bundles vary by phase.
  /// How: Pass the phase currently being rendered.
  /// Example: "research"
  @$pb.TagNumber(3)
  $core.String get phase => $_getSZ(2);
  @$pb.TagNumber(3)
  set phase($core.String v) { $_setString(2, v); }
  @$pb.TagNumber(3)
  $core.bool hasPhase() => $_has(2);
  @$pb.TagNumber(3)
  void clearPhase() => clearField(3);

  /// What: Current client projection context.
  /// Why: Control availability can depend on local markdown/assistant state.
  /// How: Fill it from the UI's current local context.
  /// Example: {"can_capture_assistant": true}
  @$pb.TagNumber(4)
  SubjectPhaseProjectionContext get projectionContext => $_getN(3);
  @$pb.TagNumber(4)
  set projectionContext(SubjectPhaseProjectionContext v) { setField(4, v); }
  @$pb.TagNumber(4)
  $core.bool hasProjectionContext() => $_has(3);
  @$pb.TagNumber(4)
  void clearProjectionContext() => clearField(4);
  @$pb.TagNumber(4)
  SubjectPhaseProjectionContext ensureProjectionContext() => $_ensure(3);

  /// What: Stable client session id.
  /// Why: Client-specific progress can influence control projections.
  /// How: Reuse the client session id.
  /// Example: "flutter-shell-a"
  @$pb.TagNumber(5)
  $core.String get clientSessionId => $_getSZ(4);
  @$pb.TagNumber(5)
  set clientSessionId($core.String v) { $_setString(4, v); }
  @$pb.TagNumber(5)
  $core.bool hasClientSessionId() => $_has(4);
  @$pb.TagNumber(5)
  void clearClientSessionId() => clearField(5);
}

/// What: Response containing the control bundle for one phase.
/// Why: The client needs service-owned action/control projections plus trace
/// metadata.
/// How: Render `bundle` as the actionable control surface for the phase.
/// Valid Example:
///   {
///     "bundle": {"phase": "research", "more_actions": []},
///     "trace_id": "subject-control-response_6735be2e",
///     "parent_id": "subject-control-request_4c517f44"
///   }
class GetSubjectControlBundleResponse extends $pb.GeneratedMessage {
  factory GetSubjectControlBundleResponse({
    SubjectControlBundleView? bundle,
    $core.String? traceId,
    $core.String? parentId,
  }) {
    final $result = create();
    if (bundle != null) {
      $result.bundle = bundle;
    }
    if (traceId != null) {
      $result.traceId = traceId;
    }
    if (parentId != null) {
      $result.parentId = parentId;
    }
    return $result;
  }
  GetSubjectControlBundleResponse._() : super();
  factory GetSubjectControlBundleResponse.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory GetSubjectControlBundleResponse.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'GetSubjectControlBundleResponse', package: const $pb.PackageName(_omitMessageNames ? '' : 'realized.workstation.subjectworkflow.v1'), createEmptyInstance: create)
    ..aOM<SubjectControlBundleView>(1, _omitFieldNames ? '' : 'bundle', subBuilder: SubjectControlBundleView.create)
    ..aOS(100, _omitFieldNames ? '' : 'traceId')
    ..aOS(101, _omitFieldNames ? '' : 'parentId')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  GetSubjectControlBundleResponse clone() => GetSubjectControlBundleResponse()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  GetSubjectControlBundleResponse copyWith(void Function(GetSubjectControlBundleResponse) updates) => super.copyWith((message) => updates(message as GetSubjectControlBundleResponse)) as GetSubjectControlBundleResponse;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static GetSubjectControlBundleResponse create() => GetSubjectControlBundleResponse._();
  GetSubjectControlBundleResponse createEmptyInstance() => create();
  static $pb.PbList<GetSubjectControlBundleResponse> createRepeated() => $pb.PbList<GetSubjectControlBundleResponse>();
  @$core.pragma('dart2js:noInline')
  static GetSubjectControlBundleResponse getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<GetSubjectControlBundleResponse>(create);
  static GetSubjectControlBundleResponse? _defaultInstance;

  /// What: Control bundle for the requested phase.
  /// Why: This is the main payload for the request.
  /// How: Render its contained controls directly.
  /// Example: {"phase":"research","more_actions":[]}
  @$pb.TagNumber(1)
  SubjectControlBundleView get bundle => $_getN(0);
  @$pb.TagNumber(1)
  set bundle(SubjectControlBundleView v) { setField(1, v); }
  @$pb.TagNumber(1)
  $core.bool hasBundle() => $_has(0);
  @$pb.TagNumber(1)
  void clearBundle() => clearField(1);
  @$pb.TagNumber(1)
  SubjectControlBundleView ensureBundle() => $_ensure(0);

  /// What: Trace id for the response.
  /// Why: Control reads are traceable operations.
  /// How: Log it when debugging.
  /// Example: "subject-control-response_6735be2e"
  @$pb.TagNumber(100)
  $core.String get traceId => $_getSZ(1);
  @$pb.TagNumber(100)
  set traceId($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(100)
  $core.bool hasTraceId() => $_has(1);
  @$pb.TagNumber(100)
  void clearTraceId() => clearField(100);

  /// What: Parent trace id linking back to the request.
  /// Why: Diagnostics need request/response correlation.
  /// How: Treat it as opaque metadata.
  /// Example: "subject-control-request_4c517f44"
  @$pb.TagNumber(101)
  $core.String get parentId => $_getSZ(2);
  @$pb.TagNumber(101)
  set parentId($core.String v) { $_setString(2, v); }
  @$pb.TagNumber(101)
  $core.bool hasParentId() => $_has(2);
  @$pb.TagNumber(101)
  void clearParentId() => clearField(101);
}

/// What: One renderer-neutral pane projection.
/// Why: Clients often lay out the same phase data across several panes/cards.
/// How: Render text lines, rows, or a structured table according to the fields.
/// Valid Example:
///   {
///     "key": "learning",
///     "title": "Learning",
///     "lines": ["A city transit authority wants to modernize fare payment."],
///     "rows": [],
///     "is_structured_table": false
///   }
class SubjectPaneView extends $pb.GeneratedMessage {
  factory SubjectPaneView({
    $core.String? key,
    $core.String? title,
    $core.Iterable<$core.String>? lines,
    $core.Iterable<KeyValueRow>? rows,
    $core.bool? isStructuredTable,
    $core.Iterable<SubjectPaneItemView>? items,
  }) {
    final $result = create();
    if (key != null) {
      $result.key = key;
    }
    if (title != null) {
      $result.title = title;
    }
    if (lines != null) {
      $result.lines.addAll(lines);
    }
    if (rows != null) {
      $result.rows.addAll(rows);
    }
    if (isStructuredTable != null) {
      $result.isStructuredTable = isStructuredTable;
    }
    if (items != null) {
      $result.items.addAll(items);
    }
    return $result;
  }
  SubjectPaneView._() : super();
  factory SubjectPaneView.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory SubjectPaneView.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'SubjectPaneView', package: const $pb.PackageName(_omitMessageNames ? '' : 'realized.workstation.subjectworkflow.v1'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'key')
    ..aOS(2, _omitFieldNames ? '' : 'title')
    ..pPS(3, _omitFieldNames ? '' : 'lines')
    ..pc<KeyValueRow>(4, _omitFieldNames ? '' : 'rows', $pb.PbFieldType.PM, subBuilder: KeyValueRow.create)
    ..aOB(5, _omitFieldNames ? '' : 'isStructuredTable')
    ..pc<SubjectPaneItemView>(6, _omitFieldNames ? '' : 'items', $pb.PbFieldType.PM, subBuilder: SubjectPaneItemView.create)
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  SubjectPaneView clone() => SubjectPaneView()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  SubjectPaneView copyWith(void Function(SubjectPaneView) updates) => super.copyWith((message) => updates(message as SubjectPaneView)) as SubjectPaneView;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static SubjectPaneView create() => SubjectPaneView._();
  SubjectPaneView createEmptyInstance() => create();
  static $pb.PbList<SubjectPaneView> createRepeated() => $pb.PbList<SubjectPaneView>();
  @$core.pragma('dart2js:noInline')
  static SubjectPaneView getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<SubjectPaneView>(create);
  static SubjectPaneView? _defaultInstance;

  /// What: Canonical pane key.
  /// Why: Clients need a stable pane identity for layout and refresh.
  /// How: Use it as a renderer lookup key.
  /// Example: "learning"
  @$pb.TagNumber(1)
  $core.String get key => $_getSZ(0);
  @$pb.TagNumber(1)
  set key($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasKey() => $_has(0);
  @$pb.TagNumber(1)
  void clearKey() => clearField(1);

  /// What: Human-readable pane title.
  /// Why: Panes need display titles in multi-pane layouts.
  /// How: Render it as the pane heading.
  /// Example: "Learning"
  @$pb.TagNumber(2)
  $core.String get title => $_getSZ(1);
  @$pb.TagNumber(2)
  set title($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasTitle() => $_has(1);
  @$pb.TagNumber(2)
  void clearTitle() => clearField(2);

  /// What: Narrative text lines for the pane.
  /// Why: Many panes are text-first projections.
  /// How: Render each string as one line or paragraph.
  /// Example: ["A city transit authority wants to modernize fare payment."]
  @$pb.TagNumber(3)
  $core.List<$core.String> get lines => $_getList(2);

  /// What: Structured key/value rows for the pane.
  /// Why: Some panes are better represented as structured metadata.
  /// How: Render these rows when present.
  /// Example: []
  @$pb.TagNumber(4)
  $core.List<KeyValueRow> get rows => $_getList(3);

  /// What: Whether the pane should be rendered as a structured table.
  /// Why: Some pane content is fundamentally tabular.
  /// How: Use it as a rendering hint.
  /// Example: false
  @$pb.TagNumber(5)
  $core.bool get isStructuredTable => $_getBF(4);
  @$pb.TagNumber(5)
  set isStructuredTable($core.bool v) { $_setBool(4, v); }
  @$pb.TagNumber(5)
  $core.bool hasIsStructuredTable() => $_has(4);
  @$pb.TagNumber(5)
  void clearIsStructuredTable() => clearField(5);

  /// What: Typed items rendered by interactive inventory and tree panes.
  /// Why: Selection, checkbox, hierarchy, and identity must not be inferred
  /// from human-readable punctuation in `lines`.
  /// How: Use these entries as the behavioral source of truth and retain
  /// `lines` only as a presentation/fallback projection.
  @$pb.TagNumber(6)
  $core.List<SubjectPaneItemView> get items => $_getList(5);
}

/// What: One typed item in a subject pane.
/// Why: UI behavior must remain stable when human-readable prose changes.
/// How: Render the display fields and use the explicit selection, check-state,
/// hierarchy, and identity fields for interaction dispatch.
class SubjectPaneItemView extends $pb.GeneratedMessage {
  factory SubjectPaneItemView({
    $core.String? entryId,
    $core.String? entryKind,
    $core.String? label,
    $core.int? ordinal,
    $core.String? parentEntryId,
    $core.int? depth,
    $core.bool? selectable,
    $core.bool? selected,
    $core.bool? toggleable,
    $core.String? checkState,
    $core.bool? held,
    $core.String? status,
    $core.String? semanticKind,
    $core.String? renderKind,
    $core.String? evidenceMode,
    $core.String? transformMode,
    $core.String? sourceUnitId,
    $core.String? sourceItemId,
    $core.String? sourceRef,
    $core.String? sourceKind,
    $core.String? mediaType,
    $core.String? latestRevisionId,
    $core.String? latestRevisionKind,
    $core.int? revisionCount,
    $core.int? bundleFileCount,
    $core.String? sortKind,
    $core.String? summary,
    $core.String? description,
    $core.String? queryText,
    $core.String? notes,
    $core.double? confidence,
    $core.Iterable<$core.String>? relatedIds,
    $core.String? detailTitle,
    $core.Iterable<$core.String>? detailLines,
    $core.Iterable<KeyValueRow>? attributes,
  }) {
    final $result = create();
    if (entryId != null) {
      $result.entryId = entryId;
    }
    if (entryKind != null) {
      $result.entryKind = entryKind;
    }
    if (label != null) {
      $result.label = label;
    }
    if (ordinal != null) {
      $result.ordinal = ordinal;
    }
    if (parentEntryId != null) {
      $result.parentEntryId = parentEntryId;
    }
    if (depth != null) {
      $result.depth = depth;
    }
    if (selectable != null) {
      $result.selectable = selectable;
    }
    if (selected != null) {
      $result.selected = selected;
    }
    if (toggleable != null) {
      $result.toggleable = toggleable;
    }
    if (checkState != null) {
      $result.checkState = checkState;
    }
    if (held != null) {
      $result.held = held;
    }
    if (status != null) {
      $result.status = status;
    }
    if (semanticKind != null) {
      $result.semanticKind = semanticKind;
    }
    if (renderKind != null) {
      $result.renderKind = renderKind;
    }
    if (evidenceMode != null) {
      $result.evidenceMode = evidenceMode;
    }
    if (transformMode != null) {
      $result.transformMode = transformMode;
    }
    if (sourceUnitId != null) {
      $result.sourceUnitId = sourceUnitId;
    }
    if (sourceItemId != null) {
      $result.sourceItemId = sourceItemId;
    }
    if (sourceRef != null) {
      $result.sourceRef = sourceRef;
    }
    if (sourceKind != null) {
      $result.sourceKind = sourceKind;
    }
    if (mediaType != null) {
      $result.mediaType = mediaType;
    }
    if (latestRevisionId != null) {
      $result.latestRevisionId = latestRevisionId;
    }
    if (latestRevisionKind != null) {
      $result.latestRevisionKind = latestRevisionKind;
    }
    if (revisionCount != null) {
      $result.revisionCount = revisionCount;
    }
    if (bundleFileCount != null) {
      $result.bundleFileCount = bundleFileCount;
    }
    if (sortKind != null) {
      $result.sortKind = sortKind;
    }
    if (summary != null) {
      $result.summary = summary;
    }
    if (description != null) {
      $result.description = description;
    }
    if (queryText != null) {
      $result.queryText = queryText;
    }
    if (notes != null) {
      $result.notes = notes;
    }
    if (confidence != null) {
      $result.confidence = confidence;
    }
    if (relatedIds != null) {
      $result.relatedIds.addAll(relatedIds);
    }
    if (detailTitle != null) {
      $result.detailTitle = detailTitle;
    }
    if (detailLines != null) {
      $result.detailLines.addAll(detailLines);
    }
    if (attributes != null) {
      $result.attributes.addAll(attributes);
    }
    return $result;
  }
  SubjectPaneItemView._() : super();
  factory SubjectPaneItemView.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory SubjectPaneItemView.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'SubjectPaneItemView', package: const $pb.PackageName(_omitMessageNames ? '' : 'realized.workstation.subjectworkflow.v1'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'entryId')
    ..aOS(2, _omitFieldNames ? '' : 'entryKind')
    ..aOS(3, _omitFieldNames ? '' : 'label')
    ..a<$core.int>(4, _omitFieldNames ? '' : 'ordinal', $pb.PbFieldType.O3)
    ..aOS(5, _omitFieldNames ? '' : 'parentEntryId')
    ..a<$core.int>(6, _omitFieldNames ? '' : 'depth', $pb.PbFieldType.O3)
    ..aOB(7, _omitFieldNames ? '' : 'selectable')
    ..aOB(8, _omitFieldNames ? '' : 'selected')
    ..aOB(9, _omitFieldNames ? '' : 'toggleable')
    ..aOS(10, _omitFieldNames ? '' : 'checkState')
    ..aOB(11, _omitFieldNames ? '' : 'held')
    ..aOS(12, _omitFieldNames ? '' : 'status')
    ..aOS(13, _omitFieldNames ? '' : 'semanticKind')
    ..aOS(14, _omitFieldNames ? '' : 'renderKind')
    ..aOS(15, _omitFieldNames ? '' : 'evidenceMode')
    ..aOS(16, _omitFieldNames ? '' : 'transformMode')
    ..aOS(17, _omitFieldNames ? '' : 'sourceUnitId')
    ..aOS(18, _omitFieldNames ? '' : 'sourceItemId')
    ..aOS(19, _omitFieldNames ? '' : 'sourceRef')
    ..aOS(20, _omitFieldNames ? '' : 'sourceKind')
    ..aOS(21, _omitFieldNames ? '' : 'mediaType')
    ..aOS(22, _omitFieldNames ? '' : 'latestRevisionId')
    ..aOS(23, _omitFieldNames ? '' : 'latestRevisionKind')
    ..a<$core.int>(24, _omitFieldNames ? '' : 'revisionCount', $pb.PbFieldType.O3)
    ..a<$core.int>(25, _omitFieldNames ? '' : 'bundleFileCount', $pb.PbFieldType.O3)
    ..aOS(26, _omitFieldNames ? '' : 'sortKind')
    ..aOS(27, _omitFieldNames ? '' : 'summary')
    ..aOS(28, _omitFieldNames ? '' : 'description')
    ..aOS(29, _omitFieldNames ? '' : 'queryText')
    ..aOS(30, _omitFieldNames ? '' : 'notes')
    ..a<$core.double>(31, _omitFieldNames ? '' : 'confidence', $pb.PbFieldType.OD)
    ..pPS(32, _omitFieldNames ? '' : 'relatedIds')
    ..aOS(33, _omitFieldNames ? '' : 'detailTitle')
    ..pPS(34, _omitFieldNames ? '' : 'detailLines')
    ..pc<KeyValueRow>(35, _omitFieldNames ? '' : 'attributes', $pb.PbFieldType.PM, subBuilder: KeyValueRow.create)
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  SubjectPaneItemView clone() => SubjectPaneItemView()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  SubjectPaneItemView copyWith(void Function(SubjectPaneItemView) updates) => super.copyWith((message) => updates(message as SubjectPaneItemView)) as SubjectPaneItemView;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static SubjectPaneItemView create() => SubjectPaneItemView._();
  SubjectPaneItemView createEmptyInstance() => create();
  static $pb.PbList<SubjectPaneItemView> createRepeated() => $pb.PbList<SubjectPaneItemView>();
  @$core.pragma('dart2js:noInline')
  static SubjectPaneItemView getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<SubjectPaneItemView>(create);
  static SubjectPaneItemView? _defaultInstance;

  @$pb.TagNumber(1)
  $core.String get entryId => $_getSZ(0);
  @$pb.TagNumber(1)
  set entryId($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasEntryId() => $_has(0);
  @$pb.TagNumber(1)
  void clearEntryId() => clearField(1);

  @$pb.TagNumber(2)
  $core.String get entryKind => $_getSZ(1);
  @$pb.TagNumber(2)
  set entryKind($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasEntryKind() => $_has(1);
  @$pb.TagNumber(2)
  void clearEntryKind() => clearField(2);

  @$pb.TagNumber(3)
  $core.String get label => $_getSZ(2);
  @$pb.TagNumber(3)
  set label($core.String v) { $_setString(2, v); }
  @$pb.TagNumber(3)
  $core.bool hasLabel() => $_has(2);
  @$pb.TagNumber(3)
  void clearLabel() => clearField(3);

  @$pb.TagNumber(4)
  $core.int get ordinal => $_getIZ(3);
  @$pb.TagNumber(4)
  set ordinal($core.int v) { $_setSignedInt32(3, v); }
  @$pb.TagNumber(4)
  $core.bool hasOrdinal() => $_has(3);
  @$pb.TagNumber(4)
  void clearOrdinal() => clearField(4);

  @$pb.TagNumber(5)
  $core.String get parentEntryId => $_getSZ(4);
  @$pb.TagNumber(5)
  set parentEntryId($core.String v) { $_setString(4, v); }
  @$pb.TagNumber(5)
  $core.bool hasParentEntryId() => $_has(4);
  @$pb.TagNumber(5)
  void clearParentEntryId() => clearField(5);

  @$pb.TagNumber(6)
  $core.int get depth => $_getIZ(5);
  @$pb.TagNumber(6)
  set depth($core.int v) { $_setSignedInt32(5, v); }
  @$pb.TagNumber(6)
  $core.bool hasDepth() => $_has(5);
  @$pb.TagNumber(6)
  void clearDepth() => clearField(6);

  @$pb.TagNumber(7)
  $core.bool get selectable => $_getBF(6);
  @$pb.TagNumber(7)
  set selectable($core.bool v) { $_setBool(6, v); }
  @$pb.TagNumber(7)
  $core.bool hasSelectable() => $_has(6);
  @$pb.TagNumber(7)
  void clearSelectable() => clearField(7);

  @$pb.TagNumber(8)
  $core.bool get selected => $_getBF(7);
  @$pb.TagNumber(8)
  set selected($core.bool v) { $_setBool(7, v); }
  @$pb.TagNumber(8)
  $core.bool hasSelected() => $_has(7);
  @$pb.TagNumber(8)
  void clearSelected() => clearField(8);

  @$pb.TagNumber(9)
  $core.bool get toggleable => $_getBF(8);
  @$pb.TagNumber(9)
  set toggleable($core.bool v) { $_setBool(8, v); }
  @$pb.TagNumber(9)
  $core.bool hasToggleable() => $_has(8);
  @$pb.TagNumber(9)
  void clearToggleable() => clearField(9);

  @$pb.TagNumber(10)
  $core.String get checkState => $_getSZ(9);
  @$pb.TagNumber(10)
  set checkState($core.String v) { $_setString(9, v); }
  @$pb.TagNumber(10)
  $core.bool hasCheckState() => $_has(9);
  @$pb.TagNumber(10)
  void clearCheckState() => clearField(10);

  @$pb.TagNumber(11)
  $core.bool get held => $_getBF(10);
  @$pb.TagNumber(11)
  set held($core.bool v) { $_setBool(10, v); }
  @$pb.TagNumber(11)
  $core.bool hasHeld() => $_has(10);
  @$pb.TagNumber(11)
  void clearHeld() => clearField(11);

  @$pb.TagNumber(12)
  $core.String get status => $_getSZ(11);
  @$pb.TagNumber(12)
  set status($core.String v) { $_setString(11, v); }
  @$pb.TagNumber(12)
  $core.bool hasStatus() => $_has(11);
  @$pb.TagNumber(12)
  void clearStatus() => clearField(12);

  @$pb.TagNumber(13)
  $core.String get semanticKind => $_getSZ(12);
  @$pb.TagNumber(13)
  set semanticKind($core.String v) { $_setString(12, v); }
  @$pb.TagNumber(13)
  $core.bool hasSemanticKind() => $_has(12);
  @$pb.TagNumber(13)
  void clearSemanticKind() => clearField(13);

  @$pb.TagNumber(14)
  $core.String get renderKind => $_getSZ(13);
  @$pb.TagNumber(14)
  set renderKind($core.String v) { $_setString(13, v); }
  @$pb.TagNumber(14)
  $core.bool hasRenderKind() => $_has(13);
  @$pb.TagNumber(14)
  void clearRenderKind() => clearField(14);

  @$pb.TagNumber(15)
  $core.String get evidenceMode => $_getSZ(14);
  @$pb.TagNumber(15)
  set evidenceMode($core.String v) { $_setString(14, v); }
  @$pb.TagNumber(15)
  $core.bool hasEvidenceMode() => $_has(14);
  @$pb.TagNumber(15)
  void clearEvidenceMode() => clearField(15);

  @$pb.TagNumber(16)
  $core.String get transformMode => $_getSZ(15);
  @$pb.TagNumber(16)
  set transformMode($core.String v) { $_setString(15, v); }
  @$pb.TagNumber(16)
  $core.bool hasTransformMode() => $_has(15);
  @$pb.TagNumber(16)
  void clearTransformMode() => clearField(16);

  @$pb.TagNumber(17)
  $core.String get sourceUnitId => $_getSZ(16);
  @$pb.TagNumber(17)
  set sourceUnitId($core.String v) { $_setString(16, v); }
  @$pb.TagNumber(17)
  $core.bool hasSourceUnitId() => $_has(16);
  @$pb.TagNumber(17)
  void clearSourceUnitId() => clearField(17);

  @$pb.TagNumber(18)
  $core.String get sourceItemId => $_getSZ(17);
  @$pb.TagNumber(18)
  set sourceItemId($core.String v) { $_setString(17, v); }
  @$pb.TagNumber(18)
  $core.bool hasSourceItemId() => $_has(17);
  @$pb.TagNumber(18)
  void clearSourceItemId() => clearField(18);

  @$pb.TagNumber(19)
  $core.String get sourceRef => $_getSZ(18);
  @$pb.TagNumber(19)
  set sourceRef($core.String v) { $_setString(18, v); }
  @$pb.TagNumber(19)
  $core.bool hasSourceRef() => $_has(18);
  @$pb.TagNumber(19)
  void clearSourceRef() => clearField(19);

  @$pb.TagNumber(20)
  $core.String get sourceKind => $_getSZ(19);
  @$pb.TagNumber(20)
  set sourceKind($core.String v) { $_setString(19, v); }
  @$pb.TagNumber(20)
  $core.bool hasSourceKind() => $_has(19);
  @$pb.TagNumber(20)
  void clearSourceKind() => clearField(20);

  @$pb.TagNumber(21)
  $core.String get mediaType => $_getSZ(20);
  @$pb.TagNumber(21)
  set mediaType($core.String v) { $_setString(20, v); }
  @$pb.TagNumber(21)
  $core.bool hasMediaType() => $_has(20);
  @$pb.TagNumber(21)
  void clearMediaType() => clearField(21);

  @$pb.TagNumber(22)
  $core.String get latestRevisionId => $_getSZ(21);
  @$pb.TagNumber(22)
  set latestRevisionId($core.String v) { $_setString(21, v); }
  @$pb.TagNumber(22)
  $core.bool hasLatestRevisionId() => $_has(21);
  @$pb.TagNumber(22)
  void clearLatestRevisionId() => clearField(22);

  @$pb.TagNumber(23)
  $core.String get latestRevisionKind => $_getSZ(22);
  @$pb.TagNumber(23)
  set latestRevisionKind($core.String v) { $_setString(22, v); }
  @$pb.TagNumber(23)
  $core.bool hasLatestRevisionKind() => $_has(22);
  @$pb.TagNumber(23)
  void clearLatestRevisionKind() => clearField(23);

  @$pb.TagNumber(24)
  $core.int get revisionCount => $_getIZ(23);
  @$pb.TagNumber(24)
  set revisionCount($core.int v) { $_setSignedInt32(23, v); }
  @$pb.TagNumber(24)
  $core.bool hasRevisionCount() => $_has(23);
  @$pb.TagNumber(24)
  void clearRevisionCount() => clearField(24);

  @$pb.TagNumber(25)
  $core.int get bundleFileCount => $_getIZ(24);
  @$pb.TagNumber(25)
  set bundleFileCount($core.int v) { $_setSignedInt32(24, v); }
  @$pb.TagNumber(25)
  $core.bool hasBundleFileCount() => $_has(24);
  @$pb.TagNumber(25)
  void clearBundleFileCount() => clearField(25);

  @$pb.TagNumber(26)
  $core.String get sortKind => $_getSZ(25);
  @$pb.TagNumber(26)
  set sortKind($core.String v) { $_setString(25, v); }
  @$pb.TagNumber(26)
  $core.bool hasSortKind() => $_has(25);
  @$pb.TagNumber(26)
  void clearSortKind() => clearField(26);

  @$pb.TagNumber(27)
  $core.String get summary => $_getSZ(26);
  @$pb.TagNumber(27)
  set summary($core.String v) { $_setString(26, v); }
  @$pb.TagNumber(27)
  $core.bool hasSummary() => $_has(26);
  @$pb.TagNumber(27)
  void clearSummary() => clearField(27);

  @$pb.TagNumber(28)
  $core.String get description => $_getSZ(27);
  @$pb.TagNumber(28)
  set description($core.String v) { $_setString(27, v); }
  @$pb.TagNumber(28)
  $core.bool hasDescription() => $_has(27);
  @$pb.TagNumber(28)
  void clearDescription() => clearField(28);

  @$pb.TagNumber(29)
  $core.String get queryText => $_getSZ(28);
  @$pb.TagNumber(29)
  set queryText($core.String v) { $_setString(28, v); }
  @$pb.TagNumber(29)
  $core.bool hasQueryText() => $_has(28);
  @$pb.TagNumber(29)
  void clearQueryText() => clearField(29);

  @$pb.TagNumber(30)
  $core.String get notes => $_getSZ(29);
  @$pb.TagNumber(30)
  set notes($core.String v) { $_setString(29, v); }
  @$pb.TagNumber(30)
  $core.bool hasNotes() => $_has(29);
  @$pb.TagNumber(30)
  void clearNotes() => clearField(30);

  @$pb.TagNumber(31)
  $core.double get confidence => $_getN(30);
  @$pb.TagNumber(31)
  set confidence($core.double v) { $_setDouble(30, v); }
  @$pb.TagNumber(31)
  $core.bool hasConfidence() => $_has(30);
  @$pb.TagNumber(31)
  void clearConfidence() => clearField(31);

  @$pb.TagNumber(32)
  $core.List<$core.String> get relatedIds => $_getList(31);

  @$pb.TagNumber(33)
  $core.String get detailTitle => $_getSZ(32);
  @$pb.TagNumber(33)
  set detailTitle($core.String v) { $_setString(32, v); }
  @$pb.TagNumber(33)
  $core.bool hasDetailTitle() => $_has(32);
  @$pb.TagNumber(33)
  void clearDetailTitle() => clearField(33);

  @$pb.TagNumber(34)
  $core.List<$core.String> get detailLines => $_getList(33);

  @$pb.TagNumber(35)
  $core.List<KeyValueRow> get attributes => $_getList(34);
}

/// What: Full set of panes for one phase.
/// Why: Clients need a stable pane grouping for multi-pane layouts.
/// How: Render the panes in the layout that matches the active phase.
/// Valid Example:
///   {
///     "phase": "research",
///     "panes": [{"key": "learning", "title": "Learning"}]
///   }
class SubjectPaneBundleView extends $pb.GeneratedMessage {
  factory SubjectPaneBundleView({
    $core.String? phase,
    $core.Iterable<SubjectPaneView>? panes,
  }) {
    final $result = create();
    if (phase != null) {
      $result.phase = phase;
    }
    if (panes != null) {
      $result.panes.addAll(panes);
    }
    return $result;
  }
  SubjectPaneBundleView._() : super();
  factory SubjectPaneBundleView.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory SubjectPaneBundleView.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'SubjectPaneBundleView', package: const $pb.PackageName(_omitMessageNames ? '' : 'realized.workstation.subjectworkflow.v1'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'phase')
    ..pc<SubjectPaneView>(2, _omitFieldNames ? '' : 'panes', $pb.PbFieldType.PM, subBuilder: SubjectPaneView.create)
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  SubjectPaneBundleView clone() => SubjectPaneBundleView()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  SubjectPaneBundleView copyWith(void Function(SubjectPaneBundleView) updates) => super.copyWith((message) => updates(message as SubjectPaneBundleView)) as SubjectPaneBundleView;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static SubjectPaneBundleView create() => SubjectPaneBundleView._();
  SubjectPaneBundleView createEmptyInstance() => create();
  static $pb.PbList<SubjectPaneBundleView> createRepeated() => $pb.PbList<SubjectPaneBundleView>();
  @$core.pragma('dart2js:noInline')
  static SubjectPaneBundleView getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<SubjectPaneBundleView>(create);
  static SubjectPaneBundleView? _defaultInstance;

  /// What: Phase that owns this pane bundle.
  /// Why: Clients may cache pane bundles across phases.
  /// How: Associate it with the active phase key.
  /// Example: "research"
  @$pb.TagNumber(1)
  $core.String get phase => $_getSZ(0);
  @$pb.TagNumber(1)
  set phase($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasPhase() => $_has(0);
  @$pb.TagNumber(1)
  void clearPhase() => clearField(1);

  /// What: Pane projections for the phase.
  /// Why: The service owns the semantic pane contents.
  /// How: Render one pane/card per entry.
  /// Example: [{"key":"learning","title":"Learning"}]
  @$pb.TagNumber(2)
  $core.List<SubjectPaneView> get panes => $_getList(1);
}

/// What: Request for the pane bundle of one phase.
/// Why: Some clients fetch panes independently from the rest of the snapshot.
/// How: Supply root, subject, phase, and client session id.
/// Valid Example:
///   {
///     "root_path": "/srv/workstations/transit",
///     "subject_id": "smart_city_travel",
///     "phase": "research",
///     "client_session_id": "flutter-shell-a"
///   }
class GetSubjectPaneBundleRequest extends $pb.GeneratedMessage {
  factory GetSubjectPaneBundleRequest({
    $core.String? rootPath,
    $core.String? subjectId,
    $core.String? phase,
    $core.String? clientSessionId,
  }) {
    final $result = create();
    if (rootPath != null) {
      $result.rootPath = rootPath;
    }
    if (subjectId != null) {
      $result.subjectId = subjectId;
    }
    if (phase != null) {
      $result.phase = phase;
    }
    if (clientSessionId != null) {
      $result.clientSessionId = clientSessionId;
    }
    return $result;
  }
  GetSubjectPaneBundleRequest._() : super();
  factory GetSubjectPaneBundleRequest.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory GetSubjectPaneBundleRequest.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'GetSubjectPaneBundleRequest', package: const $pb.PackageName(_omitMessageNames ? '' : 'realized.workstation.subjectworkflow.v1'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'rootPath')
    ..aOS(2, _omitFieldNames ? '' : 'subjectId')
    ..aOS(3, _omitFieldNames ? '' : 'phase')
    ..aOS(4, _omitFieldNames ? '' : 'clientSessionId')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  GetSubjectPaneBundleRequest clone() => GetSubjectPaneBundleRequest()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  GetSubjectPaneBundleRequest copyWith(void Function(GetSubjectPaneBundleRequest) updates) => super.copyWith((message) => updates(message as GetSubjectPaneBundleRequest)) as GetSubjectPaneBundleRequest;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static GetSubjectPaneBundleRequest create() => GetSubjectPaneBundleRequest._();
  GetSubjectPaneBundleRequest createEmptyInstance() => create();
  static $pb.PbList<GetSubjectPaneBundleRequest> createRepeated() => $pb.PbList<GetSubjectPaneBundleRequest>();
  @$core.pragma('dart2js:noInline')
  static GetSubjectPaneBundleRequest getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<GetSubjectPaneBundleRequest>(create);
  static GetSubjectPaneBundleRequest? _defaultInstance;

  /// What: Absolute workstation root path on the server.
  /// Why: Pane bundles are scoped to one workstation.
  /// How: Reuse the bootstrapped root.
  /// Example: "/srv/workstations/transit"
  @$pb.TagNumber(1)
  $core.String get rootPath => $_getSZ(0);
  @$pb.TagNumber(1)
  set rootPath($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasRootPath() => $_has(0);
  @$pb.TagNumber(1)
  void clearRootPath() => clearField(1);

  /// What: Target subject id.
  /// Why: Pane projections are subject-specific.
  /// How: Use the selected subject id.
  /// Example: "smart_city_travel"
  @$pb.TagNumber(2)
  $core.String get subjectId => $_getSZ(1);
  @$pb.TagNumber(2)
  set subjectId($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasSubjectId() => $_has(1);
  @$pb.TagNumber(2)
  void clearSubjectId() => clearField(2);

  /// What: Requested phase key.
  /// Why: Pane sets differ by phase.
  /// How: Pass the active phase.
  /// Example: "research"
  @$pb.TagNumber(3)
  $core.String get phase => $_getSZ(2);
  @$pb.TagNumber(3)
  set phase($core.String v) { $_setString(2, v); }
  @$pb.TagNumber(3)
  $core.bool hasPhase() => $_has(2);
  @$pb.TagNumber(3)
  void clearPhase() => clearField(3);

  /// What: Stable client session id.
  /// Why: Some panes may depend on client-specific view state.
  /// How: Reuse the client session id.
  /// Example: "flutter-shell-a"
  @$pb.TagNumber(4)
  $core.String get clientSessionId => $_getSZ(3);
  @$pb.TagNumber(4)
  set clientSessionId($core.String v) { $_setString(3, v); }
  @$pb.TagNumber(4)
  $core.bool hasClientSessionId() => $_has(3);
  @$pb.TagNumber(4)
  void clearClientSessionId() => clearField(4);
}

/// What: Response containing the pane bundle for one phase.
/// Why: Clients need semantic pane contents and trace metadata.
/// How: Render `bundle` in the phase's multi-pane layout.
/// Valid Example:
///   {
///     "bundle": {"phase": "research", "panes": []},
///     "trace_id": "subject-pane-response_11cab5b0",
///     "parent_id": "subject-pane-request_84e6d2fe"
///   }
class GetSubjectPaneBundleResponse extends $pb.GeneratedMessage {
  factory GetSubjectPaneBundleResponse({
    SubjectPaneBundleView? bundle,
    $core.String? traceId,
    $core.String? parentId,
  }) {
    final $result = create();
    if (bundle != null) {
      $result.bundle = bundle;
    }
    if (traceId != null) {
      $result.traceId = traceId;
    }
    if (parentId != null) {
      $result.parentId = parentId;
    }
    return $result;
  }
  GetSubjectPaneBundleResponse._() : super();
  factory GetSubjectPaneBundleResponse.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory GetSubjectPaneBundleResponse.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'GetSubjectPaneBundleResponse', package: const $pb.PackageName(_omitMessageNames ? '' : 'realized.workstation.subjectworkflow.v1'), createEmptyInstance: create)
    ..aOM<SubjectPaneBundleView>(1, _omitFieldNames ? '' : 'bundle', subBuilder: SubjectPaneBundleView.create)
    ..aOS(100, _omitFieldNames ? '' : 'traceId')
    ..aOS(101, _omitFieldNames ? '' : 'parentId')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  GetSubjectPaneBundleResponse clone() => GetSubjectPaneBundleResponse()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  GetSubjectPaneBundleResponse copyWith(void Function(GetSubjectPaneBundleResponse) updates) => super.copyWith((message) => updates(message as GetSubjectPaneBundleResponse)) as GetSubjectPaneBundleResponse;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static GetSubjectPaneBundleResponse create() => GetSubjectPaneBundleResponse._();
  GetSubjectPaneBundleResponse createEmptyInstance() => create();
  static $pb.PbList<GetSubjectPaneBundleResponse> createRepeated() => $pb.PbList<GetSubjectPaneBundleResponse>();
  @$core.pragma('dart2js:noInline')
  static GetSubjectPaneBundleResponse getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<GetSubjectPaneBundleResponse>(create);
  static GetSubjectPaneBundleResponse? _defaultInstance;

  /// What: Pane bundle payload.
  /// Why: This is the data the client asked for.
  /// How: Render its panes directly.
  /// Example: {"phase":"research","panes":[]}
  @$pb.TagNumber(1)
  SubjectPaneBundleView get bundle => $_getN(0);
  @$pb.TagNumber(1)
  set bundle(SubjectPaneBundleView v) { setField(1, v); }
  @$pb.TagNumber(1)
  $core.bool hasBundle() => $_has(0);
  @$pb.TagNumber(1)
  void clearBundle() => clearField(1);
  @$pb.TagNumber(1)
  SubjectPaneBundleView ensureBundle() => $_ensure(0);

  /// What: Trace id for the response.
  /// Why: Pane reads are traceable operations.
  /// How: Log it for diagnostics when needed.
  /// Example: "subject-pane-response_11cab5b0"
  @$pb.TagNumber(100)
  $core.String get traceId => $_getSZ(1);
  @$pb.TagNumber(100)
  set traceId($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(100)
  $core.bool hasTraceId() => $_has(1);
  @$pb.TagNumber(100)
  void clearTraceId() => clearField(100);

  /// What: Parent trace id linking back to the request.
  /// Why: Diagnostics need request/response linkage.
  /// How: Treat it as opaque metadata.
  /// Example: "subject-pane-request_84e6d2fe"
  @$pb.TagNumber(101)
  $core.String get parentId => $_getSZ(2);
  @$pb.TagNumber(101)
  set parentId($core.String v) { $_setString(2, v); }
  @$pb.TagNumber(101)
  $core.bool hasParentId() => $_has(2);
  @$pb.TagNumber(101)
  void clearParentId() => clearField(101);
}

/// What: Composite snapshot containing phase, control, and pane projections.
/// Why: Most clients want one authoritative workflow snapshot rather than
/// separate per-surface calls.
/// How: Treat it as the full semantic projection for one subject/phase.
/// Valid Example:
///   {
///     "phase_view": {"phase": "research"},
///     "control_bundle": {"phase": "research"},
///     "pane_bundle": {"phase": "research"}
///   }
class SubjectWorkflowSnapshotView extends $pb.GeneratedMessage {
  factory SubjectWorkflowSnapshotView({
    SubjectPhaseView? phaseView,
    SubjectControlBundleView? controlBundle,
    SubjectPaneBundleView? paneBundle,
  }) {
    final $result = create();
    if (phaseView != null) {
      $result.phaseView = phaseView;
    }
    if (controlBundle != null) {
      $result.controlBundle = controlBundle;
    }
    if (paneBundle != null) {
      $result.paneBundle = paneBundle;
    }
    return $result;
  }
  SubjectWorkflowSnapshotView._() : super();
  factory SubjectWorkflowSnapshotView.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory SubjectWorkflowSnapshotView.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'SubjectWorkflowSnapshotView', package: const $pb.PackageName(_omitMessageNames ? '' : 'realized.workstation.subjectworkflow.v1'), createEmptyInstance: create)
    ..aOM<SubjectPhaseView>(1, _omitFieldNames ? '' : 'phaseView', subBuilder: SubjectPhaseView.create)
    ..aOM<SubjectControlBundleView>(2, _omitFieldNames ? '' : 'controlBundle', subBuilder: SubjectControlBundleView.create)
    ..aOM<SubjectPaneBundleView>(3, _omitFieldNames ? '' : 'paneBundle', subBuilder: SubjectPaneBundleView.create)
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  SubjectWorkflowSnapshotView clone() => SubjectWorkflowSnapshotView()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  SubjectWorkflowSnapshotView copyWith(void Function(SubjectWorkflowSnapshotView) updates) => super.copyWith((message) => updates(message as SubjectWorkflowSnapshotView)) as SubjectWorkflowSnapshotView;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static SubjectWorkflowSnapshotView create() => SubjectWorkflowSnapshotView._();
  SubjectWorkflowSnapshotView createEmptyInstance() => create();
  static $pb.PbList<SubjectWorkflowSnapshotView> createRepeated() => $pb.PbList<SubjectWorkflowSnapshotView>();
  @$core.pragma('dart2js:noInline')
  static SubjectWorkflowSnapshotView getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<SubjectWorkflowSnapshotView>(create);
  static SubjectWorkflowSnapshotView? _defaultInstance;

  /// What: Main phase projection.
  /// Why: The snapshot needs the phase body.
  /// How: Render it as the primary phase content.
  /// Example: {"phase":"research"}
  @$pb.TagNumber(1)
  SubjectPhaseView get phaseView => $_getN(0);
  @$pb.TagNumber(1)
  set phaseView(SubjectPhaseView v) { setField(1, v); }
  @$pb.TagNumber(1)
  $core.bool hasPhaseView() => $_has(0);
  @$pb.TagNumber(1)
  void clearPhaseView() => clearField(1);
  @$pb.TagNumber(1)
  SubjectPhaseView ensurePhaseView() => $_ensure(0);

  /// What: Control bundle for the phase.
  /// Why: The snapshot should include the actionable control surface.
  /// How: Render its controls alongside the phase body.
  /// Example: {"phase":"research"}
  @$pb.TagNumber(2)
  SubjectControlBundleView get controlBundle => $_getN(1);
  @$pb.TagNumber(2)
  set controlBundle(SubjectControlBundleView v) { setField(2, v); }
  @$pb.TagNumber(2)
  $core.bool hasControlBundle() => $_has(1);
  @$pb.TagNumber(2)
  void clearControlBundle() => clearField(2);
  @$pb.TagNumber(2)
  SubjectControlBundleView ensureControlBundle() => $_ensure(1);

  /// What: Pane bundle for the phase.
  /// Why: Multi-pane clients need explicit pane content.
  /// How: Render it in the phase layout.
  /// Example: {"phase":"research"}
  @$pb.TagNumber(3)
  SubjectPaneBundleView get paneBundle => $_getN(2);
  @$pb.TagNumber(3)
  set paneBundle(SubjectPaneBundleView v) { setField(3, v); }
  @$pb.TagNumber(3)
  $core.bool hasPaneBundle() => $_has(2);
  @$pb.TagNumber(3)
  void clearPaneBundle() => clearField(3);
  @$pb.TagNumber(3)
  SubjectPaneBundleView ensurePaneBundle() => $_ensure(2);
}

/// What: Request for the full composite workflow snapshot.
/// Why: Clients usually need one authoritative initial snapshot before
/// switching to the watch stream.
/// How: Call this before `WatchSubjectWorkflow`.
/// Valid Example:
///   {
///     "root_path": "/srv/workstations/transit",
///     "subject_id": "smart_city_travel",
///     "phase": "research",
///     "projection_context": {"can_capture_assistant": true},
///     "client_session_id": "flutter-shell-a"
///   }
class GetSubjectWorkflowSnapshotRequest extends $pb.GeneratedMessage {
  factory GetSubjectWorkflowSnapshotRequest({
    $core.String? rootPath,
    $core.String? subjectId,
    $core.String? phase,
    SubjectPhaseProjectionContext? projectionContext,
    $core.String? clientSessionId,
  }) {
    final $result = create();
    if (rootPath != null) {
      $result.rootPath = rootPath;
    }
    if (subjectId != null) {
      $result.subjectId = subjectId;
    }
    if (phase != null) {
      $result.phase = phase;
    }
    if (projectionContext != null) {
      $result.projectionContext = projectionContext;
    }
    if (clientSessionId != null) {
      $result.clientSessionId = clientSessionId;
    }
    return $result;
  }
  GetSubjectWorkflowSnapshotRequest._() : super();
  factory GetSubjectWorkflowSnapshotRequest.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory GetSubjectWorkflowSnapshotRequest.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'GetSubjectWorkflowSnapshotRequest', package: const $pb.PackageName(_omitMessageNames ? '' : 'realized.workstation.subjectworkflow.v1'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'rootPath')
    ..aOS(2, _omitFieldNames ? '' : 'subjectId')
    ..aOS(3, _omitFieldNames ? '' : 'phase')
    ..aOM<SubjectPhaseProjectionContext>(4, _omitFieldNames ? '' : 'projectionContext', subBuilder: SubjectPhaseProjectionContext.create)
    ..aOS(5, _omitFieldNames ? '' : 'clientSessionId')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  GetSubjectWorkflowSnapshotRequest clone() => GetSubjectWorkflowSnapshotRequest()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  GetSubjectWorkflowSnapshotRequest copyWith(void Function(GetSubjectWorkflowSnapshotRequest) updates) => super.copyWith((message) => updates(message as GetSubjectWorkflowSnapshotRequest)) as GetSubjectWorkflowSnapshotRequest;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static GetSubjectWorkflowSnapshotRequest create() => GetSubjectWorkflowSnapshotRequest._();
  GetSubjectWorkflowSnapshotRequest createEmptyInstance() => create();
  static $pb.PbList<GetSubjectWorkflowSnapshotRequest> createRepeated() => $pb.PbList<GetSubjectWorkflowSnapshotRequest>();
  @$core.pragma('dart2js:noInline')
  static GetSubjectWorkflowSnapshotRequest getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<GetSubjectWorkflowSnapshotRequest>(create);
  static GetSubjectWorkflowSnapshotRequest? _defaultInstance;

  /// What: Absolute workstation root path on the server.
  /// Why: Snapshots are scoped to one workstation.
  /// How: Reuse the bootstrapped root.
  /// Example: "/srv/workstations/transit"
  @$pb.TagNumber(1)
  $core.String get rootPath => $_getSZ(0);
  @$pb.TagNumber(1)
  set rootPath($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasRootPath() => $_has(0);
  @$pb.TagNumber(1)
  void clearRootPath() => clearField(1);

  /// What: Target subject id.
  /// Why: The server needs to know which subject to snapshot.
  /// How: Use the selected subject id.
  /// Example: "smart_city_travel"
  @$pb.TagNumber(2)
  $core.String get subjectId => $_getSZ(1);
  @$pb.TagNumber(2)
  set subjectId($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasSubjectId() => $_has(1);
  @$pb.TagNumber(2)
  void clearSubjectId() => clearField(2);

  /// What: Requested phase key.
  /// Why: Snapshots are phase-specific.
  /// How: Pass the phase the UI intends to render.
  /// Example: "research"
  @$pb.TagNumber(3)
  $core.String get phase => $_getSZ(2);
  @$pb.TagNumber(3)
  set phase($core.String v) { $_setString(2, v); }
  @$pb.TagNumber(3)
  $core.bool hasPhase() => $_has(2);
  @$pb.TagNumber(3)
  void clearPhase() => clearField(3);

  /// What: Current client projection context.
  /// Why: Snapshot materialization can depend on local markdown/assistant state.
  /// How: Fill it from the current UI context.
  /// Example: {"can_capture_assistant": true}
  @$pb.TagNumber(4)
  SubjectPhaseProjectionContext get projectionContext => $_getN(3);
  @$pb.TagNumber(4)
  set projectionContext(SubjectPhaseProjectionContext v) { setField(4, v); }
  @$pb.TagNumber(4)
  $core.bool hasProjectionContext() => $_has(3);
  @$pb.TagNumber(4)
  void clearProjectionContext() => clearField(4);
  @$pb.TagNumber(4)
  SubjectPhaseProjectionContext ensureProjectionContext() => $_ensure(3);

  /// What: Stable client session id.
  /// Why: Snapshots can reflect session-scoped progress/view state.
  /// How: Reuse the client session id.
  /// Example: "flutter-shell-a"
  @$pb.TagNumber(5)
  $core.String get clientSessionId => $_getSZ(4);
  @$pb.TagNumber(5)
  set clientSessionId($core.String v) { $_setString(4, v); }
  @$pb.TagNumber(5)
  $core.bool hasClientSessionId() => $_has(4);
  @$pb.TagNumber(5)
  void clearClientSessionId() => clearField(5);
}

/// What: Response containing the full workflow snapshot.
/// Why: Clients need both the snapshot and trace metadata.
/// How: Replace the locally rendered subject phase from `snapshot`.
/// Valid Example:
///   {
///     "snapshot": {"phase_view": {"phase": "research"}},
///     "trace_id": "subject-snapshot-response_599ea09b",
///     "parent_id": "subject-snapshot-request_398d3f41"
///   }
class GetSubjectWorkflowSnapshotResponse extends $pb.GeneratedMessage {
  factory GetSubjectWorkflowSnapshotResponse({
    SubjectWorkflowSnapshotView? snapshot,
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
  GetSubjectWorkflowSnapshotResponse._() : super();
  factory GetSubjectWorkflowSnapshotResponse.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory GetSubjectWorkflowSnapshotResponse.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'GetSubjectWorkflowSnapshotResponse', package: const $pb.PackageName(_omitMessageNames ? '' : 'realized.workstation.subjectworkflow.v1'), createEmptyInstance: create)
    ..aOM<SubjectWorkflowSnapshotView>(1, _omitFieldNames ? '' : 'snapshot', subBuilder: SubjectWorkflowSnapshotView.create)
    ..aOS(100, _omitFieldNames ? '' : 'traceId')
    ..aOS(101, _omitFieldNames ? '' : 'parentId')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  GetSubjectWorkflowSnapshotResponse clone() => GetSubjectWorkflowSnapshotResponse()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  GetSubjectWorkflowSnapshotResponse copyWith(void Function(GetSubjectWorkflowSnapshotResponse) updates) => super.copyWith((message) => updates(message as GetSubjectWorkflowSnapshotResponse)) as GetSubjectWorkflowSnapshotResponse;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static GetSubjectWorkflowSnapshotResponse create() => GetSubjectWorkflowSnapshotResponse._();
  GetSubjectWorkflowSnapshotResponse createEmptyInstance() => create();
  static $pb.PbList<GetSubjectWorkflowSnapshotResponse> createRepeated() => $pb.PbList<GetSubjectWorkflowSnapshotResponse>();
  @$core.pragma('dart2js:noInline')
  static GetSubjectWorkflowSnapshotResponse getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<GetSubjectWorkflowSnapshotResponse>(create);
  static GetSubjectWorkflowSnapshotResponse? _defaultInstance;

  /// What: Full subject workflow snapshot.
  /// Why: This is the main data the client requested.
  /// How: Render it as the authoritative current subject state.
  /// Example: {"phase_view":{"phase":"research"}}
  @$pb.TagNumber(1)
  SubjectWorkflowSnapshotView get snapshot => $_getN(0);
  @$pb.TagNumber(1)
  set snapshot(SubjectWorkflowSnapshotView v) { setField(1, v); }
  @$pb.TagNumber(1)
  $core.bool hasSnapshot() => $_has(0);
  @$pb.TagNumber(1)
  void clearSnapshot() => clearField(1);
  @$pb.TagNumber(1)
  SubjectWorkflowSnapshotView ensureSnapshot() => $_ensure(0);

  /// What: Trace id for the response.
  /// Why: Snapshot reads are traceable operations.
  /// How: Log it when debugging.
  /// Example: "subject-snapshot-response_599ea09b"
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
  /// Example: "subject-snapshot-request_398d3f41"
  @$pb.TagNumber(101)
  $core.String get parentId => $_getSZ(2);
  @$pb.TagNumber(101)
  set parentId($core.String v) { $_setString(2, v); }
  @$pb.TagNumber(101)
  $core.bool hasParentId() => $_has(2);
  @$pb.TagNumber(101)
  void clearParentId() => clearField(101);
}

/// What: Request to watch the full workflow snapshot for changes.
/// Why: Clients need an event-driven way to stay synchronized with subject
/// workflow changes.
/// How: Open the stream after fetching an initial snapshot. Re-render from each
/// incoming `snapshot`.
/// Valid Example:
///   {
///     "root_path": "/srv/workstations/transit",
///     "subject_id": "smart_city_travel",
///     "phase": "research",
///     "projection_context": {"can_capture_assistant": true},
///     "client_session_id": "flutter-shell-a"
///   }
class WatchSubjectWorkflowRequest extends $pb.GeneratedMessage {
  factory WatchSubjectWorkflowRequest({
    $core.String? rootPath,
    $core.String? subjectId,
    $core.String? phase,
    SubjectPhaseProjectionContext? projectionContext,
    $core.String? clientSessionId,
  }) {
    final $result = create();
    if (rootPath != null) {
      $result.rootPath = rootPath;
    }
    if (subjectId != null) {
      $result.subjectId = subjectId;
    }
    if (phase != null) {
      $result.phase = phase;
    }
    if (projectionContext != null) {
      $result.projectionContext = projectionContext;
    }
    if (clientSessionId != null) {
      $result.clientSessionId = clientSessionId;
    }
    return $result;
  }
  WatchSubjectWorkflowRequest._() : super();
  factory WatchSubjectWorkflowRequest.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory WatchSubjectWorkflowRequest.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'WatchSubjectWorkflowRequest', package: const $pb.PackageName(_omitMessageNames ? '' : 'realized.workstation.subjectworkflow.v1'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'rootPath')
    ..aOS(2, _omitFieldNames ? '' : 'subjectId')
    ..aOS(3, _omitFieldNames ? '' : 'phase')
    ..aOM<SubjectPhaseProjectionContext>(4, _omitFieldNames ? '' : 'projectionContext', subBuilder: SubjectPhaseProjectionContext.create)
    ..aOS(5, _omitFieldNames ? '' : 'clientSessionId')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  WatchSubjectWorkflowRequest clone() => WatchSubjectWorkflowRequest()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  WatchSubjectWorkflowRequest copyWith(void Function(WatchSubjectWorkflowRequest) updates) => super.copyWith((message) => updates(message as WatchSubjectWorkflowRequest)) as WatchSubjectWorkflowRequest;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static WatchSubjectWorkflowRequest create() => WatchSubjectWorkflowRequest._();
  WatchSubjectWorkflowRequest createEmptyInstance() => create();
  static $pb.PbList<WatchSubjectWorkflowRequest> createRepeated() => $pb.PbList<WatchSubjectWorkflowRequest>();
  @$core.pragma('dart2js:noInline')
  static WatchSubjectWorkflowRequest getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<WatchSubjectWorkflowRequest>(create);
  static WatchSubjectWorkflowRequest? _defaultInstance;

  /// What: Absolute workstation root path on the server.
  /// Why: Watch channels are scoped to one workstation.
  /// How: Reuse the bootstrapped root.
  /// Example: "/srv/workstations/transit"
  @$pb.TagNumber(1)
  $core.String get rootPath => $_getSZ(0);
  @$pb.TagNumber(1)
  set rootPath($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasRootPath() => $_has(0);
  @$pb.TagNumber(1)
  void clearRootPath() => clearField(1);

  /// What: Target subject id.
  /// Why: The stream watches one subject at a time.
  /// How: Use the selected subject id.
  /// Example: "smart_city_travel"
  @$pb.TagNumber(2)
  $core.String get subjectId => $_getSZ(1);
  @$pb.TagNumber(2)
  set subjectId($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasSubjectId() => $_has(1);
  @$pb.TagNumber(2)
  void clearSubjectId() => clearField(2);

  /// What: Watched phase key.
  /// Why: Different phases can project different snapshots for the same
  /// subject.
  /// How: Pass the phase the client is currently rendering.
  /// Example: "research"
  @$pb.TagNumber(3)
  $core.String get phase => $_getSZ(2);
  @$pb.TagNumber(3)
  set phase($core.String v) { $_setString(2, v); }
  @$pb.TagNumber(3)
  $core.bool hasPhase() => $_has(2);
  @$pb.TagNumber(3)
  void clearPhase() => clearField(3);

  /// What: Current client projection context.
  /// Why: Watch projections are keyed by local markdown/assistant state too.
  /// How: Pass the same context used for the initial snapshot.
  /// Example: {"can_capture_assistant": true}
  @$pb.TagNumber(4)
  SubjectPhaseProjectionContext get projectionContext => $_getN(3);
  @$pb.TagNumber(4)
  set projectionContext(SubjectPhaseProjectionContext v) { setField(4, v); }
  @$pb.TagNumber(4)
  $core.bool hasProjectionContext() => $_has(3);
  @$pb.TagNumber(4)
  void clearProjectionContext() => clearField(4);
  @$pb.TagNumber(4)
  SubjectPhaseProjectionContext ensureProjectionContext() => $_ensure(3);

  /// What: Stable client session id.
  /// Why: Watch state and progress are client-session scoped.
  /// How: Reuse the client session id.
  /// Example: "flutter-shell-a"
  @$pb.TagNumber(5)
  $core.String get clientSessionId => $_getSZ(4);
  @$pb.TagNumber(5)
  set clientSessionId($core.String v) { $_setString(4, v); }
  @$pb.TagNumber(5)
  $core.bool hasClientSessionId() => $_has(4);
  @$pb.TagNumber(5)
  void clearClientSessionId() => clearField(5);
}

/// What: One full-snapshot update emitted by `WatchSubjectWorkflow`.
/// Why: Clients need both the replacement snapshot and stream bookkeeping
/// fields.
/// How: Re-render from `snapshot`, and use `sequence`, `snapshot_version`, and
/// `progress_fingerprint` for reconciliation/debugging.
/// Valid Example:
///   {
///     "event_kind": "subject_workflow_changed",
///     "snapshot": {"phase_view": {"phase": "research"}},
///     "channel_key": "subject:smart_city_travel:research",
///     "sequence": 14,
///     "snapshot_version": "subject-research-14",
///     "progress_fingerprint": "f0c53e2295f2",
///     "trace_id": "subject-watch-event_3d31fb24",
///     "parent_id": "subject-action-response_0ed55f93"
///   }
class SubjectWorkflowSnapshotUpdate extends $pb.GeneratedMessage {
  factory SubjectWorkflowSnapshotUpdate({
    $core.String? eventKind,
    SubjectWorkflowSnapshotView? snapshot,
    $core.String? channelKey,
    $fixnum.Int64? sequence,
    $core.String? snapshotVersion,
    $core.String? progressFingerprint,
    $core.String? traceId,
    $core.String? parentId,
  }) {
    final $result = create();
    if (eventKind != null) {
      $result.eventKind = eventKind;
    }
    if (snapshot != null) {
      $result.snapshot = snapshot;
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
    if (traceId != null) {
      $result.traceId = traceId;
    }
    if (parentId != null) {
      $result.parentId = parentId;
    }
    return $result;
  }
  SubjectWorkflowSnapshotUpdate._() : super();
  factory SubjectWorkflowSnapshotUpdate.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory SubjectWorkflowSnapshotUpdate.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'SubjectWorkflowSnapshotUpdate', package: const $pb.PackageName(_omitMessageNames ? '' : 'realized.workstation.subjectworkflow.v1'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'eventKind')
    ..aOM<SubjectWorkflowSnapshotView>(2, _omitFieldNames ? '' : 'snapshot', subBuilder: SubjectWorkflowSnapshotView.create)
    ..aOS(3, _omitFieldNames ? '' : 'channelKey')
    ..aInt64(4, _omitFieldNames ? '' : 'sequence')
    ..aOS(5, _omitFieldNames ? '' : 'snapshotVersion')
    ..aOS(6, _omitFieldNames ? '' : 'progressFingerprint')
    ..aOS(100, _omitFieldNames ? '' : 'traceId')
    ..aOS(101, _omitFieldNames ? '' : 'parentId')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  SubjectWorkflowSnapshotUpdate clone() => SubjectWorkflowSnapshotUpdate()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  SubjectWorkflowSnapshotUpdate copyWith(void Function(SubjectWorkflowSnapshotUpdate) updates) => super.copyWith((message) => updates(message as SubjectWorkflowSnapshotUpdate)) as SubjectWorkflowSnapshotUpdate;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static SubjectWorkflowSnapshotUpdate create() => SubjectWorkflowSnapshotUpdate._();
  SubjectWorkflowSnapshotUpdate createEmptyInstance() => create();
  static $pb.PbList<SubjectWorkflowSnapshotUpdate> createRepeated() => $pb.PbList<SubjectWorkflowSnapshotUpdate>();
  @$core.pragma('dart2js:noInline')
  static SubjectWorkflowSnapshotUpdate getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<SubjectWorkflowSnapshotUpdate>(create);
  static SubjectWorkflowSnapshotUpdate? _defaultInstance;

  /// What: Semantic kind of watch event.
  /// Why: Clients may want to distinguish workflow changes from progress-only
  /// refreshes.
  /// How: Treat it as an opaque event category string.
  /// Example: "subject_workflow_changed"
  @$pb.TagNumber(1)
  $core.String get eventKind => $_getSZ(0);
  @$pb.TagNumber(1)
  set eventKind($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasEventKind() => $_has(0);
  @$pb.TagNumber(1)
  void clearEventKind() => clearField(1);

  /// What: Replacement workflow snapshot.
  /// Why: The stream carries full authoritative snapshots.
  /// How: Replace local rendered state with it.
  /// Example: {"phase_view":{"phase":"research"}}
  @$pb.TagNumber(2)
  SubjectWorkflowSnapshotView get snapshot => $_getN(1);
  @$pb.TagNumber(2)
  set snapshot(SubjectWorkflowSnapshotView v) { setField(2, v); }
  @$pb.TagNumber(2)
  $core.bool hasSnapshot() => $_has(1);
  @$pb.TagNumber(2)
  void clearSnapshot() => clearField(2);
  @$pb.TagNumber(2)
  SubjectWorkflowSnapshotView ensureSnapshot() => $_ensure(1);

  /// What: Stable identifier for the watched channel.
  /// Why: Debugging and multiplexing tools need to know which channel emitted
  /// the event.
  /// How: Treat it as opaque channel metadata.
  /// Example: "subject:smart_city_travel:research"
  @$pb.TagNumber(3)
  $core.String get channelKey => $_getSZ(2);
  @$pb.TagNumber(3)
  set channelKey($core.String v) { $_setString(2, v); }
  @$pb.TagNumber(3)
  $core.bool hasChannelKey() => $_has(2);
  @$pb.TagNumber(3)
  void clearChannelKey() => clearField(3);

  /// What: Monotonic sequence number within the watched channel.
  /// Why: Clients can detect dropped or out-of-order updates.
  /// How: Expect it to increase by one for consecutive events on the same
  /// channel.
  /// Example: 14
  @$pb.TagNumber(4)
  $fixnum.Int64 get sequence => $_getI64(3);
  @$pb.TagNumber(4)
  set sequence($fixnum.Int64 v) { $_setInt64(3, v); }
  @$pb.TagNumber(4)
  $core.bool hasSequence() => $_has(3);
  @$pb.TagNumber(4)
  void clearSequence() => clearField(4);

  /// What: Snapshot version token for the emitted state.
  /// Why: Polling and streaming clients need a stable change token.
  /// How: Treat it as opaque version metadata.
  /// Example: "subject-research-14"
  @$pb.TagNumber(5)
  $core.String get snapshotVersion => $_getSZ(4);
  @$pb.TagNumber(5)
  set snapshotVersion($core.String v) { $_setString(4, v); }
  @$pb.TagNumber(5)
  $core.bool hasSnapshotVersion() => $_has(4);
  @$pb.TagNumber(5)
  void clearSnapshotVersion() => clearField(5);

  /// What: Fingerprint of the client-progress state tied to the snapshot.
  /// Why: Clients can cheaply detect whether view/progress state changed.
  /// How: Treat it as an opaque comparison fingerprint.
  /// Example: "f0c53e2295f2"
  @$pb.TagNumber(6)
  $core.String get progressFingerprint => $_getSZ(5);
  @$pb.TagNumber(6)
  set progressFingerprint($core.String v) { $_setString(5, v); }
  @$pb.TagNumber(6)
  $core.bool hasProgressFingerprint() => $_has(5);
  @$pb.TagNumber(6)
  void clearProgressFingerprint() => clearField(6);

  /// What: Trace id for this emitted event.
  /// Why: Stream events participate in cross-layer traceability.
  /// How: Log it when debugging.
  /// Example: "subject-watch-event_3d31fb24"
  @$pb.TagNumber(100)
  $core.String get traceId => $_getSZ(6);
  @$pb.TagNumber(100)
  set traceId($core.String v) { $_setString(6, v); }
  @$pb.TagNumber(100)
  $core.bool hasTraceId() => $_has(6);
  @$pb.TagNumber(100)
  void clearTraceId() => clearField(100);

  /// What: Parent trace id that caused this event.
  /// Why: Diagnostics need to link the watch event to the triggering action or
  /// refresh.
  /// How: Treat it as opaque correlation metadata.
  /// Example: "subject-action-response_0ed55f93"
  @$pb.TagNumber(101)
  $core.String get parentId => $_getSZ(7);
  @$pb.TagNumber(101)
  set parentId($core.String v) { $_setString(7, v); }
  @$pb.TagNumber(101)
  $core.bool hasParentId() => $_has(7);
  @$pb.TagNumber(101)
  void clearParentId() => clearField(101);
}

/// What: Request to apply one semantic workflow action.
/// Why: Actions mutate subject workflow state and may change the recommended
/// phase, available controls, or produced artifacts.
/// How: Provide the action key and any auxiliary import/projection context
/// needed by the action.
/// Valid Example:
///   {
///     "root_path": "/srv/workstations/transit",
///     "subject_id": "smart_city_travel",
///     "phase": "research",
///     "action_key": "approve_import",
///     "assistant_message_text": "",
///     "subject_title_override": "",
///     "import_staging": {
///       "source_subject_id": "smart_city_travel",
///       "source_subject_title": "Smart City Travel",
///       "source_subject_version_id": "subject-version-1",
///       "import_kind": "definition_support",
///       "selection_profile": "units_only"
///     },
///     "projection_context": {
///       "can_capture_assistant": true,
///       "markdown_selected_path": "/srv/workstations/transit/uploads/flutter-shell-a/city-bus.md",
///       "markdown_status_text": "Approve staged markdown import.",
///       "markdown_busy": false
///     },
///     "client_session_id": "flutter-shell-a"
///   }
class ApplySubjectActionRequest extends $pb.GeneratedMessage {
  factory ApplySubjectActionRequest({
    $core.String? rootPath,
    $core.String? subjectId,
    $core.String? phase,
    $core.String? actionKey,
    $core.String? assistantMessageText,
    $core.String? subjectTitleOverride,
    SubjectImportStaging? importStaging,
    SubjectPhaseProjectionContext? projectionContext,
    $core.String? clientSessionId,
  }) {
    final $result = create();
    if (rootPath != null) {
      $result.rootPath = rootPath;
    }
    if (subjectId != null) {
      $result.subjectId = subjectId;
    }
    if (phase != null) {
      $result.phase = phase;
    }
    if (actionKey != null) {
      $result.actionKey = actionKey;
    }
    if (assistantMessageText != null) {
      $result.assistantMessageText = assistantMessageText;
    }
    if (subjectTitleOverride != null) {
      $result.subjectTitleOverride = subjectTitleOverride;
    }
    if (importStaging != null) {
      $result.importStaging = importStaging;
    }
    if (projectionContext != null) {
      $result.projectionContext = projectionContext;
    }
    if (clientSessionId != null) {
      $result.clientSessionId = clientSessionId;
    }
    return $result;
  }
  ApplySubjectActionRequest._() : super();
  factory ApplySubjectActionRequest.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory ApplySubjectActionRequest.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'ApplySubjectActionRequest', package: const $pb.PackageName(_omitMessageNames ? '' : 'realized.workstation.subjectworkflow.v1'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'rootPath')
    ..aOS(2, _omitFieldNames ? '' : 'subjectId')
    ..aOS(3, _omitFieldNames ? '' : 'phase')
    ..aOS(4, _omitFieldNames ? '' : 'actionKey')
    ..aOS(5, _omitFieldNames ? '' : 'assistantMessageText')
    ..aOS(6, _omitFieldNames ? '' : 'subjectTitleOverride')
    ..aOM<SubjectImportStaging>(7, _omitFieldNames ? '' : 'importStaging', subBuilder: SubjectImportStaging.create)
    ..aOM<SubjectPhaseProjectionContext>(8, _omitFieldNames ? '' : 'projectionContext', subBuilder: SubjectPhaseProjectionContext.create)
    ..aOS(9, _omitFieldNames ? '' : 'clientSessionId')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  ApplySubjectActionRequest clone() => ApplySubjectActionRequest()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  ApplySubjectActionRequest copyWith(void Function(ApplySubjectActionRequest) updates) => super.copyWith((message) => updates(message as ApplySubjectActionRequest)) as ApplySubjectActionRequest;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static ApplySubjectActionRequest create() => ApplySubjectActionRequest._();
  ApplySubjectActionRequest createEmptyInstance() => create();
  static $pb.PbList<ApplySubjectActionRequest> createRepeated() => $pb.PbList<ApplySubjectActionRequest>();
  @$core.pragma('dart2js:noInline')
  static ApplySubjectActionRequest getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<ApplySubjectActionRequest>(create);
  static ApplySubjectActionRequest? _defaultInstance;

  /// What: Absolute workstation root path on the server.
  /// Why: Actions mutate state within one workstation root.
  /// How: Reuse the bootstrapped root.
  /// Example: "/srv/workstations/transit"
  @$pb.TagNumber(1)
  $core.String get rootPath => $_getSZ(0);
  @$pb.TagNumber(1)
  set rootPath($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasRootPath() => $_has(0);
  @$pb.TagNumber(1)
  void clearRootPath() => clearField(1);

  /// What: Target subject id.
  /// Why: The action applies to one subject.
  /// How: Use the currently selected subject id.
  /// Example: "smart_city_travel"
  @$pb.TagNumber(2)
  $core.String get subjectId => $_getSZ(1);
  @$pb.TagNumber(2)
  set subjectId($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasSubjectId() => $_has(1);
  @$pb.TagNumber(2)
  void clearSubjectId() => clearField(2);

  /// What: Phase from which the action was triggered.
  /// Why: Some action semantics depend on the current phase context.
  /// How: Pass the currently rendered phase key.
  /// Example: "research"
  @$pb.TagNumber(3)
  $core.String get phase => $_getSZ(2);
  @$pb.TagNumber(3)
  set phase($core.String v) { $_setString(2, v); }
  @$pb.TagNumber(3)
  $core.bool hasPhase() => $_has(2);
  @$pb.TagNumber(3)
  void clearPhase() => clearField(3);

  /// What: Canonical workflow action key.
  /// Why: The service applies actions by symbolic key.
  /// How: Use the key returned by the control/gate projection.
  /// Example: "approve_import"
  @$pb.TagNumber(4)
  $core.String get actionKey => $_getSZ(3);
  @$pb.TagNumber(4)
  set actionKey($core.String v) { $_setString(3, v); }
  @$pb.TagNumber(4)
  $core.bool hasActionKey() => $_has(3);
  @$pb.TagNumber(4)
  void clearActionKey() => clearField(4);

  /// What: Assistant text to capture for actions that consume assistant output.
  /// Why: Some phase actions incorporate generated assistant text into the
  /// workflow.
  /// How: Supply it only when the chosen action expects it.
  /// Example: ""
  @$pb.TagNumber(5)
  $core.String get assistantMessageText => $_getSZ(4);
  @$pb.TagNumber(5)
  set assistantMessageText($core.String v) { $_setString(4, v); }
  @$pb.TagNumber(5)
  $core.bool hasAssistantMessageText() => $_has(4);
  @$pb.TagNumber(5)
  void clearAssistantMessageText() => clearField(5);

  /// What: Optional subject-title override provided by the client.
  /// Why: Some creation/import flows let the user propose a subject title.
  /// How: Leave empty unless the action requires it.
  /// Example: ""
  @$pb.TagNumber(6)
  $core.String get subjectTitleOverride => $_getSZ(5);
  @$pb.TagNumber(6)
  set subjectTitleOverride($core.String v) { $_setString(5, v); }
  @$pb.TagNumber(6)
  $core.bool hasSubjectTitleOverride() => $_has(5);
  @$pb.TagNumber(6)
  void clearSubjectTitleOverride() => clearField(6);

  /// What: Optional staged-import metadata for import actions.
  /// Why: Import approval often needs more context than just an action key.
  /// How: Supply it for import actions, otherwise leave it unset/default.
  /// Example: {"source_subject_id":"smart_city_travel"}
  @$pb.TagNumber(7)
  SubjectImportStaging get importStaging => $_getN(6);
  @$pb.TagNumber(7)
  set importStaging(SubjectImportStaging v) { setField(7, v); }
  @$pb.TagNumber(7)
  $core.bool hasImportStaging() => $_has(6);
  @$pb.TagNumber(7)
  void clearImportStaging() => clearField(7);
  @$pb.TagNumber(7)
  SubjectImportStaging ensureImportStaging() => $_ensure(6);

  /// What: Current client projection context.
  /// Why: Actions can depend on staged markdown paths and assistant-capture
  /// availability.
  /// How: Pass the same context the client used for the current snapshot.
  /// Example: {"can_capture_assistant":true}
  @$pb.TagNumber(8)
  SubjectPhaseProjectionContext get projectionContext => $_getN(7);
  @$pb.TagNumber(8)
  set projectionContext(SubjectPhaseProjectionContext v) { setField(8, v); }
  @$pb.TagNumber(8)
  $core.bool hasProjectionContext() => $_has(7);
  @$pb.TagNumber(8)
  void clearProjectionContext() => clearField(8);
  @$pb.TagNumber(8)
  SubjectPhaseProjectionContext ensureProjectionContext() => $_ensure(7);

  /// What: Stable client session id.
  /// Why: Actions can mutate or consult client-scoped progress/view state.
  /// How: Reuse the client session id.
  /// Example: "flutter-shell-a"
  @$pb.TagNumber(9)
  $core.String get clientSessionId => $_getSZ(8);
  @$pb.TagNumber(9)
  set clientSessionId($core.String v) { $_setString(8, v); }
  @$pb.TagNumber(9)
  $core.bool hasClientSessionId() => $_has(8);
  @$pb.TagNumber(9)
  void clearClientSessionId() => clearField(9);
}

/// What: Response returned after one workflow action is applied.
/// Why: Clients need both the action outcome and the fresh phase projection.
/// How: Render the receipt from `result`, then update the phase from `view`.
/// Valid Example:
///   {
///     "result": {"status_text": "Import approved."},
///     "view": {"phase": "research", "preferred_phase": "itemize"},
///     "trace_id": "subject-action-response_0ed55f93",
///     "parent_id": "subject-action-request_5668713e"
///   }
class ApplySubjectActionResponse extends $pb.GeneratedMessage {
  factory ApplySubjectActionResponse({
    SubjectActionResult? result,
    SubjectPhaseView? view,
    $core.String? traceId,
    $core.String? parentId,
  }) {
    final $result = create();
    if (result != null) {
      $result.result = result;
    }
    if (view != null) {
      $result.view = view;
    }
    if (traceId != null) {
      $result.traceId = traceId;
    }
    if (parentId != null) {
      $result.parentId = parentId;
    }
    return $result;
  }
  ApplySubjectActionResponse._() : super();
  factory ApplySubjectActionResponse.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory ApplySubjectActionResponse.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'ApplySubjectActionResponse', package: const $pb.PackageName(_omitMessageNames ? '' : 'realized.workstation.subjectworkflow.v1'), createEmptyInstance: create)
    ..aOM<SubjectActionResult>(1, _omitFieldNames ? '' : 'result', subBuilder: SubjectActionResult.create)
    ..aOM<SubjectPhaseView>(2, _omitFieldNames ? '' : 'view', subBuilder: SubjectPhaseView.create)
    ..aOS(100, _omitFieldNames ? '' : 'traceId')
    ..aOS(101, _omitFieldNames ? '' : 'parentId')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  ApplySubjectActionResponse clone() => ApplySubjectActionResponse()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  ApplySubjectActionResponse copyWith(void Function(ApplySubjectActionResponse) updates) => super.copyWith((message) => updates(message as ApplySubjectActionResponse)) as ApplySubjectActionResponse;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static ApplySubjectActionResponse create() => ApplySubjectActionResponse._();
  ApplySubjectActionResponse createEmptyInstance() => create();
  static $pb.PbList<ApplySubjectActionResponse> createRepeated() => $pb.PbList<ApplySubjectActionResponse>();
  @$core.pragma('dart2js:noInline')
  static ApplySubjectActionResponse getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<ApplySubjectActionResponse>(create);
  static ApplySubjectActionResponse? _defaultInstance;

  /// What: Action outcome/receipt.
  /// Why: The caller needs explicit semantic feedback about the action.
  /// How: Use it for receipts, routing hints, reload hints, and artifacts.
  /// Example: {"status_text":"Import approved."}
  @$pb.TagNumber(1)
  SubjectActionResult get result => $_getN(0);
  @$pb.TagNumber(1)
  set result(SubjectActionResult v) { setField(1, v); }
  @$pb.TagNumber(1)
  $core.bool hasResult() => $_has(0);
  @$pb.TagNumber(1)
  void clearResult() => clearField(1);
  @$pb.TagNumber(1)
  SubjectActionResult ensureResult() => $_ensure(0);

  /// What: Fresh phase projection after applying the action.
  /// Why: The UI should render updated workflow state immediately.
  /// How: Replace the rendered phase from this message.
  /// Example: {"phase":"research","preferred_phase":"itemize"}
  @$pb.TagNumber(2)
  SubjectPhaseView get view => $_getN(1);
  @$pb.TagNumber(2)
  set view(SubjectPhaseView v) { setField(2, v); }
  @$pb.TagNumber(2)
  $core.bool hasView() => $_has(1);
  @$pb.TagNumber(2)
  void clearView() => clearField(2);
  @$pb.TagNumber(2)
  SubjectPhaseView ensureView() => $_ensure(1);

  /// What: Trace id for the response.
  /// Why: Action application is a traceable mutating operation.
  /// How: Log it when debugging.
  /// Example: "subject-action-response_0ed55f93"
  @$pb.TagNumber(100)
  $core.String get traceId => $_getSZ(2);
  @$pb.TagNumber(100)
  set traceId($core.String v) { $_setString(2, v); }
  @$pb.TagNumber(100)
  $core.bool hasTraceId() => $_has(2);
  @$pb.TagNumber(100)
  void clearTraceId() => clearField(100);

  /// What: Parent trace id linking back to the request.
  /// Why: Diagnostics need causal linkage.
  /// How: Treat it as opaque correlation metadata.
  /// Example: "subject-action-request_5668713e"
  @$pb.TagNumber(101)
  $core.String get parentId => $_getSZ(3);
  @$pb.TagNumber(101)
  set parentId($core.String v) { $_setString(3, v); }
  @$pb.TagNumber(101)
  $core.bool hasParentId() => $_has(3);
  @$pb.TagNumber(101)
  void clearParentId() => clearField(101);
}

/// What: Request for client-scoped subject progress JSON.
/// Why: The workflow keeps some view/progress state isolated per client
/// session.
/// How: Supply the current root, subject, and client session id.
/// Valid Example:
///   {
///     "root_path": "/srv/workstations/transit",
///     "subject_id": "smart_city_travel",
///     "client_session_id": "flutter-shell-a"
///   }
class GetClientSubjectProgressRequest extends $pb.GeneratedMessage {
  factory GetClientSubjectProgressRequest({
    $core.String? rootPath,
    $core.String? subjectId,
    $core.String? clientSessionId,
  }) {
    final $result = create();
    if (rootPath != null) {
      $result.rootPath = rootPath;
    }
    if (subjectId != null) {
      $result.subjectId = subjectId;
    }
    if (clientSessionId != null) {
      $result.clientSessionId = clientSessionId;
    }
    return $result;
  }
  GetClientSubjectProgressRequest._() : super();
  factory GetClientSubjectProgressRequest.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory GetClientSubjectProgressRequest.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'GetClientSubjectProgressRequest', package: const $pb.PackageName(_omitMessageNames ? '' : 'realized.workstation.subjectworkflow.v1'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'rootPath')
    ..aOS(2, _omitFieldNames ? '' : 'subjectId')
    ..aOS(3, _omitFieldNames ? '' : 'clientSessionId')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  GetClientSubjectProgressRequest clone() => GetClientSubjectProgressRequest()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  GetClientSubjectProgressRequest copyWith(void Function(GetClientSubjectProgressRequest) updates) => super.copyWith((message) => updates(message as GetClientSubjectProgressRequest)) as GetClientSubjectProgressRequest;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static GetClientSubjectProgressRequest create() => GetClientSubjectProgressRequest._();
  GetClientSubjectProgressRequest createEmptyInstance() => create();
  static $pb.PbList<GetClientSubjectProgressRequest> createRepeated() => $pb.PbList<GetClientSubjectProgressRequest>();
  @$core.pragma('dart2js:noInline')
  static GetClientSubjectProgressRequest getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<GetClientSubjectProgressRequest>(create);
  static GetClientSubjectProgressRequest? _defaultInstance;

  /// What: Absolute workstation root path on the server.
  /// Why: Progress is scoped to one workstation.
  /// How: Reuse the bootstrapped root.
  /// Example: "/srv/workstations/transit"
  @$pb.TagNumber(1)
  $core.String get rootPath => $_getSZ(0);
  @$pb.TagNumber(1)
  set rootPath($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasRootPath() => $_has(0);
  @$pb.TagNumber(1)
  void clearRootPath() => clearField(1);

  /// What: Target subject id.
  /// Why: Progress is tracked per subject.
  /// How: Use the selected subject id.
  /// Example: "smart_city_travel"
  @$pb.TagNumber(2)
  $core.String get subjectId => $_getSZ(1);
  @$pb.TagNumber(2)
  set subjectId($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasSubjectId() => $_has(1);
  @$pb.TagNumber(2)
  void clearSubjectId() => clearField(2);

  /// What: Stable client session id.
  /// Why: Progress is isolated per client session.
  /// How: Reuse the client session id.
  /// Example: "flutter-shell-a"
  @$pb.TagNumber(3)
  $core.String get clientSessionId => $_getSZ(2);
  @$pb.TagNumber(3)
  set clientSessionId($core.String v) { $_setString(2, v); }
  @$pb.TagNumber(3)
  $core.bool hasClientSessionId() => $_has(2);
  @$pb.TagNumber(3)
  void clearClientSessionId() => clearField(3);
}

/// What: Response containing client-scoped subject progress JSON.
/// Why: The client may need to restore ephemeral view state after reconnecting.
/// How: Treat `progress_json` as opaque JSON owned by the service.
/// Valid Example:
///   {
///     "progress_json": "{\"selectedImportId\":\"import_1\"}",
///     "trace_id": "subject-progress-response_6dfcf8f0",
///     "parent_id": "subject-progress-request_a4e93f2d"
///   }
class GetClientSubjectProgressResponse extends $pb.GeneratedMessage {
  factory GetClientSubjectProgressResponse({
    $core.String? progressJson,
    $core.String? traceId,
    $core.String? parentId,
  }) {
    final $result = create();
    if (progressJson != null) {
      $result.progressJson = progressJson;
    }
    if (traceId != null) {
      $result.traceId = traceId;
    }
    if (parentId != null) {
      $result.parentId = parentId;
    }
    return $result;
  }
  GetClientSubjectProgressResponse._() : super();
  factory GetClientSubjectProgressResponse.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory GetClientSubjectProgressResponse.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'GetClientSubjectProgressResponse', package: const $pb.PackageName(_omitMessageNames ? '' : 'realized.workstation.subjectworkflow.v1'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'progressJson')
    ..aOS(100, _omitFieldNames ? '' : 'traceId')
    ..aOS(101, _omitFieldNames ? '' : 'parentId')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  GetClientSubjectProgressResponse clone() => GetClientSubjectProgressResponse()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  GetClientSubjectProgressResponse copyWith(void Function(GetClientSubjectProgressResponse) updates) => super.copyWith((message) => updates(message as GetClientSubjectProgressResponse)) as GetClientSubjectProgressResponse;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static GetClientSubjectProgressResponse create() => GetClientSubjectProgressResponse._();
  GetClientSubjectProgressResponse createEmptyInstance() => create();
  static $pb.PbList<GetClientSubjectProgressResponse> createRepeated() => $pb.PbList<GetClientSubjectProgressResponse>();
  @$core.pragma('dart2js:noInline')
  static GetClientSubjectProgressResponse getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<GetClientSubjectProgressResponse>(create);
  static GetClientSubjectProgressResponse? _defaultInstance;

  /// What: Opaque client-scoped subject progress JSON.
  /// Why: The service owns the exact progress schema.
  /// How: Store and send it back unchanged unless you understand the schema.
  /// Example: "{\"selectedImportId\":\"import_1\"}"
  @$pb.TagNumber(1)
  $core.String get progressJson => $_getSZ(0);
  @$pb.TagNumber(1)
  set progressJson($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasProgressJson() => $_has(0);
  @$pb.TagNumber(1)
  void clearProgressJson() => clearField(1);

  /// What: Trace id for the response.
  /// Why: Progress reads are traceable operations.
  /// How: Log it when debugging.
  /// Example: "subject-progress-response_6dfcf8f0"
  @$pb.TagNumber(100)
  $core.String get traceId => $_getSZ(1);
  @$pb.TagNumber(100)
  set traceId($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(100)
  $core.bool hasTraceId() => $_has(1);
  @$pb.TagNumber(100)
  void clearTraceId() => clearField(100);

  /// What: Parent trace id linking back to the request.
  /// Why: Diagnostics need request/response correlation.
  /// How: Treat it as opaque metadata.
  /// Example: "subject-progress-request_a4e93f2d"
  @$pb.TagNumber(101)
  $core.String get parentId => $_getSZ(2);
  @$pb.TagNumber(101)
  set parentId($core.String v) { $_setString(2, v); }
  @$pb.TagNumber(101)
  $core.bool hasParentId() => $_has(2);
  @$pb.TagNumber(101)
  void clearParentId() => clearField(101);
}

/// What: Request to persist client-scoped subject progress JSON.
/// Why: The client needs to write isolated ephemeral view/progress state.
/// How: Supply the same targeting fields and the opaque JSON payload.
/// Valid Example:
///   {
///     "root_path": "/srv/workstations/transit",
///     "subject_id": "smart_city_travel",
///     "client_session_id": "flutter-shell-a",
///     "progress_json": "{\"selectedImportId\":\"import_1\"}"
///   }
class PutClientSubjectProgressRequest extends $pb.GeneratedMessage {
  factory PutClientSubjectProgressRequest({
    $core.String? rootPath,
    $core.String? subjectId,
    $core.String? clientSessionId,
    $core.String? progressJson,
  }) {
    final $result = create();
    if (rootPath != null) {
      $result.rootPath = rootPath;
    }
    if (subjectId != null) {
      $result.subjectId = subjectId;
    }
    if (clientSessionId != null) {
      $result.clientSessionId = clientSessionId;
    }
    if (progressJson != null) {
      $result.progressJson = progressJson;
    }
    return $result;
  }
  PutClientSubjectProgressRequest._() : super();
  factory PutClientSubjectProgressRequest.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory PutClientSubjectProgressRequest.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'PutClientSubjectProgressRequest', package: const $pb.PackageName(_omitMessageNames ? '' : 'realized.workstation.subjectworkflow.v1'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'rootPath')
    ..aOS(2, _omitFieldNames ? '' : 'subjectId')
    ..aOS(3, _omitFieldNames ? '' : 'clientSessionId')
    ..aOS(4, _omitFieldNames ? '' : 'progressJson')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  PutClientSubjectProgressRequest clone() => PutClientSubjectProgressRequest()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  PutClientSubjectProgressRequest copyWith(void Function(PutClientSubjectProgressRequest) updates) => super.copyWith((message) => updates(message as PutClientSubjectProgressRequest)) as PutClientSubjectProgressRequest;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static PutClientSubjectProgressRequest create() => PutClientSubjectProgressRequest._();
  PutClientSubjectProgressRequest createEmptyInstance() => create();
  static $pb.PbList<PutClientSubjectProgressRequest> createRepeated() => $pb.PbList<PutClientSubjectProgressRequest>();
  @$core.pragma('dart2js:noInline')
  static PutClientSubjectProgressRequest getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<PutClientSubjectProgressRequest>(create);
  static PutClientSubjectProgressRequest? _defaultInstance;

  /// What: Absolute workstation root path on the server.
  /// Why: Progress writes are scoped to one workstation.
  /// How: Reuse the bootstrapped root.
  /// Example: "/srv/workstations/transit"
  @$pb.TagNumber(1)
  $core.String get rootPath => $_getSZ(0);
  @$pb.TagNumber(1)
  set rootPath($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasRootPath() => $_has(0);
  @$pb.TagNumber(1)
  void clearRootPath() => clearField(1);

  /// What: Target subject id.
  /// Why: Progress is stored per subject.
  /// How: Use the selected subject id.
  /// Example: "smart_city_travel"
  @$pb.TagNumber(2)
  $core.String get subjectId => $_getSZ(1);
  @$pb.TagNumber(2)
  set subjectId($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasSubjectId() => $_has(1);
  @$pb.TagNumber(2)
  void clearSubjectId() => clearField(2);

  /// What: Stable client session id.
  /// Why: Progress is isolated per client session.
  /// How: Reuse the client session id.
  /// Example: "flutter-shell-a"
  @$pb.TagNumber(3)
  $core.String get clientSessionId => $_getSZ(2);
  @$pb.TagNumber(3)
  set clientSessionId($core.String v) { $_setString(2, v); }
  @$pb.TagNumber(3)
  $core.bool hasClientSessionId() => $_has(2);
  @$pb.TagNumber(3)
  void clearClientSessionId() => clearField(3);

  /// What: Opaque client-scoped progress JSON payload.
  /// Why: The service persists client-local workflow/view state in one blob.
  /// How: Write back the progress JSON previously read or locally updated.
  /// Example: "{\"selectedImportId\":\"import_1\"}"
  @$pb.TagNumber(4)
  $core.String get progressJson => $_getSZ(3);
  @$pb.TagNumber(4)
  set progressJson($core.String v) { $_setString(3, v); }
  @$pb.TagNumber(4)
  $core.bool hasProgressJson() => $_has(3);
  @$pb.TagNumber(4)
  void clearProgressJson() => clearField(4);
}

/// What: Response returned after writing client-scoped subject progress JSON.
/// Why: Clients need the normalized stored JSON plus trace metadata.
/// How: Replace local cached progress with the returned payload.
/// Valid Example:
///   {
///     "progress_json": "{\"selectedImportId\":\"import_1\"}",
///     "trace_id": "subject-progress-put-response_1be2d86f",
///     "parent_id": "subject-progress-put-request_d275f620"
///   }
class PutClientSubjectProgressResponse extends $pb.GeneratedMessage {
  factory PutClientSubjectProgressResponse({
    $core.String? progressJson,
    $core.String? traceId,
    $core.String? parentId,
  }) {
    final $result = create();
    if (progressJson != null) {
      $result.progressJson = progressJson;
    }
    if (traceId != null) {
      $result.traceId = traceId;
    }
    if (parentId != null) {
      $result.parentId = parentId;
    }
    return $result;
  }
  PutClientSubjectProgressResponse._() : super();
  factory PutClientSubjectProgressResponse.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory PutClientSubjectProgressResponse.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'PutClientSubjectProgressResponse', package: const $pb.PackageName(_omitMessageNames ? '' : 'realized.workstation.subjectworkflow.v1'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'progressJson')
    ..aOS(100, _omitFieldNames ? '' : 'traceId')
    ..aOS(101, _omitFieldNames ? '' : 'parentId')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  PutClientSubjectProgressResponse clone() => PutClientSubjectProgressResponse()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  PutClientSubjectProgressResponse copyWith(void Function(PutClientSubjectProgressResponse) updates) => super.copyWith((message) => updates(message as PutClientSubjectProgressResponse)) as PutClientSubjectProgressResponse;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static PutClientSubjectProgressResponse create() => PutClientSubjectProgressResponse._();
  PutClientSubjectProgressResponse createEmptyInstance() => create();
  static $pb.PbList<PutClientSubjectProgressResponse> createRepeated() => $pb.PbList<PutClientSubjectProgressResponse>();
  @$core.pragma('dart2js:noInline')
  static PutClientSubjectProgressResponse getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<PutClientSubjectProgressResponse>(create);
  static PutClientSubjectProgressResponse? _defaultInstance;

  /// What: Normalized stored progress JSON.
  /// Why: The server may normalize the payload before persisting it.
  /// How: Replace local cached progress with the returned text.
  /// Example: "{\"selectedImportId\":\"import_1\"}"
  @$pb.TagNumber(1)
  $core.String get progressJson => $_getSZ(0);
  @$pb.TagNumber(1)
  set progressJson($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasProgressJson() => $_has(0);
  @$pb.TagNumber(1)
  void clearProgressJson() => clearField(1);

  /// What: Trace id for the response.
  /// Why: Progress writes are traceable operations.
  /// How: Log it when debugging.
  /// Example: "subject-progress-put-response_1be2d86f"
  @$pb.TagNumber(100)
  $core.String get traceId => $_getSZ(1);
  @$pb.TagNumber(100)
  set traceId($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(100)
  $core.bool hasTraceId() => $_has(1);
  @$pb.TagNumber(100)
  void clearTraceId() => clearField(100);

  /// What: Parent trace id linking back to the write request.
  /// Why: Diagnostics need causal linkage.
  /// How: Treat it as opaque metadata.
  /// Example: "subject-progress-put-request_d275f620"
  @$pb.TagNumber(101)
  $core.String get parentId => $_getSZ(2);
  @$pb.TagNumber(101)
  set parentId($core.String v) { $_setString(2, v); }
  @$pb.TagNumber(101)
  $core.bool hasParentId() => $_has(2);
  @$pb.TagNumber(101)
  void clearParentId() => clearField(101);
}

/// What: Request to apply one lightweight client interaction to the current
/// subject workflow.
/// Why: Some client interactions mutate progress/view state without being full
/// semantic subject actions.
/// How: Supply the interaction key, delta/target information, and current
/// projection context.
/// Valid Example:
///   {
///     "root_path": "/srv/workstations/transit",
///     "subject_id": "smart_city_travel",
///     "phase": "review",
///     "client_session_id": "flutter-shell-a",
///     "interaction_key": "report_scope_select",
///     "delta": 1,
///     "target_id": "section_02",
///     "preview_only": false,
///     "projection_context": {"can_capture_assistant": true}
///   }
class ApplySubjectInteractionRequest extends $pb.GeneratedMessage {
  factory ApplySubjectInteractionRequest({
    $core.String? rootPath,
    $core.String? subjectId,
    $core.String? phase,
    $core.String? clientSessionId,
    $core.String? interactionKey,
    $core.int? delta,
    $core.String? targetId,
    $core.bool? previewOnly,
    SubjectPhaseProjectionContext? projectionContext,
  }) {
    final $result = create();
    if (rootPath != null) {
      $result.rootPath = rootPath;
    }
    if (subjectId != null) {
      $result.subjectId = subjectId;
    }
    if (phase != null) {
      $result.phase = phase;
    }
    if (clientSessionId != null) {
      $result.clientSessionId = clientSessionId;
    }
    if (interactionKey != null) {
      $result.interactionKey = interactionKey;
    }
    if (delta != null) {
      $result.delta = delta;
    }
    if (targetId != null) {
      $result.targetId = targetId;
    }
    if (previewOnly != null) {
      $result.previewOnly = previewOnly;
    }
    if (projectionContext != null) {
      $result.projectionContext = projectionContext;
    }
    return $result;
  }
  ApplySubjectInteractionRequest._() : super();
  factory ApplySubjectInteractionRequest.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory ApplySubjectInteractionRequest.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'ApplySubjectInteractionRequest', package: const $pb.PackageName(_omitMessageNames ? '' : 'realized.workstation.subjectworkflow.v1'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'rootPath')
    ..aOS(2, _omitFieldNames ? '' : 'subjectId')
    ..aOS(3, _omitFieldNames ? '' : 'phase')
    ..aOS(4, _omitFieldNames ? '' : 'clientSessionId')
    ..aOS(5, _omitFieldNames ? '' : 'interactionKey')
    ..a<$core.int>(6, _omitFieldNames ? '' : 'delta', $pb.PbFieldType.O3)
    ..aOS(7, _omitFieldNames ? '' : 'targetId')
    ..aOB(8, _omitFieldNames ? '' : 'previewOnly')
    ..aOM<SubjectPhaseProjectionContext>(9, _omitFieldNames ? '' : 'projectionContext', subBuilder: SubjectPhaseProjectionContext.create)
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  ApplySubjectInteractionRequest clone() => ApplySubjectInteractionRequest()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  ApplySubjectInteractionRequest copyWith(void Function(ApplySubjectInteractionRequest) updates) => super.copyWith((message) => updates(message as ApplySubjectInteractionRequest)) as ApplySubjectInteractionRequest;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static ApplySubjectInteractionRequest create() => ApplySubjectInteractionRequest._();
  ApplySubjectInteractionRequest createEmptyInstance() => create();
  static $pb.PbList<ApplySubjectInteractionRequest> createRepeated() => $pb.PbList<ApplySubjectInteractionRequest>();
  @$core.pragma('dart2js:noInline')
  static ApplySubjectInteractionRequest getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<ApplySubjectInteractionRequest>(create);
  static ApplySubjectInteractionRequest? _defaultInstance;

  /// What: Absolute workstation root path on the server.
  /// Why: Interaction updates are scoped to one workstation.
  /// How: Reuse the bootstrapped root.
  /// Example: "/srv/workstations/transit"
  @$pb.TagNumber(1)
  $core.String get rootPath => $_getSZ(0);
  @$pb.TagNumber(1)
  set rootPath($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasRootPath() => $_has(0);
  @$pb.TagNumber(1)
  void clearRootPath() => clearField(1);

  /// What: Target subject id.
  /// Why: Interactions apply to one subject.
  /// How: Use the selected subject id.
  /// Example: "smart_city_travel"
  @$pb.TagNumber(2)
  $core.String get subjectId => $_getSZ(1);
  @$pb.TagNumber(2)
  set subjectId($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasSubjectId() => $_has(1);
  @$pb.TagNumber(2)
  void clearSubjectId() => clearField(2);

  /// What: Phase from which the interaction originated.
  /// Why: Interaction meaning can depend on phase-local controls.
  /// How: Pass the active phase key.
  /// Example: "review"
  @$pb.TagNumber(3)
  $core.String get phase => $_getSZ(2);
  @$pb.TagNumber(3)
  set phase($core.String v) { $_setString(2, v); }
  @$pb.TagNumber(3)
  $core.bool hasPhase() => $_has(2);
  @$pb.TagNumber(3)
  void clearPhase() => clearField(3);

  /// What: Stable client session id.
  /// Why: Interaction state is client-session scoped.
  /// How: Reuse the client session id.
  /// Example: "flutter-shell-a"
  @$pb.TagNumber(4)
  $core.String get clientSessionId => $_getSZ(3);
  @$pb.TagNumber(4)
  set clientSessionId($core.String v) { $_setString(3, v); }
  @$pb.TagNumber(4)
  $core.bool hasClientSessionId() => $_has(3);
  @$pb.TagNumber(4)
  void clearClientSessionId() => clearField(4);

  /// What: Canonical interaction key.
  /// Why: The service applies lightweight interactions by symbolic key.
  /// How: Use the interaction key defined by the UI contract.
  /// Example: "report_scope_select"
  @$pb.TagNumber(5)
  $core.String get interactionKey => $_getSZ(4);
  @$pb.TagNumber(5)
  set interactionKey($core.String v) { $_setString(4, v); }
  @$pb.TagNumber(5)
  $core.bool hasInteractionKey() => $_has(4);
  @$pb.TagNumber(5)
  void clearInteractionKey() => clearField(5);

  /// What: Integer delta associated with the interaction.
  /// Why: Some interactions increment/decrement or otherwise carry a signed
  /// step.
  /// How: Supply 0 when the interaction does not use a delta.
  /// Example: 1
  @$pb.TagNumber(6)
  $core.int get delta => $_getIZ(5);
  @$pb.TagNumber(6)
  set delta($core.int v) { $_setSignedInt32(5, v); }
  @$pb.TagNumber(6)
  $core.bool hasDelta() => $_has(5);
  @$pb.TagNumber(6)
  void clearDelta() => clearField(6);

  /// What: Target id associated with the interaction.
  /// Why: Interactions often operate on one selected row/item/section.
  /// How: Supply the stable target id when required.
  /// Example: "section_02"
  @$pb.TagNumber(7)
  $core.String get targetId => $_getSZ(6);
  @$pb.TagNumber(7)
  set targetId($core.String v) { $_setString(6, v); }
  @$pb.TagNumber(7)
  $core.bool hasTargetId() => $_has(6);
  @$pb.TagNumber(7)
  void clearTargetId() => clearField(7);

  /// What: Whether to compute a preview without committing the interaction.
  /// Why: Some clients want to inspect a hypothetical result first.
  /// How: Set true for preview-only interactions.
  /// Example: false
  @$pb.TagNumber(8)
  $core.bool get previewOnly => $_getBF(7);
  @$pb.TagNumber(8)
  set previewOnly($core.bool v) { $_setBool(7, v); }
  @$pb.TagNumber(8)
  $core.bool hasPreviewOnly() => $_has(7);
  @$pb.TagNumber(8)
  void clearPreviewOnly() => clearField(8);

  /// What: Current client projection context.
  /// Why: Interaction projections can still depend on markdown/assistant state.
  /// How: Pass the same context used by the current snapshot.
  /// Example: {"can_capture_assistant": true}
  @$pb.TagNumber(9)
  SubjectPhaseProjectionContext get projectionContext => $_getN(8);
  @$pb.TagNumber(9)
  set projectionContext(SubjectPhaseProjectionContext v) { setField(9, v); }
  @$pb.TagNumber(9)
  $core.bool hasProjectionContext() => $_has(8);
  @$pb.TagNumber(9)
  void clearProjectionContext() => clearField(9);
  @$pb.TagNumber(9)
  SubjectPhaseProjectionContext ensureProjectionContext() => $_ensure(8);
}

/// What: Response returned after applying a lightweight client interaction.
/// Why: The client needs the refreshed snapshot and normalized progress state.
/// How: Replace the rendered snapshot and local cached progress with the
/// returned values.
/// Valid Example:
///   {
///     "snapshot": {"phase_view": {"phase": "review"}},
///     "progress_json": "{\"selectedSectionId\":\"section_02\"}",
///     "progress_fingerprint": "38b62d00aefe",
///     "trace_id": "subject-interaction-response_4ec1eb3a",
///     "parent_id": "subject-interaction-request_5e47cfda"
///   }
class ApplySubjectInteractionResponse extends $pb.GeneratedMessage {
  factory ApplySubjectInteractionResponse({
    SubjectWorkflowSnapshotView? snapshot,
    $core.String? progressJson,
    $core.String? progressFingerprint,
    $core.String? traceId,
    $core.String? parentId,
  }) {
    final $result = create();
    if (snapshot != null) {
      $result.snapshot = snapshot;
    }
    if (progressJson != null) {
      $result.progressJson = progressJson;
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
  ApplySubjectInteractionResponse._() : super();
  factory ApplySubjectInteractionResponse.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory ApplySubjectInteractionResponse.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'ApplySubjectInteractionResponse', package: const $pb.PackageName(_omitMessageNames ? '' : 'realized.workstation.subjectworkflow.v1'), createEmptyInstance: create)
    ..aOM<SubjectWorkflowSnapshotView>(1, _omitFieldNames ? '' : 'snapshot', subBuilder: SubjectWorkflowSnapshotView.create)
    ..aOS(2, _omitFieldNames ? '' : 'progressJson')
    ..aOS(3, _omitFieldNames ? '' : 'progressFingerprint')
    ..aOS(100, _omitFieldNames ? '' : 'traceId')
    ..aOS(101, _omitFieldNames ? '' : 'parentId')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  ApplySubjectInteractionResponse clone() => ApplySubjectInteractionResponse()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  ApplySubjectInteractionResponse copyWith(void Function(ApplySubjectInteractionResponse) updates) => super.copyWith((message) => updates(message as ApplySubjectInteractionResponse)) as ApplySubjectInteractionResponse;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static ApplySubjectInteractionResponse create() => ApplySubjectInteractionResponse._();
  ApplySubjectInteractionResponse createEmptyInstance() => create();
  static $pb.PbList<ApplySubjectInteractionResponse> createRepeated() => $pb.PbList<ApplySubjectInteractionResponse>();
  @$core.pragma('dart2js:noInline')
  static ApplySubjectInteractionResponse getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<ApplySubjectInteractionResponse>(create);
  static ApplySubjectInteractionResponse? _defaultInstance;

  /// What: Refreshed workflow snapshot after the interaction.
  /// Why: The client should re-render from authoritative service state.
  /// How: Replace local rendered state with this snapshot.
  /// Example: {"phase_view":{"phase":"review"}}
  @$pb.TagNumber(1)
  SubjectWorkflowSnapshotView get snapshot => $_getN(0);
  @$pb.TagNumber(1)
  set snapshot(SubjectWorkflowSnapshotView v) { setField(1, v); }
  @$pb.TagNumber(1)
  $core.bool hasSnapshot() => $_has(0);
  @$pb.TagNumber(1)
  void clearSnapshot() => clearField(1);
  @$pb.TagNumber(1)
  SubjectWorkflowSnapshotView ensureSnapshot() => $_ensure(0);

  /// What: Normalized client progress JSON after the interaction.
  /// Why: The service may mutate stored client progress while handling the
  /// interaction.
  /// How: Replace the local cached progress with it.
  /// Example: "{\"selectedSectionId\":\"section_02\"}"
  @$pb.TagNumber(2)
  $core.String get progressJson => $_getSZ(1);
  @$pb.TagNumber(2)
  set progressJson($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasProgressJson() => $_has(1);
  @$pb.TagNumber(2)
  void clearProgressJson() => clearField(2);

  /// What: Fingerprint of the returned progress state.
  /// Why: Clients can cheaply detect stale progress caches.
  /// How: Treat it as opaque version metadata.
  /// Example: "38b62d00aefe"
  @$pb.TagNumber(3)
  $core.String get progressFingerprint => $_getSZ(2);
  @$pb.TagNumber(3)
  set progressFingerprint($core.String v) { $_setString(2, v); }
  @$pb.TagNumber(3)
  $core.bool hasProgressFingerprint() => $_has(2);
  @$pb.TagNumber(3)
  void clearProgressFingerprint() => clearField(3);

  /// What: Trace id for the response.
  /// Why: Interaction application is a traceable operation.
  /// How: Log it when debugging.
  /// Example: "subject-interaction-response_4ec1eb3a"
  @$pb.TagNumber(100)
  $core.String get traceId => $_getSZ(3);
  @$pb.TagNumber(100)
  set traceId($core.String v) { $_setString(3, v); }
  @$pb.TagNumber(100)
  $core.bool hasTraceId() => $_has(3);
  @$pb.TagNumber(100)
  void clearTraceId() => clearField(100);

  /// What: Parent trace id linking back to the request.
  /// Why: Diagnostics need causal linkage.
  /// How: Treat it as opaque metadata.
  /// Example: "subject-interaction-request_5e47cfda"
  @$pb.TagNumber(101)
  $core.String get parentId => $_getSZ(4);
  @$pb.TagNumber(101)
  set parentId($core.String v) { $_setString(4, v); }
  @$pb.TagNumber(101)
  $core.bool hasParentId() => $_has(4);
  @$pb.TagNumber(101)
  void clearParentId() => clearField(101);
}


const _omitFieldNames = $core.bool.fromEnvironment('protobuf.omit_field_names');
const _omitMessageNames = $core.bool.fromEnvironment('protobuf.omit_message_names');
