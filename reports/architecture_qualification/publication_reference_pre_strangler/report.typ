// Generated publication build. Do not treat as subject truth.
#let report_accent = rgb("#14324A")
#let report_ink = rgb("#172230")
#let report_muted = rgb("#657483")
#let report_rule = rgb("#D6DEE6")
#let report_panel = rgb("#F7F3EE")
#let report_panel_alt = rgb("#F2F6F9")
#let report_highlight = rgb("#EEE2D1")
#let report_warning = rgb("#F7E6E0")
#set page(
  paper: "a4",
  margin: (top: 22mm, bottom: 20mm, left: 22mm, right: 22mm),
  numbering: "1",
  number-align: right + bottom,
  header: align(right)[#text(size: 8pt, fill: report_muted)[Find the Time Report]],
)
#set text(size: 10.2pt, fill: report_ink)
#set par(justify: true, leading: 0.7em)
#set heading(numbering: "1.")

#align(left)[
  #text(size: 8.5pt, weight: "bold", fill: report_accent)[GOVERNED INSIGHT REPORT]
  #v(9pt)
  #text(size: 24pt, weight: "bold", fill: report_ink)[Find the Time Report]
  #v(7pt)
  #text(size: 11pt, fill: report_muted)[This report summarizes the currently approved findings for Find the Time.]
  #v(10pt)
  #text(size: 8.4pt, fill: report_muted)[Snapshot $SNAPSHOT_HASH | 5 findings | 1 sources]
]

#pagebreak()

= Executive Summary <executive-summary>

#block(width: 100%, breakable: true, fill: report_highlight, inset: 12pt, radius: 7pt, stroke: (paint: report_rule, thickness: 0.7pt))[
  #set par(justify: false)
  #text(size: 7.8pt, weight: "bold", fill: report_muted)[EXECUTIVE SUMMARY]
  #v(3pt)
  #text(size: 8.4pt, weight: "bold", fill: report_accent)[What this report covers]
  #v(6pt)
  This report summarizes the currently approved findings for Find the Time.
]

#block(width: 100%, breakable: true, fill: report_panel, inset: 12pt, radius: 7pt, stroke: (paint: report_rule, thickness: 0.7pt))[
  #set par(justify: false)
  #text(size: 7.8pt, weight: "bold", fill: report_muted)[HEADLINE FINDINGS]
  #v(3pt)
  #text(size: 8.4pt, weight: "bold", fill: report_accent)[Key Findings]
  #v(6pt)
  - If you want to ask for the time, say "Velawa Kiiyadha".
  - ask for the time, say,
  - If you
]

#block(width: 100%, breakable: true, fill: report_panel_alt, inset: 12pt, radius: 7pt, stroke: (paint: report_rule, thickness: 0.7pt))[
  #set par(justify: false)
  #text(size: 7.8pt, weight: "bold", fill: report_muted)[READING GUIDE]
  #v(3pt)
  #text(size: 8.4pt, weight: "bold", fill: report_accent)[What comes next]
  #v(6pt)
  - 1 Definitions
]

#pagebreak()

#block(width: 100%, fill: report_accent, inset: (top: 8pt, right: 12pt, bottom: 8pt, left: 12pt), radius: 8pt)[
  #set par(justify: false)
  #text(size: 8pt, weight: "bold", fill: white)[SECTION 01 | DEFINITION | 3 CLAIMS]
  #v(6pt)
  #text(size: 20pt, weight: "bold", fill: white)[Definitions]
]

#block(width: 100%, breakable: true, fill: report_panel, inset: 12pt, radius: 7pt, stroke: (paint: report_rule, thickness: 0.7pt))[
  #set par(justify: false)
  #text(size: 7.8pt, weight: "bold", fill: report_muted)[REVIEW CITATION CALLOUT]
  #v(3pt)
  #text(size: 8.4pt, weight: "bold", fill: report_accent)[ask for the time, say,]
  #v(6pt)
  ask for the time, say,
  Evidence mode: source basis panel.
]

#block(width: 100%, breakable: true, fill: report_panel, inset: 12pt, radius: 7pt, stroke: (paint: report_rule, thickness: 0.7pt))[
  #set par(justify: false)
  #text(size: 7.8pt, weight: "bold", fill: report_muted)[REVIEW CITATION CALLOUT]
  #v(3pt)
  #text(size: 8.4pt, weight: "bold", fill: report_accent)[If you]
  #v(6pt)
  If you
  Evidence mode: source basis panel.
]

- If you want to ask for the time, say "Velawa Kiiyadha".
  #text(size: 8pt, fill: report_muted)[Sources: \[S1\]]

- ask for the time, say,
  #text(size: 8pt, fill: report_muted)[Sources: \[S1\]]

- If you
  #text(size: 8pt, fill: report_muted)[Sources: \[S1\]]

#pagebreak()

= Sources <sources>

#block(width: 100%, breakable: true, fill: report_panel, inset: 12pt, radius: 7pt, stroke: (paint: report_rule, thickness: 0.7pt))[
  #set par(justify: false)
  #text(size: 7.8pt, weight: "bold", fill: report_muted)[SOURCE GUIDE]
  #v(3pt)
  #text(size: 8.4pt, weight: "bold", fill: report_accent)[Source Register]
  #v(6pt)
  Each source is assigned a numbered handle for compact reference inside the report body.

  - \[S1\] Find the Time
]

#block(width: 100%, breakable: true, fill: report_panel_alt, inset: 12pt, radius: 7pt, stroke: (paint: report_rule, thickness: 0.7pt))[
  #set par(justify: false)
  #text(size: 7.8pt, weight: "bold", fill: report_muted)[Source 01]
  #v(3pt)
  #text(size: 8.4pt, weight: "bold", fill: report_accent)[Find the Time]
  #v(6pt)
  workstation/tests/fixtures/report\_creation/01\_FIND\_THE\_TIME.md

  #text(size: 8pt, weight: "bold", fill: report_muted)[Relevance]
  Find the Time
]


= Build Notes <report-controls>

#block(width: 100%, breakable: true, fill: report_panel, inset: 12pt, radius: 7pt, stroke: (paint: report_rule, thickness: 0.7pt))[
  #set par(justify: false)
  #text(size: 7.8pt, weight: "bold", fill: report_muted)[APPENDIX]
  #v(3pt)
  #text(size: 8.4pt, weight: "bold", fill: report_accent)[Build Notes]
  #v(6pt)
  - Built from subject find-the-time.
  - Snapshot $CONTENT_HASH.
  - Publication id pub\_find-the-time\_report\_734c5a04b5.
]
