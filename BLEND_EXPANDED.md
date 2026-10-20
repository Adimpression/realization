# This is Blend Theory expanded according to two assumed choices, Python and Flutter

Actual design choice may wary.

## Simple version

If:

* **DNA** = the data
* **RNA** = what the data means
* **Operator** = the action

then:

* **Context** = the situation the action is happening in

Context answers questions like:

* which task is currently selected?
* which panel is open?
* which document is active?
* are we in edit mode or view mode?
* which user or role is acting?
* what item is under the mouse?
* what does “delete” mean right now?

---

# Tiny example

Suppose you have a button:

```python
Delete
```

Delete what?

Without context, the app does not know.

With context:

```python
selected_task_id = "t2"
current_panel = "task_inspector"
mode = "edit"
```

Now `DeleteSelectedTask` makes sense.

So context is the invisible background that gives meaning to actions.

---

# Easy analogy

Imagine a voice command:

> “Rename it.”

That sentence is useless without context.

Context tells you:

* what “it” is
* where you are
* whether renaming is allowed

Apps are the same.

---

# In a simple task app

## DNA

```python
doc = {
    "tasks": [
        {"id": "t1", "title": "Call client", "done": False},
        {"id": "t2", "title": "Review contract", "done": True},
    ]
}
```

## RNA

```python
task_meta = {
    "title": {"type": "string", "label": "Title", "widget": "text"},
    "done": {"type": "bool", "label": "Done", "widget": "checkbox"},
}
```

## Operator

```python
DeleteSelectedTask()
```

## Context

```python
ctx = {
    "selected_task_id": "t2",
    "mode": "edit",
    "panel": "task_list"
}
```

Now the operator can use context:

* selected task is `t2`
* mode is `edit`
* delete is allowed

---

# Without context vs with context

## Without context

```python
DeleteSelectedTask()
```

Problem:

* selected by whom?
* from which document?
* from which panel?
* which item is selected?

## With context

```python
DeleteSelectedTask().run(doc, ctx)
```

Now the operator can do the right thing.

---

# The simplest way to think about it

## DNA = the nouns

* task
* title
* done

## Operator = the verbs

* rename
* delete
* toggle

## Context = the sentence meaning

* rename **this**
* delete **that selected one**
* toggle **the active item**

Context makes verbs concrete.

---

# A minimal code version

```python
class DeleteSelectedTask:
    def run(self, doc, ctx):
        selected_id = ctx["selected_task_id"]
        doc["tasks"] = [t for t in doc["tasks"] if t["id"] != selected_id]
```

That is context in practice.

The operator itself does not hardcode `"t2"`.
It asks the context.

---

# Why this matters so much

Because many actions depend on the current situation.

Examples:

* `DeleteSelectedTask`
* `RenameActiveItem`
* `DuplicateCurrentNode`
* `ApplyToSelection`
* `OpenInspectorForFocusedObject`

These actions are impossible or awkward without context.

---

# Context is not data, but it is still state

This is important.

The document is usually **persistent state**.

Context is usually **working state**.

## Persistent state

Saved in file:

* tasks
* priorities
* settings
* relationships

## Context state

Usually not the core file:

* selected task
* hovered item
* current tab
* edit mode
* current zoom
* current tool

So context is often temporary, but still essential.

---

# Flutter example

Suppose your app has:

* a task list on the left
* an inspector on the right

When the user clicks a task:

```python
ctx["selected_task_id"] = "t1"
rerender()
```

Now the inspector uses context:

```python
def build_inspector(doc, ctx):
    task_id = ctx["selected_task_id"]
    task = find_task(doc, task_id)
    return build_task_editor(task)
```

So context determines what the panel shows.

That is a very concrete example.

---

# Context also affects operators

Example:

```python
class ToggleDoneForSelectedTask:
    def run(self, doc, ctx):
        task = find_task(doc, ctx["selected_task_id"])
        task["done"] = not task["done"]
```

Again:

* operator = action
* context = target/situation

---

# Context can also affect visibility

Suppose the inspector should only show `approval_notes` if:

* the selected task is high priority
* and the app is in review mode

That means UI generation can depend on:

* DNA: actual task values
* RNA: metadata
* context: current mode and selection

Example:

```python
def should_show_approval_notes(task, ctx):
    return task["priority"] >= 4 and ctx["mode"] == "review"
```

That is where the UI starts feeling dynamic.

---

# Context can also affect permissions

Example:

```python
ctx = {
    "selected_task_id": "t1",
    "mode": "edit",
    "user_role": "viewer"
}
```

Then:

```python
class DeleteSelectedTask:
    def can_run(self, doc, ctx):
        return ctx["user_role"] == "admin"
```

So context can decide:

* what the user can see
* what the user can do
* what commands are enabled

---

# The full simple stack

The stack consists of five layers:

## 1. DNA

The actual document.

```python
{"id": "t1", "title": "Call client", "done": False}
```

## 2. RNA

Metadata describing fields.

```python
"title": {"type": "string", "label": "Title"}
```

## 3. Operators

Allowed actions.

```python
RenameTask("t1", "Call VIP client")
```

or

```python
RenameSelectedTask("Call VIP client")
```

## 4. Context

Current situation.

```python
{"selected_task_id": "t1", "mode": "edit"}
```

## 5. Renderer

Builds UI from document + metadata + context.

---

# Why Blender needs context so much

In a simple app, context may just be:

* selected task
* current tab

In a complex tool like Blender, context is much richer:

* active object
* selected objects
* current editor area
* current mode
* current scene
* current tool
* current region

That is why Blender can have commands like:

* delete selected
* extrude selected
* apply modifier
* rename active object

without the button having to explicitly name the object every time.

Context carries the meaning.

---

# Best simple analogy

Think of a restaurant.

## DNA

The actual data:

* menu items
* orders
* tables

## RNA

Definitions:

* price is money
* quantity is integer
* status is enum

## Operators

Actions:

* place order
* cancel order
* mark served

## Context

Current situation:

* table 7 is active
* waiter is Alice
* kitchen mode is open
* selected order is #123

Without context, “cancel order” is incomplete.
With context, it becomes obvious.

---

# In your Flutter app

A good starting `context` object might be:

```python
ctx = {
    "selected_task_id": "t1",
    "active_panel": "inspector",
    "mode": "edit",
    "user_role": "editor"
}
```

Then:

* inspector uses `selected_task_id`
* toolbar uses `mode`
* buttons use `user_role`
* commands use all of them

That is already enough to make the app feel much more alive.

---

# The shortest explanation

If operators are verbs, context is what tells the verb **where, to what, and under what conditions** it applies.

---

# Even shorter

* DNA = stuff
* RNA = meaning
* Operator = action
* Context = current situation

That is the whole idea.



The final layer is UI abstraction:

* **DNA** = the data
* **RNA** = the meaning of the data
* **Operators** = the allowed actions
* **Context** = the current situation
* **UI abstraction** = the reusable visual language that turns all of that into screens and panels

## Simple version

UI abstraction means:

> you do not build every screen by hand from scratch

Instead, you create a small set of reusable UI ideas like:

* panel
* section
* property field
* button
* list
* toolbar
* inspector
* dialog

Then those UI pieces read:

* the data
* the metadata
* the current context
* the available operators

and decide what to show.

So UI abstraction is the layer that says:

**“given this kind of thing, in this situation, render it in this general way.”**

---

# The easiest analogy

Think of Google Forms.

You have:

## Data

A user’s answers:

* Name = Alice
* Age = 34
* Subscribe = true

## Metadata

The form definition:

* Name is text
* Age is a number
* Subscribe is a checkbox

## UI abstraction

The form engine itself:

* text questions become text boxes
* boolean questions become checkboxes
* grouped questions become sections

The form engine is the UI abstraction.

You are not drawing every question manually.
You are using a reusable visual system.

---

# In your app

Suppose you have this DNA:

```python id="s0s00d"
task = {
    "title": "Call client",
    "priority": 3,
    "done": False
}
```

And this RNA:

```python id="x5l1xb"
task_meta = {
    "title": {"type": "string", "label": "Title", "widget": "text"},
    "priority": {"type": "int", "label": "Priority", "widget": "slider", "min": 1, "max": 5},
    "done": {"type": "bool", "label": "Done", "widget": "checkbox"}
}
```

Then your UI abstraction is the code that says:

* text widget hint → make a `TextField`
* slider widget hint → make a `Slider`
* checkbox widget hint → make a `Checkbox`

That layer is the abstraction.

---

# So what is the abstraction actually abstracting?

It hides the low-level UI code.

Instead of writing:

```python id="6hio6x"
ft.TextField(label="Title", value=task["title"])
ft.Slider(min=1, max=5, value=task["priority"])
ft.Checkbox(label="Done", value=task["done"])
```

you write something like:

```python id="q1dka0"
build_inspector(task, task_meta, ctx)
```

That is a UI abstraction.

It turns a semantic description into concrete controls.

---

# The 5 layers together

## 1. DNA

The raw stored thing.

```python id="a0mntq"
{"title": "Call client", "priority": 3, "done": False}
```

## 2. RNA

What those fields mean.

```python id="w41hcx"
"priority" = integer, label "Priority", widget "slider", min 1, max 5
```

## 3. Operator

What actions are allowed.

```python id="ddavui"
SetPriority(task_id="t1", value=5)
```

## 4. Context

What is currently going on.

```python id="09sl96"
{"selected_task_id": "t1", "mode": "edit"}
```

## 5. UI abstraction

Reusable UI rules like:

* selected task → show inspector
* string property → render text input
* bool property → render checkbox
* if mode is view → disable editing
* if operator not allowed → disable button

That is the full picture.

---

# A simple mental model

## DNA is the spreadsheet data

Cells and values.

## RNA is the column definitions

Text, number, checkbox, allowed range.

## Operators are the menu actions

Insert row, delete row, rename item.

## Context is the current selection

Which row, which tab, which mode.

## UI abstraction is the spreadsheet program itself

The thing that knows:

* how to draw cells
* how to show a formula bar
* how to show toolbars
* how to switch based on selection

That is very close to the real idea.

---

# Why UI abstraction matters

Without it, you end up with many hardcoded screens.

Example:

* task panel manually coded
* project panel manually coded
* customer panel manually coded
* settings panel manually coded

Then every panel repeats the same logic.

With UI abstraction, you instead define reusable building blocks:

* `PropertyField`
* `PropertySection`
* `InspectorPanel`
* `CommandButton`
* `ObjectList`
* `Toolbar`

Then many screens can be assembled from the same semantic parts.

That is how systems start feeling coherent.

---

# A tiny concrete example

## Hardcoded UI

```python id="y836o4"
def build_task_panel(task):
    return ft.Column([
        ft.TextField(label="Title", value=task["title"]),
        ft.Slider(min=1, max=5, value=task["priority"]),
        ft.Checkbox(label="Done", value=task["done"]),
    ])
```

This works, but it is specific to tasks only.

## Abstract UI

```python id="z4qetx"
def build_property_field(obj, prop_meta):
    value = obj[prop_meta["key"]]

    if prop_meta["widget"] == "text":
        return ft.TextField(label=prop_meta["label"], value=value)
    if prop_meta["widget"] == "slider":
        return ft.Slider(
            min=prop_meta["min"],
            max=prop_meta["max"],
            value=value
        )
    if prop_meta["widget"] == "checkbox":
        return ft.Checkbox(label=prop_meta["label"], value=value)
```

Then:

```python id="oykdt7"
def build_inspector(obj, meta):
    return ft.Column([
        build_property_field(obj, prop)
        for prop in meta
    ])
```

This is abstraction.

Now the same inspector system can render:

* task
* project
* customer
* workflow node

if each has metadata.

---

# Where context enters the UI abstraction

Suppose editing is only allowed in `"edit"` mode.

Then the UI abstraction can use context:

```python id="y3mudi"
def build_property_field(obj, prop_meta, ctx):
    disabled = ctx["mode"] != "edit"

    if prop_meta["widget"] == "text":
        return ft.TextField(
            label=prop_meta["label"],
            value=obj[prop_meta["key"]],
            disabled=disabled,
        )
```

So the UI abstraction is not only using metadata.
It is also using context.

That is why the UI becomes dynamic.

---

# Where operators enter the UI abstraction

Suppose the field changes.

The UI should not directly mutate the object.
It should dispatch an operator.

```python id="81pl5i"
def on_title_change(e):
    run_operator(SetProperty(task_id="t1", key="title", value=e.control.value), ctx)
```

So the abstraction says:

* render a text field
* when it changes, dispatch the right operator

That is a very important pattern.

---

# A more complete picture

A property field abstraction often needs all four lower layers:

## From DNA

It gets the current value:

* `priority = 3`

## From RNA

It gets rendering rules:

* label = Priority
* widget = slider
* min = 1
* max = 5

## From context

It gets situational rules:

* selected item is this task
* mode is edit
* role is reviewer

## From operators

It gets mutation rules:

* changing this field should call `SetPriority`

So a single property field is actually the meeting point of all layers.

That is why this architecture feels interconnected.

---

# The most intuitive example: inspector panel

An inspector panel is a perfect UI abstraction.

Its job is:

> show the editable properties of the currently selected object

That means:

* **context** tells it what is selected
* **DNA** provides the selected object’s current values
* **RNA** tells it which fields exist and how they should appear
* **operators** define how edits happen
* **UI abstraction** is the inspector component itself

This is the easiest place to see all the layers together.

---

# Blender-style intuition

A Blender-like UI is not just “a bunch of widgets.”

It is more like:

* there is a selected thing
* there is metadata describing that thing
* there is a general-purpose inspector/panel system
* there are semantic actions
* the UI is assembled from these ingredients

That is why it feels powerful and programmable.

Not because every panel is magical, but because the UI is built from reusable semantic building blocks.

---

# In Flutter terms

Your UI abstraction layer could be made of components like:

* `InspectorPanel`
* `PropertyField`
* `Section`
* `CommandBar`
* `ObjectList`
* `StatusBanner`

Each one would receive:

* model data
* metadata
* context
* command dispatcher

Example:

```python id="x6mi6s"
InspectorPanel(
    entity=task,
    meta=task_meta,
    context=ctx,
    dispatch=dispatch_operator,
)
```

That is much cleaner than letting every page invent its own behavior.

---

# What makes it “programmable”

The UI becomes programmable when the behavior can be described in metadata or rules.

Examples:

* hide this field unless `task.type == "approval"`
* disable this field unless `ctx.mode == "edit"`
* show this section only for admins
* when this field changes, dispatch a certain operator
* render this enum as chips on mobile and dropdown on desktop

That is programmability at the UI layer.

It means the UI is not just static code.
It can adapt based on rules.

---

# Dumbed-down one-line version

UI abstraction is the reusable visual engine that turns:

* data
* metadata
* actions
* and situation

into panels, controls, and behavior.

---

# The shortest full model

* **DNA** = the current stuff
* **RNA** = the description of the stuff
* **Operators** = the allowed verbs
* **Context** = the current situation
* **UI abstraction** = the reusable way the app turns all of that into visible screens

---

# Super simple real-world analogy

Imagine a hospital app.

## DNA

Patient record:

* name
* age
* blood pressure
* admitted

## RNA

Definitions:

* name is text
* age is number
* blood pressure is special medical field
* admitted is checkbox

## Operators

* admit patient
* discharge patient
* update blood pressure

## Context

* current doctor
* selected patient
* current department
* edit mode or read-only mode

## UI abstraction

* patient inspector panel
* vitals section
* action toolbar
* notes panel

These are reusable panel types that know how to present the selected patient.

That is the idea.
