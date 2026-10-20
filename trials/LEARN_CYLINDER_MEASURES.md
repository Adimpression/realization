# Cylinder Measures

A cylinder is a three-dimensional shape with a circular base and a matching circular top.
Two common reusable calculations are the total surface area and the volume.

---

## 1. Named quantities

We will use:

* `r` for radius
* `h` for height

Natural-language aliases:

* radius
* height
* circular radius
* cylinder height

---

## 2. Total surface area of a cylinder

The total surface area includes:

* the curved surface around the side
* the top circle
* the bottom circle

The reusable formula is:

$$
A = 2 \pi r (r + h)
$$

Where:

* input: `r`
* input: `h`
* output: `A`

Meaning:

* double pi
* multiply by radius
* multiply by the sum of radius and height

Canonical caller-facing question:

* What is the total surface area of a cylinder given radius and height?

Example:

If `r = 3` and `h = 5`:

$$
A = 2 \pi \cdot 3 \cdot (3 + 5) = 48\pi
$$

So the total surface area is `48π`, approximately `150.79644737231007`.

---

## 3. Volume of a cylinder

The reusable formula is:

$$
V = \pi r^2 h
$$

Where:

* input: `r`
* input: `h`
* output: `V`

Meaning:

* square the radius
* multiply by pi
* multiply by height

Canonical caller-facing question:

* What is the volume of a cylinder given radius and height?

Example:

If `r = 3` and `h = 5`:

$$
V = \pi \cdot 3^2 \cdot 5 = 45\pi
$$

So the volume is `45π`, approximately `141.3716694115407`.

---

## 4. Distinguishing the measures

These two calculations are related but not the same:

* total surface area measures the full outside area
* volume measures the space inside the cylinder

If a prompt asks for both, keep them separate instead of collapsing them into one quantity.

---

## 5. One-sentence summary

For a cylinder with radius `r` and height `h`, total surface area is `2πr(r+h)` and volume is `πr²h`.
