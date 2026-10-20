# Probability Relations 06 — Expected Value

This document teaches how multiple possible outcomes can be combined into one average value weighted by probability.

The point is to preserve the semantic relation between possibility, weight, and aggregate prediction.

## 1. Reusable substrate

When an overall value is formed by multiplying each possible outcome by its weight and then summing the results, the reusable family is weighted aggregation.

The reusable formula is:

$$ E = \sum_i w_i \cdot x_i $$

Where:

* input: `w_i` = weight of case `i`
* input: `x_i` = value of case `i`
* output: `E`

This family should be reused when a later relation says that an aggregate quantity is formed from weighted possibilities.

## 2. Expected value

Expected value is a weighted-aggregation relation.

The reusable formula is:

$$ \mathbb{E}[X] = \sum_i P(x_i) \cdot x_i $$

Where:

* input: `P(x_i)` = probability of outcome `x_i`
* input: `x_i` = numerical outcome
* output: `\mathbb{E}[X]`

This relation reuses the earlier weighted-aggregation family with probability-specific weights.

## 3. Reusing earlier lessons

The weights here are probabilities, so they may come from earlier ratio formation, conditioning, or Bayes updating.

For example, a posterior distribution from Bayes' theorem can become the weighting basis for a new expectation.

So this lesson reuses earlier lessons by turning probabilities into semantic weights for aggregation.

## 4. Distinguishing the relation

Expected value is not “the most likely outcome.”

* the most likely outcome is the mode
* the expected value is the probability-weighted average

If a prompt asks for long-run average payoff, expectation is the correct reusable family even when no single outcome equals the final value.

## 5. One-sentence summary

Weighted aggregation is a reusable substrate in which possibilities are multiplied by their weights and then summed, and expected value is its central probabilistic form.
