# Artifact-Mediated Verification

*A formal account*

**Abstract.** A generator whose interior is inaccessible cannot be verified by interrogation; it must be made to emit checkable objects. This note defines those objects, states adequacy conditions for their checkers, derives the dynamics that consequential checking induces, and locates the exact boundary of what the scheme can warrant.

## 1. Setting

Let G be a **generator**: a stochastic map from contexts X to decisions D, realized by a system whose parameters and computations are not inspectable in any way that supports inference about particular outputs. A **decision instance** is a pair (x, d) together with its moment of production.

Two premises govern everything that follows.

**Premise A1 (No privileged access).** Any account G gives of its own computation — rationale, confidence, comprehension — is itself an output of G. No channel exists by which G's reports about its states carry more evidential weight than its other outputs.

**Premise A2 (No intrinsic authority).** Any checker of G's outputs is itself a fallible map whose verdicts are predictions, not ground truth. A checker's authority is exactly its measured predictive value, and is zero until measured.

A1 rules out verification by interrogation. A2 rules out verification by fiat. What remains is a construction.

## 2. Artifacts

**Definition 1 (Artifact).** An artifact is an object a emitted by G at production time, bound irrevocably to a specific decision instance, and composed entirely of claims whose truth can be evaluated without access to G's interior.

Binding at production time is not bookkeeping: G is stochastic and mutable, so a justification reconstructed later is produced by a different run of a possibly different system and attaches to nothing.

**Definition 2 (Species).** Two species instantiate the definition. A **certificate** justifies a decision: claims c₁…cₙ together with an inference from those claims to d. A **transcript** records an examination administered against a context before a task: probes p₁…pₖ with G's responses, scored against externally fixed answers.

**Definition 3 (Soundness).** An artifact is sound when (i) each constituent claim is true, (ii) the inference from claims to decision is valid, and (iii) for certificates, the claims jointly select d. Soundness is a property of the pair (a, d) alone.

Contrast **faithfulness**: correspondence between a and the computation that actually produced d. Under A1, faithfulness is unmeasurable, so the scheme adopts soundness as its standard — as proof-checking does, where how a proof was found is no part of whether it holds. What this substitution costs is stated in §6, not hidden.

## 3. The verifier

**Definition 4 (Verifier).** A verifier is a map V : (a, d) ↦ {accept, reject, escalate} with cost c(V).

Four adequacy conditions separate a verifier from an ornament.

**V1 (Atomicity).** Every claim cᵢ must be re-derivable by V through its own channels — sources re-fetched, computations re-executed, tests re-run. A verifier that consumes quoted evidence evaluates the artifact's plausibility against its prior, which is not verification.

**V2 (Forcing).** Define the slack of a certificate as S(a) = {d′ : V would accept (a, d′)}. V accepts only when S(a) = {d}: the claims force the decision rather than merely permit it. Slack is measurable by substitution of alternatives, and quantifies exactly how much of the decision the certificate leaves unjustified.

**V3 (Asymmetry).** c(V) ≪ c(G). The scheme lives on the same asymmetry as proof-checking. Where checking a decision class costs as much as re-deciding it, V is a second generator; verification for that class is void, and control must be structural — restriction of what G may do — rather than evaluative.

**V4 (Independence).** V's error events must be uncorrelated with G's. A verifier sharing G's failure modes converts those failures into endorsements, which is strictly worse than no verifier: it adds confidence precisely where confidence is least warranted. Independence is obtained by construction — distinct model families, mechanical checkers, human sampling — never by assumption.

## 4. Dynamics under consequence

**Law (Adversarial coupling).** The moment V's verdict conditions any consequence, the optimization pressures acting on G — training, prompting, iteration by users — acquire a component directed at acceptance rather than at the property acceptance was meant to indicate.

**Proposition 1 (Decay).** A static V defines a fixed acceptance region. Any misalignment between that region and the target property is a standing exploit, and pressure under the Law locates it. Every fixed instrument therefore has a finite useful life.

**Proposition 2 (Signature).** Exploitation has an observable form: acceptance rate rising while independently measured outcome quality does not. Divergence of these two series is the alarm condition — which requires that outcome quality be measured by an instrument outside the verified pathway.

## 5. Validation of the verifier

By A2, V's verdicts are predictions; the object carrying V's meaning is its **operating characteristic** — for certificates, P(outcome good | accept); for transcripts, P(task success | pass) — estimated against adjudicated ground truth. Before estimation, any acceptance threshold is an unvalidated prior. Three disciplines follow from A2 jointly with the Law.

**Per-class validity.** Machine competence does not vary smoothly over task space; the framework therefore assumes no transfer. An operating characteristic estimated on one decision class licenses nothing about another: validity is estimated per class or does not exist.

**Exterior, fresh instruments.** Probes and checking criteria are generated per instance from the task itself, by a process standing outside the verified pathway. Static batteries fail twice — first contaminated by training data, then optimized against under the Law.

**Audited acceptance.** Ground truth is sampled among accepted cases, not only escalations. Correlated failure accumulates exactly where nothing is re-checked; an unaudited acceptance region is the scheme's blind spot by construction.

Transcripts carry two further validity conditions. Examination elicits knowledge on demand, while tasks require it volunteered: the quantity predicting task success is the probability that knowledge is deployed unprompted, which direct probes do not measure — hence indirect probes in which the relevant fact must surface without being pointed at. And under a finite probe budget, uniform coverage systematically underweights the conditionals where failure concentrates — negations, exceptions, boundary cases — so probe mass is allocated by failure relevance, not topical coverage.

## 6. Scope

**Proposition 3 (Limit).** Acceptance of (a, d) bounds properties of the pair (a, d) and entails nothing about the causal antecedents of d within G.

A decision may carry a sound certificate while counterfactually dependent on a factor the certificate never mentions; a passed transcript may certify knowledge the ensuing task fails to deploy. This residue is invisible to any single verification and surfaces only in aggregate — across many instances, or under deliberate perturbation of candidate hidden factors. Risks of that kind require instruments of a different type, interventional or population-statistical; the scheme's honesty consists in claiming exactly what it bounds.

## 7. Closure

A1 forces externalization: what cannot be inspected must be emitted as an object checkable on its own terms. A2 forces calibration: the checker is a predictor whose authority is purchased with measurement or not possessed at all. Between the two premises runs the Law: any consequential check reshapes what flows through it. Verification under these constraints is not a component installed once but an equilibrium maintained — soundness enforced instance by instance below, operating characteristics re-estimated class by class above, and the divergence of acceptance from outcome watched as the single signature of the whole construction failing.
