# Community center room booking reminders

A municipal community center wants to reduce no-shows for room bookings and classes. Bookings are currently recorded by front-desk staff, and reminders are handled manually with ad hoc phone calls. Managers want a lighter process without excluding residents who do not regularly use email or mobile apps.

## Actors

- community center manager
- front-desk staff
- residents
- messaging vendor
- city IT support

## Objectives

- reduce missed bookings and empty rooms
- keep reminder work off the front desk
- avoid relying on a single digital channel that some residents do not use

## Capabilities

- booking reminder messages
- reminder preferences by resident
- staff fallback call list
- attendance and no-show reporting

## Dependencies

- accurate booking contact details
- reminder consent records
- messaging service uptime

## Constraints

- staff still need a manual fallback for residents with missing contact data
- reminders must not expose private booking details to the wrong person
- the center cannot depend on residents installing an app

## Boundaries

- center-to-messaging-vendor boundary
- center-to-city-it boundary
- staff-to-resident communication boundary

## States

- reminders are handled manually by staff phone calls
- reminders are sent automatically with staff fallback for missing coverage
- reminders depend only on app notifications

## Transitions

- automate reminders with staff fallback
- add resident communication preferences and reporting
- move to app-only reminders
