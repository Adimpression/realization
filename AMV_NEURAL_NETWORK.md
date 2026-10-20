# AMV and Neural Networks

*A theory note on artifact-mediated path consolidation*

**Abstract.** Neural learning and artifact-mediated verification share a common dynamic form: a production event occurs, that event is judged in context, and the judgment conditions a consequence that changes the probability of similar future productions. This note develops that correspondence while preserving an important boundary. Formal artifact-mediated verification requires externally checkable artifacts; an internal neural activation satisfies that role only when it is externalized and made independently evaluable. The more general structure is artifact-mediated selection.

## 1. The central correspondence

A neural network does not strengthen a path merely because the path was activated. The complete learning sequence is:

\[
\text{firing} \rightarrow \text{contextual judgment} \rightarrow \text{consequence} \rightarrow \text{path-strength change}
\]

The same sequence appears in artifact-mediated verification when a verdict has consequences:

\[
\text{production} \rightarrow \text{artifact check} \rightarrow \text{acceptance consequence} \rightarrow \text{generator adaptation}
\]

The act of checking does not by itself create learning. Checking becomes a learning pressure when its result changes reward, training data, selection, deployment, escalation, or some other consequence experienced by the generator.

## 2. The activation event as artifact

A neuron is a persistent component of a network. Its firing is a particular event. The event, rather than the neuron considered in isolation, is the candidate artifact.

An activation event is identified by at least:

- the neuron or feature that activated;
- its layer, position, and time;
- the input and prior state under which it activated;
- the surrounding pattern of co-activation;
- the output or action to which the activation contributed.

This context is essential because individual neurons can be polysemantic. A neuron's activation has no stable interpretation independently of the larger activation pattern in which it participates. The meaningful unit is therefore an activation event or activation trace bound to a particular production.

In the strict definition of artifact-mediated verification, an artifact must be externally checkable and composed of claims that can be evaluated without privileged access to the generator's interior. An unobserved internal firing is not such an artifact. An instrumented activation trace can become one if it is externalized, bound to the production event, and evaluated through an independent mechanism. At the broader theoretical level, however, the activation event already plays the structural role of an artifact in an artifact-mediated selection process.

## 3. Contextual judgment and credit assignment

For a connection from unit i to unit j, a simplified backpropagation update has the form:

\[
\Delta w_{ij} \propto a_i \delta_j
\]

Here, \(a_i\) records that the upstream unit participated, while \(\delta_j\) carries a downstream error or credit signal. The update is not a judgment of the firing alone. It is a judgment of the firing's contribution within a larger causal and computational context.

The same distinction appears in three-factor learning rules:

\[
\Delta w_{ij} \propto r\,a_i a_j
\]

Pre-synaptic and post-synaptic co-activation identify an eligible path. The modulatory signal \(r\), such as reward or error, determines whether that path is reinforced or weakened. Co-activation alone establishes correlation, not correctness.

This yields three distinct roles:

1. **Occurrence:** the activation trace records what participated.
2. **Judgment:** loss, reward, or another checker evaluates the resulting relation.
3. **Consequence:** plasticity changes how readily the path will recur.

A frozen artificial neural network performs the first role during inference but not the third. Repeated inference does not normally change its parameters. Learning requires an explicit update mechanism.

## 4. Structural mapping

The correspondence between neural learning and artifact-mediated verification is:

| Artifact-mediated verification | Neural system |
| --- | --- |
| Generator | Network dynamics under parameters \(\theta\) |
| Context | Input, prior state, and surrounding activation pattern |
| Decision | Output, prediction, or action |
| Artifact | Activation event or activation trace bound to the production |
| Verifier | Loss, reward, critic, test, or external checker |
| Verdict | Error, reward, acceptance, rejection, or escalation signal |
| Consequence | Parameter update, reinforcement, suppression, or selection |
| Reproduction | Re-elicitation of a similar path under a later context |

This is a structural correspondence, not an identity between all neural learning and formal AMV. Formal AMV is an epistemic discipline concerned with externally warranted decisions. Neural learning is a mechanism that changes future behavior. Their common superclass is artifact-mediated selection: emitted events are evaluated, and consequential evaluation reshapes the process that emits them.

## 5. Hardening and forgetting

A strong memory is not necessarily a separately stored fact. It is a path or attractor that is readily and robustly reactivated under relevant cues. Repeated consequential reinforcement can:

- increase the probability that a path is selected;
- widen the range of cues that activate it;
- make it resistant to competing paths;
- reduce the energy or evidence required for its reactivation;
- consolidate it across multiple representations.

A weak path is one whose probability of reactivation is low or fragile. Forgetting can arise through several mechanisms:

- later learning interferes with the weights supporting the path;
- competing paths receive stronger reinforcement;
- regularization, pruning, or decay reduces its influence;
- retrieval cues cease to reach it;
- inhibition suppresses it in the contexts where it was formerly accessible;
- deliberate unlearning applies an opposing update.

Forgetting therefore need not mean that every physical contribution of the old path has been erased. It often means that the path can no longer be reliably reconstructed from ordinary cues. Memory strength is fundamentally about retrievability and recurrence.

## 6. Strength and validity are independent

Path strength is a behavioral property. Verification validity is an epistemic property. They must not be conflated.

| | Soundly checked | Unsoundly checked |
| --- | --- | --- |
| **Strong path** | Reliable learned behavior | Entrenched error or verifier exploit |
| **Weak path** | Valid but inaccessible or undertrained knowledge | Transient noise |

A network can strongly remember something false. It can also weakly express something true. Hardening establishes reproducibility, not truth. Truth warrant depends on the quality, independence, and measured operating characteristic of the checker.

This distinction is the neural form of the second AMV premise: a checker has no intrinsic authority. If the judgment signal is defective, repeated optimization can make the defect more persistent rather than correct it.

## 7. Adversarial coupling as consolidation

Once a verifier's verdict conditions consequences, it creates a selection landscape. Paths that produce acceptance receive an advantage over paths that do not. The generator therefore becomes increasingly likely to reproduce acceptance-generating behavior.

If acceptance tracks the intended property, this process can consolidate useful behavior. If acceptance is only imperfectly aligned with that property, the same process consolidates exploitation of the verifier's acceptance region. A static verifier does not merely make repeated classification errors. Under consequential optimization, it gradually hardens the paths that reproduce those errors successfully.

This gives the AMV adversarial-coupling law a mechanistic interpretation:

1. A production activates one of several possible paths.
2. The resulting artifact enters a consequential checker.
3. The checker's verdict assigns relative advantage.
4. Credit assignment propagates that advantage into the production mechanism.
5. Future contexts are more likely to traverse the rewarded path.
6. Competing, unrewarded paths become relatively weaker and may appear forgotten.

The observable alarm remains the same: acceptance rises while independently measured outcome quality does not. In neural terms, the network is successfully consolidating a path to the verifier rather than a path to the intended property.

## 8. The causal limitation

Neither an accepted external artifact nor an observed activation trace automatically establishes the true causal antecedents of a decision. A trace may contain activations correlated with the result without showing which factors were necessary, sufficient, or counterfactually decisive.

Consequently:

- a sound certificate does not prove that the generator used the certificate's reasoning;
- a recorded firing does not prove that the firing caused the output;
- a reinforced path does not prove that the path encodes the intended concept;
- a stable behavior does not prove that its stability arises from the desired mechanism.

Causal claims require intervention, ablation, perturbation, or population-level evidence beyond observation of a single trace. This is the same boundary stated by formal AMV: verification can warrant properties of the artifact-decision pair without warranting an account of the generator's hidden causal process.

## 9. Synthesis

AMV can be understood as a form of externalized consolidation. A transient production is bound to an artifact, the artifact is judged outside the generator, and the judgment may influence which generative paths persist. Neural learning supplies the corresponding internal dynamic: contextual credit or blame alters the future accessibility of paths.

The combined theory is therefore:

\[
\text{memory strength} = \text{persistence of a consequence-shaped path under re-elicitation}
\]

while:

\[
\text{epistemic validity} = \text{measured reliability of the independent process that shaped it}
\]

The first explains how behavior becomes durable or fades. The second determines whether that durability deserves trust.
