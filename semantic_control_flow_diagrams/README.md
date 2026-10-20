# Semantic Control Flow Diagrams

These diagrams capture the major logical and semantic control flows of the current controller.
They were updated after the governed prior-learning reuse extraction, the external markdown-learning pipeline extraction, the markdown artifact-semantics extraction, the prompt-posture extraction, the governed runtime extraction, the fallback-not semantics extraction, the closure/commitment extraction, and the entrypoint extraction, so the diagrams now distinguish:
- the extracted reuse seam
- the extracted external markdown-learning pipeline
- the extracted markdown artifact semantics cluster
- the extracted run finalization and harvest seam
- the extracted prompt-posture seam
- the extracted governed recursive runtime seam
- the extracted fallback non-achievedness seam
- the extracted closure and commitment seam
- the extracted controller entrypoint seam

Files:
- [01_governed_run_entry_and_frontier_flow.puml](semantic_control_flow_diagrams/01_governed_run_entry_and_frontier_flow.puml)
- [02_not_elaboration_and_title_depth_inference_flow.puml](semantic_control_flow_diagrams/02_not_elaboration_and_title_depth_inference_flow.puml)
- [03_prior_learning_lookup_and_reuse_selection_flow.puml](semantic_control_flow_diagrams/03_prior_learning_lookup_and_reuse_selection_flow.puml)
- [04_normal_text_to_prolog_backed_ability_resolution_flow.puml](semantic_control_flow_diagrams/04_normal_text_to_prolog_backed_ability_resolution_flow.puml)
- [05_decomposition_and_direct_refinement_flow.puml](semantic_control_flow_diagrams/05_decomposition_and_direct_refinement_flow.puml)
- [06_markdown_learning_and_relation_persistence_flow.puml](semantic_control_flow_diagrams/06_markdown_learning_and_relation_persistence_flow.puml)
- [07_run_finalization_and_discovery_harvest_flow.puml](semantic_control_flow_diagrams/07_run_finalization_and_discovery_harvest_flow.puml)
- [08_six_layer_architecture_context.puml](semantic_control_flow_diagrams/08_six_layer_architecture_context.puml)
- [09_workstation_and_shared_host_substrate.puml](semantic_control_flow_diagrams/09_workstation_and_shared_host_substrate.puml)

The diagrams are intentionally high-level. They show control ownership and semantic transitions, not line-by-line implementation detail.

Important distinction:
- [MARKDOWN_LEARNING_VS_RUNTIME_REDUCTION.md](MARKDOWN_LEARNING_VS_RUNTIME_REDUCTION.md) explains explicitly that `markdown-learn` is a bounded document-learning pipeline, not a call into the governed recursive `reduce_not(...)` control loop, and that `import-skill` is an installation path rather than a derivation path.
- [6-LAYER_ARCHITECTURE.md](6-LAYER_ARCHITECTURE.md) now describes the six-layer architecture and the shared host interaction substrate beneath workstation and controller.
