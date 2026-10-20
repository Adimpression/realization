# Probability Relations 03 — Complement Relation

This document teaches how one probability can be obtained from the whole minus another probability.

The point is to preserve the reusable semantic relation between totality and exclusion.

## 1. Reusable substrate

When one quantity is obtained by subtracting a part from a whole, the reusable family is complement subtraction.

The reusable formula is:

$$ c = W - x $$

Where:

* input: `W`
* input: `x`
* output: `c`

This family should be reused when a later relation says that the remainder of a whole is obtained by removing a named part.

## 2. Complement probability

Complement probability is a complement-subtraction relation.

The reusable formula is:

$$ P(\neg A) = 1 - P(A) $$

Where:

* input: `P(A)`
* input: `1` = total probability mass
* output: `P(\neg A)`

This relation reuses the earlier complement-subtraction family with probability-specific quantities.

## 3. Reusing earlier lessons

The term `P(A)` may itself come from ratio formation:

$$ P(A) = \frac{n(A)}{n(S)} $$

So complement probability may reuse earlier lessons as:

$$ P(\neg A) = 1 - \frac{n(A)}{n(S)} $$

This means ratio formation can produce a probability, and complement subtraction can then produce the remainder.

## 4. Distinguishing the relation

Complement is not “another unrelated event.” It is specifically the remainder of the full space once the target event is removed.

* `P(\neg A)` depends on totality being 1
* it should not be confused with a separate arbitrary event `P(B)`

If a prompt asks for “not A,” use complement structure rather than inventing a new independent event.

## 5. One-sentence summary

Complement subtraction is a reusable substrate in which the whole remains fixed and the target probability is removed to obtain the remainder.
