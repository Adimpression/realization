# Chemistry Relations 09 — pH as Logarithmic Amount Measure

This document teaches one reusable logarithmic-scaling substrate and then reuses it in acid-base chemistry.

The point is not only to store a formula, but to preserve the reusable semantic relation between a quantity and its logarithmic measure.

## 1. Reusable substrate

When a measure is defined as the negative base-10 logarithm of a quantity, the reusable family is logarithmic compression.

The reusable formula is:

$$ M = -\log_{10}(q) $$

Where:

* input: `q`
* output: `M`

This family should be reused when a later law says that a very wide numerical range is represented on a logarithmic scale.

## 2. pH from hydrogen ion concentration

Chemistry uses this family in the pH definition.

The reusable formula is:

$$ \mathrm{pH} = -\log_{10}[H^+] $$

Where:

* input: `[H^+]`
* output: `pH`

This relation reuses the earlier logarithmic-compression family with chemistry-specific quantities.

## 3. Recovering concentration from pH

The inverse relation is:

$$ [H^+] = 10^{-\mathrm{pH}} $$

Where:

* input: `pH`
* output: `[H^+]`

This relation reuses the same semantic structure from the opposite direction.

## 4. Distinguishing pH from concentration

pH and hydrogen ion concentration are tightly related, but they are not the same representation.

* concentration is the direct amount measure
* pH is the logarithmically compressed measure

If a prompt asks for one, do not answer only with the other unless the conversion is made explicit.

## 5. One-sentence summary

Logarithmic compression is the broader reusable substrate; pH is a narrower determinate chemistry law that maps hydrogen ion concentration onto a logarithmic scale.
