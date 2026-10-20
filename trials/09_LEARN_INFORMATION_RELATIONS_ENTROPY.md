# Information Relations 09 — Entropy as Expected Surprise

This document moves from probability alone into information measurement.

The point is to preserve the semantic relation between uncertainty and the probability-weighted aggregation of surprise.

## 1. Reusable substrate

When an aggregate quantity is formed by applying a meaning-transform to each probability and then taking the weighted average, the reusable family is transformed probability expectation.

The reusable formula is:

$$ I = \sum_i p_i \cdot h(p_i) $$

Where:

* input: `p_i` = probability of case `i`
* input: `h` = information-transform function
* output: `I`

This family should be reused when a later relation says that overall informational quantity is formed from transformed probabilities.

## 2. Entropy

Entropy is a transformed-probability-expectation relation where the transform is negative logarithm.

The reusable formula is:

$$ H(X) = - \sum_i p_i \log p_i $$

Where:

* input: `p_i`
* output: `H(X)`

This relation reuses the earlier transformed-probability-expectation family with `h(p_i) = \log p_i` and an outer negative sign.

## 3. Reusing earlier lessons

Entropy reuses expectation-like structure:

* probabilities act as weights
* a transformed quantity is aggregated across cases

But unlike ordinary expected value over outcomes `x_i`, entropy applies the transform to the probabilities themselves.

So this lesson reuses weighted aggregation while shifting the semantic object being aggregated.

## 4. Distinguishing the relation

Entropy is not probability of one event.

* one probability measures one event’s likelihood
* entropy measures whole-distribution uncertainty

If a prompt asks how uncertain a distribution is overall, entropy is the relevant reusable family.

## 5. One-sentence summary

Entropy is a reusable transformed-probability expectation in which each event contributes surprise according to its probability and the whole distribution aggregates those contributions.
