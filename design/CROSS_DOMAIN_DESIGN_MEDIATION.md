# Formal Theory of Cross-Domain Design Mediation

## I. Primitive Definitions

**D1. Agent**
A bounded being capable of perception, cognition, and action.

**D2. Objective**
A desired state or outcome the agent seeks to realize, preserve, avoid, restore, or optimize.

**D3. Environment**
The total field of conditions, signals, constraints, and consequences within which the agent operates.

**D4. System**
Any organized arrangement of artifacts, processes, interfaces, and rules through which the environment is mediated.

**D5. Artifact**
A designed element of a system that participates in perception, cognition, or action.

**D6. Signal**
Any perceivable distinction available to an agent.

**D7. Intent**
A primitive mode of goal-directed engagement by an agent with a system.

**D8. Task**
An organized sequence or structure of intents directed toward an objective.

**D9. Task Morphology**
The temporal and logical form of a task, such as sequential, branching, cyclical, interrupt-driven, supervisory, collaborative, or emergency.

**D10. Interaction Invariant**
A domain-independent requirement governing how systems must support perception, cognition, and action for bounded agents.

**D11. Interaction Obligation**
A context-specific operational requirement derived from one or more interaction invariants.

**D12. Embodiment**
The material, spatial, visual, auditory, tactile, procedural, or computational realization of an interaction obligation.

**D13. Framework**
A domain-specific design language, standard, or implementation regime governing embodiment.

**D14. Framework Encoding**
The translation of interaction obligations into the forms permitted by a specific framework.

**D15. Constraint**
Any limitation on possible states, actions, embodiments, resources, safety margins, or interpretations.

**D16. Feedback**
A perceivable consequence of action that updates the agent’s understanding of system state or outcome.

**D17. Error**
A divergence between intended and actual state, action, or outcome.

**D18. Design Mediation**
The structured transformation by which objectives are translated into interaction obligations and then into embodiments.

**D19. Design Quality**
The degree to which a mediated system enables objective attainment with sufficient clarity, safety, efficiency, recoverability, and contextual fit.

---

## II. Axioms

**A1. Boundedness Axiom**
All agents possess finite perceptual, cognitive, temporal, motor, and emotional capacities.

**A2. Mediation Axiom**
Agents do not act upon systems directly, but through mediated relations of perception, interpretation, and action.

**A3. Objective Axiom**
All meaningful design evaluation is relative to one or more agent objectives.

**A4. Layered Translation Axiom**
Objectives and embodiments belong to different descriptive levels and cannot be validly mapped without mediating constructs.

**A5. Invariance Axiom**
Across domains, frameworks differ in form, but recurring requirements for intelligibility and action remain structurally invariant.

**A6. Constraint Axiom**
Every design mediation occurs under human, material, temporal, environmental, social, and regulatory constraints.

**A7. Feedback Axiom**
No sustained control, correction, or trust is possible without feedback.

**A8. Risk Axiom**
As consequence severity increases, demands on salience, constraint, redundancy, and recoverability increase.

**A9. Embodiment Plurality Axiom**
The same interaction obligation may admit multiple valid embodiments across different frameworks.

**A10. Non-Identity Axiom**
No specific framework, component library, or material vocabulary is identical with the theory of design mediation itself.

---

## III. Fundamental Sets

Let:

* ( O ) = set of objectives
* ( I ) = set of primitive intents
* ( T ) = set of task morphologies
* ( V ) = set of interaction invariants
* ( G ) = set of interaction obligations
* ( E ) = set of embodiments
* ( F ) = set of frameworks
* ( C ) = set of constraints

---

## IV. Primitive Intent Algebra

The minimal intent basis consists of:

[
I = {
\text{detect},
\text{locate},
\text{distinguish},
\text{inspect},
\text{compare},
\text{select},
\text{enter},
\text{modify},
\text{trigger},
\text{navigate},
\text{monitor},
\text{verify},
\text{confirm},
\text{interrupt},
\text{recover},
\text{coordinate},
\text{learn}
}
]

**Postulate:** Complex user activity is representable as compositions of primitive intents.

---

## V. Canonical Task Morphologies

[
T = {
\text{one_shot},
\text{sequential},
\text{branching},
\text{iterative},
\text{cyclical},
\text{continuous},
\text{interrupt_driven},
\text{supervisory},
\text{collaborative},
\text{emergency}
}
]

**Postulate:** Every task instantiates one or more task morphologies.

---

## VI. Canonical Interaction Invariants

[
V = {
\text{visibility},
\text{salience},
\text{legibility},
\text{mapping},
\text{feedback},
\text{constraint},
\text{consistency},
\text{recoverability},
\text{state_awareness},
\text{prioritization},
\text{learnability},
\text{accessibility},
\text{redundancy},
\text{responsiveness},
\text{mode_clarity},
\text{trustworthiness}
}
]

**Definition:** An interaction invariant is valid if its necessity is independent of any particular framework or material substrate.

---

## VII. Core Transformations

Define the mediation pipeline as the composition:

[
\Phi: O \rightarrow I \rightarrow T \rightarrow V \rightarrow G \rightarrow E \rightarrow F(E)
]

More explicitly:

1. **Objective Decomposition**
   [
   \phi_1: O \to \mathcal{P}(I)
   ]
   Maps objectives to required intents.

2. **Task Structuring**
   [
   \phi_2: \mathcal{P}(I) \to \mathcal{P}(T)
   ]
   Maps intents to task morphologies.

3. **Invariant Derivation**
   [
   \phi_3: \mathcal{P}(I) \times \mathcal{P}(T) \times C \to \mathcal{P}(V)
   ]
   Derives required interaction invariants.

4. **Obligation Specification**
   [
   \phi_4: \mathcal{P}(V) \times C \to \mathcal{P}(G)
   ]
   Converts invariants into operational obligations.

5. **Embodiment Generation**
   [
   \phi_5: \mathcal{P}(G) \times C \to \mathcal{P}(E)
   ]
   Produces admissible embodiments.

6. **Framework Encoding**
   [
   \phi_6: \mathcal{P}(E) \times F \to \mathcal{P}(F(E))
   ]
   Encodes embodiments within a chosen framework.

---

## VIII. Propositions

**P1. Non-Direct Mapping Proposition**
No valid design mapping exists from objectives directly to framework-specific components without mediating constructs.

[
O \not\to F(E) \quad \text{except through } \Phi
]

**P2. Intent Sufficiency Proposition**
If an objective cannot be decomposed into intents, it cannot be systematically designed for.

**P3. Morphological Dependence Proposition**
The appropriateness of an embodiment depends not only on intent, but on task morphology.

**P4. Invariant Priority Proposition**
Interaction invariants have logical priority over embodiments.

[
V \prec G \prec E
]

**P5. Cross-Domain Equivalence Proposition**
Distinct embodiments in distinct frameworks may be equivalent with respect to the same interaction obligation.

**P6. Safety Amplification Proposition**
Under high-risk conditions, obligations of salience, constraint, redundancy, and recoverability increase monotonically with consequence severity.

**P7. Feedback Necessity Proposition**
Any system supporting iterative control or supervision must instantiate feedback and state awareness.

**P8. Recoverability Proposition**
Where error cannot be fully prevented, recoverability becomes obligatory.

**P9. Framework Contingency Proposition**
A framework constrains admissible embodiments but does not determine the objective, intent, or invariant structure.

**P10. Quality Dependence Proposition**
Design quality is a function of the correctness of each transformation in the mediation pipeline.

---

## IX. Corollaries

**C1. Framework Independence Corollary**
Any bridge terminating in one framework is not a general theory of mediation.

**C2. Embodiment Plurality Corollary**
The same obligation may be realized visually, mechanically, spatially, auditorily, tactually, or procedurally.

**C3. Obligation Primacy Corollary**
Design specifications should be expressed first as obligations, not components.

**C4. Domain Adaptation Corollary**
Domain specificity enters at embodiment and encoding, not at the level of invariants.

**C5. Misdesign Corollary**
A system is misdesigned when its embodiment satisfies framework conventions while violating required interaction invariants.

**C6. Superficial Consistency Corollary**
Consistency within a framework is insufficient for design quality if the upstream mediation is invalid.

**C7. Translation Validity Corollary**
Two systems in different media may be equally valid if both preserve the same objective-relevant obligations under their constraints.

---

## X. Theorem of Proper Bridging

A design bridge is proper if and only if it satisfies all of the following:

1. It begins from objectives.
2. It decomposes objectives into intents.
3. It structures intents into task morphologies.
4. It derives domain-independent interaction invariants.
5. It specifies operational obligations from those invariants.
6. It permits multiple valid embodiments.
7. It allows framework-specific encoding only at the terminal layer.

Formally:

[
\text{Proper Bridge} \iff
(O \to I \to T \to V \to G \to E \to F(E))
\land
(V \text{ domain-independent})
\land
(E \text{ framework-plural})
]

---

## XI. Theorem of Invalid Bridging

Any system claiming to bridge objectives to design, yet mapping directly from objectives to framework artifacts, is an incomplete bridge.

[
(O \to F(E)) \Rightarrow \text{Invalid Bridge}
]

---

## XII. Design Quality Functional

Let:

* ( Cl ) = clarity
* ( Sf ) = safety
* ( Ef ) = efficiency
* ( Rc ) = recoverability
* ( Ft ) = contextual fit
* ( Tr ) = trustworthiness
* ( Er ) = error burden
* ( Co ) = total cost of effort

Then:

[
Q = \frac{Cl \cdot Sf \cdot Ef \cdot Rc \cdot Ft \cdot Tr}{Er + Co}
]

subject to:

[
Q \text{ is valid only if } \Phi \text{ is structurally correct}
]

---

## XIII. Canonical Form of Design Specification

A complete design specification must include:

1. **Objective Set** ( O )
2. **Intent Decomposition** ( \phi_1(O) )
3. **Task Morphology** ( \phi_2(\phi_1(O)) )
4. **Invariant Set** ( \phi_3(...) )
5. **Obligation Set** ( \phi_4(...) )
6. **Embodiment Candidates** ( \phi_5(...) )
7. **Framework Encoding Rule** ( \phi_6(...) )

Any specification omitting levels 2 through 5 is formally incomplete.

---

## XIV. Closure Principle

The theory is complete in form if every design problem can be represented as a problem of mediated transformation from objectives to obligations to embodiments under constraints.

---

## XV. Final Statement of the Theory

**Cross-domain design mediation is the formal transformation by which agent objectives are decomposed into intents, structured into task morphologies, translated into domain-independent interaction invariants, specified as interaction obligations, embodied in material or procedural form, and finally encoded within a particular design framework.**

**Therefore, no concrete design framework is the bridge itself; each is only a terminal encoding of a deeper, framework-independent mediation structure.**

---

## XVI. Extension Note

This theory establishes the mediation bridge.

It does not by itself specify the type discipline required to preserve that bridge across code, framework encodings, runtime evidence, and revision.

That next layer is addressed in:

* [DESIGN_TYPE_SYSTEM.md](DESIGN_TYPE_SYSTEM.md)
* [DESIGN_TYPE_SYSTEM_IMPLEMENTATION.md](DESIGN_TYPE_SYSTEM_IMPLEMENTATION.md)

The why is simple:

* because a mediation theory without a preservation discipline can still be implemented incorrectly,
* and because a typed design system is the mechanism by which the bridge remains intact while implementations and realities change.
