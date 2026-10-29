# Regional emergency alerting system

## Situation

A region wants to improve emergency public alerts for floods, fires, chemical incidents, and major transport disruptions.

No single agency controls the whole system.

### Actors

* national emergency agency
* local governments
* telecom operators
* weather service
* police and fire services
* hospitals
* media broadcasters

### Objectives

* `o1`: fast alert delivery
* `o2`: reliable delivery under failure
* `o3`: accessibility for all populations
* `o4`: interoperability across agencies
* `o5`: public trust and clarity

### Capabilities

* `k1`: cell broadcast alerts
* `k2`: SMS alerts
* `k3`: app push notifications
* `k4`: multilingual message templating
* `k5`: siren fallback
* `k6`: alert coordination dashboard
* `k7`: location-specific geofencing
* `k8`: accessibility features for disabled users

### Dependencies

* `d1`: telecom integration
* `d2`: shared message standards
* `d3`: legal authority for who may send alerts
* `d4`: funding for local rollout
* `d5`: training and operating procedures

### Constraints

* `q1`: privacy law
* `q2`: uneven municipal budgets
* `q3`: legacy systems must remain active during rollout
* `q4`: no single point of failure
* `q5`: alerts must remain understandable to the public

### Boundaries

* `β1`: national-local governance boundary
* `β2`: agency-to-telecom boundary
* `β3`: technical standards boundary
* `β4`: language and accessibility boundary

### States

There are many states, because different combinations of capabilities may be available in different places.

For example:

* one municipality may have cell broadcast and sirens,
* another may only have SMS and radio coordination,
* another may have a full dashboard plus multilingual support.

So the state space is combinatorial.
