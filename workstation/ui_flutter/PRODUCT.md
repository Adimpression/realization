# Workstation Flutter UI Product Specification

See [PRODUCT_IMPLEMENTATION.md](./PRODUCT_IMPLEMENTATION.md) for the execution checklist and acceptance gates that implement this contract.

## Product Summary

The Flutter app is the desktop-web-first workstation client for the existing workstation gRPC services and shared workstation workflow surface.

Textual remains the canonical UX reference until the Flutter migration is complete, and Flutter is expected to reproduce the same shell behavior on desktop-width layouts.

## Product Objective

The product objective is Textual-exact shell parity on desktop-width layouts.

For this product, "exact parity" means:

- the same shell structure
- the same section titles and groupings
- the same pane arrangement
- the same interaction and state transitions
- the same information density
- the same class of structured renderers for critical panes

This does not require pixel-perfect terminal styling. Flutter remains Flutter-rendered, but it must reproduce the Textual shell contract faithfully.

## Canonical Reference Model

Textual UI is the source of truth for shell structure and interaction model.

Flutter is a framework encoding of that Textual shell contract. Shared helpers may represent the contract in a renderer-neutral form, but they do not define product behavior independently of Textual.

## Scope and Constraints

In scope:

- desktop-width shell parity for subject workflow tabs
- shell states and workbench states
- structured pane renderers
- interactive pane behavior
- screenshot-based evidence

Out of scope for this pass:

- backend changes
- protocol changes
- narrow/mobile parity
- terminal-style imitation for its own sake

## Target Shell States

The desktop shell states required for parity are:

- `gather.main`
- `gather.journal`
- `gather.source_detail`
- `itemize.main`
- `draft.compose`
- `draft.frame`
- `draft.model`
- `draft.explore`
- `review.main`
- `review.journal`
- `publication.main`

## Parity Evaluation Method

Parity is evaluated from the user perspective, not from implementation intent.

Every parity review should use this method:

1. Define the user objective.
2. Define what the user does in the UI to achieve that objective.
3. Evaluate what the UI actually renders and how it behaves while the objective is being achieved.

Parity is established from rendered behavior and structure, not from code shape, transport fields, or assumptions that equivalent data implies equivalent UI.

## Product Success Criteria

The product is successful only when all of the following are true:

- Flutter matches Textual shell structure for every target shell state.
- Flutter matches Textual interaction mode transitions for every target shell state.
- Flutter matches Textual pane-local interaction behavior for inventory, scope, and detail workbench panes.
- Critical structured panes are rendered in the same form class as Textual and do not collapse into generic blob text.
- Screenshot evidence and tests agree that the rendered shell is structurally equivalent to Textual.

## Current Baseline

The current Flutter baseline already satisfies the first shell-parity milestone:

- all 11 required desktop shell states render and the screenshot harness completes end to end
- the interactive inventory and scope panes for `itemize`, `draft`, `review`, and `publication` are now clickable and keyboard-driven
- row selection in those panes is expected to refresh the companion detail pane, and that behavior is part of the parity contract

This means the next parity pass is no longer about getting the shell states to exist. It is about matching Textual's container behavior more closely.

## Next Parity Frontier

The next required parity work is:

- panel-shell click-to-focus behavior that mirrors Textual's focus-target mapping
- pane-local scroll and wheel behavior, especially for scope trees and long structured panes
- fixed-height body layout under the tab strip instead of a single long page scroll
- general layout fidelity driven by the workstation layout spec rather than ad hoc Flutter sizing
- detached/maximized/info-pane behavior where Textual exposes it and Flutter does not yet

## Evidence Standard

Parity may only be claimed when:

- widget parity tests pass
- interaction tests prove that selecting rows updates the expected companion detail pane
- the webdriver screenshot suite passes
- named screenshot artifacts exist for every target shell state
- click-focus, scroll, and fixed-height behavior are covered by dedicated tests when parity is claimed for those areas

The screenshot suite is part of the product evidence standard, not an optional review aid. It is necessary but not sufficient for interactive panes or layout behavior.
