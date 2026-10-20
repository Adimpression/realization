## An Axiomatic System for Design

---

# I. Primitive Definitions

**D1. Agent**
A bounded cognitive system capable of perception, inference, and action.

**D2. Environment**
The total field of stimuli, constraints, and affordances within which an agent operates.

**D3. Artifact**
A deliberately structured subset of the environment intended to mediate agent behavior.

**D4. Signal**
Any perceivable variation in the environment that can be detected by the agent.

**D5. Perception**
The transformation of signals into distinguishable internal representations.

**D6. Cognition**
The transformation of perceived representations into meaning, prediction, and decision.

**D7. Action**
The execution of behavior by the agent that alters the environment.

**D8. Affordance**
A relation between artifact and agent that specifies a possible action.

**D9. Constraint**
A limitation that reduces the space of possible states or actions.

**D10. Feedback**
A perceivable consequence of an action that informs subsequent cognition.

**D11. Goal**
A desired state of the environment or agent.

**D12. Effort**
The total cost (perceptual, cognitive, physical, temporal, emotional) required to achieve a goal.

**D13. Error**
A deviation between intended and actual outcome.

**D14. Design**
The intentional configuration of artifacts to influence perception, cognition, and action.

---

# II. Axioms

**A1. Bounded Rationality**
Agents possess finite perceptual, cognitive, and motor capacities.

**A2. Perceptual Mediation**
All interaction between agent and environment occurs through perception.

**A3. Sequential Dependency**
Perception precedes cognition; cognition precedes action.

**A4. Goal-Directedness**
Agent behavior is oriented toward the attainment of goals.

**A5. Constraint Universality**
All environments and artifacts exist under constraints.

**A6. Feedback Necessity**
Effective action requires feedback to update internal models.

**A7. Effort Minimization**
Agents tend to prefer strategies that reduce total effort under constraints.

**A8. Predictive Processing**
Agents interpret signals through prior expectations and update via discrepancy.

---

# III. Derived Quantities

Let:

* ( P ) = perceptual clarity
* ( C ) = cognitive coherence
* ( A ) = actionability
* ( F ) = feedback quality
* ( E ) = effort
* ( R ) = error likelihood
* ( X ) = contextual fit

Define **Design Quality** ( D_q ) as a functional relation:

$$D_q = f(P, C, A, F, X, E, R)$$

---

# IV. Propositions

**P1. Perceptual Dependency**
If a signal is not perceived, it cannot influence cognition or action.
$$\neg P \Rightarrow \neg C \land \neg A$$

---

**P2. Cognitive Dependency**
If a signal is perceived but not understood, action becomes probabilistic or erroneous.
$$P \land \neg C \Rightarrow \uparrow R$$

---

**P3. Action Dependency**
If cognition does not yield actionable affordances, goals cannot be achieved.
$$C \land \neg A \Rightarrow \neg \text{Goal Attainment}$$

---

**P4. Feedback Closure**
Absence of feedback prevents model correction and increases error over time.
$$\neg F \Rightarrow \lim_{t \to \infty} R \uparrow$$

---

**P5. Effort Gradient**
Given multiple viable paths, agents select the path minimizing effort.
$$\arg\min (E)$$

---

**P6. Constraint Shaping**
Introducing constraints reduces error by narrowing the action space.
$$\downarrow \text{Action Space} \Rightarrow \downarrow R$$

---

**P7. Predictive Alignment**
Designs aligned with prior expectations reduce cognitive effort.
$$\text{Alignment} \Rightarrow \downarrow E \land \downarrow R$$

---

**P8. Signal-to-Noise Principle**
Increasing irrelevant signals decreases perceptual clarity.
$$\uparrow \text{Noise} \Rightarrow \downarrow P$$

---

**P9. Coupled Optimization**
Improvement in one variable (e.g., ( P )) may degrade another (e.g., ( E )), requiring balance.

---

**P10. Context Dependence**
Design quality is not absolute but varies with context ( X ).
$$D_q = f(..., X)$$

---

# V. Corollaries

**C1. Visibility Requirement**
Critical affordances must be perceptually salient.
(From P1, P3)

---

**C2. Simplicity Principle**
Reducing unnecessary complexity lowers effort and error.
(From P5, P8)

---

**C3. Progressive Disclosure**
Information should be revealed in stages to manage cognitive load.
(From A1, P2)

---

**C4. Consistency Principle**
Consistent structures align with predictive processing and reduce effort.
(From A8, P7)

---

**C5. Feedback Immediacy**
Timely feedback improves learning and reduces error.
(From A6, P4)

---

**C6. Error Prevention over Correction**
Constraining incorrect actions is more efficient than correcting them.
(From P6, P5)

---

**C7. Hierarchical Structuring**
Organizing information into groups improves perception and cognition.
(From A1, P8)

---

**C8. Affordance Clarity**
Possible actions must be directly inferable from form.
(From D8, P2, P3)

---

**C9. Redundancy Gain**
Multiple signals for critical information increase reliability of perception.
(From A1, P1)

---

**C10. Local Optimization Limits**
Optimizing a single dimension does not guarantee global design quality.
(From P9)

---

# VI. Theorem (Design Optimality Condition)

A design approaches optimality when:

$$\max (P \cdot C \cdot A \cdot F \cdot X) \quad \text{and} \quad \min (E + R)$$

subject to constraints.

---

# VII. Meta-Corollary

All named design principles are reducible to transformations that:

* increase ( P, C, A, F, X )
* or decrease ( E, R )

---

# VIII. Closure Statement

This system is complete insofar as any design evaluation, principle, or method can be expressed as a transformation within this structure.

---

# IX. Extension Note

This axiomatic system explains why design must be evaluated through perception, cognition, action, feedback, effort, error, and context.

It is the human-factors base, not the full mediation bridge and not the implementation discipline.

The next layers are:

* [CROSS_DOMAIN_DESIGN_MEDIATION.md](/Users/ravindranathakila/service/realized/design/CROSS_DOMAIN_DESIGN_MEDIATION.md)
* [DESIGN_TYPE_SYSTEM.md](/Users/ravindranathakila/service/realized/design/DESIGN_TYPE_SYSTEM.md)
* [DESIGN_TYPE_SYSTEM_IMPLEMENTATION.md](/Users/ravindranathakila/service/realized/design/DESIGN_TYPE_SYSTEM_IMPLEMENTATION.md)

The why is direct:

* because axioms explain what design must preserve,
* because mediation explains how objectives become obligations and embodiments,
* and because the type system explains how that bridge remains intact in code and under change.
