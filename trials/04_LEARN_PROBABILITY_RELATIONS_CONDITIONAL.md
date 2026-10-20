# Probability Relations 04 — Conditioning by Restriction

This document teaches how probability changes when the reference space is narrowed.

The point is to preserve the reusable semantic relation between a restricted universe and the event measured inside it.

## 1. Reusable substrate

When a quantity is recomputed inside a reduced reference frame, the reusable family is conditional restriction.

The reusable formula is:

$$ q = \frac{x \cap y}{y} $$

Where:

* input: `x \cap y` = overlap within the restriction
* input: `y` = the restricted reference basis
* output: `q`

This family should be reused when a later relation says that a quantity is measured relative to a narrowed context.

## 2. Conditional probability

Conditional probability is a conditional-restriction relation.

The reusable formula is:

$$ P(A \mid B) = \frac{P(A \cap B)}{P(B)} $$

Where:

* input: `P(A \cap B)`
* input: `P(B)`
* output: `P(A \mid B)`

This relation reuses the earlier conditional-restriction family with probability-specific quantities.

## 3. Reusing earlier lessons

The overlap term may be derived from count-based ratio formation:

$$ P(A \cap B) = \frac{n(A \cap B)}{n(S)} $$

And the conditioning basis may also be ratio-formed:

$$ P(B) = \frac{n(B)}{n(S)} $$

So conditional probability can reuse earlier lessons as a ratio of ratios, where the reference frame is effectively restricted to `B`.

## 4. Distinguishing the relation

Conditional probability is not the same as joint probability.

* `P(A \cap B)` measures shared occurrence in the original full space
* `P(A \mid B)` measures occurrence of `A` inside the narrowed space defined by `B`

If a prompt says “given B,” the denominator must reflect the restricted context.

## 5. One-sentence summary

Conditional restriction is a reusable substrate in which a quantity is recalculated inside a narrower basis, and conditional probability is its standard probabilistic form.
