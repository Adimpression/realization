# Chemistry Relations 03 — Mass to Mole Conversion

This document teaches one reusable ratio substrate and then reuses it in a central chemistry conversion.

The point is not only to store a conversion formula, but to preserve the reusable semantic relation between total quantity and per-unit quantity.

## 1. Reusable substrate

When the number of units is obtained by dividing a total by the amount per unit, the reusable family is total-per-unit division.

The reusable formula is:

$$ U = \frac{T}{q_u} $$

Where:

* input: `T`
* input: `q_u`
* output: `U`

This family should be reused when a later law says that a total amount is converted into number of units by dividing by unit size.

## 2. Moles from mass

Chemistry uses this family in molar-mass conversion.

The reusable formula is:

$$ n = \frac{m}{M} $$

Where:

* input: `m`
* input: `M`
* output: `n`

This relation reuses the earlier total-per-unit division family with chemistry-specific quantities.

## 3. Mass from moles

The corresponding multiplicative form is:

$$ m = n * M $$

Where:

* input: `n`
* input: `M`
* output: `m`

This relation reuses the same semantic structure from the opposite direction.

## 4. Connection to earlier lessons

Now chemistry has two reusable counting bridges:

* `N = n * N_A` connects particles and moles
* `m = n * M` connects mass and moles

So moles become a central intermediate representation between count and mass.

## 5. One-sentence summary

Total-per-unit division is the broader reusable substrate; molar-mass conversion is a narrower determinate chemistry law that uses grams per mole as the unit size.
