# Intelligence

*Memory, attention, verification, and consolidation*

**Abstract.** Intelligence can be described as a recurrent process operating across two timescales. At the fast timescale, attention selects and composes a temporary path through available memory. Reflection retrospectively examines the path that was selected, while contemplation prospectively compares possible next paths and reframings. At the slow timescale, artifact-mediated verification determines which productions and meta-attentional judgments have consequences for durable state. A checked production that changes later behavior is learning; repeated support hardens a path; loss of accessibility is forgetting. This account explains how transient thought can become durable structure without treating attention, reflection, or contemplation as intrinsically authoritative.

This note builds on [Artifact-Mediated Verification](ARTIFACT_MEDIATED_VERIFICATION.md), [AMV and Neural Networks](AMV_NEURAL_NETWORK.md), and the canonical governed-reduction definitions in [Theory](THEORY.md). `THEORY.md` remains authoritative for non-achievedness, reduction, reflection, contemplation, and governance. This note supplies the higher-level intelligence synthesis and does not redefine those operations.

## 1. The recurrent form

The central cycle is:

\[
\text{memory} \rightarrow \text{attention} \rightarrow \text{production}
\rightarrow \text{meta-attention} \rightarrow \text{verification}
\rightarrow \text{consolidation}
\rightarrow \text{changed memory}
\]

Each stage has a distinct function:

- **Memory** determines which paths exist.
- **Attention** determines which available paths influence the present step.
- **Production** creates a candidate decision and its artifact.
- **Reflection** retrospectively evaluates the path actually composed.
- **Contemplation** prospectively evaluates alternate paths and reframings.
- **Verification** evaluates that artifact in the context of its production.
- **Consequence** determines what the verdict changes.
- **Consolidation** makes the consequential change available to future cycles.

No stage can substitute for another. Memory without attention remains latent. Attention without production only rearranges influence. Production without reflection cannot reconsider its actual composition. Production without contemplation cannot compare its current direction with plausible alternatives. Reflection and contemplation without verification remain fallible proposals. Verification without consequence does not teach. Consequence without persistence cannot affect later behavior.

## 2. Durable state and active state

Let \(S_t\) denote durable state at step \(t\). It contains the paths that the system can potentially recover. Let \(C_t\) denote the temporary context constructed for the current step.

Durable state and active state are not the same thing. An artifact can exist in \(S_t\) without participating in \(C_t\). Conversely, an artifact can dominate the current context without being permanently strengthened by doing so.

This distinction separates storage from use:

- **Stored** means that a path remains representable.
- **Retrievable** means that a current cue can expose it as a candidate.
- **Attended** means that it influences the current computation.
- **Consolidated** means that the result of the computation changes future durable state.

Treating these as one operation obscures both learning and forgetting.

## 3. Attention as fast path selection

Attention is a context-dependent allocation of influence. It does not determine which memories exist; it determines which of them matter now.

The neural mechanism for this temporary allocation is developed in [AMV and Neural Networks](AMV_NEURAL_NETWORK.md). At the system level, the essential property is that attentional influence is recomputed for the current context and does not by itself alter durable memory.

The same form can be expressed outside a neural network:

1. Retrieval exposes candidate artifacts.
2. Attention assigns immediate influence among those candidates.
3. The active combination becomes the context for the next reduction.

Semantic retrieval and attention are therefore related but distinct. Retrieval defines what is available for consideration. Attention determines what actually participates.

## 4. Production and the artifact

Given durable state \(S_t\), input \(x_t\), and active context \(C_t\), a generator produces a decision \(d_t\) and an artifact \(a_t\):

\[
(a_t, d_t) = G(S_t, x_t, C_t)
\]

The artifact externalizes what can be checked about that production. In a neural account, an instrumented activation trace can play this role. In a symbolic reduction account, it can be a derivation, state transition, proof object, or receipt bound to the step.

The artifact is not automatically knowledge. It is a candidate for judgment.

## 5. AMV as the consolidation gate

The verifier evaluates the artifact-decision pair:

\[
v_t = V(a_t, d_t)
\]

Verification alone does not constitute learning. Its verdict must condition a consequence:

\[
S_{t+1} = U(S_t, a_t, d_t, v_t)
\]

The system has learned when this update changes future behavior:

\[
P(d \mid x, S_{t+1}) \neq P(d \mid x, S_t)
\]

This definition does not require neural-weight modification. The adaptive substrate can be model parameters, artifact relations, rules, persistent records, or any other state that changes future productions.

The progression is therefore:

- **AMV alone:** verification.
- **AMV with consequence:** selection.
- **AMV with consequence and persistent recurrence:** learning.
- **Repeatedly supported recurrence:** path hardening.
- **Loss of future influence:** forgetting.

## 6. Stepwise intelligence

Intelligence appears when the cycle is repeated and each checked step can condition the next:

\[
S_t \rightarrow C_t \rightarrow (a_t,d_t) \rightarrow (r_t,p_t)
\rightarrow v_t
\rightarrow S_{t+1} \rightarrow C_{t+1}
\]

Here, \(r_t\) is a reflection artifact over the actual composition and \(p_t\) is a contemplation artifact over prospective paths.

The result of one production becomes part of the possibility space for another. The process is not merely a sequence of independent answers. It is a path whose intermediate artifacts alter what can be attended to and produced next.

In a reduction loop, this has a concrete interpretation:

1. Durable state supplies potentially relevant artifacts.
2. Retrieval exposes a candidate frontier.
3. Attention selects and composes the active reduction context.
4. A reduction produces a new artifact and state claim.
5. Reflection examines coherence, sufficiency, drift, and continued relevance in the actual composition.
6. Contemplation compares admissible continuations, alternatives, and reframings.
7. AMV checks the production and the resulting meta-attentional artifacts in context.
8. The verdict determines whether active or durable state changes.
9. The next reduction begins from that changed state.

The learning event is the verified state transition, not retrieval and not generation considered separately.

## 7. Reflection and contemplation as meta-attention

First-order attention asks:

> Which available artifacts should influence the current production?

Reflection and contemplation operate over that selection process itself.

### Retrospective meta-attention

Reflection examines the actual composition subset inside the current higher non-achievedness:

\[
r_t = Reflect(Not\langle X\rangle_t, C_t)
\]

It asks whether the selected path remains coherent, sufficient, relevant, appropriately scoped, and consistent with current certainty, blockers, reusable forms, and HoldOn conditions. Reflection is not privileged access to hidden model cognition. It is a new production over an externalized composition and is therefore subject to the same verification requirements as any other artifact.

### Prospective counterfactual attention

Contemplation considers plausible future allocations of attention:

\[
p_t = Contemplate(Not\langle X\rangle_t, C_t)
\]

It may continue the current decomposition, select among subordinate non-achievednesses, choose another path, move upward in abstraction, replace a malformed framing, or defer a reusable form. Contemplation expands and compares the candidate attention landscape. It does not authorize any candidate merely by proposing it.

### Causal closure law

Reflection and contemplation become part of learning only when their checked artifacts alter the next active context or durable state:

\[
V(r_t,p_t) \rightarrow U(C_{t+1},S_{t+1})
\]

If their outputs are recorded but do not affect subsequent path selection, the system has meta-cognitive observability but not causal meta-control. The artifacts exist, but the learning loop remains open.

Together, the two operations let intelligence revise not only an answer but the path by which further answers will be sought:

\[
\text{reflection} = \text{retrospective meta-attention}
\]

\[
\text{contemplation} = \text{prospective counterfactual attention}
\]

## 8. Two timescales

The architecture operates on two coupled timescales.

### Fast adaptation

Attention changes the active path without changing durable state. It supports contextual interpretation, temporary composition, and stepwise reasoning. A frozen model can perform this form of adaptation during inference.

### Slow adaptation

Consequential verification changes durable state. It determines which productions remain available to future attention. This is consolidation and therefore learning in the system-level sense.

Fast adaptation determines what the system thinks with now. Slow adaptation determines what it will be capable of thinking with later.

## 9. Hardening

A path becomes strong when relevant contexts reliably reactivate it and when its activation survives competition from alternatives. Hardening can occur through several durable changes:

- additional support connects cues to the path;
- verified derivations make the path directly reusable;
- repeated successful recurrence increases its accessibility;
- consolidation makes the path less dependent on a narrow initiating context;
- competing paths lose relative influence.

Hardening concerns reproducibility, not truth. A defective verifier can harden an erroneous path. The quality of learned intelligence therefore depends on the measured reliability and independence of the verification process.

## 10. Forgetting

Attention reveals that forgetting has at least two forms.

### Functional forgetting

The artifact remains in durable state but no longer receives enough attention to affect behavior. It exists but is inaccessible under ordinary cues.

### Structural forgetting

Durable state changes so that the artifact's influence is weakened, superseded, invalidated, disconnected, or removed.

Functional forgetting can occur without erasure. Structural forgetting changes the memory substrate itself. Both are measured by future influence, not merely by physical presence.

## 11. Attention and verification are independent

Attention answers: **What influences this production?**

Verification answers: **What about this production is warranted?**

High attention does not imply validity. A frequently attended path can be wrong. A valid artifact can remain weak because it is rarely retrieved or attended. The system must therefore preserve separate notions of:

- availability in memory;
- current attentional influence;
- verification status;
- durable path strength.

Collapsing these dimensions creates self-reinforcement. What is already easy to retrieve receives more attention; what receives more attention is produced more often; what is produced more often supplies more opportunities for acceptance; and acceptance can make it still easier to retrieve. Without an independent verifier, repetition can masquerade as knowledge.

## 12. The role of the LLM

An LLM contributes two mechanisms to this cycle:

- attention dynamically constructs the active context;
- generation proposes the next production from that context.

It may also propose reflection and contemplation artifacts. Those proposals remain generated outputs under the no-privileged-access premise. They are not made authoritative by being described as reflective, contemplative, confident, or self-critical. Non-LLM mechanisms may perform the same control operations when they can evaluate the externalized composition and candidate paths.

Neither mechanism alone means that the surrounding system has learned. A frozen LLM can attend and generate indefinitely without changing its parameters or durable external state.

The larger system learns when a checked production or meta-attentional judgment changes what later steps can retrieve, attend to, and use. The LLM can supply fast contextual proposals. Stepwise AMV supplies the disciplined route from transient production to governed active state and durable memory.

## 13. Synthesis

The combined theory is:

\[
\text{intelligence} =
\text{memory made active by attention, transformed by production,}
\text{ reconsidered through reflection and contemplation,}
\text{ and changed through consequential verification}
\]

Attention explains how durable possibilities become present thought. Reflection checks whether the actual path remains coherent. Contemplation compares plausible future paths. AMV determines which resulting artifacts may have consequences. Their recurrence explains learning:

\[
\text{learned path} =
\text{attended production} + \text{contextual verification}
+ \text{verified meta-attention} + \text{persistent consequence}
\]

Forgetting is the inverse loss of effective recurrence, either because attention can no longer recover the path or because durable state no longer supports it.

The architecture is therefore neither merely an LLM nor merely a database. It is a recurrent relation among transient attention, retrospective and prospective meta-attention, and persistent verified artifacts. Intelligence emerges when that cycle is causally closed rather than merely recorded.
