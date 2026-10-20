# State Interface Notation Grammar

This document defines an EBNF for the **authoring language plus the generated proto-oriented structural intent**. It enforces the syntactic core and separates constraints that are inherently semantic or generator-level rather than context-free. Some rules are grammatical, while others concern meaning, identity, duplication, normalization, field generation, and cross-reference behavior.

## 1. Scope

This EBNF targets the **next-version authoring form** described by the full specification, namely:

* one YAML declaration
* one semantic-unit key
* optional `Description`
* optional `In`
* optional `Out`
* entry forms for:

    * primitive
    * repeated primitive
    * singular noun / noun phrase
    * repeated noun / noun phrase
    * one-of noun / noun phrase

It also reflects the downstream proto intent:

* one declaration corresponds to one semantic unit
* one `Not<Something>`
* one `Is<Something>`
* nested semantic references are only achieved references
* repeated nouns are repeated achieved references
* one-of is semantic alternation only

The crucial philosophical point is this: **EBNF can govern form, but not fully govern semantic singularity**. So the best complete answer is “EBNF + semantic side-conditions.” That is exactly the maximum extent possible.

---

## 2. EBNF

### 2.1 High-level document grammar

```ebnf
document                = declaration ;

declaration             = semantic-unit-key, ":", newline,
                          declaration-body ;

declaration-body        = indented-declaration-body
                        | empty ;

indented-declaration-body
                        = indent, declaration-members, dedent ;

declaration-members     = declaration-member,
                          { newline, declaration-member } ;

declaration-member      = description-section
                        | in-section
                        | out-section ;
```

---

### 2.2 Sections

```ebnf
description-section     = "Description", ":", newline,
                          indent, description-list, dedent ;

in-section              = "In", ":", newline,
                          indent, entry-list, dedent ;

out-section             = "Out", ":", [ space, inline-empty-sequence ]
                        | "Out", ":", newline,
                          indent, [ entry-list ], dedent ;

description-list        = description-item,
                          { newline, description-item } ;

description-item        = "-", space, description-text ;

entry-list              = entry,
                          { newline, entry } ;

entry                   = "-", space, entry-value ;
```

---

### 2.3 Allowed entry forms

```ebnf
entry-value             = primitive-entry
                        | repeated-primitive-entry
                        | repeated-semantic-entry
                        | oneof-semantic-entry
                        | singular-semantic-entry ;
```

Order matters here. The repeated and one-of forms are distinct surface syntaxes and should be recognized before treating something as a plain singular semantic unit.

---

### 2.4 Primitive entries

```ebnf
primitive-entry         = phrase, space, primitive-kind ;

repeated-primitive-entry
                        = phrase, space, repeated-primitive-kind ;

primitive-kind          = "String"
                        | "Bytes"
                        | "Int"
                        | "Boolean"
                        | "Float" ;

repeated-primitive-kind = "Strings"
                        | "Bytess"
                        | "Ints"
                        | "Bools"
                        | "Floats" ;
```

This matches the authored forms in the specification, including the intentionally generator-aligned repeated primitive spellings such as `Bytess` and `Bools`.

---

### 2.5 Semantic-unit references

```ebnf
singular-semantic-entry = semantic-unit ;

repeated-semantic-entry = "[", opt-space, semantic-unit, opt-space, "]" ;

oneof-semantic-entry    = semantic-unit, opt-space, "|", opt-space,
                          semantic-unit,
                          { opt-space, "|", opt-space, semantic-unit } ;
```

This encodes exactly the permitted semantic nested forms in the YAML authoring layer:

* singular noun / noun phrase
* repeated noun / noun phrase
* one-of among complete semantic units

and excludes explicit nested `Not<...>` syntax entirely at the grammar level.

---

### 2.6 Semantic-unit key and semantic-unit syntax

```ebnf
semantic-unit-key       = semantic-unit ;

semantic-unit           = semantic-segment,
                          { opt-space, "/", opt-space, semantic-segment } ;

semantic-segment        = phrase ;
```

This gives the authoring-level slash segmentation described in the YAML layer, such as:

* `Thing`
* `Thing / Predicate`
* `Thing / Qualifier / Predicate`

---

### 2.7 Phrase grammar

```ebnf
phrase                  = phrase-word,
                          { space, phrase-word } ;

phrase-word             = capitalized-word
                        | capitalized-hyphenated-word ;

capitalized-hyphenated-word
                        = capitalized-word, { "-", alnum-word } ;

capitalized-word        = upper, { alnum } ;

alnum-word              = alnum, { alnum } ;
```

This is an intentionally disciplined phrase grammar. It captures the specification’s claim that the noun system itself bears identity, and avoids a variable-like field syntax in the authoring layer by not admitting things like snake_case, camelCase field identifiers, or assignment-like fragments as first-class productions.

---

### 2.8 Description text

```ebnf
description-text        = description-char, { description-char } ;

description-char        = ? any character except newline ? ;
```

`Description` is explanatory and reference-carrying, so it is left intentionally broad.

---

### 2.9 Whitespace and layout

```ebnf
newline                 = "\n" | "\r\n" ;
space                   = " ", { " " } ;
opt-space               = [ space ] ;

indent                  = ? increased indentation level ? ;
dedent                  = ? decreased indentation level ? ;

inline-empty-sequence   = "[" , opt-space , "]"
                        | empty ;

empty                   = ;
```

Because the language is YAML-shaped, indentation sensitivity is external to pure CFG mechanics. EBNF can name `indent`/`dedent`, but an actual parser must treat them lexically or via an indentation-sensitive frontend.

---

### 2.10 Lexical atoms

```ebnf
upper                   = "A" | "B" | "C" | "D" | "E" | "F" | "G"
                        | "H" | "I" | "J" | "K" | "L" | "M" | "N"
                        | "O" | "P" | "Q" | "R" | "S" | "T" | "U"
                        | "V" | "W" | "X" | "Y" | "Z" ;

lower                   = "a" | "b" | "c" | "d" | "e" | "f" | "g"
                        | "h" | "i" | "j" | "k" | "l" | "m" | "n"
                        | "o" | "p" | "q" | "r" | "s" | "t" | "u"
                        | "v" | "w" | "x" | "y" | "z" ;

digit                   = "0" | "1" | "2" | "3" | "4"
                        | "5" | "6" | "7" | "8" | "9" ;

alnum                   = upper | lower | digit ;
```

---

## 3. Stronger, implementation-oriented version

The grammar above is the clean core. The following constrained version is closest to how an implementation should parse and validate it.

### 3.1 Canonical authoring grammar

```ebnf
document                = declaration ;

declaration             = semantic-unit, ":", newline,
                          indent, declaration-content, dedent ;

declaration-content     = declaration-sequence ;

declaration-sequence    = declaration-item,
                          { newline, declaration-item } ;

declaration-item        = description-section
                        | in-section
                        | out-section ;

description-section     = "Description", ":", newline,
                          indent, description-item,
                          { newline, description-item }, dedent ;

description-item        = "-", space, description-text ;

in-section              = "In", ":", newline,
                          indent, entry,
                          { newline, entry }, dedent ;

out-section             = "Out", ":", [ space, "[" , opt-space , "]" ]
                        | "Out", ":", newline,
                          indent, [ entry, { newline, entry } ], dedent ;

entry                   = "-", space, authored-entry ;

authored-entry          = primitive-entry
                        | repeated-primitive-entry
                        | repeated-semantic-entry
                        | oneof-semantic-entry
                        | semantic-unit ;

primitive-entry         = phrase, space, primitive-kind ;

repeated-primitive-entry
                        = phrase, space, repeated-primitive-kind ;

repeated-semantic-entry = "[", opt-space, semantic-unit, opt-space, "]" ;

oneof-semantic-entry    = semantic-unit, opt-space, "|", opt-space,
                          semantic-unit,
                          { opt-space, "|", opt-space, semantic-unit } ;

semantic-unit           = semantic-segment,
                          { opt-space, "/", opt-space, semantic-segment } ;

semantic-segment        = phrase ;

phrase                  = phrase-head, { space, phrase-tail } ;

phrase-head             = capitalized-token ;
phrase-tail             = capitalized-token ;

capitalized-token       = upper, { alnum | "-" } ;

primitive-kind          = "String"
                        | "Bytes"
                        | "Int"
                        | "Boolean"
                        | "Float" ;

repeated-primitive-kind = "Strings"
                        | "Bytess"
                        | "Ints"
                        | "Bools"
                        | "Floats" ;

description-text        = description-char, { description-char } ;
description-char        = ? any character except newline ? ;

newline                 = "\n" | "\r\n" ;
space                   = " ", { " " } ;
opt-space               = [ space ] ;

indent                  = ? indentation push ? ;
dedent                  = ? indentation pop ? ;

upper                   = "A" | "B" | "C" | "D" | "E" | "F" | "G"
                        | "H" | "I" | "J" | "K" | "L" | "M" | "N"
                        | "O" | "P" | "Q" | "R" | "S" | "T" | "U"
                        | "V" | "W" | "X" | "Y" | "Z" ;
lower                   = "a" | "b" | "c" | "d" | "e" | "f" | "g"
                        | "h" | "i" | "j" | "k" | "l" | "m" | "n"
                        | "o" | "p" | "q" | "r" | "s" | "t" | "u"
                        | "v" | "w" | "x" | "y" | "z" ;
digit                   = "0" | "1" | "2" | "3" | "4"
                        | "5" | "6" | "7" | "8" | "9" ;
alnum                   = upper | lower | digit ;
```

This is the canonical syntactic contract for an implementation.

---

## 4. What this EBNF enforces well

This grammar enforces, at the syntactic level:

1. **Exactly one top-level declaration**
   One document corresponds to one semantic unit and one service axis.

2. **The key is itself the semantic unit**
   No extra authoring-level variable name is introduced.

3. **Only the permitted sections exist**
   `Description`, `In`, `Out`.

4. **Only the permitted entry forms exist**

* primitive
* repeated primitive
* singular semantic unit
* repeated semantic unit
* one-of semantic units

5. **Repeated nouns are explicit**
   Repetition uses bracket syntax only.

6. **Alternation is explicit and semantic-shaped**
   One-of uses complete semantic units as branches.

7. **Nested `Not<...>` syntax does not exist in the language**
   It is excluded directly by grammar design.

This tracks the theory and YAML sections closely.

---

## 5. What EBNF cannot fully enforce

Here lies the deeper boundary between syntax and ontology.

### 5.1 At least one of `In` or `Out` must be materially present

Pure EBNF can allow both sections optionally, but it does not naturally express the semantic condition:

* `Description` alone is not meaningful
* at least one side should be materially defined

This should be a validator rule.

### 5.2 No duplicate singular same-kind noun entries

The grammar cannot determine whether two entries are semantically the “same kind” under rewording, qualification, or normalization. For example, it cannot decide whether:

* `User`
* `Identified User`

are sufficiently distinct in a given ontology.

### 5.3 No variable-style naming

The grammar approximates this by only allowing phrase-shaped capitalized tokens, but the notion of “variable-like” is partly semantic and stylistic. A validator should reject patterns such as:

* `userId`
* `user_id`
* `primary_user_v2`

if the project wants that prohibition to be absolute.

### 5.4 One-of only over complete semantic units

The grammar enforces this structurally, but it cannot judge whether a phrase is truly a complete semantic unit or merely a disguised fragment.

### 5.5 Naming quality

Surviving:

* collision
* context collision
* evolution

is an ontological and organizational property, not a context-free one.

### 5.6 Self-reference legitimacy

The grammar permits self-reference, but cannot compare an entry against the enclosing declaration key to reason about whether it is self-reference, repeated self-reference, or some normalized equivalent.

### 5.7 Proto-generation invariants

The following belong to generator semantics, not EBNF:

* `Not<Something>` / `Is<Something>` message synthesis
* fixed outer fields `is = 1` and `not = 1`
* import generation
* package normalization
* `is_` field-name generation
* field-number band allocation
* oneof-name derivation from branches

Those are not properties of the YAML language alone; they are properties of the translation from authoring form into proto.

---

## 6. Semantic side-conditions needed in addition to the EBNF

To make the language truly match the specification and the implementation target, pair the EBNF with these validator rules.

### 6.1 Declaration-level constraints

```text
S1. A declaration must contain at least one of In or Out.
S2. A declaration defines exactly one semantic unit.
S3. The top-level key is the achieved semantic unit of the declaration.
```

### 6.2 Entry constraints

```text
S4. No entry may contain explicit Not<...>.
S5. Repeated semantic entries are only bracketed semantic-unit references.
S6. One-of branches must each normalize to complete semantic units.
S7. One-of over primitives is forbidden.
S8. Undifferentiated singular duplicate semantic entries are forbidden.
```

### 6.3 Naming constraints

```text
S9. Semantic-unit names must not normalize to variable-style identifiers at the authoring level.
S10. A semantic unit should survive collision, context collision, and evolution.
S11. If two singular entries normalize to the same semantic identity, they must be merged, made repeated, or requalified.
```

### 6.4 Generator constraints

```text
S12. Every singular semantic reference generates a singular nested Is<ReferencedThing> field.
S13. Every repeated semantic reference generates a repeated Is<ReferencedThing> field.
S14. Every one-of semantic entry generates a proto oneof whose branches are nested Is<ReferencedThing> fields.
S15. Every declaration generates one package, one service, four RPCs, one Not<Something>, and one Is<Something>.
S16. Generated messages carry the fixed outer backreferences:
     Not<Something>.is = 1
     Is<Something>.not = 1
```

Those side-conditions are not optional decoration; they are the semantic completion of the grammar.

---

## 7. Examples accepted by the EBNF

### 7.1 Minimal declaration

```yaml
User:
  In:
    - Name String
```

### 7.2 With `Out`

```yaml
Identified User:
  In:
    - Name String
    - Email String
  Out:
    - User Id String
```

### 7.3 With slash segmentation

```yaml
User / Identified:
  In:
    - User
    - Source File | Source Folder
  Out:
    - Confidence Float
```

### 7.4 Repeated semantic entry

```yaml
Group:
  In:
    - [ User ]
```

### 7.5 Repeated primitive entry

```yaml
Dataset:
  In:
    - Values Strings
    - Counts Ints
```

### 7.6 Self-reference

```yaml
Node:
  In:
    - [ Node ]
  Out:
    - Depth Int
```

All of these are consistent with the specified authoring layer.

---

## 8. Examples rejected by the EBNF or side-conditions

### 8.1 Explicit nested `Not`

```yaml
User:
  In:
    - Not<Account>
```

Rejected: `Not<...>` is not a production of the authoring entry grammar.

### 8.2 Primitive one-of

```yaml
Thing:
  In:
    - String | Int
```

Rejected: no grammar production allows primitive alternation.

### 8.3 Repeated arbitrary fragment

```yaml
Thing:
  In:
    - [ Value String ]
```

Rejected: bracket repetition applies only to semantic units, not primitive fragments.

### 8.4 Variable-style naming

```yaml
Thing:
  In:
    - user_id String
```

Rejected by lexical discipline and definitely by side-condition.

### 8.5 Undifferentiated singular duplication

```yaml
Thing:
  In:
    - User
    - User
```

Exact duplicates can be caught trivially by a validator. More subtle same-kind duplication requires normalization and semantic checking.

---

## 9. Proto-oriented abstract grammar

The following abstract generation grammar corresponds to what the authoring declaration denotes.

This is **not** the YAML grammar. It is the **generated semantic interface grammar**.

```ebnf
generated-interface     = package-decl,
                          service-decl,
                          not-message,
                          is-message,
                          { import-decl } ;

package-decl            = "package", space, normalized-semantic-unit ;
import-decl             = "import", space, normalized-semantic-unit ;

service-decl            = "service", space, "ToIs", semantic-unit-flat, space, "{",
                          newline,
                          rpc-produce, newline,
                          rpc-produce-stream, newline,
                          rpc-stream-produce, newline,
                          rpc-stream-produce-stream, newline,
                          "}" ;

rpc-produce             = "rpc", space, "Produce", space,
                          "(", "Not", semantic-unit-flat, ")", space,
                          "returns", space,
                          "(", "Is", semantic-unit-flat, ")" ;

rpc-produce-stream      = "rpc", space, "ProduceStream", space,
                          "(", "Not", semantic-unit-flat, ")", space,
                          "returns", space,
                          "(", "stream", space, "Is", semantic-unit-flat, ")" ;

rpc-stream-produce      = "rpc", space, "StreamProduce", space,
                          "(", "stream", space, "Not", semantic-unit-flat, ")", space,
                          "returns", space,
                          "(", "Is", semantic-unit-flat, ")" ;

rpc-stream-produce-stream
                        = "rpc", space, "StreamProduceStream", space,
                          "(", "stream", space, "Not", semantic-unit-flat, ")", space,
                          "returns", space,
                          "(", "stream", space, "Is", semantic-unit-flat, ")" ;

not-message             = "message", space, "Not", semantic-unit-flat, space, "{",
                          newline,
                          outer-is-field,
                          { newline, generated-in-field },
                          newline, "}" ;

is-message              = "message", space, "Is", semantic-unit-flat, space, "{",
                          newline,
                          outer-not-field,
                          { newline, generated-out-field },
                          newline, "}" ;

outer-is-field          = "Is", semantic-unit-flat, space, "is", space, "=", space, "1", ";" ;
outer-not-field         = "Not", semantic-unit-flat, space, "not", space, "=", space, "1", ";" ;

generated-in-field      = generated-primitive-field
                        | generated-repeated-primitive-field
                        | generated-singular-semantic-field
                        | generated-repeated-semantic-field
                        | generated-oneof ;

generated-out-field     = generated-primitive-field
                        | generated-repeated-primitive-field
                        | generated-singular-semantic-field
                        | generated-repeated-semantic-field
                        | generated-oneof ;
```

This abstract grammar reflects the production reference in your document:

* one service
* four RPCs
* one `Not...` message
* one `Is...` message
* fixed outer mutual references

while leaving naming normalization, field numbering, and import closure to generator semantics.

---

## 10. Recommended implementation contract

For implementation, the most faithful and robust answer is:

1. **Use the YAML EBNF above as the syntactic contract.**
2. **Use a semantic validator for the non-context-free doctrine.**
3. **Use a generator contract for proto materialization.**

That three-layer separation mirrors the specification’s own structure:

* theory
* application / YAML authoring
* proto generation

So the mathematically clean answer is not to force everything into EBNF, but to let EBNF do what grammars do best and let semantic validation do what ontologies require. That is the maximum faithful enforcement possible.
