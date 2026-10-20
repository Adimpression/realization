# Material 3 as Terminal Encoding of Cross-Domain Design Mediation

Material 3 components are officially grouped by purpose into **action, communication, containment, navigation, selection, and text input**; these are not the theory’s primitive categories, but framework-level encodings of deeper interaction obligations. ([Material Design][1])

---

# I. Mapping Form

The correct derivation is:

[
O \rightarrow I \rightarrow T \rightarrow V \rightarrow G \rightarrow E_{M3}
]

Where:

* (O) = user objective
* (I) = digital user intent
* (T) = task morphology
* (V) = interaction invariant
* (G) = interaction obligation
* (E_{M3}) = Material 3 component embodiment

Material 3 components are therefore **not selected directly from objectives**.

They are selected from **interaction obligations**.

---

# II. Material 3 Component Families as Encodings

## 1. Action Components

Material action components include buttons, icon buttons, segmented buttons, and FABs; Material describes buttons as helping people take actions, while FABs keep a key action highly available. ([Material Design][2])

### Upstream derivation

[
\text{Objective} \rightarrow \text{trigger / confirm / select mode / perform primary act} \rightarrow \text{action obligation} \rightarrow \text{button family}
]

### Use when the required obligation is:

* initiate an operation
* confirm a decision
* expose a primary action
* choose between mutually exclusive action modes
* provide a compact action shortcut

### Component mapping

| Interaction obligation                | Material 3 component    |
| ------------------------------------- | ----------------------- |
| Primary committed action              | Filled button           |
| Secondary action                      | Outlined or text button |
| Low-emphasis action                   | Text button             |
| Iconic compact action                 | Icon button             |
| Persistent dominant action            | FAB                     |
| Persistent dominant action with label | Extended FAB            |
| Mutually exclusive local modes        | Segmented button        |

### Theory condition

Use an action component when the dominant intent is:

[
I \in {\text{trigger}, \text{confirm}, \text{select}, \text{modify}}
]

and the task requires an explicit agent commitment.

---

## 2. Communication Components

Material communication components provide information by alerting users, showing status, indicating progress, or giving brief process messages through elements such as badges, progress indicators, and snackbars. ([Android Developers][3])

### Upstream derivation

[
\text{Objective} \rightarrow \text{monitor / verify / recover} \rightarrow \text{feedback obligation} \rightarrow \text{communication component}
]

### Use when the required obligation is:

* reveal system state
* communicate progress
* notify completion
* expose interruption
* support recovery after action
* draw attention to changed status

### Component mapping

| Interaction obligation           | Material 3 component                  |
| -------------------------------- | ------------------------------------- |
| Brief post-action feedback       | Snackbar                              |
| Ongoing operation state          | Linear or circular progress indicator |
| Count or status marker           | Badge                                 |
| Blocking or consequential notice | Dialog                                |
| Contextual explanation           | Tooltip                               |

### Theory condition

Use a communication component when:

[
V \in {\text{feedback}, \text{state_awareness}, \text{salience}, \text{recoverability}}
]

and the user must update their mental model of system state.

---

## 3. Containment Components

Material containment components hold information and actions; examples include cards, dialogs, bottom sheets, side sheets, carousels, tooltips, lists, and related containers. Cards specifically display content and actions about a single subject. ([Android Developers][3])

### Upstream derivation

[
\text{Objective} \rightarrow \text{inspect / compare / contextualize} \rightarrow \text{grouping obligation} \rightarrow \text{containment component}
]

### Use when the required obligation is:

* group related information
* preserve object identity
* expose local actions
* separate transient from persistent information
* focus attention on a bounded subject
* reveal secondary detail without destroying context

### Component mapping

| Interaction obligation                    | Material 3 component |
| ----------------------------------------- | -------------------- |
| Represent one object or subject           | Card                 |
| Represent repeated homogeneous objects    | List                 |
| Require focused interruption              | Dialog               |
| Show contextual secondary content         | Bottom sheet         |
| Show supporting content on larger layouts | Side sheet           |
| Expose compact contextual commands        | Menu                 |
| Explain one element locally               | Tooltip              |
| Browse sequential visual content          | Carousel             |

### Theory condition

Use containment when:

[
I \in {\text{inspect}, \text{compare}, \text{learn}, \text{modify}}
]

and the task requires local coherence around a bounded object, state, or decision.

---

## 4. Navigation Components

Material navigation components help people move through the UI; navigation bars are for switching between views on smaller devices, while navigation drawers provide access to destinations and are more suitable on larger devices. ([Material Design][4])

### Upstream derivation

[
\text{Objective} \rightarrow \text{navigate / locate / switch context} \rightarrow \text{wayfinding obligation} \rightarrow \text{navigation component}
]

### Use when the required obligation is:

* move between major destinations
* preserve orientation
* switch among sibling views
* expose app structure
* support repeated access to important areas
* maintain spatial or conceptual continuity

### Component mapping

| Interaction obligation                                 | Material 3 component |
| ------------------------------------------------------ | -------------------- |
| Switch among top-level destinations on compact screens | Navigation bar       |
| Switch among top-level destinations on medium screens  | Navigation rail      |
| Expose many destinations or hierarchy                  | Navigation drawer    |
| Navigate peer sections within a context                | Tabs                 |
| Provide screen-level title and actions                 | Top app bar          |
| Preserve action/navigation affordance near bottom edge | Bottom app bar       |

### Theory condition

Use navigation when:

[
I \in {\text{navigate}, \text{locate}, \text{monitor}, \text{switch}}
]

and the task morphology is branching, recurrent, or multi-context.

---

## 5. Selection Components

Material selection components let people specify choices through elements such as checkboxes, radio buttons, chips, switches, and sliders. ([Android Developers][3])

### Upstream derivation

[
\text{Objective} \rightarrow \text{choose / configure / filter} \rightarrow \text{selection obligation} \rightarrow \text{selection component}
]

### Use when the required obligation is:

* choose one from many
* choose many from many
* toggle a binary state
* adjust a continuous value
* filter a set
* express preference
* configure system behavior

### Component mapping

| Interaction obligation                   | Material 3 component |
| ---------------------------------------- | -------------------- |
| Choose one from a small explicit set     | Radio buttons        |
| Choose many from a set                   | Checkboxes           |
| Toggle persistent binary state           | Switch               |
| Choose from compact categorical options  | Chips                |
| Filter visible content                   | Filter chips         |
| Adjust continuous or ordinal value       | Slider               |
| Choose one mode among local alternatives | Segmented button     |

### Theory condition

Use selection when:

[
I \in {\text{select}, \text{compare}, \text{modify}, \text{configure}}
]

and the user must specify a value, preference, state, or constraint.

---

## 6. Text Input Components

Material text input components allow people to enter and edit text; text fields are the central component for this class. ([Android Developers][3])

### Upstream derivation

[
\text{Objective} \rightarrow \text{enter / edit / express} \rightarrow \text{symbolic input obligation} \rightarrow \text{text input component}
]

### Use when the required obligation is:

* capture open-ended language
* enter identifiers
* search
* annotate
* name
* describe
* provide structured symbolic data

### Component mapping

| Interaction obligation | Material 3 component                                   |
| ---------------------- | ------------------------------------------------------ |
| Short symbolic entry   | Text field                                             |
| Longer symbolic entry  | Multi-line text field                                  |
| Search intent          | Search field / search bar                              |
| Structured entry       | Text field with validation, helper text, prefix/suffix |
| Error-prone entry      | Text field with constraints and inline feedback        |

### Theory condition

Use text input when:

[
I \in {\text{enter}, \text{modify}, \text{search}, \text{express}}
]

and the required value cannot be adequately represented as selection.

---

# III. Reverse Index: From Intent to Material 3

## Intent: Detect

The user must notice that something exists or has changed.

| Obligation             | Component                                         |
| ---------------------- | ------------------------------------------------- |
| Increase salience      | Badge                                             |
| Indicate changed state | Badge, snackbar                                   |
| Surface warning        | Dialog, banner-like region if available in system |
| Show ongoing process   | Progress indicator                                |

---

## Intent: Locate

The user must find a destination, object, or state.

| Obligation                   | Component                                    |
| ---------------------------- | -------------------------------------------- |
| Expose destination structure | Navigation drawer, rail, bar                 |
| Show current place           | Top app bar, tabs, selected navigation state |
| Find item in collection      | Search bar, list                             |
| Reveal hierarchy             | Drawer, list, tabs                           |

---

## Intent: Inspect

The user must examine a subject.

| Obligation                          | Component                  |
| ----------------------------------- | -------------------------- |
| Preserve object boundary            | Card                       |
| Show detailed secondary information | Bottom sheet, side sheet   |
| Show full focused detail            | Dialog or destination page |
| Explain local meaning               | Tooltip                    |

---

## Intent: Compare

The user must evaluate alternatives.

| Obligation                        | Component                                    |
| --------------------------------- | -------------------------------------------- |
| Present parallel options          | Cards, lists                                 |
| Expose differentiating attributes | Cards, tables if available, lists            |
| Filter alternatives               | Filter chips                                 |
| Sort or refine                    | Menus, chips                                 |
| Select final option               | Radio buttons, cards with selection, buttons |

---

## Intent: Select

The user must choose.

| Obligation           | Component        |
| -------------------- | ---------------- |
| Single choice        | Radio buttons    |
| Multiple choice      | Checkboxes       |
| Binary state         | Switch           |
| Mode selection       | Segmented button |
| Compact option token | Chips            |

---

## Intent: Enter

The user must provide symbolic information.

| Obligation      | Component                         |
| --------------- | --------------------------------- |
| Free-form input | Text field                        |
| Search query    | Search bar                        |
| Long expression | Multi-line text field             |
| Validated entry | Text field with helper/error text |

---

## Intent: Modify

The user must change an existing state.

| Obligation              | Component                             |
| ----------------------- | ------------------------------------- |
| Edit object fields      | Text fields, selection controls       |
| Adjust value            | Slider                                |
| Change setting          | Switch                                |
| Apply modification      | Button                                |
| Preserve recoverability | Snackbar with undo, confirmation flow |

---

## Intent: Trigger

The user must start an operation.

| Obligation              | Component              |
| ----------------------- | ---------------------- |
| High-priority action    | Filled button, FAB     |
| Repeated primary action | FAB                    |
| Contextual action       | Icon button, menu item |
| Low-emphasis action     | Text button            |

---

## Intent: Verify

The user must check correctness before commitment.

| Obligation                   | Component                    |
| ---------------------------- | ---------------------------- |
| Summarize state              | Card, list, review screen    |
| Confirm consequential action | Dialog                       |
| Show validation result       | Text field state, snackbar   |
| Show progress or completion  | Progress indicator, snackbar |

---

## Intent: Confirm

The user must make a deliberate commitment.

| Obligation               | Component                      |
| ------------------------ | ------------------------------ |
| Low-risk confirmation    | Filled button                  |
| High-risk confirmation   | Dialog with explicit action    |
| Destructive confirmation | Dialog plus constrained action |
| Reversible confirmation  | Button plus snackbar undo      |

---

## Intent: Monitor

The user must maintain awareness over time.

| Obligation              | Component                                  |
| ----------------------- | ------------------------------------------ |
| Show persistent state   | Cards, lists, top app bar status, badges   |
| Show active process     | Progress indicator                         |
| Indicate abnormal state | Badge, dialog, snackbar depending severity |
| Drill into condition    | Card, list item, sheet                     |

---

## Intent: Recover

The user must return from error or undesired state.

| Obligation             | Component                                  |
| ---------------------- | ------------------------------------------ |
| Communicate error      | Text field error, snackbar, dialog         |
| Offer reversal         | Snackbar with undo                         |
| Explain correction     | Helper text, tooltip, dialog               |
| Prevent repeated error | Disabled controls, validation, constraints |

---

# IV. Reverse Index: From Task Morphology to Material Structure

## One-shot task

Use:

* button
* text field
* simple selection
* snackbar feedback

Avoid:

* complex navigation
* multi-stage containers

---

## Sequential task

Use:

* progressive screens
* top app bar
* buttons
* validation
* review/confirmation
* progress indicators when latency exists

Use when:

[
T = \text{sequential}
]

and order matters.

---

## Branching task

Use:

* navigation drawer
* navigation rail
* tabs
* lists
* search
* filters

Use when:

[
T = \text{branching}
]

and the user may pursue multiple paths.

---

## Iterative task

Use:

* editable cards/lists
* text fields
* sliders
* switches
* snackbar undo
* persistent save state

Use when:

[
T = \text{iterative}
]

and refinement matters.

---

## Continuous monitoring task

Use:

* dashboard-like cards
* badges
* progress indicators
* persistent navigation
* state-bearing app bars
* alerting components

Use when:

[
T = \text{continuous}
]

and the user must maintain state awareness.

---

## Interrupt-driven task

Use:

* badges for low-to-medium salience
* snackbars for brief feedback
* dialogs for blocking or consequential interruptions
* navigation to detail when action is required

Use when:

[
T = \text{interrupt_driven}
]

and the system initiates attention demand.

---

## High-risk task

Use:

* explicit confirmation
* constrained actions
* dialogs
* validation
* redundancy
* recoverability
* clear error states

Avoid:

* gesture-only controls
* hidden actions
* ambiguous icon-only actions
* transient-only critical messages

---

# V. Component Choice Rules

## Rule 1: Button vs FAB

Use a **button** when the action belongs to a local context.

Use a **FAB** when the action is:

* primary
* frequent
* globally relevant to the current screen
* beneficial when always reachable

Formal condition:

[
\text{FAB} \iff I=\text{trigger} \land Priority=\text{primary} \land Scope=\text{screen/global}
]

---

## Rule 2: Button vs Icon Button

Use a **button** when the action needs semantic clarity.

Use an **icon button** when:

* space is constrained
* the action is familiar
* the icon is unambiguous
* the action is secondary or contextual

Formal condition:

[
\text{IconButton} \iff I=\text{trigger} \land Space=\text{constrained} \land Meaning=\text{recognizable}
]

---

## Rule 3: Dialog vs Snackbar

Use a **snackbar** for brief, non-blocking feedback after an action.

Use a **dialog** when user attention must be interrupted because the decision is blocking, consequential, or requires explicit confirmation.

Formal condition:

[
\text{Dialog} \iff Risk=\text{high} \lor Commitment=\text{required} \lor Flow=\text{blocked}
]

[
\text{Snackbar} \iff Feedback=\text{brief} \land Blocking=\text{false}
]

---

## Rule 4: Card vs List

Use a **card** when each item has object identity, heterogeneous content, or local actions.

Use a **list** when items are homogeneous, scannable, and primarily navigational or selectable.

Formal condition:

[
\text{Card} \iff Subject=\text{bounded object} \land (Content=\text{rich} \lor Actions=\text{local})
]

[
\text{List} \iff Items=\text{homogeneous} \land Intent \in {\text{locate}, \text{inspect}, \text{select}}
]

---

## Rule 5: Bottom Sheet vs Dialog

Use a **bottom sheet** when the user needs contextual secondary content while preserving relation to the current screen.

Use a **dialog** when the current flow must pause for a focused decision.

Formal condition:

[
\text{BottomSheet} \iff ContextPreservation=\text{high} \land Interruption=\text{partial}
]

[
\text{Dialog} \iff Focus=\text{exclusive} \land Decision=\text{required}
]

---

## Rule 6: Tabs vs Navigation Bar/Rail/Drawer

Use **tabs** for peer sections inside the same conceptual destination.

Use **navigation bar/rail/drawer** for top-level destinations.

Formal condition:

[
\text{Tabs} \iff Destinations=\text{sibling views within same context}
]

[
\text{Navigation} \iff Destinations=\text{top-level app areas}
]

Material itself distinguishes navigation bars as view-switching on smaller devices and drawers as access to destinations, especially on larger devices. ([Material Design][4])

---

## Rule 7: Checkbox vs Radio vs Switch

Use **radio buttons** for one-of-many selection.

Use **checkboxes** for many-of-many selection.

Use **switches** for immediate binary state changes, usually settings.

Formal condition:

[
\text{Radio} \iff Cardinality=1\text{ of }N
]

[
\text{Checkbox} \iff Cardinality=K\text{ of }N
]

[
\text{Switch} \iff State=\text{binary} \land Effect=\text{immediate/persistent}
]

---

## Rule 8: Chips vs Segmented Buttons

Use **chips** for lightweight filtering, categorization, or compact selections.

Use **segmented buttons** for a small set of mutually exclusive modes or options with stronger control semantics.

Formal condition:

[
\text{Chip} \iff Selection=\text{lightweight/contextual/filtering}
]

[
\text{SegmentedButton} \iff Selection=\text{small exclusive control set}
]

---

## Rule 9: Progress Indicator vs Snackbar

Use a **progress indicator** while an operation is ongoing.

Use a **snackbar** after a brief operation completes or fails non-critically.

Formal condition:

[
\text{ProgressIndicator} \iff State=\text{ongoing} \land Latency>\text{perceptual threshold}
]

[
\text{Snackbar} \iff State=\text{completed/failed} \land Message=\text{brief} \land Blocking=\text{false}
]

---

## Rule 10: Text Field vs Selection

Use a **text field** only when the answer space is open, large, user-generated, or not enumerable.

Use selection controls when valid values are known and bounded.

Formal condition:

[
\text{TextField} \iff ValueSpace=\text{open}
]

[
\text{SelectionControl} \iff ValueSpace=\text{bounded}
]

---

# VI. General Decision Procedure

For any user objective:

## Step 1: Decompose objective into intents

Example:

[
O=\text{manage subscriptions}
]

becomes:

[
I={\text{locate}, \text{inspect}, \text{modify}, \text{confirm}, \text{recover}}
]

---

## Step 2: Determine task morphology

[
T={\text{branching}, \text{iterative}, \text{high-risk if cancellation/payment}}
]

---

## Step 3: Derive invariants

[
V={\text{visibility}, \text{mapping}, \text{feedback}, \text{constraint}, \text{recoverability}}
]

---

## Step 4: Convert invariants into obligations

* subscriptions must be scannable
* current status must be visible
* modification actions must be locally available
* destructive actions must require confirmation
* reversible actions should support undo
* completed actions must provide feedback

---

## Step 5: Select Material 3 components

* list or cards for subscriptions
* badges/status labels for active states
* buttons/icon buttons for local actions
* dialog for cancellation confirmation
* snackbar for success/undo
* navigation bar/rail/drawer for major app areas

---

# VII. Canonical Component Selection Matrix

| If the user must…         | Intent        | Invariant         | Obligation                       | Material 3 encoding        |
| ------------------------- | ------------- | ----------------- | -------------------------------- | -------------------------- |
| Move between major areas  | navigate      | state awareness   | expose destination structure     | Navigation bar/rail/drawer |
| Move within peer sections | navigate      | mapping           | expose sibling views             | Tabs                       |
| Start a primary action    | trigger       | salience          | make primary action prominent    | FAB / filled button        |
| Start a contextual action | trigger       | mapping           | bind action to object/context    | Icon button / menu         |
| Choose one option         | select        | constraint        | enforce single selection         | Radio / segmented button   |
| Choose many options       | select        | constraint        | allow multi-selection            | Checkbox                   |
| Toggle a setting          | modify        | feedback          | show binary state                | Switch                     |
| Enter unknown value       | enter         | expressiveness    | accept open symbolic input       | Text field                 |
| Filter content            | locate/select | cognitive economy | narrow visible set               | Filter chips               |
| Inspect one object        | inspect       | grouping          | preserve subject boundary        | Card                       |
| Scan many similar objects | locate        | legibility        | show homogeneous collection      | List                       |
| Confirm risky act         | confirm       | safety            | require deliberate commitment    | Dialog                     |
| Show brief result         | verify        | feedback          | communicate non-blocking outcome | Snackbar                   |
| Show ongoing process      | monitor       | state awareness   | reveal latency/progress          | Progress indicator         |
| Reveal secondary context  | inspect       | continuity        | preserve main context            | Bottom sheet / side sheet  |
| Explain local meaning     | learn         | learnability      | provide nearby clarification     | Tooltip                    |
| Show status/count         | monitor       | salience          | attach state to object/location  | Badge                      |

---

# VIII. Component Derivation Examples

## Example 1: “User wants to create a new task”

[
O=\text{create task}
]

[
I={\text{trigger}, \text{enter}, \text{confirm}, \text{verify}}
]

[
T=\text{one_shot or sequential}
]

[
V={\text{salience}, \text{feedback}, \text{recoverability}}
]

Material encoding:

* FAB if creation is the primary recurrent screen action
* text fields for task content
* filled button for save
* snackbar for confirmation
* snackbar undo if creation is reversible

---

## Example 2: “User wants to choose a plan”

[
O=\text{choose plan}
]

[
I={\text{inspect}, \text{compare}, \text{select}, \text{confirm}}
]

[
T=\text{branching + decision}
]

[
V={\text{legibility}, \text{mapping}, \text{constraint}, \text{trustworthiness}}
]

Material encoding:

* cards for plan objects
* chips for filters
* radio buttons or selectable cards for single choice
* button for continuation
* dialog only if commitment is consequential

---

## Example 3: “User wants to monitor delivery status”

[
O=\text{monitor delivery}
]

[
I={\text{monitor}, \text{inspect}, \text{verify}, \text{recover}}
]

[
T=\text{continuous + event-driven}
]

[
V={\text{state_awareness}, \text{feedback}, \text{salience}}
]

Material encoding:

* cards for active deliveries
* progress indicator for current stage
* badge for updates
* snackbar for transient changes
* bottom sheet for delivery details
* button for corrective action

---

## Example 4: “User wants to delete an account”

[
O=\text{delete account}
]

[
I={\text{inspect}, \text{confirm}, \text{trigger}, \text{recover}}
]

[
T=\text{sequential + high-risk}
]

[
V={\text{safety}, \text{constraint}, \text{feedback}, \text{recoverability}}
]

Material encoding:

* explanatory content in page/card
* destructive action button
* dialog for confirmation
* text field if explicit phrase confirmation is required
* progress indicator if deletion takes time
* snackbar or confirmation screen after completion

---

# IX. The Material 3 “Compiler” Rule

A Material 3 component should be chosen only when the following chain is valid:

[
\text{Component} \Leftarrow \text{Embodiment} \Leftarrow \text{Obligation} \Leftarrow \text{Invariant} \Leftarrow \text{Task Morphology} \Leftarrow \text{Intent} \Leftarrow \text{Objective}
]

So the design question is never:

> “Should we use a card?”

It is:

> “Does the user objective produce an inspect/compare obligation over a bounded subject that requires visual grouping and local actions?”

If yes, use a card.

---

# X. Final Decision Grammar

## Use navigation components when:

[
I=\text{navigate}
]

and the obligation is to expose destination structure.

---

## Use action components when:

[
I \in {\text{trigger}, \text{confirm}, \text{modify}}
]

and the obligation is to make an operation executable.

---

## Use containment components when:

[
I \in {\text{inspect}, \text{compare}, \text{learn}}
]

and the obligation is to bind related information and actions into a coherent unit.

---

## Use communication components when:

[
I \in {\text{monitor}, \text{verify}, \text{recover}}
]

and the obligation is to update the user’s model of state, progress, error, or outcome.

---

## Use selection components when:

[
I=\text{select}
]

and the obligation is to constrain choice among known alternatives.

---

## Use text input components when:

[
I=\text{enter}
]

and the obligation is to capture open symbolic content.

---

# XI. Final Statement

Material 3 components are the **digital embodiment vocabulary** of the theory.

The theory does not say:

[
\text{User wants X} \rightarrow \text{Use component Y}
]

It says:

[
\text{User objective}
\rightarrow
\text{digital intent}
\rightarrow
\text{task morphology}
\rightarrow
\text{interaction invariant}
\rightarrow
\text{interaction obligation}
\rightarrow
\text{Material 3 component}
]

This is the proper bridge from abstract human purpose to concrete digital interface form.

---

## XII. Extension Note

This case study shows how the mediation chain can terminate in a real framework.

It does not by itself guarantee that the implementation will preserve that chain once the system is encoded in code, revised over time, or confronted by runtime evidence.

That preservation layer is addressed in:

* [DESIGN_TYPE_SYSTEM.md](/Users/ravindranathakila/service/realized/design/DESIGN_TYPE_SYSTEM.md)
* [DESIGN_TYPE_SYSTEM_IMPLEMENTATION.md](/Users/ravindranathakila/service/realized/design/DESIGN_TYPE_SYSTEM_IMPLEMENTATION.md)

The why is simple:

* because a correct component choice can still be implemented without semantic traceability,
* because frameworks are terminal vocabularies rather than the bridge itself,
* and because a typed mediation system is what preserves the design when the implementation and the world both change.

[1]: https://m3.material.io/components "Components — Material Design 3"
[2]: https://m3.material.io/components/buttons/overview "Buttons – Material Design 3"
[3]: https://developer.android.com/design/ui/mobile/guides/components/material-overview "Material Components | Mobile"
[4]: https://m3.material.io/components/navigation-bar/overview "Navigation bar – Material Design 3"
