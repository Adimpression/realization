# Information Relations 10 — KL Divergence as Relative Information Mismatch

This document teaches how one distribution is measured against another by aggregating probability-weighted log-ratios.

The point is to preserve the semantic relation between reference distribution, alternative distribution, and directional mismatch.

## 1. Reusable substrate

When one distribution is compared against another by taking a transformed ratio at each case and then weighting by the reference distribution, the reusable family is weighted relative transform.

The reusable formula is:

$$ R = \sum_i p_i \cdot g\!\left(\frac{p_i}{q_i}\right) $$

Where:

* input: `p_i` = reference distribution
* input: `q_i` = comparison distribution
* input: `g` = ratio-transform function
* output: `R`

This family should be reused when a later relation says that two probability distributions are compared through casewise transformed ratios.

## 2. KL divergence

KL divergence is a weighted-relative-transform relation where the transform is logarithm.

The reusable formula is:

$$ D_{KL}(P \parallel Q) = \sum_i p_i \log \frac{p_i}{q_i} $$

Where:

* input: `p_i` = probability under `P`
* input: `q_i` = probability under `Q`
* output: `D_{KL}(P \parallel Q)`

This relation reuses the earlier weighted-relative-transform family with a logarithmic ratio transform.

## 3. Reusing earlier lessons

KL divergence reuses earlier structures at a higher level:

* ratio formation appears inside `p_i / q_i`
* transformed aggregation appears through logarithm and weighted sum
* expectation-like structure remains, because the terms are weighted by `p_i`

So this lesson is a higher-order reuse of ratio, transform, and weighted aggregation.

## 4. Distinguishing the relation

KL divergence is not symmetric distance in the ordinary geometric sense.

* `D_{KL}(P \parallel Q)` is generally not equal to `D_{KL}(Q \parallel P)`
* it measures mismatch from the perspective of `P` using `Q` as comparison

If a prompt asks how costly or mismatched one modeled distribution is relative to the true or reference one, KL divergence is often the relevant reusable family.

## 5. One-sentence summary

KL divergence is a reusable weighted relative-transform relation in which one probability distribution evaluates the informational mismatch of another through probability-weighted log-ratios.
