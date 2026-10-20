# Physics Relations — Linear Motion Under Constant Acceleration

This document teaches how earlier motion quantities combine into predictive kinematic laws.

The point is to preserve the relation between initial state, rate of change, elapsed time, and resulting motion.

## 1. Reusable substrate

A later state can be obtained from an earlier state plus a change term.

The reusable formula is:

$$ S_{\text{later}} = S_{\text{initial}} + \text{change} $$

Where:

* input: `S_initial`
* input: `change`
* output: `S_later`

## 2. Velocity update

Under constant acceleration, velocity changes linearly with time.

$$ v = u + at $$

Where:

* input: `u` initial velocity
* input: `a` acceleration
* input: `t` time
* output: `v` final velocity

This reuses the earlier state-plus-change substrate, where change is `at`.

## 3. Position update

Displacement under constant acceleration is:

$$ s = ut + \frac{1}{2}at^2 $$

Where:

* input: `u`
* input: `a`
* input: `t`
* output: `s`

This reuses prior ideas of velocity, acceleration, and time, but composes them into a longer determinate law.

## 4. Velocity-displacement relation

A time-eliminated kinematic law is:

$$ v^2 = u^2 + 2as $$

This relation still depends on the same motion quantities, but removes explicit time.

## 5. One-sentence summary

Constant-acceleration kinematics reuses earlier motion quantities and assembles them into state-update laws.
