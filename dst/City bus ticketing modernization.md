# City bus ticketing modernization

## Situation

A city transit authority wants to modernize fare payment.

Today riders mostly use cash and plastic transit cards. The city wants to introduce app-based and contactless bank-card payment.

### Actors

* transit authority
* private bus operators
* payment processor
* city regulator
* passengers

### Objectives

* `o1`: reduce boarding time
* `o2`: reduce fare evasion
* `o3`: avoid service disruption

### Capabilities

* `k1`: improved smart card system
* `k2`: full open-loop contactless payment with bank cards and phones
* `k3`: fare inspector mobile verification tools
* `k4`: backward compatibility for old validators

### Dependencies

* `d1`: banks and payment processor readiness
* `d2`: operator hardware upgrade complete
* `d3`: legal approval for account-based fare processing

### Constraints

* `q1`: annual budget cap
* `q2`: buses must continue operating without downtime
* `q3`: elderly and unbanked riders must not be excluded

### Boundaries

* `β1`: public-private operator boundary
* `β2`: transit-to-banking boundary
* `β3`: policy boundary around inclusion and privacy

### States

* `s0`: legacy fare system
* `s1`: improved closed-loop card system
* `s2`: hybrid card plus compatibility tools
* `s3`: full account-based open-loop payment

### Transitions

* `τ1`: upgrade existing transit card system
* `τ2`: add compatibility and inspection tools
* `τ3`: direct shift to open-loop bank-card payment

