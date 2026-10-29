# Realized Host Interaction

`realized-host-interaction` is the backend-neutral substrate shared by the
Realization controller and workstation. It owns explicit attachment contracts,
bounded attachment resolution, common host actions, delegated-rights
narrowing, receipt shaping, and the immutable ABI for advertising, inspecting,
and invoking exact executor and broker realizers. Concrete providers are
assembled by the application or workstation host and attached to an invocation
context; the package keeps no mutable provider registry.

The package does **not** choose or admit an ability, grant authority, supply a
concrete host operation, or provide workstation/session implementations. Those
responsibilities remain with reasoning, governance, entry composition, and host
adapters. An advertised provider binding is host availability evidence only;
it is not an installed ability or an invocation grant.

Its public ABI is exported from `realized_host_interaction`. Historical
root-module imports remain available as compatibility facades while consumers
migrate.
