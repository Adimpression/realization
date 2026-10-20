# Hospital medication system upgrade

## Situation

A hospital wants to replace handwritten medication orders with a fully digital prescribing system.

### Actors

* hospital administration
* clinical safety board
* doctors
* pharmacy department
* IT vendor

### Objective

* prevent medication errors while keeping care running

### Capabilities

* `k1`: paper prescribing
* `k2`: electronic prescribing
* `k3`: barcode medication verification

### Dependencies

* `d1`: regulator approval for digital prescribing
* `d2`: staff training completed
* `d3`: pharmacy system integration working

### Constraints

* `q1`: no dual prescribing allowed for controlled drugs
* `q2`: patient safety rules require fully validated workflows before live use

### Boundary

* `β1`: clinical-to-IT boundary
* `β2`: hospital-to-regulator boundary

### States

* `s0`: paper only
* `s1`: mixed paper and electronic
* `s2`: fully electronic and validated

### Transitions

* `τ1`: move from paper-only to mixed mode
* `τ2`: move from mixed mode to full electronic
* `τ3`: direct cutover from paper-only to full electronic

