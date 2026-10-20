# Community clinic appointment reminders

## Situation

A clinic network wants fewer missed appointments.

Today front-desk staff call patients one by one. The clinics want a reminder system that reaches people earlier, but they cannot assume every patient uses the mobile app or reads messages in English.

## Actors

* `a1`: clinic operations lead
* `a2`: front-desk staff
* `a3`: messaging vendor
* `a4`: privacy officer
* `a5`: patients

## Objectives

* `o1`: reduce missed appointments
* `o2`: keep reminders accessible across language and device differences
* `o3`: protect consent and privacy rules

## Capabilities

* `k1`: automated SMS reminders
* `k2`: multilingual reminder templates
* `k3`: call fallback for high-risk visits
* `k4`: portal-app-only reminders

## Dependencies

* `d1`: patient phone numbers are current
* `d2`: consent records are complete
* `d3`: multilingual content approved
* `d4`: follow-up lists reach front-desk staff

## Constraints

* `q1`: patients without smartphones must still receive reminders
* `q2`: reminder messages require recorded consent
* `q3`: the front desk cannot absorb unlimited manual callback work

## Boundaries

* `b1`: clinic-to-vendor messaging boundary
* `b2`: privacy-to-patient-communication boundary
* `b3`: digital channel-to-manual follow-up boundary

## States

* `s0`: manual phone reminders only
* `s1`: SMS reminders only
* `s2`: SMS reminders with multilingual templates and call fallback
* `s3`: portal-app-only reminders

## Transitions

* `t1`: launch SMS reminders with multilingual templates and call fallback
* `t2`: launch SMS reminders without follow-up fallback
* `t3`: move to portal-app-only reminders

## Candidate paths

### Path A: inclusive reminder rollout

This path automates the first reminder but keeps a manual safety net for patients who need it.

* `s0 -> s2`
* use SMS for scale
* add multilingual templates
* keep call fallback for high-risk or unreachable patients

### Path B: lean SMS rollout

This path is operationally lighter than manual calling, but it is not ready if the clinics cannot guarantee callback coverage for people who miss or cannot read the first message.

* `s0 -> s1`
* use SMS as the main reminder channel
* depend on current phone and consent records
* leave follow-up capacity thin

### Path C: portal-only reminders

This path is simple on paper, but it fails the accessibility and device-coverage standard.

* `s0 -> s3`
* use the app portal as the reminder channel
* reduce manual and SMS overhead
* exclude patients who do not reliably use the portal
