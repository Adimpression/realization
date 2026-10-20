# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class SubjectWorkflowTab(StrEnum):
    RESEARCH = "research"
    ITEMIZE = "itemize"
    DRAFT = "draft"
    REVIEW = "review"
    PUBLICATION = "publication"


class SubjectWorkflowObject(StrEnum):
    SUBJECT_PROGRESS = "SubjectProgress"
    LEARNING_CONTEXT = "LearningContext"
    IMPORT_STAGING = "ImportStaging"
    SUBJECT_IMPORT = "SubjectImport"
    REASONING_SCOPE = "ReasoningScope"
    ITEMIZATION_SESSION = "ItemizationSession"
    ITEMIZED_SUBJECT_ITEM = "ItemizedSubjectItem"
    MAINTAINED_FILES = "MaintainedFiles"
    REVIEW_COMPOSITION = "ReviewComposition"
    REVIEW_ITEM = "ReviewItem"
    PUBLICATION_COMPOSITION = "PublicationComposition"
    PUBLICATION_BUILD = "PublicationBuild"
    RELEASE_REVIEW = "ReleaseReview"


class SubjectWorkflowStatus(StrEnum):
    OPEN = "open"
    CLOSED = "closed"
    MISSING = "missing"
    ADMITTED = "admitted"
    ACTIVE = "active"
    ABSENT = "absent"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    READY = "ready"
    CURRENT = "current"
    STALE = "stale"
    VALIDATED = "validated"
    BLOCKED = "blocked"
    CREATION_READY = "creation_ready"
    IMPORT_CREATION_AVAILABLE = "import_creation_available"
    CANDIDATE = "candidate"
    PROMOTED = "promoted"
    MERGED = "merged"
    SPLIT = "split"
    HELD = "held"
    INCLUDED = "included"
    EXCLUDED = "excluded"
    ORDERED = "ordered"
    ORIENTED = "oriented"
    LOCKED = "locked"
    UNLOCKED = "unlocked"
    FAILED = "failed"
    COMPLETE = "complete"
    SEED_ALL_NON_REJECTED = "seed_all_non_rejected"
    SEED_PROMOTED_ONLY = "seed_promoted_only"


class SubjectWorkflowJourneyStatus(StrEnum):
    GATHER_IMPORTING = "gather_importing"
    GATHER_NOT_STARTED = "gather_not_started"
    GATHER_IN_PROGRESS = "gather_in_progress"
    GATHER_READY = "gather_ready"
    ITEMIZE_WAITING_FOR_FIRST_IMPORT = "itemize_waiting_for_first_import"
    ITEMIZE_WAITING_FOR_IMPORT = "itemize_waiting_for_import"
    ITEMIZE_BLOCKED_NO_SUBJECT = "itemize_blocked_no_subject"
    ITEMIZE_BLOCKED_CONTEXT_CLOSED = "itemize_blocked_context_closed"
    ITEMIZE_IN_PROGRESS_GENERATE = "itemize_in_progress_generate"
    ITEMIZE_IN_PROGRESS_REFRESH = "itemize_in_progress_refresh"
    ITEMIZE_READY = "itemize_ready"
    SHAPE_BLOCKED_NO_SUBJECT = "shape_blocked_no_subject"
    SHAPE_BLOCKED_CONTEXT_CLOSED = "shape_blocked_context_closed"
    SHAPE_BLOCKED_ITEMIZE = "shape_blocked_itemize"
    SHAPE_IN_PROGRESS_CREATE_DRAFT = "shape_in_progress_create_draft"
    SHAPE_BLOCKED_PENDING_IMPORTS = "shape_blocked_pending_imports"
    SHAPE_BLOCKED_MAINTAINED_FILES = "shape_blocked_maintained_files"
    SHAPE_IN_PROGRESS_CREATE_REPORT_PLAN = "shape_in_progress_create_report_plan"
    SHAPE_IN_PROGRESS_HANDOFF = "shape_in_progress_handoff"
    SHAPE_READY = "shape_ready"
    RELEASE_BLOCKED_DRAFT_REVIEW = "release_blocked_draft_review"
    RELEASE_READY_TO_LOCK = "release_ready_to_lock"
    RELEASE_READY_TO_BUILD = "release_ready_to_build"
    RELEASE_BLOCKED_FIX_BUILD = "release_blocked_fix_build"
    RELEASE_BUILT_INSPECT_PACKET = "release_built_inspect_packet"
    RELEASE_BUILT_FINISH_REVIEW = "release_built_finish_review"
    RELEASE_COMPLETE = "release_complete"


class SubjectWorkflowCurrentStepState(StrEnum):
    MARKDOWN_BUSY = "markdown_busy"
    RESEARCH_PREPARE_IMPORT_SOURCE = "research_prepare_import_source"
    RESEARCH_CREATE_IMPORT_FROM_SOURCE = "research_create_import_from_source"
    CREATE_FIRST_SUBJECT = "create_first_subject"
    ACTIVATE_SUBJECT = "activate_subject"
    REVIEW_PENDING_IMPORT = "review_pending_import"
    ITEMIZE_GENERATE = "itemize_generate"
    ITEMIZE_REFRESH = "itemize_refresh"
    ITEMIZE_INSPECT = "itemize_inspect"
    ITEMIZE_ORIENT = "itemize_orient"
    DRAFT_CREATE_COMPOSITION = "draft_create_composition"
    DRAFT_REFRESH_COMPOSITION = "draft_refresh_composition"
    DRAFT_CHECK_MAINTAINED_FILES = "draft_check_maintained_files"
    DRAFT_CREATE_REPORT_PLAN = "draft_create_report_plan"
    DRAFT_APPROVED = "draft_approved"
    DRAFT_SHAPE = "draft_shape"
    REVIEW_CHECK_MAINTAINED_FILES = "review_check_maintained_files"
    REVIEW_RETURN_TO_DRAFT = "review_return_to_draft"
    REVIEW_CREATE_REPORT_PLAN = "review_create_report_plan"
    REVIEW_APPROVE_REPORT_PLAN = "review_approve_report_plan"
    PUBLICATION_LOCK_INPUTS = "publication_lock_inputs"
    PUBLICATION_BUILD_REPORT = "publication_build_report"
    PUBLICATION_FIX_BUILD = "publication_fix_build"
    PUBLICATION_INSPECT_RELEASE_FOLDER = "publication_inspect_release_folder"
    PUBLICATION_FINISH_RELEASE_REVIEW = "publication_finish_release_review"
    PUBLICATION_COMPLETE = "publication_complete"


@dataclass(frozen=True)
class SubjectWorkflowTransitionRow:
    from_tab: SubjectWorkflowTab
    from_object: SubjectWorkflowObject
    from_status: SubjectWorkflowStatus
    to_tab: SubjectWorkflowTab
    to_object: SubjectWorkflowObject
    to_status: SubjectWorkflowStatus


@dataclass(frozen=True)
class SubjectWorkflowStateInputs:
    subject_exists: bool
    context_opened: bool
    admitted_unit_count: int
    pending_import_count: int
    itemization_exists: bool
    itemization_current: bool
    itemization_valid: bool
    draft_composition_exists: bool
    draft_composition_current: bool
    maintained_files_aligned: bool
    report_plan_current: bool
    review_approved: bool
    publication_locked: bool
    publication_build_exists: bool
    publication_build_ready: bool
    release_packet_opened: bool
    release_review_completed: bool
    markdown_busy: bool = False
    markdown_source_label: str = ""


@dataclass(frozen=True)
class SubjectWorkflowCurrentStepInputs:
    phase: SubjectWorkflowTab
    subject_exists: bool
    context_opened: bool
    pending_import_count: int
    markdown_busy: bool = False
    import_staging_active: bool = False
    import_staging_on_current_subject: bool = False
    import_staging_target_ready: bool = False
    itemization_exists: bool = False
    itemization_current: bool = False
    itemization_valid: bool = False
    itemization_selected: bool = False
    draft_composition_exists: bool = False
    draft_composition_current: bool = False
    draft_shape_precedes_report_plan: bool = False
    maintained_files_aligned: bool = False
    report_plan_current: bool = False
    review_approved: bool = False
    publication_locked: bool = False
    publication_build_exists: bool = False
    publication_build_ready: bool = False
    release_packet_opened: bool = False
    release_review_completed: bool = False


@dataclass(frozen=True)
class SubjectWorkflowJourneyResolution:
    gather: SubjectWorkflowJourneyStatus
    itemize: SubjectWorkflowJourneyStatus
    shape: SubjectWorkflowJourneyStatus
    release: SubjectWorkflowJourneyStatus
    admitted_unit_count: int = 0
    markdown_source_label: str = ""


@dataclass(frozen=True)
class SubjectWorkflowCurrentStepResolution:
    state: SubjectWorkflowCurrentStepState


_CURRENT_STEP_GUIDANCE_TAB_BY_STATE: dict[SubjectWorkflowCurrentStepState, SubjectWorkflowTab] = {
    SubjectWorkflowCurrentStepState.MARKDOWN_BUSY: SubjectWorkflowTab.RESEARCH,
    SubjectWorkflowCurrentStepState.RESEARCH_PREPARE_IMPORT_SOURCE: SubjectWorkflowTab.RESEARCH,
    SubjectWorkflowCurrentStepState.RESEARCH_CREATE_IMPORT_FROM_SOURCE: SubjectWorkflowTab.RESEARCH,
    SubjectWorkflowCurrentStepState.CREATE_FIRST_SUBJECT: SubjectWorkflowTab.RESEARCH,
    SubjectWorkflowCurrentStepState.ACTIVATE_SUBJECT: SubjectWorkflowTab.RESEARCH,
    SubjectWorkflowCurrentStepState.REVIEW_PENDING_IMPORT: SubjectWorkflowTab.REVIEW,
    SubjectWorkflowCurrentStepState.ITEMIZE_GENERATE: SubjectWorkflowTab.ITEMIZE,
    SubjectWorkflowCurrentStepState.ITEMIZE_REFRESH: SubjectWorkflowTab.ITEMIZE,
    SubjectWorkflowCurrentStepState.ITEMIZE_INSPECT: SubjectWorkflowTab.ITEMIZE,
    SubjectWorkflowCurrentStepState.ITEMIZE_ORIENT: SubjectWorkflowTab.ITEMIZE,
    SubjectWorkflowCurrentStepState.DRAFT_CREATE_COMPOSITION: SubjectWorkflowTab.DRAFT,
    SubjectWorkflowCurrentStepState.DRAFT_REFRESH_COMPOSITION: SubjectWorkflowTab.DRAFT,
    SubjectWorkflowCurrentStepState.DRAFT_CHECK_MAINTAINED_FILES: SubjectWorkflowTab.REVIEW,
    SubjectWorkflowCurrentStepState.DRAFT_CREATE_REPORT_PLAN: SubjectWorkflowTab.DRAFT,
    SubjectWorkflowCurrentStepState.DRAFT_APPROVED: SubjectWorkflowTab.PUBLICATION,
    SubjectWorkflowCurrentStepState.DRAFT_SHAPE: SubjectWorkflowTab.DRAFT,
    SubjectWorkflowCurrentStepState.REVIEW_CHECK_MAINTAINED_FILES: SubjectWorkflowTab.REVIEW,
    SubjectWorkflowCurrentStepState.REVIEW_RETURN_TO_DRAFT: SubjectWorkflowTab.DRAFT,
    SubjectWorkflowCurrentStepState.REVIEW_CREATE_REPORT_PLAN: SubjectWorkflowTab.REVIEW,
    SubjectWorkflowCurrentStepState.REVIEW_APPROVE_REPORT_PLAN: SubjectWorkflowTab.REVIEW,
    SubjectWorkflowCurrentStepState.PUBLICATION_LOCK_INPUTS: SubjectWorkflowTab.PUBLICATION,
    SubjectWorkflowCurrentStepState.PUBLICATION_BUILD_REPORT: SubjectWorkflowTab.PUBLICATION,
    SubjectWorkflowCurrentStepState.PUBLICATION_FIX_BUILD: SubjectWorkflowTab.PUBLICATION,
    SubjectWorkflowCurrentStepState.PUBLICATION_INSPECT_RELEASE_FOLDER: SubjectWorkflowTab.PUBLICATION,
    SubjectWorkflowCurrentStepState.PUBLICATION_FINISH_RELEASE_REVIEW: SubjectWorkflowTab.PUBLICATION,
    SubjectWorkflowCurrentStepState.PUBLICATION_COMPLETE: SubjectWorkflowTab.PUBLICATION,
}

_CURRENT_STEP_GUIDANCE_TAB_OVERRIDES: dict[
    tuple[SubjectWorkflowCurrentStepState, SubjectWorkflowTab],
    SubjectWorkflowTab,
] = {
    (
        SubjectWorkflowCurrentStepState.DRAFT_APPROVED,
        SubjectWorkflowTab.DRAFT,
    ): SubjectWorkflowTab.DRAFT,
    (
        SubjectWorkflowCurrentStepState.REVIEW_CHECK_MAINTAINED_FILES,
        SubjectWorkflowTab.RESEARCH,
    ): SubjectWorkflowTab.RESEARCH,
}


SUBJECT_WORKFLOW_TRANSITIONS: tuple[SubjectWorkflowTransitionRow, ...] = (
    SubjectWorkflowTransitionRow(
        SubjectWorkflowTab.RESEARCH,
        SubjectWorkflowObject.SUBJECT_PROGRESS,
        SubjectWorkflowStatus.CLOSED,
        SubjectWorkflowTab.ITEMIZE,
        SubjectWorkflowObject.SUBJECT_PROGRESS,
        SubjectWorkflowStatus.BLOCKED,
    ),
    SubjectWorkflowTransitionRow(
        SubjectWorkflowTab.RESEARCH,
        SubjectWorkflowObject.SUBJECT_PROGRESS,
        SubjectWorkflowStatus.CLOSED,
        SubjectWorkflowTab.DRAFT,
        SubjectWorkflowObject.SUBJECT_PROGRESS,
        SubjectWorkflowStatus.BLOCKED,
    ),
    SubjectWorkflowTransitionRow(
        SubjectWorkflowTab.RESEARCH,
        SubjectWorkflowObject.SUBJECT_PROGRESS,
        SubjectWorkflowStatus.CLOSED,
        SubjectWorkflowTab.REVIEW,
        SubjectWorkflowObject.SUBJECT_PROGRESS,
        SubjectWorkflowStatus.BLOCKED,
    ),
    SubjectWorkflowTransitionRow(
        SubjectWorkflowTab.RESEARCH,
        SubjectWorkflowObject.SUBJECT_PROGRESS,
        SubjectWorkflowStatus.CLOSED,
        SubjectWorkflowTab.PUBLICATION,
        SubjectWorkflowObject.SUBJECT_PROGRESS,
        SubjectWorkflowStatus.BLOCKED,
    ),
    SubjectWorkflowTransitionRow(
        SubjectWorkflowTab.RESEARCH,
        SubjectWorkflowObject.LEARNING_CONTEXT,
        SubjectWorkflowStatus.ADMITTED,
        SubjectWorkflowTab.ITEMIZE,
        SubjectWorkflowObject.ITEMIZATION_SESSION,
        SubjectWorkflowStatus.CREATION_READY,
    ),
    SubjectWorkflowTransitionRow(
        SubjectWorkflowTab.RESEARCH,
        SubjectWorkflowObject.IMPORT_STAGING,
        SubjectWorkflowStatus.ACTIVE,
        SubjectWorkflowTab.RESEARCH,
        SubjectWorkflowObject.SUBJECT_IMPORT,
        SubjectWorkflowStatus.IMPORT_CREATION_AVAILABLE,
    ),
    SubjectWorkflowTransitionRow(
        SubjectWorkflowTab.RESEARCH,
        SubjectWorkflowObject.SUBJECT_IMPORT,
        SubjectWorkflowStatus.PENDING,
        SubjectWorkflowTab.REVIEW,
        SubjectWorkflowObject.SUBJECT_IMPORT,
        SubjectWorkflowStatus.PENDING,
    ),
    SubjectWorkflowTransitionRow(
        SubjectWorkflowTab.REVIEW,
        SubjectWorkflowObject.SUBJECT_IMPORT,
        SubjectWorkflowStatus.APPROVED,
        SubjectWorkflowTab.RESEARCH,
        SubjectWorkflowObject.REASONING_SCOPE,
        SubjectWorkflowStatus.ACTIVE,
    ),
    SubjectWorkflowTransitionRow(
        SubjectWorkflowTab.REVIEW,
        SubjectWorkflowObject.SUBJECT_IMPORT,
        SubjectWorkflowStatus.APPROVED,
        SubjectWorkflowTab.DRAFT,
        SubjectWorkflowObject.REASONING_SCOPE,
        SubjectWorkflowStatus.ACTIVE,
    ),
    SubjectWorkflowTransitionRow(
        SubjectWorkflowTab.REVIEW,
        SubjectWorkflowObject.SUBJECT_IMPORT,
        SubjectWorkflowStatus.REJECTED,
        SubjectWorkflowTab.RESEARCH,
        SubjectWorkflowObject.REASONING_SCOPE,
        SubjectWorkflowStatus.ABSENT,
    ),
    SubjectWorkflowTransitionRow(
        SubjectWorkflowTab.REVIEW,
        SubjectWorkflowObject.SUBJECT_IMPORT,
        SubjectWorkflowStatus.REJECTED,
        SubjectWorkflowTab.DRAFT,
        SubjectWorkflowObject.REASONING_SCOPE,
        SubjectWorkflowStatus.ABSENT,
    ),
    SubjectWorkflowTransitionRow(
        SubjectWorkflowTab.ITEMIZE,
        SubjectWorkflowObject.ITEMIZATION_SESSION,
        SubjectWorkflowStatus.VALIDATED,
        SubjectWorkflowTab.DRAFT,
        SubjectWorkflowObject.REVIEW_COMPOSITION,
        SubjectWorkflowStatus.CREATION_READY,
    ),
    SubjectWorkflowTransitionRow(
        SubjectWorkflowTab.ITEMIZE,
        SubjectWorkflowObject.ITEMIZATION_SESSION,
        SubjectWorkflowStatus.STALE,
        SubjectWorkflowTab.DRAFT,
        SubjectWorkflowObject.REVIEW_COMPOSITION,
        SubjectWorkflowStatus.BLOCKED,
    ),
    SubjectWorkflowTransitionRow(
        SubjectWorkflowTab.ITEMIZE,
        SubjectWorkflowObject.ITEMIZED_SUBJECT_ITEM,
        SubjectWorkflowStatus.CANDIDATE,
        SubjectWorkflowTab.DRAFT,
        SubjectWorkflowObject.REVIEW_ITEM,
        SubjectWorkflowStatus.CANDIDATE,
    ),
    SubjectWorkflowTransitionRow(
        SubjectWorkflowTab.ITEMIZE,
        SubjectWorkflowObject.ITEMIZED_SUBJECT_ITEM,
        SubjectWorkflowStatus.PROMOTED,
        SubjectWorkflowTab.DRAFT,
        SubjectWorkflowObject.REVIEW_ITEM,
        SubjectWorkflowStatus.INCLUDED,
    ),
    SubjectWorkflowTransitionRow(
        SubjectWorkflowTab.ITEMIZE,
        SubjectWorkflowObject.ITEMIZED_SUBJECT_ITEM,
        SubjectWorkflowStatus.REJECTED,
        SubjectWorkflowTab.DRAFT,
        SubjectWorkflowObject.REVIEW_ITEM,
        SubjectWorkflowStatus.EXCLUDED,
    ),
    SubjectWorkflowTransitionRow(
        SubjectWorkflowTab.ITEMIZE,
        SubjectWorkflowObject.ITEMIZED_SUBJECT_ITEM,
        SubjectWorkflowStatus.MERGED,
        SubjectWorkflowTab.ITEMIZE,
        SubjectWorkflowObject.ITEMIZED_SUBJECT_ITEM,
        SubjectWorkflowStatus.MERGED,
    ),
    SubjectWorkflowTransitionRow(
        SubjectWorkflowTab.ITEMIZE,
        SubjectWorkflowObject.ITEMIZED_SUBJECT_ITEM,
        SubjectWorkflowStatus.SPLIT,
        SubjectWorkflowTab.ITEMIZE,
        SubjectWorkflowObject.ITEMIZED_SUBJECT_ITEM,
        SubjectWorkflowStatus.CANDIDATE,
    ),
    SubjectWorkflowTransitionRow(
        SubjectWorkflowTab.ITEMIZE,
        SubjectWorkflowObject.ITEMIZED_SUBJECT_ITEM,
        SubjectWorkflowStatus.HELD,
        SubjectWorkflowTab.ITEMIZE,
        SubjectWorkflowObject.ITEMIZED_SUBJECT_ITEM,
        SubjectWorkflowStatus.HELD,
    ),
    SubjectWorkflowTransitionRow(
        SubjectWorkflowTab.ITEMIZE,
        SubjectWorkflowObject.ITEMIZATION_SESSION,
        SubjectWorkflowStatus.SEED_ALL_NON_REJECTED,
        SubjectWorkflowTab.DRAFT,
        SubjectWorkflowObject.REVIEW_COMPOSITION,
        SubjectWorkflowStatus.SEED_ALL_NON_REJECTED,
    ),
    SubjectWorkflowTransitionRow(
        SubjectWorkflowTab.ITEMIZE,
        SubjectWorkflowObject.ITEMIZATION_SESSION,
        SubjectWorkflowStatus.SEED_PROMOTED_ONLY,
        SubjectWorkflowTab.DRAFT,
        SubjectWorkflowObject.REVIEW_COMPOSITION,
        SubjectWorkflowStatus.SEED_PROMOTED_ONLY,
    ),
    SubjectWorkflowTransitionRow(
        SubjectWorkflowTab.DRAFT,
        SubjectWorkflowObject.REVIEW_COMPOSITION,
        SubjectWorkflowStatus.STALE,
        SubjectWorkflowTab.REVIEW,
        SubjectWorkflowObject.REVIEW_COMPOSITION,
        SubjectWorkflowStatus.BLOCKED,
    ),
    SubjectWorkflowTransitionRow(
        SubjectWorkflowTab.DRAFT,
        SubjectWorkflowObject.REVIEW_COMPOSITION,
        SubjectWorkflowStatus.CURRENT,
        SubjectWorkflowTab.REVIEW,
        SubjectWorkflowObject.REVIEW_COMPOSITION,
        SubjectWorkflowStatus.CURRENT,
    ),
    SubjectWorkflowTransitionRow(
        SubjectWorkflowTab.DRAFT,
        SubjectWorkflowObject.REVIEW_ITEM,
        SubjectWorkflowStatus.INCLUDED,
        SubjectWorkflowTab.PUBLICATION,
        SubjectWorkflowObject.PUBLICATION_COMPOSITION,
        SubjectWorkflowStatus.INCLUDED,
    ),
    SubjectWorkflowTransitionRow(
        SubjectWorkflowTab.DRAFT,
        SubjectWorkflowObject.REVIEW_ITEM,
        SubjectWorkflowStatus.ORDERED,
        SubjectWorkflowTab.PUBLICATION,
        SubjectWorkflowObject.PUBLICATION_COMPOSITION,
        SubjectWorkflowStatus.ORDERED,
    ),
    SubjectWorkflowTransitionRow(
        SubjectWorkflowTab.DRAFT,
        SubjectWorkflowObject.REVIEW_ITEM,
        SubjectWorkflowStatus.ORIENTED,
        SubjectWorkflowTab.PUBLICATION,
        SubjectWorkflowObject.PUBLICATION_COMPOSITION,
        SubjectWorkflowStatus.ORIENTED,
    ),
    SubjectWorkflowTransitionRow(
        SubjectWorkflowTab.REVIEW,
        SubjectWorkflowObject.MAINTAINED_FILES,
        SubjectWorkflowStatus.PENDING,
        SubjectWorkflowTab.DRAFT,
        SubjectWorkflowObject.PUBLICATION_COMPOSITION,
        SubjectWorkflowStatus.BLOCKED,
    ),
    SubjectWorkflowTransitionRow(
        SubjectWorkflowTab.REVIEW,
        SubjectWorkflowObject.MAINTAINED_FILES,
        SubjectWorkflowStatus.STALE,
        SubjectWorkflowTab.DRAFT,
        SubjectWorkflowObject.PUBLICATION_COMPOSITION,
        SubjectWorkflowStatus.BLOCKED,
    ),
    SubjectWorkflowTransitionRow(
        SubjectWorkflowTab.REVIEW,
        SubjectWorkflowObject.MAINTAINED_FILES,
        SubjectWorkflowStatus.CURRENT,
        SubjectWorkflowTab.DRAFT,
        SubjectWorkflowObject.PUBLICATION_COMPOSITION,
        SubjectWorkflowStatus.CREATION_READY,
    ),
    SubjectWorkflowTransitionRow(
        SubjectWorkflowTab.REVIEW,
        SubjectWorkflowObject.SUBJECT_PROGRESS,
        SubjectWorkflowStatus.PENDING,
        SubjectWorkflowTab.PUBLICATION,
        SubjectWorkflowObject.SUBJECT_PROGRESS,
        SubjectWorkflowStatus.BLOCKED,
    ),
    SubjectWorkflowTransitionRow(
        SubjectWorkflowTab.REVIEW,
        SubjectWorkflowObject.SUBJECT_PROGRESS,
        SubjectWorkflowStatus.APPROVED,
        SubjectWorkflowTab.PUBLICATION,
        SubjectWorkflowObject.SUBJECT_PROGRESS,
        SubjectWorkflowStatus.READY,
    ),
    SubjectWorkflowTransitionRow(
        SubjectWorkflowTab.PUBLICATION,
        SubjectWorkflowObject.SUBJECT_PROGRESS,
        SubjectWorkflowStatus.UNLOCKED,
        SubjectWorkflowTab.PUBLICATION,
        SubjectWorkflowObject.PUBLICATION_BUILD,
        SubjectWorkflowStatus.BLOCKED,
    ),
    SubjectWorkflowTransitionRow(
        SubjectWorkflowTab.PUBLICATION,
        SubjectWorkflowObject.SUBJECT_PROGRESS,
        SubjectWorkflowStatus.LOCKED,
        SubjectWorkflowTab.PUBLICATION,
        SubjectWorkflowObject.PUBLICATION_BUILD,
        SubjectWorkflowStatus.CREATION_READY,
    ),
    SubjectWorkflowTransitionRow(
        SubjectWorkflowTab.PUBLICATION,
        SubjectWorkflowObject.PUBLICATION_BUILD,
        SubjectWorkflowStatus.MISSING,
        SubjectWorkflowTab.PUBLICATION,
        SubjectWorkflowObject.RELEASE_REVIEW,
        SubjectWorkflowStatus.BLOCKED,
    ),
    SubjectWorkflowTransitionRow(
        SubjectWorkflowTab.PUBLICATION,
        SubjectWorkflowObject.PUBLICATION_BUILD,
        SubjectWorkflowStatus.FAILED,
        SubjectWorkflowTab.PUBLICATION,
        SubjectWorkflowObject.RELEASE_REVIEW,
        SubjectWorkflowStatus.BLOCKED,
    ),
    SubjectWorkflowTransitionRow(
        SubjectWorkflowTab.PUBLICATION,
        SubjectWorkflowObject.PUBLICATION_BUILD,
        SubjectWorkflowStatus.READY,
        SubjectWorkflowTab.PUBLICATION,
        SubjectWorkflowObject.RELEASE_REVIEW,
        SubjectWorkflowStatus.READY,
    ),
    SubjectWorkflowTransitionRow(
        SubjectWorkflowTab.PUBLICATION,
        SubjectWorkflowObject.RELEASE_REVIEW,
        SubjectWorkflowStatus.PENDING,
        SubjectWorkflowTab.PUBLICATION,
        SubjectWorkflowObject.RELEASE_REVIEW,
        SubjectWorkflowStatus.PENDING,
    ),
    SubjectWorkflowTransitionRow(
        SubjectWorkflowTab.PUBLICATION,
        SubjectWorkflowObject.RELEASE_REVIEW,
        SubjectWorkflowStatus.COMPLETE,
        SubjectWorkflowTab.PUBLICATION,
        SubjectWorkflowObject.RELEASE_REVIEW,
        SubjectWorkflowStatus.COMPLETE,
    ),
)


SUBJECT_WORKFLOW_PLAIN_LANGUAGE_TERMS: tuple[str, ...] = (
    "- itemization = typed glossary/entity/claim/equation/decision-role candidates",
    "- maintained files = subject.md and subject.typ",
    "- report plan = what the report will include",
    "- release folder = the built report outputs",
)


def resolve_subject_workflow_journey(inputs: SubjectWorkflowStateInputs) -> SubjectWorkflowJourneyResolution:
    source_label = inputs.markdown_source_label or "markdown intake"
    if inputs.markdown_busy:
        return SubjectWorkflowJourneyResolution(
            gather=SubjectWorkflowJourneyStatus.GATHER_IMPORTING,
            itemize=(
                SubjectWorkflowJourneyStatus.ITEMIZE_WAITING_FOR_FIRST_IMPORT
                if not inputs.subject_exists
                else SubjectWorkflowJourneyStatus.ITEMIZE_WAITING_FOR_IMPORT
            ),
            shape=SubjectWorkflowJourneyStatus.SHAPE_BLOCKED_ITEMIZE,
            release=SubjectWorkflowJourneyStatus.RELEASE_BLOCKED_DRAFT_REVIEW,
            admitted_unit_count=inputs.admitted_unit_count,
            markdown_source_label=source_label,
        )
    if not inputs.subject_exists:
        return SubjectWorkflowJourneyResolution(
            gather=SubjectWorkflowJourneyStatus.GATHER_NOT_STARTED,
            itemize=SubjectWorkflowJourneyStatus.ITEMIZE_BLOCKED_NO_SUBJECT,
            shape=SubjectWorkflowJourneyStatus.SHAPE_BLOCKED_NO_SUBJECT,
            release=SubjectWorkflowJourneyStatus.RELEASE_BLOCKED_DRAFT_REVIEW,
            admitted_unit_count=inputs.admitted_unit_count,
        )
    gather = (
        SubjectWorkflowJourneyStatus.GATHER_READY
        if inputs.admitted_unit_count > 0
        else SubjectWorkflowJourneyStatus.GATHER_IN_PROGRESS
    )
    if not inputs.context_opened:
        itemize = SubjectWorkflowJourneyStatus.ITEMIZE_BLOCKED_CONTEXT_CLOSED
    elif not inputs.itemization_exists:
        itemize = SubjectWorkflowJourneyStatus.ITEMIZE_IN_PROGRESS_GENERATE
    elif not inputs.itemization_current or not inputs.itemization_valid:
        itemize = SubjectWorkflowJourneyStatus.ITEMIZE_IN_PROGRESS_REFRESH
    else:
        itemize = SubjectWorkflowJourneyStatus.ITEMIZE_READY
    if not inputs.context_opened:
        shape = SubjectWorkflowJourneyStatus.SHAPE_BLOCKED_CONTEXT_CLOSED
    elif itemize != SubjectWorkflowJourneyStatus.ITEMIZE_READY:
        shape = SubjectWorkflowJourneyStatus.SHAPE_BLOCKED_ITEMIZE
    elif not inputs.draft_composition_current:
        shape = SubjectWorkflowJourneyStatus.SHAPE_IN_PROGRESS_CREATE_DRAFT
    elif inputs.pending_import_count > 0:
        shape = SubjectWorkflowJourneyStatus.SHAPE_BLOCKED_PENDING_IMPORTS
    elif not inputs.report_plan_current:
        shape = SubjectWorkflowJourneyStatus.SHAPE_IN_PROGRESS_CREATE_REPORT_PLAN
    elif not inputs.review_approved:
        shape = SubjectWorkflowJourneyStatus.SHAPE_IN_PROGRESS_HANDOFF
    else:
        shape = SubjectWorkflowJourneyStatus.SHAPE_READY
    if not inputs.report_plan_current and not inputs.publication_locked:
        release = SubjectWorkflowJourneyStatus.RELEASE_BLOCKED_DRAFT_REVIEW
    elif not inputs.review_approved and not inputs.publication_locked:
        release = SubjectWorkflowJourneyStatus.RELEASE_BLOCKED_DRAFT_REVIEW
    elif not inputs.publication_locked:
        release = SubjectWorkflowJourneyStatus.RELEASE_READY_TO_LOCK
    elif not inputs.publication_build_exists:
        release = SubjectWorkflowJourneyStatus.RELEASE_READY_TO_BUILD
    elif not inputs.publication_build_ready:
        release = SubjectWorkflowJourneyStatus.RELEASE_BLOCKED_FIX_BUILD
    elif not inputs.release_packet_opened:
        release = SubjectWorkflowJourneyStatus.RELEASE_BUILT_INSPECT_PACKET
    elif not inputs.release_review_completed:
        release = SubjectWorkflowJourneyStatus.RELEASE_BUILT_FINISH_REVIEW
    else:
        release = SubjectWorkflowJourneyStatus.RELEASE_COMPLETE
    return SubjectWorkflowJourneyResolution(
        gather=gather,
        itemize=itemize,
        shape=shape,
        release=release,
        admitted_unit_count=inputs.admitted_unit_count,
    )


def resolve_subject_workflow_current_step(
    inputs: SubjectWorkflowCurrentStepInputs,
) -> SubjectWorkflowCurrentStepResolution:
    if inputs.markdown_busy:
        return SubjectWorkflowCurrentStepResolution(SubjectWorkflowCurrentStepState.MARKDOWN_BUSY)
    if inputs.phase == SubjectWorkflowTab.RESEARCH and inputs.import_staging_active:
        if inputs.import_staging_on_current_subject:
            return SubjectWorkflowCurrentStepResolution(
                SubjectWorkflowCurrentStepState.RESEARCH_PREPARE_IMPORT_SOURCE
            )
        if inputs.import_staging_target_ready:
            return SubjectWorkflowCurrentStepResolution(
                SubjectWorkflowCurrentStepState.RESEARCH_CREATE_IMPORT_FROM_SOURCE
            )
    if not inputs.subject_exists:
        return SubjectWorkflowCurrentStepResolution(SubjectWorkflowCurrentStepState.CREATE_FIRST_SUBJECT)
    if not inputs.context_opened:
        return SubjectWorkflowCurrentStepResolution(SubjectWorkflowCurrentStepState.ACTIVATE_SUBJECT)
    if inputs.pending_import_count > 0:
        return SubjectWorkflowCurrentStepResolution(SubjectWorkflowCurrentStepState.REVIEW_PENDING_IMPORT)
    if inputs.phase == SubjectWorkflowTab.DRAFT:
        if not inputs.itemization_exists:
            return SubjectWorkflowCurrentStepResolution(SubjectWorkflowCurrentStepState.ITEMIZE_GENERATE)
        if not inputs.itemization_current or not inputs.itemization_valid:
            return SubjectWorkflowCurrentStepResolution(SubjectWorkflowCurrentStepState.ITEMIZE_REFRESH)
        if not inputs.draft_composition_exists:
            return SubjectWorkflowCurrentStepResolution(SubjectWorkflowCurrentStepState.DRAFT_CREATE_COMPOSITION)
        if not inputs.draft_composition_current:
            return SubjectWorkflowCurrentStepResolution(SubjectWorkflowCurrentStepState.DRAFT_REFRESH_COMPOSITION)
        if not inputs.report_plan_current:
            if inputs.draft_shape_precedes_report_plan:
                return SubjectWorkflowCurrentStepResolution(SubjectWorkflowCurrentStepState.DRAFT_SHAPE)
            return SubjectWorkflowCurrentStepResolution(SubjectWorkflowCurrentStepState.DRAFT_CREATE_REPORT_PLAN)
        if inputs.review_approved:
            return SubjectWorkflowCurrentStepResolution(SubjectWorkflowCurrentStepState.DRAFT_APPROVED)
        return SubjectWorkflowCurrentStepResolution(SubjectWorkflowCurrentStepState.DRAFT_SHAPE)
    if not inputs.maintained_files_aligned:
        return SubjectWorkflowCurrentStepResolution(SubjectWorkflowCurrentStepState.REVIEW_CHECK_MAINTAINED_FILES)
    if not inputs.itemization_exists:
        return SubjectWorkflowCurrentStepResolution(SubjectWorkflowCurrentStepState.ITEMIZE_GENERATE)
    if not inputs.itemization_current or not inputs.itemization_valid:
        return SubjectWorkflowCurrentStepResolution(SubjectWorkflowCurrentStepState.ITEMIZE_REFRESH)
    if inputs.phase == SubjectWorkflowTab.ITEMIZE:
        if not inputs.itemization_selected:
            return SubjectWorkflowCurrentStepResolution(SubjectWorkflowCurrentStepState.ITEMIZE_INSPECT)
        return SubjectWorkflowCurrentStepResolution(SubjectWorkflowCurrentStepState.ITEMIZE_ORIENT)
    if not inputs.draft_composition_current:
        return SubjectWorkflowCurrentStepResolution(SubjectWorkflowCurrentStepState.REVIEW_RETURN_TO_DRAFT)
    if not inputs.report_plan_current:
        return SubjectWorkflowCurrentStepResolution(SubjectWorkflowCurrentStepState.REVIEW_CREATE_REPORT_PLAN)
    if not inputs.review_approved:
        return SubjectWorkflowCurrentStepResolution(SubjectWorkflowCurrentStepState.REVIEW_APPROVE_REPORT_PLAN)
    if not inputs.publication_locked:
        return SubjectWorkflowCurrentStepResolution(SubjectWorkflowCurrentStepState.PUBLICATION_LOCK_INPUTS)
    if not inputs.publication_build_exists:
        return SubjectWorkflowCurrentStepResolution(SubjectWorkflowCurrentStepState.PUBLICATION_BUILD_REPORT)
    if not inputs.publication_build_ready:
        return SubjectWorkflowCurrentStepResolution(SubjectWorkflowCurrentStepState.PUBLICATION_FIX_BUILD)
    if not inputs.release_packet_opened:
        return SubjectWorkflowCurrentStepResolution(
            SubjectWorkflowCurrentStepState.PUBLICATION_INSPECT_RELEASE_FOLDER
        )
    if not inputs.release_review_completed:
        return SubjectWorkflowCurrentStepResolution(
            SubjectWorkflowCurrentStepState.PUBLICATION_FINISH_RELEASE_REVIEW
        )
    return SubjectWorkflowCurrentStepResolution(SubjectWorkflowCurrentStepState.PUBLICATION_COMPLETE)


def preferred_subject_workflow_tab_for_current_step(
    *,
    state: SubjectWorkflowCurrentStepState,
    current_tab: SubjectWorkflowTab,
) -> SubjectWorkflowTab:
    override = _CURRENT_STEP_GUIDANCE_TAB_OVERRIDES.get((state, current_tab))
    if override is not None:
        return override
    return _CURRENT_STEP_GUIDANCE_TAB_BY_STATE.get(state, current_tab)


def render_subject_workflow_journey_lines(
    resolution: SubjectWorkflowJourneyResolution,
) -> tuple[str, ...]:
    return (
        f"1. Gather material: {_render_gather_status(resolution)}",
        f"2. Itemize the subject: {_render_itemize_status(resolution.itemize)}",
        f"3. Shape the report: {_render_shape_status(resolution.shape)}",
        f"4. Release the report: {_render_release_status(resolution.release)}",
        "",
        "Plain-language terms",
        *SUBJECT_WORKFLOW_PLAIN_LANGUAGE_TERMS,
    )


def _render_gather_status(resolution: SubjectWorkflowJourneyResolution) -> str:
    if resolution.gather == SubjectWorkflowJourneyStatus.GATHER_IMPORTING:
        return f"importing {resolution.markdown_source_label or 'markdown intake'}"
    if resolution.gather == SubjectWorkflowJourneyStatus.GATHER_NOT_STARTED:
        return "not started"
    if resolution.gather == SubjectWorkflowJourneyStatus.GATHER_IN_PROGRESS:
        return "in progress (no ready items yet)"
    if resolution.gather == SubjectWorkflowJourneyStatus.GATHER_READY:
        item_label = "item" if int(resolution.admitted_unit_count or 0) == 1 else "items"
        return f"ready ({resolution.admitted_unit_count} {item_label})"
    raise ValueError(f"Unsupported gather journey status: {resolution.gather}")


def _render_itemize_status(status: SubjectWorkflowJourneyStatus) -> str:
    if status == SubjectWorkflowJourneyStatus.ITEMIZE_WAITING_FOR_FIRST_IMPORT:
        return "blocked until the import finishes and creates the first subject"
    if status == SubjectWorkflowJourneyStatus.ITEMIZE_WAITING_FOR_IMPORT:
        return "waiting for the current import to finish"
    if status == SubjectWorkflowJourneyStatus.ITEMIZE_BLOCKED_NO_SUBJECT:
        return "blocked until a subject exists"
    if status == SubjectWorkflowJourneyStatus.ITEMIZE_BLOCKED_CONTEXT_CLOSED:
        return "blocked - activate the subject first"
    if status == SubjectWorkflowJourneyStatus.ITEMIZE_IN_PROGRESS_GENERATE:
        return "in progress - generate the itemization inventory"
    if status == SubjectWorkflowJourneyStatus.ITEMIZE_IN_PROGRESS_REFRESH:
        return "in progress - refresh the itemization inventory"
    if status == SubjectWorkflowJourneyStatus.ITEMIZE_READY:
        return "ready"
    raise ValueError(f"Unsupported itemize journey status: {status}")


def _render_shape_status(status: SubjectWorkflowJourneyStatus) -> str:
    if status == SubjectWorkflowJourneyStatus.SHAPE_BLOCKED_NO_SUBJECT:
        return "blocked until a subject exists"
    if status == SubjectWorkflowJourneyStatus.SHAPE_BLOCKED_CONTEXT_CLOSED:
        return "blocked - activate the subject first"
    if status == SubjectWorkflowJourneyStatus.SHAPE_BLOCKED_ITEMIZE:
        return "blocked - finish Itemize first"
    if status == SubjectWorkflowJourneyStatus.SHAPE_IN_PROGRESS_CREATE_DRAFT:
        return "in progress - create the draft composition"
    if status == SubjectWorkflowJourneyStatus.SHAPE_BLOCKED_PENDING_IMPORTS:
        return "blocked - resolve pending imported support"
    if status == SubjectWorkflowJourneyStatus.SHAPE_BLOCKED_MAINTAINED_FILES:
        return "blocked - check the maintained files in Review"
    if status == SubjectWorkflowJourneyStatus.SHAPE_IN_PROGRESS_CREATE_REPORT_PLAN:
        return "in progress - create the report plan"
    if status == SubjectWorkflowJourneyStatus.SHAPE_IN_PROGRESS_HANDOFF:
        return "in progress - shape the draft and hand it to Review"
    if status == SubjectWorkflowJourneyStatus.SHAPE_READY:
        return "ready"
    raise ValueError(f"Unsupported shape journey status: {status}")


def _render_release_status(status: SubjectWorkflowJourneyStatus) -> str:
    if status == SubjectWorkflowJourneyStatus.RELEASE_BLOCKED_DRAFT_REVIEW:
        return "blocked - finish Draft and Review first"
    if status == SubjectWorkflowJourneyStatus.RELEASE_READY_TO_LOCK:
        return "ready to lock inputs"
    if status == SubjectWorkflowJourneyStatus.RELEASE_READY_TO_BUILD:
        return "ready to build"
    if status == SubjectWorkflowJourneyStatus.RELEASE_BLOCKED_FIX_BUILD:
        return "blocked - fix the report build"
    if status == SubjectWorkflowJourneyStatus.RELEASE_BUILT_INSPECT_PACKET:
        return "built - inspect the release folder"
    if status == SubjectWorkflowJourneyStatus.RELEASE_BUILT_FINISH_REVIEW:
        return "built - finish the release review"
    if status == SubjectWorkflowJourneyStatus.RELEASE_COMPLETE:
        return "complete"
    raise ValueError(f"Unsupported release journey status: {status}")
