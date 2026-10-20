# Workstation Flutter UI Implementation Checklist

See [PRODUCT.md](./PRODUCT.md) for the governing product contract. This document is the execution checklist for delivering that contract.

## Implementation Summary

This checklist converts the Flutter/Textual parity contract into concrete engineering work. It defines the workstreams, per-state acceptance checks, renderer obligations, behavioral parity requirements, and evidence gates required before desktop shell parity can be claimed.

## Current Baseline

As of the current Flutter baseline:

- all 11 target desktop shell states render and the screenshot harness completes
- structured `Current Step`, status, inventory, scope, and detail renderers are in place
- `itemize_inventory`, `draft_scope_tree`, `review_scope_tree`, and `publication_scope_tree` are interactive and tested
- the authoritative draft detail pane key is `draft_detail`
- layout-spec width, height, wrap, and scroll fields are parsed and consumed by the Flutter shell
- bounded desktop shell layout, wrapper click-focus, pane-local scroll ownership, and detached `maximize` / `info` behavior are implemented and widget-tested

The baseline now includes the previously missing `1`- and `2`-priority Flutter-visible workflow BDD paths. Any remaining parity work is in lower-priority edge flows rather than the core direct `v10` Gather -> Publication path.

## Working Rules

- Work only at the UI boundary:
  - Textual UI
  - Flutter UI
  - shared UI helpers
  - Flutter tests
  - screenshot harness
- Do not change backend or protocol behavior to solve shell parity issues unless that work is explicitly approved elsewhere.
- Use Textual as the canonical reference in every decision.
- Evaluate parity from rendered behavior, not from data shape alone.

## Workstream Checklist

- [x] Canonical shell extraction
- [x] Renderer parity baseline
- [x] Desktop shell-state parity baseline
- [x] Interactive inventory and scope-pane parity baseline
- [x] Screenshot evidence completion for the 11 required shell states
- [x] Panel click-focus parity
- [x] Pane-local scroll and wheel parity
- [x] Fixed-height workbench and general layout parity
- [x] Detached/maximized/help-pane parity
- [x] Layout-spec ingestion for width, height, wrap, and scroll semantics
- [x] Flutter-mirrored workflow BDD parity for same-subject DST routing and gate-state regressions
- [x] Audit adjacent Textual/backend BDDs for any remaining Flutter-visible parity gaps

## Workflow BDD Audit Outcome

### Mirrored Now In Flutter

Flutter now mirrors the remaining workflow-routing and gate-priority scenarios that were previously only exercised in backend and Textual layers.

The mirrored Flutter widget coverage now includes:

- clean direct `v10` browser upload path:
  - a real browser-targeted integration test now covers `Import Markdown -> open context -> compare maintained files -> generate itemization -> suggest DST constructs -> create draft composition -> start decision analysis -> run decision analysis -> approve review -> lock publication -> build report`
  - the built publication state is required to expose `Preview report.pdf`
  - Publication `More Actions` now explicitly keeps the plain `build_report` key visible in Flutter
- weak prose `v10` direct path:
  - Draft still presents `Start Decision Analysis` as the primary route after itemization / draft refresh
  - Review and Publication route back to `Start Decision Analysis`
  - phase-local action sets exclude later-phase actions like `Approve For Report`, `Lock Report Inputs`, and `Build Report`
- Gather / subject bootstrap path:
  - Gather empty-state follow-up action switches into Chat
  - maintained-files checking can advance directly to Review when the report plan is already the next actionable phase
- approved-import / Publication import path:
  - approved imports now surface the publication import controls in Flutter after report-plan refresh
  - publication import target / included / usage widgets are mirrored and tested
- same-subject `v2 -> v10` path:
  - Draft routes back to `Refresh DST Analysis`
  - Review and Publication route back to `Refresh DST Analysis`
  - phase-local action sets exclude inappropriate forward actions while refresh is required
- same-subject `v2 -> v10` later non-included draft row path:
  - focusing a later non-included draft row keeps the draft surface responsive
  - toggling decision inclusion still works
  - detail pane and switch state stay synchronized after the toggle
- weak-prose-after-construct-suggestion Draft path:
  - `Start Decision Analysis` remains primary
  - `Open Model` remains visible
  - `Hand To Review` stays excluded
- DST decision-analysis action matrix:
  - Draft `Start Decision Analysis` -> `Run Decision Analysis` -> Review `Approve For Report`
  - approved Draft keeps `Re-run Analysis (Balanced)` and `Open Model`
  - Review and Publication keep `Open Model` available as a Draft phase-nav action
  - built Publication keeps `Open Model` available alongside artifact actions
  - `Open Model` phase-nav returns to Draft compose without stale model-focus messaging

These mirrors are implemented in Flutter through:

- shared synthetic workflow-BDD controllers in [workstation_app_test.dart](./test/workstation_app_test.dart)
- a real browser-targeted direct-flow integration test in [direct_v10_publication_flow_test.dart](./integration_test/direct_v10_publication_flow_test.dart)

### Already Covered By Existing Flutter Tests

The adjacent visible parity surfaces that did not require new work remain covered by the existing Flutter suite:

- case-object interaction and draft lens persistence:
  - covered by the existing interactive-pane and draft-lens transition tests
- pane-local scroll, click-focus, bounded layout, and detached/maximized/info behavior:
  - covered by the existing container-behavior parity tests
- itemize, draft, review, and publication scope selection behavior:
  - covered by the existing interactive inventory/scope-pane tests

### Not Mirrored Because Not Flutter-Visible

The backend/Textual tests that assert generated report content or artifact payload details remain intentionally backend-only:

- report markdown / Typst decision-matrix content assertions in the `940+` backend BDD range
- publication artifact content and output-file assertions that Flutter does not render directly
- other receipt/content checks whose truth is visible only in generated artifacts rather than the subject shell

### Acceptance Rule

If Textual or backend BDD proves a user-visible gate, route, or Draft selection state that Flutter renders, Flutter now mirrors it directly unless the scenario is provably backend-only.

## Per-State Acceptance Checklists

### `gather.main`

**Expected sections**

- top numbered tab strip
- `Current Subject: ...`
- `Previous Subject` and `Next Subject`
- `Current Step`
- `Subject Status`
- `More Actions`
- `Source Set`
- `Revision Baseline`
- `In Source Set`
- `Source Sets`
- `Learned Snapshot`

**Expected pane layout**

- gate/status row across the top
- controls row beneath `More Actions`
- two-pane workbench: `Source Sets` left, `Learned Snapshot` right

**Expected controls**

- subject navigation buttons
- gather top actions in Textual order
- source set selector
- revision baseline selector
- in-source-set switch

**Expected transitions**

- journal action opens `gather.journal`
- source detail expansion opens `gather.source_detail`
- phase switch preserves subject context

**Renderer requirements**

- `Current Step` is structured, not prose-blob
- `Source Sets` uses the Textual source-set/detail form
- `Learned Snapshot` uses the Textual learned-summary form

**Required widget test**

- desktop gather shell renders all required titles and workbench panes

**Required screenshot artifact**

- `01-gather-main.png`

**Completion checklist**

- [ ] titles match Textual
- [ ] pane arrangement matches Textual
- [ ] controls appear in the same grouping as Textual
- [ ] no fallback blob renderers remain in primary panes

### `gather.journal`

**Expected sections**

- top numbered tab strip
- `Current Subject: ...`
- full-width `Gather Journal`

**Expected pane layout**

- single expanded journal pane replacing the normal workbench

**Expected controls**

- collapse control returns to `gather.main`

**Expected transitions**

- enter from Gather journal action
- collapse back to `gather.main`

**Renderer requirements**

- journal is a full-pane text-log/state view, not split workbench content

**Required widget test**

- gather journal replaces the main workbench and restores correctly

**Required screenshot artifact**

- `03-gather-journal.png`

**Completion checklist**

- [ ] full-pane takeover matches Textual
- [ ] collapse behavior matches Textual

### `gather.source_detail`

**Expected sections**

- top numbered tab strip
- `Current Subject: ...`
- full-width `Source Detail`

**Expected pane layout**

- single expanded source-detail pane

**Expected controls**

- collapse control returns to `gather.main`

**Expected transitions**

- enter from Gather source-set expansion
- collapse back to `gather.main`

**Renderer requirements**

- source detail uses the Textual source detail form, not generic key/value fallback when richer structure exists

**Required widget test**

- gather source-detail state replaces the main workbench and restores correctly

**Required screenshot artifact**

- `02-gather-source-detail.png`

**Completion checklist**

- [ ] full-pane state matches Textual
- [ ] content structure matches Textual source detail

### `itemize.main`

**Expected sections**

- top numbered tab strip
- `Current Subject: ...`
- `Previous Subject` and `Next Subject`
- `Current Step`
- `Itemize Status`
- `More Actions`
- `Decision Role`
- `Hold For Merge`
- `Item Inventory`
- `Item Detail`

**Expected pane layout**

- gate/status row at top
- `More Actions` controls row beneath
- left inventory / right detail workbench

**Expected controls**

- itemize gate actions in Textual grouping
- decision role selector
- hold-for-merge switch

**Expected transitions**

- item selection updates `Item Detail`
- gate actions preserve state and selection behavior

**Renderer requirements**

- inventory renders in the same structured inventory form as Textual
- detail pane renders as Textual structured item detail
- no blob-text fallback for inventory rows

**Required widget test**

- structured itemize inventory and detail match Textual shell behavior

**Required screenshot artifact**

- `04-itemize-main.png`

**Completion checklist**

- [ ] inventory uses structured inventory renderer
- [ ] current-step content is concise and structured
- [ ] controls row mirrors Textual

### `draft.compose`

**Expected sections**

- top numbered tab strip
- `Current Subject: ...`
- `Previous Subject` and `Next Subject`
- `Current Step`
- `Draft Status`
- `More Actions`
- `Selected Item`
- compose control row
- `Draft Item Inventory`
- detail pane

**Expected pane layout**

- gate/status row at top
- `More Actions` block with selection controls beneath
- left draft inventory / right draft detail

**Expected controls**

- semantic kind
- render style
- evidence mode
- transform mode
- in-decision or equivalent inclusion control

**Expected transitions**

- selection changes update detail pane
- gate actions move into review or draft lens states as Textual does

**Renderer requirements**

- `Draft Item Inventory` renders in the same structured table/tree form as Textual
- detail pane preserves Textual draft detail structure

**Required widget test**

- structured draft compose inventory matches Textual shell behavior

**Required screenshot artifact**

- `05-draft-compose.png`

**Completion checklist**

- [ ] inventory is not blob text
- [ ] `More Actions` controls match Textual grouping
- [ ] pane titles match Textual

### `draft.frame`

**Expected sections**

- top numbered tab strip
- `Current Subject: ...`
- `Current Step`
- `Draft Status`
- `More Actions`
- `Selected Change`
- `View`
- lens strip with `Frame`, `Model`, `Explore`
- `Case Objects`
- `Case Frame`
- right draft detail pane
- `Issues & Validation`

**Expected pane layout**

- three-pane upper workbench
- full-width lower validation pane

**Expected controls**

- selected change summary
- change type
- change role
- decision policy
- lens strip

**Expected transitions**

- selecting `Frame` marks the correct active lens
- moving to other draft lenses preserves context

**Renderer requirements**

- center pane renders `Case Frame` in Textual-structured form
- left case-object inventory is structured and selectable

**Required widget test**

- draft frame state renders proper lens and pane titles

**Required screenshot artifact**

- `06-draft-frame.png`

**Completion checklist**

- [ ] `Frame` lens selection matches Textual
- [ ] three-pane workbench matches Textual
- [ ] lower validation pane remains present

### `draft.model`

**Expected sections**

- same global shell as `draft.frame`
- center pane titled `Transformation Model`

**Expected pane layout**

- same as other draft lens states

**Expected controls**

- same as other draft lens states

**Expected transitions**

- selecting `Model` marks the correct active lens

**Renderer requirements**

- center pane renders model summary/structure in the Textual model form

**Required widget test**

- draft model state renders proper lens and model pane title

**Required screenshot artifact**

- `07-draft-model.png`

**Completion checklist**

- [ ] `Model` lens selection matches Textual
- [ ] model pane content is structured, not blob text

### `draft.explore`

**Expected sections**

- same global shell as `draft.frame`
- center pane titled `Explore Alternatives`

**Expected pane layout**

- same as other draft lens states

**Expected controls**

- same as other draft lens states

**Expected transitions**

- selecting `Explore` marks the correct active lens

**Renderer requirements**

- center pane renders alternatives/recommendation structure in the Textual explore form

**Required widget test**

- draft explore state renders proper lens and explore pane title

**Required screenshot artifact**

- `08-draft-explore.png`

**Completion checklist**

- [ ] `Explore` lens selection matches Textual
- [ ] explore pane uses structured alternative view

### `review.main`

**Expected sections**

- top numbered tab strip
- `Current Subject: ...`
- `Previous Subject` and `Next Subject`
- `Current Step`
- `Review Status`
- `More Actions`
- `Report Plan`
- `Selected Item`
- `Selected Section`
- `Report Scope`
- `Selection Details`

**Expected pane layout**

- gate/status row
- `More Actions` block with report-plan controls
- left report scope / right selection details

**Expected controls**

- review/report-plan actions
- output style
- report structure
- diff baseline
- selected item + in-report
- selected section + in-report
- journal action

**Expected transitions**

- journal action opens `review.journal`
- selected item/section update the detail pane

**Renderer requirements**

- report scope uses the Textual scope-tree form
- selection detail uses the Textual scope-detail form

**Required widget test**

- review main renders all report-plan sections and workbench panes

**Required screenshot artifact**

- `09-review-main.png`

**Completion checklist**

- [ ] review controls match Textual grouping
- [ ] scope/detail split matches Textual
- [ ] journal entry path works

### `review.journal`

**Expected sections**

- top numbered tab strip
- `Current Subject: ...`
- full-width `Review Journal`
- `Review Status`

**Expected pane layout**

- journal full pane above
- review status pane below

**Expected controls**

- collapse control returns to `review.main`

**Expected transitions**

- open from review journal action
- collapse back to `review.main`

**Renderer requirements**

- journal remains full-pane
- review status remains structured key/value content

**Required widget test**

- review journal replaces the main workbench and restores correctly

**Required screenshot artifact**

- `10-review-journal.png`

**Completion checklist**

- [ ] full-pane journal state matches Textual
- [ ] review status remains visible below the journal

### `publication.main`

**Expected sections**

- top numbered tab strip
- `Current Subject: ...`
- `Previous Subject` and `Next Subject`
- `Current Step`
- `Publication Status`
- `More Actions`
- `Report Plan`
- `Selected Support`
- `Selected Item`
- `Selected Section`
- `Report Scope`
- `Selection Details`

**Expected pane layout**

- gate/status row
- `More Actions` block with publication/report controls
- left report scope / right selection details

**Expected controls**

- publication/release actions
- output style
- report structure
- diff baseline
- selected support + in-report + use
- selected item + in-report
- selected section + in-report

**Expected transitions**

- publication actions preserve selection context
- scope/detail behavior matches review/publication Textual behavior

**Renderer requirements**

- report scope uses the Textual publication scope form
- selection details use the Textual publication detail form

**Required widget test**

- publication main renders all required report-plan and selection sections

**Required screenshot artifact**

- `11-publication-main.png`

**Completion checklist**

- [ ] publication controls match Textual grouping
- [ ] scope/detail split matches Textual
- [ ] support controls match Textual behavior

## Renderer Parity Checklist

### `Current Step`

- Textual visual form:
  - concise structured gate summary
  - explicit `Last Action`
  - explicit `Do this now`
  - supporting structured lines, not a prose blob
- Flutter renderer:
  - dedicated current-step renderer
- Unacceptable fallback:
  - dumping phase-view text as long-form prose

### `Status panes`

- Textual visual form:
  - labeled key/value rows
- Flutter renderer:
  - structured key/value renderer
- Unacceptable fallback:
  - flattened paragraph text

### `Item Inventory`

- Textual visual form:
  - structured inventory with selection semantics
- Flutter renderer:
  - dedicated item inventory renderer
- Unacceptable fallback:
  - generic line list or blob text

### `Item Detail`

- Textual visual form:
  - structured detail pane with grouped facts
- Flutter renderer:
  - structured detail renderer
- Unacceptable fallback:
  - unparsed multiline dump where Textual uses grouped fields

### `Draft Item Inventory`

- Textual visual form:
  - structured draft inventory/table/tree
- Flutter renderer:
  - dedicated draft inventory renderer
- Unacceptable fallback:
  - generic line list or paragraph blob

### `Draft lens workbench panes`

- Textual visual form:
  - distinct structured forms for `Frame`, `Model`, and `Explore`
- Flutter renderer:
  - dedicated per-lens structured center-pane rendering
- Unacceptable fallback:
  - single generic detail renderer for all lens states

### `Report Scope`

- Textual visual form:
  - structured scope tree
- Flutter renderer:
  - dedicated report scope renderer
- Unacceptable fallback:
  - plain text list without tree/scope semantics

### `Selection Details`

- Textual visual form:
  - structured selected entity detail
- Flutter renderer:
  - structured detail renderer
- Unacceptable fallback:
  - flattened text dump

### `Journal full-pane states`

- Textual visual form:
  - single-pane expanded journal state
- Flutter renderer:
  - dedicated full-pane journal shell state
- Unacceptable fallback:
  - journal embedded as one more normal pane in the main workbench

### `Source Detail`

- Textual visual form:
  - single-pane expanded detail state
- Flutter renderer:
  - dedicated full-pane source-detail shell state
- Unacceptable fallback:
  - reusing the main gather split when detail mode is active

## Behavioral Parity Checklist

- [x] previous/next subject switching matches Textual shell behavior
- [x] journal/detail expand-collapse matches Textual shell behavior
- [x] draft `Frame`/`Model`/`Explore` switching matches Textual shell behavior
- [x] per-phase action visibility and grouping match Textual at the shell-layout level
- [x] selected item, selected section, and selected support controls behave like Textual
- [x] full-pane states replace the correct workbench instead of layering on top of it
- [x] panel-shell click-to-focus behavior matches Textual wrapper targeting
- [x] focused-pane scroll ownership matches Textual
- [x] fixed-height workbench sizing under the tab strip matches Textual
- [x] maximized/detached/info-pane behavior matches Textual where available
- [x] same-subject DST-routing gate states that are already proven in backend/Textual BDDs are mirrored in Flutter widget tests

## Test and Screenshot Gates

Required widget test coverage:

- [x] section/title presence per target state
- [x] renderer form parity for critical panes
- [x] interaction parity for inventory and scope panes
- [x] draft lens transitions
- [x] journal/detail state replacement behavior
- [x] panel click-focus behavior
- [x] pane-local wheel and scroll behavior
- [x] fixed-height layout behavior
- [x] weak-prose `v10` and same-subject `v2 -> v10` workflow-routing BDDs are mirrored in Flutter
- [x] audited adjacent Textual/backend BDDs with Flutter-visible outcomes either have Flutter mirrors or an explicit rationale for not mirroring them

Required webdriver screenshot artifacts:

- [x] `01-gather-main.png`
- [x] `02-gather-source-detail.png`
- [x] `03-gather-journal.png`
- [x] `04-itemize-main.png`
- [x] `05-draft-compose.png`
- [x] `06-draft-frame.png`
- [x] `07-draft-model.png`
- [x] `08-draft-explore.png`
- [x] `09-review-main.png`
- [x] `10-review-journal.png`
- [x] `11-publication-main.png`

## Completion Criteria

Implementation is not complete until all of the following are true:

- [ ] every target shell state checklist is complete
- [ ] renderer parity checklist has no open mismatches
- [ ] behavioral parity checklist has no open mismatches
- [x] all required widget tests pass
- [x] all named screenshot artifacts are generated
- [ ] screenshot review shows structural equivalence with Textual
- [ ] interaction review shows that pane clicks, wheel scroll, and fixed-height behavior are equivalent to Textual
- [x] Flutter has mirrored BDD coverage for the visible DST-routing and decision-analysis scenarios that are already covered in backend/Textual layers
