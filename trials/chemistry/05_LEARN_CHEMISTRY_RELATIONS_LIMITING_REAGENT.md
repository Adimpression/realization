# Chemistry Relations 05 — Limiting Reagent as Minimum Achievable Production

This document teaches one reusable bottleneck substrate and then reuses it in reaction yield reasoning.

The point is not only to store a procedure, but to preserve the reusable semantic relation between several candidate capacities and the smallest actual achiever.

## 1. Reusable substrate

When several inputs could determine an output, but the actual output is set by the smallest achievable capacity, the reusable family is bottleneck determination.

The reusable formula is:

$$ O = \min(c_1, c_2, \dots, c_n) $$

Where:

* input: `c_1 ... c_n`
* output: `O`

This family should be reused when a later law says that the least-capable input fixes the final achievable amount.

## 2. Product possible from each reactant

For each reactant, compute the product moles it could produce.

The reusable formula is:

$$ n_P^{(i)} = n_i * \frac{\nu_P}{\nu_i} $$

Where:

* input: `n_i`
* input: `\nu_i`
* input: `\nu_P`
* output: `n_P^(i)`

This relation reuses the stoichiometric-ratio lesson for each candidate reactant.

## 3. Actual product from the limiting reagent

The real product amount is:

$$ n_P = \min\left(n_P^{(1)}, n_P^{(2)}, \dots, n_P^{(k)}\right) $$

Where:

* input: `n_P^(1) ... n_P^(k)`
* output: `n_P`

This relation reuses the earlier bottleneck family with chemistry-specific candidate capacities.

## 4. Distinguishing the ideas

Stoichiometric ratio and limiting reagent are related, but not identical.

* stoichiometric ratio tells what one amount implies about another
* limiting reagent chooses which reactant actually controls the reaction outcome

If a prompt asks for the controller of production, do not answer with only a ratio.

## 5. One-sentence summary

Bottleneck determination is the broader reusable substrate; limiting-reagent analysis is a narrower determinate chemistry law that selects the smallest stoichiometrically possible product amount.
