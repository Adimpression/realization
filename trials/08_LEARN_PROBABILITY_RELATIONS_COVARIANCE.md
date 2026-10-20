# Probability Relations 08 — Covariance as Co-Deviation

This document teaches how two variables vary together by measuring simultaneous deviation from their respective centers.

The point is to preserve the semantic relation between paired deviation and aggregate directional co-movement.

## 1. Reusable substrate

When a quantity is formed by multiplying two deviations and then aggregating them, the reusable family is co-deviation aggregation.

The reusable formula is:

$$ C = \sum_i w_i \cdot (x_i - c_x)(y_i - c_y) $$

Where:

* input: `x_i`
* input: `y_i`
* input: `c_x`
* input: `c_y`
* input: `w_i`
* output: `C`

This family should be reused when a later relation says that two variables are measured by how their deviations align.

## 2. Covariance

Covariance is a co-deviation-aggregation relation.

The reusable formula is:

$$ \mathrm{Cov}(X,Y) = \sum_i P_i \cdot (x_i - \mathbb{E}[X])(y_i - \mathbb{E}[Y]) $$

Where:

* input: `P_i` = probability weight
* input: `x_i`
* input: `y_i`
* input: `\mathbb{E}[X]`
* input: `\mathbb{E}[Y]`
* output: `\mathrm{Cov}(X,Y)`

This relation reuses the earlier co-deviation-aggregation family with expectation-derived centers.

## 3. Reusing earlier lessons

Covariance reuses:

* expectation for both centers
* transformed deviation thinking from variance
* weighted aggregation over probability

It extends variance from one variable’s spread to two variables’ joint directional movement.

## 4. Distinguishing the relation

Covariance is not simple association in ordinary language.

* positive covariance means values tend to move above their means together
* negative covariance means one tends to rise above its mean when the other falls below its mean
* zero covariance does not automatically imply full independence in every case

If a prompt asks whether two variables move together, covariance is closer than variance or expectation.

## 5. One-sentence summary

Covariance is a reusable co-deviation relation in which two centered variables are multiplied and aggregated to measure directional joint variation.
