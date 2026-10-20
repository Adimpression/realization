# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from publication import (
    Publication,
    PublicationBlock,
    PublicationClaim,
    PublicationCrossReference,
    PublicationEntity,
    PublicationReviewRecord,
    PublicationSection,
    PublicationSource,
    VALID_PUBLICATION_SECTION_ROLES,
    VALID_PUBLICATION_XREF_TARGET_KINDS,
    VALID_PUBLICATION_XREF_TYPES,
)
from semantic_text import collapse_ws


def validate_publication(
    publication: Publication,
    *,
    sections: tuple[PublicationSection, ...],
    blocks: tuple[PublicationBlock, ...] = (),
    claims: tuple[PublicationClaim, ...],
    sources: tuple[PublicationSource, ...],
    entities: tuple[PublicationEntity, ...] = (),
    xrefs: tuple[PublicationCrossReference, ...] = (),
    reviews: tuple[PublicationReviewRecord, ...] = (),
) -> dict[str, object]:
    errors: list[str] = []
    section_ids = [section.section_id for section in sections]
    if len(section_ids) != len(set(section_ids)):
        errors.append("every PublicationSection id must be unique")
    block_ids = [block.block_id for block in blocks]
    if len(block_ids) != len(set(block_ids)):
        errors.append("every PublicationBlock id must be unique")
    block_by_id = {block.block_id: block for block in blocks}
    claim_by_id = {claim.claim_id: claim for claim in claims}
    source_ids = {source.source_id for source in sources}
    entity_by_id = {entity.entity_id: entity for entity in entities}
    xref_ids = [xref.xref_id for xref in xrefs]
    if len(xref_ids) != len(set(xref_ids)):
        errors.append("every PublicationCrossReference id must be unique")
    xref_by_id = {xref.xref_id: xref for xref in xrefs}
    review_ids = [review.review_id for review in reviews]
    if len(review_ids) != len(set(review_ids)):
        errors.append("every PublicationReviewRecord id must be unique")
    known_ids_by_kind = {
        "publication": {publication.publication_id},
        "section": set(section_ids),
        "claim": set(claim_by_id),
        "unit": set(publication.included_unit_ids),
        "source": set(source_ids),
        "entity": set(entity_by_id),
        "block": set(block_by_id),
    }
    if len(publication.entity_ids) != len(set(publication.entity_ids)):
        errors.append("publication.entity_ids must be unique")
    for root_section_id in publication.root_section_ids:
        if root_section_id not in known_ids_by_kind["section"]:
            errors.append(f"publication {publication.publication_id} references missing root section {root_section_id}")
    for entity_id in publication.entity_ids:
        if entity_id not in entity_by_id:
            errors.append(f"publication {publication.publication_id} references missing entity {entity_id}")
    publication_block_ids = list(publication.block_ids)
    if len(publication_block_ids) != len(set(publication_block_ids)):
        errors.append("publication.block_ids must be unique")
    for block_id in publication.block_ids:
        if block_id not in block_by_id:
            errors.append(f"publication {publication.publication_id} references missing block {block_id}")
    for section in sections:
        if section.role not in VALID_PUBLICATION_SECTION_ROLES:
            errors.append(f"section {section.section_id} uses unsupported role {section.role}")
        if section.parent_section_id:
            if section.parent_section_id not in known_ids_by_kind["section"]:
                errors.append(f"section {section.section_id} references missing parent section {section.parent_section_id}")
            elif section.section_id in publication.root_section_ids:
                errors.append(f"root section {section.section_id} must not declare parent {section.parent_section_id}")
            else:
                parent_section = next(item for item in sections if item.section_id == section.parent_section_id)
                if collapse_ws(parent_section.role) != collapse_ws(section.role):
                    errors.append(
                        f"section {section.section_id} uses role {section.role} under parent {parent_section.section_id} with role {parent_section.role}"
                    )
        elif section.section_id not in publication.root_section_ids:
            errors.append(f"non-root section {section.section_id} must declare parent_section_id")
        for child_section_id in section.child_section_ids:
            if child_section_id not in known_ids_by_kind["section"]:
                errors.append(f"section {section.section_id} references missing child section {child_section_id}")
                continue
            child_section = next(item for item in sections if item.section_id == child_section_id)
            if child_section.parent_section_id != section.section_id:
                errors.append(
                    f"section {section.section_id} lists child {child_section_id} but that child declares parent {child_section.parent_section_id or '<root>'}"
                )
        for claim_id in section.claim_ids:
            if claim_id not in claim_by_id:
                errors.append(f"section {section.section_id} references missing claim {claim_id}")
        for block_id in section.block_ids:
            if block_id not in block_by_id:
                errors.append(f"section {section.section_id} references missing block {block_id}")
        for xref_id in section.xref_ids:
            if xref_id not in xref_by_id:
                errors.append(f"section {section.section_id} references missing xref {xref_id}")
    for block in blocks:
        if block.publication_id != publication.publication_id:
            errors.append(f"block {block.block_id} belongs to {block.publication_id}, expected {publication.publication_id}")
        for included_block_id in block.included_block_refs:
            if included_block_id not in block_by_id:
                errors.append(f"block {block.block_id} includes missing block {included_block_id}")
    for claim in claims:
        if claim.claim_kind == "descriptive" and not claim.source_ids:
            errors.append(f"descriptive claim {claim.claim_id} must have at least one source")
        for source_id in claim.source_ids:
            if source_id not in source_ids:
                errors.append(f"claim {claim.claim_id} references missing source {source_id}")
        for entity_id in claim.entity_ids:
            if entity_id not in entity_by_id:
                errors.append(f"claim {claim.claim_id} references missing entity {entity_id}")
        for xref_id in claim.xref_ids:
            if xref_id not in xref_by_id:
                errors.append(f"claim {claim.claim_id} references missing xref {xref_id}")
    for entity in entities:
        if entity.publication_id != publication.publication_id:
            errors.append(f"entity {entity.entity_id} belongs to {entity.publication_id}, expected {publication.publication_id}")
        if not entity.entity_kind:
            errors.append(f"entity {entity.entity_id} must declare entity_kind")
        if not entity.canonical_name:
            errors.append(f"entity {entity.entity_id} must declare canonical_name")
    for xref in xrefs:
        if xref.publication_id != publication.publication_id:
            errors.append(f"xref {xref.xref_id} belongs to {xref.publication_id}, expected {publication.publication_id}")
        if xref.xref_type not in VALID_PUBLICATION_XREF_TYPES:
            errors.append(f"xref {xref.xref_id} uses unsupported type {xref.xref_type}")
        if xref.from_kind not in VALID_PUBLICATION_XREF_TARGET_KINDS:
            errors.append(f"xref {xref.xref_id} uses unsupported from_kind {xref.from_kind}")
        if xref.to_kind not in VALID_PUBLICATION_XREF_TARGET_KINDS:
            errors.append(f"xref {xref.xref_id} uses unsupported to_kind {xref.to_kind}")
        if xref.from_kind in known_ids_by_kind and xref.from_id not in known_ids_by_kind[xref.from_kind]:
            errors.append(f"xref {xref.xref_id} references missing {xref.from_kind} {xref.from_id}")
        if xref.to_kind in known_ids_by_kind and xref.to_id not in known_ids_by_kind[xref.to_kind]:
            errors.append(f"xref {xref.xref_id} references missing {xref.to_kind} {xref.to_id}")
    for review in reviews:
        if review.publication_id != publication.publication_id:
            errors.append(f"review {review.review_id} belongs to {review.publication_id}, expected {publication.publication_id}")
        if not review.review_state:
            errors.append(f"review {review.review_id} must declare review_state")
        if review.target_kind not in known_ids_by_kind:
            errors.append(f"review {review.review_id} uses unsupported target_kind {review.target_kind}")
            continue
        if review.target_id not in known_ids_by_kind[review.target_kind]:
            errors.append(f"review {review.review_id} references missing {review.target_kind} {review.target_id}")
    visiting: set[str] = set()
    visited: set[str] = set()

    def _visit_block(block_id: str, stack: list[str]) -> None:
        if block_id in visited:
            return
        if block_id in visiting:
            cycle_start = stack.index(block_id) if block_id in stack else 0
            cycle_path = stack[cycle_start:] + [block_id]
            errors.append(f"block transclusion cycle detected: {' -> '.join(cycle_path)}")
            return
        block = block_by_id.get(block_id)
        if block is None:
            return
        visiting.add(block_id)
        next_stack = stack + [block_id]
        for included_block_id in block.included_block_refs:
            _visit_block(included_block_id, next_stack)
        visiting.remove(block_id)
        visited.add(block_id)

    for block_id in block_by_id:
        _visit_block(block_id, [])

    section_by_id = {section.section_id: section for section in sections}
    visiting_sections: set[str] = set()
    visited_sections: set[str] = set()

    def _visit_section(section_id: str, stack: list[str]) -> None:
        if section_id in visited_sections:
            return
        if section_id in visiting_sections:
            cycle_start = stack.index(section_id) if section_id in stack else 0
            cycle_path = stack[cycle_start:] + [section_id]
            errors.append(f"section tree cycle detected: {' -> '.join(cycle_path)}")
            return
        section = section_by_id.get(section_id)
        if section is None:
            return
        visiting_sections.add(section_id)
        next_stack = stack + [section_id]
        for child_section_id in section.child_section_ids:
            _visit_section(child_section_id, next_stack)
        visiting_sections.remove(section_id)
        visited_sections.add(section_id)

    for root_section_id in publication.root_section_ids:
        _visit_section(root_section_id, [])
    for section_id in section_by_id:
        _visit_section(section_id, [])
    return {
        "status": "ok" if not errors else "error",
        "errors": errors,
        "section_count": len(sections),
        "block_count": len(blocks),
        "claim_count": len(claims),
        "source_count": len(sources),
        "entity_count": len(entities),
        "xref_count": len(xrefs),
        "review_count": len(reviews),
        "publication_id": publication.publication_id,
    }
