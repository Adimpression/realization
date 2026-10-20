# Service Interface Notation Specification

## 1. Theory

### 1.1 Purpose

This notation defines a service interface as one semantic becoming:

`Produce(Not<Something>) -> Is<Something>`

It does not define services by actor, procedure, endpoint verb, or implementation.
It defines services by **what becomes true**.

---

### 1.2 Semantic unit

`<Something>` denotes a **semantic unit**.

A semantic unit may be:

* a **Noun**
* a **Noun Phrase**

A Noun is a simple semantic unit.
A Noun Phrase is a qualified semantic unit whose modifiers are part of its meaning.

The notation admits both.

---

### 1.3 Name-bearing rule

Nouns and Noun Phrases are themselves the names.

There is no separate variable-like naming layer in the high-level notation.

Semantic distinction must therefore live in the noun system itself, not in auxiliary field labels.

---

### 1.4 `Is<Something>`

`Is<Something>` denotes achievedness.

It means that the semantic unit `<Something>` is now established, realized, or true in the sense relevant to the interface.

`Is<Something>` is the achieved pole of the service axis.

---

### 1.5 `Not<Something>`

`Not<Something>` denotes structured not-yet-achievedness.

It does not mean total negation.
It means that the same semantic unit `<Something>` is not yet achieved, but is described minimally enough to reach `Is<Something>`.

`Not` is therefore **target-relative incompleteness**.

---

### 1.6 `Produce`

`Produce` is universal.

It means only:

* bring about
* establish
* witness

`Is<Something>` from `Not<Something>`.

Its purpose is to keep service identity semantic rather than procedural.

---

### 1.7 Semantic singularity

A well-formed interface denotes one coherent realization axis:

* one `Not<Something>`
* one `Is<Something>`
* one `Produce`

This is the doctrine of **semantic singularity**.

From it follow the main structural consequences of the notation.

---

### 1.8 Relative truth

A thing may be globally `Not<Something>` while containing locally true `Is<SomeOtherThing>` constituents.

So incompleteness is relative to the outer semantic unit, not to every constituent fact.

---

### 1.9 Nested-form rule

Nested semantic forms are only:

* `Is<SomeOtherThing>`
* repeated `Is<SomeOtherThing>`

Nested `Not<...>` forms are not allowed.

`Not` exists only as the outer pre-achieved pole of a service axis.

---

### 1.10 Repetition rule

Repetition is explicit.

Allowed repetition:

* repeated primitives
* repeated `Is<SomeOtherThing>`

Repeated Nouns are therefore only repeated `Is...` forms.

---

### 1.11 Alternation rule

`one-of` is only allowed for **Nouns** or **Noun Phrases**.

So alternation is semantic, not arbitrary structural.

Allowed:

* one-of among complete semantic units

Not allowed:

* one-of among primitives
* one-of among unnamed fragments
* one-of among arbitrary field bundles

---

### 1.12 Non-duplication rule

A singular achieved kind must not appear twice without one of the following being made explicit:

* plurality
* semantic requalification

So if two singular constituents appear to be “the same”, either:

* they are many, and must be repeated
* or they are different, and must become different Nouns or Noun Phrases

Undifferentiated singular duplication is excluded.

---

### 1.13 Naming quality

A semantic unit is judged by whether it survives:

* collision
* context collision
* evolution

A weak name eventually fails under one of these pressures.

---

### 1.14 High-level doctrine

The notation is governed by the following doctrine:

* Name services by what they make true.
* Let Nouns and Noun Phrases carry distinction.
* Let `Not` express target-relative incompleteness.
* Let `Is` express achievedness.
* Let `Produce` express realization.
* Let plurality, distinction, and alternation be explicit.

---

## 2. Application

### 2.1 Role of the application layer

The application layer is the authoring layer.
It declares semantic units and the structures from which `Not<Something>` and `Is<Something>` are generated.

This layer is expressed in YAML.

The lower generation layer is expressed in gRPC proto.

---

### 2.2 Layer relation

The layers are:

* **Theory**: defines meaning
* **Application**: defines authored declarations
* **YAML**: defines the high-level authoring form
* **Proto**: defines the generated interface form

The application layer may include references in `Description` when external sources are useful to explain the meaning or origin of a declaration. These references belong to the authored declaration, not to the theory.

---

### 2.3 What a declaration defines

Each declaration defines one semantic unit and therefore one service axis.

From one declaration, generation produces:

* one package
* one service
* one `Not...` message
* one `Is...` message

---

### 2.4 What `In` means

`In` defines the structure of `Not<Something>`.

It is the minimally sufficient structured not-yet-achieved form.

`In` is not a list of false values.
It is a list of the structured material needed for realization.

---

### 2.5 What `Out` means

`Out` defines the structure of `Is<Something>` beyond its mandatory outer `not` reference.

`Out` may be empty.
If `Out` is empty, successful production still yields `Is<Something>` as the achieved witness.

---

### 2.6 Application-level constraints

The application layer obeys all theoretical constraints:

* Nouns and Noun Phrases are the names
* repeated nouns are only repeated `Is...`
* nested `Not...` is not allowed
* one-of is only over Nouns or Noun Phrases
* undifferentiated singular duplication is not allowed

---

## 3. YAML

### 3.1 Top-level structure

A YAML declaration has the form:

```yaml
<Semantic Unit>:
  Description:
    - <reference or note>
    - <reference or note>
  In:
    - <entry>
    - <entry>
  Out:
    - <entry>
    - <entry>
```

`Description` is optional.
`In` and `Out` are optional individually, though a meaningful declaration normally defines at least one side materially.

For artifact interchange, the same declaration form may carry an additional `Metadata` mapping:

```yaml
<Semantic Unit>:
  Description:
    - <reference or note>
  In:
    - <entry>
  Out:
    - <entry>
  Metadata:
    artifact_type: <knowledge|ability|...>
    ...
```

`Metadata` is not required for ordinary state/interface notation, but it is the standard extension for exported/imported artifact declarations.

For artifact interchange, `Metadata.artifact_id` is the serialized/storage name of
the artifact identifier. When the declaration is loaded into the controller, the
hydrated in-memory object uses `id` as the canonical field name. In other words:
external YAML/DB/CLI may say `artifact_id`, while in-memory code should use
`artifact.id`.

---

### 3.2 Semantic-unit key

The declaration key is a Noun or Noun Phrase.
It may be segmented using `/`.

General forms:

```yaml
<Thing>
<Thing> / <Predicate>
<Thing> / <Qualifier> / <Predicate>
<Thing> / <Qualifier A> / <Qualifier B> / <Predicate>
```

`/` is the authoring-level phrase separator.

---

### 3.3 Description

`Description` contains explanatory notes and, where needed, external references.

These references are lower-layer usage references only.
They do not alter the theory.
They document origin, intended meaning, protocol source, or implementation background.

---

### 3.4 Allowed entry forms

An `In` or `Out` entry may be one of the following.

#### Primitive

```yaml
- Value String
- Data Bytes
- Count Int
- Enabled Boolean
- Amount Float
```

#### Repeated primitive

```yaml
- Values Strings
- Data Bytess
- Counts Ints
- Amounts Floats
- Flags Bools
```

#### Singular Noun or Noun Phrase

```yaml
- User
- Identified User
- User / Identified
```

This generates a singular nested `Is...` field.

#### Repeated Noun or Noun Phrase

```yaml
- [ User ]
- [ Identified User ]
- [ User / Identified ]
```

This generates a repeated nested `Is...` field.

#### One-of Nouns or Noun Phrases

```yaml
- A | B
- Source File | Source Folder
- Identified User | Identified Group
```

This generates a `oneof`.

Each branch must itself be a complete Noun or Noun Phrase.

---

### 3.5 Not allowed in YAML

The following are excluded from the YAML authoring layer:

* variable-style field names
* nested `Not<...>` entries
* repeated `Not<...>` entries
* one-of over primitives
* one-of over arbitrary field fragments
* undifferentiated duplicate singular same-kind noun entries

---

### 3.6 Self-reference

Self-reference is allowed.

A declaration may reference its own semantic unit in `In`, `Out`, or both.

Repeated self-reference is also allowed, as repeated `Is...`.

---

### 3.7 Build procedure for a YAML declaration

A declaration is built in the following order.

#### Step 1: choose the semantic unit

Choose the Noun or Noun Phrase that names the achieved semantic unit.

This unit should survive:

* collision
* context collision
* evolution

#### Step 2: choose the declaration key

Write the semantic unit as the YAML key, optionally segmented by `/`.

#### Step 3: add references if needed

Add `Description` only where explanatory notes or external source references are useful.

#### Step 4: define `In`

List the minimally sufficient structured not-yet-achieved constituents.

Allowed forms:

* primitive
* repeated primitive
* singular noun / noun phrase
* repeated noun / noun phrase
* one-of noun / noun phrase

#### Step 5: define `Out`

List the achieved constituents returned or made explicit in the achieved form.

If nothing beyond achievedness needs to be carried, `Out` may be omitted or empty.

#### Step 6: validate constraints

Confirm that:

* no nested `Not...` appears
* no primitive one-of appears
* no variable-like naming appears
* all repeated nouns are repeated `Is...`
* all singular same-kind ambiguity has been removed by plurality or requalification

---

### 3.8 YAML authoring summary

The YAML layer is a semantic authoring language, not a generic schema language.

Its job is to author:

* one semantic unit
* one `In`
* one `Out`

from which the proto layer is generated.

---

## 4. Proto

### 4.1 Proto generation overview

Each YAML declaration generates:

* a proto package
* a service named `ToIs<Something>`
* four RPC methods
* a message pair:

    * `Not<Something>`
    * `Is<Something>`

---

### 4.2 Package generation

The package name is generated by normalizing the semantic-unit name:

* remove separators
* lowercase
* concatenate tokens

In non-versioned multi-part declarations, generation may canonicalize ordering by moving the final semantic emphasis to the front. This behavior belongs to the generator and affects package names, type names, and imports consistently.

---

### 4.3 Service generation

The generated service form is:

```proto
service ToIs<Something> {
  rpc Produce (Not<Something>) returns (Is<Something>) {}
  rpc ProduceStream (Not<Something>) returns (stream Is<Something>) {}
  rpc StreamProduce (stream Not<Something>) returns (Is<Something>) {}
  rpc StreamProduceStream (stream Not<Something>) returns (stream Is<Something>) {}
}
```

All four methods are part of the generated service shape.

---

### 4.4 Message generation

The generated message pair is:

```proto
message Is<Something> {
    Not<Something> not = 1;
    // generated from Out
}

message Not<Something> {
    Is<Something> is = 1;
    // generated from In
}
```

The outer references are fixed:

* `not = 1` in `Is<Something>`
* `is = 1` in `Not<Something>`

---

### 4.5 Import generation

If a generated field references another semantic unit, the corresponding proto package is imported.

Import generation follows the referenced noun / noun phrase dependencies.

---

### 4.6 Primitive mapping

Primitive YAML entries map to proto scalar fields.

Typical mappings are:

* `String` -> `string`
* `Bytes` -> `bytes`
* `Int` -> integer proto type according to generator policy
* `Float` -> `float`
* `Boolean` -> `bool`

Repeated primitive mappings are the repeated forms of the same.

---

### 4.7 Singular noun mapping

A singular Noun or Noun Phrase entry maps to a singular nested `Is...` field.

A high-level noun reference always compiles to an `Is<ReferencedThing>` field.

---

### 4.8 Repeated noun mapping

A repeated Noun or Noun Phrase entry maps to:

```proto
repeated Is<ReferencedThing> ...
```

Repeated nouns are therefore always repeated achieved forms.

---

### 4.9 One-of mapping

A noun / noun phrase alternation maps to a proto `oneof`.

Each branch of the `oneof` is generated as a nested `Is...` field.

The `oneof` name is generated from the generated branch field names.

---

### 4.10 Self-reference mapping

Self-reference maps directly to self-typed `Is...` fields.

Repeated self-reference maps directly to repeated self-typed `Is...` fields.

---

### 4.11 Low-level field-name generation

Although not part of the high-level API, generated field names follow a stable rule.

#### Prefix

Generated semantic fields are prefixed with `is_`.

This applies even inside `Not<Something>`, because constituent truth is local and already achieved.

#### Primitive field-name procedure

For a primitive entry:

1. take the authored phrase
2. lowercase it
3. tokenize it
4. join with `_`
5. prefix with `is_`
6. preserve the primitive kind word at the end

Examples of the pattern:

* `<Phrase> String` -> `is_<phrase>_string`
* `<Phrase> Bytes` -> `is_<phrase>_bytes`

#### Noun field-name procedure

For a noun or noun phrase entry:

1. normalize the semantic-unit name to lowercase underscore tokens
2. prefix with `is_`

So the field name is derived from the noun system, not from a variable name.

#### Repeated noun field-name procedure

Repeated noun fields keep the same stem as singular noun fields.

Multiplicity is expressed by the proto `repeated` modifier, not by pluralizing the field name.

#### One-of name generation

A `oneof` name is generated from the generated branch field names, according to the generator’s stable branch-ordering rule.

---

### 4.12 Field-number generation

The generator uses stable field-number bands by field kind.

Observed band structure:

* `1` : outer `is` / `not`
* `1000000+` : repeated noun fields
* `2000000+` : singular primitive fields
* `3000000+` : `oneof` branch fields
* `4000000+` : singular noun fields
* `5000000+` : repeated primitive fields

This banding is a generator-level concern, not a high-level semantic concern, but it is part of the produced proto form.

---

### 4.13 Proto generation summary

The proto layer materializes the application-layer declaration into:

* one package
* one service
* four RPCs
* one `Not...` message
* one `Is...` message
* generated imports
* generated field names
* generated field-number bands

The generated proto remains faithful to the theory by preserving:

* semantic singularity
* achieved constituent naming through `is_`
* nested `Is...` only
* explicit repetition
* semantic alternation only

---

## 5. Consolidated authoring checklist

A declaration is complete when all of the following are true:

* the semantic unit is a Noun or Noun Phrase
* the declaration key is stable under collision, context, and evolution
* `In` defines the minimally sufficient `Not<Something>`
* `Out` defines the achieved `Is<Something>`
* nested semantic fields are only `Is...`
* repeated nouns are only repeated `Is...`
* one-of is only over Nouns or Noun Phrases
* no variable-like naming has been introduced
* no singular same-kind ambiguity remains unresolved
* any lower-layer references are kept in `Description`

---

## 6. Final statement

This notation is a service-interface language in which:

* the semantic unit is a Noun or Noun Phrase
* `Not` is target-relative incompleteness
* `Is` is achievedness
* `Produce` is realization
* YAML authors the semantic axis
* proto materializes it
* generated names remain aligned with the noun system all the way down

Its governing rule is:

**Services are named not by what they do, but by what they make true.**
