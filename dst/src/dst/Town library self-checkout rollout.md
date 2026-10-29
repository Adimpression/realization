# Town library self-checkout rollout

## Situation

A town library network wants shorter checkout lines and less repetitive desk work.

Today branch staff check out every book and media item by hand. The library is considering self-checkout kiosks, but it cannot leave patrons without help and it cannot shut branches during installation.

## Actors

* `a1`: library administration
* `a2`: branch staff
* `a3`: kiosk vendor
* `a4`: accessibility office
* `a5`: patrons

## Objectives

* `o1`: reduce checkout wait times
* `o2`: keep checkout accessible for patrons who need staff help
* `o3`: avoid branch disruption during rollout

## Capabilities

* `k1`: self-checkout kiosks
* `k2`: staffed assistance desk during kiosk use
* `k3`: accessible kiosk prompts and large-text guidance
* `k4`: kiosk-first checkout with minimal staffed support

## Dependencies

* `d1`: vendor installation readiness
* `d2`: staff training complete
* `d3`: accessibility review signed off

## Constraints

* `q1`: branches must stay open during rollout
* `q2`: patrons who need staff help must still be served
* `q3`: budget only allows staged installation

## Boundaries

* `b1`: library-to-vendor boundary
* `b2`: accessibility-to-service-design boundary

## States

* `s0`: staffed checkout only
* `s1`: main-branch pilot with staff support
* `s2`: multi-branch kiosks with staffed support
* `s3`: kiosk-first checkout with minimal staffed support

## Transitions

* `t1`: branch pilot with staffed support
* `t2`: expand kiosks while keeping staffed assistance
* `t3`: fast kiosk-first rollout

## Candidate paths

### Path A: branch pilot with staffed support

This path keeps the service legible to patrons and gives staff time to learn the new workflow before the library expands kiosks across branches.

* `s0 -> s1 -> s2`
* keep staffed assistance in place
* stage installation branch by branch
* preserve accessibility and service continuity

### Path B: kiosk-first cutover

This path reduces desk traffic faster, but it is brittle because it depends on full readiness and weakens the staffed fallback too early.

* `s0 -> s3`
* push kiosks out quickly
* reduce staffed checkout coverage early
* risk excluding patrons who still need direct help
