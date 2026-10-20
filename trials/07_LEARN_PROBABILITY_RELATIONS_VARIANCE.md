# Probability Relations 07 — Variance as Expected Squared Deviation

This document teaches how spread is obtained by measuring deviation from an average, transforming that deviation, and then aggregating it.

The point is to preserve the semantic relation between center, deviation, transformation, and weighted average.

## 1. Reusable substrate

When spread is computed by first subtracting a central value, then applying a transformation, then taking a weighted aggregate, the reusable family is transformed deviation aggregation.

The reusable formula is:

$$ D = \sum_i w_i \cdot g(x_i - c) $$

Where:

* input: `x_i` = value
* input: `c` = center
* input: `g` = deviation-transform function
* input: `w_i` = weight
* output: `D`

This family should be reused when a later relation says that dispersion is formed from transformed deviations around a center.

## 2. Variance

Variance is a transformed-deviation-aggregation relation where the transformation is squaring.

The reusable formula is:

$$ \mathrm{Var}(X) = \sum_i P(x_i) \cdot (x_i - \mathbb{E}[X])^2 $$

Where:

* input: `P(x_i)` = probability weight
* input: `x_i` = outcome value
* input: `\mathbb{E}[X]` = expected value
* output: `\mathrm{Var}(X)`

This relation reuses the earlier transformed-deviation-aggregation family with a squared deviation transform.

## 3. Reusing earlier lessons

Variance directly reuses expectation:

* it needs `\mathbb{E}[X]` as the center
* it again uses weighted aggregation over probabilities

So this lesson is structurally downstream of expected value.

## 4. Distinguishing the relation

Variance is not the same as average value.

* expectation measures central tendency
* variance measures spread around that center

If a prompt asks how unstable, dispersed, or variable a distribution is, use variance rather than expectation.

## 5. One-sentence summary

Variance is a reusable transformed-deviation relation built on expectation, where spread is measured by probability-weighted squared distance from the mean.
