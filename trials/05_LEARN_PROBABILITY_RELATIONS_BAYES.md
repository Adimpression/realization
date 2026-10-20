# Probability Relations 05 — Bayes Update

This document teaches how a conditional relation can be reversed by preserving the same joint event from two directions.

The point is to preserve the semantic relation between prior belief, evidence likelihood, evidence prevalence, and posterior belief.

## 1. Reusable substrate

When one conditional quantity is transformed into its reverse-direction counterpart through a shared joint relation, the reusable family is inverse conditional update.

The reusable formula is:

$$ u = \frac{\ell \cdot p}{e} $$

Where:

* input: `\ell` = likelihood-like term
* input: `p` = prior-like term
* input: `e` = evidence-normalizing term
* output: `u` = updated belief

This family should be reused when a later relation says that belief about a cause is updated after observing evidence.

## 2. Bayes' theorem

Bayes' theorem is an inverse-conditional-update relation.

The reusable formula is:

$$ P(A \mid B) = \frac{P(B \mid A) \cdot P(A)}{P(B)} $$

Where:

* input: `P(B \mid A)` = likelihood
* input: `P(A)` = prior
* input: `P(B)` = evidence probability
* output: `P(A \mid B)` = posterior

This relation reuses the earlier inverse-conditional-update family with probability-specific quantities.

## 3. Reusing earlier lessons

This lesson reuses several earlier structures:

* `P(B \mid A)` is itself a conditional-restriction relation
* `P(A)` and `P(B)` may be formed through ratio relations
* `P(B)` may itself be assembled from additive cases in more advanced decompositions

So Bayes' theorem is not isolated. It is a structured reuse of prior reusable forms.

## 4. Distinguishing the relation

Bayes' theorem does not merely restate conditional probability. It changes direction.

* `P(B \mid A)` asks: how likely is evidence if the cause is true?
* `P(A \mid B)` asks: how likely is the cause after the evidence is seen?

If a prompt asks for diagnosis, inference, or posterior belief, do not confuse forward likelihood with backward belief.

## 5. One-sentence summary

Inverse conditional update is a reusable substrate in which conditional direction is reversed by preserving the same shared event structure and renormalizing by evidence.
