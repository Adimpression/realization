# Pythagorean Theorem

The Pythagorean theorem is a rule for **right-angled triangles**.
It tells you how to find the **slanted side** when you know the other two sides.

---

## 1. The triangle and the side roles

A right-angled triangle has:

* two shorter sides that meet at the 90-degree corner
* one slanted side opposite the 90-degree corner

We will use these names:

* `a` = one shorter side
* `b` = the other shorter side
* `c` = the slanted side, also called the **hypotenuse**

Useful natural-language aliases:

* slanted side
* longest side
* hypotenuse
* the side opposite the right angle

---

## 2. The core rule

The rule is:

$$
a^2 + b^2 = c^2
$$

If you want the slanted side itself, solve for `c`:

$$
c = \sqrt{a^2 + b^2}
$$

This is the reusable calculation form.

### Primary executable calculation contract

The main reusable function in this curriculum is:

* inputs: `a`, `b`
* output: `c`
* meaning: compute the hypotenuse from the two shorter sides

Use this exact executable relation:

$$
c = \sqrt{a^2 + b^2}
$$

For this curriculum, this is the primary direction of use.
Do not treat the main executable pattern here as "solve for `a` from `c`" or "solve for `b` from `c`".
The main executable task is always:

* given `a` and `b`
* return `c`

Canonical question form for the main executable pattern:

* What is the length of the hypotenuse `c` given side lengths `a` and `b`?

---

## 3. What the reusable calculation needs

Inputs:

* `a`: one shorter side length
* `b`: the other shorter side length

Output:

* `c`: the slanted side length

Meaning:

* square the first shorter side
* square the second shorter side
* add those two squares
* take the square root

---

## 4. Standard example

If the two shorter sides are `3` and `4`:

$$
c = \sqrt{3^2 + 4^2} = \sqrt{9 + 16} = \sqrt{25} = 5
$$

So the slanted side is `5`.

---

## 5. Equal-side special case

If the **other two sides are the same length**, call that shared length `s`.

This is a secondary specialized shortcut.
It should only be used when the prompt clearly says the two shorter sides are the same length or both have the same explicit value.
If the prompt gives separate `a` and `b` values, prefer the main executable contract above.

Then:

$$
c = \sqrt{s^2 + s^2} = \sqrt{2s^2}
$$

Which is the same as:

$$
c = s\sqrt{2}
$$

Example:

If the other two sides are `5` metres each:

$$
c = \sqrt{5^2 + 5^2} = \sqrt{25 + 25} = \sqrt{50} \approx 7.0710678118654755
$$

So the slanted side is about `7.0710678118654755` metres.

Natural-language paraphrases of the same task:

* calculate the slanted side from the other two sides
* find the hypotenuse from the two shorter sides
* if the other two sides are 5 each, what is the slanted side

---

## 6. One-sentence summary

In a right-angled triangle, the slanted side is found by taking the square root of the sum of the squares of the other two sides.
