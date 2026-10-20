"""Stable subject-workflow surface for the Textual UI adapter."""

from workstation.contracts.subject import SubjectWorkflowScenarioView as MockSubjectScenario
from workstation.subject.textual.models import (
    SUBJECT_PHASES as MOCK_SUBJECT_PHASES,
    TextualSubjectActionSpec as MockSubjectActionSpec,
    TextualSubjectGateAction as MockSubjectGateAction,
    TextualSubjectProgress as MockSubjectProgress,
    TextualSubjectSelectionListSpec as MockSubjectSelectionListSpec,
    TextualSubjectSelectSpec as MockSubjectSelectSpec,
    TextualSubjectSwitchSpec as MockSubjectSwitchSpec,
    TextualSubjectTableSpec as MockSubjectTableSpec,
    latest_source_revision,
    new_textual_subject_progress as new_mock_subject_progress,
    normalize_textual_decision_role as normalize_itemized_decision_role,
    source_collection_option_label as mock_source_collection_option_label,
    source_collection_workbench_rows,
    textual_subject_status_title as mock_subject_status_title,
)
from workstation.subject.textual.subject_workflow_textual_backend import (
    TextualSubjectWorkflowProjectionBackend,
)


def mock_subject_research_source_collection_workbench_rows(
    *,
    root_path,
    scenario,
    progress,
    selected_collection,
):
    del root_path, scenario, progress
    return source_collection_workbench_rows(selected_collection)


__all__ = [
    "MOCK_SUBJECT_PHASES",
    "MockSubjectActionSpec",
    "MockSubjectGateAction",
    "MockSubjectProgress",
    "MockSubjectScenario",
    "MockSubjectSelectSpec",
    "MockSubjectSelectionListSpec",
    "MockSubjectSwitchSpec",
    "MockSubjectTableSpec",
    "TextualSubjectWorkflowProjectionBackend",
    "latest_source_revision",
    "mock_source_collection_option_label",
    "mock_subject_research_source_collection_workbench_rows",
    "mock_subject_status_title",
    "new_mock_subject_progress",
    "normalize_itemized_decision_role",
]
