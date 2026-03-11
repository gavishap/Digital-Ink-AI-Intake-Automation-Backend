"""
Cross-report diff engine.

Compares all scanned reports to identify static boilerplate vs dynamic patient
data, purely through code -- no LLM needed.  The 32 reports share the same
template, so text that is identical in every report is static, and text that
varies is dynamic.
"""

import re
from collections import Counter, defaultdict
from pathlib import Path

from rich.console import Console

from .models import (
    ContentClassification,
    ReportTemplate,
    ScannedReport,
    SlotType,
    TemplateSection,
    TemplateSlot,
)

console = Console()

# Label patterns: "Label:\t\tValue" or "Label: \tValue" or "Label:  Value"
_LABEL_VALUE_RE = re.compile(r"^(.+?):[\t ]{2,}(.+)$")


def _normalize_heading(heading: str) -> str:
    """Normalize heading text for cross-report matching."""
    cleaned = heading.strip().upper()
    cleaned = re.sub(r"[\t ]+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned


def _classify_dynamic_element(texts: list[str]) -> SlotType:
    """Determine what kind of dynamic content this is based on the variations."""
    avg_len = sum(len(t) for t in texts) / len(texts) if texts else 0

    # Long varying text = narrative
    if avg_len > 200:
        return SlotType.DYNAMIC_NARRATIVE

    # If most variations are short and look like list items
    if avg_len < 100 and len(texts) > 3:
        return SlotType.DYNAMIC_DIRECT

    return SlotType.DYNAMIC_DIRECT


def _extract_label(text: str) -> str | None:
    """Extract field label from 'Label:\\t\\tValue' patterns."""
    m = _LABEL_VALUE_RE.match(text)
    if m:
        return m.group(1).strip()
    return None


def diff_reports(reports: list[ScannedReport]) -> ReportTemplate:
    """Compare all reports and produce a canonical template.

    For each section, compares element text across all reports:
    - Identical everywhere = STATIC
    - Varies = DYNAMIC (with sub-type detection)
    """
    n = len(reports)
    console.print(f"[bold]Diffing {n} reports to extract template...[/bold]")

    # Step 1: Build heading inventory across all reports
    heading_counts: Counter[str] = Counter()
    section_order_votes: defaultdict[str, list[int]] = defaultdict(list)

    for report in reports:
        for idx, section in enumerate(report.sections):
            norm = _normalize_heading(section.heading)
            heading_counts[norm] += 1
            section_order_votes[norm].append(idx)

    # Step 2: For each heading, collect element texts across all reports
    # Key = normalized heading, Value = list of (report_idx, element_texts)
    section_data: defaultdict[str, list[list[str]]] = defaultdict(list)

    for report in reports:
        for section in report.sections:
            norm = _normalize_heading(section.heading)
            texts = [el.text for el in section.elements]
            section_data[norm].append(texts)

    # Step 3: Determine canonical section ordering
    avg_positions = {
        heading: sum(positions) / len(positions)
        for heading, positions in section_order_votes.items()
    }
    ordered_headings = sorted(avg_positions.keys(), key=lambda h: avg_positions[h])

    # Step 4: Build template sections
    template_sections: list[TemplateSection] = []
    conditional_ids: list[str] = []

    for norm_heading in ordered_headings:
        count = heading_counts[norm_heading]

        # Filter noise: sections appearing in fewer than 3 reports are one-offs
        if count < 3:
            continue

        is_required = count >= n * 0.9
        all_element_lists = section_data[norm_heading]

        # Find the original heading text (from first report that has it)
        original_heading = norm_heading
        for report in reports:
            for section in report.sections:
                if _normalize_heading(section.heading) == norm_heading:
                    original_heading = section.heading
                    break
            else:
                continue
            break

        section_id = _make_section_id(norm_heading)

        # Compare element by element across reports
        slots = _diff_section_elements(all_element_lists)

        # Determine overall section classification
        slot_types = [s.slot_type for s in slots]
        if all(t == SlotType.STATIC for t in slot_types):
            classification = ContentClassification.STATIC
        elif all(t == SlotType.DYNAMIC_NARRATIVE for t in slot_types):
            classification = ContentClassification.DYNAMIC_NARRATIVE
        elif any(t == SlotType.DYNAMIC_NARRATIVE for t in slot_types):
            classification = ContentClassification.DYNAMIC_NARRATIVE
        elif any(t != SlotType.STATIC for t in slot_types):
            classification = ContentClassification.DYNAMIC_DIRECT
        else:
            classification = ContentClassification.UNKNOWN

        ts = TemplateSection(
            id=section_id,
            heading=original_heading,
            appears_in=count,
            total_reports=n,
            is_required=is_required,
            classification=classification,
            slots=slots,
        )
        template_sections.append(ts)

        if not is_required:
            conditional_ids.append(section_id)

    section_ids = [s.id for s in template_sections]

    template = ReportTemplate(
        total_reports_analyzed=n,
        total_sections=len(template_sections),
        sections=template_sections,
        section_order=section_ids,
        conditional_sections=conditional_ids,
    )

    # Summary stats
    static_sections = sum(1 for s in template_sections if s.classification == ContentClassification.STATIC)
    dynamic_sections = sum(1 for s in template_sections if s.classification != ContentClassification.STATIC)
    console.print(
        f"  [green]Template: {len(template_sections)} sections "
        f"({static_sections} static, {dynamic_sections} dynamic, "
        f"{len(conditional_ids)} conditional)[/green]"
    )

    return template


def _make_section_id(norm_heading: str) -> str:
    cleaned = norm_heading.lower().strip()
    cleaned = "".join(c if c.isalnum() or c == " " else "" for c in cleaned)
    parts = cleaned.split()
    return "_".join(parts[:6])


def _diff_section_elements(all_element_lists: list[list[str]]) -> list[TemplateSlot]:
    """Diff element texts within a section across all reports.

    Aligns by position index.  If element at index i has the same text in
    every report -> static.  If it varies -> dynamic.
    """
    if not all_element_lists:
        return []

    max_len = max(len(el_list) for el_list in all_element_lists)
    if max_len == 0:
        return []

    slots: list[TemplateSlot] = []

    for idx in range(max_len):
        texts_at_idx: list[str] = []
        for el_list in all_element_lists:
            if idx < len(el_list):
                texts_at_idx.append(el_list[idx])

        if not texts_at_idx:
            continue

        unique_texts = set(texts_at_idx)

        if len(unique_texts) == 1:
            # Identical in every report -> static
            slots.append(TemplateSlot(
                slot_type=SlotType.STATIC,
                static_text=texts_at_idx[0],
                element_index=idx,
            ))
        else:
            # Varies across reports -> dynamic
            slot_type = _classify_dynamic_element(texts_at_idx)

            # Check for label:value pattern
            label = None
            labels = [_extract_label(t) for t in texts_at_idx]
            labels_clean = [l for l in labels if l]
            if labels_clean:
                # If >80% of reports have the same label, it's a label:value field
                label_counts = Counter(labels_clean)
                most_common_label, lcount = label_counts.most_common(1)[0]
                if lcount > len(texts_at_idx) * 0.7:
                    label = most_common_label
                    slot_type = SlotType.DYNAMIC_DIRECT

            # Pick a few diverse examples
            examples = _pick_examples(texts_at_idx, max_examples=3)

            slots.append(TemplateSlot(
                slot_type=slot_type,
                label=label,
                example_values=examples,
                element_index=idx,
            ))

    return slots


def _pick_examples(texts: list[str], max_examples: int = 3) -> list[str]:
    """Pick a few diverse example values, preferring shorter + distinct."""
    unique = list(set(texts))
    unique.sort(key=len)
    return unique[:max_examples]
