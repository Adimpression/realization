"""Provider-neutral natural-language planning for governed conversation turns."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
import json
from typing import Any, Protocol


PLANNING_SCHEMA_VERSION = "1"
PLANNING_PROMPT_VERSION = "23"
RENDERING_SCHEMA_VERSION = "1"
RENDERING_PROMPT_VERSION = "6"


class ConversationPlanningError(ValueError):
    """Raised when an advisory interpretation cannot form an exact plan."""

    def __init__(
        self,
        message: str,
        *,
        provider_receipt: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.provider_receipt = dict(provider_receipt or {})


class ConversationOperation(StrEnum):
    """Provider-facing operation vocabulary, independent of the engine ABI."""

    START = "start"
    CONTINUE = "continue"
    DERIVE = "derive"
    RESUME_AFTER_INTERRUPTION = "resume_after_interruption"
    RESUME_SUSPENDED = "resume_suspended"
    AUGMENT = "augment"
    CORRECT = "correct"
    REDIRECT_AND_REALIGN = "redirect_and_realign"
    BRANCH = "branch"
    MERGE = "merge"
    EXPLAIN = "explain"
    VERIFY = "verify"
    REVERSE = "reverse"
    RECONSTRUCT = "reconstruct"


class ConversationIdentityDisposition(StrEnum):
    """Provider-facing identity proposal interpreted by the application."""

    SAME_OBJECTIVE = "same_objective"
    DERIVED_OBJECTIVE = "derived_objective"
    BRANCH = "branch"


@dataclass(frozen=True, slots=True)
class AdvisoryJsonResult:
    """Provider-neutral JSON payload accompanied by inspectable provenance."""

    payload: Mapping[str, Any]
    receipt: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SemanticItemProposal:
    """Public semantic material proposed without an internal item identity."""

    selector: str
    kind: str
    value: str = ""
    text: str = ""

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> SemanticItemProposal:
        return cls(
            selector=str(value.get("selector", "")).strip(),
            kind=str(value.get("kind", "fact")).strip() or "fact",
            value=str(value.get("value", "")).strip(),
            text=str(value.get("text", "")).strip(),
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "selector": self.selector,
            "kind": self.kind,
            "value": self.value,
            "text": self.text,
        }


@dataclass(frozen=True, slots=True)
class CorrectionProposal:
    """Advisory replacement or removal of one public semantic selector."""

    target_selector: str
    replacement: SemanticItemProposal | None
    rationale: str

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> CorrectionProposal:
        raw_replacement = value.get("replacement")
        return cls(
            target_selector=str(value.get("target_selector", "")).strip(),
            replacement=(
                SemanticItemProposal.from_dict(raw_replacement)
                if isinstance(raw_replacement, Mapping)
                and any(str(item).strip() for item in raw_replacement.values())
                else None
            ),
            rationale=str(value.get("rationale", "")).strip(),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_selector": self.target_selector,
            "replacement": (
                self.replacement.to_dict()
                if self.replacement is not None
                else None
            ),
            "rationale": self.rationale,
        }


@dataclass(frozen=True, slots=True)
class ConversationPlanProposal:
    """Advisory interpretation that still requires host materialization."""

    operation: ConversationOperation | None
    schema_version: str = PLANNING_SCHEMA_VERSION
    objective: str = ""
    required_outcome: str = ""
    achieved_items: tuple[SemanticItemProposal, ...] = ()
    non_achieved_items: tuple[SemanticItemProposal, ...] = ()
    selected_selectors: tuple[str, ...] = ()
    promote_selectors: tuple[str, ...] = ()
    resolved_selectors: tuple[str, ...] = ()
    resolved_applicability_selectors: tuple[str, ...] = ()
    corrections: tuple[CorrectionProposal, ...] = ()
    affected_selectors: tuple[str, ...] = ()
    retained_selectors: tuple[str, ...] = ()
    superseded_selectors: tuple[str, ...] = ()
    unresolved_selectors: tuple[str, ...] = ()
    introduced_items: tuple[SemanticItemProposal, ...] = ()
    identity_disposition: ConversationIdentityDisposition = (
        ConversationIdentityDisposition.SAME_OBJECTIVE
    )
    target_branch: str = ""
    merge_branch_aliases: tuple[str, ...] = ()
    reversal_selector: str = ""
    unresolved_interpretation: tuple[str, ...] = ()
    rationale: str = ""

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> ConversationPlanProposal:
        schema_version = str(
            value.get("schema_version", PLANNING_SCHEMA_VERSION)
        ).strip()
        operation_text = str(value.get("operation", "")).strip().casefold()
        operation = None
        try:
            operation = ConversationOperation(operation_text)
        except ValueError:
            pass
        unresolved = _strings(value.get("unresolved_interpretation"))
        if schema_version != PLANNING_SCHEMA_VERSION:
            unresolved = tuple(
                dict.fromkeys(
                    (
                        *unresolved,
                        "unsupported planning schema version: "
                        f"{schema_version or 'empty'}",
                    )
                )
            )
        disposition_text = str(
            value.get(
                "identity_disposition",
                ConversationIdentityDisposition.SAME_OBJECTIVE.value,
            )
        ).strip().casefold()
        try:
            disposition = ConversationIdentityDisposition(disposition_text)
        except ValueError:
            disposition = ConversationIdentityDisposition.SAME_OBJECTIVE
            unresolved = tuple(
                dict.fromkeys(
                    (
                        *unresolved,
                        "unsupported identity disposition: "
                        f"{disposition_text or 'empty'}",
                    )
                )
            )
        if operation is None:
            unresolved = tuple(
                dict.fromkeys(
                    (*unresolved, f"unsupported operation: {operation_text or 'empty'}")
                )
            )
        return cls(
            operation=operation,
            schema_version=schema_version,
            objective=str(value.get("objective", "")).strip(),
            required_outcome=str(value.get("required_outcome", "")).strip(),
            achieved_items=_items(value.get("achieved_items")),
            non_achieved_items=_items(value.get("non_achieved_items")),
            selected_selectors=_strings(value.get("selected_selectors")),
            promote_selectors=_strings(value.get("promote_selectors")),
            resolved_selectors=_strings(value.get("resolved_selectors")),
            resolved_applicability_selectors=_strings(
                value.get("resolved_applicability_selectors")
            ),
            corrections=_corrections(value.get("corrections")),
            affected_selectors=_strings(value.get("affected_selectors")),
            retained_selectors=_strings(value.get("retained_selectors")),
            superseded_selectors=_strings(value.get("superseded_selectors")),
            unresolved_selectors=_strings(value.get("unresolved_selectors")),
            introduced_items=_items(value.get("introduced_items")),
            identity_disposition=disposition,
            target_branch=str(value.get("target_branch", "")).strip(),
            merge_branch_aliases=_strings(value.get("merge_branch_aliases")),
            reversal_selector=str(value.get("reversal_selector", "")).strip(),
            unresolved_interpretation=unresolved,
            rationale=str(value.get("rationale", "")).strip(),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "operation": self.operation.value if self.operation else None,
            "objective": self.objective,
            "required_outcome": self.required_outcome,
            "achieved_items": [item.to_dict() for item in self.achieved_items],
            "non_achieved_items": [
                item.to_dict() for item in self.non_achieved_items
            ],
            "selected_selectors": list(self.selected_selectors),
            "promote_selectors": list(self.promote_selectors),
            "resolved_selectors": list(self.resolved_selectors),
            "resolved_applicability_selectors": list(
                self.resolved_applicability_selectors
            ),
            "corrections": [item.to_dict() for item in self.corrections],
            "affected_selectors": list(self.affected_selectors),
            "retained_selectors": list(self.retained_selectors),
            "superseded_selectors": list(self.superseded_selectors),
            "unresolved_selectors": list(self.unresolved_selectors),
            "introduced_items": [
                item.to_dict() for item in self.introduced_items
            ],
            "identity_disposition": self.identity_disposition.value,
            "target_branch": self.target_branch,
            "merge_branch_aliases": list(self.merge_branch_aliases),
            "reversal_selector": self.reversal_selector,
            "unresolved_interpretation": list(
                self.unresolved_interpretation
            ),
            "rationale": self.rationale,
        }


@dataclass(frozen=True, slots=True)
class ConversationPlanningContext:
    """Bounded state supplied to an advisory conversational planner."""

    prompt: str
    scope_id: str
    parent_run_id: str = ""
    parent_identity: dict[str, Any] | None = None
    current_state: dict[str, Any] | None = None
    binding_aliases: dict[str, str] = field(default_factory=dict)
    interrupted_attempt_available: bool = False

    @property
    def has_causal_binding(self) -> bool:
        return self.parent_identity is not None

    def public_payload(self) -> dict[str, Any]:
        state = dict(self.current_state or {})
        return {
            "planning_schema_version": PLANNING_SCHEMA_VERSION,
            "planning_prompt_version": PLANNING_PROMPT_VERSION,
            "prompt": self.prompt,
            "has_causal_binding": self.has_causal_binding,
            "current_direction": dict(state.get("governing_direction", {})),
            "current_achieved": _public_items(state.get("achieved")),
            "current_non_achievedness": _public_items(
                state.get("non_achievedness")
            ),
            "active_holds": _public_holds(state),
            "unresolved_applicability_selectors": _selectors_for_ids(
                state,
                state.get("unresolved_applicability_item_ids", ()),
            ),
            "available_branch_aliases": sorted(self.binding_aliases),
            "interrupted_attempt_available": (
                self.interrupted_attempt_available
            ),
        }


class ConversationPlanner(Protocol):
    def propose(
        self,
        context: ConversationPlanningContext,
    ) -> ConversationPlanningResult: ...


@dataclass(frozen=True, slots=True)
class ConversationPlanningResult:
    """One advisory plan and its non-semantic provider receipt."""

    proposal: ConversationPlanProposal
    receipt: dict[str, Any] = field(default_factory=dict)
    schema_version: str = PLANNING_SCHEMA_VERSION
    prompt_version: str = PLANNING_PROMPT_VERSION


@dataclass(frozen=True, slots=True)
class ConversationRenderContext:
    prompt: str
    operation: ConversationOperation
    current_state: dict[str, Any]
    path: tuple[dict[str, Any], ...]
    structured_result: dict[str, Any]
    default_text: str

    def public_payload(self) -> dict[str, Any]:
        return {
            "rendering_schema_version": RENDERING_SCHEMA_VERSION,
            "rendering_prompt_version": RENDERING_PROMPT_VERSION,
            "user_prompt": self.prompt,
            "operation": self.operation.value,
            "current_state": {
                "governing_direction": dict(
                    self.current_state.get("governing_direction", {})
                ),
                "achieved": _public_items(
                    self.current_state.get("achieved")
                ),
                "non_achievedness": _public_items(
                    self.current_state.get("non_achievedness")
                ),
            },
            "admitted_path": list(self.path),
            "structured_result": dict(self.structured_result),
            "fallback_response": self.default_text,
        }


class ConversationRenderer(Protocol):
    def render(self, context: ConversationRenderContext) -> ConversationRenderResult: ...


@dataclass(frozen=True, slots=True)
class ConversationRenderResult:
    """Rendered presentation and its non-semantic provider receipt."""

    text: str
    receipt: dict[str, Any] = field(default_factory=dict)
    schema_version: str = RENDERING_SCHEMA_VERSION
    prompt_version: str = RENDERING_PROMPT_VERSION


type JsonProposalCallable = Callable[
    [str, dict[str, Any]], Mapping[str, Any] | AdvisoryJsonResult
]


@dataclass(frozen=True, slots=True)
class JsonConversationPlanner:
    """Interpret one turn through an injected structured-proposal provider."""

    propose_json: JsonProposalCallable

    def propose(
        self,
        context: ConversationPlanningContext,
    ) -> ConversationPlanningResult:
        prompt = (
            "Interpret one user contribution into an advisory governed "
            "conversation plan. The host has already decided whether an exact "
            "causal binding exists; never invent or select a revision.\n\n"
            "Use these operation values only: "
            + ", ".join(item.value for item in ConversationOperation)
            + ".\n"
            "Interpret the current user prompt as the requested action. The "
            "current state is context, not a request to repeat or restart.\n"
            "Operation decision gate (apply in this order):\n"
            "1. An explicit request to undo, reverse, or restore an admitted "
            "change is reverse. Use a named public selector or the explicit "
            "generic selector 'last correction' or 'latest correction'; "
            "otherwise keep reversal_selector empty and report the ambiguity.\n"
            "2. A request to create, prepare, fork, or make an alternate named "
            "version of the current work is branch, with that version name as "
            "target_branch. This remains branch even when the version is for a "
            "different audience, such as executive or technical. A request to "
            "combine advertised branches is merge.\n"
            "3. If interrupted_attempt_available is true and the user explicitly "
            "asks to resume from the last admitted state or exclude interrupted "
            "candidate work, use resume_after_interruption. The host already "
            "owns the exact attempt identity.\n"
            "4. An instruction to change, move, set, replace, remove, or drop "
            "existing semantic material is correct. Read-only operations are "
            "never valid for such an instruction.\n"
            "5. A change to the governing product, objective, scope, or required "
            "outcome is redirect_and_realign, not correct or start. With an "
            "exact causal binding, 'instead of X, do Y' replaces the current "
            "direction and is always redirect_and_realign.\n"
            "6. A compatible addition is augment. A supplied value directly "
            "satisfying an active hold is resume_suspended. Merely seeing an "
            "active hold does not make another request resume_suspended.\n"
            "7. Explain, verify, and reconstruct apply only when the user asks "
            "to inspect admitted state or path without changing it.\n"
            "Rules:\n"
            "- Use start only for a separate independent objective. Never use "
            "start for 'instead of', 'replace the current objective', or another "
            "request that explicitly redirects the bound work.\n"
            "- A new topic does not by itself prove either continuation or "
            "redirection. Use start only when the contribution explicitly "
            "establishes independent identity, for example: 'Separately, start "
            "a new objective: plan a weekend hiking trip.' That exact example "
            "is start, not redirect_and_realign. Without an explicit identity "
            "relationship, report unresolved interpretation rather than "
            "choosing identity from semantic similarity or dissimilarity.\n"
            "- When an exact causal binding exists, a question asking for the "
            "current state, constraints, history, rationale, or remaining work "
            "is explain, verify, or reconstruct as appropriate, never start. "
            "Use start with an existing binding only when the user clearly "
            "requests a separate independent objective.\n"
            "- Use correct for explicit replacement or removal of current "
            "semantic material when the governing objective, scope, and "
            "required outcome stay the same; name each public target selector. "
            "Changing blue to green or Friday to Monday is correction, not "
            "redirection.\n"
            "- Exact unresolved-field example: when audience is current "
            "non-achievedness and the user says 'Set the unresolved audience "
            "to city officials', use correct with one audience correction whose "
            "replacement is the achieved audience value city officials. It is "
            "not augment merely because the value is newly supplied.\n"
            "- Use augment only for additive requirements.\n"
            "- Use redirect_and_realign only when the governing objective, "
            "scope, or required outcome changes, such as changing a brief into "
            "a launch checklist. 'Instead of a brief, create a launch checklist' "
            "is redirect_and_realign even when an unrelated hold is active. "
            "Classify every current public selector as retained, superseded, "
            "or unresolved.\n"
            "- A redirect remains the same objective identity unless the user "
            "explicitly requests a new, separate, derived, distinct, or "
            "independent objective. In particular, 'instead of X, do Y' alone "
            "uses identity_disposition same_objective.\n"
            "- Realignment classifications require evidence from the redirecting "
            "contribution. Retain only a selector whose continued applicability "
            "the contribution establishes; supersede only a selector the "
            "contribution invalidates; classify every other current selector as "
            "unresolved. Do not infer applicability from plausibility.\n"
            "- Exact example: with a bound Cedar brief, 'Instead of a brief, "
            "create a launch checklist for Cedar' requires operation "
            "redirect_and_realign, objective 'Create a launch checklist for "
            "Cedar', project retained because Cedar is explicit, and color, "
            "deadline, audience, and budget unresolved because their checklist "
            "applicability was not stated. No current selector is superseded by "
            "that sentence alone.\n"
            "- To resolve post-redirection applicability, use correct. Put a "
            "retained fact or supplied value that is now achieved in "
            "promote_selectors. Put a retained requirement whose applicability "
            "is confirmed but whose content remains non-achieved in "
            "resolved_applicability_selectors. Put inapplicable unresolved "
            "selectors in resolved_selectors or corrections with a null "
            "replacement.\n"
            "- Exact applicability-clarification example: after a redirect has "
            "left deadline, budget, color, and audience unresolved, 'Keep "
            "Monday and the budget summary, but drop the color and audience "
            "requirements' uses correct; put deadline in promote_selectors, "
            "put budget in resolved_applicability_selectors because the budget "
            "summary is still required and remains non-achieved, use "
            "null-replacement corrections for color and audience, and leave "
            "direct item arrays empty.\n"
            "- Use branch with a short target_branch name for an alternate "
            "line or named version of the current work. 'Prepare an executive "
            "version' means branch with target_branch executive, not a "
            "read-only operation and not redirect_and_realign. Use merge with "
            "only host-advertised branch aliases explicitly named by the user.\n"
            "- Branch creates a new alternate line; it never selects or "
            "recreates a name already listed in available_branch_aliases. When "
            "an exact causal binding already names the bound existing branch, "
            "apply an additive request to that binding with augment or continue, "
            "and apply a replacement with correct. For example, 'Add a "
            "deployment note to the earlier technical version' with an exact "
            "technical binding is augment, not branch.\n"
            "- Use derive only for a new objective based on admitted source "
            "material and list that material in selected_selectors.\n"
            "- Explain, verify, and reconstruct are read-only path operations.\n"
            "- Explicit undo, reverse, or restore requests use reverse, not "
            "correct. 'Undo the deadline change' can target deadline. 'Undo my "
            "last correction' uses reversal_selector 'last correction', which "
            "the host resolves mechanically against the admitted path. 'Change "
            "it back' is unresolved and must not guess a selector.\n"
            "- Use resume_after_interruption only when the host has supplied "
            "an exact interrupted attempt outside this proposal, represented by "
            "interrupted_attempt_available. A request to resume from the last "
            "admitted state without accepting interrupted work uses this "
            "operation and introduces no semantic material.\n"
            "- When an active hold exists and the user supplies the missing "
            "boundary contribution, use resume_suspended. Put supplied values "
            "in achieved_items and name the corresponding prior unresolved "
            "selectors in resolved_selectors.\n"
            "- If interpretation is materially ambiguous, list the ambiguity "
            "in unresolved_interpretation rather than guessing.\n"
            "- Never turn prior presentation prose into state.\n"
            "- Current achieved and non-achieved semantic items are authoritative "
            "for mutable field values. An admitted correction may supersede a "
            "value repeated in older required-outcome prose; do not report that "
            "as ambiguity. Use the admitted path when asked why it changed.\n"
            "- Extract only facts or obligations stated by the user or already "
            "present in the supplied current state.\n"
            "- Model domain content, not conversational actions. A request to "
            "ask for an undecided field creates one non-achieved item for that "
            "field; it does not create achieved query, request, or flag items.\n"
            "- Selectors name the domain field itself using the shortest "
            "conventional noun, such as project, color, deadline, or audience. "
            "Do not prefix it with the objective type and do not encode an "
            "action in it. A named work item in a phrase such as 'a brief for "
            "Cedar' is an achieved project fact, not only objective prose.\n"
            "- Materialize every explicit assignment or assertion needed by "
            "the operation as an achieved item, introduced item, or "
            "correction; do not merely repeat it in rationale.\n"
            "- On start, materialize every directly named domain value from "
            "the current contribution even when it also appears in objective "
            "prose. For example, 'The project is Cedar' requires an achieved "
            "item with selector project and value Cedar.\n"
            "- Materialize every explicitly required but undecided input as a "
            "non-achieved item. Words such as undecided, unknown, unspecified, "
            "unresolved, pending, TBD, or 'not decided' describe absence of a "
            "value; they are never supplied achieved values. Keep value empty "
            "and describe what remains needed in text.\n"
            "- Each achieved_items, non_achieved_items, or introduced_items "
            "entry must be an object with selector, kind, value, and text. "
            "Use a stable concise selector, and put the semantic content in "
            "value or text; at least one of value or text must be non-empty.\n"
            "- A selector may occur at most once across achieved_items, "
            "non_achieved_items, and introduced_items. In particular, an "
            "undecided selector belongs only in non_achieved_items and must not "
            "also be copied into achieved_items.\n"
            "- Each corrections entry must have target_selector, replacement, "
            "and rationale. Replacement is either null for removal or one "
            "complete semantic item object as defined above.\n"
            "- For start, populate objective, required_outcome, achieved_items, "
            "and non_achieved_items only; leave all selector-control, "
            "correction, realignment, branch, merge, and reversal fields empty.\n"
            "- Keep required_outcome as a stable completion criterion. Do not "
            "repeat mutable values already represented by achieved or "
            "non-achieved items, because later admitted corrections change "
            "those values without changing the governing objective.\n"
            "- For correct, target exact current selectors in corrections, "
            "promote_selectors, resolved_selectors, or "
            "resolved_applicability_selectors. A replacement preserves the "
            "target selector. Leave direct and realignment item arrays empty.\n"
            "- For resume_suspended, represent newly supplied domain values in "
            "achieved_items and put the prior unresolved selectors they satisfy "
            "in resolved_selectors. Do not restate unrelated current items.\n"
            "- For augment or continue, represent only genuinely added domain "
            "content in achieved_items or non_achieved_items and do not "
            "restate current items.\n"
            "- Exact augmentation example: when the current state already has "
            "project, color, deadline, and audience, and the user says "
            "'Augment the current plan with an unresolved budget summary "
            "requirement', use augment, leave achieved_items empty, and put "
            "only one new requirement in non_achieved_items: selector budget, "
            "empty value, and text stating that the budget summary remains "
            "unresolved. Do not copy project, color, deadline, or audience.\n"
            "- For redirect_and_realign, put every exact current selector in "
            "affected_selectors and partition it exactly once among retained, "
            "superseded, and unresolved selectors. Use introduced_items only "
            "for genuinely new domain content.\n"
            "- For branch, populate only target_branch. For merge, populate "
            "only merge_branch_aliases using advertised aliases.\n"
            "- For explain, verify, reconstruct, and safe resumption without "
            "new user content, leave every semantic-change field empty.\n"
            "- For reverse, set only an explicitly named reversal_selector. "
            "Use the same explicit generic phrase the user supplied: last "
            "correction or latest correction. If the target is merely 'it' or "
            "otherwise ambiguous, leave reversal_selector empty and report "
            "unresolved_interpretation instead of inferring a recent change.\n"
            "- Before returning, clear every field that the chosen operation "
            "does not permit. Do not copy current state into semantic arrays.\n"
            "- Use empty arrays for fields that do not apply. Never leave the "
            "output shape's placeholder values in the response.\n\n"
            "Bounded planning context:\n"
            + json.dumps(
                context.public_payload(),
                indent=2,
                sort_keys=True,
                ensure_ascii=True,
            )
        )
        raw_result = self.propose_json(prompt, _PLAN_SCHEMA)
        payload, receipt = _json_result(raw_result)
        if not isinstance(payload, Mapping):
            raise ConversationPlanningError(
                "The conversation planner returned no structured proposal."
            )
        return ConversationPlanningResult(
            proposal=ConversationPlanProposal.from_dict(payload),
            receipt=receipt,
        )


@dataclass(frozen=True, slots=True)
class JsonConversationRenderer:
    """Render admitted state through an injected structured provider."""

    propose_json: JsonProposalCallable

    def render(self, context: ConversationRenderContext) -> ConversationRenderResult:
        prompt = (
            "Answer the user from the admitted governed state and path below. "
            "Treat current state as authoritative for current facts. Use path "
            "artifacts only when the question asks about history, explanation, "
            "verification, reconstruction, or reversal. Do not invent facts, "
            "and do not claim the objective is complete while non-achievedness "
            "remains. Return a concise conversational answer.\n\n"
            + json.dumps(
                context.public_payload(),
                indent=2,
                sort_keys=True,
                ensure_ascii=True,
            )
        )
        raw_result = self.propose_json(
            prompt,
            _RENDER_SCHEMA,
        )
        payload, receipt = _json_result(raw_result)
        answer = str(payload.get("answer", "")).strip()
        return ConversationRenderResult(
            text=answer or context.default_text,
            receipt=receipt,
        )


_SEMANTIC_ITEM_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "selector": {
            "type": "string",
            "description": (
                "Shortest canonical domain-field noun, such as project, "
                "color, deadline, or audience. Never encode an action or a "
                "relational phrase such as brief_for."
            ),
        },
        "kind": {
            "type": "string",
            "description": (
                "Semantic category, normally fact or requirement."
            ),
        },
        "value": {
            "type": "string",
            "description": (
                "Concise supplied value. For non-achieved material this is "
                "empty; absence markers such as undecided, unknown, pending, "
                "or TBD are not values."
            ),
        },
        "text": {
            "type": "string",
            "description": (
                "Natural-language semantic content; empty only when value "
                "carries the content."
            ),
        },
    },
    "required": ["selector", "kind", "value", "text"],
}

_CORRECTION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "target_selector": {
            "type": "string",
            "description": "Existing public selector to replace or remove.",
        },
        "replacement": {
            "description": (
                "Replacement semantic item, or null when removing the target."
            ),
            "anyOf": [_SEMANTIC_ITEM_SCHEMA, {"type": "null"}],
        },
        "rationale": {
            "type": "string",
            "description": "Why the explicit correction applies.",
        },
    },
    "required": ["target_selector", "replacement", "rationale"],
}

_STRING_ARRAY_SCHEMA: dict[str, Any] = {
    "type": "array",
    "items": {"type": "string"},
}

_PLAN_SCHEMA: dict[str, Any] = {
    "title": "RealizedConversationPlan",
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "schema_version": {
            "type": "string",
            "enum": [PLANNING_SCHEMA_VERSION],
        },
        "operation": {
            "type": "string",
            "enum": [item.value for item in ConversationOperation],
            "description": (
                "Single operation that best realizes this turn. Explicit undo "
                "or restore requests are reverse; alternate named versions are "
                "branch; an explicitly bound interrupted-attempt resume is "
                "resume_after_interruption; change/move/set/replace/remove/drop "
                "instructions are correct; an explicit objective replacement "
                "such as 'instead of X, do Y' is redirect_and_realign despite "
                "unrelated active holds and is never start; "
                "explain/verify/reconstruct are read-only only."
            ),
        },
        "objective": {
            "type": "string",
            "description": (
                "Non-empty objective for start, derive, or "
                "redirect_and_realign; otherwise empty."
            ),
        },
        "required_outcome": {
            "type": "string",
            "description": (
                "Non-empty completion condition for start, derive, or "
                "redirect_and_realign; otherwise empty."
            ),
        },
        "achieved_items": {
            "type": "array",
            "items": _SEMANTIC_ITEM_SCHEMA,
            "description": (
                "Facts whose values the user actually supplied, including "
                "names, dates, colors, and satisfied requirements. Include "
                "every supplied assignment; never put an undecided field here, "
                "and never duplicate a selector from non_achieved_items. Empty "
                "for branch, merge, correct, redirect_and_realign, reverse, and "
                "all read-only operations."
            ),
        },
        "non_achieved_items": {
            "type": "array",
            "items": _SEMANTIC_ITEM_SCHEMA,
            "description": (
                "Required fields for which the user supplied no value. Treat "
                "undecided, unknown, unspecified, unresolved, pending, TBD, and "
                "not decided as no value, with an empty value string. If the "
                "prompt supplies a real value, the field belongs in "
                "achieved_items. Never duplicate a selector from "
                "achieved_items. Empty for branch, merge, correct, "
                "redirect_and_realign, reverse, and all read-only operations."
            ),
        },
        "selected_selectors": {
            **_STRING_ARRAY_SCHEMA,
            "description": (
                "Only for derive: current selectors chosen as source "
                "material. Empty for every other operation."
            ),
        },
        "promote_selectors": {
            **_STRING_ARRAY_SCHEMA,
            "description": (
                "Only for correct: existing unresolved selectors promoted "
                "into achieved state. Empty for every other operation."
            ),
        },
        "resolved_selectors": {
            **_STRING_ARRAY_SCHEMA,
            "description": (
                "For correct or resume_suspended: existing unresolved selectors "
                "removed as resolved. Empty for every other operation."
            ),
        },
        "resolved_applicability_selectors": {
            **_STRING_ARRAY_SCHEMA,
            "description": (
                "Only for correct after realignment: existing selectors whose "
                "applicability is now confirmed while the represented "
                "requirement remains non-achieved. Empty for every other "
                "operation."
            ),
        },
        "corrections": {
            "type": "array",
            "items": _CORRECTION_SCHEMA,
            "description": (
                "Only for correct: explicit replacements or removals. Empty "
                "for every other operation."
            ),
        },
        "affected_selectors": {
            **_STRING_ARRAY_SCHEMA,
            "description": (
                "Only for redirect_and_realign: every current selector, each "
                "of which must appear in exactly one classification array."
            ),
        },
        "retained_selectors": {
            **_STRING_ARRAY_SCHEMA,
            "description": (
                "Only for redirect_and_realign: affected current selectors "
                "known to remain applicable."
            ),
        },
        "superseded_selectors": {
            **_STRING_ARRAY_SCHEMA,
            "description": (
                "Only for redirect_and_realign: affected current selectors "
                "known to be invalidated."
            ),
        },
        "unresolved_selectors": {
            **_STRING_ARRAY_SCHEMA,
            "description": (
                "Only for redirect_and_realign: affected current selectors "
                "whose applicability is not yet known."
            ),
        },
        "introduced_items": {
            "type": "array",
            "items": _SEMANTIC_ITEM_SCHEMA,
            "description": (
                "Only for redirect_and_realign: genuinely new semantic items. "
                "Empty for every other operation."
            ),
        },
        "identity_disposition": {
            "type": "string",
            "enum": [item.value for item in ConversationIdentityDisposition],
            "description": (
                "Whether objective identity continues or changes. A redirect "
                "uses same_objective unless the user explicitly requests a "
                "new, separate, derived, distinct, or independent objective."
            ),
        },
        "target_branch": {
            "type": "string",
            "description": (
                "Only for branch, or a branching realignment: short new branch "
                "alias not already listed in available_branch_aliases. Preparing "
                "an executive or technical version of current work is branch "
                "only when it creates a new alternate line, "
                "not redirect_and_realign. Empty otherwise."
            ),
        },
        "merge_branch_aliases": {
            **_STRING_ARRAY_SCHEMA,
            "description": (
                "Only for merge: advertised branch aliases to merge. Empty "
                "otherwise."
            ),
        },
        "reversal_selector": {
            "type": "string",
            "description": (
                "Only for reverse: an unambiguous public selector explicitly "
                "named by the user, or the explicit phrase last correction or "
                "latest correction. Preserve whichever generic phrase the user "
                "used. A vague pronoun such as it is ambiguous, so this is "
                "empty and unresolved_interpretation explains the ambiguity."
            ),
        },
        "unresolved_interpretation": {
            **_STRING_ARRAY_SCHEMA,
            "description": (
                "Material ambiguities that prevent safe interpretation; empty "
                "when the turn is unambiguous."
            ),
        },
        "rationale": {
            "type": "string",
            "description": "Concise reason for the proposed operation.",
        },
    },
    "required": [
        "schema_version",
        "operation",
        "objective",
        "required_outcome",
        "achieved_items",
        "non_achieved_items",
        "selected_selectors",
        "promote_selectors",
        "resolved_selectors",
        "resolved_applicability_selectors",
        "corrections",
        "affected_selectors",
        "retained_selectors",
        "superseded_selectors",
        "unresolved_selectors",
        "introduced_items",
        "identity_disposition",
        "target_branch",
        "merge_branch_aliases",
        "reversal_selector",
        "unresolved_interpretation",
        "rationale",
    ],
}

_RENDER_SCHEMA: dict[str, Any] = {
    "title": "RealizedConversationRendering",
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "answer": {
            "type": "string",
            "description": (
                "Concise answer grounded only in the supplied admitted result."
            ),
        }
    },
    "required": ["answer"],
}


def _items(value: Any) -> tuple[SemanticItemProposal, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(
        item
        for raw in value
        if isinstance(raw, Mapping)
        and (item := SemanticItemProposal.from_dict(raw)).selector
    )


def _corrections(value: Any) -> tuple[CorrectionProposal, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(
        item
        for raw in value
        if isinstance(raw, Mapping)
        and (item := CorrectionProposal.from_dict(raw)).target_selector
    )


def _strings(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(
        dict.fromkeys(
            item
            for raw in value
            if (item := str(raw).strip())
        )
    )


def _json_result(
    value: Mapping[str, Any] | AdvisoryJsonResult,
) -> tuple[Mapping[str, Any], dict[str, Any]]:
    if isinstance(value, AdvisoryJsonResult):
        return value.payload, dict(value.receipt)
    if isinstance(value, Mapping):
        return value, {}
    raise ConversationPlanningError(
        "The conversation provider returned neither JSON nor a JSON result."
    )


def _public_items(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, (list, tuple)):
        return []
    result: list[dict[str, str]] = []
    for raw in value:
        if not isinstance(raw, Mapping):
            continue
        payload = raw.get("payload")
        if not isinstance(payload, Mapping):
            continue
        selector = str(payload.get("semantic_key", "")).strip()
        if not selector:
            continue
        result.append(
            {
                "selector": selector,
                "kind": str(raw.get("kind", "")),
                "value": str(payload.get("value", "")),
                "text": str(payload.get("text", "")),
            }
        )
    return result


def _public_holds(state: Mapping[str, Any]) -> list[dict[str, Any]]:
    public_item_ids = {
        str(raw.get("item_id", ""))
        for collection in ("achieved", "non_achievedness")
        for raw in state.get(collection, ())
        if isinstance(raw, Mapping)
        and isinstance(raw.get("payload"), Mapping)
        and str(raw["payload"].get("semantic_key", "")).strip()
    }
    result: list[dict[str, Any]] = []
    for raw in state.get("holds", ()):
        if not isinstance(raw, Mapping):
            continue
        if str(raw.get("disposition", "remain_held")) != "remain_held":
            continue
        unresolved = raw.get("unresolved_semantic_object", {})
        if not isinstance(unresolved, Mapping):
            continue
        unresolved_id = str(unresolved.get("item_id", ""))
        if (
            unresolved_id not in public_item_ids
            and not str(unresolved.get("semantic_key", "")).strip()
        ):
            continue
        result.append(
            {
                "hold_id": str(raw.get("hold_id", "")),
                "unresolved_semantic_object": dict(unresolved),
                "resume_predicate": dict(raw.get("resume_predicate", {})),
            }
        )
    return result


def _selectors_for_ids(
    state: Mapping[str, Any],
    item_ids: Any,
) -> list[str]:
    selected_ids = {str(item) for item in item_ids or ()}
    result: list[str] = []
    for collection in ("achieved", "non_achievedness"):
        for raw in state.get(collection, ()):
            if not isinstance(raw, Mapping):
                continue
            if str(raw.get("item_id", "")) not in selected_ids:
                continue
            payload = raw.get("payload")
            if isinstance(payload, Mapping):
                selector = str(payload.get("semantic_key", "")).strip()
                if selector:
                    result.append(selector)
    return result


__all__ = [
    "AdvisoryJsonResult",
    "ConversationIdentityDisposition",
    "ConversationOperation",
    "ConversationPlanProposal",
    "ConversationPlanner",
    "ConversationPlanningContext",
    "ConversationPlanningError",
    "ConversationPlanningResult",
    "ConversationRenderContext",
    "ConversationRenderResult",
    "ConversationRenderer",
    "CorrectionProposal",
    "JsonConversationPlanner",
    "JsonConversationRenderer",
    "PLANNING_PROMPT_VERSION",
    "PLANNING_SCHEMA_VERSION",
    "RENDERING_PROMPT_VERSION",
    "RENDERING_SCHEMA_VERSION",
    "SemanticItemProposal",
]
