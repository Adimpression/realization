# Semantic Rules (v2.0.0)

JSON Schema checks structure. These rules check product meaning.

1. Every Duty must map to at least one real-world object and one real-world interaction.
2. Every Journey must fulfill exactly one primary Duty.
3. Every Journey must decompose into atomic GWT Steps.
4. Every Journey for a **high** or **critical** Duty must have at least one UX SLI and one UX SLO.
5. Every Golden Trace must validate named GWT Steps and must not violate invariants or SLOs.
6. Every Anti-Golden Trace must violate at least one named Step, Invariant, or SLO.
7. Every Invariant should be guarded by at least one Anti-Golden Trace before being relied upon as “critical”.
8. Every Network Boundary must include real-world latency class and causal justification.
9. Under-1s real-world interactions must not be network-separated **unless** an explicit exception approval exists.
10. If a Journey includes variants/failure paths, prefer an explicit `journey.flow` graph to make branching decidable.
11. Step ordering must be consistent: sequences are unique per journey, and `journey.stepIds` matches step `sequence`.
12. Every update must be compatibility-classified; weakening and breaking updates require migration plans.
13. All referenced IDs must resolve to exactly one defined artifact.
