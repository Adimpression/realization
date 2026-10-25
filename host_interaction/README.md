# Realized Host Interaction

`realized-host-interaction` is the backend-neutral substrate shared by the
Realization controller and workstation. It owns explicit attachment contracts,
bounded attachment resolution, common host actions, delegated-rights
narrowing, and receipt shaping.

The package does **not** choose an ability, grant authority, register arbitrary
host operations, or provide concrete workstation/session implementations.
Those responsibilities remain with reasoning, governance, and host adapters.

Its public ABI is exported from `realized_host_interaction`. Historical
root-module imports remain available as compatibility facades while consumers
migrate.
