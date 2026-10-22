# Resumption Expanded

*A worked account of state, path, and non-achievedness across reductions*

## 1. Purpose

This document is the explanatory companion to
[Resumption](RESUMPTION.md). The canonical document states the theory in pure
form. This document makes its distinctions concrete through one continuing
scenario.

The scenario is deliberately simple because the difficulty does not arise from
the subject matter. It arises from deciding what a later reduction is actually
continuing.

## 2. Initial inlet

The first inlet is:

> Create a brief for Cedar, use blue, due Friday.

This inlet introduces an objective and several candidate facts:

- the objective is to create a brief;
- the project is Cedar;
- the selected color is blue;
- and the deadline is Friday.

Suppose the intended audience is required for a complete brief but has not been
provided. The resulting realization state can therefore distinguish what is
already achieved from what remains non-achieved:

```text
Achieved:
  project = Cedar
  color = blue
  deadline = Friday

Non-achieved:
  audience is undetermined
```

The original sentence is part of the conversation history. The admitted facts
and unresolved audience form the state from which a later reduction can
continue.

## 3. First correction

The next inlet is:

> Change blue to green.

This is not merely another sentence to append. It proposes a transition in the
existing state. If admitted, the transition establishes green as current and
supersedes blue:

```text
Current achieved state:
  project = Cedar
  color = green
  deadline = Friday

Current non-achievedness:
  audience is undetermined

Provenance:
  blue was established by the first inlet
  green superseded blue through the second inlet
```

Blue remains historically real. It does not remain currently active. This is
why history and current state cannot be treated as the same representation.

## 4. Second correction

The third inlet is:

> Move the deadline to Monday.

If admitted, Monday supersedes Friday. The state now becomes:

```text
Current achieved state:
  project = Cedar
  color = green
  deadline = Monday

Current non-achievedness:
  audience is undetermined

Provenance:
  blue was superseded by green
  Friday was superseded by Monday
```

The conversation now contains blue, green, Friday, and Monday. The current
state contains only green and Monday. The reduction path retains both
transitions. The unresolved audience remains non-achievedness throughout.

These are four distinct representations:

| Representation | What it contains |
| --- | --- |
| Conversation history | The three inlets in their original order |
| Reduction path | The transitions from blue to green and Friday to Monday |
| Current achieved state | Cedar, green, and Monday |
| Current non-achievedness | The still-undetermined audience |

## 5. Ordinary resumption

Suppose processing stops after the third inlet and later resumes. The next
reduction ordinarily needs a projection equivalent to:

```text
Objective: complete the Cedar brief
Current achieved state: Cedar; green; Monday
Current non-achievedness: audience is undetermined
Provenance references: the admitted correction transitions
```

It does not ordinarily need blue and Friday as candidate current values. Their
presence in the transcript does not make them active facts. Replaying the
transcript without supersession semantics would force the next reduction to
rediscover which values are current and could allow obsolete values to compete
with admitted state.

The projection is therefore not a summary chosen merely to save tokens. It is
the explicit representation of what the next reduction is entitled to treat as
current.

## 6. Interruption

Suppose a reduction begins to determine the missing audience. It develops
`city officials` as a candidate, but processing is interrupted before that
candidate is validated and admitted.

The interruption does not change the semantic state:

```text
Current achieved state:
  project = Cedar
  color = green
  deadline = Monday

Current non-achievedness:
  audience is undetermined

Unfinished work:
  city officials is an unaccepted candidate audience
```

The unfinished candidate can remain available in the path and provenance. It
does not become the current audience, and the missing-audience obligation is not
discharged. If reduction later resumes without another inlet, it resumes from
the same achieved state and non-achievedness.

## 7. Augmentation

Before reduction resumes, the next inlet is:

> Also include a budget summary.

This is an augmentation. It adds a requirement without withdrawing the Cedar
brief, green, Monday, or the unresolved audience:

```text
Current achieved state:
  project = Cedar
  color = green
  deadline = Monday

Current non-achievedness:
  audience is undetermined
  budget summary content is undetermined
```

The addition may eventually affect layout, evidence needs, or completion. Those
are consequences to determine separately. They are not implicit withdrawals or
redirections contained in the augmentation itself.

## 8. Redirection

After that augmentation, suppose another inlet says:

> Instead of a brief, create a launch checklist for Cedar.

This changes the intended direction. Continuing to produce the brief unchanged
would no longer follow the governing request. But the redirection alone does not
decide which details of the prior state remain applicable to the checklist.

Before further reduction, the existing achieved state and non-achievedness must
therefore be reconciled with the launch-checklist direction.

## 9. Realignment

Realignment can immediately establish some relationships:

```text
Retained:
  project = Cedar

Superseded active direction:
  create a brief

Introduced active direction:
  create a launch checklist

Applicability still undetermined:
  color = green
  deadline = Monday
  audience is undetermined
  budget summary is required
```

The redirection does not provide enough evidence to decide whether the
checklist should remain green, remain due Monday, target an audience, or include
the budget summary. Realignment must not silently retain or discard those
details. Their applicability remains non-achievedness.

Suppose a later inlet clarifies:

> Keep Monday and the budget summary, but drop the color and audience
> requirements.

An accepted realignment can then retain Monday and the budget-summary
requirement, supersede the active color and audience requirements, and continue
toward the launch checklist. The prior brief direction, green requirement, and
audience requirement remain in the path and provenance rather than being
erased.

The remaining examples return to the Cedar-brief state established at the end
of Section 4. The launch-checklist sequence is one illustrative continuation
from that state, not a replacement for the baseline used by every later
example.

## 10. When the path becomes necessary

The reduction path remains relevant even though it is not ordinarily projected
as current state.

If the next inlet is:

> Why is the deadline Monday?

the answer requires the path showing that the deadline was first Friday and was
then corrected to Monday.

If the next inlet is:

> Undo my last correction.

the path is needed to identify the transition being reversed and the prior
value that may be restored.

If the next inlet is:

> Change it back.

the path helps expose an ambiguity: `it` may refer to the color or the deadline,
and `back` depends on the relevant predecessor. The system should preserve that
ambiguity as non-achievedness rather than guessing from transcript proximity.

Thus the path supports explanation, verification, reversal, and reconstruction.
It does not replace current state.

## 11. Turn completion is not objective completion

Each correction can receive a valid response:

- the color was changed successfully;
- the deadline was changed successfully.

Neither response determines the missing audience. The individual turns can be
complete while the brief remains non-achieved.

If the system equates a completed reply with a completed objective, it loses
the audience obligation. A valid resumption must therefore carry forward the
remaining non-achievedness independently of whether earlier turns were answered
successfully.

## 12. Presentation is not continuation state

The system might render the third result as:

> The Cedar brief will use green and is now due Monday. Who is its audience?

That sentence is useful presentation, but it is not the authoritative state.
If a later reduction reparses it, the result depends on wording and may lose the
supersession and provenance relationships behind it.

The authoritative continuation state is the admitted structured result from
which the sentence was rendered. Presentation can change without changing what
has been achieved or what remains non-achieved.

## 13. Branching

Suppose two later inlets continue from the same state revision:

> Prepare an executive version of the Cedar brief.

and:

> Prepare a technical version of the Cedar brief.

Both can validly inherit Cedar, green, Monday, and the unresolved audience. They
need not overwrite each other. They are two branches from one causal state.

If the technical branch later changes its deadline, that transition belongs to
that branch unless a governed merge admits it elsewhere. A single linear
transcript cannot express this distinction reliably by ordering alone.

## 14. Independent continuation

Suppose the next inlet is instead:

> Plan my holiday.

This inlet should not inherit Cedar, green, Monday, or the missing audience.
Those facts may be linguistically retrievable, but they do not establish that
the holiday request continues the Cedar objective.

Continuation therefore requires explicit identity. Similarity may help locate
candidate prior state, but it cannot establish the subject, objective, revision,
and branch to be resumed.

## 15. Loosely chained reductions

Assume each individual reduction correctly enforces admission, supersession,
provenance, and non-achievedness. Those guarantees still do not automatically
survive if reductions are chained only by passing the previous prose response.

The first reduction may know that green superseded blue. Its prose output may
mention only green. The second reduction can consume that prose and produce a
plausible answer, but it no longer possesses the supersession relationship, the
supporting artifacts, the unresolved audience, or the causal revision.

Local correctness has not composed into end-to-end correctness. Composition
requires an inter-reduction contract carrying governed state relationships, not
merely a natural-language handoff.

## 16. What must survive the boundary

The scenario shows why a resumable boundary must preserve:

- that the continued subject is Cedar;
- that the objective is the Cedar brief;
- which revision and branch are being continued;
- that green and Monday are currently admitted;
- that blue and Friday are superseded;
- that the audience remains non-achieved;
- where an interruption separated accepted state from unfinished work;
- which augmentations were added without displacing existing material;
- which direction currently governs continuation;
- which prior material was retained or superseded through realignment;
- which applicability questions remain unresolved;
- and which provenance supports each transition.

The precise storage representation remains an implementation concern. The
semantic distinctions are not. If they do not cross the boundary, the next
reduction is not resuming governed state. It is inferring a new state from an
incomplete trace.
